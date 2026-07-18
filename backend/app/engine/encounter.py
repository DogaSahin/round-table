from __future__ import annotations


def advance_turn(
    active_id: int | None, ordered_ids: list[int], current_round: int
) -> tuple[int | None, int]:
    """Next-turn engine. None/stale active -> first (round unchanged, starts
    combat); wrapping past the last -> first + round++. Empty -> (None, round)."""
    if not ordered_ids:
        return None, current_round
    if active_id not in ordered_ids:
        return ordered_ids[0], current_round
    idx = ordered_ids.index(active_id)
    if idx + 1 < len(ordered_ids):
        return ordered_ids[idx + 1], current_round
    return ordered_ids[0], current_round + 1


def hp_band(current: int, maximum: int) -> str:
    """Coarse health band for HP bars. On the player-facing surface this band
    is the ONLY HP signal shown (no numbers), so every consumer must agree
    on these thresholds."""
    ratio = (current / maximum) if maximum > 0 else 0
    if ratio <= 0.25:
        return "low"
    if ratio <= 0.5:
        return "mid"
    return "high"


def clamp_hp(current: int, maximum: int | None) -> int:
    """Clamp HP into [0, maximum]. No max (None or <=0) => floor at 0 only."""
    if maximum is None or maximum <= 0:
        return max(0, current)
    return max(0, min(current, maximum))
