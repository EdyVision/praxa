"""Tests for lossless COMPASS allowlist/denylist → Praxa import."""

from __future__ import annotations

from praxa.adapters.outbound.compass_import import (
    audit_compass_praxa_roundtrip,
    compass_to_praxa,
    praxa_to_compass,
)

MINI_COMPASS = {
    "allowlist": {
        "vitamins": "Staff may discuss over-the-counter vitamins.",
    },
    "denylist": {
        "diagnose": "Staff must not diagnose medical conditions.",
        "prescribe": "Staff must not prescribe medication.",
    },
}


def test_compass_roundtrip_1to1() -> None:
    policy = compass_to_praxa(
        MINI_COMPASS,
        policy_id="compass.mini.v1",
        domain="medical",
        company="MiniCo",
    )
    audit = audit_compass_praxa_roundtrip(MINI_COMPASS, policy)
    assert audit["ok"] is True
    assert audit["n_compass_topics"] == 3
    assert audit["n_praxa_rules"] == 3
    assert praxa_to_compass(policy) == {
        "allowlist": MINI_COMPASS["allowlist"],
        "denylist": MINI_COMPASS["denylist"],
    }
    assert policy.rules[0].metadata["clause_text"].startswith("Staff may")
