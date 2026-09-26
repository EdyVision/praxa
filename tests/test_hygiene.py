"""Generation hygiene helpers."""

from __future__ import annotations

from praxa.evaluation.metrics.hygiene import clean_stop, hygiene_report


def test_clean_stop() -> None:
    assert clean_stop(hit_max_new_tokens=False, stopped_on_valid_terminal=True) is True
    assert clean_stop(hit_max_new_tokens=True, stopped_on_valid_terminal=True) is False
    report = hygiene_report(
        n_generated=12,
        hit_max_new_tokens=False,
        stopped_on_valid_terminal=True,
        output_text="ok <|im_end|>",
        contamination_markers=["<|im_end|>"],
    )
    assert report["clean_stop"] is True
    assert report["contaminated"] is True
    assert report["contamination_hits"] == ["<|im_end|>"]
