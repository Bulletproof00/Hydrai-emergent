import json

from packages.llm.base import LLMResult


class GeminiClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def generate_json(self, system_prompt: str, user_prompt: str, model: str = "gemini-1.5-flash") -> LLMResult:
        # MVP stub for environments without SDK/network.
        payload = {
            "summary": "LLM augmentation stubbed",
            "key_points": ["Gemini integration ready"],
            "risk_notes": ["Live SDK call disabled in offline/dev mode"],
            "confidence_adjustment": 0.0,
            "next_checks": ["Enable SDK and key in production"],
        }
        return LLMResult(text=json.dumps(payload), raw={"model": model, "stub": True})
