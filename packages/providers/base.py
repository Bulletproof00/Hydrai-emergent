from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class CandlePoint:
    ts: datetime
    o: float
    h: float
    l: float
    c: float
    volume: float


class BaseMarketDataProvider(Protocol):
    provider_type: str
    capabilities: dict

    def fetch_ohlcv(self, symbol: str, timeframe: str, since: datetime | None = None, until: datetime | None = None) -> list[CandlePoint]:
        ...
