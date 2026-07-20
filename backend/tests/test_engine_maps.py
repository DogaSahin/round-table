from __future__ import annotations

import pytest

from app.engine.maps import (
    path_distance,
    reduce_fog_ops,
    segment_distance,
    snap_to_grid,
    token_is_player_visible,
)

# =============================================================================
# snap_to_grid tests
# =============================================================================


def test_snap_to_grid_on_grid_unchanged():
    """A point already on-grid stays put."""
    assert snap_to_grid(70, 140, 70, 0, 0) == (70, 140)


def test_snap_to_grid_snaps_to_nearest_intersection():
    """Points snap to the nearest cell in each direction."""
    # size 70, no offset: 100 -> 70 (nearest of 0/70/140), 120 -> 140
    assert snap_to_grid(100, 120, 70, 0, 0) == (70, 140)


def test_snap_to_grid_offset_respected():
    """Non-zero offset_x/offset_y shifts the grid origin correctly."""
    # offset 10: intersections at 10, 80, 150 ...; 95 -> 80, 130 -> 150
    assert snap_to_grid(95, 130, 70, 10, 10) == (80, 150)


def test_snap_to_grid_half_cell_rounds_up():
    """Exact half-cell input rounds UP (matching JS Math.round, not Python banker's round)."""
    # Exact half-cell input: (35-0)/70 = 0.5. JS Math.round(0.5) == 1 -> 70.
    # Python's banker's round(0.5) would give 0; half-up must match the JS mirror.
    assert snap_to_grid(35, 105, 70, 0, 0) == (70, 140)


def test_snap_to_grid_zero_size_returns_input():
    """size <= 0 disables snapping and returns input unchanged."""
    assert snap_to_grid(33, 44, 0, 0, 0) == (33, 44)
    assert snap_to_grid(100, 200, -5, 0, 0) == (100, 200)


# =============================================================================
# segment_distance tests
# =============================================================================


@pytest.mark.parametrize(
    "dx,dy,rule,expected",
    [
        (3, 0, "chebyshev", 15),
        (3, 3, "chebyshev", 15),  # max(3,3)*5
        (4, 2, "chebyshev", 20),  # max*5
        (4, 2, "five_ten_five", 25),  # (4 + 2//2)*5 = (4+1)*5
        (3, 3, "five_ten_five", 20),  # (3 + 1)*5
        (3, 4, "euclidean", 25),  # round(5)*5
        (2, 2, "euclidean", 15),  # round(2.828)*5 = 3*5 = 15
        (3, 2, "manhattan", 25),  # (3+2)*5
    ],
)
def test_segment_distance_rules(dx, dy, rule, expected):
    """All four diagonal_rule values work correctly."""
    assert segment_distance(dx, dy, 5, rule) == expected


def test_segment_distance_negative_deltas():
    """Negative deltas are absorbed by abs(); results match positive equivalents."""
    # euclidean: (-3, 4) → abs: (3, 4) → sqrt(9+16)=5 → round(5)=5 → 5*5=25
    assert segment_distance(-3, 4, 5, "euclidean") == 25
    # chebyshev: (-4, -2) → abs: (4, 2) → max(4,2)=4 → 4*5=20
    assert segment_distance(-4, -2, 5, "chebyshev") == 20
    # five_ten_five: (-4, 2) → abs: (4, 2) → (4+2//2)*5=(4+1)*5=25
    assert segment_distance(-4, 2, 5, "five_ten_five") == 25
    # manhattan: (3, -2) → abs: (3, 2) → (3+2)*5=25
    assert segment_distance(3, -2, 5, "manhattan") == 25


def test_segment_distance_diagonal_chebyshev():
    """Pure diagonal case: chebyshev treats diagonal as same as horizontal/vertical."""
    assert segment_distance(5, 5, 10, "chebyshev") == 50


def test_segment_distance_straight_manhattan():
    """Straight line case: manhattan sums the components."""
    assert segment_distance(0, 7, 10, "manhattan") == 70


def test_segment_distance_unknown_rule_defaults_to_chebyshev():
    """Unknown rule string falls back to chebyshev (hi * feet)."""
    assert segment_distance(3, 2, 5, "unknown") == 15


# =============================================================================
# path_distance tests
# =============================================================================


def test_path_distance_with_chebyshev():
    """Multi-waypoint path sums correctly across the rule type."""
    # pixels in px on a 70px grid: (0,0)->(140,0)->(140,140) = 2 + 2 squares.
    # chebyshev: 2*5 + 2*5 = 20
    pts = [(0, 0), (140, 0), (140, 140)]
    assert path_distance(pts, 5, "chebyshev", 70) == 20


def test_path_distance_empty_points():
    """Empty path returns 0."""
    assert path_distance([], 5, "chebyshev", 70) == 0


def test_path_distance_single_point():
    """Single-point path returns 0."""
    assert path_distance([(0, 0)], 5, "chebyshev", 70) == 0


def test_path_distance_invalid_grid_size():
    """grid_size <= 0 returns 0."""
    pts = [(0, 0), (100, 100)]
    assert path_distance(pts, 5, "chebyshev", 0) == 0
    assert path_distance(pts, 5, "chebyshev", -10) == 0


