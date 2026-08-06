<script setup lang="ts">
  // frontend/src/components/SelectInput.vue
  defineProps<{
    options: { value: string | number; label: string }[]
    name?: string
  }>()

  const model = defineModel<string | number>({ required: true })
</script>

<template>
  <select v-model="model" :name="name" class="select-input">
    <option v-for="opt in options" :key="opt.value" :value="opt.value">
      {{ opt.label }}
    </option>
  </select>
</template>

<style scoped>
  .select-input {
    font-family: var(--font-body);
    font-size: var(--text-sm);
    color: var(--color-text);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: var(--space-2) var(--space-3);
    transition: border-color var(--transition-fast);
  }

  .select-input:focus {
    outline: none;
    border-color: var(--color-accent);
  }
</style>
