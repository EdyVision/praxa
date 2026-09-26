"""Human-readable rendering of selected policy rules."""

from __future__ import annotations

from praxa.application.services.clause_text import rule_clause_text
from praxa.domain.dispositions import Disposition
from praxa.domain.policy import Rule


def _section_heading(rule: Rule) -> str:
    if rule.disposition == Disposition.ALLOW:
        return "Allowed"
    if rule.disposition == Disposition.DENY:
        return "Prohibited"
    return rule.disposition.value.replace("_", " ").title()


class ReadablePolicyRenderer:
    """Readable multi-section policy block for retrieved prompts."""

    renderer_id = "readable_v1"

    def render(
        self,
        rules: list[Rule],
        *,
        policy_label: str = "organization",
    ) -> str:
        heading = f"Relevant {policy_label} policy rules"
        if not rules:
            return (
                f"# {heading}\n\n"
                "No policy clause matched the query under the lexical selector."
            )

        lines = [f"# {heading}", ""]
        for rule in rules:
            title = (rule.title or rule.rule_id).replace("_", " ").title()
            lines.append(f"## {_section_heading(rule)}: {title}")
            lines.append(rule_clause_text(rule))
            lines.append("")
        return "\n".join(lines).strip()
