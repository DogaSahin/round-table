import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import MapsView from './MapsView.vue'
import * as mapsApi from './api'
import type { MapDetailOut } from './api'

// MapCanvas mounts a real (mocked-Konva) canvas; MapsView's own concerns are
// the roster/create/select page chrome, so the canvas child is stubbed here
// to keep this suite focused and independent of Konva/WS wiring, which is
// covered by MapCanvas.test.ts.
vi.mock('./MapCanvas.vue', () => ({
  default: {
    name: 'MapCanvas',
    props: ['map', 'tool', 'snapEnabled'],
    template: '<div class="map-canvas-stub" />',
  },
}))

function makeMapDetail(overrides: Partial<MapDetailOut> = {}): MapDetailOut {
  return {
    id: 1,
    name: 'Goblin Warren',
    image_path: null,
    image_w: null,
    image_h: null,
    grid_size_px: 70,
    grid_offset_x: 0,
    grid_offset_y: 0,
    grid_visible: true,
    feet_per_square: 5,
    diagonal_rule: 'chebyshev',
    is_active: false,
    tokens: [],
    fog: [],
    ...overrides,
  }
}

describe('MapsView', () => {
  it('loads the roster on mount', async () => {
    vi.spyOn(mapsApi, 'listMaps').mockResolvedValue([
      { id: 1, name: 'Goblin Warren', is_active: false },
    ])

    const wrapper = mount(MapsView)
    await flushPromises()

    expect(wrapper.text()).toContain('Goblin Warren')
  })

  it('creates a map and selects it', async () => {
    vi.spyOn(mapsApi, 'listMaps').mockResolvedValue([])
    vi.spyOn(mapsApi, 'createMap').mockResolvedValue(makeMapDetail())

    const wrapper = mount(MapsView)
    await flushPromises()

    await wrapper.find('input[placeholder="Map name"]').setValue('Goblin Warren')
    await wrapper.find('form.maps-create-form').trigger('submit.prevent')
    await flushPromises()

    expect(mapsApi.createMap).toHaveBeenCalledWith('Goblin Warren')
    expect(wrapper.text()).toContain('Goblin Warren')
    expect(wrapper.findComponent({ name: 'MapCanvas' }).exists()).toBe(true)
  })

  it('selects a map from the roster and passes it to the canvas', async () => {
    vi.spyOn(mapsApi, 'listMaps').mockResolvedValue([
      { id: 1, name: 'Goblin Warren', is_active: false },
    ])
    vi.spyOn(mapsApi, 'fetchMap').mockResolvedValue(makeMapDetail())

    const wrapper = mount(MapsView)
    await flushPromises()

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Goblin Warren')
      ?.trigger('click')
    await flushPromises()

    const canvas = wrapper.findComponent({ name: 'MapCanvas' })
    expect(canvas.exists()).toBe(true)
    expect((canvas.props('map') as MapDetailOut).id).toBe(1)
  })
})
