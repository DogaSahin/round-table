// frontend/src/modules/maps/geometry.test.ts
//
// A same-language port of backend/tests/test_engine_maps.py's cases for
// snapToGrid/segmentDistance/pathDistance, proving this TS port matches the
// Python source of truth (backend/app/engine/maps.py). reduceFogOps and
// tokenIsPlayerVisible are intentionally not ported here: the former only
// ever runs server-side (the client renders whatever `fog` array the
// map-detail endpoint returns as-is) and the latter is a server-only WS
// topic-gate predicate the client doesn't need (this DM-only view always
// connects to both the public and :dm topics).
import { describe, expect, it } from 'vitest'
import { pathDistance, segmentDistance, snapToGrid } from './geometry'

describe('snapToGrid', () => {
  it('leaves a point already on-grid unchanged', () => {
    expect(snapToGrid(70, 140, 70, 0, 0)).toEqual([70, 140])
  })

  it('snaps to the nearest intersection in each direction', () => {
    // size 70, no offset: 100 -> 70 (nearest of 0/70/140), 120 -> 140
    expect(snapToGrid(100, 120, 70, 0, 0)).toEqual([70, 140])
  })

  it('respects a non-zero offset', () => {
    // offset 10: intersections at 10, 80, 150 ...; 95 -> 80, 130 -> 150
    expect(snapToGrid(95, 130, 70, 10, 10)).toEqual([80, 150])
  })

  it('rounds an exact half-cell input up', () => {
    // Exact half-cell input: (35-0)/70 = 0.5. JS Math.round(0.5) == 1 -> 70.
    expect(snapToGrid(35, 105, 70, 0, 0)).toEqual([70, 140])
  })

  it('returns the input unchanged when size <= 0', () => {
    expect(snapToGrid(33, 44, 0, 0, 0)).toEqual([33, 44])
    expect(snapToGrid(100, 200, -5, 0, 0)).toEqual([100, 200])
  })
})

describe('segmentDistance', () => {
  it.each([
    [3, 0, 'chebyshev', 15],
    [3, 3, 'chebyshev', 15], // max(3,3)*5
    [4, 2, 'chebyshev', 20], // max*5
    [4, 2, 'five_ten_five', 25], // (4 + floor(2/2))*5 = (4+1)*5
    [3, 3, 'five_ten_five', 20], // (3 + 1)*5
    [3, 4, 'euclidean', 25], // round(5)*5
    [2, 2, 'euclidean', 15], // round(2.828)*5 = 3*5 = 15
    [3, 2, 'manhattan', 25], // (3+2)*5
  ] as const)('handles dx=%d dy=%d rule=%s', (dx, dy, rule, expected) => {
    expect(segmentDistance(dx, dy, 5, rule)).toBe(expected)
  })

  it('absorbs negative deltas via abs()', () => {
    expect(segmentDistance(-3, 4, 5, 'euclidean')).toBe(25)
    expect(segmentDistance(-4, -2, 5, 'chebyshev')).toBe(20)
    expect(segmentDistance(-4, 2, 5, 'five_ten_five')).toBe(25)
    expect(segmentDistance(3, -2, 5, 'manhattan')).toBe(25)
  })

  it('treats a pure diagonal the same as horizontal/vertical under chebyshev', () => {
    expect(segmentDistance(5, 5, 10, 'chebyshev')).toBe(50)
  })

  it('sums components under manhattan for a straight line', () => {
    expect(segmentDistance(0, 7, 10, 'manhattan')).toBe(70)
  })

  it('falls back to chebyshev for an unrecognized rule', () => {
    expect(segmentDistance(3, 2, 5, 'unknown')).toBe(15)
  })
})

describe('pathDistance', () => {
  it('sums a multi-waypoint path under chebyshev', () => {
    // pixels on a 70px grid: (0,0)->(140,0)->(140,140) = 2 + 2 squares.
    // chebyshev: 2*5 + 2*5 = 20
    const pts: Array<[number, number]> = [
      [0, 0],
      [140, 0],
      [140, 140],
    ]
    expect(pathDistance(pts, 5, 'chebyshev', 70)).toBe(20)
  })

  it('returns 0 for an empty path', () => {
    expect(pathDistance([], 5, 'chebyshev', 70)).toBe(0)
  })

  it('returns 0 for a single-point path', () => {
    expect(pathDistance([[0, 0]], 5, 'chebyshev', 70)).toBe(0)
  })

  it('returns 0 when grid_size_px <= 0', () => {
    const pts: Array<[number, number]> = [
      [0, 0],
      [100, 100],
    ]
    expect(pathDistance(pts, 5, 'chebyshev', 0)).toBe(0)
    expect(pathDistance(pts, 5, 'chebyshev', -10)).toBe(0)
  })

  it('sums each leg independently across multiple segments', () => {
    // 70px grid: (0,0)->(70,0) = 1 sq, (70,0)->(140,70) = 1 sq + 1 sq = chebyshev max = 1 sq
    // chebyshev(1, 0, feet=5) = 5, chebyshev(1, 1, feet=5) = 5, total = 10
    const pts: Array<[number, number]> = [
      [0, 0],
      [70, 0],
      [140, 70],
    ]
    expect(pathDistance(pts, 5, 'chebyshev', 70)).toBe(10)
  })

  it('handles a backward leg (decreasing x or y) via abs()', () => {
    const pts: Array<[number, number]> = [
      [140, 0],
      [0, 0],
      [0, 70],
    ]
    expect(pathDistance(pts, 5, 'chebyshev', 70)).toBe(15)
  })

  it('produces different totals under different diagonal rules', () => {
    const pts: Array<[number, number]> = [
      [0, 0],
      [100, 100],
    ]
    expect(pathDistance(pts, 5, 'chebyshev', 70)).toBe(5)
    expect(pathDistance(pts, 5, 'euclidean', 70)).toBe(5)
    expect(pathDistance(pts, 5, 'manhattan', 70)).toBe(10)
  })
})
