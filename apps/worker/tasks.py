import asyncio

from sqlalchemy import select

from apps.worker.celery_app import celery_app
from packages.core.db.models import FeatureDefinition, Instrument, Timeframe
from packages.core.db.session import SessionLocal
from packages.core.services.analysis import run_analysis_for_symbol
from packages.core.services.ingestion import ingest_instrument_timeframe
from packages.features.engine import compute_feature_definition


async def _compute_features_incremental() -> dict:
    res: dict[str, str] = {}
    async with SessionLocal() as session:
        defs = (await session.execute(select(FeatureDefinition).where(FeatureDefinition.enabled == True))).scalars().all()
        for d in defs:
            if not d.instrument_id:
                continue
            out = await compute_feature_definition(session, d, instrument_id=d.instrument_id, days=7)
            res[d.name] = out.get("status", "unknown")
    return res


@celery_app.task(name="apps.worker.tasks.compute_features_incremental")
def compute_features_incremental() -> dict:
    return asyncio.run(_compute_features_incremental())


@celery_app.task(name="apps.worker.tasks.compute_features_backfill")
def compute_features_backfill(feature_definition_id: int, instrument_id: int, days: int = 30) -> dict:
    async def _run() -> dict:
        async with SessionLocal() as session:
            d = await session.scalar(select(FeatureDefinition).where(FeatureDefinition.id == feature_definition_id))
            if not d:
                return {"status": "failed", "error": "feature_definition not found"}
            return await compute_feature_definition(session, d, instrument_id=instrument_id, days=days)

    return asyncio.run(_run())


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
    await _compute_features_incremental()
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
