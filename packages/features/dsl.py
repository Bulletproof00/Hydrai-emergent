from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class IndicatorParams(BaseModel):
    source: Literal["open", "high", "low", "close", "hl2", "ohlc4"] = "close"
    length: int | None = Field(default=None, ge=1, le=1000)
    fast: int | None = Field(default=None, ge=1, le=1000)
    slow: int | None = Field(default=None, ge=1, le=1000)
    signal: int | None = Field(default=None, ge=1, le=1000)
    stddev: float | None = Field(default=None, gt=0, le=10)


class IndicatorFeatureDef(BaseModel):
    name: str
    enabled: bool = True
    instrument_id: int | None = None
    instrument_tags: list[str] = Field(default_factory=list)
    timeframe: str
    feature_key: str
    type: Literal["indicator"] = "indicator"
    indicator_type: str
    params: IndicatorParams = Field(default_factory=IndicatorParams)


class FormulaFeatureDef(BaseModel):
    name: str
    enabled: bool = True
    instrument_id: int | None = None
    instrument_tags: list[str] = Field(default_factory=list)
    timeframe: str
    feature_key: str
    type: Literal["formula"] = "formula"
    expr: str


class FeatureDefinitionOut(BaseModel):
    id: int
    name: str
    enabled: bool
    instrument_id: int | None
    timeframe: str
    feature_key: str
    type: str
    indicator_type: str | None
    params_jsonb: dict
    formula_expr: str | None
    output_schema_jsonb: dict
    version: int
    config_hash: str
    created_at: datetime
    updated_at: datetime


class BackfillRequest(BaseModel):
    instrument_id: int | None = None
    days: int = Field(default=30, ge=1, le=2000)


class FormulaValidationRequest(BaseModel):
    expression: str


class FormulaValidationResponse(BaseModel):
    valid: bool
    error: str | None = None


class FeatureValueOut(BaseModel):
    feature_definition_id: int
    instrument_id: int
    timeframe: str
    ts: datetime
    value_num: float | None = None
    value_bool: bool | None = None
    value_jsonb: dict | None = None
