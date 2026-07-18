from __future__ import annotations


def toggle_fill(current_filled: int, segment_clicked: int, total_segments: int) -> int:
    """Progress-clock segment click behavior: clicking 0-based segment index
    `i` fills the clock through segment `i+1`. Clicking the segment that is
    currently the top filled one toggles it back off instead. Result is
    clamped to [0, total_segments]."""
    target = segment_clicked + 1
    new_filled = segment_clicked if current_filled == target else target
    return max(0, min(new_filled, total_segments))
