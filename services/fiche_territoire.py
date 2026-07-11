"""
Fiche territoire — croisement parlementaire × industrie INSEE SIRENE.

Usage :
    from services.fiche_territoire import rechercher_parlementaire

    fiches = rechercher_parlementaire("Dupont")      # par nom
    fiches = rechercher_parlementaire("69")          # par code département
    fiches = rechercher_parlementaire("Rhône")       # par libellé département
"""
import pandas as pd
from services.api_rne import get_parlementaires
from services.api_sirene import resume_industrie_dept
from utils.data_cleaning import fmt_date


def rechercher_parlementaire(query: str) -> list[dict]:
    """
    Recherche un parlementaire par nom, code département ou libellé département.
    Retourne une liste de fiches (homonymie possible → plusieurs résultats).

    Chaque fiche :
      parlementaire : nom, prénom, chambre, dept, circonscription, mandat, CSP
      territoire    : nb établissements industriels, effectifs estimés, top NAF
    """
    df = get_parlementaires()
    matches = df[_mask(df, query.strip())]
    if matches.empty:
        return []

    return [_build_fiche(row) for _, row in matches.iterrows() if _geo_key(row)]


# ---------------------------------------------------------------------------
# Helpers privés
# ---------------------------------------------------------------------------

def _geo_key(row: pd.Series) -> str | None:
    """Retourne le code géographique utilisable pour SIRENE, ou None."""
    key = row.get("geo_key") or row.get("code_dept")
    if key is None or (isinstance(key, float) and pd.isna(key)):
        return None
    return str(key)


def _mask(df: pd.DataFrame, query: str) -> pd.Series:
    q = query.lower()

    mask_nom = (
        df["nom"].str.lower().str.contains(q, na=False)
        | df["prenom"].str.lower().str.contains(q, na=False)
    )

    mask_dept = pd.Series(False, index=df.index)
    for col in ("code_dept", "geo_key"):
        if col in df.columns:
            mask_dept |= df[col].str.lower().eq(q)
    if "libelle_dept" in df.columns:
        mask_dept |= df["libelle_dept"].str.lower().str.contains(q, na=False)

    return mask_nom | mask_dept


def _build_fiche(row: pd.Series) -> dict:
    code_dept = _geo_key(row)
    industrie = resume_industrie_dept(code_dept) if code_dept else {}

    parl: dict = {
        "nom":               row.get("nom"),
        "prenom":            row.get("prenom"),
        "chambre":           row.get("chambre"),
        "sexe":              row.get("sexe"),
        "code_dept":         code_dept,
        "libelle_dept":      row.get("libelle_dept"),
        "date_debut_mandat": fmt_date(row.get("date_debut_mandat")),
        "libelle_csp":       row.get("libelle_csp"),
    }

    if pd.notna(row.get("libelle_circo")):
        parl["circonscription"] = row.get("libelle_circo")
        parl["code_circo"]      = row.get("code_circo")

    return {
        "parlementaire": parl,
        "territoire": {
            "nb_etablissements_industriels": industrie.get("nb_etablissements", 0),
            "effectifs_estimes":             industrie.get("effectifs_estimes_total", 0),
            "top_naf":                       industrie.get("top_naf", []),
        },
    }
