<script setup lang="ts">
  // frontend/src/components/Card.vue
</script>

<template>
  <div class="card">
    <slot />
  </div>
</template>

<style scoped>
  .card {
    background: var(--color-surface);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-card);
    padding: var(--space-4);
  }
</style>
