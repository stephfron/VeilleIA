"""
Ciblage lobbying — répond à « qui contacter en premier ? ».

`cibles_departement()` croise les fiches territoire (déjà en cache, aucun
fetch nouveau) avec le CRM (services/crm.py) et calcule un score de priorité
sur 100, explicable à l'écran :

  - 45 % poids industriel : effectifs du territoire, normalisés sur le
    maximum de la recherche (le plus gros département de la liste = 100) ;
  - 30 % activité législative : amendements + questions (Regards Citoyens,
    best-effort, uniquement si avec_activite=True) ;
  - 25 % fraîcheur du contact : jamais contacté = priorité maximale, un
    contact ancien (≥ 90 jours) redevient prioritaire (relance).
"""
from datetime import date

from services.api_activite import get_activite
from services.crm import elu_key, resume_engagement
from services.fiche_territoire import rechercher_parlementaire

POIDS_INDUSTRIE = 0.45
POIDS_ACTIVITE = 0.30
POIDS_FRAICHEUR = 0.25

SEUIL_RELANCE_JOURS = 90     # au-delà, l'élu redevient prioritaire
PLAFOND_ACTIVITE = 200       # amendements + questions valant un score de 1.0


def _score_fraicheur(dernier_contact: str | None) -> tuple[float, str]:
    """
    Score [0, 1] + motif affichable. Jamais contacté = 1.0 ; dernier contact
    ≥ 90 jours = 0.9 (relance) ; sinon la priorité remonte linéairement avec
    l'ancienneté (jours/90 × 0.6, un contact d'hier écrase la priorité).
    """
    if not dernier_contact:
        return 1.0, "jamais contacté"
    jours = (date.today() - date.fromisoformat(dernier_contact)).days
    motif = f"contacté il y a {jours} j"
    if jours >= SEUIL_RELANCE_JOURS:
        return 0.9, motif
    return max(jours, 0) / SEUIL_RELANCE_JOURS * 0.6, motif


def _score_activite(activite: dict | None) -> float:
    """
    Score [0, 1] : None (activité inconnue) = 0.3 neutre-prudent ; sinon
    somme des amendements et questions, plafonnée à 1.0 vers PLAFOND_ACTIVITE.
    """
    if activite is None:
        return 0.3
    total = sum(
        activite.get(champ) or 0
        for champ in ("amendements_proposes", "questions_ecrites", "questions_orales")
    )
    return min(total / PLAFOND_ACTIVITE, 1.0)


def cibles_departement(
    query: str,
    chambre: str | None = None,
    limit: int = 20,
    avec_activite: bool = False,
) -> list[dict]:
    """
    Liste priorisée des parlementaires à contacter pour une recherche
    (département, code ou nom), triée par score décroissant.

    avec_activite : interroge Regards Citoyens (best-effort, plus lent) pour
    pondérer par l'activité législative réelle ; sinon composante neutre.

    Chaque cible : parlementaire, territoire, statut, nb_interactions,
    dernier_contact, score (/100) et detail_score (composantes /100 +
    motif_fraicheur) pour rendre le score explicable à l'écran.
    """
    fiches = rechercher_parlementaire(query, limit=limit, chambre=chambre)
    if not fiches:
        return []

    engagement = resume_engagement()
    max_effectifs = max(f["territoire"]["effectifs_estimes"] or 0 for f in fiches)

    cibles: list[dict] = []
    for fiche in fiches:
        parl = fiche["parlementaire"]
        suivi = engagement.get(elu_key(parl["nom"], parl["prenom"]), {})

        effectifs = fiche["territoire"]["effectifs_estimes"] or 0
        part_industrie = effectifs / max_effectifs if max_effectifs else 0.0

        activite = None
        if avec_activite:
            try:
                activite = get_activite(parl["nom"], parl["prenom"], parl["chambre"])
            except Exception:
                activite = None  # source citoyenne best-effort : composante neutre
        part_activite = _score_activite(activite)

        dernier_contact = suivi.get("dernier_contact")
        part_fraicheur, motif = _score_fraicheur(dernier_contact)

        score = (
            POIDS_INDUSTRIE * part_industrie
            + POIDS_ACTIVITE * part_activite
            + POIDS_FRAICHEUR * part_fraicheur
        ) * 100

        cibles.append({
            "parlementaire": parl,
            "territoire": fiche["territoire"],
            "statut": suivi.get("statut", "a_contacter"),
            "nb_interactions": suivi.get("nb_interactions", 0),
            "dernier_contact": dernier_contact,
            "score": round(score, 1),
            "detail_score": {
                "industrie": round(part_industrie * 100, 1),
                "activite": round(part_activite * 100, 1),
                "fraicheur": round(part_fraicheur * 100, 1),
                "motif_fraicheur": motif,
            },
        })

    cibles.sort(key=lambda c: c["score"], reverse=True)
    return cibles
