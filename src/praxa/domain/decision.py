"""Policy decision: disposition plus explicit constraints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from praxa.domain.dispositions import Disposition


class PolicyDecision(BaseModel):
    """Resolved disposition and behavioral constraints for one example."""

    model_config = ConfigDict(extra="forbid")

    disposition: Disposition
    custom_disposition: str | None = None
    required: list[str] = Field(default_factory=list)
    prohibited: list[str] = Field(default_factory=list)
    matched_rule_ids: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)

    def resolved_disposition_label(self) -> str:
        if self.disposition == Disposition.CUSTOM:
            return self.custom_disposition or "custom"
        return str(self.disposition)
