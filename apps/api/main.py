from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.config.settings import get_settings
from packages.core.crypto import encrypt_secret
from packages.core.db.models import (
    AgentConfig,
    AgentPromptVersion,
    AnalysisRun,
    AppSetting,
    Candle,
    Finding,
    Instrument,
    LLMConfig,
    ProviderConfig,
    Signal,
    SupervisorReport,
    FeatureDefinition,
    FeatureDefinitionVersion,
    FeatureValue,
)
from packages.core.db.session import get_db_session
from packages.observability.logging import configure_logging
from packages.providers import PROVIDER_REGISTRY

configure_logging()
settings = get_settings()
app = FastAPI(title="CHAiNALYZE API", version="0.2.0")
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


class SecretPayload(BaseModel):
    secret: str = Field(min_length=1)


class ProviderUpsert(BaseModel):
    provider_type: str
    name: str
    enabled: bool = True
    settings_jsonb: dict = Field(default_factory=dict)
    secret: str | None = None


class LLMUpsert(BaseModel):
    enabled: bool
    settings_jsonb: dict = Field(default_factory=dict)
    secret: str | None = None


class AgentUpsert(BaseModel):
    enabled: bool = True
    mode: str = "deterministic"
    provider: str = "gemini"
    model: str = "gemini-1.5-flash"
    system_prompt: str = ""
    user_prompt_template: str = ""
    temperature: float = 0.2
    max_tokens: int = 400
    timeout_s: int = 20
    tools_allowed_jsonb: dict = Field(default_factory=dict)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/app-settings")
