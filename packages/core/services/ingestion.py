from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.db.models import Candle, Instrument, ProviderConfig
from packages.core.crypto import decrypt_secret
from packages.core.config.settings import get_settings
from packages.providers import build_provider


async def get_provider_for_instrument(session: AsyncSession, instrument: Instrument):
    if instrument.provider_id:
        cfg = await session.scalar(select(ProviderConfig).where(ProviderConfig.id == instrument.provider_id))
    else:
        cfg = await session.scalar(select(ProviderConfig).where(ProviderConfig.enabled == True).order_by(ProviderConfig.id.asc()))
    if not cfg:
        return None
    cfg_settings = dict(cfg.settings_jsonb or {})
    if cfg.secret_encrypted:
        cfg_settings["api_key"] = decrypt_secret(get_settings().chainalyze_master_key, cfg.secret_encrypted)
    return build_provider(cfg.provider_type, cfg_settings)


async def ingest_instrument_timeframe(session: AsyncSession, instrument: Instrument, timeframe: str) -> int:
    provider = await get_provider_for_instrument(session, instrument)
    if not provider:
        return 0
    rows = provider.fetch_ohlcv(instrument.symbol, timeframe)
    inserted = 0
    for row in rows:
        stmt = (
            insert(Candle)
            .values(
                instrument_id=instrument.id,
                timeframe=timeframe,
                ts=row.ts,
                o=row.o,
                h=row.h,
                l=row.l,
                c=row.c,
                volume=row.volume,
            )
            .on_conflict_do_nothing(index_elements=["instrument_id", "timeframe", "ts"])
        )
        result = await session.execute(stmt)
        inserted += result.rowcount or 0
    return inserted
