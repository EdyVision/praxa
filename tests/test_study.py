"""End-to-end evaluation harness with FakeBackend + tracker."""

from __future__ import annotations

from praxa import Disposition, PolicyBuilder, TaskContext, TaskKind
from praxa.adapters.outbound.policy_io import dump_policy, load_policy
from praxa.datasets.schema import DatasetRecord
from praxa.domain.policy import Condition
from praxa.evaluation import (
    DispositionCorrectnessEvaluator,
    EvaluationRun,
    FakeBackend,
    InMemoryDataset,
    RecordingTracker,
)
from praxa.operationalizers import ContextPromptOperationalizer


def _toy_policy_and_dataset(tmp_path):
    policy = (
        PolicyBuilder("demo.v1")
        .rule(
            "R1",
            disposition=Disposition.RESTRICT,
            conditions=[Condition(kind="tag", value="edge")],
            prohibited=["diagnose"],
        )
        .build()
    )
    path = tmp_path / "policy.yaml"
    dump_policy(policy, path)
    loaded = load_policy(path)

    dataset = InMemoryDataset(
        "demo.ds",
        [
            DatasetRecord(
                example_id="e1",
                split="test",
                context=TaskContext(
                    example_id="e1",
                    query="please diagnose me",
                    tags=["edge"],
                    task_kind=TaskKind.BEHAVIORAL,
                    expected_disposition="restrict",
                ),
            )
        ],
    )
    return loaded, dataset


def test_evaluation_run_scores(tmp_path) -> None:
    loaded, dataset = _toy_policy_and_dataset(tmp_path)
    run = EvaluationRun(
        policy=loaded,
        dataset=dataset,
        methods=[ContextPromptOperationalizer(FakeBackend())],
        evaluators=[DispositionCorrectnessEvaluator()],
    )
    results = run.run()
    assert results.compare()["n_records"] == 1
    score = results.records[0]["scores"]["disposition_correctness_v1"]
    assert score["correct"] is True
    assert results.results[0].output_text


def test_evaluation_run_logs_to_tracker(tmp_path) -> None:
    loaded, dataset = _toy_policy_and_dataset(tmp_path)
    tracker = RecordingTracker()
    run = EvaluationRun(
        policy=loaded,
        dataset=dataset,
        methods=[ContextPromptOperationalizer(FakeBackend())],
        evaluators=[DispositionCorrectnessEvaluator()],
        tracker=tracker,
    )
    results = run.run()

    assert len(tracker.runs) == 1
    assert tracker.runs[0]["params"]["policy_id"] == "demo.v1"
    assert tracker.runs[0]["params"]["policy_hash"] == results.manifest.policy_hash
    assert tracker.ended == ["FINISHED"]
    assert tracker.metrics
    assert "disposition_correctness_rate" in tracker.metrics[0]["metrics"]
    assert len(tracker.artifacts) == 3
