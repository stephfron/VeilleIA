"""
CRM lobbying — suivi des relations et interactions avec les parlementaires.

Double backend, choisi par la config (utils/config.py) :
  - DATABASE_URL défini  → PostgreSQL (Supabase) via psycopg 3. Persistant :
    mode requis sur Vercel où le filesystem serverless est éphémère.
  - DATABASE_URL absent  → SQLite (stdlib) dans CRM_DB_PATH. Mode dev/tests,
    zéro configuration.

Les fonctions publiques sont strictement identiques quel que soit le backend :
les requêtes sont écrites une seule fois en style `?` (sqlite3) et traduites
en `%s` pour psycopg (`_pg_sql`). `INSERT … RETURNING id` unifie la
récupération des ids (supporté par SQLite ≥ 3.35 et PostgreSQL).

Clé élu : « prenom nom » normalisé (accents/casse ignorés, tirets ≡ espaces),
même logique que fiche_par_identite() dans services/fiche_territoire.py.
"""
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

from services.pertinence import _fold
from utils import config

STATUTS = {"a_contacter", "contacte", "allie", "neutre", "opposant"}
CANAUX = {"rendez_vous", "mail", "courrier", "appel", "evenement", "autre"}

# Schémas — colonnes identiques entre les deux moteurs (testé), seule la
# déclaration d'auto-incrément diffère. Dates stockées en TEXT ISO 8601 :
# l'ordre lexicographique est l'ordre chronologique, comparable en SQL.
_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS relations (
    elu_key TEXT PRIMARY KEY,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    statut TEXT NOT NULL DEFAULT 'a_contacter',
    maj TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    elu_key TEXT NOT NULL,
    date TEXT NOT NULL,
    canal TEXT NOT NULL,
    objet TEXT NOT NULL,
    notes TEXT,
    rappel TEXT,
    cree_le TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_interactions_elu_date ON interactions (elu_key, date DESC);
"""

_SCHEMA_POSTGRES = """
CREATE TABLE IF NOT EXISTS relations (
    elu_key TEXT PRIMARY KEY,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    statut TEXT NOT NULL DEFAULT 'a_contacter',
    maj TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS interactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    elu_key TEXT NOT NULL,
    date TEXT NOT NULL,
    canal TEXT NOT NULL,
    objet TEXT NOT NULL,
    notes TEXT,
    rappel TEXT,
    cree_le TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_interactions_elu_date ON interactions (elu_key, date DESC);
"""

# Le schéma Postgres n'est vérifié qu'une fois par process (aller-retour réseau).
_pg_schema_ok = False


def elu_key(nom: str, prenom: str) -> str:
    """Clé « prenom nom » : accents/casse ignorés, tirets ≡ espaces."""
    return re.sub(r"[-\s]+", " ", _fold(f"{prenom} {nom}")).strip()


def _pg_sql(sql: str) -> str:
    """Traduit les placeholders `?` (sqlite3) en `%s` (psycopg)."""
    return sql.replace("?", "%s")


def _maintenant() -> str:
    """Horodatage ISO 8601 UTC (colonnes maj / cree_le)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _date_iso(valeur: str | None, defaut_aujourdhui: bool = False) -> str | None:
    """Valide une date ISO (ValueError sinon) ; date du jour en option par défaut."""
    if valeur is None:
        return date.today().isoformat() if defaut_aujourdhui else None
    return date.fromisoformat(valeur).isoformat()


def _connect_sqlite() -> sqlite3.Connection:
    path = Path(config.CRM_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA_SQLITE)
    return conn


def _connect_postgres():
    global _pg_schema_ok
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(config.DATABASE_URL, row_factory=dict_row)
    if not _pg_schema_ok:
        # psycopg refuse les scripts multi-instructions préparés :
        # exécution instruction par instruction.
        with conn.cursor() as cur:
            for stmt in _SCHEMA_POSTGRES.split(";"):
                if stmt.strip():
                    cur.execute(stmt)
        conn.commit()
        _pg_schema_ok = True
    return conn


@contextmanager
def _cursor() -> Iterator:
    """Curseur transactionnel : commit en sortie, rollback sur exception."""
    conn = _connect_postgres() if config.DATABASE_URL else _connect_sqlite()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _exec(cur, sql: str, params: tuple = ()) -> None:
    """Exécute une requête écrite en style `?`, traduite si backend Postgres."""
    cur.execute(_pg_sql(sql) if config.DATABASE_URL else sql, params)


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------

def set_statut(nom: str, prenom: str, statut: str) -> dict:
    """Fixe le statut d'un élu (upsert). ValueError si statut inconnu."""
    if statut not in STATUTS:
        raise ValueError(f"statut inconnu : {statut!r} (attendu : {sorted(STATUTS)})")
    key = elu_key(nom, prenom)
    with _cursor() as cur:
        _exec(cur, """
            INSERT INTO relations (elu_key, nom, prenom, statut, maj)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (elu_key) DO UPDATE SET statut = excluded.statut, maj = excluded.maj
        """, (key, nom, prenom, statut, _maintenant()))
    return {"elu_key": key, "statut": statut}


def get_statuts() -> dict[str, str]:
    """Statut de chaque élu suivi : {elu_key: statut}."""
    with _cursor() as cur:
        _exec(cur, "SELECT elu_key, statut FROM relations")
        return {row["elu_key"]: row["statut"] for row in map(dict, cur.fetchall())}


def add_interaction(
    nom: str,
    prenom: str,
    canal: str,
    objet: str,
    date_interaction: str | None = None,
    notes: str | None = None,
    rappel: str | None = None,
) -> dict:
    """
    Enregistre une interaction avec un élu. ValueError si canal inconnu ou
    date/rappel non ISO (AAAA-MM-JJ). Date du jour par défaut. Crée la
    relation avec le statut `contacte` s'il s'agit du premier contact,
    sans écraser un statut déjà fixé.
    """
    if canal not in CANAUX:
        raise ValueError(f"canal inconnu : {canal!r} (attendu : {sorted(CANAUX)})")
    date_iso = _date_iso(date_interaction, defaut_aujourdhui=True)
    rappel_iso = _date_iso(rappel)
    key = elu_key(nom, prenom)

    with _cursor() as cur:
        _exec(cur, """
            INSERT INTO relations (elu_key, nom, prenom, statut, maj)
            VALUES (?, ?, ?, 'contacte', ?)
            ON CONFLICT (elu_key) DO NOTHING
        """, (key, nom, prenom, _maintenant()))
        _exec(cur, """
            INSERT INTO interactions (elu_key, date, canal, objet, notes, rappel, cree_le)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING id
        """, (key, date_iso, canal, objet, notes, rappel_iso, _maintenant()))
        new_id = dict(cur.fetchone())["id"]
    return {"id": new_id, "elu_key": key}


def get_interactions(nom: str, prenom: str) -> list[dict]:
    """Interactions d'un élu, les plus récentes d'abord."""
    with _cursor() as cur:
        _exec(cur, """
            SELECT id, elu_key, date, canal, objet, notes, rappel, cree_le
            FROM interactions
            WHERE elu_key = ?
            ORDER BY date DESC, id DESC
        """, (elu_key(nom, prenom),))
        return [dict(row) for row in cur.fetchall()]


def delete_interaction(interaction_id: int) -> bool:
    """Supprime une interaction. False si l'id est inconnu."""
    with _cursor() as cur:
        _exec(cur, "DELETE FROM interactions WHERE id = ?", (interaction_id,))
        return cur.rowcount > 0


def rappels_en_attente() -> list[dict]:
    """
    Interactions dont la date de rappel est échue (rappel <= aujourd'hui),
    jointes aux relations pour retrouver nom, prénom et statut de l'élu.
    """
    with _cursor() as cur:
        _exec(cur, """
            SELECT i.id, i.elu_key, i.date, i.canal, i.objet, i.notes, i.rappel,
                   r.nom, r.prenom, r.statut
            FROM interactions i
            JOIN relations r ON r.elu_key = i.elu_key
            WHERE i.rappel IS NOT NULL AND i.rappel <= ?
            ORDER BY i.rappel ASC, i.id ASC
        """, (date.today().isoformat(),))
        return [dict(row) for row in cur.fetchall()]


def resume_engagement() -> dict[str, dict]:
    """
    Vue d'ensemble par élu suivi :
    {elu_key: {statut, nb_interactions, dernier_contact}} (dernier_contact
    None si aucune interaction).
    """
    with _cursor() as cur:
        _exec(cur, """
            SELECT r.elu_key, r.statut,
                   COUNT(i.id) AS nb_interactions,
                   MAX(i.date) AS dernier_contact
            FROM relations r
            LEFT JOIN interactions i ON i.elu_key = r.elu_key
            GROUP BY r.elu_key, r.statut
        """)
        return {
            row["elu_key"]: {
                "statut": row["statut"],
                "nb_interactions": int(row["nb_interactions"]),
                "dernier_contact": row["dernier_contact"],
            }
            for row in map(dict, cur.fetchall())
        }
