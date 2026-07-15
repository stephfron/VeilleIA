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
from pydantic import BaseModel, Field

from services import crm
from services.api_activite import get_activite
from services.api_dole import CATEGORY_LABEL, rechercher_textes
from services.api_onisep import get_formations
from services.ciblage import cibles_departement
from services.dossier import constituer_dossier
from services.fiche_territoire import rechercher_parlementaire

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("veilleia.api")

app = FastAPI(title="VeilleIA API", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")

# En dev, Vite tourne sur son propre port ; en prod le front est servi par
# cette app (même origine), la liste reste donc restrictive.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

CHAMBRES = {"Sénat", "Assemblée nationale"}


class InteractionIn(BaseModel):
    """Corps de POST /api/interactions."""
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    canal: str = Field(min_length=1, max_length=30)
    objet: str = Field(min_length=1, max_length=300)
    date_interaction: str | None = Field(default=None, max_length=10)
    notes: str | None = Field(default=None, max_length=2000)
    rappel: str | None = Field(default=None, max_length=10)


class StatutIn(BaseModel):
    """Corps de PUT /api/statut."""
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    statut: str = Field(min_length=1, max_length=30)


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
    q: str = Query(min_length=1, max_length=200, description="Nom, code ou libellé de département"),
    chambre: str | None = Query(default=None, description="Sénat ou Assemblée nationale"),
    limit: int = Query(default=20, ge=1, le=50, description="Nb max de fiches (borne les fetchs SIRENE)"),
) -> dict:
    if chambre is not None and chambre not in CHAMBRES:
        raise HTTPException(status_code=422, detail=f"chambre doit être l'une de : {sorted(CHAMBRES)}")
    try:
        fiches = rechercher_parlementaire(q, limit=limit, chambre=chambre)
    except Exception:
        logger.exception("Échec rechercher_parlementaire(q=%r)", q)
        raise HTTPException(status_code=502, detail="Service RNE/SIRENE indisponible, réessayez plus tard.")

    return {"count": len(fiches), "results": _json_safe(fiches)}


