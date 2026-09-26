"""Evaluation result containers and comparison helpers."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from praxa.application.services.provenance import RunManifest
from praxa.domain.execution import ExecutionResult


@dataclass
class EvalResults:
    manifest: RunManifest
    records: list[dict[str, Any]] = field(default_factory=list)
    results: list[ExecutionResult] = field(default_factory=list)

    def compare(self) -> dict[str, Any]:
        by_method: dict[str, list[ExecutionResult]] = defaultdict(list)
        for result in self.results:
            by_method[result.method_id].append(result)

        summary: dict[str, Any] = {}
        for method_id, items in sorted(by_method.items()):
            dispositions: dict[str, int] = defaultdict(int)
            for item in items:
                dispositions[item.decision.resolved_disposition_label()] += 1
            summary[method_id] = {
                "n": len(items),
                "disposition_counts": dict(dispositions),
            }
        return {"by_method": summary, "n_records": len(self.records)}

    def error_analysis(self) -> list[dict[str, Any]]:
        failures: list[dict[str, Any]] = []
        for record in self.records:
            result = record["result"]
            decision = result.get("decision") or {}
            conflicts = decision.get("conflicts") or []
            if conflicts:
                failures.append(
                    {
                        "example_id": record["example_id"],
                        "method_id": record["method_id"],
                        "conflicts": conflicts,
                    }
                )
        return failures
