<script setup lang="ts">
  // frontend/src/components/Checkbox.vue
  defineProps<{
    name?: string
  }>()

  const model = defineModel<boolean>({ required: true })
</script>

<template>
  <label class="checkbox">
    <input v-model="model" type="checkbox" :name="name" class="checkbox__input" />
    <span class="checkbox__label"><slot /></span>
  </label>
</template>

<style scoped>
  .checkbox {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    font-family: var(--font-body);
    font-size: var(--text-sm);
    color: var(--color-text);
    cursor: pointer;
  }

  .checkbox__input {
    accent-color: var(--color-accent);
  }
</style>
