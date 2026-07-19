<script setup lang="ts">
  import { onMounted, ref } from 'vue'
  import { ApiError } from '@/api/client'
  import { fetchHistory, rollDice, type HistoryEntry, type RollResult } from './api'

  const expression = ref('')
  const lastResult = ref<RollResult | null>(null)
  const history = ref<HistoryEntry[]>([])
  const errorMessage = ref<string | null>(null)

  async function loadHistory() {
    history.value = await fetchHistory()
  }

  async function submitRoll() {
    errorMessage.value = null
    try {
      lastResult.value = await rollDice(expression.value)
      await loadHistory()
    } catch (err) {
      errorMessage.value = err instanceof ApiError ? err.message : 'Unknown error'
    }
  }

  onMounted(loadHistory)
</script>

<template>
  <section>
    <h1>Dice Roller</h1>
    <form @submit.prevent="submitRoll">
      <input v-model="expression" type="text" placeholder="e.g. 2d6+3" />
      <button type="submit">Roll</button>
    </form>

    <p v-if="errorMessage">Error: {{ errorMessage }}</p>
    <p v-if="lastResult">Total: {{ lastResult.total }}</p>

    <h2>History</h2>
    <ul>
      <li v-for="entry in history" :key="entry.id">{{ entry.expression }} = {{ entry.result }}</li>
    </ul>
  </section>
</template>
