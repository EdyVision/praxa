"""Extract display text for a policy rule (clause projection)."""

from __future__ import annotations

from praxa.domain.policy import Rule


def rule_clause_text(rule: Rule) -> str:
    """Prefer metadata clause_text; otherwise title + required/prohibited notes."""
    meta = rule.metadata.get("clause_text")
    if isinstance(meta, str) and meta.strip():
        return meta.strip()

    parts: list[str] = []
    if rule.title.strip():
        parts.append(rule.title.strip())
    if rule.required:
        parts.append("Required: " + ", ".join(rule.required))
    if rule.prohibited:
        parts.append("Prohibited: " + ", ".join(rule.prohibited))
    for constraint in rule.constraints:
        desc = constraint.description.strip() or constraint.name
        parts.append(f"{constraint.polarity}: {desc}")
    return "\n".join(parts).strip()
