"""In-memory tracker for unit tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RecordingTracker:
    """Capture tracker calls for assertions (no external service)."""

    runs: list[dict[str, Any]] = field(default_factory=list)
    metrics: list[dict[str, Any]] = field(default_factory=list)
    params: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    ended: list[str] = field(default_factory=list)
    _active: str | None = None

    def start_run(
        self,
        *,
        run_name: str,
        params: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        self._active = run_name
        self.runs.append(
            {
                "run_name": run_name,
                "params": dict(params or {}),
                "tags": dict(tags or {}),
            }
        )
        if params:
            self.params.append(dict(params))

    def log_metrics(
        self, metrics: dict[str, float], *, step: int | None = None
    ) -> None:
        self.metrics.append({"metrics": dict(metrics), "step": step})

    def log_params(self, params: dict[str, Any]) -> None:
        self.params.append(dict(params))

    def log_artifact(
        self, path: str | Path, *, artifact_path: str | None = None
    ) -> None:
        self.artifacts.append({"path": str(path), "artifact_path": artifact_path})

    def end_run(self, *, status: str = "FINISHED") -> None:
        self.ended.append(status)
        self._active = None
