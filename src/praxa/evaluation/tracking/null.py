"""No-op tracker (default)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class NullTracker:
    """Discard all tracking calls."""

    def start_run(
        self,
        *,
        run_name: str,
        params: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        return None

    def log_metrics(
        self, metrics: dict[str, float], *, step: int | None = None
    ) -> None:
        return None

    def log_params(self, params: dict[str, Any]) -> None:
        return None

    def log_artifact(
        self, path: str | Path, *, artifact_path: str | None = None
    ) -> None:
        return None

    def end_run(self, *, status: str = "FINISHED") -> None:
        return None
