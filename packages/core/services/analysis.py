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
from packages.core.config_hash import compute_config_hash
from packages.core.db.models import (
    AgentConfig,
    AnalysisRun,
    AppSetting,
    Candle,
    Finding,
    Instrument,
    ProviderConfig,
    Signal,
    SupervisorReport,
)
from packages.strategies.synthesis import synthesize_signal
from packages.supervisors import DataQualitySupervisor, DriftSupervisor, OverfitRiskSupervisor, RiskCoherenceSupervisor


async def _build_snapshot(session: AsyncSession) -> dict:
    agents = (await session.execute(select(AgentConfig))).scalars().all()
    providers = (await session.execute(select(ProviderConfig).where(ProviderConfig.enabled == True))).scalars().all()
    instruments = (await session.execute(select(Instrument))).scalars().all()
    app_settings = (await session.execute(select(AppSetting))).scalars().all()
    return {
        "agents": [
            {
                "agent_name": a.agent_name,
                "enabled": a.enabled,
                "mode": a.mode,
                "provider": a.provider,
                "model": a.model,
                "temperature": a.temperature,
                "max_tokens": a.max_tokens,
                "timeout_s": a.timeout_s,
            }
            for a in agents
        ],
        "providers": [
            {
                "id": p.id,
                "provider_type": p.provider_type,
                "name": p.name,
                "enabled": p.enabled,
                "settings_jsonb": p.settings_jsonb,
            }
            for p in providers
        ],
        "instruments": [
            {"symbol": i.symbol, "provider_id": i.provider_id, "asset_class": i.asset_class}
            for i in instruments
        ],
        "app_settings": [{"key": s.key, "value": s.value_jsonb} for s in app_settings],
    }


async def run_analysis_for_symbol(session: AsyncSession, symbol: str, timeframe: str = "5m") -> str:
    run_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    snapshot = await _build_snapshot(session)
    config_hash = compute_config_hash(snapshot)

    run = AnalysisRun(
        run_id=run_id,
        created_at=now,
        window_start=now - timedelta(hours=24),
        window_end=now,
        status="running",
        config_hash=config_hash,
        metadata_jsonb=snapshot,
    )
    session.add(run)

    inst = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
    if not inst:
        run.status = "failed"
        await session.commit()
        return run_id

    rows = (
        await session.execute(
            select(Candle)
            .where(Candle.instrument_id == inst.id, Candle.timeframe == timeframe)
            .order_by(Candle.ts.desc())
            .limit(300)
        )
    ).scalars().all()
    candles = list(reversed(rows))
    if not candles:
        run.status = "failed"
        await session.commit()
        return run_id

    df = pd.DataFrame([{"ts": c.ts, "open": c.o, "high": c.h, "low": c.l, "close": c.c, "volume": c.volume} for c in candles])
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

    for f in findings:
        session.add(
            Finding(
                run_id=run_id,
                instrument_id=inst.id,
                agent_name=f.agent_name,
                ts=f.ts,
                kind=f.payload.get("state", f.payload.get("regime", "generic")),
                severity=min(100, max(0, int(f.confidence * 100))),
                confidence=f.confidence,
                tags=f.tags,
                payload_jsonb=f.payload,
                llm_status="disabled",
                created_at=now,
            )
        )

    signal = synthesize_signal(symbol=symbol, findings=findings)
    session.add(
        Signal(
            run_id=run_id,
            instrument_id=inst.id,
            ts=signal["ts"],
            direction="neutral" if signal["direction"] == "hold" else signal["direction"],
            confidence=signal["confidence"],
            invalidation_level=signal["invalidation"],
            horizon="1h",
            metadata_jsonb=signal["metadata"],
            created_at=now,
        )
    )

    sup_instances = [DataQualitySupervisor(), DriftSupervisor(), OverfitRiskSupervisor(), RiskCoherenceSupervisor()]
    finding_dicts = [dict(tags=f.tags, severity=f.severity, payload=f.payload) for f in findings]
    for sup in sup_instances:
        rep = sup.run(finding_dicts, signal)
        session.add(
            SupervisorReport(
                run_id=run_id,
                instrument_id=inst.id,
                supervisor_name=rep.supervisor_name,
                ts=rep.ts,
                verdict=rep.verdict,
                payload_jsonb=rep.payload,
                created_at=now,
            )
        )

    run.status = "completed"
    await session.commit()
    return run_id
