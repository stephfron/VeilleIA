"""
INSEE SIRENE — établissements industriels par territoire.
API : https://api.insee.fr/api-sirene/3.11
Auth : header X-INSEE-Api-Key-Integration (clé dans .env → INSEE_SIRENE_API_KEY)

Sections NAF couvertes :
  B  05–09  Industries extractives
  C  10–33  Industries manufacturières
"""
import time
import pandas as pd
from utils.cache import load, save
from utils.config import (
    SIRENE_BASE_URL, SIRENE_API_KEY,
    SIRENE_PAGE_SIZE, SIRENE_MAX_OFFSET, SIRENE_DELAY, SIRENE_RETRY_DELAY,
    SIRENE_NAF_PREFIXES, SIRENE_TRANCHE_MIDPOINT,
)
from utils.http import get_with_retry

_CHAMPS = (
    "siret,trancheEffectifsEtablissement,"
    "activitePrincipaleUniteLegale,"
    "codePostalEtablissement,libelleCommuneEtablissement,"
    "denominationUniteLegale"
)


def _headers() -> dict[str, str]:
    return {"X-INSEE-Api-Key-Integration": SIRENE_API_KEY, "Accept": "application/json"}


def _dept_to_cp_prefix(code_dept: str) -> str:
    """Code département → préfixe de code postal pour la requête Lucene."""
    if code_dept in ("2A", "2B"):
        return "20"   # Corse : CP 20xxx partagé entre les deux depts
    return code_dept  # "01", "75", "971"… déjà au bon format


def _lucene_query(cp_prefix: str, naf_prefix: str) -> str:
    return (
        f"codePostalEtablissement:{cp_prefix}* "
        f"AND periode(etatAdministratifEtablissement:A) "
        f"AND activitePrincipaleUniteLegale:{naf_prefix}*"
    )


def _flatten(e: dict) -> dict:
    addr = e.get("adresseEtablissement") or {}
    ul = e.get("uniteLegale") or {}
    tranche = e.get("trancheEffectifsEtablissement") or "NN"
    return {
        "siret":             e.get("siret"),
        "naf":               ul.get("activitePrincipaleUniteLegale"),
        "nom":               ul.get("denominationUniteLegale"),
        "code_postal":       addr.get("codePostalEtablissement"),
        "commune":           addr.get("libelleCommuneEtablissement"),
        "tranche_effectifs": tranche,
        "effectifs_estimes": SIRENE_TRANCHE_MIDPOINT.get(tranche, 0),
    }


def _fetch_naf_prefix(cp_prefix: str, naf_prefix: str) -> list[dict]:
    """Télécharge tous les établissements actifs d'un dept pour un préfixe NAF."""
    q = _lucene_query(cp_prefix, naf_prefix)
    records: list[dict] = []
    debut = 0

    while True:
        resp = get_with_retry(
            SIRENE_BASE_URL,
            headers=_headers(),
            params={"q": q, "nombre": SIRENE_PAGE_SIZE, "debut": debut, "champs": _CHAMPS},
            retryable=(429,),
            base_delay=SIRENE_RETRY_DELAY,
        )
        if resp.status_code == 404:
            break   # Aucun résultat pour ce préfixe NAF dans ce département
        resp.raise_for_status()

        data = resp.json()
        batch = data.get("etablissements") or []
        records.extend(_flatten(e) for e in batch)

        total = data.get("header", {}).get("total", 0)
        debut += SIRENE_PAGE_SIZE
        if debut >= total or debut > SIRENE_MAX_OFFSET:
            break
        time.sleep(SIRENE_DELAY)

    return records


def get_industrie_dept(code_dept: str) -> pd.DataFrame:
    """
    Retourne tous les établissements industriels actifs d'un département.
    Colonnes : siret, naf, nom, code_postal, commune, tranche_effectifs, effectifs_estimes
    Cache 24 h.
    """
    cache_key = f"sirene_industrie_{code_dept}"
    cached = load(cache_key)
    if cached is not None:
        return pd.DataFrame(cached)

    cp_prefix = _dept_to_cp_prefix(code_dept)
    seen: set[str] = set()
    records: list[dict] = []

    for naf_prefix in SIRENE_NAF_PREFIXES:
        for rec in _fetch_naf_prefix(cp_prefix, naf_prefix):
            siret = rec.get("siret") or ""
            if siret and siret not in seen:
                seen.add(siret)
                records.append(rec)

    _EMPTY_COLS = list(_flatten({}).keys())
    df = pd.DataFrame(records) if records else pd.DataFrame(columns=_EMPTY_COLS)
    save(cache_key, df.to_dict("records"))
    return df


def resume_industrie_dept(code_dept: str) -> dict:
    """
    Résumé agrégé pour un département :
      nb_etablissements, effectifs_estimes_total, top_naf (5 codes)
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
        "nb_etablissements":      len(df),
        "effectifs_estimes_total": int(df["effectifs_estimes"].sum()),
        "top_naf":                top_naf,
    }
