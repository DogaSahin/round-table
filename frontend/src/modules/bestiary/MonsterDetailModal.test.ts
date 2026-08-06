import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import MonsterDetailModal from './MonsterDetailModal.vue'
import * as bestiaryApi from './api'
import type { BestiaryMonsterDetail } from './api'

const DETAIL: BestiaryMonsterDetail = {
  id: 1,
  name: 'Giant Rat',
  slug: 'giant-rat',
  statblock: {
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
    saving_throws: [],
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
    actions: [],
    legendary_actions: [],
    legendary_actions_per_turn: null,
  },
  image_url: null,
  is_favorite: false,
  cloned_from_content_id: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const RICH_DETAIL: BestiaryMonsterDetail = {
  id: 2,
  name: 'Rich Rat',
  slug: 'rich-rat',
  statblock: {
    size: 'Small',
    creature_type: 'beast',
    subtype: null,
    alignment: 'unaligned',
    armor_class: 12,
    armor_class_notes: null,
    hit_points: 7,
    hit_dice: '2d6',
    speed: { walk: 30, fly: 60, swim: null, climb: null, burrow: null, hover: true },
    ability_scores: {
      strength: 8,
      dexterity: 15,
      constitution: 11,
      intelligence: 2,
      wisdom: 10,
      charisma: 4,
    },
    saving_throws: [
      { ability: 'wisdom', bonus: 2 },
      { ability: 'dexterity', bonus: 2 },
    ],
    skills: [
      { skill: 'Perception', bonus: 4 },
      { skill: 'Stealth', bonus: 6 },
    ],
    damage_vulnerabilities: [],
    damage_resistances: ['fire', 'cold'],
    damage_immunities: [],
    condition_immunities: [],
    senses: ['darkvision 60 ft.'],
    languages: ['Common', 'Draconic'],
    challenge_rating: 1,
    experience_points: 200,
    special_abilities: [
      {
        id: 'keen-smell',
        name: 'Keen Smell',
        description: 'Advantage on smell-based Perception checks.',
        recharge: null,
        uses_per_day: 3,
      },
      {
        id: 'pack-tactics',
        name: 'Pack Tactics',
        description: 'Advantage on attack rolls if an ally is within 5 feet.',
        recharge: null,
        uses_per_day: null,
      },
    ],
    actions: [
      {
        id: 'bite',
        name: 'Bite',
        description: 'A bite attack.',
        attack_bonus: 4,
        reach_or_range: '5 ft.',
        target: 'one target',
        damage: [{ dice: '1d4', damage_type: 'piercing' }],
        save: { ability: 'dexterity', dc: 12, effect_on_save: 'take half damage.' },
        recharge: '5-6',
        uses_per_day: null,
        multiattack_refs: [],
      },
      {
        id: 'multiattack',
        name: 'Multiattack',
        description: 'The rat makes two attacks.',
        attack_bonus: null,
        reach_or_range: null,
        target: null,
        damage: [],
        save: null,
        recharge: null,
        uses_per_day: null,
        multiattack_refs: ['bite', 'nonexistent-action'],
      },
    ],
    legendary_actions: [
      {
        id: 'detect',
        name: 'Detect',
        description: 'The rat makes a Wisdom (Perception) check.',
        attack_bonus: null,
        reach_or_range: null,
        target: null,
        damage: [],
        save: null,
        recharge: null,
        uses_per_day: null,
        multiattack_refs: [],
        cost: 2,
      },
    ],
    legendary_actions_per_turn: 3,
  },
  image_url: null,
  is_favorite: false,
  cloned_from_content_id: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const DETAIL_WITHOUT_PER_TURN: BestiaryMonsterDetail = {
  ...RICH_DETAIL,
  id: 3,
  statblock: { ...RICH_DETAIL.statblock, legendary_actions_per_turn: null },
}

let wrapper: VueWrapper | null = null

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
})

