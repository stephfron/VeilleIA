"""
DOLE — Dossiers législatifs vectorisés.
Source : AgentPublic/dole sur HuggingFace (datasets-server API).

3 573 dossiers / 4 343 chunks — lois publiées, ordonnances, projets, propositions.
Recherche par mots-clés sur titre + texte (ET implicite). Sans LLM, sans embeddings.
"""
import time
import pandas as pd
from utils.cache import load, save
from utils.config import (
    DOLE_HF_URL, DOLE_HF_DATASET, DOLE_HF_CONFIG,
    DOLE_PAGE_SIZE, DOLE_PAGE_DELAY,
)
from utils.http import get_with_retry

_KEEP_COLS = [
    "doc_id", "chunk_id", "chunk_index",
    "category", "content_type",
    "title", "number", "wording",
    "creation_date",
    "article_number", "article_title", "article_synthesis",
    "chunk_text",
]

CATEGORY_LABEL: dict[str, str] = {
    "LOI_PUBLIEE":       "Loi publiée",
    "ORDONNANCE_PUBLIEE":"Ordonnance publiée",
    "PROJET_LOI":        "Projet de loi",
    "PROPOSITION_LOI":   "Proposition de loi",
    "PROJET_ORDONNANCE": "Projet d'ordonnance",
}


def _fetch_all() -> pd.DataFrame:
    """Télécharge tous les chunks DOLE depuis HuggingFace (sans embeddings)."""
    records: list[dict] = []
    offset = 0

    while True:
        resp = get_with_retry(
            DOLE_HF_URL,
            params={
                "dataset": DOLE_HF_DATASET,
                "config":  DOLE_HF_CONFIG,
                "split":   "train",
                "offset":  offset,
                "length":  DOLE_PAGE_SIZE,
            },
            retryable=(429, 502, 503),
            base_delay=5.0,
        )
        resp.raise_for_status()

        batch = resp.json().get("rows", [])
        if not batch:
            break

        records.extend({k: row["row"].get(k) for k in _KEEP_COLS} for row in batch)
        offset += len(batch)

        if len(batch) < DOLE_PAGE_SIZE:
            break
        time.sleep(DOLE_PAGE_DELAY)

    df = pd.DataFrame(records)
    df["creation_date"] = pd.to_datetime(df["creation_date"], errors="coerce")
    return df


def get_dole() -> pd.DataFrame:
    """Retourne tous les textes DOLE (cache 24 h)."""
    cached = load("dole")
    if cached is not None:
        df = pd.DataFrame(cached)
        df["creation_date"] = pd.to_datetime(df["creation_date"], errors="coerce")
        return df
    df = _fetch_all()
    save("dole", df.to_dict("records"))
    return df


def rechercher_textes(
    query: str,
    categories: list[str] | None = None,
    annee_min: int | None = None,
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Recherche des textes législatifs par mots-clés (ET implicite entre les termes).

    Paramètres
    ----------
    query      : mots-clés libres (ex : "agroalimentaire", "industrie automobile")
    categories : filtre sur les clés de CATEGORY_LABEL
    annee_min  : année minimale de création
    top_n      : nombre max de dossiers retournés (un dossier = un doc_id)

    Retourne
    --------
    DataFrame : title, category_label, annee, article_title,
                article_synthesis, chunk_text, doc_id
    """
    df = get_dole()

    if categories:
        df = df[df["category"].isin(categories)]

    if annee_min:
        df = df[df["creation_date"].dt.year >= annee_min]

    mots = [m.strip() for m in query.lower().split() if m.strip()]
    if not mots:
        return pd.DataFrame()

    corpus = df["title"].fillna("").str.lower() + " " + df["chunk_text"].fillna("").str.lower()
    mask = pd.Series(True, index=df.index)
    for mot in mots:
        mask &= corpus.str.contains(mot, regex=False, na=False)

    results = (
        df[mask]
        .sort_values("chunk_index")
        .drop_duplicates(subset="doc_id", keep="first")
        .head(top_n)
        .copy()
    )

    results["category_label"] = results["category"].map(CATEGORY_LABEL).fillna(results["category"])
    results["annee"] = results["creation_date"].dt.year.astype("Int64")

    return results[
        ["title", "category_label", "annee", "article_title", "article_synthesis", "chunk_text", "doc_id"]
    ].reset_index(drop=True)
