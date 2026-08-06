<script setup lang="ts">
  // frontend/src/components/TextInput.vue
  withDefaults(
    defineProps<{
      type?: 'text' | 'number'
      placeholder?: string
      name?: string
      error?: string
    }>(),
    {
      type: 'text',
    },
  )

  const model = defineModel<string | number | null>({ required: true })
</script>

<template>
  <div class="text-input">
    <!-- Two branches, not one input with a dynamic :type: the .number v-model modifier is a
         compile-time template feature and cannot be toggled by a runtime prop. -->
    <input
      v-if="type === 'number'"
      v-model.number="model"
      type="number"
      :name="name"
      :placeholder="placeholder"
      class="text-input__field"
    />
    <input
      v-else
      v-model="model"
      type="text"
      :name="name"
      :placeholder="placeholder"
      class="text-input__field"
    />
    <span v-if="error" class="text-input__error">{{ error }}</span>
  </div>
</template>

<style scoped>
  .text-input {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .text-input__field {
    font-family: var(--font-body);
    font-size: var(--text-sm);
    color: var(--color-text);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: var(--space-2) var(--space-3);
    transition: border-color var(--transition-fast);
  }

  .text-input__field:focus {
    outline: none;
    border-color: var(--color-accent);
  }

  .text-input__error {
    color: var(--color-danger);
    font-size: var(--text-xs);
  }
</style>
