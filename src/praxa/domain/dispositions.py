"""Disposition vocabulary for policy decisions."""

from __future__ import annotations

from enum import StrEnum


class Disposition(StrEnum):
    """Canonical dispositions; policies may also emit custom strings via Decision."""

    ALLOW = "allow"
    DENY = "deny"
    RESTRICT = "restrict"
    REDIRECT = "redirect"
    CUSTOM = "custom"
