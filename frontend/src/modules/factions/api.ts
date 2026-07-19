// frontend/src/modules/factions/api.ts
import { apiFetch } from '@/api/client'

export interface FactionClockEntry {
  id: number
  name: string
  segments: number
  filled: number
}

export interface FactionActivityEntry {
  id: number
  entry: string
  occurred_at: string
}

export interface FactionListItem {
  id: number
  name: string
  disposition: string
}

export interface FactionDetail {
  id: number
  name: string
  description: string | null
  disposition: string
  goals: string | null
  clocks: FactionClockEntry[]
  activity: FactionActivityEntry[]
}

export function listFactions(): Promise<FactionListItem[]> {
  return apiFetch<FactionListItem[]>('/api/factions')
}

export function createFaction(name: string): Promise<FactionDetail> {
  return apiFetch<FactionDetail>('/api/factions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export function fetchFaction(factionId: number): Promise<FactionDetail> {
  return apiFetch<FactionDetail>(`/api/factions/${factionId}`)
}

export function deleteFaction(factionId: number): Promise<void> {
  return apiFetch<void>(`/api/factions/${factionId}`, { method: 'DELETE' })
}

export function createClock(
  factionId: number,
  name: string,
  segments: number,
): Promise<FactionClockEntry> {
  return apiFetch<FactionClockEntry>(`/api/factions/${factionId}/clocks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, segments }),
  })
}

export function fillClock(clockId: number, segment: number): Promise<FactionClockEntry> {
  return apiFetch<FactionClockEntry>(`/api/factions/clocks/${clockId}/fill`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ segment }),
  })
}

export function addActivity(factionId: number, entry: string): Promise<FactionActivityEntry> {
  return apiFetch<FactionActivityEntry>(`/api/factions/${factionId}/activity`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ entry }),
  })
}
