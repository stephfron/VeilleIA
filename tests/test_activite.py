"""Tests de services/api_activite.py — index et matching, sans réseau."""
import pytest

from services import api_activite


RECORDS_AN = [
    {"nom": "Jean Dupont", "prenom": "Jean", "nom_de_famille": "Dupont",
     "groupe_sigle": "GRP", "amendements_proposes": 12, "amendements_signes": 40,
     "amendements_adoptes": 3, "questions_ecrites": 25, "questions_orales": 2,
     "rapports": 1, "interventions": 150, "semaines_presence": 30, "slug": "jean-dupont"},
]


@pytest.fixture(autouse=True)
def _reset_memo():
    api_activite._index_memo.clear()
    yield
    api_activite._index_memo.clear()


def _patch_sources(monkeypatch, an=None, senat=None):
    def fake_fetch(chambre):
        return an if chambre == "Assemblée nationale" else senat
    monkeypatch.setattr(api_activite, "_fetch_synthese", fake_fetch)


def test_get_activite_match_insensible_casse_et_accents(monkeypatch):
    _patch_sources(monkeypatch, an=RECORDS_AN)
    result = api_activite.get_activite("DUPONT", "Jean", "Assemblée nationale")
    assert result is not None
    assert result["groupe_sigle"] == "GRP"
    assert result["amendements_proposes"] == 12
    assert result["source_url"] == "https://www.nosdeputes.fr/jean-dupont"


def test_get_activite_introuvable_retourne_none(monkeypatch):
    _patch_sources(monkeypatch, an=RECORDS_AN)
    assert api_activite.get_activite("Martin", "Paul", "Assemblée nationale") is None


def test_get_activite_source_ko_retourne_none(monkeypatch):
    _patch_sources(monkeypatch, an=None, senat=None)
    assert api_activite.get_activite("Dupont", "Jean", "Assemblée nationale") is None


def test_get_activite_chambre_inconnue():
    assert api_activite.get_activite("Dupont", "Jean", "Congrès") is None


def test_echec_retente_apres_ttl_court(monkeypatch):
    """Un échec ne doit pas être mémorisé 1 h : nouvel essai après _ECHEC_TTL."""
    appels = {"n": 0}

    def fake_fetch(chambre):
        appels["n"] += 1
        return None if appels["n"] == 1 else RECORDS_AN

    monkeypatch.setattr(api_activite, "_fetch_synthese", fake_fetch)

    assert api_activite.get_activite("Dupont", "Jean", "Assemblée nationale") is None
    # dans la fenêtre d'échec : pas de refetch
    assert api_activite.get_activite("Dupont", "Jean", "Assemblée nationale") is None
    assert appels["n"] == 1
    # fenêtre expirée : refetch et succès
    exp, val = api_activite._index_memo["Assemblée nationale"]
    api_activite._index_memo["Assemblée nationale"] = (0.0, val)
    assert api_activite.get_activite("Dupont", "Jean", "Assemblée nationale") is not None
    assert appels["n"] == 2


def test_chambre_non_demandee_jamais_chargee(monkeypatch):
    """Question sur un député → le Sénat ne doit pas être fetché (chargement paresseux)."""
    chambres_vues = []

    def fake_fetch(chambre):
        chambres_vues.append(chambre)
        return RECORDS_AN

    monkeypatch.setattr(api_activite, "_fetch_synthese", fake_fetch)
    api_activite.get_activite("Dupont", "Jean", "Assemblée nationale")
    assert chambres_vues == ["Assemblée nationale"]
