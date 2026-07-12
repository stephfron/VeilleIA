"""
Activité législative nominative — synthèses Regards Citoyens.
Sources : nosdeputes.fr / nossenateurs.fr (endpoint /synthese/data/json,
une seule requête pour toute la chambre, cache 24 h + seed committé).

Fournit par élu : groupe politique, amendements (proposés/signés/adoptés),
questions écrites et orales, rapports, interventions, semaines de présence.

Service best-effort : les API citoyennes peuvent être indisponibles (HTML au
lieu de JSON, 5xx) ou en retard d'une législature. Chaque chambre est chargée
paresseusement (on ne paye jamais le Sénat pour une question sur un député),
avec un budget de retry réduit ; un échec est mémorisé quelques minutes
seulement pour laisser la source se rétablir.
"""
import logging
import time

from services.pertinence import _fold
from utils.cache import load, save
from utils.http import get_with_retry

logger = logging.getLogger("veilleia.activite")

_SOURCES = {
    "Assemblée nationale": ("deputes", "https://www.nosdeputes.fr/synthese/data/json"),
    "Sénat":               ("senateurs", "https://www.nossenateurs.fr/synthese/data/json"),
}

_CHAMPS = [
    "groupe_sigle",
    "amendements_proposes", "amendements_signes", "amendements_adoptes",
    "questions_ecrites", "questions_orales",
    "rapports", "interventions", "semaines_presence",
]

_OK_TTL = 3_600        # index valide gardé en RAM 1 h
_ECHEC_TTL = 300       # échec retenté après 5 min (pas de cache négatif d'1 h)

# {chambre: (expiration, index par nom | None si échec)}
_index_memo: dict[str, tuple[float, dict[str, dict] | None]] = {}


def _fetch_synthese(chambre: str) -> list[dict] | None:
    """Télécharge la synthèse d'activité d'une chambre (cache 24 h). None si KO."""
    key_prefix, url = _SOURCES[chambre]
    cache_key = f"activite_{key_prefix}"

    try:
        cached = load(cache_key)
    except Exception:
        logger.exception("Cache %s illisible — refetch", cache_key)
        cached = None
    if cached is not None:
        return cached

    try:
        # Budget réduit : source best-effort, ne doit jamais bloquer une requête
        # utilisateur plusieurs minutes (fonction serverless plafonnée à 300 s).
        resp = get_with_retry(url, retryable=(429, 500, 502, 503),
                              max_attempts=2, base_delay=1.0, timeout=15)
        resp.raise_for_status()
        wrapper_key = key_prefix[:-1]  # "deputes" → "depute", "senateurs" → "senateur"
        records = [item[wrapper_key] for item in resp.json().get(key_prefix, []) if wrapper_key in item]
    except Exception:
        logger.exception("Synthèse %s indisponible (%s)", chambre, url)
        return None

    save(cache_key, records)
    return records


def _index_chambre(chambre: str) -> dict[str, dict] | None:
    """
    Index {"prenom nom" normalisé: record} d'une chambre, chargé paresseusement.
    Mémo RAM : 1 h après succès, 5 min après échec (la source peut revenir).
    """
    now = time.time()
    memo = _index_memo.get(chambre)
    if memo is not None and now < memo[0]:
        return memo[1]

    records = _fetch_synthese(chambre)
    if records is None:
        _index_memo[chambre] = (now + _ECHEC_TTL, None)
        return None

    by_name: dict[str, dict] = {}
    for rec in records:
        nom_complet = rec.get("nom") or f"{rec.get('prenom', '')} {rec.get('nom_de_famille', '')}"
        by_name[_fold(nom_complet.strip())] = rec
    _index_memo[chambre] = (now + _OK_TTL, by_name)
    return by_name


def get_activite(nom: str, prenom: str, chambre: str) -> dict | None:
    """
    Activité législative d'un parlementaire, ou None si introuvable / source KO.
    Matching par "prénom nom" normalisé (accents et casse ignorés).
    """
    if chambre not in _SOURCES:
        return None
    by_name = _index_chambre(chambre)
    if not by_name:
        return None
    rec = by_name.get(_fold(f"{prenom} {nom}".strip()))
    if rec is None:
        return None

    activite = {champ: rec.get(champ) for champ in _CHAMPS}
    slug = rec.get("slug")
    if slug:
        base = "nosdeputes.fr" if chambre == "Assemblée nationale" else "nossenateurs.fr"
        activite["source_url"] = f"https://www.{base}/{slug}"
    return activite
