from datetime import UTC, datetime

import ccxt
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.db.models import Candle, Instrument


async def upsert_instrument(session: AsyncSession, symbol: str, market_type: str = "spot") -> Instrument:
    existing = await session.scalar(
        select(Instrument).where(
            Instrument.symbol == symbol,
            Instrument.exchange == "binance",
            Instrument.type == market_type,
        )
    )
    if existing:
        return existing

    item = Instrument(symbol=symbol, exchange="binance", type=market_type)
    session.add(item)
    await session.flush()
    return item


def fetch_ohlcv(symbol: str, timeframe: str, limit: int = 300) -> list[list[float]]:
    exchange = ccxt.binance({"enableRateLimit": True})
    return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)


async def store_candles(session: AsyncSession, instrument_id: int, timeframe: str, rows: list[list[float]]) -> int:
    inserted = 0
    for row in rows:
        ts = datetime.fromtimestamp(row[0] / 1000, tz=UTC)
        stmt = (
            insert(Candle)
            .values(
                instrument_id=instrument_id,
                timeframe=timeframe,
                ts=ts,
                open=row[1],
                high=row[2],
                low=row[3],
                close=row[4],
                volume=row[5],
            )
            .on_conflict_do_nothing(index_elements=["instrument_id", "timeframe", "ts"])
        )
        result = await session.execute(stmt)
        inserted += result.rowcount or 0
    return inserted
