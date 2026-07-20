<script setup lang="ts">
  import { onMounted, reactive, ref } from 'vue'
  import { ApiError } from '@/api/client'
  import {
    activateEncounter,
    addCombatant,
    applyCondition,
    createEncounter,
    damageCombatant,
    deleteCombatant,
    deleteEncounter,
    fetchEncounter,
    healCombatant,
    listEncounters,
    nextTurn,
    renameEncounter,
    reorder,
    setAc,
    sortByInitiative,
    toggleConcentration,
    updateCombatant,
    type Combatant,
    type EncounterDetail,
    type EncounterListItem,
  } from './api'

  const CONDITIONS = [
    'blinded',
    'charmed',
    'deafened',
    'frightened',
    'grappled',
    'incapacitated',
    'invisible',
    'paralyzed',
    'petrified',
    'poisoned',
    'prone',
    'restrained',
    'stunned',
    'unconscious',
  ]

  const encounters = ref<EncounterListItem[]>([])
  const selected = ref<EncounterDetail | null>(null)
  const newEncounterName = ref('')
  const renameName = ref('')
  const errorMessage = ref<string | null>(null)

  const damageAmounts = reactive<Record<number, number>>({})
  const healAmounts = reactive<Record<number, number>>({})
  const acInputs = reactive<Record<number, number | null>>({})
  const customConditions = reactive<Record<number, string>>({})

  const newCombatantName = ref('')
  const newCombatantInitiative = ref(0)
  const newCombatantHpMax = ref(0)
  const newCombatantHpCurrent = ref(0)
  const newCombatantAc = ref('')
  const newCombatantIsPc = ref(false)
  const newCombatantVisibleToPlayers = ref(false)
  const newCombatantNpcId = ref('')

  function handleError(err: unknown) {
    errorMessage.value = err instanceof ApiError ? err.message : 'Unknown error'
  }

  function checkboxValue(event: Event): boolean {
    return (event.target as HTMLInputElement).checked
  }

  async function loadEncounters() {
    encounters.value = await listEncounters()
  }

  async function selectEncounter(encounterId: number) {
    errorMessage.value = null
    try {
      selected.value = await fetchEncounter(encounterId)
      renameName.value = selected.value.name
    } catch (err) {
      handleError(err)
    }
  }

  async function refreshSelected() {
    if (selected.value === null) return
    selected.value = await fetchEncounter(selected.value.id)
  }

  async function submitCreateEncounter() {
    errorMessage.value = null
    try {
      const created = await createEncounter(newEncounterName.value)
      newEncounterName.value = ''
      await loadEncounters()
      selected.value = created
      renameName.value = created.name
    } catch (err) {
      handleError(err)
    }
  }

  async function submitRename() {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await renameEncounter(selected.value.id, renameName.value)
      await refreshSelected()
      await loadEncounters()
    } catch (err) {
      handleError(err)
    }
  }

  async function activate(encounterId: number) {
    errorMessage.value = null
    try {
      await activateEncounter(encounterId)
      await loadEncounters()
      if (selected.value?.id === encounterId) {
        await refreshSelected()
      }
    } catch (err) {
      handleError(err)
    }
  }

  async function removeEncounter(encounterId: number) {
    errorMessage.value = null
    try {
      await deleteEncounter(encounterId)
      if (selected.value?.id === encounterId) selected.value = null
      await loadEncounters()
    } catch (err) {
      handleError(err)
    }
  }

  async function submitSortByInitiative() {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await sortByInitiative(selected.value.id)
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  async function submitNextTurn() {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await nextTurn(selected.value.id)
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  async function submitReorder(order: number[]) {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await reorder(selected.value.id, order)
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  function moveUp(index: number) {
    if (selected.value === null || index <= 0) return
    const ids = selected.value.combatants.map((c) => c.id)
    ;[ids[index - 1], ids[index]] = [ids[index], ids[index - 1]]
    void submitReorder(ids)
  }

  function moveDown(index: number) {
    if (selected.value === null || index >= selected.value.combatants.length - 1) return
    const ids = selected.value.combatants.map((c) => c.id)
    ;[ids[index], ids[index + 1]] = [ids[index + 1], ids[index]]
    void submitReorder(ids)
  }

  async function submitAddCombatant() {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await addCombatant(selected.value.id, {
        name: newCombatantName.value,
        initiative: newCombatantInitiative.value,
        hp_current: newCombatantHpCurrent.value,
        hp_max: newCombatantHpMax.value,
        ac: newCombatantAc.value.trim() === '' ? null : Number(newCombatantAc.value),
        is_pc: newCombatantIsPc.value,
        visible_to_players: newCombatantVisibleToPlayers.value,
        npc_id: newCombatantNpcId.value.trim() === '' ? null : Number(newCombatantNpcId.value),
      })
      newCombatantName.value = ''
      newCombatantInitiative.value = 0
      newCombatantHpMax.value = 0
      newCombatantHpCurrent.value = 0
      newCombatantAc.value = ''
      newCombatantIsPc.value = false
      newCombatantVisibleToPlayers.value = false
      newCombatantNpcId.value = ''
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  async function removeCombatant(combatantId: number) {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await deleteCombatant(combatantId)
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  async function submitDamage(combatantId: number) {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await damageCombatant(combatantId, damageAmounts[combatantId] ?? 0)
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  async function submitHeal(combatantId: number) {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await healCombatant(combatantId, healAmounts[combatantId] ?? 0)
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  async function submitSetAc(combatantId: number) {
    if (selected.value === null) return
    errorMessage.value = null
    const value = acInputs[combatantId]
    try {
      await setAc(combatantId, typeof value === 'number' && !Number.isNaN(value) ? value : null)
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  async function submitTogglePc(combatantId: number, value: boolean) {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await updateCombatant(combatantId, { is_pc: value })
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  async function submitToggleVisible(combatantId: number, value: boolean) {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await updateCombatant(combatantId, { visible_to_players: value })
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  async function toggleCondition(c: Combatant, condition: string) {
    if (selected.value === null) return
    errorMessage.value = null
    const op = c.conditions.includes(condition) ? 'remove' : 'add'
    try {
      await applyCondition(c.id, condition, op)
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  async function submitCustomCondition(combatantId: number) {
    if (selected.value === null) return
    const name = (customConditions[combatantId] ?? '').trim()
    if (name === '') return
    errorMessage.value = null
    try {
      await applyCondition(combatantId, name, 'add')
      customConditions[combatantId] = ''
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  async function submitToggleConcentration(combatantId: number) {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await toggleConcentration(combatantId)
      await refreshSelected()
    } catch (err) {
      handleError(err)
    }
  }

  onMounted(loadEncounters)
</script>

<template>
  <section>
    <h1>Combat</h1>
    <p v-if="errorMessage">Error: {{ errorMessage }}</p>

    <form class="combat-create-form" @submit.prevent="submitCreateEncounter">
      <input v-model="newEncounterName" type="text" placeholder="Encounter name" />
      <button type="submit">New Encounter</button>
    </form>

    <ul>
      <li v-for="e in encounters" :key="e.id">
        <button type="button" @click="selectEncounter(e.id)">
          {{ e.name }} (round {{ e.round }}){{ e.is_active ? ' [active]' : '' }}
        </button>
        <button type="button" @click="activate(e.id)">Activate</button>
        <button type="button" @click="removeEncounter(e.id)">Delete</button>
      </li>
    </ul>

    <div v-if="selected">
      <h2>{{ selected.name }}</h2>
      <p>Round {{ selected.round }}</p>

      <form class="combat-rename-form" @submit.prevent="submitRename">
        <input v-model="renameName" type="text" placeholder="Encounter name" />
        <button type="submit">Rename</button>
      </form>

      <button type="button" data-sort-initiative @click="submitSortByInitiative">
        Sort by Initiative
      </button>
      <button type="button" data-next-turn @click="submitNextTurn">Next Turn</button>

      <ul class="combatant-list">
        <li
          v-for="(c, index) in selected.combatants"
          :key="c.id"
          :data-combatant-id="c.id"
          class="combatant-row"
          :class="{ 'combatant-row--active': c.id === selected.active_combatant_id }"
        >
          <strong>{{ c.name }}</strong>
          <span v-if="c.id === selected.active_combatant_id" class="combatant-row__marker">
            (Active)
          </span>
          <span>Init: {{ c.initiative }}</span>
          <span>HP: {{ c.hp_current }}/{{ c.hp_max }}</span>

          <input v-model.number="damageAmounts[c.id]" type="number" :data-damage-input="c.id" />
          <button type="button" :data-damage-button="c.id" @click="submitDamage(c.id)">
            Damage
          </button>

          <input v-model.number="healAmounts[c.id]" type="number" :data-heal-input="c.id" />
          <button type="button" :data-heal-button="c.id" @click="submitHeal(c.id)">Heal</button>

          <span>AC: {{ c.ac ?? '-' }}</span>
          <input v-model.number="acInputs[c.id]" type="number" :data-ac-input="c.id" />
          <button type="button" @click="submitSetAc(c.id)">Set AC</button>

          <label>
            <input
              type="checkbox"
              :checked="c.is_pc"
              @change="submitTogglePc(c.id, checkboxValue($event))"
            />
            PC
          </label>
          <label>
            <input
              type="checkbox"
              :checked="c.visible_to_players"
              @change="submitToggleVisible(c.id, checkboxValue($event))"
            />
            Visible to players
          </label>

          <div class="combatant-row__conditions">
            <button
              v-for="condition in CONDITIONS"
              :key="condition"
              type="button"
              class="condition-chip"
              :class="{ 'condition-chip--active': c.conditions.includes(condition) }"
              @click="toggleCondition(c, condition)"
            >
              {{ condition }}
            </button>
          </div>
          <form class="combat-condition-form" @submit.prevent="submitCustomCondition(c.id)">
            <input v-model="customConditions[c.id]" type="text" placeholder="Custom condition" />
            <button type="submit">Add Condition</button>
          </form>

          <button type="button" @click="submitToggleConcentration(c.id)">
            {{ c.concentration ? 'Concentrating' : 'Concentration' }}
          </button>

          <button type="button" :disabled="index === 0" @click="moveUp(index)">Move Up</button>
          <button
            type="button"
            :disabled="index === selected.combatants.length - 1"
            @click="moveDown(index)"
          >
            Move Down
          </button>

          <button type="button" @click="removeCombatant(c.id)">Delete</button>
        </li>
      </ul>

      <form class="combat-add-combatant-form" @submit.prevent="submitAddCombatant">
        <input v-model="newCombatantName" type="text" placeholder="Combatant name" />
        <input v-model.number="newCombatantInitiative" type="number" placeholder="Initiative" />
        <input v-model.number="newCombatantHpMax" type="number" placeholder="HP max" />
        <input v-model.number="newCombatantHpCurrent" type="number" placeholder="HP current" />
        <input v-model="newCombatantAc" type="number" placeholder="AC" />
        <label>
          <input v-model="newCombatantIsPc" type="checkbox" />
          PC
        </label>
        <label>
          <input v-model="newCombatantVisibleToPlayers" type="checkbox" />
          Visible to players
        </label>
        <input v-model="newCombatantNpcId" type="number" placeholder="NPC id (optional)" />
        <button type="submit">Add Combatant</button>
      </form>
    </div>
  </section>
</template>
