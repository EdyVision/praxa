"""Context-prompt operationalizer: full policy JSON in the system prompt.

Thin wrapper around :class:`PromptOperationalizer` for backward compatibility.
Prefer ``PromptOperationalizer.full_policy_system(...)`` for new code.
"""

from __future__ import annotations

from praxa.application.ports.backend import ModelBackend
from praxa.application.services.recognition import TagKeywordRecognizer
from praxa.operationalizers.prompt import PromptOperationalizer


class ContextPromptOperationalizer(PromptOperationalizer):
    """Baseline method: serialize policy into system chat context and generate."""

    def __init__(
        self,
        backend: ModelBackend,
        *,
        recognizer: TagKeywordRecognizer | None = None,
        max_new_tokens: int = 512,
        system_prompt: str | None = None,
    ) -> None:
        super().__init__(
            backend,
            method_id="context_prompt_v1",
            system_prompt=system_prompt,
            policy_placement="system_json",
            recognizer=recognizer,
            max_new_tokens=max_new_tokens,
        )
