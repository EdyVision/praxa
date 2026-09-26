"""Helpers to turn EvalResults into flat tracker metrics."""

from __future__ import annotations

from typing import Any

from praxa.evaluation.results import EvalResults


def flatten_compare_metrics(summary: dict[str, Any]) -> dict[str, float]:
    metrics: dict[str, float] = {
        "n_records": float(summary.get("n_records") or 0),
    }
    by_method = summary.get("by_method") or {}
    for method_id, block in by_method.items():
        safe = str(method_id).replace(".", "_").replace("/", "_")
        metrics[f"method.{safe}.n"] = float(block.get("n") or 0)
        counts = block.get("disposition_counts") or {}
        for disposition, count in counts.items():
            disp = str(disposition).replace(".", "_")
            metrics[f"method.{safe}.disposition.{disp}"] = float(count)
    return metrics


def disposition_correctness_rate(results: EvalResults) -> float | None:
    """Mean of disposition_correctness_v1.correct when that evaluator ran."""
    values: list[float] = []
    for record in results.records:
        scores = record.get("scores") or {}
        block = scores.get("disposition_correctness_v1") or {}
        correct = block.get("correct")
        if correct is None:
            continue
        values.append(1.0 if correct else 0.0)
    if not values:
        return None
    return sum(values) / len(values)


def metrics_from_results(results: EvalResults) -> dict[str, float]:
    metrics = flatten_compare_metrics(results.compare())
    rate = disposition_correctness_rate(results)
    if rate is not None:
        metrics["disposition_correctness_rate"] = rate
    return metrics
