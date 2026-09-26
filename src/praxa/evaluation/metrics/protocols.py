"""Deterministic stage evaluators."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from praxa.domain.execution import ExecutionResult
from praxa.evaluation.metrics.hygiene import hygiene_report


class DispositionCorrectnessEvaluator:
    """Compare predicted disposition to TaskContext expected_disposition when present."""

    evaluator_id = "disposition_correctness_v1"

    def score(self, result: ExecutionResult) -> dict[str, Any]:
        expected = (result.metadata or {}).get("expected_disposition")
        predicted = result.decision.resolved_disposition_label()
        if expected is None:
            return {"predicted": predicted, "expected": None, "correct": None}
        return {
            "predicted": predicted,
            "expected": expected,
            "correct": predicted == expected,
        }


class HygieneEvaluator:
    """Generation hygiene: clean stop plus optional contamination markers."""

    evaluator_id = "hygiene_v1"

    def __init__(self, *, contamination_markers: Sequence[str] | None = None) -> None:
        self.contamination_markers = list(contamination_markers or ())

    def score(self, result: ExecutionResult) -> dict[str, Any]:
        return hygiene_report(
            n_generated=result.n_generated,
            hit_max_new_tokens=result.hit_max_new_tokens,
            stopped_on_valid_terminal=result.stopped_on_valid_terminal,
            output_text=result.output_text,
            contamination_markers=self.contamination_markers,
        )
