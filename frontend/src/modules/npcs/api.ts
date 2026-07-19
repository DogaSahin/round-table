import { apiFetch } from '@/api/client'

export interface NpcListItem {
  id: number
  name: string
  disposition: string
  faction_id: number | null
}

export interface NpcDetail {
  id: number
  name: string
  disposition: string
  faction_id: number | null
  statblock: string | null
  motivation: string | null
  secrets: string | null
  voice: string | null
  portrait_path: string | null
  player_visible: boolean
}

export function listNpcs(): Promise<NpcListItem[]> {
  return apiFetch<NpcListItem[]>('/api/npcs')
}

export function createNpc(name: string): Promise<NpcDetail> {
  return apiFetch<NpcDetail>('/api/npcs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export function fetchNpc(npcId: number): Promise<NpcDetail> {
  return apiFetch<NpcDetail>(`/api/npcs/${npcId}`)
}

export function deleteNpc(npcId: number): Promise<void> {
  return apiFetch<void>(`/api/npcs/${npcId}`, { method: 'DELETE' })
}
