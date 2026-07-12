"""
Dossier de synthèse par parlementaire — socle de la future fonction IA.

`constituer_dossier()` agrège tout ce qu'une génération de synthèse aura
besoin de connaître : l'élu, son territoire industriel, son activité
législative et les textes récents pertinents. Le résultat est un dict
JSON-safe, stable, pensé comme *contexte* à passer à un LLM.

`generer_synthese()` est le point d'extension IA (second temps) : il reçoit
un dossier complet et devra retourner une synthèse rédigée. L'implémentation
appellera l'API Claude (voir le skill claude-api pour les modèles et le SDK) ;
tant qu'elle n'existe pas, elle retourne None et l'API expose
`synthese_status = "non_implementee"`.
"""
from datetime import date

from services.api_activite import get_activite
from services.api_dole import rechercher_textes
from services.fiche_territoire import fiche_par_identite

# Mots-clés utilisés pour rattacher des textes législatifs récents au dossier
# tant qu'aucune thématique n'est fournie par l'appelant.
_THEMES_DEFAUT = "industrie production manufacturière usine"


def constituer_dossier(nom: str, prenom: str, themes: str | None = None) -> dict | None:
    """
    Assemble le dossier complet d'un parlementaire (None si introuvable).

    themes : mots-clés métier pour sélectionner les textes pertinents
             (défaut : vocabulaire industriel générique).
    """
    fiche = fiche_par_identite(nom, prenom)
    if fiche is None:
        return None

    parl = fiche["parlementaire"]
    activite = get_activite(parl["nom"], parl["prenom"], parl["chambre"])

    # Fenêtre de 10 ans : une synthèse de rendez-vous ne doit pas présenter
    # une loi des années 90 comme de la législation d'actualité.
    textes = rechercher_textes(themes or _THEMES_DEFAUT, top_n=5, annee_min=date.today().year - 10)
    textes_pertinents = (
        textes[["title", "category_label", "annee", "article_synthesis", "score"]]
        .astype(object)
        .where(textes.notna(), None)
        .to_dict("records")
        if not textes.empty
        else []
    )

    dossier = {
        "parlementaire": parl,
        "territoire": fiche["territoire"],
        "activite_legislative": activite,          # None si source citoyenne KO
        "textes_pertinents": textes_pertinents,
        "themes": themes or _THEMES_DEFAUT,
    }
    # --- Espace réservé à la fonction IA (second temps) ---
    synthese = generer_synthese(dossier)
    dossier["synthese"] = synthese
    dossier["synthese_status"] = "ok" if synthese else "non_implementee"
    return dossier


def generer_synthese(dossier: dict) -> str | None:
    """
    Point d'extension IA — à implémenter dans un second temps.

    Contrat prévu : reçoit le dossier complet (dict ci-dessus), retourne une
    synthèse rédigée en français (profil de l'élu, poids industriel du
    territoire, angles d'approche) destinée à préparer un rendez-vous.
    Implémentation envisagée : API Claude, prompt structuré sur le dossier.
    """
    return None
