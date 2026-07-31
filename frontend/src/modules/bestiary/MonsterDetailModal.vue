<script setup lang="ts">
  // frontend/src/modules/bestiary/MonsterDetailModal.vue
  import { onBeforeUnmount, ref, watch } from 'vue'
  import { fetchMonster, formatChallengeRating, type BestiaryMonsterDetail } from './api'

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

        <template v-if="detail.statblock.actions.length">
          <h3>Actions</h3>
          <ul>
            <li v-for="action in detail.statblock.actions" :key="action.id">
              <strong>{{ action.name }}.</strong> {{ action.description }}
            </li>
          </ul>
        </template>

        <template v-if="detail.statblock.legendary_actions.length">
          <h3>Legendary Actions</h3>
          <ul>
            <li v-for="action in detail.statblock.legendary_actions" :key="action.id">
              <strong>{{ action.name }}</strong> (Cost {{ action.cost }}). {{ action.description }}
            </li>
          </ul>
        </template>

        <template v-if="detail.statblock.special_abilities.length">
          <h3>Special Abilities</h3>
          <ul>
            <li v-for="ability in detail.statblock.special_abilities" :key="ability.id">
              <strong>{{ ability.name }}.</strong> {{ ability.description }}
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
