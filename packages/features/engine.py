from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.db.models import Candle, FeatureDefinition, FeatureValue, Instrument
from packages.features.formulas import evaluate_formula, validate_formula
from packages.features.registry import INDICATOR_REGISTRY
from packages.features.store import create_compute_run, insert_feature_value


async def _load_candles(session: AsyncSession, instrument_id: int, timeframe: str, since: datetime) -> pd.DataFrame:
    rows = (
        await session.execute(
            select(Candle)
            .where(Candle.instrument_id == instrument_id, Candle.timeframe == timeframe, Candle.ts >= since)
            .order_by(Candle.ts.asc())
        )
    ).scalars().all()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([{"ts": r.ts, "open": r.o, "high": r.h, "low": r.l, "close": r.c, "volume": r.volume} for r in rows])


async def compute_feature_definition(session: AsyncSession, feature_def: FeatureDefinition, instrument_id: int, days: int = 30, run_id: str | None = None) -> dict:
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    cr = await create_compute_run(session, feature_def.id, instrument_id, feature_def.timeframe, start, end, run_id=run_id)

    try:
        df = await _load_candles(session, instrument_id, feature_def.timeframe, start)
        if df.empty:
            cr.status = "failed"
            cr.error = "No candles"
            await session.commit()
            return {"inserted": 0, "status": "failed"}

        inserted = 0
        if feature_def.type == "indicator":
            spec = INDICATOR_REGISTRY.get(feature_def.indicator_type or "")
            if not spec:
                raise ValueError(f"Unknown indicator type: {feature_def.indicator_type}")
            out = spec["fn"](df, **(feature_def.params_jsonb or {}))
            for col, series in out.items():
                for ts, v in zip(df["ts"], series):
                    if pd.isna(v):
                        continue
                    if len(out) == 1:
                        inserted += await insert_feature_value(session, feature_def.id, instrument_id, feature_def.timeframe, ts, value_num=float(v))
                    else:
                        inserted += await insert_feature_value(session, feature_def.id, instrument_id, feature_def.timeframe, ts, value_jsonb={col: float(v)})

        elif feature_def.type == "formula":
            validate_formula(feature_def.formula_expr or "")
            refs = {
                "close": df["close"],
                "open": df["open"],
                "high": df["high"],
                "low": df["low"],
                "volume": df["volume"],
            }
            base_defs = (
                await session.execute(
                    select(FeatureDefinition).where(
                        FeatureDefinition.instrument_id == instrument_id,
                        FeatureDefinition.timeframe == feature_def.timeframe,
                        FeatureDefinition.enabled == True,
                    )
                )
            ).scalars().all()
            for bd in base_defs:
                vals = (
                    await session.execute(
                        select(FeatureValue)
                        .where(
                            FeatureValue.feature_definition_id == bd.id,
                            FeatureValue.instrument_id == instrument_id,
                            FeatureValue.timeframe == feature_def.timeframe,
                            FeatureValue.ts >= start,
                        )
                        .order_by(FeatureValue.ts.asc())
                    )
                ).scalars().all()
                if vals:
                    refs[bd.feature_key] = pd.Series([v.value_num if v.value_num is not None else None for v in vals], index=[v.ts for v in vals]).reindex(df["ts"]).ffill()

            res = evaluate_formula(feature_def.formula_expr or "", refs).reindex(df["ts"])
            for ts, v in zip(df["ts"], res):
                if pd.isna(v):
                    continue
                if isinstance(v, (bool, pd.BooleanDtype)):
                    inserted += await insert_feature_value(session, feature_def.id, instrument_id, feature_def.timeframe, ts, value_bool=bool(v))
                else:
                    try:
                        inserted += await insert_feature_value(session, feature_def.id, instrument_id, feature_def.timeframe, ts, value_num=float(v))
                    except Exception:
                        inserted += await insert_feature_value(session, feature_def.id, instrument_id, feature_def.timeframe, ts, value_bool=bool(v))

        cr.status = "completed"
        await session.commit()
        return {"inserted": inserted, "status": "completed"}
    except Exception as e:
        cr.status = "failed"
        cr.error = str(e)
        await session.commit()
        return {"inserted": 0, "status": "failed", "error": str(e)}
