"""
Scoring de pertinence TF-IDF — Python pur (stdlib uniquement, pas de
sklearn/scipy qui dépasseraient la limite de taille de la fonction serverless).

Améliore la recherche DOLE par rapport au simple AND-contains :
  - insensible aux accents ("energie" trouve "énergie")
  - expansion par préfixe ("décarbon" trouve "décarbonation")
  - tri par pertinence (TF-IDF × cosinus) au lieu d'un ordre arbitraire

Le corpus étant figé entre deux rafraîchissements du cache, l'index est
construit une fois puis mémoïsé par l'appelant (voir api_dole).
"""
import math
import re
import unicodedata
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9]{2,}")

# Stop-words français minimaux — uniquement des mots-outils, pas de vocabulaire métier
_STOPWORDS = frozenset(
    "le la les de des du un une et en au aux pour sur dans par avec sans sous "
    "ce cette ces cet qui que quoi dont ou où il elle on nous vous ils elles "
    "se sa son ses leur leurs ne pas plus est sont etre avoir a d l n s c j qu "
    "meme aussi tout tous toute toutes autre autres entre vers chez apres avant".split()
)


def _fold(text: str) -> str:
    """Minuscule + suppression des accents (é→e)."""
    nfkd = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(_fold(text)) if t not in _STOPWORDS]


class IndexPertinence:
    """Index TF-IDF sur une liste de documents (dictionnaires terme → poids)."""

    def __init__(self, documents: list[str]):
        self.n_docs = len(documents)
        doc_tokens = [tokenize(doc) for doc in documents]

        df_counts: Counter = Counter()
        for tokens in doc_tokens:
            df_counts.update(set(tokens))
        self._idf = {
            term: math.log((1 + self.n_docs) / (1 + df)) + 1.0
            for term, df in df_counts.items()
        }

        self._vectors: list[dict[str, float]] = []
        self._norms: list[float] = []
        for tokens in doc_tokens:
            if not tokens:
                self._vectors.append({})
                self._norms.append(0.0)
                continue
            counts = Counter(tokens)
            vec = {t: (c / len(tokens)) * self._idf[t] for t, c in counts.items()}
            self._vectors.append(vec)
            self._norms.append(math.sqrt(sum(w * w for w in vec.values())))

    def _expand(self, term: str) -> list[str]:
        """
        Terme exact + termes du corpus qui le préfixent (dès 4 caractères) :
        "agro" doit rapporter "agroalimentaire" même si "agro" est aussi un
        token du corpus, sinon les requêtes courtes ratent l'essentiel.
        """
        exact = [term] if term in self._idf else []
        if len(term) < 4:
            return exact
        return exact + [t for t in self._idf if t != term and t.startswith(term)]

    def scores(self, query: str) -> list[float]:
        """Score cosinus TF-IDF de chaque document pour la requête (0 si aucun terme)."""
        terms: list[str] = []
        for tok in tokenize(query):
            terms.extend(self._expand(tok))
        if not terms:
            return [0.0] * self.n_docs

        counts = Counter(terms)
        q_vec = {t: (c / len(terms)) * self._idf[t] for t, c in counts.items()}
        q_norm = math.sqrt(sum(w * w for w in q_vec.values()))
        if q_norm == 0:
            return [0.0] * self.n_docs

        out: list[float] = []
        for vec, norm in zip(self._vectors, self._norms):
            if norm == 0:
                out.append(0.0)
                continue
            dot = sum(w * vec[t] for t, w in q_vec.items() if t in vec)
            out.append(dot / (q_norm * norm))
        return out
