"""
Répertoire National des Élus — sénateurs et députés.
Source : API tabulaire data.gouv.fr (dataset 5c34c4d1634f4173183a64f1)
"""
import requests
import pandas as pd
from utils.cache import get, set as cache_set
from utils.data_cleaning import normalize_dept_column

_TABULAR_BASE = "https://tabular-api.data.gouv.fr/api/resources/{}/data/"
_PAGE_SIZE = 100

_RESOURCE_IDS = {
    "senateurs": "b78f8945-509f-4609-a4a7-3048b8370479",
    "deputes":   "1ac42ff4-1336-44f8-a221-832039dbc142",
}

_COL = {
    "Code du département":                              "code_dept",
    "Libellé du département":                           "libelle_dept",
    "Code de la collectivité à statut particulier":     "code_collectivite",
    "Libellé de la collectivité à statut particulier":  "libelle_collectivite",
    "Nom de l'élu":                                     "nom",
    "Prénom de l'élu":                                  "prenom",
    "Code sexe":                                        "sexe",
    "Date de naissance":                                "date_naissance",
    "Code de la catégorie socio-professionnelle":       "code_csp",
    "Libellé de la catégorie socio-professionnelle":    "libelle_csp",
    "Date de début du mandat":                          "date_debut_mandat",
}

_COL_DEPUTE = {
    "Code de la circonscription législative":  "code_circo",
    "Libellé de la circonscription législative": "libelle_circo",
}


def _fetch_all(resource_id: str) -> list[dict]:
    """Télécharge toutes les pages de l'API tabulaire."""
    url = _TABULAR_BASE.format(resource_id)
    records: list[dict] = []
    page = 1
    while url:
        resp = requests.get(
            url,
            params={"page": page, "page_size": _PAGE_SIZE} if page == 1 else None,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        records.extend(data["data"])
        url = data["links"].get("next")
        page += 1
    return records


def _clean(records: list[dict], extra_cols: dict | None = None) -> pd.DataFrame:
    df = pd.DataFrame(records)
    rename = {**_COL, **(extra_cols or {})}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    df = df.drop(columns=["__id"], errors="ignore")
    if "code_dept" in df.columns:
        df = normalize_dept_column(df, "code_dept")
    df["geo_key"] = df.get("code_dept", pd.Series(dtype=str)).fillna(
        df.get("code_collectivite", pd.Series(dtype=str))
    )
    for col in ("date_naissance", "date_debut_mandat"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def get_senateurs() -> pd.DataFrame:
    cached = get("senateurs")
    if cached is not None:
        return pd.DataFrame(cached)
    records = _fetch_all(_RESOURCE_IDS["senateurs"])
    df = _clean(records)
    cache_set("senateurs", df.to_dict("records"))
    return df


def get_deputes() -> pd.DataFrame:
    cached = get("deputes")
    if cached is not None:
        return pd.DataFrame(cached)
    records = _fetch_all(_RESOURCE_IDS["deputes"])
    df = _clean(records, extra_cols=_COL_DEPUTE)
    cache_set("deputes", df.to_dict("records"))
    return df


def get_parlementaires() -> pd.DataFrame:
    """Sénateurs + Députés fusionnés avec colonne `chambre`."""
    sen = get_senateurs().assign(chambre="Sénat")
    dep = get_deputes().assign(chambre="Assemblée nationale")
    return pd.concat([sen, dep], ignore_index=True)
