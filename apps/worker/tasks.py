import asyncio

from sqlalchemy import select

from apps.worker.celery_app import celery_app
from packages.core.db.models import Instrument, Timeframe
from packages.core.db.session import SessionLocal
from packages.core.services.analysis import run_analysis_for_symbol
from packages.core.services.ingestion import ingest_instrument_timeframe


async def _ingest() -> dict:
    result: dict[str, int] = {}
    async with SessionLocal() as session:
        instruments = (await session.execute(select(Instrument))).scalars().all()
        tfs = [t.code for t in (await session.execute(select(Timeframe))).scalars().all()] or ["5m"]
        for inst in instruments:
            for tf in tfs:
                ins = await ingest_instrument_timeframe(session, inst, tf)
                result[f"{inst.symbol}:{tf}"] = ins
        await session.commit()
    return result


@celery_app.task(name="apps.worker.tasks.ingest_candles")
def ingest_candles() -> dict:
    return asyncio.run(_ingest())


async def _analyze() -> list[str]:
    run_ids: list[str] = []
    async with SessionLocal() as session:
        instruments = (await session.execute(select(Instrument))).scalars().all()
        for inst in instruments:
            run_ids.append(await run_analysis_for_symbol(session, symbol=inst.symbol, timeframe="5m"))
    return run_ids


@celery_app.task(name="apps.worker.tasks.run_analysis")
def run_analysis() -> list[str]:
    return asyncio.run(_analyze())
