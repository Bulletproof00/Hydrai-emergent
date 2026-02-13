import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core.db.models import FeatureDefinition, FeatureValue


async def get_feature_series(
    session: AsyncSession,
    feature_key: str,
    instrument_id: int,
    timeframe: str,
) -> pd.Series:
    fdef = await session.scalar(
        select(FeatureDefinition).where(
            FeatureDefinition.feature_key == feature_key,
            FeatureDefinition.timeframe == timeframe,
            FeatureDefinition.enabled == True,
        )
    )
    if not fdef:
        return pd.Series(dtype=float)

    rows = (
        await session.execute(
            select(FeatureValue)
            .where(
                FeatureValue.feature_definition_id == fdef.id,
                FeatureValue.instrument_id == instrument_id,
                FeatureValue.timeframe == timeframe,
            )
            .order_by(FeatureValue.ts.asc())
        )
    ).scalars().all()

    vals = [r.value_num if r.value_num is not None else (1.0 if r.value_bool else 0.0 if r.value_bool is not None else None) for r in rows]
    idx = [r.ts for r in rows]
    return pd.Series(vals, index=idx)
