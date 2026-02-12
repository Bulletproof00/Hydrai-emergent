from datetime import datetime
from pydantic import BaseModel, Field


class FindingOut(BaseModel):
    agent_name: str
    symbol: str
    ts: datetime
    severity: str
    tags: list[str] = Field(default_factory=list)
    payload: dict


class SignalOut(BaseModel):
    symbol: str
    ts: datetime
    direction: str
    confidence: float
    invalidation: float | None = None
    metadata: dict = Field(default_factory=dict)
