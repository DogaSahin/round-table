<script setup lang="ts">
  import { onMounted, ref } from 'vue'
  import { ApiError } from '@/api/client'
  import {
    activateMap,
    createMap,
    deleteMap,
    fetchMap,
    fogHideAll,
    fogRevealAll,
    listMaps,
    stopSharing,
    uploadMapImage,
    type MapDetailOut,
    type MapListItemOut,
  } from './api'
  import MapCanvas from './MapCanvas.vue'

  type Tool = 'select' | 'measure' | 'reveal-rect' | 'hide-rect'

  const maps = ref<MapListItemOut[]>([])
  const selected = ref<MapDetailOut | null>(null)
  const newMapName = ref('')
  const errorMessage = ref<string | null>(null)
  const tool = ref<Tool>('select')
  const snapEnabled = ref(true)

  function handleError(err: unknown) {
    errorMessage.value = err instanceof ApiError ? err.message : 'Unknown error'
  }

  async function loadMaps() {
    maps.value = await listMaps()
  }

  async function selectMap(mapId: number) {
    errorMessage.value = null
    try {
      selected.value = await fetchMap(mapId)
    } catch (err) {
      handleError(err)
    }
  }

  async function submitCreateMap() {
    errorMessage.value = null
    try {
      const created = await createMap(newMapName.value)
      newMapName.value = ''
      await loadMaps()
      selected.value = created
    } catch (err) {
      handleError(err)
    }
  }

  async function removeMap(mapId: number) {
    errorMessage.value = null
    try {
      await deleteMap(mapId)
      if (selected.value?.id === mapId) selected.value = null
      await loadMaps()
    } catch (err) {
      handleError(err)
    }
  }

  async function activate(mapId: number) {
    errorMessage.value = null
    try {
      await activateMap(mapId)
      await loadMaps()
      if (selected.value?.id === mapId) selected.value = await fetchMap(mapId)
    } catch (err) {
      handleError(err)
    }
  }

  async function submitStopSharing() {
    errorMessage.value = null
    try {
      await stopSharing()
      await loadMaps()
    } catch (err) {
      handleError(err)
    }
  }

  async function submitImageUpload(event: Event) {
    if (selected.value === null) return
    const input = event.target as HTMLInputElement
    const file = input.files?.[0]
    if (!file) return
    errorMessage.value = null
    try {
      selected.value = await uploadMapImage(selected.value.id, file)
    } catch (err) {
      handleError(err)
    } finally {
      input.value = ''
    }
  }

  async function submitRevealAll() {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      selected.value = await fogRevealAll(selected.value.id)
    } catch (err) {
      handleError(err)
    }
  }

  async function submitHideAll() {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      selected.value = await fogHideAll(selected.value.id)
    } catch (err) {
      handleError(err)
    }
  }

  function onMapUpdated(map: MapDetailOut) {
    selected.value = map
  }

  onMounted(loadMaps)
</script>

<template>
  <section>
    <h1>Maps</h1>
    <p v-if="errorMessage">Error: {{ errorMessage }}</p>

    <form class="maps-create-form" @submit.prevent="submitCreateMap">
      <input v-model="newMapName" type="text" placeholder="Map name" />
      <button type="submit">New Map</button>
    </form>

    <ul>
      <li v-for="m in maps" :key="m.id">
        <button type="button" @click="selectMap(m.id)">
          {{ m.name }}{{ m.is_active ? ' [active]' : '' }}
        </button>
        <button type="button" @click="activate(m.id)">Share to Players</button>
        <button type="button" @click="removeMap(m.id)">Delete</button>
      </li>
    </ul>

    <button type="button" @click="submitStopSharing">Stop Sharing</button>

    <div v-if="selected">
      <h2>{{ selected.name }}</h2>

      <label>
        Upload map image
        <input type="file" accept="image/*" @change="submitImageUpload" />
      </label>

      <div class="maps-toolbar">
        <label v-for="t in ['select', 'measure', 'reveal-rect', 'hide-rect'] as Tool[]" :key="t">
          <input v-model="tool" type="radio" :value="t" :name="'tool'" />
          {{ t }}
        </label>

        <label>
          <input v-model="snapEnabled" type="checkbox" />
          Snap to grid
        </label>

        <button type="button" @click="submitRevealAll">Reveal All</button>
        <button type="button" @click="submitHideAll">Hide All</button>
      </div>

      <MapCanvas
        :key="selected.id"
        :map="selected"
        :tool="tool"
        :snap-enabled="snapEnabled"
        @map-updated="onMapUpdated"
        @error="handleError"
      />
    </div>
  </section>
</template>
