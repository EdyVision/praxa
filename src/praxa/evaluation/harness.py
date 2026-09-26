"""Evaluation run harness over policy × dataset × methods."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from praxa.application.ports.dataset import DatasetPort
from praxa.application.ports.evaluation import StageEvaluator
from praxa.application.ports.operationalizer import Operationalizer
from praxa.application.ports.tracking import RunTracker
from praxa.application.services.provenance import build_run_manifest
from praxa.domain.execution import ExecutionResult
from praxa.domain.policy import Policy
from praxa.evaluation.results import EvalResults
from praxa.evaluation.tracking.metrics import metrics_from_results
from praxa.evaluation.tracking.null import NullTracker


@dataclass
class EvaluationRun:
    """Execute one policy-operationalization evaluation matrix.

    Consumer experiments own the research question. This harness records stage
    artifacts and optionally ships them to a ``RunTracker`` (Null or MLflow).
    """

    policy: Policy
    dataset: DatasetPort
    methods: list[Operationalizer]
    split: str = "test"
    seed: int | None = 42
    evaluators: list[StageEvaluator] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    tracker: RunTracker | None = None

    def run(self) -> EvalResults:
        if not self.methods:
            raise ValueError("methods must be non-empty")

        tracker = self.tracker or NullTracker()
        run_id = f"run_{uuid4().hex[:12]}"
        method_ids = [method.method_id for method in self.methods]
        manifest = build_run_manifest(
            run_id=run_id,
            policy=self.policy,
            dataset_id=self.dataset.dataset_id,
            method_ids=method_ids,
            seed=self.seed,
            metadata=self.metadata,
        )

        params = {
            "run_id": run_id,
            "policy_id": manifest.policy_id,
            "policy_version": manifest.policy_version,
            "policy_hash": manifest.policy_hash,
            "dataset_id": manifest.dataset_id,
            "split": self.split,
            "seed": self.seed,
            "method_ids": method_ids,
            "praxa_version": manifest.praxa_version,
        }
        tags = {
            "praxa.run_id": run_id,
            "praxa.policy_id": manifest.policy_id,
            "praxa.dataset_id": manifest.dataset_id,
        }

        status = "FINISHED"
        records: list[dict[str, Any]] = []
        results: list[ExecutionResult] = []

        tracker.start_run(run_name=run_id, params=params, tags=tags)
        try:
            for context in self.dataset.iter_split(self.split):
                for method in self.methods:
                    result = method.run(policy=self.policy, context=context)
                    scores: dict[str, Any] = {}
                    for evaluator in self.evaluators:
                        scores[evaluator.evaluator_id] = evaluator.score(result)
                    records.append(
                        {
                            "run_id": run_id,
                            "example_id": context.example_id,
                            "stratum": context.stratum,
                            "method_id": method.method_id,
                            "result": result.model_dump(mode="json"),
                            "scores": scores,
                        }
                    )
                    results.append(result)

            eval_results = EvalResults(
                manifest=manifest,
                records=records,
                results=results,
            )
            tracker.log_metrics(metrics_from_results(eval_results))
            _log_run_artifacts(tracker, eval_results)
            return eval_results
        except Exception:
            status = "FAILED"
            raise
        finally:
            tracker.end_run(status=status)


def _log_run_artifacts(tracker: RunTracker, results: EvalResults) -> None:
    with tempfile.TemporaryDirectory(prefix="praxa_eval_") as tmp:
        root = Path(tmp)
        manifest_path = root / "run_manifest.json"
        records_path = root / "eval_records.jsonl"
        compare_path = root / "compare.json"

        manifest_path.write_text(
            json.dumps(
                results.manifest.model_dump(mode="json"), indent=2, sort_keys=True
            )
            + "\n",
            encoding="utf-8",
        )
        with records_path.open("w", encoding="utf-8") as fh:
            for record in results.records:
                fh.write(json.dumps(record, sort_keys=True) + "\n")
        compare_path.write_text(
            json.dumps(results.compare(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        tracker.log_artifact(manifest_path, artifact_path="praxa")
        tracker.log_artifact(records_path, artifact_path="praxa")
        tracker.log_artifact(compare_path, artifact_path="praxa")
