<script setup lang="ts">
  // frontend/src/modules/bestiary/SpecialAbilityEditor.vue
  import TextInput from '@/components/TextInput.vue'
  import Button from '@/components/Button.vue'

  interface SpecialAbilityFormState {
    name: string
    description: string
    recharge: string
    usesPerDay: number | null
  }

  defineProps<{
    errors: Record<string, string>
  }>()

  const emit = defineEmits<{
    (e: 'remove'): void
  }>()

  const model = defineModel<SpecialAbilityFormState>({ required: true })
</script>

<template>
  <div class="special-ability-editor">
    <label class="field-label">
      Name
      <TextInput v-model="model.name" name="name" :error="errors.name" />
    </label>

    <label class="field-label">
      Description
      <textarea
        v-model="model.description"
        name="description"
        class="special-ability-editor__textarea"
      ></textarea>
      <span v-if="errors.description" class="field-error">{{ errors.description }}</span>
    </label>

    <label class="field-label">
      Recharge
      <TextInput v-model="model.recharge" name="recharge" placeholder="5-6" />
    </label>

    <label class="field-label">
      Uses per Day
      <TextInput
        v-model="model.usesPerDay"
        type="number"
        name="usesPerDay"
        :error="errors.usesPerDay"
      />
    </label>

    <Button variant="danger" @click="emit('remove')">Remove special ability</Button>
  </div>
</template>

<style scoped>
  .special-ability-editor {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--space-3);
  }

  .field-label {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
    font-family: var(--font-body);
    font-size: var(--text-sm);
    color: var(--color-text-muted);
  }

  .special-ability-editor__textarea {
    font-family: var(--font-body);
    font-size: var(--text-sm);
    color: var(--color-text);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: var(--space-2) var(--space-3);
    resize: vertical;
  }

  .field-error {
    color: var(--color-danger);
    display: block;
    font-size: var(--text-xs);
  }
</style>
