import pandas as pd

from packages.features.registry import INDICATOR_REGISTRY


def test_registry_contains_core_indicators() -> None:
    for name in ["sma", "ema", "rsi", "atr", "macd", "bbands", "vwap", "roc", "volume_sma"]:
        assert name in INDICATOR_REGISTRY


def test_ema_output_shape() -> None:
    df = pd.DataFrame({"open": [1, 2, 3], "high": [2, 3, 4], "low": [0.5, 1.5, 2.5], "close": [1, 2, 3], "volume": [10, 11, 12]})
    out = INDICATOR_REGISTRY["ema"]["fn"](df, length=2, source="close")
    assert "value" in out
    assert len(out["value"]) == len(df)
