<script setup lang="ts">
  import { onMounted, ref } from 'vue'
  import { ApiError } from '@/api/client'
  import {
    addActivity,
    createClock,
    createFaction,
    deleteFaction,
    fetchFaction,
    fillClock,
    listFactions,
    type FactionDetail,
    type FactionListItem,
  } from './api'

  const factions = ref<FactionListItem[]>([])
  const selected = ref<FactionDetail | null>(null)
  const newName = ref('')
  const clockName = ref('')
  const clockSegments = ref(6)
  const activityEntry = ref('')
  const errorMessage = ref<string | null>(null)

  function handleError(err: unknown) {
    errorMessage.value = err instanceof ApiError ? err.message : 'Unknown error'
  }

  async function loadFactions() {
    factions.value = await listFactions()
  }

  async function selectFaction(factionId: number) {
    errorMessage.value = null
    try {
      selected.value = await fetchFaction(factionId)
    } catch (err) {
      handleError(err)
    }
  }

  async function submitCreate() {
    errorMessage.value = null
    try {
      const created = await createFaction(newName.value)
      newName.value = ''
      await loadFactions()
      selected.value = created
    } catch (err) {
      handleError(err)
    }
  }

  async function submitClock() {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await createClock(selected.value.id, clockName.value, clockSegments.value)
      clockName.value = ''
      selected.value = await fetchFaction(selected.value.id)
    } catch (err) {
      handleError(err)
    }
  }

  async function clickSegment(clockId: number, segment: number) {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await fillClock(clockId, segment)
      selected.value = await fetchFaction(selected.value.id)
    } catch (err) {
      handleError(err)
    }
  }

  async function submitActivity() {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await addActivity(selected.value.id, activityEntry.value)
      activityEntry.value = ''
      selected.value = await fetchFaction(selected.value.id)
    } catch (err) {
      handleError(err)
    }
  }

  async function remove(factionId: number) {
    errorMessage.value = null
    try {
      await deleteFaction(factionId)
      if (selected.value?.id === factionId) selected.value = null
      await loadFactions()
    } catch (err) {
      handleError(err)
    }
  }

  onMounted(loadFactions)
</script>

<template>
  <section>
    <h1>Factions</h1>
    <p v-if="errorMessage">Error: {{ errorMessage }}</p>

    <form @submit.prevent="submitCreate">
      <input v-model="newName" type="text" placeholder="Faction name" />
      <button type="submit">New Faction</button>
    </form>

    <ul>
      <li v-for="f in factions" :key="f.id">
        <button type="button" @click="selectFaction(f.id)">
          {{ f.name }} ({{ f.disposition }})
        </button>
        <button type="button" @click="remove(f.id)">Delete</button>
      </li>
    </ul>

    <div v-if="selected">
      <h2>{{ selected.name }}</h2>
      <p>{{ selected.disposition }}</p>
      <p v-if="selected.goals">{{ selected.goals }}</p>
      <p v-if="selected.description">{{ selected.description }}</p>

      <h3>Clocks</h3>
      <ul>
        <li v-for="clock in selected.clocks" :key="clock.id">
          {{ clock.name }} ({{ clock.filled }}/{{ clock.segments }})
          <button
            v-for="i in clock.segments"
            :key="i"
            type="button"
            data-clock-segment
            @click="clickSegment(clock.id, i - 1)"
          >
            {{ i <= clock.filled ? '●' : '○' }}
          </button>
        </li>
      </ul>
      <form @submit.prevent="submitClock">
        <input v-model="clockName" type="text" placeholder="Clock name" />
        <input v-model.number="clockSegments" type="number" min="2" max="12" />
        <button type="submit">Add Clock</button>
      </form>

      <h3>Activity</h3>
      <ul>
        <li v-for="a in selected.activity" :key="a.id">{{ a.entry }}</li>
      </ul>
      <form @submit.prevent="submitActivity">
        <input v-model="activityEntry" type="text" placeholder="Activity entry" />
        <button type="submit">Log</button>
      </form>
    </div>
  </section>
</template>
