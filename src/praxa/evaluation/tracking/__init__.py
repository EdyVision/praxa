"""Tracking adapters for evaluation runs."""

from __future__ import annotations

from praxa.evaluation.tracking.null import NullTracker
from praxa.evaluation.tracking.recording import RecordingTracker

__all__ = [
    "NullTracker",
    "RecordingTracker",
]


def load_mlflow_tracker(*args: object, **kwargs: object) -> object:
    """Lazy import so ``praxa`` installs without mlflow."""
    from praxa.evaluation.tracking.mlflow import MLflowTracker

    return MLflowTracker(*args, **kwargs)
