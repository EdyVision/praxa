"""Aggregate matched rules into a PolicyDecision."""

from __future__ import annotations

from praxa.domain.decision import PolicyDecision
from praxa.domain.dispositions import Disposition
from praxa.domain.match import PolicyMatch
from praxa.domain.policy import Policy

_DISPOSITION_RANK = {
    Disposition.DENY: 40,
    Disposition.RESTRICT: 30,
    Disposition.REDIRECT: 20,
    Disposition.ALLOW: 10,
    Disposition.CUSTOM: 25,
}


def decide(*, policy: Policy, match: PolicyMatch) -> PolicyDecision:
    rule_map = policy.rule_map()
    matched = [rule_map[rid] for rid in match.applicable if rid in rule_map]

    if not matched:
        return PolicyDecision(
            disposition=Disposition.ALLOW,
            matched_rule_ids=[],
            required=[],
            prohibited=[],
            conflicts=[],
        )

    matched_sorted = sorted(matched, key=lambda rule: (-rule.precedence, rule.rule_id))
    winner = max(
        matched_sorted,
        key=lambda rule: (_DISPOSITION_RANK.get(rule.disposition, 0), rule.precedence),
    )

    required: set[str] = set()
    prohibited: set[str] = set()
    for rule in matched_sorted:
        required.update(rule.required)
        prohibited.update(rule.prohibited)

    conflicts: list[str] = []
    overlap = required & prohibited
    if overlap:
        conflicts.append(f"required/prohibited overlap: {sorted(overlap)}")

    return PolicyDecision(
        disposition=winner.disposition,
        custom_disposition=winner.custom_disposition,
        required=sorted(required),
        prohibited=sorted(prohibited),
        matched_rule_ids=[rule.rule_id for rule in matched_sorted],
        conflicts=conflicts,
    )
