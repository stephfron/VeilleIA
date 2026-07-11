# VeilleIA — Feuille de route

## Refonte React (2026-07-11, branche `claude/refonte-react`)

L'UI Streamlit est remplacée par une stack web moderne, **sans toucher à la couche
données** (services/, utils/, cache, tests) qui reste la source unique de logique métier :

| Couche | Avant | Après |
|---|---|---|
| UI | Streamlit + Plotly | React 18 + TypeScript + Vite + Recharts |
| Serveur | streamlit run | FastAPI (`api/main.py`) + uvicorn |
| Design system | ui/theme.py + inject_css | `frontend/src/styles/global.css` (mêmes tokens UIMM, WCAG AA) |
| Auth | streamlit-authenticator (AUTH_ENABLED) | retirée — à réintroduire en middleware FastAPI si besoin (voir backlog) |

- `api/main.py` : `/api/parlementaires`, `/api/textes`, `/api/categories` — validation
  des paramètres, sérialisation JSON-safe (NaN → null), erreurs 502 journalisées ;
  sert `frontend/dist` statiquement en production (une seule origine, pas de CORS en prod)
- `frontend/` : 3 pages (Accueil, Fiche territoire, Textes législatifs), recherche avec
  debounce 400 ms, filtres chambre/catégories/année, bouton Réinitialiser, navigation
  React Router, responsive (sidebar → barre horizontale sur mobile)
- Graphiques Recharts mono-série, couleur de barre validée (contraste ≥ 3:1), tooltip au survol
- `tests/test_api.py` : 10 tests FastAPI (TestClient, services mockés — aucun réseau)
- `render.yaml` : build front (npm ci + vite build) puis `uvicorn backend.app:app`

**Optimisation des recherches (2026-07-11)** — trois goulots corrigés :
1. *Cold start serverless* : snapshot réel RNE + DOLE committé (`data/seed/`,
   régénérable via `scripts/refresh_seed.py`) servi en fallback du cache → première
   recherche sans aucun téléchargement (~0,2 s au lieu de 40-60 s). RNE = élus en
   activité uniquement (348 sénateurs + 577 députés, mandats en cours).
2. *Re-parsing* : `@memoize()` (utils/cache.py) garde en RAM les DataFrames parsés
   (le JSON DOLE fait 8 Mo) pour la durée de vie de l'instance.
3. *SIRENE non borné* : `rechercher_parlementaire(limit=20)` — les fetchs SIRENE
   (1-3 min/département hors cache, quota INSEE 30 req/min) s'arrêtent à la limite.
   Reste vrai : la première fiche d'un département est lente, les suivantes instantanées.
