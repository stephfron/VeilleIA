# VeilleIA — Documentation Technique

## 1. Présentation

VeilleIA est une application web de **veille territoriale et institutionnelle**. Elle agrège des données publiques françaises pour croiser le tissu économique local avec l'activité législative des élus.

**Aucune IA, aucun LLM. Données brutes → visualisation.**

**Stack :**

| Composant | Technologie |
|---|---|
| Backend | Python 3.11 · FastAPI · Pandas |
| Frontend | React 18 · TypeScript · Vite |
| Visualisation | Recharts |
| HTTP (services) | requests |
| Tests | pytest (backend) |

---

## 2. Architecture & Flux de données

```text
APIs publiques
  ├── RNE (data.gouv.fr)     → élus / mandats / circonscriptions
  ├── SIRENE (INSEE)          → entreprises / codes NAF / départements
  └── DOLE (HuggingFace)      → textes de loi / dossiers législatifs

        ↓  services/*.py  (fetch + cache local 24 h, data/raw/)

        ↓  api/main.py  (FastAPI — /api/parlementaires, /api/textes)

    frontend/ (React + Vite)  → UI + Recharts
```

**Clé de jointure : Code Département** (harmonisé dans `utils/data_cleaning.py`).

---

## 3. Structure du projet

```
VeilleIA/
├── api/
│   └── main.py             # API FastAPI + service statique du build React
├── services/
│   ├── api_rne.py          # Élus par département/mandat
│   ├── api_sirene.py       # Entreprises par NAF/département
│   ├── api_dole.py         # Textes de loi (recherche mots-clés)
│   └── fiche_territoire.py # Croisement RNE × SIRENE
├── utils/
│   ├── config.py           # Constantes + variables d'env centralisées
│   ├── http.py             # Retry HTTP partagé
│   ├── data_cleaning.py    # Harmonisation codes département
│   └── cache.py            # Cache fichier 24 h (évite les appels répétés)
├── frontend/
│   ├── src/
│   │   ├── pages/          # Accueil, FicheTerritoire, Textes
│   │   ├── components/     # ui.tsx (design system), charts.tsx (Recharts)
│   │   ├── api.ts          # Client HTTP typé
│   │   └── styles/global.css  # Tokens design system UIMM (WCAG AA)
│   ├── package.json
│   └── vite.config.ts      # Proxy /api → localhost:8000 en dev
├── tests/                  # pytest — services, utils, API (mockée)
├── requirements.txt
└── render.yaml             # Déploiement Render (build front + uvicorn)
```

---

## 4. Développement local

```bash
# Backend (terminal 1)
pip install -r requirements-dev.txt
uvicorn api.main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend && npm install && npm run dev   # http://localhost:5173

# Tests backend
pytest
```

En production, un seul process : `npm run build` génère `frontend/dist`, servi statiquement par FastAPI (voir `render.yaml`).

Variables d'environnement (`.env` à la racine, chargé par `api/main.py`) :
- `INSEE_SIRENE_API_KEY` — clé API SIRENE (reste côté serveur, jamais exposée au navigateur)

---

## 5. Conventions

- **Type hints** sur toutes les fonctions publiques Python ; TypeScript `strict` côté front
- **Cache fichier** systématique sur les appels API externes (`data/raw/`) — zéro appel réseau superflu
- `api/` = validation des paramètres + sérialisation, aucune logique métier
- `services/` = fetch + retour `pd.DataFrame` propre, rien d'autre
- Erreurs réseau : journalisées côté serveur (`logging`), message générique côté client (502)
- Palette et contrastes conformes WCAG 2.2 AA (tokens dans `frontend/src/styles/global.css`)
