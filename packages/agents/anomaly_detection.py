import numpy as np

from packages.agents.framework import AgentContext, Finding


class AnomalyDetectionAgent:
    name = "AnomalyDetectionAgent"
    required_inputs = ["candles"]

    def run(self, context: AgentContext) -> list[Finding]:
        if len(context.candles) < 30:
            return []

        close = context.candles["close"].pct_change().dropna()
        vol = context.candles["volume"]
        z = (close.iloc[-1] - close.mean()) / (close.std() or 1)
        vol_spike = float(vol.iloc[-1] / (vol.tail(20).mean() or 1))
        is_anomaly = abs(z) > 2.5 or vol_spike > 2.0

        return [
            Finding(
                agent_name=self.name,
                symbol=context.symbol,
                ts=context.candles.iloc[-1]["ts"],
                severity="high" if is_anomaly else "low",
                confidence=0.75 if is_anomaly else 0.4,
                tags=["anomaly"],
                payload={"return_zscore": float(z), "volume_spike": vol_spike, "anomaly": bool(is_anomaly)},
            )
        ]
