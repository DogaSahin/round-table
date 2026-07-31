import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import MonsterFormModal from './MonsterFormModal.vue'
import * as bestiaryApi from './api'
import type { BestiaryMonsterDetail, Statblock } from './api'

const EXISTING_STATBLOCK: Statblock = {
  size: 'Small',
  creature_type: 'beast',
  subtype: null,
  alignment: 'unaligned',
  armor_class: 12,
  armor_class_notes: null,
  hit_points: 7,
  hit_dice: '2d6',
  speed: { walk: 30, fly: null, swim: null, climb: null, burrow: null, hover: false },
  ability_scores: {
    strength: 8,
    dexterity: 15,
    constitution: 11,
    intelligence: 2,
    wisdom: 10,
    charisma: 4,
  },
  saving_throws: [{ ability: 'wisdom', bonus: 2 }],
  skills: [],
  damage_vulnerabilities: [],
  damage_resistances: [],
  damage_immunities: [],
  condition_immunities: [],
  senses: [],
  languages: [],
  challenge_rating: 0.125,
  experience_points: 25,
  special_abilities: [],
  actions: [
    {
      id: 'bite',
      name: 'Bite',
      description: 'A bite attack.',
      attack_bonus: 4,
      reach_or_range: '5 ft.',
      target: 'one target',
      damage: [],
      save: null,
      recharge: null,
      uses_per_day: null,
      multiattack_refs: [],
    },
  ],
  legendary_actions: [],
  legendary_actions_per_turn: null,
}

const EXISTING_DETAIL: BestiaryMonsterDetail = {
  id: 1,
  name: 'Giant Rat',
  slug: 'giant-rat',
  statblock: EXISTING_STATBLOCK,
  image_url: null,
  is_favorite: false,
  cloned_from_content_id: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

let wrapper: VueWrapper | null = null

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
})

describe('MonsterFormModal', () => {
  it('renders create-mode defaults', () => {
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })

    expect(wrapper.text()).toContain('New Monster')
    expect((wrapper.find('input[name="name"]').element as HTMLInputElement).value).toBe('')
    expect((wrapper.find('input[name="size"]').element as HTMLInputElement).value).toBe('Medium')
    expect((wrapper.find('input[name="strength"]').element as HTMLInputElement).valueAsNumber).toBe(
      10,
    )
    expect(
      (wrapper.find('select[name="challengeRating"]').element as HTMLSelectElement).value,
    ).toBe('0')
  })

  it('pre-fills every visible field from a fetched monster in edit mode', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(EXISTING_DETAIL)

    wrapper = mount(MonsterFormModal, { props: { monsterId: 1 } })
    await flushPromises()

    expect(wrapper.text()).toContain('Edit Monster')
    expect((wrapper.find('input[name="name"]').element as HTMLInputElement).value).toBe('Giant Rat')
    expect((wrapper.find('input[name="size"]').element as HTMLInputElement).value).toBe('Small')
    expect((wrapper.find('input[name="creatureType"]').element as HTMLInputElement).value).toBe(
      'beast',
    )
    expect((wrapper.find('input[name="strength"]').element as HTMLInputElement).valueAsNumber).toBe(
      8,
    )
    expect(
      (wrapper.find('input[name="hitPoints"]').element as HTMLInputElement).valueAsNumber,
    ).toBe(7)
  })

  it('blocks submit and shows inline errors for missing required text fields', async () => {
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster')
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })

    await wrapper.find('input[name="size"]').setValue('')
    await wrapper.find('input[name="alignment"]').setValue('')
    await wrapper.find('input[name="hitDice"]').setValue('')
    // name and creatureType are already empty in create mode.
    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.text()).toContain('Name is required.')
    expect(wrapper.text()).toContain('Size is required.')
    expect(wrapper.text()).toContain('Type is required.')
    expect(wrapper.text()).toContain('Alignment is required.')
    expect(wrapper.text()).toContain('Hit dice is required.')
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('blocks submit and shows inline errors for negative numeric fields', async () => {
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster')
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })

    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('input[name="armorClass"]').setValue('-1')
    await wrapper.find('input[name="hitPoints"]').setValue('-1')
    await wrapper.find('input[name="experiencePoints"]').setValue('-1')
    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.text()).toContain('Armor class cannot be negative.')
    expect(wrapper.text()).toContain('Hit points cannot be negative.')
    expect(wrapper.text()).toContain('Experience points cannot be negative.')
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('blocks submit and shows inline errors for out-of-range ability scores', async () => {
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster')
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })

    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('input[name="strength"]').setValue('0')
    await wrapper.find('input[name="charisma"]').setValue('31')
    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.text()).toContain('Must be between 1 and 30.')
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('creates a new monster with the schema-default base merged with form values', async () => {
    const created: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Test Monster' }
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster').mockResolvedValue(created)

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    const payload = createSpy.mock.calls[0][0]
    expect(payload.name).toBe('Test Monster')
    expect(payload.statblock.creature_type).toBe('beast')
    expect(payload.statblock.saving_throws).toEqual([])
    expect(payload.statblock.actions).toEqual([])
    expect(wrapper.emitted('saved')).toEqual([[created]])
  })

  it('updates an existing monster, preserving fields the form does not expose', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(EXISTING_DETAIL)
    const updated: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Renamed Rat' }
    const updateSpy = vi.spyOn(bestiaryApi, 'updateMonster').mockResolvedValue(updated)

    wrapper = mount(MonsterFormModal, { props: { monsterId: 1 } })
    await flushPromises()

    await wrapper.find('input[name="name"]').setValue('Renamed Rat')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(updateSpy).toHaveBeenCalledTimes(1)
    const [calledId, payload] = updateSpy.mock.calls[0]
    expect(calledId).toBe(1)
    expect(payload.name).toBe('Renamed Rat')
    expect(payload.statblock?.saving_throws).toEqual(EXISTING_STATBLOCK.saving_throws)
    expect(payload.statblock?.actions).toEqual(EXISTING_STATBLOCK.actions)
    expect(wrapper.emitted('saved')).toEqual([[updated]])
  })

  it('shows an error and does not emit saved when the save fails', async () => {
    vi.spyOn(bestiaryApi, 'createMonster').mockRejectedValue(new Error('server error'))

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(wrapper.text()).toContain('Error:')
    expect(wrapper.emitted('saved')).toBeUndefined()
  })
})
