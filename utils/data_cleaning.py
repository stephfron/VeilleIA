"""
Fonctions de nettoyage et normalisation partagées.
"""
import pandas as pd


def normalize_dept(code: str) -> str:
    """Normalise un code département : '1' → '01', '2A' → '2A', '971' → '971'."""
    code = str(code).strip().upper()
    if code in ("2A", "2B"):
        return code
    if len(code) >= 3:          # DOM/TOM : 971, 972, 973, 974, 976
        return code
    return code.zfill(2)


def normalize_dept_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Applique normalize_dept sur une colonne d'un DataFrame (copy-safe)."""
    df = df.copy()
    df[col] = df[col].apply(normalize_dept)
    return df


def fmt_date(val: object) -> str | None:
    """Formate une valeur date/Timestamp en 'YYYY-MM-DD', ou None si invalide."""
    if val is None:
        return None
    try:
        ts = pd.Timestamp(val)  # type: ignore[arg-type]
        if pd.isna(ts):
            return None
        return ts.strftime("%Y-%m-%d")
    except Exception:
        return str(val)
