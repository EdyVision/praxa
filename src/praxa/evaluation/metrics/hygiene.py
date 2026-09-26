"""Generation hygiene metrics (pure functions)."""

from __future__ import annotations

from collections.abc import Sequence


def clean_stop(*, hit_max_new_tokens: bool, stopped_on_valid_terminal: bool) -> bool:
    return bool(stopped_on_valid_terminal and not hit_max_new_tokens)


def contamination_hits(
    text: str,
    *,
    markers: Sequence[str],
) -> list[str]:
    """Return configured contamination markers found in ``text`` (case-sensitive)."""
    return [marker for marker in markers if marker and marker in text]


def hygiene_report(
    *,
    n_generated: int | None,
    hit_max_new_tokens: bool | None,
    stopped_on_valid_terminal: bool | None,
    output_text: str | None = None,
    contamination_markers: Sequence[str] | None = None,
) -> dict[str, bool | int | None | list[str]]:
    hit = bool(hit_max_new_tokens) if hit_max_new_tokens is not None else None
    term = (
        bool(stopped_on_valid_terminal)
        if stopped_on_valid_terminal is not None
        else None
    )
    markers = list(contamination_markers or ())
    hits = contamination_hits(output_text or "", markers=markers) if markers else []
    return {
        "n_generated": n_generated,
        "hit_max_new_tokens": hit,
        "stopped_on_valid_terminal": term,
        "clean_stop": (
            clean_stop(
                hit_max_new_tokens=bool(hit), stopped_on_valid_terminal=bool(term)
            )
            if hit is not None and term is not None
            else None
        ),
        "contamination_hits": hits,
        "contaminated": bool(hits) if markers else None,
    }
