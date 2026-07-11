"""
Configuration centrale — toutes les constantes et variables d'environnement.
Importer depuis ici, jamais directement depuis os.getenv dans les services.
"""
import os
from pathlib import Path


def _get_secret(key: str, default: str = "") -> str:
    """Lit une variable de config depuis l'environnement (.env chargé par l'API)."""
    return os.getenv(key) or default

# ---------------------------------------------------------------------------
# Répertoires
# Sur Vercel (env VERCEL=1) le filesystem est en lecture seule sauf /tmp :
# le cache y est éphémère (perdu à chaque cold start) mais fonctionnel.
# Surchargeable via DATA_RAW_DIR dans tous les environnements.
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent.parent
_DEFAULT_RAW = Path("/tmp/veilleia/raw") if os.getenv("VERCEL") else ROOT_DIR / "data" / "raw"
DATA_RAW_DIR = Path(_get_secret("DATA_RAW_DIR", str(_DEFAULT_RAW)))
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
# Snapshot committé (RNE + DOLE) servi quand le cache est vide — évite de
# repayer les téléchargements à chaque cold start serverless.
DATA_SEED_DIR = ROOT_DIR / "data" / "seed"

# ---------------------------------------------------------------------------
# Mémoïsation en RAM des DataFrames parsés (instance serverless chaude)
# ---------------------------------------------------------------------------
MEMO_TTL: int = 3_600           # 1 h en secondes

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
CACHE_TTL: int = 86_400          # 24 h en secondes

# ---------------------------------------------------------------------------
# RNE — API tabulaire data.gouv.fr
# ---------------------------------------------------------------------------
RNE_BASE_URL: str = "https://tabular-api.data.gouv.fr/api/resources/{}/data/"
RNE_PAGE_SIZE: int = 100
RNE_RESOURCE_IDS: dict[str, str] = {
    "senateurs": "b78f8945-509f-4609-a4a7-3048b8370479",
    "deputes":   "1ac42ff4-1336-44f8-a221-832039dbc142",
}

# ---------------------------------------------------------------------------
# INSEE SIRENE — api.insee.fr
# ---------------------------------------------------------------------------
SIRENE_BASE_URL: str = "https://api.insee.fr/api-sirene/3.11/siret"
SIRENE_API_KEY: str = _get_secret("INSEE_SIRENE_API_KEY")
SIRENE_PAGE_SIZE: int = 1_000
SIRENE_MAX_OFFSET: int = 9_000   # L'API bloque au-delà de 10 000 résultats / requête
SIRENE_DELAY: float = 1.0        # Délai entre pages (évite le rate-limit)
SIRENE_RETRY_DELAY: float = 10.0 # Attente après un 429

# Sections NAF industrie (B + C) — préfixes utilisés pour les requêtes Lucene
SIRENE_NAF_PREFIXES: list[str] = [
    "05", "06", "07", "08", "09",   # Section B — Industries extractives
    "1", "2",                        # Section C 10–29 (deux appels larges)
    "30", "31", "32", "33",          # Section C 30–33
]

# Midpoints salariés par tranche INSEE (estimation)
SIRENE_TRANCHE_MIDPOINT: dict[str, int] = {
    "NN": 0,  "00": 0,  "01": 1,  "02": 4,   "03": 7,
    "11": 14, "12": 34, "21": 74, "22": 149,
    "31": 224, "32": 374, "41": 749, "42": 1_499,
    "51": 3_499, "52": 7_499, "53": 15_000,
}

# ---------------------------------------------------------------------------
# DOLE — HuggingFace datasets-server (AgentPublic/dole)
# ---------------------------------------------------------------------------
DOLE_HF_URL: str = "https://datasets-server.huggingface.co/rows"
DOLE_HF_DATASET: str = "AgentPublic/dole"
DOLE_HF_CONFIG: str = "latest"
DOLE_PAGE_SIZE: int = 100
DOLE_PAGE_DELAY: float = 0.5     # Délai entre pages HF

