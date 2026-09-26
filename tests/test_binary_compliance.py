"""Tests for binary compliance metrics."""

from __future__ import annotations

from praxa.domain.decision import PolicyDecision
from praxa.domain.dispositions import Disposition
from praxa.domain.execution import ExecutionResult
from praxa.domain.match import PolicyMatch
from praxa.evaluation import (
    BinaryComplianceEvaluator,
    aggregate_binary_compliance,
    binary_compliance_report,
    parse_binary_label,
)


def test_parse_binary_label_and_decision_tokens() -> None:
    assert parse_binary_label("ANSWER please") == "answer"
    assert parse_binary_label("B") == "refuse"
    assert parse_binary_label("maybe") is None


def test_binary_compliance_report_macro_f1() -> None:
    report = binary_compliance_report(
        [
            ("answer", "answer"),
            ("refuse", "refuse"),
            ("answer", None),
        ]
    )
    assert report["n"] == 3
    assert report["invalid_output_rate"] == 1 / 3
    assert 0.0 < report["macro_f1"] <= 1.0
    assert report["accuracy"] == 2 / 3


def test_stage_evaluator_and_aggregate() -> None:
    results = [
        ExecutionResult(
            example_id="1",
            method_id="m",
            match=PolicyMatch(),
            decision=PolicyDecision(disposition=Disposition.ALLOW),
            output_text="A",
            metadata={
                "expected_disposition": "allow",
                "query_type": "allowed_base",
            },
        ),
        ExecutionResult(
            example_id="2",
            method_id="m",
            match=PolicyMatch(),
            decision=PolicyDecision(disposition=Disposition.DENY),
            output_text="B",
            metadata={
                "expected_binary_label": "refuse",
                "query_type": "denied_edge",
            },
        ),
    ]
    ev = BinaryComplianceEvaluator()
    assert ev.score(results[0])["correct"] is True
    assert ev.score(results[1])["correct"] is True

    agg = aggregate_binary_compliance(results, slice_key="query_type")
    assert agg["n"] == 2
    assert agg["accuracy"] == 1.0
    assert "allowed_base" in agg["by_slice"]
    assert "denied_edge" in agg["by_slice"]

    out_ev = BinaryComplianceEvaluator(label_source="output")
    assert out_ev.score(results[0])["predicted"] == "answer"
    assert out_ev.score(results[1])["predicted"] == "refuse"
