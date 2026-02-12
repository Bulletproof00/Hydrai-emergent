import numpy as np
import pandas as pd
from ta.trend import ADXIndicator
from ta.volatility import AverageTrueRange

from packages.agents.framework import AgentContext, Finding


class RegimeDetectionAgent:
    name = "RegimeDetectionAgent"
    required_inputs = ["candles"]

    def run(self, context: AgentContext) -> list[Finding]:
        if context.candles.empty or len(context.candles) < 30:
            return []

        df = context.candles.copy()
        adx = ADXIndicator(df["high"], df["low"], df["close"], window=14).adx().iloc[-1]
        atr = AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range().iloc[-1]
        ma_fast = df["close"].rolling(10).mean().iloc[-1]
        ma_slow = df["close"].rolling(25).mean().iloc[-1]
        slope = (ma_fast - ma_slow) / ma_slow if ma_slow else 0.0

        if adx > 25 and abs(slope) > 0.002:
            regime = "trend"
            confidence = 0.7
        elif atr < df["close"].tail(20).std() * 0.8:
            regime = "compression"
            confidence = 0.6
        else:
            regime = "range"
            confidence = 0.55

        return [
            Finding(
                agent_name=self.name,
                symbol=context.symbol,
                ts=df.iloc[-1]["ts"],
                severity="low",
                confidence=float(confidence),
                tags=["regime", regime],
                payload={"regime": regime, "adx": float(adx), "atr": float(atr), "slope": float(slope)},
            )
        ]
