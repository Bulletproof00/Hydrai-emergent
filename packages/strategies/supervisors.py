from datetime import datetime, timezone


def drift_supervisor(run_id: str, findings: list[dict]) -> dict:
    return {
        "run_id": run_id,
        "supervisor_name": "DriftSupervisor",
        "ts": datetime.now(timezone.utc),
        "payload_json": {"status": "ok", "note": "Baseline drift checks are MVP heuristics."},
        "verdict": "pass",
    }


def overfit_risk_supervisor(run_id: str, signal: dict) -> dict:
    verdict = "pass" if signal.get("confidence", 0) < 0.9 else "warn"
    return {
        "run_id": run_id,
        "supervisor_name": "OverfitRiskSupervisor",
        "ts": datetime.now(timezone.utc),
        "payload_json": {"signal_confidence": signal.get("confidence", 0)},
        "verdict": verdict,
    }


def risk_coherence_supervisor(run_id: str, findings: list[dict], signal: dict) -> dict:
    high_uncertainty = any(f.get("severity") == "high" for f in findings if "anomaly" in f.get("tags", []))
    verdict = "hold" if high_uncertainty and signal.get("direction") != "hold" else "pass"
    return {
        "run_id": run_id,
        "supervisor_name": "RiskCoherenceSupervisor",
        "ts": datetime.now(timezone.utc),
        "payload_json": {"high_uncertainty": high_uncertainty},
        "verdict": verdict,
    }
