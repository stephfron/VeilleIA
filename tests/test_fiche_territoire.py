import pandas as pd

from services.fiche_territoire import _geo_key, _mask, rechercher_parlementaire


def _df():
    return pd.DataFrame([
        {"nom": "Dupont", "prenom": "Alice", "chambre": "Sénat",
         "code_dept": "75", "geo_key": "75", "libelle_dept": "Paris"},
        {"nom": "Martin", "prenom": "Bob", "chambre": "Assemblée nationale",
         "code_dept": "69", "geo_key": "69", "libelle_dept": "Rhône"},
        {"nom": "Curie", "prenom": "Marie", "chambre": "Sénat",
         "code_dept": None, "geo_key": "971", "libelle_dept": "Guadeloupe"},
    ])


def test_mask_matches_by_nom_case_insensitive():
    df = _df()
    assert list(df[_mask(df, "dupont")]["nom"]) == ["Dupont"]


def test_mask_matches_by_prenom_partial():
    df = _df()
    assert list(df[_mask(df, "ali")]["nom"]) == ["Dupont"]


def test_mask_matches_by_code_dept_exact():
    df = _df()
    assert list(df[_mask(df, "69")]["nom"]) == ["Martin"]


def test_mask_matches_by_libelle_dept_partial():
    df = _df()
    assert list(df[_mask(df, "guadeloupe")]["nom"]) == ["Curie"]


def test_mask_no_match_returns_empty():
    df = _df()
    assert df[_mask(df, "introuvable")].empty


def test_geo_key_prefers_geo_key_over_code_dept():
    row = pd.Series({"geo_key": "971", "code_dept": None})
    assert _geo_key(row) == "971"


def test_geo_key_falls_back_to_code_dept():
    row = pd.Series({"geo_key": None, "code_dept": "75"})
    assert _geo_key(row) == "75"


def test_geo_key_none_when_both_missing():
    row = pd.Series({"geo_key": None, "code_dept": float("nan")})
    assert _geo_key(row) is None


def test_rechercher_parlementaire_builds_fiche(monkeypatch):
    monkeypatch.setattr("services.fiche_territoire.get_parlementaires", lambda: _df())
    monkeypatch.setattr(
        "services.fiche_territoire.resume_industrie_dept",
        lambda code_dept: {"nb_etablissements": 42, "effectifs_estimes_total": 100, "top_naf": []},
    )

    fiches = rechercher_parlementaire("Dupont")

    assert len(fiches) == 1
    assert fiches[0]["parlementaire"]["nom"] == "Dupont"
    assert fiches[0]["territoire"]["nb_etablissements_industriels"] == 42


def test_rechercher_parlementaire_no_match_returns_empty_list(monkeypatch):
    monkeypatch.setattr("services.fiche_territoire.get_parlementaires", lambda: _df())
    assert rechercher_parlementaire("introuvable") == []


def test_rechercher_parlementaire_respecte_limit(monkeypatch):
    monkeypatch.setattr("services.fiche_territoire.get_parlementaires", lambda: _df())
    appels = []

    def fake_resume(code_dept):
        appels.append(code_dept)
        return {"nb_etablissements": 0, "effectifs_estimes_total": 0, "top_naf": []}

    monkeypatch.setattr("services.fiche_territoire.resume_industrie_dept", fake_resume)

    fiches = rechercher_parlementaire("a", limit=2)  # "a" matche les 3 élus du jeu

    assert len(fiches) == 2
    assert len(appels) == 2  # les fetchs SIRENE au-delà de limit ne partent pas
