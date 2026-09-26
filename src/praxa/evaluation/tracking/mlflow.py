"""MLflow RunTracker adapter (optional extra: praxa[mlflow])."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _require_mlflow() -> Any:
    try:
        import mlflow
    except ImportError as exc:
        raise ImportError(
            "MLflowTracker requires mlflow. Install with: "
            "uv add 'praxa[mlflow]' or pip install 'praxa[mlflow]'"
        ) from exc
    return mlflow


def _stringify_params(params: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in params.items():
        if value is None:
            out[str(key)] = ""
        elif isinstance(value, (list, tuple)):
            out[str(key)] = ",".join(str(item) for item in value)
        else:
            out[str(key)] = str(value)
    return out


class MLflowTracker:
    """Log EvaluationRun provenance to an MLflow experiment."""

    def __init__(
        self,
        *,
        experiment: str,
        tracking_uri: str | None = None,
        run_name_prefix: str = "",
    ) -> None:
        self.experiment = experiment
        self.tracking_uri = tracking_uri
        self.run_name_prefix = run_name_prefix
        self._mlflow = _require_mlflow()
        if tracking_uri:
            self._mlflow.set_tracking_uri(tracking_uri)
        self._mlflow.set_experiment(experiment)

    def start_run(
        self,
        *,
        run_name: str,
        params: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        name = f"{self.run_name_prefix}{run_name}" if self.run_name_prefix else run_name
        self._mlflow.start_run(run_name=name)
        if params:
            self.log_params(params)
        if tags:
            for key, value in tags.items():
                self._mlflow.set_tag(key, value)

    def log_metrics(
        self, metrics: dict[str, float], *, step: int | None = None
    ) -> None:
        clean = {str(k): float(v) for k, v in metrics.items()}
        if not clean:
            return
        if step is None:
            self._mlflow.log_metrics(clean)
        else:
            self._mlflow.log_metrics(clean, step=step)

    def log_params(self, params: dict[str, Any]) -> None:
        safe = _stringify_params(params)
        if safe:
            self._mlflow.log_params(safe)

    def log_artifact(
        self, path: str | Path, *, artifact_path: str | None = None
    ) -> None:
        self._mlflow.log_artifact(str(path), artifact_path=artifact_path)

    def end_run(self, *, status: str = "FINISHED") -> None:
        # MLflow statuses: FINISHED, FAILED, KILLED
        ml_status = status if status in {"FINISHED", "FAILED", "KILLED"} else "FINISHED"
        self._mlflow.end_run(status=ml_status)
