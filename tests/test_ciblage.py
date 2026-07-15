"""Tests du ciblage (services/ciblage.py) — fiches et CRM mockés, aucun réseau."""
from datetime import date, timedelta

import pytest

from services import ciblage


def _fiche(nom: str, prenom: str, effectifs: int, chambre: str = "Sénat") -> dict:
    return {
        "parlementaire": {"nom": nom, "prenom": prenom, "chambre": chambre,
                          "code_dept": "69", "libelle_dept": "Rhône"},
        "territoire": {"nb_etablissements_industriels": 10,
                       "effectifs_estimes": effectifs, "top_naf": [], "top_employeurs": []},
    }


@pytest.fixture(autouse=True)
def sans_reseau(monkeypatch):
    """Par défaut : deux fiches, CRM vide, activité jamais interrogée."""
    monkeypatch.setattr(
        ciblage, "rechercher_parlementaire",
        lambda query, limit=20, chambre=None: [
            _fiche("Grand", "Anne", 10_000), _fiche("Petit", "Bob", 1_000),
        ],
    )
    monkeypatch.setattr(ciblage, "resume_engagement", lambda: {})

    def _pas_de_reseau(*args, **kwargs):
        raise AssertionError("get_activite ne doit pas être appelé sans avec_activite=True")
    monkeypatch.setattr(ciblage, "get_activite", _pas_de_reseau)


def test_plus_gros_territoire_en_premier():
    """À fraîcheur égale (jamais contactés), le plus gros territoire gagne."""
    cibles = ciblage.cibles_departement("69")
    assert [c["parlementaire"]["nom"] for c in cibles] == ["Grand", "Petit"]
    # Score max : 45 (industrie) + 9 (activité inconnue 0.3×30) + 25 (fraîcheur) = 79
    assert cibles[0]["score"] == 79.0
    assert cibles[0]["detail_score"]["motif_fraicheur"] == "jamais contacté"
    assert cibles[0]["statut"] == "a_contacter"


def test_contact_recent_fait_chuter_la_priorite(monkeypatch):
    """Contact d'hier réduit la fraîcheur, mais l'industrie reste dominante (45%)."""
    hier = (date.today() - timedelta(days=1)).isoformat()
    monkeypatch.setattr(ciblage, "resume_engagement", lambda: {
        "anne grand": {"statut": "contacte", "nb_interactions": 1, "dernier_contact": hier},
    })
    cibles = ciblage.cibles_departement("69")
    # Grand territoire reste d'abord (industrie = 45%)
    assert cibles[0]["parlementaire"]["nom"] == "Grand"
    grand = cibles[0]
    assert grand["nb_interactions"] == 1
    assert grand["dernier_contact"] == hier
    assert grand["detail_score"]["motif_fraicheur"] == "contacté il y a 1 j"
    # 1/90 × 0.6 → composante fraîcheur réduite à ~0.7/100
    assert grand["detail_score"]["fraicheur"] == pytest.approx(0.7, abs=0.05)
    # Mais le score global baisse par rapport à jamais-contacté (79 → ~55)
    assert grand["score"] < 75.0


def test_relance_apres_90_jours(monkeypatch):
    """Au-delà de 90 jours, l'élu contacté redevient prioritaire (0.9)."""
    ancien = (date.today() - timedelta(days=120)).isoformat()
    monkeypatch.setattr(ciblage, "resume_engagement", lambda: {
        "anne grand": {"statut": "allie", "nb_interactions": 3, "dernier_contact": ancien},
    })
    cibles = ciblage.cibles_departement("69")
    # Le gros territoire reste premier : la relance (90) bat presque le jamais-contacté (100)
    assert cibles[0]["parlementaire"]["nom"] == "Grand"
    assert cibles[0]["detail_score"]["fraicheur"] == 90.0
    assert cibles[0]["detail_score"]["motif_fraicheur"] == "contacté il y a 120 j"
    assert cibles[0]["statut"] == "allie"


def test_liste_vide(monkeypatch):
    monkeypatch.setattr(ciblage, "rechercher_parlementaire",
                        lambda query, limit=20, chambre=None: [])
    assert ciblage.cibles_departement("999") == []


def test_avec_activite(monkeypatch):
    """avec_activite=True interroge la source et pondère le score."""
    monkeypatch.setattr(ciblage, "get_activite", lambda nom, prenom, chambre: {
        "amendements_proposes": 80, "questions_ecrites": 15, "questions_orales": 5,
    } if nom == "Grand" else None)
    cibles = ciblage.cibles_departement("69", avec_activite=True)
    grand = next(c for c in cibles if c["parlementaire"]["nom"] == "Grand")
    petit = next(c for c in cibles if c["parlementaire"]["nom"] == "Petit")
    assert grand["detail_score"]["activite"] == 50.0   # 100/200
    assert petit["detail_score"]["activite"] == 30.0   # élu non référencé → neutre


def test_paliers_score_activite():
    assert ciblage._score_activite(None) == 0.3
    assert ciblage._score_activite({}) == 0.0
    assert ciblage._score_activite({"amendements_proposes": 100}) == 0.5
    assert ciblage._score_activite({"amendements_proposes": 150,
                                    "questions_ecrites": 50}) == 1.0
    assert ciblage._score_activite({"amendements_proposes": 999}) == 1.0  # plafonné
    # Valeurs None dans le record → traitées comme 0
    assert ciblage._score_activite({"amendements_proposes": None,
                                    "questions_ecrites": 20}) == 0.1
