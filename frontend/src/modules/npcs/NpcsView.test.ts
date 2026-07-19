import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import NpcsView from './NpcsView.vue'
import * as npcsApi from './api'

describe('NpcsView', () => {
  it('loads the roster on mount', async () => {
    vi.spyOn(npcsApi, 'listNpcs').mockResolvedValue([
      { id: 1, name: 'Old Man Grigg', disposition: 'neutral', faction_id: null },
    ])

    const wrapper = mount(NpcsView)
    await flushPromises()

    expect(wrapper.text()).toContain('Old Man Grigg')
  })

  it('creates an npc and selects it', async () => {
    vi.spyOn(npcsApi, 'listNpcs').mockResolvedValue([])
    vi.spyOn(npcsApi, 'createNpc').mockResolvedValue({
      id: 1,
      name: 'New NPC',
      disposition: 'neutral',
      faction_id: null,
      statblock: null,
      motivation: null,
      secrets: null,
      voice: null,
      portrait_path: null,
      player_visible: false,
    })

    const wrapper = mount(NpcsView)
    await flushPromises()

    await wrapper.find('input[type="text"]').setValue('New NPC')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(npcsApi.createNpc).toHaveBeenCalledWith('New NPC')
    expect(wrapper.text()).toContain('New NPC')
  })

  it('deletes an npc and clears the selection', async () => {
    vi.spyOn(npcsApi, 'listNpcs').mockResolvedValue([
      { id: 1, name: 'Old Man Grigg', disposition: 'neutral', faction_id: null },
    ])
    vi.spyOn(npcsApi, 'fetchNpc').mockResolvedValue({
      id: 1,
      name: 'Old Man Grigg',
      disposition: 'neutral',
      faction_id: null,
      statblock: null,
      motivation: null,
      secrets: null,
      voice: null,
      portrait_path: null,
      player_visible: false,
    })
    vi.spyOn(npcsApi, 'deleteNpc').mockResolvedValue(undefined)

    const wrapper = mount(NpcsView)
    await flushPromises()

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Old Man Grigg (neutral)')
      ?.trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Old Man Grigg')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Delete')
      ?.trigger('click')
    await flushPromises()

    expect(npcsApi.deleteNpc).toHaveBeenCalledWith(1)
  })
})
