<script setup lang="ts">
  // frontend/src/modules/bestiary/SpecialAbilityEditor.vue
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
    <label>
      Name
      <input v-model="model.name" type="text" name="name" />
      <span v-if="errors.name" class="field-error">{{ errors.name }}</span>
    </label>

    <label>
      Description
      <textarea v-model="model.description" name="description"></textarea>
      <span v-if="errors.description" class="field-error">{{ errors.description }}</span>
    </label>

    <label>
      Recharge
      <input v-model="model.recharge" type="text" name="recharge" placeholder="5-6" />
    </label>

    <label>
      Uses per Day
      <input v-model.number="model.usesPerDay" type="number" name="usesPerDay" />
      <span v-if="errors.usesPerDay" class="field-error">{{ errors.usesPerDay }}</span>
    </label>

    <button type="button" @click="emit('remove')">Remove special ability</button>
  </div>
</template>

<style scoped>
  .special-ability-editor {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .field-error {
    color: #c00;
    display: block;
    font-size: 0.85rem;
  }
</style>
