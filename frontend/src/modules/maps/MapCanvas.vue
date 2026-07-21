<script setup lang="ts">
  // frontend/src/modules/maps/MapCanvas.vue
  //
  // Owns the Konva stage/layers and all pointer interaction for a single
  // selected map. Kept separate from MapsView.vue so the page chrome (roster,
  // create form, tool/snap controls) stays independently reviewable from the
  // canvas rendering + WS wiring.
  //
  // Layer order, bottom to top: background -> grid -> tokens -> fog ->
  // interaction (drag-rect / measure-line previews, always on top so the DM
  // can see what they're drawing even under fog).
  //
  // Testing note: a pixel-accurate Konva mouse-interaction test through jsdom
  // (no real <canvas> 2D context is available in the test environment) isn't
  // meaningful to write. MapCanvas.test.ts mocks the `konva` module and
  // asserts at the level of "constructed with the right stage size" and "the
  // exposed handleTokenDragEnd, given coordinates, calls moveToken correctly"
  // rather than simulating real Konva hit-testing/dragging.
  import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
  import Konva from 'konva'
  import { addFogOp, fetchMap, mediaUrl, moveToken, type MapDetailOut, type TokenOut } from './api'
  import { pathDistance } from './geometry'
  import { connectMapSocket } from './ws'

  const props = defineProps<{
    map: MapDetailOut
    tool: 'select' | 'measure' | 'reveal-rect' | 'hide-rect'
    snapEnabled: boolean
  }>()

  const emit = defineEmits<{
    (e: 'map-updated', map: MapDetailOut): void
    (e: 'error', err: unknown): void
  }>()

  const DEFAULT_WIDTH = 800
  const DEFAULT_HEIGHT = 600
  const FOG_OPACITY = '0.65'

  const containerEl = ref<HTMLDivElement | null>(null)
  const measureDistanceFt = ref<number | null>(null)

  let stage: Konva.Stage | null = null
  let backgroundLayer: Konva.Layer | null = null
  let gridLayer: Konva.Layer | null = null
  let tokensLayer: Konva.Layer | null = null
  let fogLayer: Konva.Layer | null = null
  let interactionLayer: Konva.Layer | null = null
  let disconnectSocket: (() => void) | null = null

  const tokenNodes = new Map<number, Konva.Node>()
  const tokenLabels = new Map<number, Konva.Text>()

  let measurePoints: Array<[number, number]> = []
  let measuring = false
  let rectStart: { x: number; y: number } | null = null

  function stageWidth(): number {
    return props.map.image_w ?? DEFAULT_WIDTH
  }

  function stageHeight(): number {
    return props.map.image_h ?? DEFAULT_HEIGHT
  }

  function tokenPixelSize(token: TokenOut): number {
    return Math.max(1, token.size_squares) * props.map.grid_size_px
  }

  function buildBackground() {
    if (!backgroundLayer) return
    backgroundLayer.destroyChildren()
    if (props.map.image_path) {
      const img = new window.Image()
      const path = props.map.image_path
      img.onload = () => {
        backgroundLayer?.add(
          new Konva.Image({
            image: img,
            x: 0,
            y: 0,
            width: stageWidth(),
            height: stageHeight(),
          }),
        )
        backgroundLayer?.batchDraw()
      }
      img.src = mediaUrl(path)
    } else {
      backgroundLayer.add(
        new Konva.Rect({
          x: 0,
          y: 0,
          width: stageWidth(),
          height: stageHeight(),
          fill: '#1e293b',
        }),
      )
    }
    backgroundLayer.batchDraw()
  }

  function buildGrid() {
    if (!gridLayer) return
    gridLayer.destroyChildren()
    if (props.map.grid_visible) {
      const size = props.map.grid_size_px
      if (size > 0) {
        const w = stageWidth()
        const h = stageHeight()
        const startX = ((props.map.grid_offset_x % size) + size) % size
        const startY = ((props.map.grid_offset_y % size) + size) % size
        for (let x = startX; x <= w; x += size) {
          gridLayer.add(
            new Konva.Line({
              points: [x, 0, x, h],
              stroke: 'rgba(255,255,255,0.3)',
              strokeWidth: 1,
            }),
          )
        }
        for (let y = startY; y <= h; y += size) {
          gridLayer.add(
            new Konva.Line({
              points: [0, y, w, y],
              stroke: 'rgba(255,255,255,0.3)',
              strokeWidth: 1,
            }),
          )
        }
      }
    }
    gridLayer.batchDraw()
  }

  function buildTokens() {
    if (!tokensLayer) return
    tokensLayer.destroyChildren()
    tokenNodes.clear()
    tokenLabels.clear()

    for (const token of props.map.tokens) {
      const size = tokenPixelSize(token)
      let node: Konva.Node

      if (token.image_path) {
        const path = token.image_path
        const konvaImage = new Konva.Image({
          image: undefined,
          x: token.x,
          y: token.y,
          width: size,
          height: size,
          offsetX: size / 2,
          offsetY: size / 2,
          draggable: props.tool === 'select',
        })
        const img = new window.Image()
        img.onload = () => {
          konvaImage.image(img)
          tokensLayer?.batchDraw()
        }
        img.src = mediaUrl(path)
        node = konvaImage
      } else {
        node = new Konva.Circle({
          x: token.x,
          y: token.y,
          radius: size / 2,
          fill: token.color,
          draggable: props.tool === 'select',
        })
      }

      node.on('dragend', () => {
        const pos = node.position()
        void handleTokenDragEnd(token, Math.round(pos.x), Math.round(pos.y))
      })
      tokensLayer.add(node)
      tokenNodes.set(token.id, node)

      const label = new Konva.Text({
        x: token.x - size / 2,
        y: token.y + size / 2 + 2,
        width: size,
        align: 'center',
        text: token.name,
        fontSize: 12,
        fill: '#ffffff',
      })
      tokensLayer.add(label)
      tokenLabels.set(token.id, label)
    }
    tokensLayer.batchDraw()
  }

  function buildFog() {
    if (!fogLayer) return
    fogLayer.destroyChildren()
    fogLayer.add(
      new Konva.Rect({ x: 0, y: 0, width: stageWidth(), height: stageHeight(), fill: '#000000' }),
    )
    for (const entry of props.map.fog) {
      const geom = entry.geom
      const isAll = geom.type === 'all'
      const rectBox = isAll
        ? { x: 0, y: 0, width: stageWidth(), height: stageHeight() }
        : {
            x: Number(geom.x ?? 0),
            y: Number(geom.y ?? 0),
            width: Number(geom.w ?? 0),
            height: Number(geom.h ?? 0),
          }
      fogLayer.add(
        new Konva.Rect({
          ...rectBox,
          fill: '#000000',
          globalCompositeOperation: entry.kind === 'reveal' ? 'destination-out' : 'source-over',
        }),
      )
    }
    fogLayer.batchDraw()
    // The whole fog layer is dimmed via the underlying <canvas> element's CSS
    // opacity -- NOT Konva node opacity. Node-level opacity would double-apply
    // through the destination-out/source-over compositing that's already
    // doing the reveal/hide visual work above, washing out the effect.
    fogLayer.getNativeCanvasElement().style.opacity = FOG_OPACITY
  }

  function renderAll() {
    if (!stage) return
    stage.width(stageWidth())
    stage.height(stageHeight())
    buildBackground()
    buildGrid()
    buildTokens()
    buildFog()
  }

  async function handleTokenDragEnd(token: TokenOut, x: number, y: number) {
    try {
      await moveToken(token.id, x, y, props.snapEnabled)
      // Re-fetch (rather than optimistically patching local state) to match
      // every other module's convention. The dragged node itself is left
      // wherever Konva's drag already placed it visually until this refresh
      // lands -- a brief visual settle if the server snapped it elsewhere is
      // expected, not a bug to engineer away.
      const fresh = await fetchMap(props.map.id)
      emit('map-updated', fresh)
    } catch (err) {
      emit('error', err)
    }
  }

  async function handleMapChanged() {
    try {
      const fresh = await fetchMap(props.map.id)
      emit('map-updated', fresh)
    } catch (err) {
      emit('error', err)
    }
  }

  function repositionToken(tokenId: number, x: number, y: number) {
    const node = tokenNodes.get(tokenId)
    if (node) node.position({ x, y })
    const label = tokenLabels.get(tokenId)
    if (label) {
      const size = label.width() ?? 0
      label.position({ x: x - size / 2, y: y + size / 2 + 2 })
    }
    tokensLayer?.batchDraw()
  }

  function stagePointer(): { x: number; y: number } | null {
    const pos = stage?.getPointerPosition()
    return pos ? { x: pos.x, y: pos.y } : null
  }

  function onStageMouseDown() {
    const pos = stagePointer()
    if (!pos) return
    if (props.tool === 'measure') {
      if (measurePoints.length === 0) measurePoints.push([pos.x, pos.y])
      measuring = true
    } else if (props.tool === 'reveal-rect' || props.tool === 'hide-rect') {
      rectStart = pos
    }
  }

  function onStageMouseMove() {
    const pos = stagePointer()
    if (!pos) return
    if (props.tool === 'measure' && measuring && measurePoints.length > 0) {
      drawMeasurePreview(pos)
    } else if ((props.tool === 'reveal-rect' || props.tool === 'hide-rect') && rectStart) {
      drawRectPreview(rectStart, pos)
    }
  }

  function onStageMouseUp() {
    const pos = stagePointer()
    if (props.tool === 'measure') {
      if (measuring && pos) measurePoints.push([pos.x, pos.y])
      measuring = false
    } else if ((props.tool === 'reveal-rect' || props.tool === 'hide-rect') && rectStart && pos) {
      const start = rectStart
      rectStart = null
      interactionLayer?.destroyChildren()
      interactionLayer?.batchDraw()
      // Fires exactly once, on mouse-up -- never on intermediate mousemove,
      // which would flood the API with requests.
      void commitRect(start, pos)
    }
  }

  function drawMeasurePreview(current: { x: number; y: number }) {
    if (!interactionLayer) return
    interactionLayer.destroyChildren()
    const allPoints: Array<[number, number]> = [...measurePoints, [current.x, current.y]]
    interactionLayer.add(
      new Konva.Line({ points: allPoints.flat(), stroke: '#ffd700', strokeWidth: 2 }),
    )
    measureDistanceFt.value = pathDistance(
      allPoints,
      props.map.feet_per_square,
      props.map.diagonal_rule,
      props.map.grid_size_px,
    )
    interactionLayer.batchDraw()
  }

  function drawRectPreview(start: { x: number; y: number }, current: { x: number; y: number }) {
    if (!interactionLayer) return
    interactionLayer.destroyChildren()
    interactionLayer.add(
      new Konva.Rect({
        x: Math.min(start.x, current.x),
        y: Math.min(start.y, current.y),
        width: Math.abs(current.x - start.x),
        height: Math.abs(current.y - start.y),
        stroke: '#ffd700',
        dash: [4, 4],
      }),
    )
    interactionLayer.batchDraw()
  }

  async function commitRect(start: { x: number; y: number }, current: { x: number; y: number }) {
    const x = Math.min(start.x, current.x)
    const y = Math.min(start.y, current.y)
    const w = Math.abs(current.x - start.x)
    const h = Math.abs(current.y - start.y)
    if (w <= 0 || h <= 0) return
    try {
      const op = props.tool === 'reveal-rect' ? 'reveal' : 'hide'
      const fresh = await addFogOp(props.map.id, op, { type: 'rect', x, y, w, h })
      emit('map-updated', fresh)
    } catch (err) {
      emit('error', err)
    }
  }

  function clearMeasurement() {
    measurePoints = []
    measureDistanceFt.value = null
    interactionLayer?.destroyChildren()
    interactionLayer?.batchDraw()
  }

  watch(
    () => props.tool,
    (tool) => {
      tokenNodes.forEach((node) => node.draggable(tool === 'select'))
      clearMeasurement()
      rectStart = null
    },
  )

  watch(
    () => props.map,
    () => renderAll(),
    { deep: true },
  )

  onMounted(() => {
    if (!containerEl.value) return
    stage = new Konva.Stage({
      container: containerEl.value,
      width: stageWidth(),
      height: stageHeight(),
    })
    backgroundLayer = new Konva.Layer()
    gridLayer = new Konva.Layer()
    tokensLayer = new Konva.Layer()
    fogLayer = new Konva.Layer()
    interactionLayer = new Konva.Layer()
    stage.add(backgroundLayer, gridLayer, tokensLayer, fogLayer, interactionLayer)

    stage.on('mousedown', onStageMouseDown)
    stage.on('mousemove', onStageMouseMove)
    stage.on('mouseup', onStageMouseUp)

    renderAll()

    disconnectSocket = connectMapSocket(props.map.id, {
      onMapChanged: () => void handleMapChanged(),
      onTokenMove: repositionToken,
    })
  })

  onBeforeUnmount(() => {
    disconnectSocket?.()
    stage?.destroy()
  })

  defineExpose({ handleTokenDragEnd, clearMeasurement })
</script>

<template>
  <div class="map-canvas">
    <div v-if="tool === 'measure'" class="map-canvas__readout">
      <span>Distance: {{ measureDistanceFt ?? 0 }} ft</span>
      <button type="button" @click="clearMeasurement">Clear</button>
    </div>
    <div ref="containerEl" class="map-canvas__stage"></div>
  </div>
</template>
