"""Typed policy core: Policy, Rule, Condition, Action, Constraint."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from praxa.domain.dispositions import Disposition
from praxa.domain.hashing import hash_payload


class Condition(BaseModel):
    """A matchable predicate on task context (tag, keyword, or free-form expression)."""

    model_config = ConfigDict(extra="forbid")

    kind: str = Field(description="Condition kind, e.g. tag, keyword, always.")
    value: str = Field(description="Operand for the condition kind.")


class Action(BaseModel):
    """Named behavior the operationalizer should realize."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""


class Constraint(BaseModel):
    """Hard limit on allowed behavior."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""
    polarity: str = Field(
        default="prohibited",
        description="required | prohibited",
    )

    @field_validator("polarity")
    @classmethod
    def _polarity_ok(cls, value: str) -> str:
        allowed = {"required", "prohibited"}
        if value not in allowed:
            raise ValueError(f"polarity must be one of {sorted(allowed)}")
        return value


class Rule(BaseModel):
    """One policy rule with conditions, disposition, and constraints."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str
    title: str = ""
    conditions: list[Condition] = Field(default_factory=list)
    disposition: Disposition = Disposition.RESTRICT
    custom_disposition: str | None = None
    required: list[str] = Field(default_factory=list)
    prohibited: list[str] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    precedence: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _custom_disposition_present(self) -> Rule:
        if self.disposition == Disposition.CUSTOM and not self.custom_disposition:
            raise ValueError("custom_disposition required when disposition=custom")
        return self


class Policy(BaseModel):
    """Versioned declarative policy document."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str
    version: str = "0.1.0"
    title: str = ""
    description: str = ""
    domain: str = "general"
    rules: list[Rule] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _unique_rule_ids(self) -> Policy:
        if not self.rules:
            raise ValueError("policy must contain at least one rule")
        ids = [rule.rule_id for rule in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate rule_id values are not allowed")
        return self

    def content_hash(self) -> str:
        return hash_payload(self.model_dump(mode="json"))

    def rule_map(self) -> dict[str, Rule]:
        return {rule.rule_id: rule for rule in self.rules}