Tri des textes DOLE par date décroissante (les lois récentes d'abord).

**Déploiement Vercel (2026-07-11, prototype privé)** — `vercel.json` : front statique
(CDN) + une fonction serverless Python (`api/index.py` → `backend/app.py`, maxDuration
300 s), rewrites `/api/*` → fonction, SPA fallback. Cache fichier redirigé vers `/tmp`
sur Vercel (`utils/config.py`, env `VERCEL`), éphémère entre cold starts. Confidentialité
via Deployment Protection (Vercel Authentication, « All Deployments ») à activer dans le
dashboard + variable `INSEE_SIRENE_API_KEY`. Détails et limites : readme §5.

---

## État antérieur (branche `devapp`)

Pipeline de données opérationnel :

| Service | Source | Statut |
|---|---|---|
| `services/api_rne.py` | API tabulaire data.gouv.fr | ✅ |
| `services/api_sirene.py` | INSEE SIRENE (clé API) | ✅ |
| `services/api_dole.py` | HuggingFace AgentPublic/dole | ✅ |
| `services/fiche_territoire.py` | Croisement RNE × SIRENE | ✅ |
| `utils/cache.py` | Cache fichier JSON 24 h | ✅ |
| `utils/config.py` | Constantes centralisées | ✅ |
| `utils/http.py` | Retry HTTP partagé (statuts + erreurs réseau) | ✅ |
| `utils/data_cleaning.py` | Normalisation codes dept | ✅ |
| `tests/` | Suite pytest (31 tests) — data_cleaning, échappement HTML, recherche, retry HTTP | ✅ |

---

## Refactor fullstack (2026-07-11)

Audit du code existant (pas seulement l'UI) avec la checklist sécurité/fiabilité du
`code-reviewer`, plus les principes transversaux (tests à tous les niveaux, observabilité,
"aucune couche incomplète") de `fullstack-developer` — sans reprendre son stack
Next.js/PostgreSQL/tRPC/IA-native, hors sujet pour ce projet Python/Streamlit sans IA.

Corrections :
- `services/api_rne.py` n'utilisait pas le helper de retry partagé (`get_with_retry`),
  contrairement à `api_sirene.py`/`api_dole.py` → uniformisé
- `utils/http.py` : `get_with_retry` ne gérait que les codes HTTP transitoires, pas les
  erreurs réseau (timeout, connexion) → retry + exception relevée après épuisement
- `streamlit_app.py` : erreurs réseau désormais journalisées (`logging`) avant d'afficher un message
  générique à l'utilisateur — invisibles auparavant dans les logs serveur
- **Bug réel trouvé en testant après refactor** : `page_fiche_territoire` plantait
  (`StreamlitDuplicateElementId`) dès qu'une recherche renvoyait plusieurs élus du même
  département (graphiques NAF identiques → collision d'ID auto-généré). Corrigé avec une
  `key` explicite par résultat.
- `tests/` créé (pytest) : logique pure sans dépendance réseau (normalisation, échappement
  HTML, filtrage de recherche, retry HTTP avec mocks) — `requirements-dev.txt` pour l'installer

Auth (`streamlit-authenticator`) câblée le 2026-07-11 — voir Phase 5, le blocage est levé.

---

## Phase 2 — Interface Streamlit ✅ (squelette livré)

### 2.1 `streamlit_app.py` — Squelette et navigation ✅

- Sidebar : navigation Accueil / Fiche territoire / Textes législatifs (`st.sidebar.radio`)
- Page **Accueil** : hero + 3 cartes de raccourci
- Page **Fiche territoire** : recherche → `rechercher_parlementaire()` → header sombre + stats + bar chart NAF
- Page **Textes législatifs** : recherche → `rechercher_textes()` → grille de cards (3 colonnes)
- Filtre chambre (Sénat / Assemblée nationale / Les deux) sur la page Fiche territoire ✅
- Filtre année minimale sur la page Textes législatifs ✅
- Compteur de résultats (`result_count()`) sur les deux pages de recherche ✅

Reste à faire : pagination résultats (au-delà des ~20 premiers), filtre département dédié.

### 2.2 Design system ✅ (basé sur le design Figma UIMM)

Charte extraite du design Figma de référence (rouge `#E63C46`, navy `#171A1F`, fond `#F2F7FA`,
badges bleu-gris) et adaptée en composants Streamlit réutilisables :

| Fichier | Contenu |
|---|---|
| `ui/theme.py` | Tokens couleurs + police (Inter, Google Fonts) |
| `ui/style.py` | `inject_css()` — reskin boutons/inputs Streamlit + classes `.uimm-*` |
| `ui/components.py` | `eyebrow()`, `stat_card()`, `texte_card()`, `fiche_header()` |

Vérifié en local (Playwright + vraies données RNE/SIRENE/DOLE) : rendu conforme sur les 3 pages.

Palette ajustée pour conformité WCAG 2.2 AA (contraste texte ≥ 4.5:1) : rouge boutons/stats
`#C6303A` (5.4:1, remplace `#E63C46` qui était à 4.1:1), badges `#3D5F82` (6.6:1, remplace
`#5B86B1` à 3.8:1), texte secondaire `#565F6E` (5.9-6.4:1). Le rouge vif d'origine (`red_bright`)
reste utilisé pour les éléments non-textuels (barres de graphique Plotly). Focus visible ajouté
sur les boutons (`:focus-visible`, critère WCAG 2.4.11).

### 2.3 Graphiques Plotly

- ✅ Bar chart top 5 codes NAF par nb d'établissements (page Fiche territoire)
- ✅ Évolution du nombre de textes législatifs par année (page Textes législatifs, sur les résultats filtrés)

---

## Phase 3 — Enrichissement des données parlementaires

### 3.1 Groupes politiques + commissions

Objectif : savoir si un élu siège en commission des affaires économiques ou industrie.

| Source | Données | Accès |
|---|---|---|
| `data.assemblee-nationale.fr` | Groupes + commissions AN | JSON open data (ZIP) |
| `data.senat.fr` | Groupes + commissions Sénat | À confirmer |

Livrable : `services/api_organes.py` — enrichit `get_parlementaires()` avec `groupe_politique` et `commission`.

### 3.2 Activité législative nominative

| Source | Données | Accès |
|---|---|---|
| AN open data | Amendements (auteur + texte) | ZIP JSON |
| AN open data | Questions au Gouvernement (QAG) | ZIP JSON |

Livrable : `services/api_activite.py` — retourne les amendements et QAG d'un parlementaire filtrés par mot-clé sectoriel.

---

## Phase 4 — Scoring et export

### 4.1 Score d'appétence lobbying

Calcul local (pas de LLM) basé sur des heuristiques pondérées :

| Signal | Poids |
|---|---|
| Nb établissements industriels dans le territoire | 30 % |
| Nb salariés estimés | 25 % |
| Appartenance à la commission Affaires économiques | 25 % |
| Nb amendements sur des sujets industriels | 20 % |

Livrable : `services/scoring.py`

### 4.2 Export

- Export CSV de la liste des fiches (Streamlit `st.download_button`)
- Export PDF d'une fiche territoire (via `fpdf2` ou `weasyprint`)

---

## Phase 5 — Déploiement ✅ (prêt à déployer)

**Décision : Render** (tier gratuit, `render.yaml` en place à la racine, `runtime.txt` pin Python 3.11).

App privée (usage personnel) → authentification requise avant l'UI, câblée le 2026-07-11 :

- `utils/auth.py` (`require_login()`) : gate toute l'app avec `streamlit-authenticator`, appelé en tête d'`streamlit_app.py`
- Credentials via variables d'environnement (déjà déclarées dans `render.yaml`, `sync: false` → à saisir dans le dashboard Render, déjà dans `.env` local) :
  - `AUTH_USERNAME`
  - `AUTH_PASSWORD_HASH` (hash bcrypt — jamais le mot de passe en clair)
  - `AUTH_COOKIE_KEY` (clé de signature du cookie de session)
  - `INSEE_SIRENE_API_KEY`

Testé en local (Playwright) : accès bloqué sans identifiants, rejeté avec un mauvais mot de
passe, accordé avec les bons + déconnexion fonctionnelle.

**Auth rendue optionnelle (2026-07-11)** — `AUTH_ENABLED` (`utils/config.py`) pilote le gate,
**fail-closed** : activée par défaut (valeur `"true"` si la variable n'est pas définie), pour
qu'un déploiement qui oublie de la configurer (Render, Streamlit Community Cloud, ou tout futur
environnement) reste protégé au lieu de se retrouver public sans login par défaut. Valeur brute
validée strictement (`"true"`/`"false"` uniquement, sinon `ValueError` au démarrage — pas de
défaut silencieux). `require_login()` retourne immédiatement si désactivée ; un badge sidebar
« Authentification désactivée » s'affiche pour rendre l'état visible.

Pour désactiver l'auth sur **un environnement de test précis** (jamais par défaut dans le
dépôt) : définir `AUTH_ENABLED=false` dans le `.env` local ou les secrets de cette plateforme
uniquement (`.env` est gitignored). `render.yaml` fixe `AUTH_ENABLED=true` explicitement pour
le service Render de production — après un merge touchant `render.yaml`, vérifier dans le
dashboard Render qu'un Sync manuel du Blueprint a bien propagé la variable au service déjà
provisionné (Render ne le fait pas toujours rétroactivement).

Le tier gratuit Render met l'instance en veille après inactivité (cold start ~30-50s au réveil) — acceptable pour un usage personnel.

**Reste à faire pour déployer réellement** (action manuelle sur render.com, hors du dépôt) :

1. New → Blueprint sur render.com, connecter le repo GitHub `VeilleIA`, branche `devapp`
2. Renseigner les 4 variables d'environnement listées ci-dessus dans le dashboard Render
   (valeurs identiques à celles du `.env` local pour AUTH_*)
3. Déployer — l'URL Render n'est accessible qu'après connexion (login/mot de passe)

---

## Backlog (hors roadmap principale)

- Comparaison multi-territoires (ex : top 10 départements industriels)
- Cartographie Plotly (`choropleth_mapbox`) des effectifs par département
- Actualisation automatique du cache (cron Streamlit ou scheduler)
- Intégration BODACC (créations/liquidations d'entreprises par département)
