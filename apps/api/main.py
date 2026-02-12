from fastapi import Depends, FastAPI, Query
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.db.models import AnalysisRun, Candle, Finding, Instrument, Signal, SupervisorReport
from packages.core.db.session import get_db_session
from packages.core.schemas.analysis import FindingOut, SignalOut
from packages.observability.logging import configure_logging

configure_logging()
app = FastAPI(title="CHAiNALYZE API", version="0.1.0")
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/instruments")
async def instruments(session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    rows = (await session.execute(select(Instrument))).scalars().all()
    return [{"id": i.id, "symbol": i.symbol, "exchange": i.exchange, "type": i.type} for i in rows]


@app.get("/candles")
async def candles(
    symbol: str,
    tf: str = Query("5m"),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    inst = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
    if not inst:
        return []
    rows = (
        await session.execute(
            select(Candle)
            .where(Candle.instrument_id == inst.id, Candle.timeframe == tf)
            .order_by(Candle.ts.desc())
            .limit(500)
        )
    ).scalars().all()
    return [
        {
            "ts": r.ts,
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume,
        }
        for r in reversed(rows)
    ]


@app.get("/latest/findings", response_model=list[FindingOut])
async def latest_findings(symbol: str, session: AsyncSession = Depends(get_db_session)) -> list[FindingOut]:
    rows = (
        await session.execute(select(Finding).where(Finding.symbol == symbol).order_by(Finding.ts.desc()).limit(20))
    ).scalars().all()
    return [
        FindingOut(
            agent_name=f.agent_name,
            symbol=f.symbol,
            ts=f.ts,
            severity=f.severity,
            tags=f.payload_json.get("tags", []),
            payload=f.payload_json,
        )
        for f in rows
    ]


@app.get("/latest/signals", response_model=list[SignalOut])
async def latest_signals(symbol: str, session: AsyncSession = Depends(get_db_session)) -> list[SignalOut]:
    inst = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
    if not inst:
        return []
    rows = (
        await session.execute(select(Signal).where(Signal.instrument_id == inst.id).order_by(Signal.ts.desc()).limit(20))
    ).scalars().all()
    return [
        SignalOut(
            symbol=symbol,
            ts=s.ts,
            direction=s.direction,
            confidence=s.confidence,
            invalidation=s.invalidation,
            metadata=s.metadata_json,
        )
        for s in rows
    ]


@app.get("/runs/{run_id}")
async def run_details(run_id: str, session: AsyncSession = Depends(get_db_session)) -> dict:
    run = await session.scalar(select(AnalysisRun).where(AnalysisRun.run_id == run_id))
    if not run:
        return {"error": "run not found"}
    reports = (
        await session.execute(select(SupervisorReport).where(SupervisorReport.run_id == run_id))
    ).scalars().all()
    return {
        "run_id": run.run_id,
        "status": run.status,
        "config_hash": run.config_hash,
        "ts_start": run.ts_start,
        "ts_end": run.ts_end,
        "supervisor_reports": [
            {"name": r.supervisor_name, "verdict": r.verdict, "payload": r.payload_json} for r in reports
        ],
    }
