from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResult:
    text: str
    raw: dict


class LLMClient(Protocol):
    def generate_json(self, system_prompt: str, user_prompt: str, model: str) -> LLMResult:
        ...
