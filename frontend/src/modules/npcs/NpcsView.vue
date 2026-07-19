<script setup lang="ts">
  import { onMounted, ref } from 'vue'
  import { ApiError } from '@/api/client'
  import { createNpc, deleteNpc, fetchNpc, listNpcs, type NpcDetail, type NpcListItem } from './api'

  const npcs = ref<NpcListItem[]>([])
  const selected = ref<NpcDetail | null>(null)
  const newName = ref('')
  const errorMessage = ref<string | null>(null)

  function handleError(err: unknown) {
    errorMessage.value = err instanceof ApiError ? err.message : 'Unknown error'
  }

  async function loadNpcs() {
    npcs.value = await listNpcs()
  }

  async function selectNpc(npcId: number) {
    errorMessage.value = null
    try {
      selected.value = await fetchNpc(npcId)
    } catch (err) {
      handleError(err)
    }
  }

  async function submitCreate() {
    errorMessage.value = null
    try {
      const created = await createNpc(newName.value)
      newName.value = ''
      await loadNpcs()
      selected.value = created
    } catch (err) {
      handleError(err)
    }
  }

  async function remove(npcId: number) {
    errorMessage.value = null
    try {
      await deleteNpc(npcId)
      if (selected.value?.id === npcId) selected.value = null
      await loadNpcs()
    } catch (err) {
      handleError(err)
    }
  }

  onMounted(loadNpcs)
</script>

<template>
  <section>
    <h1>NPCs</h1>
    <p v-if="errorMessage">Error: {{ errorMessage }}</p>

    <form @submit.prevent="submitCreate">
      <input v-model="newName" type="text" placeholder="NPC name" />
      <button type="submit">New NPC</button>
    </form>

    <ul>
      <li v-for="n in npcs" :key="n.id">
        <button type="button" @click="selectNpc(n.id)">{{ n.name }} ({{ n.disposition }})</button>
      </li>
    </ul>

    <div v-if="selected">
      <h2>{{ selected.name }}</h2>
      <p>{{ selected.disposition }}</p>
      <p v-if="selected.faction_id">Faction #{{ selected.faction_id }}</p>
      <p v-if="selected.motivation">{{ selected.motivation }}</p>
      <p v-if="selected.voice">{{ selected.voice }}</p>
      <p v-if="selected.secrets">Secrets: {{ selected.secrets }}</p>
      <p>{{ selected.player_visible ? 'Visible to players' : 'DM only' }}</p>
      <button type="button" @click="remove(selected.id)">Delete</button>
    </div>
  </section>
</template>
