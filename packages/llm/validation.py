from pydantic import BaseModel, Field


class LLMOutputSchema(BaseModel):
    summary: str
    key_points: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    confidence_adjustment: float = Field(ge=-0.2, le=0.2)
    next_checks: list[str] = Field(default_factory=list)