async def get_app_settings(session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    rows = (await session.execute(select(AppSetting))).scalars().all()
    return [{"key": r.key, "value_jsonb": r.value_jsonb, "updated_at": r.updated_at} for r in rows]


@app.post("/app-settings")
async def upsert_app_setting(payload: dict[str, Any], session: AsyncSession = Depends(get_db_session)) -> dict:
    key = payload.get("key")
    value = payload.get("value_jsonb", {})
    if not key:
        raise HTTPException(status_code=400, detail="key required")
    row = await session.scalar(select(AppSetting).where(AppSetting.key == key))
    now = datetime.now(UTC)
    if row:
        row.value_jsonb = value
        row.updated_at = now
    else:
        session.add(AppSetting(key=key, value_jsonb=value, updated_at=now))
    await session.commit()
    return {"ok": True}


@app.get("/providers")
async def list_providers(session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    rows = (await session.execute(select(ProviderConfig))).scalars().all()
    return [
        {
            "id": r.id,
            "provider_type": r.provider_type,
            "name": r.name,
            "enabled": r.enabled,
            "settings_jsonb": r.settings_jsonb,
            "secret_is_set": bool(r.secret_encrypted),
        }
        for r in rows
    ]


@app.post("/providers")
async def create_provider(payload: ProviderUpsert, session: AsyncSession = Depends(get_db_session)) -> dict:
    if payload.provider_type not in PROVIDER_REGISTRY:
        raise HTTPException(status_code=400, detail="unsupported provider_type")
    now = datetime.now(UTC)
    encrypted = encrypt_secret(settings.chainalyze_master_key, payload.secret) if payload.secret else None
    row = ProviderConfig(
        provider_type=payload.provider_type,
        name=payload.name,
        enabled=payload.enabled,
        settings_jsonb=payload.settings_jsonb,
        secret_encrypted=encrypted,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "secret_is_set": bool(row.secret_encrypted)}


@app.put("/providers/{provider_id}")
async def update_provider(provider_id: int, payload: ProviderUpsert, session: AsyncSession = Depends(get_db_session)) -> dict:
    row = await session.scalar(select(ProviderConfig).where(ProviderConfig.id == provider_id))
    if not row:
        raise HTTPException(status_code=404, detail="provider not found")
    row.provider_type = payload.provider_type
    row.name = payload.name
    row.enabled = payload.enabled
    row.settings_jsonb = payload.settings_jsonb
    if payload.secret:
        row.secret_encrypted = encrypt_secret(settings.chainalyze_master_key, payload.secret)
    row.updated_at = datetime.now(UTC)
    await session.commit()
    return {"ok": True, "secret_is_set": bool(row.secret_encrypted)}


@app.post("/providers/{provider_id}/test")
async def test_provider(provider_id: int, session: AsyncSession = Depends(get_db_session)) -> dict:
    row = await session.scalar(select(ProviderConfig).where(ProviderConfig.id == provider_id))
    if not row:
        raise HTTPException(status_code=404, detail="provider not found")
    return {"ok": True, "provider_type": row.provider_type, "capabilities": PROVIDER_REGISTRY[row.provider_type].capabilities}


@app.get("/llm")
async def get_llm(session: AsyncSession = Depends(get_db_session)) -> dict:
    row = await session.scalar(select(LLMConfig).order_by(LLMConfig.id.desc()))
    if not row:
        return {"enabled": False, "provider": "gemini", "settings_jsonb": {}, "secret_is_set": False}
    return {"enabled": row.enabled, "provider": row.provider, "settings_jsonb": row.settings_jsonb, "secret_is_set": bool(row.secret_encrypted)}


@app.post("/llm")
async def upsert_llm(payload: LLMUpsert, session: AsyncSession = Depends(get_db_session)) -> dict:
    row = await session.scalar(select(LLMConfig).order_by(LLMConfig.id.desc()))
    now = datetime.now(UTC)
    if row:
        row.enabled = payload.enabled
        row.settings_jsonb = payload.settings_jsonb
        if payload.secret:
            row.secret_encrypted = encrypt_secret(settings.chainalyze_master_key, payload.secret)
        row.updated_at = now
    else:
        row = LLMConfig(
            provider="gemini",
            enabled=payload.enabled,
            settings_jsonb=payload.settings_jsonb,
            secret_encrypted=encrypt_secret(settings.chainalyze_master_key, payload.secret) if payload.secret else None,
            updated_at=now,
        )
        session.add(row)
    await session.commit()
    return {"ok": True, "secret_is_set": bool(row.secret_encrypted)}


@app.post("/llm/test")
async def test_llm() -> dict:
    return {"ok": True, "provider": "gemini", "note": "stub call successful"}


@app.get("/agents")
async def list_agents(session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    rows = (await session.execute(select(AgentConfig))).scalars().all()
    return [{"agent_name": r.agent_name, "enabled": r.enabled, "mode": r.mode, "model": r.model} for r in rows]


@app.put("/agents/{name}")
async def upsert_agent(name: str, payload: AgentUpsert, session: AsyncSession = Depends(get_db_session)) -> dict:
    row = await session.scalar(select(AgentConfig).where(AgentConfig.agent_name == name))
    now = datetime.now(UTC)
    if not row:
        row = AgentConfig(agent_name=name, updated_at=now, **payload.model_dump())
        session.add(row)
    else:
        for k, v in payload.model_dump().items():
            setattr(row, k, v)
        row.updated_at = now
    await session.commit()
    return {"ok": True}


@app.get("/agents/{name}/versions")
async def get_agent_versions(name: str, session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    rows = (await session.execute(select(AgentPromptVersion).where(AgentPromptVersion.agent_name == name).order_by(AgentPromptVersion.version.desc()))).scalars().all()
    return [{"version": r.version, "created_at": r.created_at, "created_by": r.created_by} for r in rows]


@app.post("/agents/{name}/version")
async def save_agent_version(name: str, session: AsyncSession = Depends(get_db_session)) -> dict:
    cfg = await session.scalar(select(AgentConfig).where(AgentConfig.agent_name == name))
    if not cfg:
        raise HTTPException(status_code=404, detail="agent config missing")
    latest = await session.scalar(select(AgentPromptVersion).where(AgentPromptVersion.agent_name == name).order_by(AgentPromptVersion.version.desc()))
    version = 1 if not latest else latest.version + 1
    session.add(AgentPromptVersion(agent_name=name, version=version, system_prompt=cfg.system_prompt, user_prompt_template=cfg.user_prompt_template, model=cfg.model, temperature=cfg.temperature, max_tokens=cfg.max_tokens, created_at=datetime.now(UTC), created_by="ui"))
    await session.commit()
    return {"ok": True, "version": version}


@app.post("/agents/{name}/rollback")
async def rollback_agent(name: str, version: int = Query(...), session: AsyncSession = Depends(get_db_session)) -> dict:
    cfg = await session.scalar(select(AgentConfig).where(AgentConfig.agent_name == name))
    ver = await session.scalar(select(AgentPromptVersion).where(AgentPromptVersion.agent_name == name, AgentPromptVersion.version == version))
    if not cfg or not ver:
        raise HTTPException(status_code=404, detail="agent/version not found")
    cfg.system_prompt = ver.system_prompt
    cfg.user_prompt_template = ver.user_prompt_template
    cfg.model = ver.model
    cfg.temperature = ver.temperature
    cfg.max_tokens = ver.max_tokens
    cfg.updated_at = datetime.now(UTC)
    await session.commit()
    return {"ok": True}


@app.get("/instruments")
async def instruments(session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    rows = (await session.execute(select(Instrument))).scalars().all()
    return [{"id": i.id, "symbol": i.symbol, "display_name": i.display_name, "asset_class": i.asset_class, "provider_id": i.provider_id} for i in rows]


@app.post("/instruments")
async def create_instrument(payload: dict, session: AsyncSession = Depends(get_db_session)) -> dict:
    now = datetime.now(UTC)
    item = Instrument(
        symbol=payload["symbol"],
        display_name=payload.get("display_name", payload["symbol"]),
        asset_class=payload.get("asset_class", "crypto"),
        market_type=payload.get("market_type", "spot"),
        session_type=payload.get("session_type", "24_7"),
        timezone=payload.get("timezone", "UTC"),
        provider_id=payload.get("provider_id"),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return {"id": item.id}


@app.post("/instruments/{instrument_id}/assign-provider")
async def assign_provider(instrument_id: int, provider_id: int = Query(...), session: AsyncSession = Depends(get_db_session)) -> dict:
    inst = await session.scalar(select(Instrument).where(Instrument.id == instrument_id))
    if not inst:
        raise HTTPException(status_code=404, detail="instrument not found")
    inst.provider_id = provider_id
    await session.commit()
    return {"ok": True}


@app.get("/candles")
async def candles(symbol: str, tf: str = Query("5m"), session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    inst = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
    if not inst:
        return []
    rows = (await session.execute(select(Candle).where(Candle.instrument_id == inst.id, Candle.timeframe == tf).order_by(Candle.ts.desc()).limit(500))).scalars().all()
    return [{"ts": r.ts, "open": r.o, "high": r.h, "low": r.l, "close": r.c, "volume": r.volume} for r in reversed(rows)]


@app.get("/runs")
async def runs(session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    rows = (await session.execute(select(AnalysisRun).order_by(AnalysisRun.created_at.desc()).limit(100))).scalars().all()
    return [{"run_id": r.run_id, "status": r.status, "created_at": r.created_at} for r in rows]


@app.get("/runs/{run_id}")
async def run_details(run_id: str, session: AsyncSession = Depends(get_db_session)) -> dict:
    run = await session.scalar(select(AnalysisRun).where(AnalysisRun.run_id == run_id))
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    reps = (await session.execute(select(SupervisorReport).where(SupervisorReport.run_id == run_id))).scalars().all()
    return {"run_id": run.run_id, "status": run.status, "config_hash": run.config_hash, "metadata": run.metadata_jsonb, "supervisor_reports": [{"name": r.supervisor_name, "verdict": r.verdict, "payload": r.payload_jsonb} for r in reps]}


@app.post("/runs/trigger")
async def trigger_run() -> dict:
    return {"ok": True, "note": "manual trigger endpoint wired; connect Celery task in production"}


@app.get("/latest/findings")
async def latest_findings(symbol: str, session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    inst = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
    if not inst:
        return []
    rows = (await session.execute(select(Finding).where(Finding.instrument_id == inst.id).order_by(Finding.ts.desc()).limit(20))).scalars().all()
    return [{"agent_name": f.agent_name, "kind": f.kind, "severity": f.severity, "confidence": f.confidence, "tags": f.tags, "payload": f.payload_jsonb} for f in rows]


@app.get("/latest/signals")
async def latest_signals(symbol: str, session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    inst = await session.scalar(select(Instrument).where(Instrument.symbol == symbol))
    if not inst:
        return []
    rows = (await session.execute(select(Signal).where(Signal.instrument_id == inst.id).order_by(Signal.ts.desc()).limit(20))).scalars().all()
    return [{"direction": s.direction, "confidence": s.confidence, "horizon": s.horizon, "metadata": s.metadata_jsonb} for s in rows]


@app.get("/alerts/config")
async def get_alerts(session: AsyncSession = Depends(get_db_session)) -> dict:
    from packages.core.db.models import AlertConfig

    cfg = await session.scalar(select(AlertConfig).order_by(AlertConfig.id.desc()))
    if not cfg:
        return {"telegram_enabled": False, "rules_jsonb": {}, "secret_is_set": False}
    return {"telegram_enabled": cfg.telegram_enabled, "rules_jsonb": cfg.rules_jsonb, "secret_is_set": bool(cfg.telegram_secret_encrypted)}


@app.post("/alerts/config")
async def upsert_alerts(payload: dict, session: AsyncSession = Depends(get_db_session)) -> dict:
    from packages.core.db.models import AlertConfig

    cfg = await session.scalar(select(AlertConfig).order_by(AlertConfig.id.desc()))
    now = datetime.now(UTC)
    secret = payload.get("telegram_secret")
    encrypted = encrypt_secret(settings.chainalyze_master_key, secret) if secret else None
    if not cfg:
        cfg = AlertConfig(
            telegram_enabled=bool(payload.get("telegram_enabled", False)),
            telegram_secret_encrypted=encrypted,
            rules_jsonb=payload.get("rules_jsonb", {}),
            updated_at=now,
        )
        session.add(cfg)
    else:
        cfg.telegram_enabled = bool(payload.get("telegram_enabled", cfg.telegram_enabled))
        cfg.rules_jsonb = payload.get("rules_jsonb", cfg.rules_jsonb)
        if encrypted:
            cfg.telegram_secret_encrypted = encrypted
        cfg.updated_at = now
    await session.commit()
    return {"ok": True, "secret_is_set": bool(cfg.telegram_secret_encrypted)}


@app.post("/alerts/test")
async def test_alert() -> dict:
    return {"ok": True, "note": "alert test stub"}


@app.get("/features/registry")
async def features_registry() -> dict:
    from packages.features.registry import INDICATOR_REGISTRY

    return {k: {"params": v["params"]} for k, v in INDICATOR_REGISTRY.items()}


@app.get("/features/definitions")
async def list_feature_definitions(session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    rows = (await session.execute(select(FeatureDefinition).order_by(FeatureDefinition.updated_at.desc()))).scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "enabled": r.enabled,
            "instrument_id": r.instrument_id,
            "timeframe": r.timeframe,
            "feature_key": r.feature_key,
            "type": r.type,
            "indicator_type": r.indicator_type,
            "params_jsonb": r.params_jsonb,
            "formula_expr": r.formula_expr,
            "version": r.version,
            "config_hash": r.config_hash,
        }
        for r in rows
    ]


@app.post("/features/definitions")
async def create_feature_definition(payload: dict, session: AsyncSession = Depends(get_db_session)) -> dict:
    from packages.features.store import upsert_feature_definition

    row = await upsert_feature_definition(session, payload)
    return {"id": row.id, "version": row.version, "config_hash": row.config_hash}


@app.put("/features/definitions/{feature_id}")
async def update_feature_definition(feature_id: int, payload: dict, session: AsyncSession = Depends(get_db_session)) -> dict:
    from packages.features.store import upsert_feature_definition

    obj = await session.scalar(select(FeatureDefinition).where(FeatureDefinition.id == feature_id))
    if not obj:
        raise HTTPException(status_code=404, detail="feature definition not found")
    payload["name"] = payload.get("name", obj.name)
    row = await upsert_feature_definition(session, payload)
    return {"id": row.id, "version": row.version, "config_hash": row.config_hash}


@app.get("/features/definitions/{feature_id}/versions")
async def feature_versions(feature_id: int, session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    rows = (await session.execute(select(FeatureDefinitionVersion).where(FeatureDefinitionVersion.feature_definition_id == feature_id).order_by(FeatureDefinitionVersion.version.desc()))).scalars().all()
    return [{"version": r.version, "created_at": r.created_at, "created_by": r.created_by} for r in rows]


@app.post("/features/definitions/{feature_id}/rollback")
async def rollback_feature(feature_id: int, version: int = Query(...), session: AsyncSession = Depends(get_db_session)) -> dict:
    from packages.features.store import upsert_feature_definition

    snap = await session.scalar(select(FeatureDefinitionVersion).where(FeatureDefinitionVersion.feature_definition_id == feature_id, FeatureDefinitionVersion.version == version))
    if not snap:
        raise HTTPException(status_code=404, detail="version not found")
    row = await upsert_feature_definition(session, snap.snapshot_jsonb)
    return {"ok": True, "id": row.id, "version": row.version}


@app.post("/features/definitions/{feature_id}/backfill")
async def backfill_feature(feature_id: int, payload: dict, session: AsyncSession = Depends(get_db_session)) -> dict:
    from packages.features.engine import compute_feature_definition

    feature = await session.scalar(select(FeatureDefinition).where(FeatureDefinition.id == feature_id))
    if not feature:
        raise HTTPException(status_code=404, detail="feature not found")
    instrument_id = payload.get("instrument_id") or feature.instrument_id
    if not instrument_id:
        raise HTTPException(status_code=400, detail="instrument_id required")
    days = int(payload.get("days", 30))
    out = await compute_feature_definition(session, feature, instrument_id=instrument_id, days=days)
    return out


@app.get("/features/values")
async def get_feature_values(
    instrument: str,
    tf: str,
    feature_key: str,
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    inst = await session.scalar(select(Instrument).where(Instrument.symbol == instrument))
    if not inst:
        return []
    fdef = await session.scalar(select(FeatureDefinition).where(FeatureDefinition.feature_key == feature_key, FeatureDefinition.timeframe == tf))
    if not fdef:
        return []
    rows = (await session.execute(select(FeatureValue).where(FeatureValue.feature_definition_id == fdef.id, FeatureValue.instrument_id == inst.id, FeatureValue.timeframe == tf).order_by(FeatureValue.ts.desc()).limit(1000))).scalars().all()
    return [{"ts": r.ts, "value_num": r.value_num, "value_bool": r.value_bool, "value_jsonb": r.value_jsonb} for r in reversed(rows)]


@app.post("/features/validate-formula")
async def validate_formula(payload: dict) -> dict:
    from packages.features.formulas import validate_formula

    expr = payload.get("expression", "")
    try:
        validate_formula(expr)
        return {"valid": True, "error": None}
    except Exception as e:
        return {"valid": False, "error": str(e)}
