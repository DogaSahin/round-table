from __future__ import annotations

from app.engine.encounter import advance_turn, clamp_hp, hp_band


def test_advance_turn_from_no_active_starts_at_first() -> None:
    active, rnd = advance_turn(None, [3, 1, 2], current_round=1)
    assert (active, rnd) == (3, 1)


def test_advance_turn_stale_active_restarts_at_first() -> None:
    # active_id no longer in the ordered list (e.g. that combatant was removed)
    active, rnd = advance_turn(99, [3, 1, 2], current_round=2)
    assert (active, rnd) == (3, 2)


def test_advance_turn_moves_to_next() -> None:
    active, rnd = advance_turn(3, [3, 1, 2], current_round=1)
    assert (active, rnd) == (1, 1)


def test_advance_turn_wraps_and_increments_round() -> None:
    active, rnd = advance_turn(2, [3, 1, 2], current_round=1)
    assert (active, rnd) == (3, 2)


def test_advance_turn_empty_list_is_noop() -> None:
    active, rnd = advance_turn(5, [], current_round=4)
    assert (active, rnd) == (None, 4)


def test_hp_band_thresholds() -> None:
    assert hp_band(10, 40) == "low"  # 25%
    assert hp_band(11, 40) == "mid"
    assert hp_band(20, 40) == "mid"  # 50%
    assert hp_band(21, 40) == "high"
    assert hp_band(40, 40) == "high"


def test_hp_band_zero_max_is_low() -> None:
    assert hp_band(0, 0) == "low"


def test_clamp_hp_within_bounds() -> None:
    assert clamp_hp(5, 10) == 5


def test_clamp_hp_over_max_clamps_down() -> None:
    assert clamp_hp(15, 10) == 10


def test_clamp_hp_negative_clamps_to_zero() -> None:
    assert clamp_hp(-3, 10) == 0


def test_clamp_hp_no_max_floors_at_zero_only() -> None:
    assert clamp_hp(-3, None) == 0
    assert clamp_hp(500, None) == 500
    assert clamp_hp(500, 0) == 500