describe('MonsterDetailModal', () => {
  it('does not render when monsterId is null', () => {
    wrapper = mount(MonsterDetailModal, { props: { monsterId: null } })
    expect(wrapper.find('.monster-detail-modal__backdrop').exists()).toBe(false)
  })

  it('fetches and renders detail when monsterId becomes non-null', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(DETAIL)

    wrapper = mount(MonsterDetailModal, { props: { monsterId: 1 } })
    await flushPromises()

    expect(bestiaryApi.fetchMonster).toHaveBeenCalledWith(1)
    expect(wrapper.text()).toContain('Giant Rat')
    expect(wrapper.text()).toContain('CR 1/8')
    expect(wrapper.text()).toContain('Speed 30 ft.')
  })

  it('emits close when the close button is clicked', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(DETAIL)
    wrapper = mount(MonsterDetailModal, { props: { monsterId: 1 } })
    await flushPromises()

    await wrapper.find('.monster-detail-modal__close').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('emits close on a backdrop click but not a click inside the modal body', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(DETAIL)
    wrapper = mount(MonsterDetailModal, { props: { monsterId: 1 } })
    await flushPromises()

    await wrapper.find('.monster-detail-modal__body').trigger('click')
    expect(wrapper.emitted('close')).toBeUndefined()

    await wrapper.find('.monster-detail-modal__backdrop').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('emits close on Escape keydown', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(DETAIL)
    wrapper = mount(MonsterDetailModal, { props: { monsterId: 1 } })
    await flushPromises()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('emits edit with the monster id when Edit is clicked', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(DETAIL)
    wrapper = mount(MonsterDetailModal, { props: { monsterId: 1 } })
    await flushPromises()

    await wrapper.find('.monster-detail-modal__edit').trigger('click')
    expect(wrapper.emitted('edit')).toEqual([[1]])
  })

  it('shows saving throws, skills, and tag-list fields when present', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(RICH_DETAIL)
    wrapper = mount(MonsterDetailModal, { props: { monsterId: 2 } })
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('Speed 30 ft., fly 60 ft. (hover)')
    expect(text).toContain('WIS +2, DEX +2')
    expect(text).toContain('Perception +4, Stealth +6')
    expect(text).toContain('Damage Resistances: fire, cold')
    expect(text).toContain('Senses: darkvision 60 ft.')
    expect(text).toContain('Languages: Common, Draconic')
    expect(text).not.toContain('Damage Vulnerabilities:')
    expect(text).not.toContain('Damage Immunities:')
    expect(text).not.toContain('Condition Immunities:')
  })

  it('hides saving throws, skills, and tag-list sections when empty', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(DETAIL)
    wrapper = mount(MonsterDetailModal, { props: { monsterId: 1 } })
    await flushPromises()

    const text = wrapper.text()
    expect(text).not.toContain('Saving Throws')
    expect(text).not.toContain('Skills')
    expect(text).not.toContain('Damage Vulnerabilities')
    expect(text).not.toContain('Damage Resistances')
    expect(text).not.toContain('Damage Immunities')
    expect(text).not.toContain('Condition Immunities')
    expect(text).not.toContain('Senses')
    expect(text).not.toContain('Languages')
  })

  it("renders a fully-populated action's composed summary", async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(RICH_DETAIL)
    wrapper = mount(MonsterDetailModal, { props: { monsterId: 2 } })
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('+4 to hit, 5 ft., one target.')
    expect(text).toContain('Hit: 1d4 piercing damage.')
    expect(text).toContain('DC 12 Dexterity saving throw or take half damage.')
    expect(text).toContain('Recharge 5-6.')
  })

  it('resolves multiattack references to names and drops unresolvable ones', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(RICH_DETAIL)
    wrapper = mount(MonsterDetailModal, { props: { monsterId: 2 } })
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('References: Bite.')
    expect(text).not.toContain('nonexistent-action')
  })

  it('shows the legendary actions per turn lead-in when set', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(RICH_DETAIL)
    wrapper = mount(MonsterDetailModal, { props: { monsterId: 2 } })
    await flushPromises()

    expect(wrapper.text()).toContain('The creature can take 3 legendary actions')
  })

  it('omits the legendary actions per turn lead-in when null', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(DETAIL_WITHOUT_PER_TURN)
    wrapper = mount(MonsterDetailModal, { props: { monsterId: 3 } })
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('Detect')
    expect(text).not.toContain('legendary actions, choosing')
  })

  it('shows special ability recharge/uses-per-day when present, omits when absent', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(RICH_DETAIL)
    wrapper = mount(MonsterDetailModal, { props: { monsterId: 2 } })
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('Keen Smell')
    expect(text).toContain('(3/day)')
    expect(text).toContain('Pack Tactics')
    // Only Keen Smell has a uses-per-day parenthetical — Pack Tactics has neither recharge nor
    // uses_per_day, so exactly one "/day)" fragment should exist across the whole render.
    expect((text.match(/\/day\)/g) ?? []).length).toBe(1)
  })
})
