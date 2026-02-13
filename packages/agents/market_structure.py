import numpy as np

from packages.agents.framework import AgentContext, Finding


class MarketStructureAgent:
    name = "MarketStructureAgent"
    required_inputs = ["candles"]

    def run(self, context: AgentContext) -> list[Finding]:
        if context.candles.empty or len(context.candles) < 20:
            return []

        highs = context.candles["high"].values
        lows = context.candles["low"].values
        close = context.candles["close"].values

        swing_high = float(np.max(highs[-20:]))
        swing_low = float(np.min(lows[-20:]))
        state = "range"
        if close[-1] > highs[-2]:
            state = "bos_up"
        elif close[-1] < lows[-2]:
            state = "bos_down"

        return [
            Finding(
                agent_name=self.name,
                symbol=context.symbol,
                ts=context.candles.iloc[-1]["ts"],
                severity="medium",
                confidence=0.62,
                tags=["structure", state],
                payload={"swing_high": swing_high, "swing_low": swing_low, "state": state},
            )
        ]
