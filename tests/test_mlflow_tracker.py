"""MLflow tracker adapter tests (optional dependency)."""

from __future__ import annotations

import pytest

pytest.importorskip("mlflow")

from praxa.evaluation.tracking.mlflow import MLflowTracker


def test_mlflow_tracker_round_trip(tmp_path) -> None:
    db = tmp_path / "mlflow.db"
    uri = f"sqlite:///{db}"
    tracker = MLflowTracker(experiment="praxa-test", tracking_uri=uri)
    tracker.start_run(
        run_name="unit",
        params={"policy_id": "demo.v1", "seed": 1},
        tags={"praxa.test": "1"},
    )
    tracker.log_metrics({"n_records": 2.0, "method.context_prompt_v1.n": 2.0})
    artifact = tmp_path / "note.txt"
    artifact.write_text("ok\n", encoding="utf-8")
    tracker.log_artifact(artifact, artifact_path="praxa")
    tracker.end_run(status="FINISHED")
