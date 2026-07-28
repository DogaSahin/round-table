import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import MonsterCard from './MonsterCard.vue'
import * as bestiaryApi from './api'
import type { BestiaryMonsterDetail, BestiaryMonsterListItem, Statblock } from './api'

const ITEM: BestiaryMonsterListItem = {
  id: 1,
  name: 'Giant Rat',
  slug: 'giant-rat',
  creature_type: 'beast',
  challenge_rating: 0.125,
  is_favorite: false,
  image_url: null,
}

const STATBLOCK: Statblock = {
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
}

function detailWith(isFavorite: boolean): BestiaryMonsterDetail {
  return {
    id: 1,
    name: 'Giant Rat',
    slug: 'giant-rat',
    statblock: STATBLOCK,
    image_url: null,
    is_favorite: isFavorite,
    cloned_from_content_id: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  }
}

describe('MonsterCard', () => {
  it('renders name, type, and formatted CR', () => {
    const wrapper = mount(MonsterCard, { props: { item: ITEM } })
    expect(wrapper.text()).toContain('Giant Rat')
    expect(wrapper.text()).toContain('beast')
    expect(wrapper.text()).toContain('CR 1/8')
  })

  it('emits open with the monster id when the body is clicked', async () => {
    const wrapper = mount(MonsterCard, { props: { item: ITEM } })
    await wrapper.find('.monster-card__body').trigger('click')
    expect(wrapper.emitted('open')).toEqual([[1]])
  })

  it('favorites an unfavorited monster and updates the star', async () => {
    vi.spyOn(bestiaryApi, 'favoriteMonster').mockResolvedValue(detailWith(true))

    const wrapper = mount(MonsterCard, { props: { item: ITEM } })
    expect(wrapper.find('.monster-card__favorite').text()).toBe('☆')

    await wrapper.find('.monster-card__favorite').trigger('click')
    await flushPromises()

    expect(bestiaryApi.favoriteMonster).toHaveBeenCalledWith(1)
    expect(wrapper.find('.monster-card__favorite').text()).toBe('★')
  })

  it('unfavorites an already-favorited monster', async () => {
    vi.spyOn(bestiaryApi, 'unfavoriteMonster').mockResolvedValue(detailWith(false))

    const wrapper = mount(MonsterCard, {
      props: { item: { ...ITEM, is_favorite: true } },
    })

    await wrapper.find('.monster-card__favorite').trigger('click')
    await flushPromises()

    expect(bestiaryApi.unfavoriteMonster).toHaveBeenCalledWith(1)
    expect(wrapper.find('.monster-card__favorite').text()).toBe('☆')
  })
})
