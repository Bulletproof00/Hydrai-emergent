from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.config_hash import compute_config_hash
from packages.core.db.models import (
    FeatureComputeRun,
    FeatureDefinition,
    FeatureDefinitionVersion,
    FeatureValue,
)


async def upsert_feature_definition(session: AsyncSession, payload: dict) -> FeatureDefinition:
    now = datetime.now(UTC)
    existing = await session.scalar(select(FeatureDefinition).where(FeatureDefinition.name == payload["name"]))
    cfg_hash = compute_config_hash(payload)
    if existing:
        existing.enabled = payload.get("enabled", True)
        existing.instrument_id = payload.get("instrument_id")
        existing.timeframe = payload["timeframe"]
        existing.feature_key = payload["feature_key"]
        existing.type = payload["type"]
        existing.indicator_type = payload.get("indicator_type")
        existing.params_jsonb = payload.get("params_jsonb", {})
        existing.formula_expr = payload.get("formula_expr")
        existing.output_schema_jsonb = payload.get("output_schema_jsonb", {})
        existing.version += 1
        existing.config_hash = cfg_hash
        existing.updated_at = now
        row = existing
    else:
        row = FeatureDefinition(
            name=payload["name"],
            enabled=payload.get("enabled", True),
            instrument_id=payload.get("instrument_id"),
            timeframe=payload["timeframe"],
            feature_key=payload["feature_key"],
            type=payload["type"],
            indicator_type=payload.get("indicator_type"),
            params_jsonb=payload.get("params_jsonb", {}),
            formula_expr=payload.get("formula_expr"),
            output_schema_jsonb=payload.get("output_schema_jsonb", {}),
            version=1,
            config_hash=cfg_hash,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        await session.flush()

    session.add(
        FeatureDefinitionVersion(
            feature_definition_id=row.id,
            version=row.version,
            snapshot_jsonb=payload,
            created_at=now,
            created_by="ui",
        )
    )
    await session.commit()
    await session.refresh(row)
    return row


async def insert_feature_value(
    session: AsyncSession,
    feature_definition_id: int,
    instrument_id: int,
    timeframe: str,
    ts,
    value_num=None,
    value_bool=None,
    value_jsonb=None,
) -> int:
    stmt = (
        insert(FeatureValue)
        .values(
            feature_definition_id=feature_definition_id,
            instrument_id=instrument_id,
            timeframe=timeframe,
            ts=ts,
            value_num=value_num,
            value_bool=value_bool,
            value_jsonb=value_jsonb,
            created_at=datetime.now(UTC),
        )
        .on_conflict_do_update(
            index_elements=["feature_definition_id", "instrument_id", "timeframe", "ts"],
            set_={"value_num": value_num, "value_bool": value_bool, "value_jsonb": value_jsonb},
        )
    )
    res = await session.execute(stmt)
    return res.rowcount or 0


async def create_compute_run(session: AsyncSession, feature_definition_id: int, instrument_id: int, timeframe: str, window_start, window_end, run_id: str | None = None) -> FeatureComputeRun:
    obj = FeatureComputeRun(
        run_id=run_id,
        feature_definition_id=feature_definition_id,
        instrument_id=instrument_id,
        timeframe=timeframe,
        window_start=window_start,
        window_end=window_end,
        status="running",
        error=None,
        created_at=datetime.now(UTC),
    )
    session.add(obj)
    await session.flush()
    return obj
