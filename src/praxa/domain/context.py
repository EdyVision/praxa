"""Task and context models shared across memory, safety, and behavioral studies."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskKind(StrEnum):
    BEHAVIORAL = "behavioral"
    SAFETY = "safety"
    MEMORY = "memory"
    EXTRACTION = "extraction"
    CUSTOM = "custom"


class ConversationTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    content: str


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = ""
    text: str = ""
    source: str = ""
    span: tuple[int, int] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskContext(BaseModel):
    """Normalized model input for a single operationalization example."""

    model_config = ConfigDict(extra="forbid")

    example_id: str
    query: str
    task_kind: TaskKind = TaskKind.BEHAVIORAL
    tags: list[str] = Field(default_factory=list)
    stratum: str = ""
    conversation: list[ConversationTurn] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    expected_disposition: str | None = None
    expected_required: list[str] = Field(default_factory=list)
    expected_prohibited: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
