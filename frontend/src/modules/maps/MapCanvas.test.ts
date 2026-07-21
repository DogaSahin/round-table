import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MapCanvas from './MapCanvas.vue'
import * as mapsApi from './api'
import type { MapDetailOut, TokenOut } from './api'

// A real Konva.Stage needs a live <canvas> 2D context, which jsdom does not
// provide. Konva is mocked with lightweight fakes so MapCanvas can mount in
// the test environment; assertions target construction args (e.g. stage
// size) rather than pixel-accurate rendering -- see the scoping note in
// MapCanvas.vue's header comment.
const { createdStages } = vi.hoisted(() => {
  return { createdStages: [] as Array<{ config: Record<string, unknown> }> }
})

vi.mock('konva', () => {
  class FakeNode {
    config: Record<string, unknown>
    constructor(config: Record<string, unknown> = {}) {
      this.config = { ...config }
    }
    on() {
      return this
    }
    off() {
      return this
    }
    position(pos?: { x: number; y: number }) {
      if (pos) {
        this.config.x = pos.x
        this.config.y = pos.y
        return this
      }
      return { x: Number(this.config.x ?? 0), y: Number(this.config.y ?? 0) }
    }
    draggable() {
      return this
    }
    width() {
      return Number(this.config.width ?? 0)
    }
    height() {
      return Number(this.config.height ?? 0)
    }
    image(img?: unknown) {
      if (img !== undefined) this.config.image = img
      return this.config.image
    }
    destroy() {
      return this
    }
  }

  class FakeLayer extends FakeNode {
    children: FakeNode[] = []
    add(...nodes: FakeNode[]) {
      this.children.push(...nodes)
      return this
    }
    destroyChildren() {
      this.children = []
      return this
    }
    batchDraw() {
      return this
    }
    getNativeCanvasElement() {
      return { style: {} } as unknown as HTMLCanvasElement
    }
  }

  class FakeStage extends FakeNode {
    layers: FakeLayer[] = []
    pointer: { x: number; y: number } | null = null
    constructor(config: Record<string, unknown> = {}) {
      super(config)
      createdStages.push(this)
    }
    add(...layers: FakeLayer[]) {
      this.layers.push(...layers)
      return this
    }
    getPointerPosition() {
      return this.pointer
    }
  }

  return {
    default: {
      Stage: FakeStage,
      Layer: FakeLayer,
      Image: FakeNode,
      Circle: FakeNode,
      Rect: FakeNode,
      Line: FakeNode,
      Text: FakeNode,
    },
  }
})

vi.mock('./ws', () => ({
  connectMapSocket: vi.fn(() => () => {}),
}))

function makeMap(overrides: Partial<MapDetailOut> = {}): MapDetailOut {
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

function makeToken(overrides: Partial<TokenOut> = {}): TokenOut {
  return {
    id: 1,
    layer: 'tokens',
    kind: 'disc',
    x: 100,
    y: 100,
    size_squares: 1,
    color: '#888888',
    image_path: null,
    name: 'Goblin',
    hp_current: null,
    hp_max: null,
    hp_visible_to_players: false,
    visible_to_players: true,
    status_markers: [],
    is_pc: false,
    npc_id: null,
    combatant_id: null,
    ...overrides,
  }
}

describe('MapCanvas', () => {
  it('mounts a Konva stage sized to the image dimensions once an image is present', () => {
    createdStages.length = 0
    const map = makeMap({ image_path: 'maps/abc.png', image_w: 1200, image_h: 900 })

    mount(MapCanvas, {
      props: { map, tool: 'select', snapEnabled: true },
    })

    expect(createdStages).toHaveLength(1)
    expect(createdStages[0]?.config.width).toBe(1200)
    expect(createdStages[0]?.config.height).toBe(900)
  })

  it('falls back to a default stage size when no image has been uploaded yet', () => {
    createdStages.length = 0
    const map = makeMap()

    mount(MapCanvas, {
      props: { map, tool: 'select', snapEnabled: true },
    })

    expect(createdStages[0]?.config.width).toBe(800)
    expect(createdStages[0]?.config.height).toBe(600)
  })

  it('calls moveToken with the dragged coordinates and re-fetches the map on token dragend', async () => {
    const map = makeMap({ tokens: [makeToken({ id: 7 })] })
    const moveSpy = vi.spyOn(mapsApi, 'moveToken').mockResolvedValue(makeToken({ id: 7 }))
    const fetchSpy = vi.spyOn(mapsApi, 'fetchMap').mockResolvedValue(map)

    const wrapper = mount(MapCanvas, {
      props: { map, tool: 'select', snapEnabled: true },
    })

    const vm = wrapper.vm as unknown as {
      handleTokenDragEnd: (token: TokenOut, x: number, y: number) => Promise<void>
    }
    await vm.handleTokenDragEnd(map.tokens[0], 210, 340)

    expect(moveSpy).toHaveBeenCalledWith(7, 210, 340, true)
    expect(fetchSpy).toHaveBeenCalledWith(map.id)
    expect(wrapper.emitted('map-updated')).toBeTruthy()
  })

  it('passes snap=false through to moveToken when the snap toggle is off', async () => {
    const map = makeMap({ tokens: [makeToken({ id: 3 })] })
    const moveSpy = vi.spyOn(mapsApi, 'moveToken').mockResolvedValue(makeToken({ id: 3 }))
    vi.spyOn(mapsApi, 'fetchMap').mockResolvedValue(map)

    const wrapper = mount(MapCanvas, {
      props: { map, tool: 'select', snapEnabled: false },
    })

    const vm = wrapper.vm as unknown as {
      handleTokenDragEnd: (token: TokenOut, x: number, y: number) => Promise<void>
    }
    await vm.handleTokenDragEnd(map.tokens[0], 50, 60)

    expect(moveSpy).toHaveBeenCalledWith(3, 50, 60, false)
  })
})
