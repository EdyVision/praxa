"""Model backend port."""

from __future__ import annotations

from typing import Protocol

from praxa.domain.execution import ChatMessage


class ModelBackend(Protocol):
    """Generate text from chat messages. Implementations live in adapters."""

    backend_id: str

    def generate(
        self,
        messages: list[ChatMessage],
        *,
        max_new_tokens: int = 512,
    ) -> str: ...
