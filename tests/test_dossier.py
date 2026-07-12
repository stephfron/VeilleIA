"""Tests de services/dossier.py — assemblage du contexte pour la future IA."""
import pandas as pd

from services import dossier


FICHE = {
    "parlementaire": {"nom": "Dupont", "prenom": "Jean", "chambre": "Sénat",
                      "code_dept": "69", "libelle_dept": "Rhône",
                      "date_debut_mandat": None, "sexe": "M", "libelle_csp": None},
    "territoire": {"nb_etablissements_industriels": 10, "effectifs_estimes": 500,
                   "top_naf": [], "top_employeurs": []},
}

ACTIVITE = {"groupe_sigle": "GRP", "amendements_proposes": 5}

TEXTES = pd.DataFrame([{
    "title": "Loi industrie verte", "category_label": "Loi publiée", "annee": 2023,
    "article_title": None, "article_synthesis": "Synthèse.", "chunk_text": "…",
    "doc_id": "d1", "score": 0.8,
}])


def _patch_all(monkeypatch, fiche=FICHE, activite=ACTIVITE, textes=TEXTES):
    monkeypatch.setattr(dossier, "fiche_par_identite", lambda nom, prenom: fiche)
    monkeypatch.setattr(dossier, "get_activite", lambda nom, prenom, chambre: activite)
    monkeypatch.setattr(dossier, "rechercher_textes",
                        lambda q, top_n=5, annee_min=None: textes)


def test_constituer_dossier_assemble_tout(monkeypatch):
    _patch_all(monkeypatch)
    d = dossier.constituer_dossier("Dupont", "Jean")
    assert d is not None
    assert d["parlementaire"]["nom"] == "Dupont"
    assert d["activite_legislative"]["groupe_sigle"] == "GRP"
    assert d["textes_pertinents"][0]["title"] == "Loi industrie verte"
    assert d["synthese"] is None
    assert d["synthese_status"] == "non_implementee"


def test_constituer_dossier_introuvable(monkeypatch):
    _patch_all(monkeypatch, fiche=None)
    assert dossier.constituer_dossier("Inconnu", "Personne") is None


def test_constituer_dossier_activite_indisponible(monkeypatch):
    _patch_all(monkeypatch, activite=None)
    d = dossier.constituer_dossier("Dupont", "Jean")
    assert d["activite_legislative"] is None


def test_constituer_dossier_textes_vides(monkeypatch):
    _patch_all(monkeypatch, textes=pd.DataFrame())
    d = dossier.constituer_dossier("Dupont", "Jean")
    assert d["textes_pertinents"] == []
