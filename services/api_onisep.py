"""
Formations professionnelles par territoire — données Onisep.

Sources : API Onisep (gratuit, pas d'authentification).
Fournit par département : formations en apprentissage, CAP, Bac pro, BTS, etc.
relevant pour le secteur industriel (métallurgie UIMM).

Service best-effort : l'API Onisep peut être indisponible ou lente.
Chaque département est chargé paresseusement avec un budget réduit ;
un échec est mémorisé quelques minutes seulement pour laisser la source
se rétablir (même pattern que api_activite.py).
"""
import logging
import time

from utils.cache import load, save
from utils.http import get_with_retry

logger = logging.getLogger("veilleia.formations")

_ONISEP_API = "https://api.onisep.fr/search"

_OK_TTL = 86_400       # cache valide gardé 24 h
_ECHEC_TTL = 300       # échec retenté après 5 min

# {code_dept: (expiration, formations | None si échec)}
_index_memo: dict[str, tuple[float, list[dict] | None]] = {}


def _fetch_formations_dept(code_dept: str) -> list[dict] | None:
    """
    Récupère les formations du département depuis Onisep (cache 24 h).
    Returns None si source indisponible.
    """
    cache_key = f"formations_{code_dept}"

    try:
        cached = load(cache_key)
    except Exception:
        logger.exception("Cache %s illisible — refetch", cache_key)
        cached = None
    if cached is not None:
        return cached

    try:
        # Budget réduit : source best-effort, ne doit jamais bloquer (comme api_activite)
        # Query : formations industrielles (CAP, Bac pro, BTS) en apprentissage
        params = {
            "domain": "formation_continue",  # ou "formation_initiale"
            "romes": "H1203",  # Code Rome pour opérateurs industriels
            "page": "1",
            "rows": "50",
        }
        resp = get_with_retry(
            _ONISEP_API,
            params=params,
            retryable=(429, 500, 502, 503),
            max_attempts=2,
            base_delay=1.0,
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("resultats", [])
        records = []
        for item in results:
            record = {
                "titre": item.get("titre_principal", ""),
                "url_descriptif": item.get("url", ""),
                "etablissement": item.get("etablissement_libelle_principal", ""),
                "type": item.get("type_libelle", ""),
                "localite": item.get("localite_libelle", ""),
            }
            if record["titre"]:
                records.append(record)
    except Exception:
        logger.exception("Formations %s indisponible (%s)", code_dept, _ONISEP_API)
        return None

    save(cache_key, records)
    return records


def get_formations(code_dept: str) -> list[dict] | None:
    """
    Formations professionnelles d'un département, ou None si source indisponible.
    Matching par code département.

    Mémo RAM : 24 h après succès, 5 min après échec (la source peut revenir).
    Returns list of dicts with: titre, url_descriptif, etablissement, type, localite.
    """
    now = time.time()
    memo = _index_memo.get(code_dept)
    if memo is not None and now < memo[0]:
        return memo[1]

    records = _fetch_formations_dept(code_dept)
    if records is None:
        _index_memo[code_dept] = (now + _ECHEC_TTL, None)
        return None

    _index_memo[code_dept] = (now + _OK_TTL, records)
    return records
