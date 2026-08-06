<script setup lang="ts">
  // frontend/src/modules/bestiary/TagListField.vue
  import { ref, watch } from 'vue'

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
        @change="onSelectChange(index, ($event.target as HTMLSelectElement).value)"
      >
        <option value="" disabled>Select…</option>
        <option v-for="opt in optionsFor(index)" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
        <option :value="CUSTOM_OPTION">Other (custom)...</option>
      </select>
      <input
        v-else
        :name="`${fieldName}-${index}`"
        type="text"
        :value="value"
        @input="setValue(index, ($event.target as HTMLInputElement).value)"
      />
      <button type="button" :aria-label="`Remove ${label} entry`" @click="removeRow(index)">
        ×
      </button>
    </div>
    <button type="button" @click="addRow">+ Add {{ label }}</button>
  </fieldset>
</template>

<style scoped>
  .tag-list-field__row {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
  }
</style>
