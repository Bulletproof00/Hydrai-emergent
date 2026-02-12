from collections import defaultdict
from datetime import datetime, timezone

from packages.agents.framework import Finding


def synthesize_signal(symbol: str, findings: list[Finding], weights: dict[str, float] | None = None) -> dict:
    weights = weights or {}
    score = defaultdict(float)
    for finding in findings:
        w = weights.get(finding.agent_name, 1.0)
        state = str(finding.payload.get("state", ""))
        regime = str(finding.payload.get("regime", ""))
        bias = str(finding.payload.get("bias", ""))

        if "up" in state or regime == "trend":
            score["long"] += w * finding.confidence
        if "down" in state:
            score["short"] += w * finding.confidence
        if bias == "crowded_longs":
            score["short"] += 0.2 * w
        if bias == "crowded_shorts":
            score["long"] += 0.2 * w

    direction = "hold"
    confidence = 0.0
    if score["long"] > score["short"] and score["long"] > 0.6:
        direction = "long"
        confidence = min(0.95, score["long"] / max(1, len(findings)))
    elif score["short"] > score["long"] and score["short"] > 0.6:
        direction = "short"
        confidence = min(0.95, score["short"] / max(1, len(findings)))

    return {
        "symbol": symbol,
        "ts": datetime.now(timezone.utc),
        "direction": direction,
        "confidence": round(confidence, 4),
        "invalidation": None,
        "metadata": {"agent_count": len(findings), "score": dict(score)},
    }
