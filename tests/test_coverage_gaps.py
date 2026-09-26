"""Close coverage gaps across adapters, metrics, tracking, and edge paths."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from praxa import Disposition, PolicyBuilder, TaskContext, TaskKind
from praxa.adapters.outbound.compass_import import (
    audit_compass_praxa_roundtrip,
    compass_to_praxa,
    load_compass_policy_json,
    praxa_to_compass,
)
from praxa.adapters.outbound.openai_compatible_backend import OpenAICompatibleBackend
from praxa.adapters.outbound.policy_io import dump_policy, load_policy
from praxa.application.services.clause_text import rule_clause_text
from praxa.application.services.decision import decide
from praxa.application.services.lexical_selector import LexicalPolicySelector
from praxa.application.services.readable_renderer import ReadablePolicyRenderer
from praxa.application.services.recognition import TagKeywordRecognizer
from praxa.domain.decision import PolicyDecision
from praxa.domain.execution import ChatMessage, ExecutionResult
from praxa.domain.match import PolicyMatch
from praxa.domain.policy import Condition, Constraint, Policy, Rule
from praxa.datasets.schema import DatasetRecord
from praxa.evaluation import (
    BinaryComplianceEvaluator,
    DispositionCorrectnessEvaluator,
    EvaluationRun,
    FakeBackend,
    InMemoryDataset,
    binary_compliance_report,
    map_disposition_to_label,
)
from praxa.evaluation.results import EvalResults
from praxa.evaluation.tracking import NullTracker, load_mlflow_tracker
from praxa.evaluation.tracking.metrics import metrics_from_results
from praxa.operationalizers import PromptOperationalizer
from praxa.application.services.provenance import RunManifest, build_run_manifest


def _policy():
    return (
        PolicyBuilder("cov.v1")
        .rule(
            "allow.a",
            title="alpha_topic",
            disposition=Disposition.ALLOW,
            conditions=[Condition(kind="tag", value="alpha")],
            metadata={"clause_text": "Allow alpha discussions."},
        )
        .rule(
            "deny.b",
            title="beta",
            disposition=Disposition.DENY,
            conditions=[Condition(kind="keyword", value="secret")],
            prohibited=["secret"],
        )
        .build()
    )


def test_clause_text_fallback_without_metadata() -> None:
    rule = Rule(
        rule_id="r1",
        title="Topic One",
        disposition=Disposition.RESTRICT,
        required=["cite_source"],
        prohibited=["invent_facts"],
        constraints=[
            Constraint(
                name="length", description="Keep answers short", polarity="required"
            )
        ],
    )
    text = rule_clause_text(rule)
    assert "Topic One" in text
    assert "Required: cite_source" in text
    assert "Prohibited: invent_facts" in text
    assert "required: Keep answers short" in text


def test_policy_validation_errors() -> None:
    with pytest.raises(ValidationError):
        Constraint(name="x", polarity="maybe")
    with pytest.raises(ValidationError):
        Rule(
            rule_id="c1",
            disposition=Disposition.CUSTOM,
            custom_disposition=None,
        )
    with pytest.raises(ValidationError):
        Policy(policy_id="p", rules=[])
    with pytest.raises(ValidationError):
        Policy(
            policy_id="p",
            rules=[
                Rule(rule_id="dup", disposition=Disposition.ALLOW),
                Rule(rule_id="dup", disposition=Disposition.DENY),
            ],
        )


def test_decision_empty_match_and_conflicts() -> None:
    policy = _policy()
    empty = decide(policy=policy, match=PolicyMatch())
    assert empty.disposition == Disposition.ALLOW
    assert empty.matched_rule_ids == []

    conflict_policy = (
        PolicyBuilder("conflict.v1")
        .rule(
            "a",
            disposition=Disposition.ALLOW,
            required=["x"],
            conditions=[Condition(kind="always", value="1")],
        )
        .rule(
            "b",
            disposition=Disposition.DENY,
            prohibited=["x"],
            conditions=[Condition(kind="always", value="1")],
            precedence=100,
        )
        .build()
    )
    match = TagKeywordRecognizer().recognize(
        policy=conflict_policy,
        context=TaskContext(example_id="e", query="q", task_kind=TaskKind.BEHAVIORAL),
    )
    decision = decide(policy=conflict_policy, match=match)
    assert decision.conflicts
    assert decision.disposition == Disposition.DENY


def test_custom_disposition_label() -> None:
    decision = PolicyDecision(
        disposition=Disposition.CUSTOM, custom_disposition="escalate"
    )
    assert decision.resolved_disposition_label() == "escalate"
    bare = PolicyDecision(disposition=Disposition.CUSTOM)
    assert bare.resolved_disposition_label() == "custom"


def test_recognition_always_and_empty_conditions() -> None:
    policy = (
        PolicyBuilder("rec.v1")
        .rule(
            "always",
            disposition=Disposition.ALLOW,
            conditions=[Condition(kind="always", value="1")],
        )
        .rule("empty", disposition=Disposition.RESTRICT, conditions=[])
        .build()
    )
    match = TagKeywordRecognizer().recognize(
        policy=policy,
        context=TaskContext(example_id="e", query="hi", task_kind=TaskKind.BEHAVIORAL),
    )
    assert "always" in match.applicable
    assert "empty" in match.applicable


def test_lexical_selector_edges() -> None:
    selector = LexicalPolicySelector()
    policy = _policy()
    ctx = TaskContext(example_id="e", query="", task_kind=TaskKind.BEHAVIORAL)
    assert selector.select(policy=policy, context=ctx, top_k=3) == []
    assert selector.select(policy=policy, context=ctx, top_k=0) == []
    empty_text = (
        PolicyBuilder("empty.v1")
        .rule(
            "blank",
            title="",
            disposition=Disposition.ALLOW,
            metadata={"clause_text": ""},
        )
        .build()
    )
    ctx2 = TaskContext(
        example_id="e", query="alpha vitamins", task_kind=TaskKind.BEHAVIORAL
    )
    assert selector.select(policy=empty_text, context=ctx2, top_k=1) == []


def test_readable_renderer_disposition_headings() -> None:
    renderer = ReadablePolicyRenderer()
    allow = Rule(
        rule_id="a",
        title="ok",
        disposition=Disposition.ALLOW,
        metadata={"clause_text": "yes"},
    )
    deny = Rule(
        rule_id="d",
        title="no",
        disposition=Disposition.DENY,
        metadata={"clause_text": "nope"},
    )
    restrict = Rule(
        rule_id="r",
        title="maybe",
        disposition=Disposition.RESTRICT,
        metadata={"clause_text": "careful"},
    )
    text = renderer.render([allow, deny, restrict], policy_label="Acme")
    assert "Allowed" in text
    assert "Prohibited" in text
    assert "Restrict" in text


def test_policy_io_json_and_invalid(tmp_path: Path) -> None:
    policy = _policy()
    path = tmp_path / "policy.json"
    dump_policy(policy, path)
    loaded = load_policy(path)
    assert loaded.policy_id == policy.policy_id

    bad = tmp_path / "bad.json"
    bad.write_text("[1, 2]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_policy(bad)


def test_compass_error_paths(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_text("[1]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        load_compass_policy_json(path)

    with pytest.raises(ValueError, match="must be an object"):
        compass_to_praxa({"allowlist": ["not", "a", "dict"]}, policy_id="x", domain="d")
    with pytest.raises(ValueError, match="empty COMPASS topic"):
        compass_to_praxa({"allowlist": {"": "t"}}, policy_id="x", domain="d")
    with pytest.raises(ValueError, match="must be a string"):
        compass_to_praxa({"allowlist": {"t": 1}}, policy_id="x", domain="d")

    policy = compass_to_praxa(
        {"allowlist": {"a": "A"}, "denylist": {"b": "B"}},
        policy_id="c.v1",
        domain="d",
    )
    missing_topic = policy.model_copy(
        update={
            "rules": [
                policy.rules[0].model_copy(
                    update={"metadata": {"compass_list_type": "allowlist"}}
                )
            ]
        }
    )
    with pytest.raises(ValueError, match="missing compass_topic"):
        praxa_to_compass(missing_topic)

    wrong_text = policy.model_copy(
        update={
            "rules": [
                policy.rules[0].model_copy(
                    update={
                        "metadata": {
                            **policy.rules[0].metadata,
                            "clause_text": "WRONG",
                        }
                    }
                ),
                policy.rules[1],
            ]
        }
    )
    audit = audit_compass_praxa_roundtrip(
        {"allowlist": {"a": "A"}, "denylist": {"b": "B"}},
        wrong_text,
    )
    assert audit["ok"] is False


def test_openai_compatible_backend_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    backend = OpenAICompatibleBackend.from_env(model="demo-model")
    assert backend.model == "demo-model"

    class _Resp:
        def read(self) -> bytes:
            return json.dumps(
                {"choices": [{"message": {"content": "hello from api"}}]}
            ).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    with patch("urllib.request.urlopen", return_value=_Resp()):
        out = backend.generate(
            [ChatMessage(role="user", content="hi")], max_new_tokens=16
        )
    assert out == "hello from api"

    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_BASE_URL"):
        OpenAICompatibleBackend.from_env(model="x")


def test_openai_http_error() -> None:
    backend = OpenAICompatibleBackend(
        base_url="https://example.test/v1", api_key="k", model="m"
    )

    class _HTTPError(Exception):
        def __init__(self):
            self.code = 500

        def read(self):
            return b"boom"

    import urllib.error

    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError(
            url="https://example.test/v1/chat/completions",
            code=500,
            msg="err",
            hdrs=None,
            fp=MagicMock(read=lambda: b"boom"),
        ),
    ):
        with pytest.raises(RuntimeError, match="HTTP 500"):
            backend.generate([ChatMessage(role="user", content="hi")])


def test_binary_compliance_edge_helpers() -> None:
    assert map_disposition_to_label(None) is None
    with pytest.raises(ValueError):
        binary_compliance_report([("answer", "answer")], invalid_fill="nope")
    assert (
        BinaryComplianceEvaluator(label_source="decision").score(
            ExecutionResult(
                example_id="e",
                method_id="m",
                match=PolicyMatch(),
                decision=PolicyDecision(disposition=Disposition.ALLOW),
                metadata={},
            )
        )["expected"]
        is None
    )


def test_eval_results_error_analysis_and_disposition_evaluator() -> None:
    result = ExecutionResult(
        example_id="e1",
        method_id="m",
        match=PolicyMatch(),
        decision=PolicyDecision(
            disposition=Disposition.ALLOW, conflicts=["required/prohibited overlap"]
        ),
        metadata={"expected_disposition": "allow"},
    )
    results = EvalResults(
        manifest=build_run_manifest(
            run_id="r1",
            policy=_policy(),
            dataset_id="ds",
            method_ids=["m"],
        ),
        records=[
            {
                "example_id": "e1",
                "method_id": "m",
                "result": result.model_dump(mode="json"),
            }
        ],
        results=[result],
    )
    failures = results.error_analysis()
    assert failures and failures[0]["conflicts"]
    assert DispositionCorrectnessEvaluator().score(result)["correct"] is True
    metrics = metrics_from_results(results)
    assert "n_records" in metrics


def test_harness_failure_path() -> None:
    class Boom:
        method_id = "boom"

        def run(self, *, policy, context):
            raise RuntimeError("explode")

    dataset = InMemoryDataset(
        "ds",
        [
            DatasetRecord(
                example_id="e",
                split="test",
                context=TaskContext(
                    example_id="e", query="q", task_kind=TaskKind.BEHAVIORAL
                ),
            )
        ],
    )
    run = EvaluationRun(
        policy=_policy(), dataset=dataset, methods=[Boom()], tracker=NullTracker()
    )
    with pytest.raises(RuntimeError, match="explode"):
        run.run()
    with pytest.raises(ValueError, match="non-empty"):
        EvaluationRun(policy=_policy(), dataset=dataset, methods=[]).run()


def test_prompt_operationalizer_validation_and_few_shot_retrieved() -> None:
    with pytest.raises(ValueError, match="top_k"):
        PromptOperationalizer(FakeBackend(), policy_placement="retrieved", top_k=0)
    op = PromptOperationalizer.full_policy_system(FakeBackend())
    assert op.method_id == "context_prompt_v1"


def test_stub_package_exports() -> None:
    from praxa.evaluation import alignment, memory
    from praxa import provenance
    from praxa.provenance import manifest

    assert alignment.Disposition is Disposition
    assert memory.MemoryKind
    assert provenance
    assert manifest.RunManifest is RunManifest


def test_mlflow_tracker_mocked() -> None:
    fake = MagicMock()
    with patch("praxa.evaluation.tracking.mlflow._require_mlflow", return_value=fake):
        tracker = load_mlflow_tracker(
            experiment="exp", tracking_uri="file:///tmp/ml", run_name_prefix="p-"
        )
        tracker.start_run(
            run_name="r1",
            params={"seed": 1, "ids": ["a", "b"], "none": None},
            tags={"t": "1"},
        )
        tracker.log_metrics({})
        tracker.log_metrics({"n": 1.0}, step=2)
        tracker.log_params({})
        tracker.log_artifact("/tmp/x.txt", artifact_path="praxa")
        tracker.end_run(status="WEIRD")
        tracker.end_run(status="FAILED")

    fake.set_tracking_uri.assert_called()
    fake.set_experiment.assert_called_with("exp")
    fake.start_run.assert_called()
    fake.log_metrics.assert_called()
    fake.end_run.assert_called()


def test_mlflow_require_import_error() -> None:
    import builtins

    real_import = builtins.__import__

    def _guard(name, *args, **kwargs):
        if name == "mlflow" or name.startswith("mlflow."):
            raise ImportError("no mlflow")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=_guard):
        from praxa.evaluation.tracking import mlflow as mlmod

        with pytest.raises(ImportError, match="praxa\\[mlflow\\]"):
            mlmod._require_mlflow()


def test_null_tracker_log_artifact(tmp_path: Path) -> None:
    tracker = NullTracker()
    tracker.start_run(run_name="n")
    tracker.log_metrics({"a": 1.0})
    tracker.log_params({"b": "c"})
    tracker.log_artifact(tmp_path / "missing.txt")
    tracker.end_run()
