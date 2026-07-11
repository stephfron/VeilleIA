"""
Cache fichier JSON — TTL 24 h par défaut.
Les données brutes sont écrites dans data/raw/<key>.json (ou /tmp sur Vercel).

Fallback : si le cache primaire est absent ou expiré, un snapshot committé
(data/seed/<key>.json, régénérable via scripts/refresh_seed.py) est servi tel
quel — indispensable en serverless où /tmp est vidé à chaque cold start.
"""
import functools
import json
import time
from pathlib import Path
from typing import Callable, TypeVar

from utils.config import DATA_RAW_DIR, DATA_SEED_DIR, CACHE_TTL, MEMO_TTL

T = TypeVar("T")


def _cache_path(key: str) -> Path:
    return DATA_RAW_DIR / f"{key}.json"


def _json_default(obj: object) -> str:
    """Sérialise les types non natifs JSON (pd.Timestamp, datetime, date…)."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()  # type: ignore[union-attr]
    raise TypeError(f"Type non sérialisable : {type(obj)}")


def load(key: str, ttl: int = CACHE_TTL) -> list | dict | None:
    """
    Charge une entrée du cache primaire, sinon le seed committé, sinon None.
    Le primaire est soumis au TTL ; le seed est servi sans condition d'âge
    (données quasi statiques, rafraîchies à chaque déploiement).
    """
    path = _cache_path(key)
    if path.exists() and time.time() - path.stat().st_mtime <= ttl:
        return json.loads(path.read_text(encoding="utf-8"))

    seed = DATA_SEED_DIR / f"{key}.json"
    if seed.exists():
        return json.loads(seed.read_text(encoding="utf-8"))
    return None


def save(key: str, data: list | dict) -> None:
    """Persiste data dans le cache (crée le répertoire si nécessaire)."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(key).write_text(
        json.dumps(data, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )


def memoize(ttl: int = MEMO_TTL) -> Callable[[Callable[[], T]], Callable[[], T]]:
    """
    Mémoïse en RAM le résultat d'une fonction sans argument (DataFrame parsé…)
    pour la durée de vie de l'instance. Évite de relire/reparser le JSON du
    cache fichier à chaque requête — le gros du coût sur les recherches DOLE.
    """
    def decorator(fn: Callable[[], T]) -> Callable[[], T]:
        state: dict = {}

        @functools.wraps(fn)
        def wrapper() -> T:
            now = time.time()
            if "value" in state and now - state["at"] <= ttl:
                return state["value"]
            state["value"] = fn()
            state["at"] = now
            return state["value"]

        wrapper.cache_clear = state.clear  # type: ignore[attr-defined]
        return wrapper

    return decorator
