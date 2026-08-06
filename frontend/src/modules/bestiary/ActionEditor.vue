<script setup lang="ts">
  // frontend/src/modules/bestiary/ActionEditor.vue
  import { ref } from 'vue'
  import type { AbilityName } from './api'
  import TextInput from '@/components/TextInput.vue'
  import Checkbox from '@/components/Checkbox.vue'
  import Button from '@/components/Button.vue'

  interface DamageRowState {
    dice: string
    damageType: string
  }

  interface ActionFormState {
    clientKey: string
    name: string
    description: string
    attackBonus: number | null
    reachOrRange: string
    target: string
    damage: DamageRowState[]
    hasSave: boolean
    saveAbility: AbilityName | null
    saveDc: number | null
    saveEffect: string
    recharge: string
    usesPerDay: number | null
    cost: number
    multiattackRefs: string[]
  }

  const SAVE_ABILITIES: AbilityName[] = [
    'strength',
    'dexterity',
    'constitution',
    'intelligence',
    'wisdom',
    'charisma',
  ]

  const DAMAGE_TYPE_CUSTOM_OPTION = '__custom__'

  const props = defineProps<{
    showCost: boolean
    otherActionNames: { clientKey: string; name: string }[]
    errors: Record<string, string>
    damageTypeOptions: { value: string; label: string }[]
  }>()

  const emit = defineEmits<{
    (e: 'remove'): void
  }>()

  const model = defineModel<ActionFormState>({ required: true })

  // Scalar/per-row fields below mutate `model.value` in place, relying on the parent binding the
  // same live reactive object via `v-model="form.actions[index]"` (not a copy); add/remove-row and
  // multiattack-toggle instead reassign `model.value` so `update:modelValue` actually fires.
  function isDamageTypeUnmatched(damageType: string): boolean {
    if (damageType === '') return false
    return !props.damageTypeOptions.some((opt) => opt.value === damageType)
  }

  const customDamageRows = ref<boolean[]>(
    model.value.damage.map((d) => isDamageTypeUnmatched(d.damageType)),
  )

  function addDamageRow() {
    model.value = {
      ...model.value,
      damage: [...model.value.damage, { dice: '', damageType: '' }],
    }
    customDamageRows.value.push(false)
  }

  function removeDamageRow(index: number) {
    model.value = {
      ...model.value,
      damage: model.value.damage.filter((_, i) => i !== index),
    }
    customDamageRows.value.splice(index, 1)
  }

  function damageTypeOptionsFor(index: number): { value: string; label: string }[] {
    const usedElsewhere = new Set(
      model.value.damage.filter((_, i) => i !== index).map((d) => d.damageType),
    )
    return props.damageTypeOptions.filter((opt) => !usedElsewhere.has(opt.value))
  }

  function onDamageTypeSelectChange(index: number, value: string) {
    if (value === DAMAGE_TYPE_CUSTOM_OPTION) {
      customDamageRows.value[index] = true
      model.value.damage[index].damageType = ''
    } else {
      customDamageRows.value[index] = false
      model.value.damage[index].damageType = value
    }
  }

  function toggleMultiattackRef(clientKey: string, checked: boolean) {
    const included = model.value.multiattackRefs.includes(clientKey)
    if (checked && !included) {
      model.value = {
        ...model.value,
        multiattackRefs: [...model.value.multiattackRefs, clientKey],
      }
    } else if (!checked && included) {
      model.value = {
        ...model.value,
        multiattackRefs: model.value.multiattackRefs.filter((k) => k !== clientKey),
      }
    }
  }
</script>

<template>
  <div class="action-editor">
    <label class="field-label">
      Name
      <TextInput v-model="model.name" name="name" :error="errors.name" />
    </label>

    <label class="field-label">
      Description
      <textarea
        v-model="model.description"
        name="description"
        class="action-editor__textarea"
      ></textarea>
      <span v-if="errors.description" class="field-error">{{ errors.description }}</span>
    </label>

    <label class="field-label">
      Attack Bonus
      <TextInput v-model="model.attackBonus" type="number" name="attackBonus" />
    </label>

    <label class="field-label">
      Reach or Range
      <TextInput v-model="model.reachOrRange" name="reachOrRange" />
    </label>

    <label class="field-label">
      Target
      <TextInput v-model="model.target" name="target" />
    </label>

    <fieldset class="action-editor__fieldset">
      <legend>Damage</legend>
      <div v-for="(row, index) in model.damage" :key="index" class="damage-row">
        <TextInput v-model="row.dice" :name="`damageDice-${index}`" placeholder="1d6" />
        <select
          v-if="!customDamageRows[index]"
          :name="`damageType-${index}`"
          :value="row.damageType"
          class="native-select"
          @change="onDamageTypeSelectChange(index, ($event.target as HTMLSelectElement).value)"
        >
          <option value="" disabled>Select…</option>
          <option v-for="opt in damageTypeOptionsFor(index)" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
          <option :value="DAMAGE_TYPE_CUSTOM_OPTION">Other (custom)...</option>
        </select>
        <TextInput v-else v-model="row.damageType" :name="`damageType-${index}`" />
        <Button variant="ghost" aria-label="Remove damage entry" @click="removeDamageRow(index)">
          ×
        </Button>
      </div>
      <Button variant="secondary" @click="addDamageRow">+ Add damage</Button>
    </fieldset>

    <Checkbox v-model="model.hasSave" name="hasSave">Has saving throw</Checkbox>
    <template v-if="model.hasSave">
      <label class="field-label">
        Ability
        <select v-model="model.saveAbility" name="saveAbility" class="native-select">
          <option :value="null" disabled>Select…</option>
          <option v-for="ability in SAVE_ABILITIES" :key="ability" :value="ability">
            {{ ability }}
          </option>
        </select>
        <span v-if="errors.saveAbility" class="field-error">{{ errors.saveAbility }}</span>
      </label>
      <label class="field-label">
        DC
        <TextInput v-model="model.saveDc" type="number" name="saveDc" :error="errors.saveDc" />
      </label>
      <label class="field-label">
        Effect on save
        <TextInput v-model="model.saveEffect" name="saveEffect" :error="errors.saveEffect" />
      </label>
    </template>

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

    <label v-if="showCost" class="field-label">
      Cost
      <TextInput v-model="model.cost" type="number" name="cost" :error="errors.cost" />
    </label>

    <fieldset v-if="otherActionNames.length > 0" class="action-editor__fieldset">
      <legend>Multiattack References</legend>
      <Checkbox
        v-for="opt in otherActionNames"
        :key="opt.clientKey"
        :name="`multiattack-${opt.clientKey}`"
        :model-value="model.multiattackRefs.includes(opt.clientKey)"
        @update:model-value="(checked) => toggleMultiattackRef(opt.clientKey, checked)"
      >
        {{ opt.name || '(unnamed action)' }}
      </Checkbox>
    </fieldset>

    <Button variant="danger" @click="emit('remove')">Remove action</Button>
  </div>
</template>

<style scoped>
  .action-editor {
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

  .action-editor__fieldset {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--space-3);
  }

  .action-editor__fieldset legend {
    font-family: var(--font-heading);
    color: var(--color-text);
    padding: 0 var(--space-2);
  }

  .action-editor__textarea {
    font-family: var(--font-body);
    font-size: var(--text-sm);
    color: var(--color-text);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: var(--space-2) var(--space-3);
    resize: vertical;
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

  .damage-row {
    display: flex;
    align-items: flex-start;
    gap: var(--space-2);
  }

  .field-error {
    color: var(--color-danger);
    display: block;
    font-size: var(--text-xs);
  }
</style>
