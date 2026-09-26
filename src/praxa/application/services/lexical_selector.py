"""Lexical overlap policy selector (query tokens vs rule clause text)."""

from __future__ import annotations

import re

from praxa.application.services.clause_text import rule_clause_text
from praxa.domain.context import TaskContext
from praxa.domain.policy import Policy, Rule

_TOKEN = re.compile(r"[a-z0-9']+")


def tokenize(text: str) -> set[str]:
    return {
        match.group(0)
        for match in _TOKEN.finditer(text.lower())
        if len(match.group(0)) > 2
    }


def lexical_relevance(query: str, rule: Rule) -> float:
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0
    title = rule.title.replace("_", " ")
    clause = rule_clause_text(rule)
    clause_tokens = tokenize(f"{title} {clause}")
    if not clause_tokens:
        return 0.0
    overlap = len(query_tokens & clause_tokens)
    return overlap / len(query_tokens)


class LexicalPolicySelector:
    """Frozen lexical overlap selector; uses query text only."""

    selector_id = "lexical_v1"

    def select(
        self,
        *,
        policy: Policy,
        context: TaskContext,
        top_k: int,
    ) -> list[Rule]:
        if top_k <= 0:
            return []
        scored = [
            (lexical_relevance(context.query, rule), rule.rule_id, rule)
            for rule in policy.rules
        ]
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [rule for score, _, rule in scored[:top_k] if score > 0.0]
