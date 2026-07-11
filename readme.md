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
│   └── index.py            # Entrée serverless Vercel (importe backend.app)
├── backend/
│   └── app.py              # API FastAPI + service statique du build React
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
├── vercel.json             # Déploiement Vercel (front statique + fonction Python)
└── render.yaml             # Alternative Render (build front + uvicorn)
```

---

## 4. Développement local

```bash
# Backend (terminal 1)
pip install -r requirements-dev.txt
uvicorn backend.app:app --reload --port 8000

# Frontend (terminal 2)
cd frontend && npm install && npm run dev   # http://localhost:5173

# Tests backend
pytest
```

Variables d'environnement (`.env` à la racine, chargé par `backend/app.py`) :
- `INSEE_SIRENE_API_KEY` — clé API SIRENE (reste côté serveur, jamais exposée au navigateur)
- `DATA_RAW_DIR` — optionnel, emplacement du cache fichier (défaut : `data/raw/`, ou `/tmp/veilleia/raw` sur Vercel)

---

## 5. Déploiement Vercel (prototype privé)

`vercel.json` configure tout : le front est buildé (`npm ci && npm run build`) et servi
par le CDN, l'API tourne dans **une** fonction serverless Python (`api/index.py`,
`maxDuration` 300 s) vers laquelle les rewrites routent tout `/api/*` ; le reste
retombe sur `index.html` (SPA).

Étapes dans le dashboard Vercel après import du repo (branche `devReact`) :

1. **Variable d'environnement** : `INSEE_SIRENE_API_KEY` (Settings → Environment Variables)
2. **Accès privé** : Settings → Deployment Protection → **Vercel Authentication** →
   « All Deployments » — seuls les membres du compte Vercel peuvent ouvrir l'app,
   y compris l'URL de production (inclus dans le plan gratuit)

Limites connues du serverless (acceptables pour un prototype) :

- Le cache fichier vit dans `/tmp` : il est **éphémère** — après un cold start, la
  première recherche repaye le téléchargement complet (DOLE ~30-60 s, SIRENE
  1-3 min par département). Les requêtes suivantes sur la même instance sont rapides.
- Si une recherche dépasse les 300 s de `maxDuration`, relancer : le cache
  partiellement rempli n'est pas conservé, mais une instance chaude aboutit en général.

Alternative long-running : `render.yaml` reste en place (un seul process uvicorn qui
sert aussi le front, cache persistant sur disque).

---

## 6. Conventions

- **Type hints** sur toutes les fonctions publiques Python ; TypeScript `strict` côté front
- **Cache fichier** systématique sur les appels API externes (`data/raw/`) — zéro appel réseau superflu
- `api/` = validation des paramètres + sérialisation, aucune logique métier
- `services/` = fetch + retour `pd.DataFrame` propre, rien d'autre
- Erreurs réseau : journalisées côté serveur (`logging`), message générique côté client (502)
- Palette et contrastes conformes WCAG 2.2 AA (tokens dans `frontend/src/styles/global.css`)
