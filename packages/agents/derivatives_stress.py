from packages.agents.framework import AgentContext, Finding


class DerivativesStressAgent:
    name = "DerivativesStressAgent"
    required_inputs = ["funding_rate", "open_interest_change"]

    def run(self, context: AgentContext) -> list[Finding]:
        if context.funding_rate is None and context.open_interest_change is None:
            return []

        bias = "neutral"
        if (context.funding_rate or 0) > 0.0008 and (context.open_interest_change or 0) > 0.02:
            bias = "crowded_longs"
        if (context.funding_rate or 0) < -0.0008 and (context.open_interest_change or 0) > 0.02:
            bias = "crowded_shorts"

        return [
            Finding(
                agent_name=self.name,
                symbol=context.symbol,
                ts=context.candles.iloc[-1]["ts"],
                severity="medium",
                confidence=0.58,
                tags=["derivatives", bias],
                payload={
                    "funding_rate": context.funding_rate,
                    "open_interest_change": context.open_interest_change,
                    "bias": bias,
                },
            )
        ]
