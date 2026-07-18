from __future__ import annotations

from app.engine.distance import path_distance, segment_distance, snap_to_grid


def test_chebyshev_diagonal_counts_as_one_square() -> None:
    assert segment_distance(3, 3, 5, "chebyshev") == 15


def test_five_ten_five_alternates() -> None:
    assert segment_distance(2, 1, 5, "five_ten_five") == 10


def test_euclidean_rounds() -> None:
    assert segment_distance(3, 4, 5, "euclidean") == 25


def test_manhattan_sums_axes() -> None:
    assert segment_distance(3, 4, 5, "manhattan") == 35


def test_unknown_rule_defaults_to_chebyshev() -> None:
    assert segment_distance(2, 5, 5, "bogus") == segment_distance(2, 5, 5, "chebyshev")


def test_path_distance_sums_segments() -> None:
    points = [(0, 0), (70, 0), (70, 70)]
    assert path_distance(points, feet=5, rule="chebyshev", grid_size=70) == 10


def test_path_distance_zero_grid_size_is_zero() -> None:
    assert path_distance([(0, 0), (70, 0)], feet=5, rule="chebyshev", grid_size=0) == 0


def test_snap_to_grid_half_up_parity() -> None:
    # x=35 is exactly half a 70px cell — must floor(v+0.5), matching the
    # client-side snap.js twin bit-for-bit (not Python's banker's round()).
    assert snap_to_grid(35, 0, 70, 0, 0) == (70, 0)


def test_snap_to_grid_disabled_when_size_non_positive() -> None:
    assert snap_to_grid(13, 27, 0, 0, 0) == (13, 27)


def test_snap_to_grid_respects_offset() -> None:
    assert snap_to_grid(15, 15, 10, 5, 5) == (15, 15)
