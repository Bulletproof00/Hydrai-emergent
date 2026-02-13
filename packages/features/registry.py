from __future__ import annotations

import numpy as np
import pandas as pd


def _source_series(df: pd.DataFrame, source: str) -> pd.Series:
    if source == "hl2":
        return (df["high"] + df["low"]) / 2
    if source == "ohlc4":
        return (df["open"] + df["high"] + df["low"] + df["close"]) / 4
    return df[source]


def sma(df: pd.DataFrame, length: int = 14, source: str = "close") -> dict[str, pd.Series]:
    s = _source_series(df, source)
    return {"value": s.rolling(length).mean()}


def ema(df: pd.DataFrame, length: int = 14, source: str = "close") -> dict[str, pd.Series]:
    s = _source_series(df, source)
    return {"value": s.ewm(span=length, adjust=False).mean()}


def rsi(df: pd.DataFrame, length: int = 14, source: str = "close") -> dict[str, pd.Series]:
    s = _source_series(df, source)
    delta = s.diff()
    up = delta.clip(lower=0).rolling(length).mean()
    down = (-delta.clip(upper=0)).rolling(length).mean()
    rs = up / down.replace(0, np.nan)
    return {"value": 100 - (100 / (1 + rs))}


def atr(df: pd.DataFrame, length: int = 14) -> dict[str, pd.Series]:
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    return {"value": tr.rolling(length).mean()}


def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, source: str = "close") -> dict[str, pd.Series]:
    s = _source_series(df, source)
    macd_line = s.ewm(span=fast, adjust=False).mean() - s.ewm(span=slow, adjust=False).mean()
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return {"macd_line": macd_line, "signal_line": signal_line, "hist": hist}


def bbands(df: pd.DataFrame, length: int = 20, stddev: float = 2.0, source: str = "close") -> dict[str, pd.Series]:
    s = _source_series(df, source)
    mid = s.rolling(length).mean()
    std = s.rolling(length).std()
    return {"bb_mid": mid, "bb_upper": mid + stddev * std, "bb_lower": mid - stddev * std}


def vwap(df: pd.DataFrame) -> dict[str, pd.Series]:
    pv = (df["close"] * df["volume"]).cumsum()
    vol = df["volume"].replace(0, np.nan).cumsum()
    return {"value": pv / vol}


def roc(df: pd.DataFrame, length: int = 12, source: str = "close") -> dict[str, pd.Series]:
    s = _source_series(df, source)
    return {"value": s.pct_change(length) * 100}


def volume_sma(df: pd.DataFrame, length: int = 20) -> dict[str, pd.Series]:
    return {"value": df["volume"].rolling(length).mean()}


INDICATOR_REGISTRY = {
    "sma": {"fn": sma, "params": {"length": "int", "source": "str"}},
    "ema": {"fn": ema, "params": {"length": "int", "source": "str"}},
    "rsi": {"fn": rsi, "params": {"length": "int", "source": "str"}},
    "atr": {"fn": atr, "params": {"length": "int"}},
    "macd": {"fn": macd, "params": {"fast": "int", "slow": "int", "signal": "int", "source": "str"}},
    "bbands": {"fn": bbands, "params": {"length": "int", "stddev": "float", "source": "str"}},
    "vwap": {"fn": vwap, "params": {}},
    "roc": {"fn": roc, "params": {"length": "int", "source": "str"}},
    "volume_sma": {"fn": volume_sma, "params": {"length": "int"}},
}
