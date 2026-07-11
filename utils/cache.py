import json
import time
from pathlib import Path

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

TTL = 86400  # 24h en secondes


def _cache_path(key: str) -> Path:
    return RAW_DIR / f"{key}.json"


def _json_default(obj):
    """Sérialise les types non natifs JSON (Timestamp, date…)."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    raise TypeError(f"Type non sérialisable : {type(obj)}")


def get(key: str) -> dict | list | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > TTL:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def set(key: str, data: dict | list) -> None:
    _cache_path(key).write_text(
        json.dumps(data, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
