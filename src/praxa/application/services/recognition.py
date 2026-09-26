"""Deterministic tag/keyword policy recognition."""

from __future__ import annotations

from praxa.domain.context import TaskContext
from praxa.domain.match import PolicyMatch
from praxa.domain.policy import Policy, Rule


class TagKeywordRecognizer:
    """Match rules whose conditions are satisfied by context tags/query text."""

    def recognize(self, *, policy: Policy, context: TaskContext) -> PolicyMatch:
        applicable: list[str] = []
        scores: dict[str, float] = {}

        for rule in policy.rules:
            matched, score = _rule_match(rule, context)
            if matched:
                applicable.append(rule.rule_id)
                scores[rule.rule_id] = score

        confidence = max(scores.values()) if scores else 0.0
        return PolicyMatch(
            applicable=applicable,
            confidence=confidence,
            scores=scores,
            rationale="tag_keyword_v1",
        )


def _rule_match(rule: Rule, context: TaskContext) -> tuple[bool, float]:
    if not rule.conditions:
        return True, 1.0

    tags = {tag.lower() for tag in context.tags}
    query = context.query.lower()
    hits = 0

    for condition in rule.conditions:
        kind = condition.kind.lower()
        value = condition.value.lower()

        if kind == "always":
            hits += 1
        elif kind == "tag" and value in tags:
            hits += 1
        elif kind == "keyword" and value in query:
            hits += 1
        else:
            return False, 0.0

    return True, hits / max(1, len(rule.conditions))
