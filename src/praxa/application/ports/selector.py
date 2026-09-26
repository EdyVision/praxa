"""Policy clause selection port."""

from __future__ import annotations

from typing import Protocol

from praxa.domain.context import TaskContext
from praxa.domain.policy import Policy, Rule


class PolicySelector(Protocol):
    """Choose which rules apply as prompt context for a task."""

    selector_id: str

    def select(
        self,
        *,
        policy: Policy,
        context: TaskContext,
        top_k: int,
    ) -> list[Rule]: ...
