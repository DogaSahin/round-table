<script setup lang="ts">
  import { onMounted, ref } from 'vue'
  import { ApiError } from '@/api/client'
  import {
    activateSession,
    addLog,
    createSession,
    deleteSession,
    fetchSession,
    listSessions,
    type SessionDetail,
    type SessionListItem,
  } from './api'

  const sessions = ref<SessionListItem[]>([])
  const selected = ref<SessionDetail | null>(null)
  const newTitle = ref('')
  const logText = ref('')
  const logTag = ref('none')
  const errorMessage = ref<string | null>(null)

  function handleError(err: unknown) {
    errorMessage.value = err instanceof ApiError ? err.message : 'Unknown error'
  }

  async function loadSessions() {
    sessions.value = await listSessions()
  }

  async function selectSession(sessionId: number) {
    errorMessage.value = null
    try {
      selected.value = await fetchSession(sessionId)
    } catch (err) {
      handleError(err)
    }
  }

  async function submitCreate() {
    errorMessage.value = null
    try {
      const created = await createSession(newTitle.value)
      newTitle.value = ''
      await loadSessions()
      selected.value = created
    } catch (err) {
      handleError(err)
    }
  }

  async function submitLog() {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await addLog(selected.value.id, logText.value, logTag.value)
      logText.value = ''
      selected.value = await fetchSession(selected.value.id)
    } catch (err) {
      handleError(err)
    }
  }

  async function activate(sessionId: number) {
    errorMessage.value = null
    try {
      selected.value = await activateSession(sessionId)
      await loadSessions()
    } catch (err) {
      handleError(err)
    }
  }

  async function remove(sessionId: number) {
    errorMessage.value = null
    try {
      await deleteSession(sessionId)
      if (selected.value?.id === sessionId) selected.value = null
      await loadSessions()
    } catch (err) {
      handleError(err)
    }
  }

  onMounted(loadSessions)
</script>

<template>
  <section>
    <h1>Sessions</h1>
    <p v-if="errorMessage">Error: {{ errorMessage }}</p>

    <form @submit.prevent="submitCreate">
      <input v-model="newTitle" type="text" placeholder="Session title" />
      <button type="submit">New Session</button>
    </form>

    <ul>
      <li v-for="s in sessions" :key="s.id">
        <button type="button" @click="selectSession(s.id)">
          #{{ s.number }} {{ s.title }} ({{ s.status }})
        </button>
        <button v-if="s.status !== 'active'" type="button" @click="activate(s.id)">Activate</button>
        <button type="button" @click="remove(s.id)">Delete</button>
      </li>
    </ul>

    <div v-if="selected">
      <h2>#{{ selected.number }} {{ selected.title }}</h2>
      <p>{{ selected.date }} — {{ selected.status }}</p>
      <p v-if="selected.summary">{{ selected.summary }}</p>

      <form @submit.prevent="submitLog">
        <input v-model="logText" type="text" placeholder="Log entry" />
        <select v-model="logTag">
          <option value="none">None</option>
          <option value="combat">Combat</option>
          <option value="roleplay">Roleplay</option>
          <option value="loot">Loot</option>
          <option value="thread">Thread</option>
        </select>
        <button type="submit">Add</button>
      </form>

      <ul>
        <li v-for="log in selected.logs" :key="log.id">[{{ log.tag }}] {{ log.text }}</li>
      </ul>
    </div>
  </section>
</template>
