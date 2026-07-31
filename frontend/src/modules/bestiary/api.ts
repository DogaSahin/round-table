// frontend/src/modules/bestiary/api.ts
import { apiFetch } from '@/api/client'

export type AbilityName =
  'strength' | 'dexterity' | 'constitution' | 'intelligence' | 'wisdom' | 'charisma'

export interface Speed {
  walk: number | null
  fly: number | null
  swim: number | null
  climb: number | null
  burrow: number | null
  hover: boolean
}

export interface AbilityScores {
  strength: number
  dexterity: number
  constitution: number
  intelligence: number
  wisdom: number
  charisma: number
}

export interface SavingThrowProficiency {
  ability: AbilityName
  bonus: number
}

export interface SkillProficiency {
  skill: string
  bonus: number
}

export interface DamageComponent {
  dice: string
  damage_type: string
}

export interface SavingThrowEffect {
  ability: AbilityName
  dc: number
  effect_on_save: string
}

export interface Action {
  id: string
  name: string
  description: string
  attack_bonus: number | null
  reach_or_range: string | null
  target: string | null
  damage: DamageComponent[]
  save: SavingThrowEffect | null
  recharge: string | null
  uses_per_day: number | null
  multiattack_refs: string[]
}

export interface LegendaryAction extends Action {
  cost: number
}

export interface SpecialAbility {
  id: string
  name: string
  description: string
  recharge: string | null
  uses_per_day: number | null
}

export interface Statblock {
  size: string
  creature_type: string
  subtype: string | null
  alignment: string
  armor_class: number
  armor_class_notes: string | null
  hit_points: number
  hit_dice: string
  speed: Speed
  ability_scores: AbilityScores
  saving_throws: SavingThrowProficiency[]
  skills: SkillProficiency[]
  damage_vulnerabilities: string[]
  damage_resistances: string[]
  damage_immunities: string[]
  condition_immunities: string[]
  senses: string[]
  languages: string[]
  challenge_rating: number
  experience_points: number
  special_abilities: SpecialAbility[]
  actions: Action[]
  legendary_actions: LegendaryAction[]
  legendary_actions_per_turn: number | null
}

export interface BestiaryMonsterListItem {
  id: number
  name: string
  slug: string
  creature_type: string
  challenge_rating: number
  is_favorite: boolean
  image_url: string | null
}

export interface BestiaryMonsterDetail {
  id: number
  name: string
  slug: string
  statblock: Statblock
  image_url: string | null
  is_favorite: boolean
  cloned_from_content_id: number | null
  created_at: string
  updated_at: string
}

export type BestiarySort = 'name' | 'cr' | 'created_at'

export interface BestiaryListParams {
  search?: string
  type?: string
  cr_min?: number
  cr_max?: number
  favorites_only?: boolean
  sort?: BestiarySort
}

function buildQuery(params: BestiaryListParams): string {
  const query = new URLSearchParams()
  if (params.search) query.set('search', params.search)
  if (params.type) query.set('type', params.type)
  if (params.cr_min !== undefined) query.set('cr_min', String(params.cr_min))
  if (params.cr_max !== undefined) query.set('cr_max', String(params.cr_max))
  if (params.favorites_only) query.set('favorites_only', 'true')
  if (params.sort) query.set('sort', params.sort)
  const qs = query.toString()
  return qs ? `?${qs}` : ''
}

export function listBestiary(params: BestiaryListParams = {}): Promise<BestiaryMonsterListItem[]> {
  return apiFetch<BestiaryMonsterListItem[]>(`/api/bestiary${buildQuery(params)}`)
}

export function fetchMonster(monsterId: number): Promise<BestiaryMonsterDetail> {
  return apiFetch<BestiaryMonsterDetail>(`/api/bestiary/${monsterId}`)
}

export function favoriteMonster(monsterId: number): Promise<BestiaryMonsterDetail> {
  return apiFetch<BestiaryMonsterDetail>(`/api/bestiary/${monsterId}/favorite`, {
    method: 'POST',
  })
}

export function unfavoriteMonster(monsterId: number): Promise<BestiaryMonsterDetail> {
  return apiFetch<BestiaryMonsterDetail>(`/api/bestiary/${monsterId}/favorite`, {
    method: 'DELETE',
  })
}

export const ALLOWED_CHALLENGE_RATINGS: number[] = [
  0,
  0.125,
  0.25,
  0.5,
  ...Array.from({ length: 30 }, (_, i) => i + 1),
]

const CHALLENGE_RATING_FRACTIONS: Record<number, string> = {
  0.125: '1/8',
  0.25: '1/4',
  0.5: '1/2',
}

export function formatChallengeRating(cr: number): string {
  return CHALLENGE_RATING_FRACTIONS[cr] ?? String(cr)
}

export interface BestiaryMonsterWritePayload {
  name: string
  statblock: Statblock
  image_url?: string | null
}

export function createMonster(
  payload: BestiaryMonsterWritePayload,
): Promise<BestiaryMonsterDetail> {
  return apiFetch<BestiaryMonsterDetail>('/api/bestiary', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function updateMonster(
  monsterId: number,
  payload: Partial<BestiaryMonsterWritePayload>,
): Promise<BestiaryMonsterDetail> {
  return apiFetch<BestiaryMonsterDetail>(`/api/bestiary/${monsterId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}
