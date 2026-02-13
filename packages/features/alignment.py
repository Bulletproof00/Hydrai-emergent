import pandas as pd


def align_to_index(series: pd.Series, index: pd.Index, ffill: bool = True) -> pd.Series:
    out = series.reindex(index)
    return out.ffill() if ffill else out
