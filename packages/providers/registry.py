from packages.providers.binance_spot import BinanceSpotProvider
from packages.providers.demo_csv import DemoCSVProvider
from packages.providers.generic_http import GenericHTTPProvider

PROVIDER_REGISTRY = {
    "binance_spot": BinanceSpotProvider,
    "demo_csv": DemoCSVProvider,
    "generic_http": GenericHTTPProvider,
}


def build_provider(provider_type: str, settings: dict | None = None):
    cls = PROVIDER_REGISTRY.get(provider_type)
    if not cls:
        raise ValueError(f"Unknown provider_type={provider_type}")
    settings = settings or {}
    return cls(**settings)
