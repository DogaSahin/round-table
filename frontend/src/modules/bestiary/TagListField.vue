<script setup lang="ts">
  // frontend/src/modules/bestiary/TagListField.vue
  import { ref, watch } from 'vue'
  import TextInput from '@/components/TextInput.vue'
  import Button from '@/components/Button.vue'

  interface TagOption {
    value: string
    label: string
  }

  const props = defineProps<{
    modelValue: string[]
    label: string
    fieldName: string
    options?: TagOption[]
  }>()

  const emit = defineEmits<{
    (e: 'update:modelValue', value: string[]): void
  }>()

  const CUSTOM_OPTION = '__custom__'

  function isUnmatched(value: string): boolean {
    if (!props.options) return true
    if (value === '') return false
    return !props.options.some((opt) => opt.value === value)
  }

  const customRows = ref<boolean[]>(props.modelValue.map((value) => isUnmatched(value)))

  // Re-derive custom-row flags only when the array's length changes out from under us (the
  // parent replacing `modelValue` wholesale after an async fetch resolves). Our own edits below
  // always update customRows in lockstep with the emitted array, so a length match here means
  // this watcher fired for our own change and must NOT recompute — recomputing on every change
  // would incorrectly flip a row mid-"Other (custom)" entry (value '') back to dropdown mode.
  watch(
    () => props.modelValue,
    (newValue) => {
      if (newValue.length !== customRows.value.length) {
        customRows.value = newValue.map((value) => isUnmatched(value))
      }
    },
  )

  function optionsFor(index: number): TagOption[] {
    if (!props.options) return []
    const usedElsewhere = new Set(props.modelValue.filter((_, i) => i !== index))
    return props.options.filter((opt) => !usedElsewhere.has(opt.value))
  }

  function setValue(index: number, value: string) {
    const next = [...props.modelValue]
    next[index] = value
    emit('update:modelValue', next)
  }

  function onSelectChange(index: number, value: string) {
    if (value === CUSTOM_OPTION) {
      customRows.value[index] = true
      setValue(index, '')
    } else {
      customRows.value[index] = false
      setValue(index, value)
    }
  }

  function addRow() {
    customRows.value.push(false)
    emit('update:modelValue', [...props.modelValue, ''])
  }

  function removeRow(index: number) {
    customRows.value.splice(index, 1)
    emit(
      'update:modelValue',
      props.modelValue.filter((_, i) => i !== index),
    )
  }
</script>

<template>
  <fieldset class="tag-list-field">
    <legend>{{ label }}</legend>
    <div v-for="(value, index) in modelValue" :key="index" class="tag-list-field__row">
      <select
        v-if="options && !customRows[index]"
        :name="`${fieldName}-${index}`"
        :value="value"
        class="native-select"
        @change="onSelectChange(index, ($event.target as HTMLSelectElement).value)"
      >
        <option value="" disabled>Select…</option>
        <option v-for="opt in optionsFor(index)" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
        <option :value="CUSTOM_OPTION">Other (custom)...</option>
      </select>
      <TextInput
        v-else
        :name="`${fieldName}-${index}`"
        :model-value="value"
        @update:model-value="(next) => setValue(index, String(next))"
      />
      <Button variant="ghost" :aria-label="`Remove ${label} entry`" @click="removeRow(index)">
        ×
      </Button>
    </div>
    <Button variant="secondary" @click="addRow">+ Add {{ label }}</Button>
  </fieldset>
</template>

<style scoped>
  .tag-list-field {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--space-3);
  }

  .tag-list-field legend {
    font-family: var(--font-heading);
    color: var(--color-text);
    padding: 0 var(--space-2);
  }

  .native-select {
    font-family: var(--font-body);
    font-size: var(--text-sm);
    color: var(--color-text);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: var(--space-2) var(--space-3);
  }

  .tag-list-field__row {
    display: flex;
    align-items: flex-start;
    gap: var(--space-2);
  }
</style>
