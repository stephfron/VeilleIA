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
| `utils/http.py` | Retry HTTP partagé | ✅ |
| `utils/data_cleaning.py` | Normalisation codes dept | ✅ |

---

## Phase 2 — Interface Streamlit (priorité immédiate)

### 2.1 `app.py` — Squelette et navigation

- Sidebar : filtre chambre (Sénat / AN / les deux), filtre département
- Page **Accueil** : barre de recherche (nom ou département)
- Page **Fiche territoire** : résultat de `rechercher_parlementaire()`
- Page **Textes législatifs** : résultat de `rechercher_textes()`

### 2.2 Composants UI à créer

| Fichier | Contenu |
|---|---|
| `ui/carte_parlementaire.py` | Carte info élu (nom, chambre, dept, mandat) |
| `ui/bloc_industrie.py` | Métriques + graphique Plotly (NAF, effectifs) |
| `ui/tableau_textes.py` | Tableau DOLE filtrable (catégorie, année, mots-clés) |

### 2.3 Graphiques Plotly prévus

- Treemap ou bar chart des codes NAF par effectifs estimés
- Évolution temporelle des textes législatifs par secteur (création_date)

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

## Phase 5 — Déploiement

| Option | Coût | Contraintes |
|---|---|---|
| Streamlit Community Cloud | Gratuit | Repo public, 1 Go RAM |
| HuggingFace Spaces | Gratuit | Docker, clé API en secret |
| Scaleway / Render | ~5 €/mois | Plus flexible |

Recommandation : **HuggingFace Spaces** (Dockerfile) — cohérent avec la source DOLE, gestion des secrets intégrée, RAM suffisante.

Prérequis : externaliser la clé INSEE SIRENE en variable d'environnement Spaces.

---

## Backlog (hors roadmap principale)

- Comparaison multi-territoires (ex : top 10 départements industriels)
- Cartographie Plotly (`choropleth_mapbox`) des effectifs par département
- Actualisation automatique du cache (cron Streamlit ou scheduler)
- Intégration BODACC (créations/liquidations d'entreprises par département)
