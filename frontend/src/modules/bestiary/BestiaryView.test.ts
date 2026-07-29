import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import BestiaryView from './BestiaryView.vue'
import * as bestiaryApi from './api'
import type { BestiaryMonsterListItem, Statblock } from './api'

const RAT: BestiaryMonsterListItem = {
  id: 1,
  name: 'Giant Rat',
  slug: 'giant-rat',
  creature_type: 'beast',
  challenge_rating: 0.125,
  is_favorite: false,
  image_url: null,
}

const OWLBEAR: BestiaryMonsterListItem = {
  id: 2,
  name: 'Owlbear',
  slug: 'owlbear',
  creature_type: 'monstrosity',
  challenge_rating: 3,
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

let wrapper: VueWrapper | null = null

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
  vi.useRealTimers()
})

describe('BestiaryView', () => {
  it('loads the roster and the type-options list once on mount', async () => {
    const listSpy = vi.spyOn(bestiaryApi, 'listBestiary').mockResolvedValue([RAT, OWLBEAR])

    wrapper = mount(BestiaryView)
    await flushPromises()

    expect(wrapper.text()).toContain('Giant Rat')
    expect(wrapper.text()).toContain('Owlbear')
    // Once for the unfiltered type-options fetch, once for the initial roster load.
    expect(listSpy).toHaveBeenCalledTimes(2)
    expect(listSpy).toHaveBeenCalledWith({})
  })

  it('does not refetch type options when other filters change', async () => {
    const listSpy = vi.spyOn(bestiaryApi, 'listBestiary').mockResolvedValue([RAT])
    wrapper = mount(BestiaryView)
    await flushPromises()
    listSpy.mockClear()

    await wrapper.find('.bestiary-filters__favorites-chip').trigger('click')
    await flushPromises()

    expect(listSpy).toHaveBeenCalledTimes(1)
    expect(listSpy).toHaveBeenCalledWith(expect.objectContaining({ favorites_only: true }))
  })

  it('debounces the search input before fetching', async () => {
    vi.useFakeTimers()
    const listSpy = vi.spyOn(bestiaryApi, 'listBestiary').mockResolvedValue([RAT])
    wrapper = mount(BestiaryView)
    await flushPromises()
    listSpy.mockClear()

    await wrapper.find('input[type="text"]').setValue('rat')
    expect(listSpy).not.toHaveBeenCalled()

    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(listSpy).toHaveBeenCalledWith(expect.objectContaining({ search: 'rat' }))
  })

  it('shows an empty state and resets filters on "Clear filters"', async () => {
    const listSpy = vi.spyOn(bestiaryApi, 'listBestiary').mockResolvedValue([])
    wrapper = mount(BestiaryView)
    await flushPromises()

    expect(wrapper.text()).toContain('No monsters match')

    listSpy.mockClear()
    await wrapper.find('.bestiary-filters__favorites-chip').trigger('click')
    await flushPromises()

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Clear filters')
      ?.trigger('click')
    await flushPromises()

    expect(wrapper.find('.bestiary-filters__favorites-chip').attributes('aria-pressed')).toBe(
      'false',
    )
  })

  it('removes a card from the grid when unfavorited while the favorites filter is active', async () => {
    const listSpy = vi
      .spyOn(bestiaryApi, 'listBestiary')
      .mockResolvedValue([{ ...RAT, is_favorite: true }])
    vi.spyOn(bestiaryApi, 'unfavoriteMonster').mockResolvedValue({
      id: 1,
      name: 'Giant Rat',
      slug: 'giant-rat',
      statblock: STATBLOCK,
      image_url: null,
      is_favorite: false,
      cloned_from_content_id: null,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    })

    wrapper = mount(BestiaryView)
    await flushPromises()

    await wrapper.find('.bestiary-filters__favorites-chip').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Giant Rat')

    listSpy.mockClear()

    await wrapper.find('.monster-card__favorite').trigger('click')
    await flushPromises()

    expect(wrapper.text()).not.toContain('Giant Rat')
    expect(listSpy).not.toHaveBeenCalled()
  })
})
