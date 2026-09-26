"""OpenAI-compatible chat completions backend (stdlib only)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from praxa.domain.execution import ChatMessage


class OpenAICompatibleBackend:
    """Minimal ``/chat/completions`` client. No ``openai`` package required."""

    backend_id = "openai_compatible_v1"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_s: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s

    @classmethod
    def from_env(
        cls,
        *,
        model: str,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> OpenAICompatibleBackend:
        url = (
            base_url
            or os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("OPENAI_API_BASE")
        )
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not url:
            raise RuntimeError(
                "Set OPENAI_BASE_URL (OpenAI-compatible API root, including /v1)"
            )
        if not key:
            raise RuntimeError("Set OPENAI_API_KEY")
        return cls(base_url=url, api_key=key, model=model)

    def generate(
        self,
        messages: list[ChatMessage],
        *,
        max_new_tokens: int = 512,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_new_tokens,
            "temperature": 0.0,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"chat.completions HTTP {exc.code}: {detail}") from exc
        choices = body.get("choices") or []
        if not choices:
            raise RuntimeError(f"empty choices from {self.model}")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("missing message.content in completion")
        return content
