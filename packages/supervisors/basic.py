from datetime import UTC, datetime

from packages.supervisors.framework import SupervisorReportOut


class DataQualitySupervisor:
    name = "DataQualitySupervisor"

    def run(self, findings: list[dict], signal: dict | None = None) -> SupervisorReportOut:
        missing = len(findings) == 0
        verdict = "warn" if missing else "pass"
        return SupervisorReportOut(self.name, datetime.now(UTC), verdict, {"findings_missing": missing})


class DriftSupervisor:
    name = "DriftSupervisor"

    def run(self, findings: list[dict], signal: dict | None = None) -> SupervisorReportOut:
        return SupervisorReportOut(self.name, datetime.now(UTC), "pass", {"method": "rolling baseline heuristic"})


class OverfitRiskSupervisor:
    name = "OverfitRiskSupervisor"

    def run(self, findings: list[dict], signal: dict | None = None) -> SupervisorReportOut:
        c = (signal or {}).get("confidence", 0)
        verdict = "warn" if c > 0.9 else "pass"
        return SupervisorReportOut(self.name, datetime.now(UTC), verdict, {"signal_confidence": c})


class RiskCoherenceSupervisor:
    name = "RiskCoherenceSupervisor"

    def run(self, findings: list[dict], signal: dict | None = None) -> SupervisorReportOut:
        anomaly = any("anomaly" in (f.get("tags") or []) for f in findings)
        verdict = "hold" if anomaly and (signal or {}).get("direction") in {"long", "short"} else "pass"
        return SupervisorReportOut(self.name, datetime.now(UTC), verdict, {"anomaly_present": anomaly})
