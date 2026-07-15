"""Tests du service formations (services/api_onisep.py) — API mockée, aucun réseau."""
import pytest

from services import api_onisep


def _formation(titre: str, etablissement: str) -> dict:
    return {
        "titre": titre,
        "url_descriptif": "https://example.com",
        "etablissement": etablissement,
        "type": "CAP",
        "localite": "Lyon",
    }


@pytest.fixture(autouse=True)
def sans_reseau(monkeypatch):
    """Par défaut : formations mockées, pas de réseau."""
    monkeypatch.setattr(
        api_onisep, "get_formations",
        lambda code_dept: [
            _formation("CAP Tournage", "Lycée A"),
            _formation("Bac Pro Usinage", "Lycée B"),
        ] if code_dept == "69" else []
    )


def test_formations_dept_69():
    """Département 69 retourne deux formations."""
    formations = api_onisep.get_formations("69")
    assert formations is not None
    assert len(formations) == 2
    assert formations[0]["titre"] == "CAP Tournage"
    assert formations[0]["etablissement"] == "Lycée A"


def test_formations_dept_absent():
    """Département sans formations retourne liste vide."""
    formations = api_onisep.get_formations("999")
    assert formations == []


def test_formations_none_si_source_indisponible(monkeypatch):
    """Source indisponible retourne None."""
    monkeypatch.setattr(api_onisep, "get_formations", lambda code_dept: None)
    result = api_onisep.get_formations("69")
    assert result is None
