"""End-to-end library smoke validation (no network).

Runs synthetic demo packs and compositional operationalizer configs against
FakeBackend. Exit non-zero on failure.

Usage:
  uv run python scripts/validate_smoke.py
  make validate
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from praxa import Disposition, PolicyBuilder, TaskContext, TaskKind
from praxa.adapters.outbound.compass_import import (
    audit_compass_praxa_roundtrip,
    compass_to_praxa,
)
from praxa.adapters.outbound.policy_io import load_policy
from praxa.datasets.schema import DatasetRecord
from praxa.domain.policy import Condition
from praxa.evaluation import (
    BinaryComplianceEvaluator,
    DispositionCorrectnessEvaluator,
    EvaluationRun,
    FakeBackend,
    HygieneEvaluator,
    InMemoryDataset,
    aggregate_binary_compliance,
)
from praxa.operationalizers import PromptOperationalizer


def _check(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {name}{suffix}")
    if not ok:
        raise SystemExit(1)


def validate_example_packs() -> None:
    examples = ROOT / "examples"
    for pack in ("medical", "government"):
        policy = load_policy(examples / pack / "policy.yaml")
        _check(f"load {pack} policy", bool(policy.rules), policy.policy_id)


def validate_prompt_ladder() -> None:
    policy = (
        PolicyBuilder("validate.v1")
        .rule(
            "allow.info",
            title="general_info",
            disposition=Disposition.ALLOW,
            conditions=[Condition(kind="tag", value="general_info")],
            metadata={"clause_text": "Staff may share general information."},
        )
        .rule(
            "deny.diagnose",
            title="diagnose",
            disposition=Disposition.DENY,
            conditions=[Condition(kind="keyword", value="diagnose")],
            metadata={"clause_text": "Staff must not diagnose."},
        )
        .build()
    )
    context = TaskContext(
        example_id="v1",
        query="please diagnose me",
        tags=["general_info"],
        task_kind=TaskKind.BEHAVIORAL,
        expected_disposition="deny",
        metadata={"expected_binary_label": "refuse", "query_type": "denied_edge"},
    )
    backend = FakeBackend(default_text="B")
    methods = [
        PromptOperationalizer.base(backend),
        PromptOperationalizer.full_policy_system(backend),
        PromptOperationalizer.full_policy_user(backend),
        PromptOperationalizer.retrieved(backend, top_k=2, policy_label="ValidateCo"),
        PromptOperationalizer.few_shot(
            backend,
            demonstrations=[("vitamins?", "Yes, vitamins are ok.")],
        ),
        PromptOperationalizer.decision_only(backend),
    ]
    dataset = InMemoryDataset(
        "validate.ds",
        [DatasetRecord(example_id="v1", split="test", context=context)],
    )
    run = EvaluationRun(
        policy=policy,
        dataset=dataset,
        methods=methods,
        evaluators=[
            DispositionCorrectnessEvaluator(),
            HygieneEvaluator(contamination_markers=[]),
            BinaryComplianceEvaluator(label_source="output"),
        ],
    )
    results = run.run()
    _check("prompt ladder run", len(results.results) == len(methods))
    agg = aggregate_binary_compliance(
        results.results, label_source="output", slice_key="query_type"
    )
    _check("binary aggregate n", agg["n"] == len(methods), str(agg["n"]))


def validate_compass_roundtrip() -> None:
    compass = {
        "allowlist": {"vitamins": "May discuss vitamins."},
        "denylist": {"diagnose": "Must not diagnose."},
    }
    policy = compass_to_praxa(compass, policy_id="validate.compass", domain="medical")
    audit = audit_compass_praxa_roundtrip(compass, policy)
    _check("compass roundtrip", audit["ok"] is True, str(audit["n_praxa_rules"]))


def main() -> None:
    print("Praxa library smoke validation")
    validate_example_packs()
    validate_prompt_ladder()
    validate_compass_roundtrip()
    print("All smoke checks passed.")


if __name__ == "__main__":
    main()
