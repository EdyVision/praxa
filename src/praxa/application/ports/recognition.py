"""Policy recognition port."""

from __future__ import annotations

from typing import Protocol

from praxa.domain.context import TaskContext
from praxa.domain.match import PolicyMatch
from praxa.domain.policy import Policy


class PolicyRecognizer(Protocol):
    def recognize(self, *, policy: Policy, context: TaskContext) -> PolicyMatch: ...
