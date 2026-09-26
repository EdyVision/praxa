"""Policy evaluation harness and metrics.

Imports operationalizers from ``praxa.operationalizers``. Does not define them.
"""

from __future__ import annotations

from praxa.evaluation.backends.fake_backend import FakeBackend
from praxa.evaluation.datasets import InMemoryDataset
from praxa.evaluation.harness import EvaluationRun
from praxa.evaluation.metrics.binary_compliance import (
    DEFAULT_DISPOSITION_MAP,
    BinaryComplianceEvaluator,
    aggregate_binary_compliance,
    binary_compliance_report,
    map_disposition_to_label,
    parse_binary_label,
)
from praxa.evaluation.metrics.hygiene import (
    clean_stop,
    contamination_hits,
    hygiene_report,
)
from praxa.evaluation.metrics.protocols import (
    DispositionCorrectnessEvaluator,
    HygieneEvaluator,
)
from praxa.evaluation.results import EvalResults
from praxa.evaluation.tracking import NullTracker, RecordingTracker, load_mlflow_tracker

__all__ = [
    "BinaryComplianceEvaluator",
    "DEFAULT_DISPOSITION_MAP",
    "DispositionCorrectnessEvaluator",
    "EvalResults",
    "EvaluationRun",
    "FakeBackend",
    "HygieneEvaluator",
    "InMemoryDataset",
    "NullTracker",
    "RecordingTracker",
    "aggregate_binary_compliance",
    "binary_compliance_report",
    "clean_stop",
    "contamination_hits",
    "hygiene_report",
    "load_mlflow_tracker",
    "map_disposition_to_label",
    "parse_binary_label",
]
