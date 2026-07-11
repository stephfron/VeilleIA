# VeilleIA — Documentation Technique

## 1. Présentation

VeilleIA est un dashboard Streamlit de **veille territoriale et institutionnelle**. Il agrège des données publiques françaises pour croiser le tissu économique local avec l'activité législative des élus.

**Aucune IA, aucun LLM. Données brutes → visualisation.**

**Stack :**

| Composant | Technologie |
|---|---|
| Langage | Python 3.11 |
| Interface | Streamlit |
| Données | Pandas |
| Visualisation | Plotly |
| HTTP | requests |
| Environnement | GitHub Codespaces |

---

## 2. Architecture & Flux de données

```text
APIs publiques
  ├── RNE (data.gouv.fr)     → élus / mandats / circonscriptions
  ├── SIRENE (INSEE)          → entreprises / codes NAF / départements
  └── DOLE (data.gouv.fr)    → textes de loi / amendements

        ↓  services/*.py  (fetch + cache local)

    data/raw/               → JSON/CSV bruts
    data/processed/         → DataFrames nettoyés (Parquet)

        ↓  utils/           (nettoyage, harmonisation)

    streamlit_app.py        → Streamlit UI + Plotly
```

**Clé de jointure : Code Département** (harmonisé dans `utils/data_cleaning.py`).

---

## 3. Structure du projet

```
VeilleIA/
├── .devcontainer/
│   └── devcontainer.json
├── data/
│   ├── raw/
│   └── processed/
├── services/
│   ├── api_rne.py          # Élus par département/mandat
│   ├── api_sirene.py       # Entreprises par NAF/département
│   └── api_dole.py         # Textes de loi, amendements
├── utils/
│   ├── data_cleaning.py    # Harmonisation codes département
│   └── cache.py            # Cache fichier (évite les appels répétés)
├── streamlit_app.py        # Point d'entrée Streamlit
├── requirements.txt
└── readme.md
```

---

## 4. Conventions

- **Type hints** sur toutes les fonctions publiques
- **Cache fichier** systématique sur les appels API (`data/raw/`) — zéro appel réseau superflu
- `streamlit_app.py` = UI uniquement, aucune logique métier
- `services/` = fetch + retour `pd.DataFrame` propre, rien d'autre
- Gestion d'erreur réseau via `try/except` + `st.error()` dans l'UI

---

## 5. Environnement Codespaces

**`.devcontainer/devcontainer.json` :**
- Image : `mcr.microsoft.com/devcontainers/python:3.11`
- Extensions : `ms-python.python`, `charliermarsh.ruff`
- PostCreate : `pip install -r requirements.txt`
- Port forward : `8501` (Streamlit)

---

## 6. Ordre d'implémentation

1. `requirements.txt` + `.devcontainer/devcontainer.json`
2. `utils/data_cleaning.py` + `utils/cache.py`
3. `services/api_rne.py` → DataFrame élus
4. `services/api_sirene.py` → DataFrame entreprises
5. `services/api_dole.py` → DataFrame activité législative
6. `streamlit_app.py` → UI Streamlit avec filtres département + graphiques Plotly
