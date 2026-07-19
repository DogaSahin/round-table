// frontend/src/modules/dice/api.ts
import { apiFetch } from '@/api/client'

export interface RollTerm {
  source: string
  sign: number
  is_dice: boolean
  total: number
  kept: number[]
  discarded: number[]
  flat: number | null
}

export interface RollResult {
  expression: string
  total: number
  terms: RollTerm[]
}

export interface HistoryEntry {
  id: number
  expression: string
  result: number
  rolled_at: string
}

export function rollDice(expression: string): Promise<RollResult> {
  return apiFetch<RollResult>('/api/dice/roll', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ expression }),
  })
}

export function fetchHistory(): Promise<HistoryEntry[]> {
  return apiFetch<HistoryEntry[]>('/api/dice/history')
}
