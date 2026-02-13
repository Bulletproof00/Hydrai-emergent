from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from packages.providers.base import CandlePoint


class DemoCSVProvider:
    provider_type = "demo_csv"
    capabilities = {"supports_ohlcv": True, "supports_symbols": True, "offline": True}

    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)

    def fetch_ohlcv(self, symbol: str, timeframe: str, since: datetime | None = None, until: datetime | None = None) -> list[CandlePoint]:
        f = self.data_dir / f"{symbol}_{timeframe}.csv"
        if not f.exists():
            return []
        df = pd.read_csv(f)
        df["ts"] = pd.to_datetime(df["ts"], utc=True)
        if since is not None:
            df = df[df["ts"] >= since]
        if until is not None:
            df = df[df["ts"] <= until]
        return [
            CandlePoint(ts=row.ts.to_pydatetime().astimezone(UTC), o=row.open, h=row.high, l=row.low, c=row.close, volume=row.volume)
            for row in df.itertuples(index=False)
        ]
