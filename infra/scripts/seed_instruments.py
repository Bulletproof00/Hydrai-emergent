import asyncio
from datetime import UTC, datetime

from sqlalchemy import select

from packages.core.db.models import AgentConfig, AppSetting, Instrument, ProviderConfig, Timeframe
from packages.core.db.session import SessionLocal


DEFAULT_INSTRUMENTS = [
    ("BTCUSDT", "Bitcoin", "crypto", "spot", "24_7"),
    ("ETHUSDT", "Ethereum", "crypto", "spot", "24_7"),
    ("XAUUSD", "Gold", "metals", "spot", "weekday"),
    ("XAGUSD", "Silver", "metals", "spot", "weekday"),
    ("SPX", "S&P500", "index", "index", "weekday"),
]
DEFAULT_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]
DEFAULT_AGENTS = ["RegimeDetectionAgent", "MarketStructureAgent", "AnomalyDetectionAgent", "CorrelationAgent", "SessionAwarenessAgent"]


async def main() -> None:
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        demo = await session.scalar(select(ProviderConfig).where(ProviderConfig.name == "Demo CSV"))
        if not demo:
            demo = ProviderConfig(provider_type="demo_csv", name="Demo CSV", enabled=True, settings_jsonb={"data_dir": "data"}, secret_encrypted=None, created_at=now, updated_at=now)
            session.add(demo)
            await session.flush()

        binance = await session.scalar(select(ProviderConfig).where(ProviderConfig.name == "Binance Spot"))
        if not binance:
            binance = ProviderConfig(provider_type="binance_spot", name="Binance Spot", enabled=True, settings_jsonb={}, secret_encrypted=None, created_at=now, updated_at=now)
            session.add(binance)
            await session.flush()

        for sym, dn, ac, mt, sess in DEFAULT_INSTRUMENTS:
            item = await session.scalar(select(Instrument).where(Instrument.symbol == sym))
            if not item:
                provider_id = binance.id if ac == "crypto" else demo.id
                session.add(Instrument(symbol=sym, display_name=dn, asset_class=ac, market_type=mt, session_type=sess, timezone="UTC", provider_id=provider_id))

        for tf in DEFAULT_TIMEFRAMES:
            if not await session.scalar(select(Timeframe).where(Timeframe.code == tf)):
                session.add(Timeframe(code=tf))

        for a in DEFAULT_AGENTS:
            cfg = await session.scalar(select(AgentConfig).where(AgentConfig.agent_name == a))
            if not cfg:
                session.add(AgentConfig(agent_name=a, enabled=True, mode="deterministic", provider="gemini", model="gemini-1.5-flash", system_prompt=f"You are {a}. Return concise JSON.", user_prompt_template="Analyze {{symbol}} with deterministic context.", temperature=0.2, max_tokens=400, timeout_s=20, tools_allowed_jsonb={}, updated_at=now))

        defaults = {
            "schedule.ingest_crypto_s": {"value": 60},
            "schedule.ingest_macro_s": {"value": 300},
            "schedule.analysis_s": {"value": 300},
            "strategy.weights_version": {"value": "v1"},
        }
        for k, v in defaults.items():
            row = await session.scalar(select(AppSetting).where(AppSetting.key == k))
            if not row:
                session.add(AppSetting(key=k, value_jsonb=v, updated_at=now))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
