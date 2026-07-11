# VeilleIA — Feuille de route

## État actuel (branche `devapp`)

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
- `app.py` : erreurs réseau désormais journalisées (`logging`) avant d'afficher un message
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

### 2.1 `app.py` — Squelette et navigation ✅

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

- `utils/auth.py` (`require_login()`) : gate toute l'app avec `streamlit-authenticator`, appelé en tête d'`app.py`
- Credentials via variables d'environnement (déjà déclarées dans `render.yaml`, `sync: false` → à saisir dans le dashboard Render, déjà dans `.env` local) :
  - `AUTH_USERNAME`
  - `AUTH_PASSWORD_HASH` (hash bcrypt — jamais le mot de passe en clair)
  - `AUTH_COOKIE_KEY` (clé de signature du cookie de session)
  - `INSEE_SIRENE_API_KEY`

Testé en local (Playwright) : accès bloqué sans identifiants, rejeté avec un mauvais mot de
passe, accordé avec les bons + déconnexion fonctionnelle.

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
