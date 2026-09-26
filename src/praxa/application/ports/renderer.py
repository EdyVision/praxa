"""Policy clause rendering port."""

from __future__ import annotations

from typing import Protocol

from praxa.domain.policy import Rule


class PolicyRenderer(Protocol):
    """Turn selected rules into prompt text."""

    renderer_id: str

    def render(
        self,
        rules: list[Rule],
        *,
        policy_label: str = "organization",
    ) -> str: ...
