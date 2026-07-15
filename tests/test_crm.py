"""Tests du CRM (services/crm.py) — backend SQLite sur tmp_path, aucun réseau."""
import re
from datetime import date, timedelta

import pytest

from services import crm
from utils import config


@pytest.fixture(autouse=True)
def crm_db(tmp_path, monkeypatch):
    """Base SQLite jetable : pas de DATABASE_URL, CRM_DB_PATH vers tmp_path."""
    monkeypatch.setattr(config, "DATABASE_URL", "")
    monkeypatch.setattr(config, "CRM_DB_PATH", tmp_path / "crm.sqlite")


# ---------------------------------------------------------------- elu_key

def test_elu_key_normalisation():
    assert crm.elu_key("Dupont", "Marie") == "marie dupont"
    # Accents et casse ignorés
    assert crm.elu_key("KERNÉIS", "Élodie") == crm.elu_key("kerneis", "elodie")
    # Tirets ≡ espaces
    assert crm.elu_key("Kernéis-Dupont", "Jean") == "jean kerneis dupont"
    # Espaces multiples et bords repliés
    assert crm.elu_key("  Dupont ", " Marie  ") == "marie dupont"


# ---------------------------------------------------------------- statuts

def test_set_statut_upsert():
    crm.set_statut("Dupont", "Marie", "neutre")
    crm.set_statut("Dupont", "Marie", "allie")  # même élu → mise à jour
    crm.set_statut("Martin", "Paul", "opposant")
    assert crm.get_statuts() == {"marie dupont": "allie", "paul martin": "opposant"}


def test_set_statut_invalide():
    with pytest.raises(ValueError):
        crm.set_statut("Dupont", "Marie", "meilleur_ami")


# ---------------------------------------------------------------- interactions

def test_add_interaction_canal_invalide():
    with pytest.raises(ValueError):
        crm.add_interaction("Dupont", "Marie", "pigeon_voyageur", "Sujet")


def test_add_interaction_date_invalide():
    with pytest.raises(ValueError):
        crm.add_interaction("Dupont", "Marie", "mail", "Sujet", date_interaction="13/07/2026")
    with pytest.raises(ValueError):
        crm.add_interaction("Dupont", "Marie", "mail", "Sujet", rappel="pas-une-date")


def test_cycle_interaction_complet():
    resultat = crm.add_interaction("Dupont", "Marie", "rendez_vous", "Présentation filière",
                                   date_interaction="2026-07-01", notes="Très ouvert")
    assert resultat["elu_key"] == "marie dupont"

    # Première interaction → relation créée avec statut contacte
    assert crm.get_statuts() == {"marie dupont": "contacte"}

    # Un statut déjà fixé n'est pas écrasé par une interaction suivante
    crm.set_statut("Dupont", "Marie", "allie")
    crm.add_interaction("Dupont", "Marie", "mail", "Relance")
    assert crm.get_statuts()["marie dupont"] == "allie"

    inters = crm.get_interactions("Dupont", "Marie")
    assert len(inters) == 2
    assert inters[0]["objet"] == "Relance"  # plus récente d'abord (date du jour)
    assert inters[1]["date"] == "2026-07-01"
    assert inters[1]["notes"] == "Très ouvert"

    assert crm.delete_interaction(resultat["id"]) is True
    assert crm.delete_interaction(resultat["id"]) is False  # déjà supprimée
    assert len(crm.get_interactions("Dupont", "Marie")) == 1


def test_add_interaction_date_du_jour_par_defaut():
    crm.add_interaction("Dupont", "Marie", "appel", "Prise de contact")
    inters = crm.get_interactions("Dupont", "Marie")
    assert inters[0]["date"] == date.today().isoformat()


# ---------------------------------------------------------------- rappels

def test_rappels_dus_vs_futurs():
    hier = (date.today() - timedelta(days=1)).isoformat()
    demain = (date.today() + timedelta(days=1)).isoformat()
    crm.add_interaction("Dupont", "Marie", "mail", "À relancer", rappel=hier)
    crm.add_interaction("Dupont", "Marie", "mail", "Rappel du jour", rappel=date.today().isoformat())
    crm.add_interaction("Martin", "Paul", "appel", "Plus tard", rappel=demain)
    crm.add_interaction("Martin", "Paul", "appel", "Sans rappel")

    dus = crm.rappels_en_attente()
    assert [r["objet"] for r in dus] == ["À relancer", "Rappel du jour"]
    # Jointure avec relations : nom/prénom/statut disponibles
    assert dus[0]["nom"] == "Dupont"
    assert dus[0]["prenom"] == "Marie"
    assert dus[0]["statut"] == "contacte"


# ---------------------------------------------------------------- résumé

def test_resume_engagement():
    crm.set_statut("Durand", "Luc", "a_contacter")  # relation sans interaction
    crm.add_interaction("Dupont", "Marie", "mail", "Premier contact", date_interaction="2026-06-01")
    crm.add_interaction("Dupont", "Marie", "rendez_vous", "Suivi", date_interaction="2026-07-02")

    resume = crm.resume_engagement()
    assert resume["luc durand"] == {"statut": "a_contacter", "nb_interactions": 0,
                                    "dernier_contact": None}
    assert resume["marie dupont"] == {"statut": "contacte", "nb_interactions": 2,
                                      "dernier_contact": "2026-07-02"}


# ---------------------------------------------------------------- backend PG

def test_pg_sql_traduction():
    assert crm._pg_sql("SELECT * FROM t WHERE a = ? AND b <= ?") == \
        "SELECT * FROM t WHERE a = %s AND b <= %s"
    assert crm._pg_sql("SELECT 1") == "SELECT 1"


def _colonnes(schema: str) -> dict[str, list[str]]:
    """Parse les CREATE TABLE d'un schéma : {table: [colonnes]}."""
    tables: dict[str, list[str]] = {}
    for nom, corps in re.findall(r"CREATE TABLE IF NOT EXISTS (\w+) \(([^;]+)\);", schema):
        tables[nom] = [
            ligne.strip().split()[0]
            for ligne in corps.strip().splitlines()
            if ligne.strip()
        ]
    return tables


def test_parite_colonnes_sqlite_postgres():
    sqlite = _colonnes(crm._SCHEMA_SQLITE)
    postgres = _colonnes(crm._SCHEMA_POSTGRES)
    assert sqlite.keys() == {"relations", "interactions"}
    assert sqlite == postgres
