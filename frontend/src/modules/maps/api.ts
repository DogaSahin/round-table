// frontend/src/modules/maps/api.ts
import { apiFetch } from '@/api/client'

export type DiagonalRule = 'chebyshev' | 'five_ten_five' | 'euclidean' | 'manhattan'
export type TokenLayer = 'tokens' | 'dm'
export type TokenKind = 'disc' | 'image'
export type FogOp = 'reveal' | 'hide'

export interface TokenOut {
  id: number
  layer: TokenLayer
  kind: TokenKind
  x: number
  y: number
  size_squares: number
  color: string
  image_path: string | null
  name: string
  hp_current: number | null
  hp_max: number | null
  hp_visible_to_players: boolean
  visible_to_players: boolean
  status_markers: string[]
  is_pc: boolean
  npc_id: number | null
  combatant_id: number | null
}

export interface FogRegionOut {
  id: number
  order_index: number
  kind: FogOp
  geom: Record<string, unknown>
}

export interface MapListItemOut {
  id: number
  name: string
  is_active: boolean
}

export interface MapDetailOut {
  id: number
  name: string
  image_path: string | null
  image_w: number | null
  image_h: number | null
  grid_size_px: number
  grid_offset_x: number
  grid_offset_y: number
  grid_visible: boolean
  feet_per_square: number
  diagonal_rule: DiagonalRule
  is_active: boolean
  tokens: TokenOut[]
  fog: FogRegionOut[]
}

export interface MapUpdatePatch {
  name?: string
  grid_size_px?: number
  grid_offset_x?: number
  grid_offset_y?: number
  grid_visible?: boolean
  feet_per_square?: number
  diagonal_rule?: DiagonalRule
}

export interface TokenCreatePayload {
  name?: string
  layer?: TokenLayer
  kind?: TokenKind
  size_squares?: number
  color?: string
  is_pc?: boolean
  visible_to_players?: boolean
  npc_id?: number | null
  combatant_id?: number | null
}

export interface TokenUpdatePatch {
  name?: string
  layer?: TokenLayer
  size_squares?: number
  color?: string
  is_pc?: boolean
  visible_to_players?: boolean
  npc_id?: number | null
  combatant_id?: number | null
  hp_current?: number | null
  hp_max?: number | null
  hp_visible_to_players?: boolean
  status_markers?: string[]
}

/** Uploaded map/token images are stored with a media_dir-relative path (e.g.
 * "maps/abc123.png") and served by the backend's StaticFiles mount at "/media". */
export function mediaUrl(imagePath: string): string {
  return `/media/${imagePath}`
}

export function listMaps(): Promise<MapListItemOut[]> {
  return apiFetch<MapListItemOut[]>('/api/maps')
}

export function createMap(name: string): Promise<MapDetailOut> {
  return apiFetch<MapDetailOut>('/api/maps', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export function fetchMap(mapId: number): Promise<MapDetailOut> {
  return apiFetch<MapDetailOut>(`/api/maps/${mapId}`)
}

export function updateMap(mapId: number, patch: MapUpdatePatch): Promise<MapDetailOut> {
  return apiFetch<MapDetailOut>(`/api/maps/${mapId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
}

export function deleteMap(mapId: number): Promise<void> {
  return apiFetch<void>(`/api/maps/${mapId}`, { method: 'DELETE' })
}

export function activateMap(mapId: number): Promise<MapDetailOut> {
  return apiFetch<MapDetailOut>(`/api/maps/${mapId}/activate`, { method: 'POST' })
}

export function stopSharing(): Promise<void> {
  return apiFetch<void>('/api/maps/stop-sharing', { method: 'POST' })
}

export function uploadMapImage(mapId: number, file: File): Promise<MapDetailOut> {
  const form = new FormData()
  form.append('upload', file)
  // Do not set Content-Type here: the browser must set it (with the
  // multipart boundary) itself. apiFetch just forwards `init` to fetch and
  // parses the (perfectly normal JSON) response, so it needs no changes to
  // support a FormData request body.
  return apiFetch<MapDetailOut>(`/api/maps/${mapId}/image`, {
    method: 'POST',
    body: form,
  })
}

export function addToken(mapId: number, payload: TokenCreatePayload): Promise<TokenOut> {
  return apiFetch<TokenOut>(`/api/maps/${mapId}/tokens`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function updateToken(tokenId: number, patch: TokenUpdatePatch): Promise<TokenOut> {
  return apiFetch<TokenOut>(`/api/maps/tokens/${tokenId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
}

export function deleteToken(tokenId: number): Promise<void> {
  return apiFetch<void>(`/api/maps/tokens/${tokenId}`, { method: 'DELETE' })
}

export function uploadTokenImage(tokenId: number, file: File): Promise<TokenOut> {
  const form = new FormData()
  form.append('upload', file)
  return apiFetch<TokenOut>(`/api/maps/tokens/${tokenId}/image`, {
    method: 'POST',
    body: form,
  })
}

export function moveToken(tokenId: number, x: number, y: number, snap: boolean): Promise<TokenOut> {
  return apiFetch<TokenOut>(`/api/maps/tokens/${tokenId}/move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ x, y, snap }),
  })
}

export function addFogOp(
  mapId: number,
  op: FogOp,
  geom: Record<string, unknown>,
): Promise<MapDetailOut> {
  return apiFetch<MapDetailOut>(`/api/maps/${mapId}/fog`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ op, geom }),
  })
}

export function fogRevealAll(mapId: number): Promise<MapDetailOut> {
  return apiFetch<MapDetailOut>(`/api/maps/${mapId}/fog/reveal-all`, { method: 'POST' })
}

export function fogHideAll(mapId: number): Promise<MapDetailOut> {
  return apiFetch<MapDetailOut>(`/api/maps/${mapId}/fog/hide-all`, { method: 'POST' })
}
