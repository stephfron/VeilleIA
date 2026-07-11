"""
INSEE SIRENE — établissements industriels par territoire.
API : https://api.insee.fr/api-sirene/3.11
Auth : header X-INSEE-Api-Key-Integration (clé dans .env)

Sections NAF couvertes (industrie manufacturière + extractive) :
  B  05–09  Industries extractives
  C  10–33  Industries manufacturières
"""
import os
import time
import requests
import pandas as pd
from utils.cache import get, set as cache_set

_BASE_URL = "https://api.insee.fr/api-sirene/3.11/siret"
_PAGE_SIZE = 1000
_MAX_OFFSET = 9000   # INSEE bloque au-delà de 10 000 résultats par requête
_DELAY = 1.0         # secondes entre appels pour éviter le rate-limit
_RETRY_DELAY = 10.0  # attente après un 429

# Sections NAF industrie — 8 préfixes larges au lieu de 29 précis
# "1*" couvre 10–19, "2*" couvre 20–29, puis 30/31/32/33 séparément
# Section B (extractives) : 05–09
_NAF_PREFIXES = ["05", "06", "07", "08", "09",   # Section B
                 "1", "2",                        # Section C 10-29 (deux appels)
                 "30", "31", "32", "33"]          # Section C 30-33

# Midpoint salariés par tranche (estimation basse/haute moyennée)
_TRANCHE_MIDPOINT: dict[str, int] = {
    "NN": 0, "00": 0, "01": 1, "02": 4, "03": 7,
    "11": 14, "12": 34, "21": 74, "22": 149,
    "31": 224, "32": 374, "41": 749, "42": 1499,
    "51": 3499, "52": 7499, "53": 15000,
}


def _headers() -> dict[str, str]:
    key = os.getenv("INSEE_SIRENE_API_KEY", "")
    return {"X-INSEE-Api-Key-Integration": key, "Accept": "application/json"}


def _dept_to_cp_prefix(code_dept: str) -> str:
    """Convertit un code département en préfixe de code postal SIRENE."""
    if code_dept in ("2A", "2B"):
        return "20"       # Corse : CP 20xxx (les deux depts partagent le préfixe)
    return code_dept      # "01", "75", "971"… déjà formatés


def _fetch_naf_prefix(cp_prefix: str, naf_prefix: str) -> list[dict]:
    """Récupère tous les établissements actifs d'un dept pour un préfixe NAF."""
    q = (
        f"codePostalEtablissement:{cp_prefix}* "
        f"AND periode(etatAdministratifEtablissement:A) "
        f"AND activitePrincipaleUniteLegale:{naf_prefix}*"
    )
    records: list[dict] = []
    debut = 0
    while True:
        resp = requests.get(
            _BASE_URL,
            headers=_headers(),
            params={"q": q, "nombre": _PAGE_SIZE, "debut": debut,
                    "champs": "siret,trancheEffectifsEtablissement,"
                               "activitePrincipaleUniteLegale,"
                               "codePostalEtablissement,libelleCommuneEtablissement,"
                               "denominationUniteLegale"},
            timeout=30,
        )
        if resp.status_code == 404:
            break   # aucun établissement pour ce préfixe NAF dans ce département
        if resp.status_code == 429:
            time.sleep(_RETRY_DELAY)
            continue  # retry la même page
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("etablissements") or []
        records.extend(_flatten(e) for e in batch)
        total = data.get("header", {}).get("total", 0)
        debut += _PAGE_SIZE
        if debut >= total or debut > _MAX_OFFSET:
            break
        time.sleep(_DELAY)
    return records


def _flatten(e: dict) -> dict:
    addr = e.get("adresseEtablissement") or {}
    ul = e.get("uniteLegale") or {}
    tranche = e.get("trancheEffectifsEtablissement") or "NN"
    return {
        "siret": e.get("siret"),
        "naf": ul.get("activitePrincipaleUniteLegale"),
        "nom": ul.get("denominationUniteLegale"),
        "code_postal": addr.get("codePostalEtablissement"),
        "commune": addr.get("libelleCommuneEtablissement"),
        "tranche_effectifs": tranche,
        "effectifs_estimes": _TRANCHE_MIDPOINT.get(tranche, 0),
    }


def get_industrie_dept(code_dept: str) -> pd.DataFrame:
    """
    Retourne tous les établissements industriels actifs d'un département.
    Colonnes : siret, naf, nom, code_postal, commune,
               tranche_effectifs, effectifs_estimes
    Cache 24h par département.
    """
    cache_key = f"sirene_industrie_{code_dept}"
    cached = get(cache_key)
    if cached is not None:
        return pd.DataFrame(cached)

    cp_prefix = _dept_to_cp_prefix(code_dept)
    seen: set[str] = set()
    records: list[dict] = []

    for naf_prefix in _NAF_PREFIXES:
        batch = _fetch_naf_prefix(cp_prefix, naf_prefix)
        for rec in batch:
            siret = rec.get("siret") or ""
            if siret and siret not in seen:
                seen.add(siret)
                records.append(rec)

    df = pd.DataFrame(records) if records else pd.DataFrame(columns=list(_flatten({}).keys()))
    cache_set(cache_key, df.to_dict("records"))
    return df


def resume_industrie_dept(code_dept: str) -> dict:
    """
    Résumé agrégé pour un département :
      nb_etablissements, effectifs_estimes_total,
      top_naf (5 codes les plus fréquents avec libellé court)
    """
    df = get_industrie_dept(code_dept)
    if df.empty:
        return {"nb_etablissements": 0, "effectifs_estimes_total": 0, "top_naf": []}

    top_naf = (
        df.groupby("naf")
        .agg(nb=("siret", "count"), effectifs=("effectifs_estimes", "sum"))
        .sort_values("nb", ascending=False)
        .head(5)
        .reset_index()
        .to_dict("records")
    )

    return {
        "nb_etablissements": len(df),
        "effectifs_estimes_total": int(df["effectifs_estimes"].sum()),
        "top_naf": top_naf,
    }
