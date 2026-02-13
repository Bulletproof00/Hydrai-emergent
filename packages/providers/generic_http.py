from datetime import datetime

from packages.providers.base import CandlePoint


class GenericHTTPProvider:
    provider_type = "generic_http"
    capabilities = {"supports_ohlcv": False, "stub": True}

    def __init__(self, settings: dict | None = None) -> None:
        self.settings = settings or {}

    def fetch_ohlcv(self, symbol: str, timeframe: str, since: datetime | None = None, until: datetime | None = None) -> list[CandlePoint]:
        return []
