"""In-memory dataset helper for demos and unit tests."""

from __future__ import annotations

from collections.abc import Iterator

from praxa.datasets.schema import DatasetRecord
from praxa.domain.context import TaskContext


class InMemoryDataset:
    """Simple DatasetPort implementation for tests and tiny examples."""

    def __init__(self, dataset_id: str, records: list[DatasetRecord]) -> None:
        self.dataset_id = dataset_id
        self._records = list(records)

    def iter_split(self, split: str) -> Iterator[TaskContext]:
        for record in self._records:
            if record.split == split:
                yield record.context
