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
})
