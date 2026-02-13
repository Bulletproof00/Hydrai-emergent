from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class SupervisorReportOut:
    supervisor_name: str
    ts: datetime
    verdict: str
    payload: dict


class BaseSupervisor(Protocol):
    name: str

    def run(self, findings: list[dict], signal: dict | None = None) -> SupervisorReportOut:
        ...
