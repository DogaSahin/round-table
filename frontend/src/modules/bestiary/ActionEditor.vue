<script setup lang="ts">
  // frontend/src/modules/bestiary/ActionEditor.vue
  import { ref } from 'vue'
  import type { AbilityName } from './api'

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
      Attack Bonus
      <input v-model.number="model.attackBonus" type="number" name="attackBonus" />
    </label>

    <label>
      Reach or Range
      <input v-model="model.reachOrRange" type="text" name="reachOrRange" />
    </label>

    <label>
      Target
      <input v-model="model.target" type="text" name="target" />
    </label>

    <fieldset>
      <legend>Damage</legend>
      <div v-for="(row, index) in model.damage" :key="index" class="damage-row">
        <input v-model="row.dice" type="text" :name="`damageDice-${index}`" placeholder="1d6" />
        <select
          v-if="!customDamageRows[index]"
          :name="`damageType-${index}`"
          :value="row.damageType"
          @change="onDamageTypeSelectChange(index, ($event.target as HTMLSelectElement).value)"
        >
          <option value="" disabled>Select…</option>
          <option v-for="opt in damageTypeOptionsFor(index)" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
          <option :value="DAMAGE_TYPE_CUSTOM_OPTION">Other (custom)...</option>
        </select>
        <input v-else v-model="row.damageType" type="text" :name="`damageType-${index}`" />
        <button type="button" aria-label="Remove damage entry" @click="removeDamageRow(index)">
          ×
        </button>
      </div>
      <button type="button" @click="addDamageRow">+ Add damage</button>
    </fieldset>

    <label>
      <input v-model="model.hasSave" type="checkbox" name="hasSave" />
      Has saving throw
    </label>
    <template v-if="model.hasSave">
      <label>
        Ability
        <select v-model="model.saveAbility" name="saveAbility">
          <option :value="null" disabled>Select…</option>
          <option v-for="ability in SAVE_ABILITIES" :key="ability" :value="ability">
            {{ ability }}
          </option>
        </select>
        <span v-if="errors.saveAbility" class="field-error">{{ errors.saveAbility }}</span>
      </label>
      <label>
        DC
        <input v-model.number="model.saveDc" type="number" name="saveDc" />
        <span v-if="errors.saveDc" class="field-error">{{ errors.saveDc }}</span>
      </label>
      <label>
        Effect on save
        <input v-model="model.saveEffect" type="text" name="saveEffect" />
        <span v-if="errors.saveEffect" class="field-error">{{ errors.saveEffect }}</span>
      </label>
    </template>

    <label>
      Recharge
      <input v-model="model.recharge" type="text" name="recharge" placeholder="5-6" />
    </label>

    <label>
      Uses per Day
      <input v-model.number="model.usesPerDay" type="number" name="usesPerDay" />
      <span v-if="errors.usesPerDay" class="field-error">{{ errors.usesPerDay }}</span>
    </label>

    <label v-if="showCost">
      Cost
      <input v-model.number="model.cost" type="number" name="cost" />
      <span v-if="errors.cost" class="field-error">{{ errors.cost }}</span>
    </label>

    <fieldset v-if="otherActionNames.length > 0">
      <legend>Multiattack References</legend>
      <label v-for="opt in otherActionNames" :key="opt.clientKey">
        <input
          type="checkbox"
          :name="`multiattack-${opt.clientKey}`"
          :checked="model.multiattackRefs.includes(opt.clientKey)"
          @change="toggleMultiattackRef(opt.clientKey, ($event.target as HTMLInputElement).checked)"
        />
        {{ opt.name || '(unnamed action)' }}
      </label>
    </fieldset>

    <button type="button" @click="emit('remove')">Remove action</button>
  </div>
</template>

<style scoped>
  .action-editor {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .damage-row {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
  }

  .field-error {
    color: #c00;
    display: block;
    font-size: 0.85rem;
  }
</style>
