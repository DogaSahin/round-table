from __future__ import annotations

import math


def segment_distance(dx: int, dy: int, feet: int, rule: str) -> int:
    """Distance in feet for a move of |dx|,|dy| squares under the given diagonal rule."""
    dx, dy = abs(dx), abs(dy)
    hi, lo = max(dx, dy), min(dx, dy)
    if rule == "chebyshev":
        return hi * feet
    if rule == "five_ten_five":
        return (hi + lo // 2) * feet
    if rule == "euclidean":
        return round(math.sqrt(dx * dx + dy * dy)) * feet
    if rule == "manhattan":
        return (dx + dy) * feet
    return hi * feet  # default to chebyshev


def path_distance(points: list[tuple[int, int]], feet: int, rule: str, grid_size: int) -> int:
    """Sum of segment distances along a polyline of pixel points."""
    if grid_size <= 0 or len(points) < 2:
        return 0
    total = 0
    for (x0, y0), (x1, y1) in zip(points, points[1:], strict=False):
        dx = round(abs(x1 - x0) / grid_size)
        dy = round(abs(y1 - y0) / grid_size)
        total += segment_distance(dx, dy, feet, rule)
    return total


def snap_to_grid(x: int, y: int, size: int, off_x: int, off_y: int) -> tuple[int, int]:
    """Nearest grid intersection. size<=0 => snapping disabled (return input).

    Uses half-up rounding (floor(v + 0.5)) rather than Python's banker's
    round() so the result is byte-for-byte identical to the client-side
    snap.js twin — the coordinate the DM sees snapped locally must be the
    coordinate the server persists.
    """
    if size <= 0:
        return x, y
    sx = math.floor((x - off_x) / size + 0.5) * size + off_x
    sy = math.floor((y - off_y) / size + 0.5) * size + off_y
    return int(sx), int(sy)
