"""Policy recognition result."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PolicyMatch(BaseModel):
    """Which rules apply to a task context."""

    model_config = ConfigDict(extra="forbid")

    applicable: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    scores: dict[str, float] = Field(default_factory=dict)
    rationale: str = ""
