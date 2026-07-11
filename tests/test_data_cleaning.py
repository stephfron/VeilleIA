import pandas as pd
import pytest

from utils.data_cleaning import normalize_dept, normalize_dept_column, fmt_date


@pytest.mark.parametrize("raw, expected", [
    ("1", "01"),
    ("01", "01"),
    ("75", "75"),
    ("2A", "2A"),
    ("2b", "2B"),
    ("971", "971"),
    (75, "75"),
])
def test_normalize_dept(raw, expected):
    assert normalize_dept(raw) == expected


def test_normalize_dept_column_does_not_mutate_input():
    df = pd.DataFrame({"code_dept": ["1", "75"]})
    out = normalize_dept_column(df, "code_dept")
    assert list(out["code_dept"]) == ["01", "75"]
    assert list(df["code_dept"]) == ["1", "75"]  # copy-safe : l'original n'est pas modifié


@pytest.mark.parametrize("raw, expected", [
    (None, None),
    (float("nan"), None),
    ("2024-01-15", "2024-01-15"),
    (pd.Timestamp("2024-01-15"), "2024-01-15"),
])
def test_fmt_date(raw, expected):
    assert fmt_date(raw) == expected
