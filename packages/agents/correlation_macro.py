from packages.agents.framework import AgentContext, Finding


class CorrelationMacroAgent:
    name = "CorrelationMacroAgent"
    required_inputs = []

    def run(self, context: AgentContext) -> list[Finding]:
        return [
            Finding(
                agent_name=self.name,
                symbol=context.symbol,
                ts=context.candles.iloc[-1]["ts"],
                severity="low",
                confidence=0.2,
                tags=["stub", "macro"],
                payload={"status": "stub", "note": "Macro correlation sources not wired in MVP."},
            )
        ]
