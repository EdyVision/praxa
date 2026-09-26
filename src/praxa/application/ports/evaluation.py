"""Evaluation port."""

from __future__ import annotations

from typing import Any, Protocol

from praxa.domain.execution import ExecutionResult


class StageEvaluator(Protocol):
    """Score one operationalization stage. Deterministic preferred."""

    evaluator_id: str

    def score(self, result: ExecutionResult) -> dict[str, Any]: ...
