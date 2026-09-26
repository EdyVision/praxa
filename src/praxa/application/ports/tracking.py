"""Experiment / run tracking port."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class RunTracker(Protocol):
    """Sink for evaluation params, metrics, and artifacts.

    Implementations: NullTracker (default), MLflowTracker (optional extra).
    """

    def start_run(
        self,
        *,
        run_name: str,
        params: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> None: ...

    def log_metrics(
        self, metrics: dict[str, float], *, step: int | None = None
    ) -> None: ...

    def log_params(self, params: dict[str, Any]) -> None: ...

    def log_artifact(
        self, path: str | Path, *, artifact_path: str | None = None
    ) -> None: ...

    def end_run(self, *, status: str = "FINISHED") -> None: ...
