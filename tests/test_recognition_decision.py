"""Recognition and decision pipeline tests."""

from __future__ import annotations

from praxa import Disposition, PolicyBuilder, TaskContext
from praxa.application.services.decision import decide
from praxa.application.services.recognition import TagKeywordRecognizer
from praxa.domain.policy import Condition


def _policy():
    return (
        PolicyBuilder("demo.v1")
        .rule(
            "ALLOW-1",
            disposition=Disposition.ALLOW,
            precedence=1,
            conditions=[Condition(kind="tag", value="general")],
            required=["general_info"],
        )
        .rule(
            "RESTRICT-1",
            disposition=Disposition.RESTRICT,
            precedence=5,
            conditions=[Condition(kind="tag", value="individual")],
            prohibited=["diagnose"],
            required=["redirect"],
        )
        .build()
    )


def test_tag_recognition_and_restrict_wins() -> None:
    policy = _policy()
    recognizer = TagKeywordRecognizer()
    context = TaskContext(
        example_id="e1",
        query="diagnose me",
        tags=["individual"],
    )
    match = recognizer.recognize(policy=policy, context=context)
    assert match.applicable == ["RESTRICT-1"]
    decision = decide(policy=policy, match=match)
    assert decision.disposition == Disposition.RESTRICT
    assert "diagnose" in decision.prohibited
    assert "redirect" in decision.required
