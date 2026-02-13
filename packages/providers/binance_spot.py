from datetime import UTC, datetime

import ccxt

from packages.providers.base import CandlePoint


class BinanceSpotProvider:
    provider_type = "binance_spot"
    capabilities = {"supports_ohlcv": True, "supports_symbols": True}

    def __init__(self, api_key: str | None = None, secret: str | None = None) -> None:
        cfg = {"enableRateLimit": True}
        if api_key and secret:
            cfg.update({"apiKey": api_key, "secret": secret})
        self.exchange = ccxt.binance(cfg)

    def fetch_ohlcv(self, symbol: str, timeframe: str, since: datetime | None = None, until: datetime | None = None) -> list[CandlePoint]:
        since_ms = int(since.timestamp() * 1000) if since else None
        rows = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=500)
        data = [
            CandlePoint(
                ts=datetime.fromtimestamp(r[0] / 1000, tz=UTC), o=r[1], h=r[2], l=r[3], c=r[4], volume=r[5]
            )
            for r in rows
        ]
        return [r for r in data if until is None or r.ts <= until]