def test_path_distance_multiple_segments():
    """Multiple segments: each leg is summed independently."""
    # 70px grid: (0,0)->(70,0) = 1 sq, (70,0)->(140,70) = 1 sq + 1 sq = chebyshev max = 1 sq
    # chebyshev(1, 0, feet=5) = 1*5 = 5
    # chebyshev(1, 1, feet=5) = 1*5 = 5
    # total = 5 + 5 = 10
    pts = [(0, 0), (70, 0), (140, 70)]
    assert path_distance(pts, 5, "chebyshev", 70) == 10


def test_path_distance_backward_leg():
    """Negative deltas in path legs (x or y decreasing) are handled by abs()."""
    # 70px grid, chebyshev, feet=5
    # leg1: (140,0) to (0,0) → dx=abs(0-140)=140, dy=abs(0-0)=0 → 140//70=2 squares → 2*5=10 ft
    # leg2: (0,0) to (0,70) → dx=abs(0-0)=0, dy=abs(70-0)=70 → 70//70=1 square → 1*5=5 ft
    # total = 10 + 5 = 15
    pts = [(140, 0), (0, 0), (0, 70)]
    assert path_distance(pts, 5, "chebyshev", 70) == 15


def test_path_distance_multiple_rules():
    """Path distance works correctly with different diagonal rules."""
    pts = [(0, 0), (100, 100)]
    # dx_sq = dy_sq = round(100/70) = round(1.42857) = 1 square each way
    # chebyshev: max(1, 1) * 5 = 5
    # euclidean: round(sqrt(1^2 + 1^2)) * 5 = round(1.414) * 5 = 1 * 5 = 5
    # manhattan: (1 + 1) * 5 = 10
    assert path_distance(pts, 5, "chebyshev", 70) == 5
    assert path_distance(pts, 5, "euclidean", 70) == 5
    assert path_distance(pts, 5, "manhattan", 70) == 10


# =============================================================================
# reduce_fog_ops tests
# =============================================================================


def _rect(x, y, w, h):
    """Helper to create a rect geometry object."""
    return {"type": "rect", "x": x, "y": y, "w": w, "h": h}


def test_reduce_fog_ops_empty_list():
    """Empty list returns empty."""
    assert reduce_fog_ops([]) == []


def test_reduce_fog_ops_reveal_then_hide():
    """A reveal-then-hide sequence of rects keeps both entries in order."""
    ops = [
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
        {"op": "hide", "geom": _rect(10, 10, 20, 20)},
    ]
    assert reduce_fog_ops(ops) == ops


def test_reduce_fog_ops_reveal_all_collapses():
    """A {"type": "all"} reveal collapses everything before it into one reveal-all entry."""
    ops = [
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
        {"op": "hide", "geom": _rect(0, 0, 35, 35)},
        {"op": "reveal", "geom": {"type": "all"}},
    ]
    out = reduce_fog_ops(ops)
    assert out == [{"op": "reveal", "geom": {"type": "all"}}]


def test_reduce_fog_ops_hide_all_empties():
    """A {"type": "all"} hide empties the whole list."""
    ops = [
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
        {"op": "hide", "geom": {"type": "all"}},
    ]
    assert reduce_fog_ops(ops) == []


def test_reduce_fog_ops_reveal_after_hide_all():
    """DM hides everything, then reveals one room — the reveal must survive."""
    ops = [
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
        {"op": "hide", "geom": {"type": "all"}},
        {"op": "reveal", "geom": _rect(140, 140, 70, 70)},
    ]
    assert reduce_fog_ops(ops) == [{"op": "reveal", "geom": _rect(140, 140, 70, 70)}]


def test_reduce_fog_ops_hide_after_reveal_all():
    """DM reveals the whole map, then re-hides one room — the hide must survive."""
    ops = [
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
        {"op": "reveal", "geom": {"type": "all"}},
        {"op": "hide", "geom": _rect(210, 0, 70, 70)},
    ]
    assert reduce_fog_ops(ops) == [
        {"op": "reveal", "geom": {"type": "all"}},
        {"op": "hide", "geom": _rect(210, 0, 70, 70)},
    ]


def test_reduce_fog_ops_malformed_non_dict_geom_skipped():
    """An entry with a non-dict geom (e.g. None, int, str) is skipped defensively, not raised."""
    ops = [
        {"op": "reveal", "geom": 5},
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
    ]
    assert reduce_fog_ops(ops) == [{"op": "reveal", "geom": _rect(0, 0, 70, 70)}]


def test_reduce_fog_ops_malformed_non_dict_geom_various_types():
    """Non-dict geom can be None, string, list, or any non-dict — all skipped."""
    ops = [
        {"op": "reveal", "geom": None},
        {"op": "reveal", "geom": "invalid"},
        {"op": "reveal", "geom": [1, 2, 3]},
        {"op": "reveal", "geom": _rect(0, 0, 70, 70)},
    ]
    assert reduce_fog_ops(ops) == [{"op": "reveal", "geom": _rect(0, 0, 70, 70)}]


# =============================================================================
# token_is_player_visible tests
# =============================================================================


def test_token_is_player_visible_both_true():
    """Token is player-visible only when both visible_to_players=True AND layer='tokens'."""
    assert token_is_player_visible(True, "tokens") is True


def test_token_is_player_visible_false_visibility():
    """visible_to_players=False excludes token from player view."""
    assert token_is_player_visible(False, "tokens") is False


def test_token_is_player_visible_dm_layer():
    """layer='dm' excludes token from player view even if visible_to_players=True."""
    assert token_is_player_visible(True, "dm") is False


def test_token_is_player_visible_both_false():
    """Both false: not visible."""
    assert token_is_player_visible(False, "dm") is False
