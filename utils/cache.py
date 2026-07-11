"""
Cache fichier JSON — TTL 24 h par défaut.
Les données brutes sont écrites dans data/raw/<key>.json.
"""
import json
import time
from pathlib import Path
from utils.config import DATA_RAW_DIR, CACHE_TTL


def _cache_path(key: str) -> Path:
    return DATA_RAW_DIR / f"{key}.json"


def _json_default(obj: object) -> str:
    """Sérialise les types non natifs JSON (pd.Timestamp, datetime, date…)."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()  # type: ignore[union-attr]
    raise TypeError(f"Type non sérialisable : {type(obj)}")


def load(key: str, ttl: int = CACHE_TTL) -> list | dict | None:
    """
    Charge une entrée du cache.
    Retourne None si absente ou expirée (> ttl secondes).
    """
    path = _cache_path(key)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > ttl:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save(key: str, data: list | dict) -> None:
    """Persiste data dans le cache (crée le répertoire si nécessaire)."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(key).write_text(
        json.dumps(data, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
