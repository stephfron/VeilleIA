"""
Répertoire National des Élus — sénateurs et députés.
Source : API tabulaire data.gouv.fr (dataset 5c34c4d1634f4173183a64f1)
"""
import pandas as pd
from utils.cache import load, save
from utils.config import RNE_BASE_URL, RNE_PAGE_SIZE, RNE_RESOURCE_IDS
from utils.data_cleaning import normalize_dept_column
from utils.http import get_with_retry

_COL = {
    "Code du département":                             "code_dept",
    "Libellé du département":                          "libelle_dept",
    "Code de la collectivité à statut particulier":    "code_collectivite",
    "Libellé de la collectivité à statut particulier": "libelle_collectivite",
    "Nom de l'élu":                                    "nom",
    "Prénom de l'élu":                                 "prenom",
    "Code sexe":                                       "sexe",
    "Date de naissance":                               "date_naissance",
    "Code de la catégorie socio-professionnelle":      "code_csp",
    "Libellé de la catégorie socio-professionnelle":   "libelle_csp",
    "Date de début du mandat":                         "date_debut_mandat",
}

_COL_DEPUTE = {
    "Code de la circonscription législative":    "code_circo",
    "Libellé de la circonscription législative": "libelle_circo",
}


def _fetch_all(resource_id: str) -> list[dict]:
    """Télécharge toutes les pages de l'API tabulaire (pagination via links.next)."""
    next_url: str | None = RNE_BASE_URL.format(resource_id)
    params: dict | None = {"page": 1, "page_size": RNE_PAGE_SIZE}
    records: list[dict] = []

    while next_url:
        resp = get_with_retry(next_url, params=params, retryable=(429, 500, 502, 503))
        resp.raise_for_status()
        data = resp.json()
        records.extend(data["data"])
        next_url = data["links"].get("next")
        params = None   # L'URL suivante contient déjà les paramètres

    return records


def _clean(records: list[dict], extra_cols: dict | None = None) -> pd.DataFrame:
    df = pd.DataFrame(records)
    rename = {**_COL, **(extra_cols or {})}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    df = df.drop(columns=["__id"], errors="ignore")

    if "code_dept" in df.columns:
        df = normalize_dept_column(df, "code_dept")

    # Clé géographique : code_dept en priorité, sinon code_collectivite (DOM/TOM)
    dept_col = df.get("code_dept", pd.Series(dtype=str))
    coll_col = df.get("code_collectivite", pd.Series(dtype=str))
    df["geo_key"] = dept_col.where(dept_col.notna(), coll_col)

    for col in ("date_naissance", "date_debut_mandat"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


def get_senateurs() -> pd.DataFrame:
    """Retourne les sénateurs (cache 24 h)."""
    cached = load("senateurs")
    if cached is not None:
        return pd.DataFrame(cached)
    records = _fetch_all(RNE_RESOURCE_IDS["senateurs"])
    df = _clean(records)
    save("senateurs", df.to_dict("records"))
    return df


def get_deputes() -> pd.DataFrame:
    """Retourne les députés (cache 24 h)."""
    cached = load("deputes")
    if cached is not None:
        return pd.DataFrame(cached)
    records = _fetch_all(RNE_RESOURCE_IDS["deputes"])
    df = _clean(records, extra_cols=_COL_DEPUTE)
    save("deputes", df.to_dict("records"))
    return df


def get_parlementaires() -> pd.DataFrame:
    """Sénateurs + Députés fusionnés avec colonne `chambre`."""
    sen = get_senateurs().assign(chambre="Sénat")
    dep = get_deputes().assign(chambre="Assemblée nationale")
    return pd.concat([sen, dep], ignore_index=True)
