"""Fluent policy construction and validation."""

from __future__ import annotations

from typing import Any, Self

from praxa.domain.dispositions import Disposition
from praxa.domain.policy import Condition, Policy, Rule


class PolicyBuilder:
    """Build and validate a Policy without mutating framework internals."""

    def __init__(self, policy_id: str, *, version: str = "0.1.0") -> None:
        self._policy_id = policy_id
        self._version = version
        self._title = ""
        self._description = ""
        self._domain = "general"
        self._rules: list[Rule] = []
        self._metadata: dict[str, Any] = {}

    def title(self, value: str) -> Self:
        self._title = value
        return self

    def description(self, value: str) -> Self:
        self._description = value
        return self

    def domain(self, value: str) -> Self:
        self._domain = value
        return self

    def metadata(self, **kwargs: Any) -> Self:
        self._metadata.update(kwargs)
        return self

    def rule(
        self,
        rule_id: str,
        *,
        title: str = "",
        disposition: Disposition = Disposition.RESTRICT,
        custom_disposition: str | None = None,
        conditions: list[Condition] | None = None,
        required: list[str] | None = None,
        prohibited: list[str] | None = None,
        precedence: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> Self:
        self._rules.append(
            Rule(
                rule_id=rule_id,
                title=title,
                disposition=disposition,
                custom_disposition=custom_disposition,
                conditions=list(conditions or []),
                required=list(required or []),
                prohibited=list(prohibited or []),
                precedence=precedence,
                metadata=dict(metadata or {}),
            )
        )
        return self

    def validate(self) -> list[str]:
        errors: list[str] = []
        try:
            policy = self._assemble()
        except ValueError as exc:
            return [str(exc)]

        for rule in policy.rules:
            overlap = set(rule.required) & set(rule.prohibited)
            if overlap:
                errors.append(
                    f"rule {rule.rule_id}: required/prohibited overlap {sorted(overlap)}"
                )
        return errors

    def build(self) -> Policy:
        errors = self.validate()
        if errors:
            raise ValueError("; ".join(errors))
        return self._assemble()

    def _assemble(self) -> Policy:
        return Policy(
            policy_id=self._policy_id,
            version=self._version,
            title=self._title,
            description=self._description,
            domain=self._domain,
            rules=list(self._rules),
            metadata=dict(self._metadata),
        )


# Alias matching the Notion brief.
CustomPolicy = PolicyBuilder
