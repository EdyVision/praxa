"""Core dataset record schemas (no runners)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from praxa.domain.context import TaskContext


class DatasetRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    example_id: str
    split: str
    context: TaskContext


class SplitManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    splits: dict[str, list[str]] = Field(default_factory=dict)
