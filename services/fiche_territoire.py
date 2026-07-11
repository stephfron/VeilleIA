"""
Fiche territoire — croisement parlementaire × industrie INSEE SIRENE.

Usage :
    from services.fiche_territoire import rechercher_parlementaire

    fiches = rechercher_parlementaire("Dupont")
    fiches = rechercher_parlementaire("69")          # par code département
    fiches = rechercher_parlementaire("Rhône")       # par libellé département
"""
import pandas as pd
from services.api_rne import get_parlementaires
from services.api_sirene import resume_industrie_dept


def rechercher_parlementaire(query: str) -> list[dict]:
    """
    Recherche un parlementaire par nom, code département ou libellé département.
    Retourne une liste de fiches (plusieurs résultats possibles en cas d'homonymie).

    Chaque fiche contient :
      - infos élu (nom, prénom, chambre, dept, mandat)
      - résumé industriel de son territoire (nb établissements, effectifs, top NAF)
    """
    df = get_parlementaires()
    mask = _build_mask(df, query.strip())
    matches = df[mask]

    if matches.empty:
        return []

    fiches: list[dict] = []
    for _, row in matches.iterrows():
        code_dept = row.get("geo_key") or row.get("code_dept")
        if not code_dept or pd.isna(code_dept):
            continue
        code_dept = str(code_dept)
        industrie = resume_industrie_dept(code_dept)
        fiches.append(_build_fiche(row, industrie))

    return fiches


def _build_mask(df: pd.DataFrame, query: str) -> pd.Series:
    """Construit le masque de recherche (nom, code dept, libellé dept)."""
    q = query.lower()

    mask_nom = (
        df["nom"].str.lower().str.contains(q, na=False)
        | df["prenom"].str.lower().str.contains(q, na=False)
    )

    mask_dept = pd.Series(False, index=df.index)
    if "code_dept" in df.columns:
        mask_dept = mask_dept | df["code_dept"].str.lower().eq(q)
    if "geo_key" in df.columns:
        mask_dept = mask_dept | df["geo_key"].str.lower().eq(q)
    if "libelle_dept" in df.columns:
        mask_dept = mask_dept | df["libelle_dept"].str.lower().str.contains(q, na=False)

    return mask_nom | mask_dept


def _build_fiche(row: pd.Series, industrie: dict) -> dict:
    """Assemble la fiche parlementaire + résumé industriel."""
    chambre = row.get("chambre", "")
    fiche: dict = {
        "parlementaire": {
            "nom": row.get("nom"),
            "prenom": row.get("prenom"),
            "chambre": chambre,
            "sexe": row.get("sexe"),
            "code_dept": row.get("geo_key") or row.get("code_dept"),
            "libelle_dept": row.get("libelle_dept"),
            "date_debut_mandat": _fmt_date(row.get("date_debut_mandat")),
            "libelle_csp": row.get("libelle_csp"),
        },
        "territoire": {
            "nb_etablissements_industriels": industrie["nb_etablissements"],
            "effectifs_estimes": industrie["effectifs_estimes_total"],
            "top_naf": industrie["top_naf"],
        },
    }

    # Champs spécifiques aux députés
    if "libelle_circo" in row and pd.notna(row.get("libelle_circo")):
        fiche["parlementaire"]["circonscription"] = row.get("libelle_circo")
        fiche["parlementaire"]["code_circo"] = row.get("code_circo")

    return fiche


def _fmt_date(val) -> str | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return pd.Timestamp(val).strftime("%Y-%m-%d")
    except Exception:
        return str(val)
