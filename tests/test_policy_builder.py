"""Unit tests for PolicyBuilder and policy validation."""

from __future__ import annotations

import pytest

from praxa import Disposition, PolicyBuilder
from praxa.domain.policy import Condition


def test_builder_round_trip_hash_stable() -> None:
    policy = (
        PolicyBuilder("demo.v1")
        .title("Demo")
        .domain("medical")
        .rule(
            "R1",
            disposition=Disposition.ALLOW,
            conditions=[Condition(kind="tag", value="ok")],
            required=["say_hi"],
        )
        .build()
    )
    assert policy.policy_id == "demo.v1"
    assert policy.content_hash() == policy.content_hash()
    assert len(policy.rules) == 1


def test_builder_rejects_required_prohibited_overlap() -> None:
    builder = PolicyBuilder("demo.v1").rule(
        "R1",
        required=["x"],
        prohibited=["x"],
        conditions=[Condition(kind="always", value="1")],
    )
    with pytest.raises(ValueError, match="overlap"):
        builder.build()


def test_empty_policy_rejected() -> None:
    with pytest.raises(ValueError, match="at least one rule"):
        PolicyBuilder("demo.v1").build()
