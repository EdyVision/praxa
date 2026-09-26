"""Trajectory diagnostics types (research instrumentation)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OpenerSnapshot(BaseModel):
    """First-token / opener distribution for one condition."""

    model_config = ConfigDict(extra="forbid")

    condition: str
    next_token: str
    opener_class: str
    p_refusal_first: float | None = None
    p_essay_opener: float | None = None
    topk: list[dict[str, float | int | str]] = Field(default_factory=list)


class TerminationSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    n_generated: int
    hit_max_new_tokens: bool
    stopped_on_valid_terminal: bool
    clean_stop: bool


class TrajectoryDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    example_id: str
    opener: OpenerSnapshot | None = None
    termination: TerminationSnapshot | None = None
    paired_deltas: dict[str, float] = Field(default_factory=dict)
