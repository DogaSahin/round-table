from __future__ import annotations

from app.engine.clocks import toggle_fill


def test_click_fills_up_to_clicked_segment() -> None:
    # 6-segment clock, currently 2 filled, click segment index 3 (0-based)
    # -> fills through segment 4
    assert toggle_fill(current_filled=2, segment_clicked=3, total_segments=6) == 4


def test_clicking_current_top_segment_toggles_off() -> None:
    # 6-segment clock, 4 filled, click index 3 again (the current top) -> unfills to 3
    assert toggle_fill(current_filled=4, segment_clicked=3, total_segments=6) == 3


def test_click_beyond_segments_clamps_to_total() -> None:
    assert toggle_fill(current_filled=0, segment_clicked=10, total_segments=6) == 6


def test_click_first_segment_from_empty() -> None:
    assert toggle_fill(current_filled=0, segment_clicked=0, total_segments=6) == 1


def test_result_never_negative() -> None:
    assert toggle_fill(current_filled=0, segment_clicked=0, total_segments=6) >= 0
