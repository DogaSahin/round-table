// frontend/src/modules/maps/geometry.ts
//
// TypeScript port of backend/app/engine/maps.py's snap_to_grid, segment_distance,
// and path_distance. reduce_fog_ops is intentionally NOT ported: it only ever
// runs server-side (the map-detail endpoint already returns the reduced `fog`
// array; the client just renders it as-is).
import type { DiagonalRule } from './api'

/** Snap a point to the nearest grid intersection. size<=0 disables snapping.
 *
 * The Python source uses `math.floor((v - offset) / size + 0.5)` to get
 * round-half-up behavior (Python's builtin round() is banker's rounding, so
 * it can't be used directly). JS's Math.round() already rounds half-up for
 * all inputs, so it's a direct, non-divergent substitute here — not a
 * cross-language quirk to work around.
 */
export function snapToGrid(
  x: number,
  y: number,
  size: number,
  offsetX: number,
  offsetY: number,
): [number, number] {
  if (size <= 0) return [x, y]
  const sx = Math.round((x - offsetX) / size) * size + offsetX
  const sy = Math.round((y - offsetY) / size) * size + offsetY
  return [sx, sy]
}

/** Distance in feet for one straight segment, per a D&D diagonal-movement rule. */
export function segmentDistance(
  dxIn: number,
  dyIn: number,
  feetPerSquare: number,
  rule: DiagonalRule | string,
): number {
  const dx = Math.abs(dxIn)
  const dy = Math.abs(dyIn)
  const hi = Math.max(dx, dy)
  const lo = Math.min(dx, dy)
  if (rule === 'five_ten_five') {
    return (hi + Math.floor(lo / 2)) * feetPerSquare
  }
  if (rule === 'euclidean') {
    return Math.round(Math.sqrt(dx * dx + dy * dy)) * feetPerSquare
  }
  if (rule === 'manhattan') {
    return (dx + dy) * feetPerSquare
  }
  return hi * feetPerSquare // chebyshev, and the fallback for any unrecognized rule
}

/** Sum of segmentDistance across consecutive waypoints, converting pixel deltas to
 * grid squares first. */
export function pathDistance(
  points: Array<[number, number]>,
  feetPerSquare: number,
  rule: DiagonalRule | string,
  gridSizePx: number,
): number {
  if (points.length < 2 || gridSizePx <= 0) return 0
  let total = 0
  for (let i = 0; i < points.length - 1; i++) {
    const [x0, y0] = points[i]
    const [x1, y1] = points[i + 1]
    const dxSq = Math.round(Math.abs(x1 - x0) / gridSizePx)
    const dySq = Math.round(Math.abs(y1 - y0) / gridSizePx)
    total += segmentDistance(dxSq, dySq, feetPerSquare, rule)
  }
  return total
}
