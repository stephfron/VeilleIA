"""Tests de l'API FastAPI — services mockés, aucun appel réseau."""
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend import app as main


@pytest.fixture()
def client() -> TestClient:
    return TestClient(main.app)


FICHE = {
    "parlementaire": {
        "nom": "Dupont", "prenom": "Marie", "chambre": "Sénat",
        "sexe": "F", "code_dept": "69", "libelle_dept": "Rhône",
        "date_debut_mandat": "01/10/2023", "libelle_csp": float("nan"),
    },
    "territoire": {
        "nb_etablissements_industriels": 120,
        "effectifs_estimes": 4500,
        "top_naf": [{"naf": "25.62B", "nb": 30}],
    },
}


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_categories(client):
    body = client.get("/api/categories").json()
    assert body["LOI_PUBLIEE"] == "Loi publiée"


def test_parlementaires_nan_becomes_null(client, monkeypatch):
    monkeypatch.setattr(main, "rechercher_parlementaire", lambda q, limit=20: [FICHE])
    body = client.get("/api/parlementaires", params={"q": "dupont"}).json()
    assert body["count"] == 1
    assert body["results"][0]["parlementaire"]["libelle_csp"] is None
    assert body["results"][0]["territoire"]["top_naf"] == [{"naf": "25.62B", "nb": 30}]


def test_parlementaires_filtre_chambre(client, monkeypatch):
    autre = {**FICHE, "parlementaire": {**FICHE["parlementaire"], "chambre": "Assemblée nationale"}}
    monkeypatch.setattr(main, "rechercher_parlementaire", lambda q, limit=20: [FICHE, autre])
    body = client.get("/api/parlementaires", params={"q": "dupont", "chambre": "Sénat"}).json()
    assert body["count"] == 1
    assert body["results"][0]["parlementaire"]["chambre"] == "Sénat"


def test_parlementaires_chambre_invalide(client):
    resp = client.get("/api/parlementaires", params={"q": "x", "chambre": "Congrès"})
    assert resp.status_code == 422


def test_parlementaires_query_vide(client):
    assert client.get("/api/parlementaires", params={"q": ""}).status_code == 422


def test_parlementaires_service_down(client, monkeypatch):
    def boom(q, limit=20):
        raise RuntimeError("réseau KO")
    monkeypatch.setattr(main, "rechercher_parlementaire", boom)
    resp = client.get("/api/parlementaires", params={"q": "dupont"})
    assert resp.status_code == 502


def test_textes_ok(client, monkeypatch):
    df = pd.DataFrame([
        {"title": "Loi industrie verte", "category_label": "Loi publiée", "annee": 2023,
         "article_title": None, "article_synthesis": "Synthèse.", "chunk_text": "…", "doc_id": "d1"},
        {"title": "Proposition acier", "category_label": "Proposition de loi", "annee": 2024,
         "article_title": None, "article_synthesis": None, "chunk_text": "…", "doc_id": "d2"},
    ])
    monkeypatch.setattr(main, "rechercher_textes", lambda q, categories, annee_min: df)
    body = client.get("/api/textes", params={"q": "industrie"}).json()
    assert body["count"] == 2
    assert body["par_annee"] == {"2023": 1, "2024": 1}
    assert body["results"][1]["article_synthesis"] is None


def test_textes_vide(client, monkeypatch):
    monkeypatch.setattr(main, "rechercher_textes", lambda q, categories, annee_min: pd.DataFrame())
    body = client.get("/api/textes", params={"q": "zzz"}).json()
    assert body == {"count": 0, "results": [], "par_annee": {}}


def test_textes_categorie_inconnue(client):
    resp = client.get("/api/textes", params={"q": "x", "categories": ["FAKE_CAT"]})
    assert resp.status_code == 422
