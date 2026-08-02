<script setup lang="ts">
  // frontend/src/modules/bestiary/MonsterDetailModal.vue
  import { onBeforeUnmount, ref, watch } from 'vue'
  import {
    fetchMonster,
    formatChallengeRating,
    type AbilityName,
    type Action,
    type BestiaryMonsterDetail,
    type SavingThrowProficiency,
    type SkillProficiency,
    type SpecialAbility,
  } from './api'

  const props = defineProps<{
    monsterId: number | null
  }>()

  const emit = defineEmits<{
    (e: 'close'): void
    (e: 'edit', monsterId: number): void
    (e: 'error', err: unknown): void
  }>()

  const detail = ref<BestiaryMonsterDetail | null>(null)

  async function load(monsterId: number) {
    try {
      detail.value = await fetchMonster(monsterId)
    } catch (err) {
      emit('error', err)
    }
  }

  function onKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') emit('close')
  }

  function handleEdit() {
    if (props.monsterId !== null) emit('edit', props.monsterId)
  }

  watch(
    () => props.monsterId,
    (monsterId) => {
      detail.value = null
      if (monsterId !== null) {
        void load(monsterId)
        window.addEventListener('keydown', onKeydown)
      } else {
        window.removeEventListener('keydown', onKeydown)
      }
    },
    { immediate: true },
  )

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', onKeydown)
  })

  function formatBonus(bonus: number): string {
    return bonus >= 0 ? `+${bonus}` : `${bonus}`
  }

  const ABILITY_ABBREVIATIONS: Record<AbilityName, string> = {
    strength: 'STR',
    dexterity: 'DEX',
    constitution: 'CON',
    intelligence: 'INT',
    wisdom: 'WIS',
    charisma: 'CHA',
  }

  function formatSavingThrows(savingThrows: SavingThrowProficiency[]): string {
    return savingThrows
      .map((st) => `${ABILITY_ABBREVIATIONS[st.ability]} ${formatBonus(st.bonus)}`)
      .join(', ')
  }

  function formatSkills(skills: SkillProficiency[]): string {
    return skills.map((s) => `${s.skill} ${formatBonus(s.bonus)}`).join(', ')
  }

  function capitalize(text: string): string {
    return text.charAt(0).toUpperCase() + text.slice(1)
  }

  function formatActionSummary(action: Action, siblings: Action[]): string {
    const parts: string[] = []

    const attackParts: string[] = []
    if (action.attack_bonus !== null) {
      attackParts.push(`${formatBonus(action.attack_bonus)} to hit`)
    }
    if (action.reach_or_range) attackParts.push(action.reach_or_range)
    if (action.target) attackParts.push(action.target)
    if (attackParts.length > 0) parts.push(attackParts.join(', ') + '.')

    if (action.damage.length > 0) {
      const damageText = action.damage.map((d) => `${d.dice} ${d.damage_type}`).join(' plus ')
      parts.push(`Hit: ${damageText} damage.`)
    }

    if (action.save) {
      parts.push(
        `The target must succeed on a DC ${action.save.dc} ${capitalize(action.save.ability)} ` +
          `saving throw or ${action.save.effect_on_save}`,
      )
    }

    if (action.recharge) parts.push(`Recharge ${action.recharge}.`)
    if (action.uses_per_day !== null) parts.push(`${action.uses_per_day}/day.`)

    if (action.multiattack_refs.length > 0) {
      const names = action.multiattack_refs
        .map((id) => siblings.find((a) => a.id === id)?.name)
        .filter((name): name is string => name !== undefined)
      if (names.length > 0) parts.push(`References: ${names.join(', ')}.`)
    }

    return parts.join(' ')
  }

  function formatSpecialAbilityNote(ability: SpecialAbility): string {
    return [ability.recharge, ability.uses_per_day !== null ? `${ability.uses_per_day}/day` : null]
      .filter((part): part is string => Boolean(part))
      .join(', ')
  }
</script>

