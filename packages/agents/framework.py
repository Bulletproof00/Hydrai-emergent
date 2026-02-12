from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import pandas as pd
from pydantic import BaseModel, Field


class Finding(BaseModel):
    agent_name: str
    symbol: str
    ts: datetime
    severity: str = "info"
    confidence: float = 0.5
    tags: list[str] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)


@dataclass
class AgentContext:
    run_id: str
    symbol: str
    timeframe: str
    candles: pd.DataFrame
    funding_rate: float | None = None
    open_interest_change: float | None = None
    config: dict | None = None


class BaseAgent(Protocol):
    name: str
    required_inputs: list[str]

    def run(self, context: AgentContext) -> list[Finding]: ...
