"""Tests de rechercher_textes avec corpus mocké — dédup, tri, filtres."""
import pandas as pd
import pytest

from services import api_dole


CORPUS = pd.DataFrame([
    {"doc_id": "d1", "chunk_index": 0, "category": "LOI_PUBLIEE",
     "title": "Loi industrie verte", "chunk_text": "décarbonation des usines industrielles",
     "creation_date": pd.Timestamp("2023-05-01"), "article_title": None,
     "article_synthesis": None, "number": None, "wording": None, "content_type": None,
     "chunk_id": "c1"},
    {"doc_id": "d1", "chunk_index": 1, "category": "LOI_PUBLIEE",
     "title": "Loi industrie verte", "chunk_text": "dispositions diverses",
     "creation_date": pd.Timestamp("2023-05-01"), "article_title": None,
     "article_synthesis": None, "number": None, "wording": None, "content_type": None,
     "chunk_id": "c2"},
    {"doc_id": "d2", "chunk_index": 0, "category": "PROJET_LOI",
     "title": "Projet de loi finances", "chunk_text": "budget de l'État",
     "creation_date": pd.Timestamp("1995-01-01"), "article_title": None,
     "article_synthesis": None, "number": None, "wording": None, "content_type": None,
     "chunk_id": "c3"},
])


@pytest.fixture(autouse=True)
def _mock_corpus(monkeypatch):
    monkeypatch.setattr(api_dole, "get_dole", lambda: CORPUS)
    api_dole._index_pertinence.cache_clear()
    yield
    api_dole._index_pertinence.cache_clear()


def test_dedoublonne_par_doc_id_et_score_positif_seulement():
    r = api_dole.rechercher_textes("industrie décarbonation")
    assert list(r["doc_id"]) == ["d1"]          # un seul dossier, pas deux chunks
    assert (r["score"] > 0).all()               # le doc finances (score 0) est exclu


def test_filtre_annee_min():
    r = api_dole.rechercher_textes("loi", annee_min=2000)
    assert set(r["doc_id"]) <= {"d1"}


def test_filtre_categorie():
    r = api_dole.rechercher_textes("loi", categories=["PROJET_LOI"])
    assert set(r["doc_id"]) <= {"d2"}


def test_requete_vide_dataframe_vide():
    assert api_dole.rechercher_textes("   ").empty


def test_expansion_prefixe_inclut_terme_exact():
    # "industrie" est un token ET un préfixe d'"industrielles" — les deux comptent
    r = api_dole.rechercher_textes("industrie")
    assert list(r["doc_id"]) == ["d1"]