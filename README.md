# 🏛️ LobbyIndus — Cartographie du Lobbying Industriel Territorial

## Présentation

LobbyIndus est une application d'aide à la décision destinée à cartographier l'engagement des parlementaires français (députés et sénateurs) sur les enjeux de souveraineté industrielle et de formation professionnelle.

En croisant les données législatives avec les caractéristiques économiques des territoires, l'application permet d'identifier les opportunités de dialogue institutionnel et de lobbying territorial.

---

# 🎯 Objectifs

L'application vise à :

- Cartographier les positions et l'activité des parlementaires.
- Analyser le tissu industriel local.
- Croiser les données économiques et législatives.
- Produire un score d'appétence sur les sujets industriels.
- Identifier les territoires prioritaires pour les actions d'affaires publiques.

---

# 🛠️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| Langage | Python 3.11 |
| Framework Web | Streamlit |
| Traitement des données | Pandas |
| Intelligence artificielle | Gemini Pro (`google-generativeai`) |
| Environnement de développement | GitHub Codespaces (`.devcontainer`) |

---

# 📊 Architecture des données

Le projet repose sur une architecture centrée autour du **code départemental**, utilisé comme clé de correspondance entre plusieurs jeux de données.

```
                 Code département
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   API RNE         API SIRENE      Données législatives
     Élus        Entreprises          Dole / data.gouv
```

Cette architecture permet de relier :

- les élus du territoire ;
- le tissu industriel local ;
- l'activité parlementaire.

---

# 📁 Sources de données

## 1. Données des élus

**Source**

- Répertoire National des Élus (RNE)

**Objectif**

- récupérer les députés et sénateurs ;
- identifier les mandats ;
- associer les élus à leur département ou circonscription.

---

## 2. Données économiques

**Source**

- API SIRENE

**Objectif**

- identifier les entreprises implantées sur un territoire ;
- filtrer les activités selon les codes NAF industriels ;
- caractériser le poids industriel local.

---

## 3. Données législatives

**Sources**

- Dole
- data.gouv.fr

**Objectif**

Analyser :

- les projets et propositions de loi ;
- les amendements ;
- les questions écrites ;
- les interventions parlementaires.

---

# 🤖 Architecture des agents IA

Le projet adopte une architecture modulaire.

Chaque agent dispose de son propre fichier de contexte (`.md`) afin de séparer clairement les responsabilités et de faciliter les évolutions.

| Agent | Rôle | Fichier de contexte |
|--------|------|---------------------|
| Agent Politique | Analyse législative | `agents/agent_politique.md` |
| Agent Économique | Analyse du tissu industriel | `agents/agent_economique.md` |
| Agent Synthèse | Calcul des scores et recommandations | `agents/agent_synthese.md` |

---

# 📂 Organisation du projet

```text
LobbyIndus/
│
├── agents/
│   ├── agent_politique.md
│   ├── agent_economique.md
│   └── agent_synthese.md
│
├── data/
│
├── services/
│
├── utils/
│
├── app.py
│
└── README.md
```

---

# 🚀 Feuille de route

## Phase 1 — Pipeline de données

- Développer les fonctions d'ingestion des API.
- Convertir les données en DataFrames Pandas.
- Harmoniser les identifiants territoriaux.

---

## Phase 2 — Interface utilisateur

Créer un tableau de bord Streamlit comprenant :

- une vue par territoire ;
- une fiche détaillée par parlementaire ;
- une synthèse générée par IA.

---

## Phase 3 — Intelligence artificielle

- Chargement dynamique des prompts depuis les fichiers `.md`.
- Appels à Gemini Pro.
- Génération des analyses politiques et économiques.

---

## Phase 4 — Visualisation

Intégrer des graphiques interactifs avec Plotly afin de représenter notamment :

- les scores d'appétence ;
- les niveaux d'engagement ;
- les indicateurs territoriaux.

---

# 💡 Bonnes pratiques de développement

## Modularité

Chaque source de données doit disposer de sa propre fonction dédiée.

Exemple :

```python
get_rne_data()
get_sirene_data()
get_legislation_data()
```

---

## Gestion des erreurs

Tous les appels réseau doivent être encapsulés dans des blocs :

```python
try:
    ...
except Exception:
    ...
```

---

## Format des réponses IA

Tous les agents doivent produire **exclusivement du JSON valide**, directement exploitable par l'application.

Exemple :

```json
{
  "score": 87,
  "position": "Favorable",
  "arguments": [
    "...",
    "..."
  ]
}
```

---

## Gestion du contexte

Avant chaque appel à Gemini :

1. Charger le fichier de contexte correspondant (`.md`).
2. Construire le prompt.
3. Interroger le modèle.
4. Parser la réponse JSON.

Cette approche garantit la cohérence des rôles et la reproductibilité des analyses.

---

# 📌 Vision

LobbyIndus a vocation à devenir une plateforme d'intelligence territoriale capable de relier données économiques, activité parlementaire et intelligence artificielle afin d'aider les organisations professionnelles à mieux cibler leurs actions d'affaires publiques et de représentation des intérêts.
