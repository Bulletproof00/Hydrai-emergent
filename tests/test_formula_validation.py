import pandas as pd

from packages.features.formulas import evaluate_formula, validate_formula


def test_validate_formula_safe() -> None:
    validate_formula("close > ema_200")


def test_evaluate_formula_series() -> None:
    idx = pd.date_range("2026-01-01", periods=3, freq="h", tz="UTC")
    data = {"close": pd.Series([1, 2, 3], index=idx), "ema_200": pd.Series([0.5, 1.5, 2.5], index=idx)}
    out = evaluate_formula("close > ema_200", data)
    assert bool(out.iloc[-1]) is True