@app.get("/api/textes")
def textes(
    q: str = Query(min_length=1, max_length=200, description="Mots-clés"),
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


@app.get("/api/activite")
def activite(
    nom: str = Query(min_length=1, max_length=100),
    prenom: str = Query(min_length=1, max_length=100),
    chambre: str = Query(description="Sénat ou Assemblée nationale"),
) -> dict:
    """Activité législative d'un élu (source Regards Citoyens, best-effort)."""
    if chambre not in CHAMBRES:
        raise HTTPException(status_code=422, detail=f"chambre doit être l'une de : {sorted(CHAMBRES)}")
    try:
        result = get_activite(nom, prenom, chambre)
    except Exception:
        # Contrat best-effort : jamais de 500, l'UI affiche « indisponible »
        logger.exception("Échec get_activite(nom=%r, prenom=%r, chambre=%r)", nom, prenom, chambre)
        result = None
    if result is None:
        return {"disponible": False}
    return {"disponible": True, **_json_safe(result)}  # type: ignore[dict-item]


@app.get("/api/dossier")
def dossier(
    nom: str = Query(min_length=1, max_length=100),
    prenom: str = Query(min_length=1, max_length=100),
    themes: str | None = Query(default=None, max_length=200, description="Mots-clés pour les textes pertinents"),
) -> dict:
    """
    Dossier de synthèse complet d'un parlementaire — contexte destiné à la
    future fonction IA de génération de synthèses (synthese_status le signale).
    """
    try:
        result = constituer_dossier(nom, prenom, themes)
    except Exception:
        logger.exception("Échec constituer_dossier(nom=%r, prenom=%r)", nom, prenom)
        raise HTTPException(status_code=502, detail="Sources de données indisponibles, réessayez plus tard.")
    if result is None:
        raise HTTPException(status_code=404, detail="Parlementaire introuvable.")
    return _json_safe(result)  # type: ignore[return-value]


@app.get("/api/formations")
def formations(
    code_dept: str = Query(min_length=2, max_length=3, description="Code département (ex : 69)"),
) -> dict:
    """
    Formations professionnelles d'un département (API Onisep, best-effort).
    Retourne [] si source indisponible.
    """
    try:
        results = get_formations(code_dept)
    except Exception:
        logger.exception("Échec get_formations(code_dept=%r)", code_dept)
        results = None
    # Best-effort : jamais de 5xx, retourne [] si indisponible
    if results is None:
        return {"count": 0, "results": [], "disponible": False}
    return {"count": len(results), "results": _json_safe(results), "disponible": True}


# --- CRM lobbying : cibles, interactions, statuts, rappels ---

@app.get("/api/cibles")
def cibles(
    q: str = Query(min_length=1, max_length=200, description="Nom, code ou libellé de département"),
    chambre: str | None = Query(default=None, description="Sénat ou Assemblée nationale"),
    limit: int = Query(default=20, ge=1, le=50),
    avec_activite: bool = Query(default=False, description="Pondérer par l'activité législative (plus lent)"),
) -> dict:
    """Liste priorisée des parlementaires à contacter (score /100 explicable)."""
    if chambre is not None and chambre not in CHAMBRES:
        raise HTTPException(status_code=422, detail=f"chambre doit être l'une de : {sorted(CHAMBRES)}")
    try:
        results = cibles_departement(q, chambre=chambre, limit=limit, avec_activite=avec_activite)
    except Exception:
        logger.exception("Échec cibles_departement(q=%r)", q)
        raise HTTPException(status_code=502, detail="Sources de données indisponibles, réessayez plus tard.")
    return {"count": len(results), "results": _json_safe(results)}


@app.get("/api/interactions")
def interactions(
    nom: str = Query(min_length=1, max_length=100),
    prenom: str = Query(min_length=1, max_length=100),
) -> dict:
    """Historique des interactions avec un élu + statut de la relation."""
    try:
        results = crm.get_interactions(nom, prenom)
        statut = crm.get_statuts().get(crm.elu_key(nom, prenom), "a_contacter")
    except Exception:
        logger.exception("Échec get_interactions(nom=%r, prenom=%r)", nom, prenom)
        raise HTTPException(status_code=502, detail="Base CRM indisponible, réessayez plus tard.")
    return {"count": len(results), "statut": statut, "results": results}


@app.post("/api/interactions", status_code=201)
def creer_interaction(corps: InteractionIn) -> dict:
    """Enregistre une interaction (422 si canal ou date invalide)."""
    try:
        return crm.add_interaction(
            corps.nom, corps.prenom, corps.canal, corps.objet,
            date_interaction=corps.date_interaction, notes=corps.notes, rappel=corps.rappel,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Échec add_interaction(nom=%r, prenom=%r)", corps.nom, corps.prenom)
        raise HTTPException(status_code=502, detail="Base CRM indisponible, réessayez plus tard.")


@app.delete("/api/interactions/{interaction_id}")
def supprimer_interaction(interaction_id: int) -> dict:
    """Supprime une interaction (404 si id inconnu)."""
    try:
        supprimee = crm.delete_interaction(interaction_id)
    except Exception:
        logger.exception("Échec delete_interaction(id=%r)", interaction_id)
        raise HTTPException(status_code=502, detail="Base CRM indisponible, réessayez plus tard.")
    if not supprimee:
        raise HTTPException(status_code=404, detail="Interaction introuvable.")
    return {"deleted": True}


@app.put("/api/statut")
def statut(corps: StatutIn) -> dict:
    """Fixe le statut d'un élu (422 si statut invalide)."""
    try:
        return crm.set_statut(corps.nom, corps.prenom, corps.statut)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Échec set_statut(nom=%r, prenom=%r)", corps.nom, corps.prenom)
        raise HTTPException(status_code=502, detail="Base CRM indisponible, réessayez plus tard.")


@app.get("/api/rappels")
def rappels() -> dict:
    """Relances dues : interactions dont la date de rappel est échue."""
    try:
        results = crm.rappels_en_attente()
    except Exception:
        logger.exception("Échec rappels_en_attente()")
        raise HTTPException(status_code=502, detail="Base CRM indisponible, réessayez plus tard.")
    return {"count": len(results), "results": results}


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
