import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.agents.anomaly_detection import AnomalyDetectionAgent
from packages.agents.correlation_macro import CorrelationMacroAgent
from packages.agents.derivatives_stress import DerivativesStressAgent
from packages.agents.framework import AgentContext
from packages.agents.market_structure import MarketStructureAgent
from packages.agents.regime_detection import RegimeDetectionAgent
from packages.core.db.models import AnalysisRun, Candle, Finding, Instrument, Signal, SupervisorReport
from packages.strategies.supervisors import (
    drift_supervisor,
    overfit_risk_supervisor,
    risk_coherence_supervisor,
)
from packages.strategies.synthesis import synthesize_signal


async def run_analysis_for_symbol(session: AsyncSession, symbol: str, timeframe: str = "5m") -> str:
    run_id = str(uuid.uuid4())
    config = {"symbol": symbol, "timeframe": timeframe, "agents": 5}
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()

    run = AnalysisRun(run_id=run_id, ts_start=datetime.now(UTC), config_hash=config_hash, status="running")
    session.add(run)

    inst = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
    if not inst:
        run.status = "failed"
        run.ts_end = datetime.now(UTC)
        await session.commit()
        return run_id

    rows = await session.execute(
        select(Candle)
        .where(Candle.instrument_id == inst.id, Candle.timeframe == timeframe)
        .order_by(Candle.ts.desc())
        .limit(300)
    )
    candles = list(reversed(rows.scalars().all()))
    if not candles:
        run.status = "failed"
        run.ts_end = datetime.now(UTC)
        await session.commit()
        return run_id

    df = pd.DataFrame(
        [{"ts": c.ts, "open": c.open, "high": c.high, "low": c.low, "close": c.close, "volume": c.volume} for c in candles]
    )

    context = AgentContext(run_id=run_id, symbol=symbol, timeframe=timeframe, candles=df)
    agents = [
        MarketStructureAgent(),
        RegimeDetectionAgent(),
        DerivativesStressAgent(),
        AnomalyDetectionAgent(),
        CorrelationMacroAgent(),
    ]

    findings = []
    for agent in agents:
        findings.extend(agent.run(context))

    for finding in findings:
        session.add(
            Finding(
                run_id=run_id,
                agent_name=finding.agent_name,
                symbol=symbol,
                ts=finding.ts,
                payload_json={**finding.payload, "tags": finding.tags, "confidence": finding.confidence},
                severity=finding.severity,
            )
        )

    signal = synthesize_signal(symbol=symbol, findings=findings)
    session.add(
        Signal(
            run_id=run_id,
            instrument_id=inst.id,
            ts=signal["ts"],
            direction=signal["direction"],
            confidence=signal["confidence"],
            invalidation=signal["invalidation"],
            metadata_json=signal["metadata"],
        )
    )

    finding_dicts = [f.model_dump() for f in findings]
    reports = [
        drift_supervisor(run_id, finding_dicts),
        overfit_risk_supervisor(run_id, signal),
        risk_coherence_supervisor(run_id, finding_dicts, signal),
    ]
    for report in reports:
        session.add(SupervisorReport(**report))

    run.status = "completed"
    run.ts_end = datetime.now(UTC)
    await session.commit()
    return run_id
