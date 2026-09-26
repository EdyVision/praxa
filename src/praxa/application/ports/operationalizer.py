"""Operationalizer port."""

from __future__ import annotations

from typing import Protocol

from praxa.domain.context import TaskContext
from praxa.domain.execution import ExecutionResult
from praxa.domain.policy import Policy


class Operationalizer(Protocol):
    """One method for turning policy + context into an execution result."""

    method_id: str

    def run(self, *, policy: Policy, context: TaskContext) -> ExecutionResult: ...
