"""Deterministic fake model backend for tests."""

from __future__ import annotations

from praxa.domain.execution import ChatMessage


class FakeBackend:
    """Return scripted text; optional mapping by substring in the last user turn."""

    backend_id = "fake_v1"

    def __init__(
        self,
        *,
        default_text: str = "I cannot provide individualized medical advice.",
        responses: dict[str, str] | None = None,
    ) -> None:
        self.default_text = default_text
        self.responses = dict(responses or {})

    def generate(
        self,
        messages: list[ChatMessage],
        *,
        max_new_tokens: int = 512,
    ) -> str:
        del max_new_tokens
        blob = "\n".join(message.content for message in messages)
        for needle, text in self.responses.items():
            if needle.lower() in blob.lower():
                return text
        return self.default_text
