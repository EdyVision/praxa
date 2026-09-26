"""Execution-stage artifacts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from praxa.domain.decision import PolicyDecision
from praxa.domain.match import PolicyMatch


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    content: str


class ExecutionResult(BaseModel):
    """Output of running an operationalizer on one example."""

    model_config = ConfigDict(extra="forbid")

    example_id: str
    method_id: str
    match: PolicyMatch
    decision: PolicyDecision
    messages: list[ChatMessage] = Field(default_factory=list)
    output_text: str = ""
    structured: dict[str, Any] = Field(default_factory=dict)
    n_generated: int | None = None
    hit_max_new_tokens: bool | None = None
    stopped_on_valid_terminal: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
