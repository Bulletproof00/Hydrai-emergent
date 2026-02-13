from datetime import UTC, datetime

from packages.agents.framework import Finding
from packages.strategies.synthesis import synthesize_signal


def test_synthesize_signal_returns_structure() -> None:
    findings = [
        Finding(
            agent_name="MarketStructureAgent",
            symbol="BTC/USDT",
            ts=datetime.now(UTC),
            confidence=0.7,
            payload={"state": "bos_up"},
        )
    ]
    signal = synthesize_signal("BTC/USDT", findings)
    assert signal["symbol"] == "BTC/USDT"
    assert signal["direction"] in {"long", "short", "hold"}
