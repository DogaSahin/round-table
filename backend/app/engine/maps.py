from __future__ import annotations

import math

_DIAGONAL_RULES = ("chebyshev", "five_ten_five", "euclidean", "manhattan")


def snap_to_grid(x: int, y: int, size: int, offset_x: int, offset_y: int) -> tuple[int, int]:
    """Snap a point to the nearest grid intersection. size<=0 disables snapping."""
    if size <= 0:
        return x, y
    sx = math.floor((x - offset_x) / size + 0.5) * size + offset_x
    sy = math.floor((y - offset_y) / size + 0.5) * size + offset_y
    return int(sx), int(sy)


def segment_distance(dx: int, dy: int, feet_per_square: int, rule: str) -> int:
    """Distance in feet for one straight segment, per a D&D diagonal-movement rule."""
    dx, dy = abs(dx), abs(dy)
    hi, lo = max(dx, dy), min(dx, dy)
    if rule == "five_ten_five":
        return (hi + lo // 2) * feet_per_square
    if rule == "euclidean":
        return round(math.sqrt(dx * dx + dy * dy)) * feet_per_square
    if rule == "manhattan":
        return (dx + dy) * feet_per_square
    return hi * feet_per_square  # chebyshev, and the fallback for any unrecognized rule


def path_distance(
    points: list[tuple[int, int]], feet_per_square: int, rule: str, grid_size_px: int
) -> int:
    """Sum of segment_distance across consecutive waypoints, converting pixel deltas to
    grid squares first."""
    if len(points) < 2 or grid_size_px <= 0:
        return 0
    total = 0
    for (x0, y0), (x1, y1) in zip(points, points[1:], strict=False):
        dx_sq = round(abs(x1 - x0) / grid_size_px)
        dy_sq = round(abs(y1 - y0) / grid_size_px)
        total += segment_distance(dx_sq, dy_sq, feet_per_square, rule)
    return total


def reduce_fog_ops(ops: list[dict[str, object]]) -> list[dict[str, object]]:
    """Collapse an ordered reveal/hide op list. A type:'all' reveal replaces everything
    seen so far with a single reveal-all; a type:'all' hide empties the list. Entries
    with a malformed (non-dict) geom are skipped, never raised on."""
    result: list[dict[str, object]] = []
    for entry in ops:
        geom = entry.get("geom", {})
        if not isinstance(geom, dict):
            continue
        if geom.get("type") == "all":
            if entry.get("op") == "reveal":
                result = [{"op": "reveal", "geom": {"type": "all"}}]
            else:
                result = []
            continue
        result.append({"op": entry.get("op"), "geom": geom})
    return result


def token_is_player_visible(visible_to_players: bool, layer: str) -> bool:
    """The single predicate both the player-state HTTP projection and the WS topic-gate
    for token.move use — kept identical on purpose so the two surfaces can't drift."""
    return bool(visible_to_players) and layer == "tokens"
