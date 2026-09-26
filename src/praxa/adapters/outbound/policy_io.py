"""YAML/JSON policy serialization."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from praxa.domain.policy import Policy


def policy_to_dict(policy: Policy) -> dict:
    return policy.model_dump(mode="json")


def policy_from_dict(payload: dict) -> Policy:
    return Policy.model_validate(payload)


def load_policy(path: str | Path) -> Policy:
    text = Path(path).read_text(encoding="utf-8")
    suffix = Path(path).suffix.lower()
    if suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(text)
    else:
        payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError(f"policy file must contain a mapping: {path}")
    return policy_from_dict(payload)


def dump_policy(policy: Policy, path: str | Path) -> None:
    target = Path(path)
    payload = policy_to_dict(policy)
    if target.suffix.lower() in {".yaml", ".yml"}:
        target.write_text(
            yaml.safe_dump(payload, sort_keys=True, allow_unicode=False),
            encoding="utf-8",
        )
        return
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
