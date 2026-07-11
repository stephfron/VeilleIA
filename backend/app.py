"""
API HTTP VeilleIA — FastAPI.

Expose la couche services (RNE × SIRENE, DOLE) au frontend React.
Aucune logique métier ici : validation des paramètres, appel du service,
sérialisation JSON-safe, c'est tout.

Dev    : uvicorn backend.app:app --reload --port 8000  (+ Vite sur 5173, proxy /api)
Vercel : exposée via la fonction serverless api/index.py (voir vercel.json) ;
         le front est servi par le CDN Vercel, pas par cette app.
Render : le build React (frontend/dist) est servi statiquement par cette app.
"""
from dotenv import load_dotenv

load_dotenv()  # avant l'import des services : utils/config lit l'env au chargement

import logging
import math
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from services.api_dole import CATEGORY_LABEL, rechercher_textes
from services.fiche_territoire import rechercher_parlementaire

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("veilleia.api")

app = FastAPI(title="VeilleIA API", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")

# En dev, Vite tourne sur son propre port ; en prod le front est servi par
# cette app (même origine), la liste reste donc restrictive.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

CHAMBRES = {"Sénat", "Assemblée nationale"}


def _json_safe(value: object) -> object:
    """Remplace NaN/NaT/inf (illégaux en JSON) par None, récursivement."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/categories")
def categories() -> dict[str, str]:
    """Catégories DOLE (clé technique → libellé affichable)."""
    return CATEGORY_LABEL


@app.get("/api/parlementaires")
def parlementaires(
    q: str = Query(min_length=1, description="Nom, code ou libellé de département"),
    chambre: str | None = Query(default=None, description="Sénat ou Assemblée nationale"),
    limit: int = Query(default=20, ge=1, le=50, description="Nb max de fiches (borne les fetchs SIRENE)"),
) -> dict:
    if chambre is not None and chambre not in CHAMBRES:
        raise HTTPException(status_code=422, detail=f"chambre doit être l'une de : {sorted(CHAMBRES)}")
    try:
        fiches = rechercher_parlementaire(q, limit=limit)
    except Exception:
        logger.exception("Échec rechercher_parlementaire(q=%r)", q)
        raise HTTPException(status_code=502, detail="Service RNE/SIRENE indisponible, réessayez plus tard.")

    if chambre:
        fiches = [f for f in fiches if f["parlementaire"]["chambre"] == chambre]
    return {"count": len(fiches), "results": _json_safe(fiches)}


@app.get("/api/textes")
def textes(
    q: str = Query(min_length=1, description="Mots-clés (ET implicite)"),
    categories: list[str] | None = Query(default=None),
    annee_min: int | None = Query(default=None, ge=1990, le=2030),
) -> dict:
    if categories:
        inconnues = set(categories) - set(CATEGORY_LABEL)
        if inconnues:
            raise HTTPException(status_code=422, detail=f"Catégories inconnues : {sorted(inconnues)}")
    try:
        df = rechercher_textes(q, categories=categories or None, annee_min=annee_min)
    except Exception:
        logger.exception("Échec rechercher_textes(q=%r)", q)
        raise HTTPException(status_code=502, detail="Service DOLE indisponible, réessayez plus tard.")

    if df.empty:
        return {"count": 0, "results": [], "par_annee": {}}

    par_annee = (
        df.dropna(subset=["annee"]).groupby("annee").size()
    )
    records = df.astype(object).where(df.notna(), None).to_dict("records")
    return {
        "count": len(records),
        "results": _json_safe(records),
        "par_annee": {str(int(annee)): int(nb) for annee, nb in par_annee.items()},
    }


# --- Front React buildé (prod) — monté en dernier pour ne pas masquer /api/* ---
_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        candidate = _DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_DIST / "index.html")
