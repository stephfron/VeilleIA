import pandas as pd


def normalize_dept(code: str) -> str:
    """Normalise un code département : '1' → '01', '2A' → '2A'."""
    code = str(code).strip().upper()
    if code in ("2A", "2B"):
        return code
    return code.zfill(2)


def normalize_dept_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Applique normalize_dept sur une colonne d'un DataFrame."""
    df = df.copy()
    df[col] = df[col].apply(normalize_dept)
    return df
