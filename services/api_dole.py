"""
DOLE — Dossiers législatifs vectorisés.
Source : AgentPublic/dole sur HuggingFace (via datasets-server API).

4 343 chunks de textes législatifs (lois publiées, projets, propositions).
Recherche par mots-clés sur titre + texte — sans embeddings, sans LLM.
"""
import time
import requests
import pandas as pd
from utils.cache import get, set as cache_set

_HF_URL = "https://datasets-server.huggingface.co/rows"
_HF_PARAMS_BASE = {
    "dataset": "AgentPublic/dole",
    "config": "latest",
    "split": "train",
}
_PAGE_SIZE = 100   # max autorisé par l'API HuggingFace datasets-server

# Colonnes conservées (on exclut les embeddings ~2 ko par ligne)
_KEEP_COLS = [
    "doc_id", "chunk_id", "chunk_index",
    "category", "content_type",
    "title", "number", "wording",
    "creation_date",
    "article_number", "article_title", "article_synthesis",
    "chunk_text",
]

_CATEGORY_LABEL = {
    "LOI_PUBLIEE":       "Loi publiée",
    "ORDONNANCE_PUBLIEE":"Ordonnance publiée",
    "PROJET_LOI":        "Projet de loi",
    "PROPOSITION_LOI":   "Proposition de loi",
    "PROJET_ORDONNANCE": "Projet d'ordonnance",
}


def _fetch_all() -> pd.DataFrame:
    """Télécharge tous les chunks DOLE (sans embeddings), retourne un DataFrame."""
    records: list[dict] = []
    offset = 0
    while True:
        for attempt in range(5):
            resp = requests.get(
                _HF_URL,
                params={**_HF_PARAMS_BASE, "offset": offset, "length": _PAGE_SIZE},
                timeout=30,
            )
            if resp.status_code in (502, 503, 429):
                time.sleep(5 * (attempt + 1))
                continue
            break
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("rows", [])
        if not batch:
            break
        for item in batch:
            row = item["row"]
            records.append({k: row.get(k) for k in _KEEP_COLS})
        offset += len(batch)
        if len(batch) < _PAGE_SIZE:
            break
        time.sleep(0.5)   # délai entre pages pour éviter le rate-limit

    df = pd.DataFrame(records)
    if "creation_date" in df.columns:
        df["creation_date"] = pd.to_datetime(df["creation_date"], errors="coerce")
    return df


def get_dole() -> pd.DataFrame:
    """
    Retourne tous les textes DOLE, depuis le cache ou HuggingFace.
    Cache 24h (les données évoluent peu).
    """
    cached = get("dole")
    if cached is not None:
        df = pd.DataFrame(cached)
        df["creation_date"] = pd.to_datetime(df["creation_date"], errors="coerce")
        return df
    df = _fetch_all()
    cache_set("dole", df.to_dict("records"))
    return df


def rechercher_textes(
    query: str,
    categories: list[str] | None = None,
    annee_min: int | None = None,
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Recherche les textes législatifs contenant les mots-clés de `query`.

    Paramètres
    ----------
    query       : mots-clés séparés par des espaces (tous doivent être présents)
    categories  : filtre sur ['LOI_PUBLIEE', 'PROJET_LOI', 'PROPOSITION_LOI']
    annee_min   : ne retourne que les textes à partir de cette année
    top_n       : nombre maximum de résultats

    Retourne
    --------
    DataFrame avec colonnes : title, category_label, creation_date,
                              article_title, article_synthesis, chunk_text, doc_id
    """
    df = get_dole()

    # Filtre catégorie
    if categories:
        df = df[df["category"].isin(categories)]

    # Filtre année
    if annee_min:
        df = df[df["creation_date"].dt.year >= annee_min]

    # Recherche mots-clés (tous les termes doivent être présents — ET implicite)
    # On cherche dans title + chunk_text, insensible à la casse
    mots = [m.strip() for m in query.lower().split() if m.strip()]
    if not mots:
        return pd.DataFrame()

    search_corpus = (
        df["title"].fillna("").str.lower()
        + " "
        + df["chunk_text"].fillna("").str.lower()
    )
    mask = pd.Series(True, index=df.index)
    for mot in mots:
        mask = mask & search_corpus.str.contains(mot, regex=False, na=False)

    results = df[mask].copy()

    # Dédoublonnage par doc_id : on garde le chunk le plus pertinent (chunk_index=1)
    results = (
        results.sort_values("chunk_index")
        .drop_duplicates(subset="doc_id", keep="first")
        .head(top_n)
    )

    results["category_label"] = results["category"].map(_CATEGORY_LABEL).fillna(results["category"])
    results["annee"] = results["creation_date"].dt.year

    return results[[
        "title", "category_label", "annee",
        "article_title", "article_synthesis",
        "chunk_text", "doc_id",
    ]].reset_index(drop=True)
