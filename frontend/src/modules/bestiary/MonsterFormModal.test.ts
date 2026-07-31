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
  skills: [{ skill: 'Perception', bonus: 4 }],
  damage_vulnerabilities: [],
  damage_resistances: ['fire'],
  damage_immunities: [],
  condition_immunities: ['poisoned'],
  senses: ['darkvision 60 ft.'],
  languages: ['Common'],
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
    expect(
      (wrapper.find('input[name="savingThrow-strength"]').element as HTMLInputElement).value,
    ).toBe('')
    expect(wrapper.find('[name^="skill-"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Damage Vulnerabilities')
    expect(wrapper.text()).toContain('Languages')
    expect(wrapper.find('[name^="languages-"]').exists()).toBe(false)
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
    expect(
      (wrapper.find('input[name="savingThrow-wisdom"]').element as HTMLInputElement).valueAsNumber,
    ).toBe(2)
    expect(
      (wrapper.find('input[name="savingThrow-strength"]').element as HTMLInputElement).value,
    ).toBe('')
    expect((wrapper.find('select[name="skill-0"]').element as HTMLSelectElement).value).toBe(
      'Perception',
    )
    expect(
      (wrapper.find('input[name="skillBonus-0"]').element as HTMLInputElement).valueAsNumber,
    ).toBe(4)
    expect(
      (wrapper.find('select[name="damageResistances-0"]').element as HTMLSelectElement).value,
    ).toBe('fire')
    expect(
      (wrapper.find('select[name="conditionImmunities-0"]').element as HTMLSelectElement).value,
    ).toBe('poisoned')
    expect((wrapper.find('input[name="senses-0"]').element as HTMLInputElement).value).toBe(
      'darkvision 60 ft.',
    )
    expect((wrapper.find('input[name="languages-0"]').element as HTMLInputElement).value).toBe(
      'Common',
    )
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
    expect(payload.statblock.skills).toEqual([])
    expect(payload.statblock.actions).toEqual([])
    expect(wrapper.emitted('saved')).toEqual([[created]])
  })

  it('includes saving throws, skills, and tag-list entries in a create submission', async () => {
    const created: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Test Monster' }
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster').mockResolvedValue(created)

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('input[name="savingThrow-dexterity"]').setValue('3')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add skill')
      ?.trigger('click')
    await wrapper.find('select[name="skill-0"]').setValue('Stealth')
    await wrapper.find('input[name="skillBonus-0"]').setValue('5')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add Damage Resistances')
      ?.trigger('click')
    await wrapper.find('select[name="damageResistances-0"]').setValue('cold')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add Languages')
      ?.trigger('click')
    await wrapper.find('input[name="languages-0"]').setValue('Elvish')

    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    const payload = createSpy.mock.calls[0][0]
    expect(payload.statblock.saving_throws).toEqual([{ ability: 'dexterity', bonus: 3 }])
    expect(payload.statblock.skills).toEqual([{ skill: 'Stealth', bonus: 5 }])
    expect(payload.statblock.damage_resistances).toEqual(['cold'])
    expect(payload.statblock.languages).toEqual(['Elvish'])
  })

  it('drops incomplete skill and tag-list rows from the submitted payload without blocking submit', async () => {
    const created: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Test Monster' }
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster').mockResolvedValue(created)

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add skill')
      ?.trigger('click')
    // Leave the skill row's select and bonus unfilled.

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add Languages')
      ?.trigger('click')
    // Leave the language row blank.

    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    const payload = createSpy.mock.calls[0][0]
    expect(payload.statblock.skills).toEqual([])
    expect(payload.statblock.languages).toEqual([])
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
    expect(payload.statblock?.actions).toEqual(EXISTING_STATBLOCK.actions)
    expect(payload.statblock?.legendary_actions).toEqual(EXISTING_STATBLOCK.legendary_actions)
    expect(payload.statblock?.special_abilities).toEqual(EXISTING_STATBLOCK.special_abilities)
    expect(payload.statblock?.legendary_actions_per_turn).toEqual(
      EXISTING_STATBLOCK.legendary_actions_per_turn,
    )
    expect(wrapper.emitted('saved')).toEqual([[updated]])
  })

  it('submits a changed saving throw during edit, proving it is genuinely editable', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(EXISTING_DETAIL)
    const updated: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Giant Rat' }
    const updateSpy = vi.spyOn(bestiaryApi, 'updateMonster').mockResolvedValue(updated)

    wrapper = mount(MonsterFormModal, { props: { monsterId: 1 } })
    await flushPromises()

    await wrapper.find('input[name="savingThrow-wisdom"]').setValue('5')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(updateSpy).toHaveBeenCalledTimes(1)
    const [, payload] = updateSpy.mock.calls[0]
    expect(payload.statblock?.saving_throws).toEqual([{ ability: 'wisdom', bonus: 5 }])
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

  it('blocks submit and shows an error when the edit-mode detail fetch fails', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockRejectedValue(new Error('network blip'))
    const updateSpy = vi.spyOn(bestiaryApi, 'updateMonster')

    wrapper = mount(MonsterFormModal, { props: { monsterId: 1 } })
    await flushPromises()

    await wrapper.find('input[name="name"]').setValue('Renamed Rat')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(updateSpy).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Could not load monster details. Please close and try again.')
    expect(wrapper.emitted('saved')).toBeUndefined()
  })

  it('blocks submit and shows the negative-number error when a numeric field is cleared', async () => {
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster')
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })

    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('input[name="armorClass"]').setValue('')
    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.text()).toContain('Armor class cannot be negative.')
    expect(createSpy).not.toHaveBeenCalled()
  })
})
