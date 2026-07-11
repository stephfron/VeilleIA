"""
Recherche d'entreprises — recherche-entreprises.api.gouv.fr
Source SIRENE (INSEE) via API publique, sans authentification.
"""
import requests
import pandas as pd
from utils.cache import get, set as cache_set

_BASE_URL = "https://recherche-entreprises.api.gouv.fr/search"
_DEFAULT_PER_PAGE = 25
_MAX_PER_PAGE = 25  # limite API


def search_entreprises(
    q: str = "",
    departement: str | None = None,
    code_naf: str | None = None,
    page: int = 1,
    per_page: int = _DEFAULT_PER_PAGE,
) -> dict:
    """
    Recherche d'entreprises avec filtres optionnels.

    Retourne le dict brut de l'API :
      {
        "results": [...],
        "total_results": int,
        "page": int,
        "per_page": int,
        "total_pages": int,
      }

    Paramètres
    ----------
    q           : terme libre (raison sociale, SIREN, SIRET…)
    departement : code département, ex. "75", "2A"
    code_naf    : code APE/NAF, ex. "2030Z"
    page        : numéro de page (base 1)
    per_page    : résultats par page (max 25)
    """
    params: dict = {"page": page, "per_page": min(per_page, _MAX_PER_PAGE)}
    if q:
        params["q"] = q
    if departement:
        params["departement"] = departement
    if code_naf:
        params["activite_principale"] = code_naf

    resp = requests.get(_BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_entreprises_dept(
    departement: str,
    code_naf: str | None = None,
    max_pages: int = 4,
) -> pd.DataFrame:
    """
    Récupère toutes les entreprises d'un département (jusqu'à max_pages pages).
    Met en cache par clé `sirene_{departement}_{code_naf or 'all'}`.

    Colonnes retournées (sélection) :
      siren, nom_complet, siege_adresse, siege_code_postal, siege_commune,
      activite_principale, date_creation, etat_administratif,
      tranche_effectif_salarie, categorie_entreprise
    """
    naf_key = code_naf or "all"
    cache_key = f"sirene_{departement}_{naf_key}"

    cached = get(cache_key)
    if cached is not None:
        return pd.DataFrame(cached)

    records: list[dict] = []
    for p in range(1, max_pages + 1):
        data = search_entreprises(
            departement=departement, code_naf=code_naf, page=p, per_page=_MAX_PER_PAGE
        )
        batch = data.get("results", [])
        records.extend(_flatten(r) for r in batch)
        if p >= data.get("total_pages", 1):
            break

    df = pd.DataFrame(records) if records else pd.DataFrame(columns=_COLUMNS)
    cache_set(cache_key, df.to_dict("records"))
    return df


_COLUMNS = [
    "siren",
    "nom_complet",
    "siege_adresse",
    "siege_code_postal",
    "siege_commune",
    "activite_principale",
    "date_creation",
    "etat_administratif",
    "tranche_effectif_salarie",
    "categorie_entreprise",
]


def _flatten(r: dict) -> dict:
    """Extrait les champs utiles d'un résultat API."""
    siege = r.get("siege") or {}
    return {
        "siren": r.get("siren"),
        "nom_complet": r.get("nom_complet"),
        "siege_adresse": siege.get("adresse"),
        "siege_code_postal": siege.get("code_postal"),
        "siege_commune": siege.get("libelle_commune"),
        "activite_principale": r.get("activite_principale"),
        "date_creation": r.get("date_creation"),
        "etat_administratif": r.get("etat_administratif"),
        "tranche_effectif_salarie": r.get("tranche_effectif_salarie"),
        "categorie_entreprise": r.get("categorie_entreprise"),
    }
