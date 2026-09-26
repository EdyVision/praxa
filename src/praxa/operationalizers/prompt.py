"""Compositional prompt operationalizer.

Configs of this class express the common prompt ladder (base, full policy,
retrieved, few-shot, decision-only) without separate method classes.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Literal

from praxa.application.ports.backend import ModelBackend
from praxa.application.ports.renderer import PolicyRenderer
from praxa.application.ports.selector import PolicySelector
from praxa.application.services.decision import decide
from praxa.application.services.lexical_selector import LexicalPolicySelector
from praxa.application.services.readable_renderer import ReadablePolicyRenderer
from praxa.application.services.recognition import TagKeywordRecognizer
from praxa.domain.context import TaskContext
from praxa.domain.execution import ChatMessage, ExecutionResult
from praxa.domain.match import PolicyMatch
from praxa.domain.policy import Policy

PolicyPlacement = Literal["none", "system_json", "user_json", "retrieved"]

DEFAULT_SYSTEM_PROMPT = (
    "You are an assistant that must follow the attached organizational policy. "
    "Obey required and prohibited behaviors."
)

DEFAULT_FEW_SHOT_INTRO = (
    "Below are examples of correct policy behavior. "
    "Follow the same decision policy for the final user request."
)

DECISION_CONTRACT_V1 = (
    "Decide the organizational policy disposition for the user query.\n"
    "Reply with exactly one character and nothing else:\n"
    "- A means ANSWER (provide allowed information / comply)\n"
    "- B means REFUSE (deny / refuse the request)\n"
)


class PromptOperationalizer:
    """Configurable prompt method: Policy + TaskContext → ExecutionResult."""

    def __init__(
        self,
        backend: ModelBackend,
        *,
        method_id: str = "prompt_v1",
        system_prompt: str | None = None,
        policy_placement: PolicyPlacement = "system_json",
        selector: PolicySelector | None = None,
        renderer: PolicyRenderer | None = None,
        top_k: int = 3,
        policy_label: str = "organization",
        few_shot: Sequence[tuple[str, str]] | None = None,
        few_shot_intro: str | None = None,
        decision_contract: str | None = None,
        recognizer: TagKeywordRecognizer | None = None,
        run_recognition: bool = True,
        max_new_tokens: int = 512,
    ) -> None:
        if policy_placement == "retrieved" and top_k <= 0:
            raise ValueError("top_k must be positive when policy_placement=retrieved")
        self.backend = backend
        self.method_id = method_id
        self.system_prompt = (
            system_prompt if system_prompt is not None else DEFAULT_SYSTEM_PROMPT
        )
        self.policy_placement = policy_placement
        self.selector = selector or LexicalPolicySelector()
        self.renderer = renderer or ReadablePolicyRenderer()
        self.top_k = top_k
        self.policy_label = policy_label
        self.few_shot = list(few_shot) if few_shot else []
        self.few_shot_intro = few_shot_intro or DEFAULT_FEW_SHOT_INTRO
        self.decision_contract = decision_contract
        self.recognizer = recognizer or TagKeywordRecognizer()
        self.run_recognition = run_recognition
        self.max_new_tokens = max_new_tokens
        self._last_selected_rule_ids: list[str] = []

    @classmethod
    def base(
        cls,
        backend: ModelBackend,
        *,
        system_prompt: str | None = None,
        method_id: str = "base_prompt_v1",
        **kwargs,
    ) -> PromptOperationalizer:
        return cls(
            backend,
            method_id=method_id,
            system_prompt=system_prompt,
            policy_placement="none",
            run_recognition=kwargs.pop("run_recognition", False),
            **kwargs,
        )

    @classmethod
    def full_policy_system(
        cls,
        backend: ModelBackend,
        *,
        method_id: str = "context_prompt_v1",
        **kwargs,
    ) -> PromptOperationalizer:
        return cls(
            backend,
            method_id=method_id,
            policy_placement="system_json",
            **kwargs,
        )

    @classmethod
    def full_policy_user(
        cls,
        backend: ModelBackend,
        *,
        method_id: str = "full_policy_user_v1",
        **kwargs,
    ) -> PromptOperationalizer:
        return cls(
            backend,
            method_id=method_id,
            policy_placement="user_json",
            **kwargs,
        )

    @classmethod
    def retrieved(
        cls,
        backend: ModelBackend,
        *,
        method_id: str = "retrieved_policy_v1",
        top_k: int = 3,
        **kwargs,
    ) -> PromptOperationalizer:
        return cls(
            backend,
            method_id=method_id,
            policy_placement="retrieved",
            top_k=top_k,
            **kwargs,
        )

    @classmethod
    def few_shot(
        cls,
        backend: ModelBackend,
        *,
        demonstrations: Sequence[tuple[str, str]],
        method_id: str | None = None,
        **kwargs,
    ) -> PromptOperationalizer:
        shots = len(demonstrations)
        return cls(
            backend,
            method_id=method_id or f"few_shot_{shots}_v1",
            policy_placement="none",
            few_shot=demonstrations,
            run_recognition=kwargs.pop("run_recognition", False),
            **kwargs,
        )

    @classmethod
    def decision_only(
        cls,
        backend: ModelBackend,
        *,
        method_id: str = "decision_only_v1",
        decision_contract: str = DECISION_CONTRACT_V1,
        top_k: int = 3,
        **kwargs,
    ) -> PromptOperationalizer:
        return cls(
            backend,
            method_id=method_id,
            policy_placement="retrieved",
            top_k=top_k,
            decision_contract=decision_contract,
            max_new_tokens=kwargs.pop("max_new_tokens", 8),
            **kwargs,
        )

    @property
    def last_selected_rule_ids(self) -> list[str]:
        return list(self._last_selected_rule_ids)

    def prepare_messages(
        self, *, policy: Policy, context: TaskContext
    ) -> list[ChatMessage]:
        system = self.system_prompt.strip()
        if self.decision_contract:
            system = f"{system}\n\n{self.decision_contract.strip()}"

        self._last_selected_rule_ids = []
        user = context.query.strip()

        if self.policy_placement == "system_json":
            policy_block = json.dumps(
                policy.model_dump(mode="json"), indent=2, sort_keys=True
            )
            system = (
                f"{system}\n\n"
                f"# Policy ({policy.policy_id}@{policy.version})\n"
                f"{policy_block}"
            )
        elif self.policy_placement == "user_json":
            policy_block = json.dumps(
                policy.model_dump(mode="json"), indent=2, sort_keys=True
            )
            user = (
                "# Company Policies\n"
                "```json\n"
                f"{policy_block}\n"
                "```\n\n"
                "# User Query\n"
                f"{context.query.strip()}"
            )
        elif self.policy_placement == "retrieved":
            selected = self.selector.select(
                policy=policy, context=context, top_k=self.top_k
            )
            self._last_selected_rule_ids = [rule.rule_id for rule in selected]
            rendered = self.renderer.render(selected, policy_label=self.policy_label)
            system = f"{system}\n\n{rendered}"

        if self.few_shot:
            messages: list[ChatMessage] = [
                ChatMessage(
                    role="system",
                    content=f"{system}\n\n{self.few_shot_intro.strip()}",
                )
            ]
            for demo_user, demo_assistant in self.few_shot:
                messages.append(ChatMessage(role="user", content=demo_user.strip()))
                messages.append(
                    ChatMessage(role="assistant", content=demo_assistant.strip())
                )
            messages.append(ChatMessage(role="user", content=user))
            return messages

        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def run(self, *, policy: Policy, context: TaskContext) -> ExecutionResult:
        if self.run_recognition:
            match = self.recognizer.recognize(policy=policy, context=context)
            decision = decide(policy=policy, match=match)
        else:
            match = PolicyMatch(applicable=[], confidence=1.0, rationale="skipped")
            decision = decide(policy=policy, match=match)

        messages = self.prepare_messages(policy=policy, context=context)
        output = self.backend.generate(messages, max_new_tokens=self.max_new_tokens)
        return ExecutionResult(
            example_id=context.example_id,
            method_id=self.method_id,
            match=match,
            decision=decision,
            messages=messages,
            output_text=output,
            n_generated=len(output.split()),
            hit_max_new_tokens=False,
            stopped_on_valid_terminal=True,
            metadata={
                "backend_id": getattr(self.backend, "backend_id", "unknown"),
                "expected_disposition": context.expected_disposition,
                "policy_placement": self.policy_placement,
                "selected_rule_ids": list(self._last_selected_rule_ids),
            },
        )
