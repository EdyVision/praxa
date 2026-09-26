"""Dataset port."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from praxa.domain.context import TaskContext


class DatasetPort(Protocol):
    dataset_id: str

    def iter_split(self, split: str) -> Iterator[TaskContext]: ...
