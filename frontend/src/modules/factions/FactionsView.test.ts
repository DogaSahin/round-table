import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import FactionsView from './FactionsView.vue'
import * as factionsApi from './api'

describe('FactionsView', () => {
  it('loads the roster on mount', async () => {
    vi.spyOn(factionsApi, 'listFactions').mockResolvedValue([
      { id: 1, name: 'The Ashen Circle', disposition: 'neutral' },
    ])

    const wrapper = mount(FactionsView)
    await flushPromises()

    expect(wrapper.text()).toContain('The Ashen Circle')
  })

  it('creates a faction and selects it', async () => {
    vi.spyOn(factionsApi, 'listFactions').mockResolvedValue([])
    vi.spyOn(factionsApi, 'createFaction').mockResolvedValue({
      id: 1,
      name: 'New Faction',
      description: null,
      disposition: 'neutral',
      goals: null,
      clocks: [],
      activity: [],
    })

    const wrapper = mount(FactionsView)
    await flushPromises()

    await wrapper.find('input[type="text"]').setValue('New Faction')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(factionsApi.createFaction).toHaveBeenCalledWith('New Faction')
    expect(wrapper.text()).toContain('New Faction')
  })

  it('fills a clock on the selected faction', async () => {
    const detail = {
      id: 1,
      name: 'The Ashen Circle',
      description: null,
      disposition: 'neutral',
      goals: null,
      clocks: [{ id: 1, name: 'Ritual complete', segments: 6, filled: 2 }],
      activity: [],
    }
    vi.spyOn(factionsApi, 'listFactions').mockResolvedValue([
      { id: 1, name: 'The Ashen Circle', disposition: 'neutral' },
    ])
    vi.spyOn(factionsApi, 'fetchFaction').mockResolvedValue(detail)
    vi.spyOn(factionsApi, 'fillClock').mockResolvedValue({
      id: 1,
      name: 'Ritual complete',
      segments: 6,
      filled: 3,
    })

    const wrapper = mount(FactionsView)
    await flushPromises()

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'The Ashen Circle (neutral)')
      ?.trigger('click')
    await flushPromises()

    const segmentButtons = wrapper.findAll('[data-clock-segment]')
    await segmentButtons[2].trigger('click')
    await flushPromises()

    expect(factionsApi.fillClock).toHaveBeenCalledWith(1, 2)
  })
})
