"""Tests du moteur de pertinence TF-IDF (services/pertinence.py)."""
from services.pertinence import IndexPertinence, tokenize


CORPUS = [
    "Loi relative à l'industrie verte et à la décarbonation des usines",
    "Ordonnance sur la simplification administrative des collectivités",
    "Proposition de loi pour l'industrie automobile et les batteries électriques",
    "Loi de finances pour 2024",
]


def test_tokenize_supprime_accents_et_stopwords():
    tokens = tokenize("L'Énergie DÉCARBONÉE et la loi")
    assert "energie" in tokens
    assert "decarbonee" in tokens
    assert "et" not in tokens
    assert "la" not in tokens


def test_document_pertinent_score_le_plus_haut():
    index = IndexPertinence(CORPUS)
    scores = index.scores("industrie automobile")
    assert scores.index(max(scores)) == 2  # le doc automobile devant le doc industrie verte
    assert scores[0] > 0                    # "industrie" matche aussi le doc 0
    assert scores[1] == 0                   # aucun terme commun
    assert scores[3] == 0


def test_insensible_aux_accents():
    index = IndexPertinence(CORPUS)
    assert index.scores("decarbonation")[0] > 0  # trouve "décarbonation"


def test_expansion_par_prefixe():
    index = IndexPertinence(CORPUS)
    scores = index.scores("décarbon")  # préfixe absent du vocabulaire
    assert scores[0] > 0


def test_requete_sans_terme_connu_scores_nuls():
    index = IndexPertinence(CORPUS)
    assert all(s == 0 for s in index.scores("zzz xyzabc"))


def test_document_vide_score_nul():
    index = IndexPertinence(["", "industrie"])
    scores = index.scores("industrie")
    assert scores[0] == 0
    assert scores[1] > 0
