"""Tests for compositional PromptOperationalizer configs."""

from __future__ import annotations

from praxa import Disposition, PolicyBuilder, TaskContext, TaskKind
from praxa.domain.policy import Condition
from praxa.evaluation import FakeBackend
from praxa.operationalizers import PromptOperationalizer


def _policy():
    return (
        PolicyBuilder("demo.v1")
        .rule(
            "allow.vitamins",
            title="vitamins",
            disposition=Disposition.ALLOW,
            conditions=[Condition(kind="tag", value="vitamins")],
            metadata={
                "clause_text": "Staff may discuss over-the-counter vitamins.",
            },
        )
        .rule(
            "deny.diagnose",
            title="diagnose",
            disposition=Disposition.DENY,
            conditions=[Condition(kind="keyword", value="diagnose")],
            metadata={
                "clause_text": "Staff must not diagnose medical conditions.",
            },
        )
        .build()
    )


def test_base_has_no_policy_body() -> None:
    op = PromptOperationalizer.base(FakeBackend(), system_prompt="Be helpful.")
    messages = op.prepare_messages(
        policy=_policy(),
        context=TaskContext(
            example_id="e1",
            query="Can I take vitamins?",
            task_kind=TaskKind.BEHAVIORAL,
        ),
    )
    assert messages[0].content == "Be helpful."
    assert "allow.vitamins" not in messages[0].content
    assert messages[1].content == "Can I take vitamins?"


def test_full_policy_user_places_json_in_user_turn() -> None:
    op = PromptOperationalizer.full_policy_user(FakeBackend())
    messages = op.prepare_messages(
        policy=_policy(),
        context=TaskContext(
            example_id="e1",
            query="hello",
            task_kind=TaskKind.BEHAVIORAL,
        ),
    )
    assert "# Company Policies" in messages[1].content
    assert "demo.v1" in messages[1].content
    assert "hello" in messages[1].content


def test_retrieved_selects_relevant_clause() -> None:
    op = PromptOperationalizer.retrieved(FakeBackend(), top_k=1, policy_label="DemoCo")
    messages = op.prepare_messages(
        policy=_policy(),
        context=TaskContext(
            example_id="e1",
            query="please diagnose my rash",
            task_kind=TaskKind.BEHAVIORAL,
        ),
    )
    assert "Relevant DemoCo policy rules" in messages[0].content
    assert "must not diagnose" in messages[0].content
    assert op.last_selected_rule_ids == ["deny.diagnose"]


def test_few_shot_interleaves_demos() -> None:
    op = PromptOperationalizer.few_shot(
        FakeBackend(),
        demonstrations=[
            ("May I ask about vitamins?", "Yes, vitamins are allowed."),
            ("Diagnose me", "I cannot diagnose."),
        ],
    )
    messages = op.prepare_messages(
        policy=_policy(),
        context=TaskContext(
            example_id="e1",
            query="final query",
            task_kind=TaskKind.BEHAVIORAL,
        ),
    )
    roles = [m.role for m in messages]
    assert roles == ["system", "user", "assistant", "user", "assistant", "user"]
    assert messages[-1].content == "final query"


def test_decision_only_appends_contract_and_runs() -> None:
    op = PromptOperationalizer.decision_only(FakeBackend(default_text="B"))
    result = op.run(
        policy=_policy(),
        context=TaskContext(
            example_id="e1",
            query="please diagnose me",
            task_kind=TaskKind.BEHAVIORAL,
            expected_disposition="deny",
        ),
    )
    assert "Reply with exactly one character" in result.messages[0].content
    assert result.output_text == "B"
    assert result.method_id == "decision_only_v1"


def test_context_prompt_alias_still_works() -> None:
    from praxa.operationalizers import ContextPromptOperationalizer

    op = ContextPromptOperationalizer(FakeBackend())
    result = op.run(
        policy=_policy(),
        context=TaskContext(
            example_id="e1",
            query="vitamins ok?",
            tags=["vitamins"],
            task_kind=TaskKind.BEHAVIORAL,
        ),
    )
    assert result.method_id == "context_prompt_v1"
    assert "Policy (demo.v1" in result.messages[0].content
