"""Typed memory records for policy-guided extraction studies."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MemoryKind(StrEnum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    PREFERENCE = "preference"
    SAFETY = "safety"
    POLICY = "policy"


class MemoryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    memory_id: str
    kind: MemoryKind
    text: str
    confidence: float = 1.0
    evidence_ids: list[str] = Field(default_factory=list)
    source_span: tuple[int, int] | None = None
    triggering_rule_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
