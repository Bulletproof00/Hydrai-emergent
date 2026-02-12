import asyncio

from apps.worker.celery_app import celery_app
from packages.core.config.settings import get_settings
from packages.core.db.session import SessionLocal
from packages.core.services.analysis import run_analysis_for_symbol
from packages.core.services.ingestion import fetch_ohlcv, store_candles, upsert_instrument

settings = get_settings()


async def _ingest() -> dict:
    symbols = [s.strip() for s in settings.symbols.split(",") if s.strip()]
    timeframes = [t.strip() for t in settings.timeframes.split(",") if t.strip()]
    result: dict[str, int] = {}
    async with SessionLocal() as session:
        for symbol in symbols:
            inst = await upsert_instrument(session, symbol)
            for tf in timeframes:
                rows = fetch_ohlcv(symbol, tf)
                inserted = await store_candles(session, inst.id, tf, rows)
                result[f"{symbol}:{tf}"] = inserted
        await session.commit()
    return result


@celery_app.task(name="apps.worker.tasks.ingest_candles")
def ingest_candles() -> dict:
    return asyncio.run(_ingest())


async def _analyze() -> list[str]:
    symbols = [s.strip() for s in settings.symbols.split(",") if s.strip()]
    run_ids: list[str] = []
    async with SessionLocal() as session:
        for symbol in symbols:
            run_id = await run_analysis_for_symbol(session, symbol=symbol, timeframe="5m")
            run_ids.append(run_id)
    return run_ids


@celery_app.task(name="apps.worker.tasks.run_analysis")
def run_analysis() -> list[str]:
    return asyncio.run(_analyze())
