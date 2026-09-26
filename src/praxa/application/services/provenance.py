"""Run provenance manifests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from praxa._version import __version__ as PRAXA_VERSION
from praxa.domain.hashing import hash_payload
from praxa.domain.policy import Policy


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    created_at: str
    praxa_version: str
    policy_id: str
    policy_version: str
    policy_hash: str
    dataset_id: str
    method_ids: list[str] = Field(default_factory=list)
    seed: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def content_hash(self) -> str:
        return hash_payload(self.model_dump(mode="json"))


def build_run_manifest(
    *,
    run_id: str,
    policy: Policy,
    dataset_id: str,
    method_ids: list[str],
    seed: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        created_at=datetime.now(UTC).isoformat(),
        praxa_version=PRAXA_VERSION,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        policy_hash=policy.content_hash(),
        dataset_id=dataset_id,
        method_ids=list(method_ids),
        seed=seed,
        metadata=dict(metadata or {}),
    )
