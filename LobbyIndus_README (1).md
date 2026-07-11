# 🏛️ LobbyIndus — Technical & Architecture Documentation

## 📝 1. Présentation et Contexte

LobbyIndus est une application Streamlit d'aide à la décision (Intelligence Territoriale et Affaires Publiques). Son but est de croiser la géographie économique (tissu industriel local) avec l'activité législative (députés/sénateurs) pour identifier des opportunités de dialogue institutionnel.

**Stack technique principale :**

- **Langage** : Python 3.11
- **Interface** : Streamlit
- **Data Processing** : Pandas (manipulation), Plotly (visualisation)
- **LLM Engine** : `google-generativeai` (Gemini Pro) pour l'analyse sémantique et la synthèse
- **Environnement** : GitHub Codespaces (`.devcontainer`)

---

## 🏗️ 2. Architecture Logicielle & Flux de Données

L'application suit un modèle de conception modulaire en couches (Séparation des préoccupations / *Separation of Concerns*).

### Flux de données (Data Flow)

1. **Ingestion** : Les modules `services/` interrogent les API publiques (RNE, SIRENE, DOLE/Data.gouv).
2. **Transformation** : Les données brutes sont nettoyées et fusionnées avec Pandas en utilisant le **Code Département** comme clé primaire de jointure (Primary Key).
3. **Analyse IA** : Les données transformées sont injectées dans les templates de prompts (`agents/*.md`) et envoyées à l'API Gemini. L'IA renvoie exclusivement un objet **JSON structuré**.
4. **Restitution** : Streamlit (`app.py`) consomme le JSON généré par l'IA et les DataFrames Pandas pour afficher des métriques, des synthèses textuelles et des graphiques interactifs (Plotly).

---

## 📂 3. Organisation du Répertoire & Responsabilités

```
LobbyIndus/
│
├── .devcontainer/             # Configuration de l'environnement Codespaces
│   ├── devcontainer.json
│   └── Dockerfile             # (Optionnel) Setup des dépendances système
│
├── agents/                    # Fichiers de configuration des System Prompts (Markdown)
│   ├── agent_politique.md     # Rôle : Analyse des amendements/QAG (DOLE)
│   ├── agent_economique.md    # Rôle : Analyse du poids industriel (SIRENE/NAF)
│   └── agent_synthese.md      # Rôle : Calcul du score d'appétence final
│
├── data/                      # Stockage temporaire / Cache local
│   ├── raw/                   # JSON/CSV bruts issus des API
│   └── processed/             # DataFrames nettoyés (Parquet ou CSV)
│
├── services/                  # Connecteurs API et ingestion de données
│   ├── api_rne.py             # Fetch : Députés/Sénateurs par mandat/département
│   ├── api_sirene.py          # Fetch : Entreprises par code NAF/département
│   ├── api_dole.py            # Fetch : Textes de loi, amendements
│   └── llm_client.py          # Wrapper pour `google-generativeai` (gestion appels + parsing JSON)
│
├── utils/                     # Fonctions transverses et helpers
│   ├── data_cleaning.py       # Harmonisation des identifiants (ex: Codes Départements)
│   └── json_parser.py         # Validation et extraction sécurisée du JSON en sortie d'IA
│
├── app.py                     # Point d'entrée Streamlit (Routage et Layout principal)
├── requirements.txt           # Dépendances Python (streamlit, pandas, google-generativeai...)
└── README.md                  # Documentation technique (Ce fichier)
```

---

## 🤖 4. Architecture des Agents IA & Prompts

L'intelligence artificielle n'est pas utilisée comme un simple chatbot, mais comme un **moteur de traitement de données structurées**. Le pattern utilisé est celui du **Multi-Agent simulé** via des System Prompts distincts.

> **Règle d'or de l'interaction LLM :**
> Chaque fichier `.md` dans le dossier `agents/` contient les directives (System Prompt) de l'agent. Le wrapper Python (`services/llm_client.py`) lit ce fichier `.md`, lui concatène les données JSON/Texte du contexte actuel, et force le LLM à répondre strictement selon un schéma JSON défini.

**Exemple de schéma de sortie attendu (JSON Strict) :**

```json
{
  "score_appetence": 87,
  "positionnement": "Favorable",
  "facteurs_cles": [
    "Forte densité d'industries NAF 25 dans la circonscription",
    "Auteur d'un amendement pro-réindustrialisation"
  ],
  "recommandation_action": "Prioriser un rendez-vous sur le site de production local."
}
```

---

## 💻 5. Conventions de Développement

Pour garantir un code propre, maintenable et compréhensible par les IA de complétion (Copilot), les règles suivantes s'appliquent :

- **Typage statique (Type Hinting)** : Toutes les fonctions doivent être typées (`from typing import List, Dict, Optional`, etc.).
  Exemple : `def get_rne_data(dept_code: str) -> pd.DataFrame:`

- **Gestion des erreurs & Résilience** :
  Tous les appels réseau (API gouvernementales, API Gemini) doivent être protégés par des blocs `try/except`, avec gestion du fallback ou affichage clair dans Streamlit via `st.error()`.

- **Modularité stricte** :
  L'UI (`app.py`) ne doit contenir aucune logique métier ou appel API direct. Elle ne fait qu'appeler les fonctions exposées par `services/` et `utils/`.

- **Formatage et Linting** :
  Utilisation recommandée de **Black** (formatage) et **Ruff** ou **Flake8** (linting) configurés dans l'environnement.

---

## 🛠️ 6. Environnement Codespaces (Prêt à l'emploi)

Ce projet est conçu pour s'exécuter instantanément via GitHub Codespaces.

**Configuration `.devcontainer/devcontainer.json` attendue :**

- **Image** : `mcr.microsoft.com/devcontainers/python:3.11`
- **Extensions VS Code pré-installées** :
  - `ms-python.python` (Python)
  - `ms-python.vscode-pylance` (Pylance pour le typage)
  - `charliermarsh.ruff` (Linter ultra-rapide)
  - `GitHub.copilot` (Pour l'aide au dev)
- **PostCreateCommand** : `pip install -r requirements.txt`
- **Ports Forwarding** : Le port `8501` (Streamlit) doit être ouvert par défaut pour la prévisualisation web.

---

## 🚀 7. Roadmap d'implémentation (Pour l'assistant IA)

Si vous êtes une IA assistant le développeur sur ce projet, veuillez suivre cet ordre d'implémentation :

1. **Setup** : Initialiser `requirements.txt` et `devcontainer.json`.
2. **Couche Services (Data Pipeline)** : Écrire les scripts `api_rne.py` et `api_sirene.py` avec `requests` et retourner des DataFrames propres.
3. **Couche IA** : Configurer `services/llm_client.py` en utilisant `google.generativeai` et écrire le premier fichier `agents/agent_synthese.md`.
4. **Couche UI** : Développer `app.py` avec Streamlit pour l'assemblage final, en intégrant des graphiques Plotly.
