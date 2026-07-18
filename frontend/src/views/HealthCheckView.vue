<script setup lang="ts">
  import { onMounted, ref } from 'vue'
  import { apiFetch, ApiError } from '@/api/client'

  const status = ref<string | null>(null)
  const errorMessage = ref<string | null>(null)

  onMounted(async () => {
    try {
      const result = await apiFetch<{ status: string }>('/health')
      status.value = result.status
    } catch (err) {
      errorMessage.value = err instanceof ApiError ? err.message : 'Unknown error'
    }
  })
</script>

<template>
  <section>
    <h1>Backend health check</h1>
    <p v-if="status">Status: {{ status }}</p>
    <p v-else-if="errorMessage">Error: {{ errorMessage }}</p>
    <p v-else>Checking…</p>
  </section>
</template>
