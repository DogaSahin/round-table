// frontend/src/modules/combat/api.ts
import { apiFetch } from '@/api/client'

export interface Combatant {
  id: number
  name: string
  initiative: number
  hp_current: number
  hp_max: number
  ac: number | null
  conditions: string[]
  concentration: boolean
  sort_order: number
  is_pc: boolean
  visible_to_players: boolean
  npc_id: number | null
  token_id: number | null
}

export interface EncounterListItem {
  id: number
  name: string
  round: number
  is_active: boolean
}

export interface EncounterDetail {
  id: number
  name: string
  round: number
  active_combatant_id: number | null
  is_active: boolean
  combatants: Combatant[]
}

export interface CombatantCreatePayload {
  name: string
  initiative: number
  hp_current: number
  hp_max: number
  ac: number | null
  is_pc: boolean
  visible_to_players: boolean
  npc_id: number | null
}

export interface CombatantPatch {
  name?: string
  initiative?: number
  is_pc?: boolean
  visible_to_players?: boolean
  npc_id?: number | null
}

export function listEncounters(): Promise<EncounterListItem[]> {
  return apiFetch<EncounterListItem[]>('/api/combat')
}

export function createEncounter(name: string): Promise<EncounterDetail> {
  return apiFetch<EncounterDetail>('/api/combat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export function fetchEncounter(encounterId: number): Promise<EncounterDetail> {
  return apiFetch<EncounterDetail>(`/api/combat/${encounterId}`)
}

export function renameEncounter(encounterId: number, name: string): Promise<EncounterDetail> {
  return apiFetch<EncounterDetail>(`/api/combat/${encounterId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export function deleteEncounter(encounterId: number): Promise<void> {
  return apiFetch<void>(`/api/combat/${encounterId}`, { method: 'DELETE' })
}

export function activateEncounter(encounterId: number): Promise<EncounterDetail> {
  return apiFetch<EncounterDetail>(`/api/combat/${encounterId}/activate`, { method: 'POST' })
}

export function sortByInitiative(encounterId: number): Promise<EncounterDetail> {
  return apiFetch<EncounterDetail>(`/api/combat/${encounterId}/sort`, { method: 'POST' })
}

export function reorder(encounterId: number, order: number[]): Promise<EncounterDetail> {
  return apiFetch<EncounterDetail>(`/api/combat/${encounterId}/reorder`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ order }),
  })
}

export function nextTurn(encounterId: number): Promise<EncounterDetail> {
  return apiFetch<EncounterDetail>(`/api/combat/${encounterId}/next-turn`, { method: 'POST' })
}

export function addCombatant(
  encounterId: number,
  payload: CombatantCreatePayload,
): Promise<Combatant> {
  return apiFetch<Combatant>(`/api/combat/${encounterId}/combatants`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function updateCombatant(combatantId: number, patch: CombatantPatch): Promise<Combatant> {
  return apiFetch<Combatant>(`/api/combat/combatants/${combatantId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
}

export function deleteCombatant(combatantId: number): Promise<void> {
  return apiFetch<void>(`/api/combat/combatants/${combatantId}`, { method: 'DELETE' })
}

export function damageCombatant(combatantId: number, amount: number): Promise<Combatant> {
  return apiFetch<Combatant>(`/api/combat/combatants/${combatantId}/damage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount }),
  })
}

export function healCombatant(combatantId: number, amount: number): Promise<Combatant> {
  return apiFetch<Combatant>(`/api/combat/combatants/${combatantId}/heal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount }),
  })
}

export function setAc(combatantId: number, ac: number | null): Promise<Combatant> {
  return apiFetch<Combatant>(`/api/combat/combatants/${combatantId}/ac`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ac }),
  })
}

export function applyCondition(
  combatantId: number,
  name: string,
  op: 'add' | 'remove',
): Promise<Combatant> {
  return apiFetch<Combatant>(`/api/combat/combatants/${combatantId}/condition`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, op }),
  })
}

export function toggleConcentration(combatantId: number): Promise<Combatant> {
  return apiFetch<Combatant>(`/api/combat/combatants/${combatantId}/concentration`, {
    method: 'POST',
  })
}