<template>
  <div v-if="monsterId !== null" class="monster-detail-modal__backdrop" @click.self="emit('close')">
    <div class="monster-detail-modal__body">
      <button type="button" class="monster-detail-modal__close" @click="emit('close')">
        Close
      </button>
      <button type="button" class="monster-detail-modal__edit" @click="handleEdit">Edit</button>
      <template v-if="detail">
        <h2>{{ detail.name }}</h2>
        <p>
          {{ detail.statblock.size }} {{ detail.statblock.creature_type
          }}<span v-if="detail.statblock.subtype"> ({{ detail.statblock.subtype }})</span>,
          {{ detail.statblock.alignment }}
        </p>
        <p>
          AC {{ detail.statblock.armor_class
          }}<span v-if="detail.statblock.armor_class_notes">
            ({{ detail.statblock.armor_class_notes }})</span
          >
        </p>
        <p>HP {{ detail.statblock.hit_points }} ({{ detail.statblock.hit_dice }})</p>
        <p>
          CR {{ formatChallengeRating(detail.statblock.challenge_rating) }} ({{
            detail.statblock.experience_points
          }}
          XP)
        </p>

        <h3>Ability Scores</h3>
        <ul>
          <li>STR {{ detail.statblock.ability_scores.strength }}</li>
          <li>DEX {{ detail.statblock.ability_scores.dexterity }}</li>
          <li>CON {{ detail.statblock.ability_scores.constitution }}</li>
          <li>INT {{ detail.statblock.ability_scores.intelligence }}</li>
          <li>WIS {{ detail.statblock.ability_scores.wisdom }}</li>
          <li>CHA {{ detail.statblock.ability_scores.charisma }}</li>
        </ul>

        <template v-if="detail.statblock.saving_throws.length">
          <h3>Saving Throws</h3>
          <p>{{ formatSavingThrows(detail.statblock.saving_throws) }}</p>
        </template>

        <template v-if="detail.statblock.skills.length">
          <h3>Skills</h3>
          <p>{{ formatSkills(detail.statblock.skills) }}</p>
        </template>

        <p v-if="detail.statblock.damage_vulnerabilities.length">
          Damage Vulnerabilities: {{ detail.statblock.damage_vulnerabilities.join(', ') }}
        </p>
        <p v-if="detail.statblock.damage_resistances.length">
          Damage Resistances: {{ detail.statblock.damage_resistances.join(', ') }}
        </p>
        <p v-if="detail.statblock.damage_immunities.length">
          Damage Immunities: {{ detail.statblock.damage_immunities.join(', ') }}
        </p>
        <p v-if="detail.statblock.condition_immunities.length">
          Condition Immunities: {{ detail.statblock.condition_immunities.join(', ') }}
        </p>
        <p v-if="detail.statblock.senses.length">
          Senses: {{ detail.statblock.senses.join(', ') }}
        </p>
        <p v-if="detail.statblock.languages.length">
          Languages: {{ detail.statblock.languages.join(', ') }}
        </p>

        <template v-if="detail.statblock.actions.length">
          <h3>Actions</h3>
          <ul>
            <li v-for="action in detail.statblock.actions" :key="action.id">
              <strong>{{ action.name }}.</strong> {{ action.description }}
              {{ formatActionSummary(action, detail.statblock.actions) }}
            </li>
          </ul>
        </template>

        <template v-if="detail.statblock.legendary_actions.length">
          <h3>Legendary Actions</h3>
          <p v-if="detail.statblock.legendary_actions_per_turn !== null">
            The creature can take {{ detail.statblock.legendary_actions_per_turn }} legendary
            actions, choosing from the options below.
          </p>
          <ul>
            <li v-for="action in detail.statblock.legendary_actions" :key="action.id">
              <strong>{{ action.name }}</strong> (Cost {{ action.cost }}). {{ action.description }}
              {{ formatActionSummary(action, detail.statblock.legendary_actions) }}
            </li>
          </ul>
        </template>

        <template v-if="detail.statblock.special_abilities.length">
          <h3>Special Abilities</h3>
          <ul>
            <li v-for="ability in detail.statblock.special_abilities" :key="ability.id">
              <strong>{{ ability.name }}.</strong> {{ ability.description }}
              <template v-if="ability.recharge || ability.uses_per_day !== null">
                ({{ formatSpecialAbilityNote(ability) }})
              </template>
            </li>
          </ul>
        </template>
      </template>
    </div>
  </div>
</template>

<style scoped>
  .monster-detail-modal__backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .monster-detail-modal__body {
    background: white;
    border-radius: 4px;
    padding: 1.5rem;
    max-width: 32rem;
    max-height: 80vh;
    overflow-y: auto;
  }
</style>
