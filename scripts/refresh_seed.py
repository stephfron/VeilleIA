"""
Régénère data/seed/ (snapshot RNE + DOLE committé, servi en fallback du cache).

Usage : python scripts/refresh_seed.py
À relancer ponctuellement (nouvelles législatures, nouveaux textes) puis committer.
Bypasse volontairement le cache : appelle les fetchers privés des services.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services import api_dole, api_rne  # noqa: E402
from utils.config import DATA_SEED_DIR, RNE_RESOURCE_IDS  # noqa: E402


def _write(key: str, records: list[dict]) -> None:
    DATA_SEED_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_SEED_DIR / f"{key}.json"
    path.write_text(json.dumps(records, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"  {path} — {len(records)} enregistrements")


def main() -> None:
    print("RNE sénateurs…")
    sen = api_rne._clean(api_rne._fetch_all(RNE_RESOURCE_IDS["senateurs"]))
    _write("senateurs", sen.to_dict("records"))

    print("RNE députés…")
    dep = api_rne._clean(api_rne._fetch_all(RNE_RESOURCE_IDS["deputes"]), extra_cols=api_rne._COL_DEPUTE)
    _write("deputes", dep.to_dict("records"))

    print("DOLE (long, ~1 min)…")
    dole = api_dole._fetch_all()
    _write("dole", dole.to_dict("records"))

    print("Seed régénéré — penser à committer data/seed/.")


if __name__ == "__main__":
    main()
