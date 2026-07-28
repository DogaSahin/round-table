<script setup lang="ts">
  // frontend/src/modules/bestiary/MonsterCard.vue
  import { ref, watch } from 'vue'
  import {
    favoriteMonster,
    formatChallengeRating,
    unfavoriteMonster,
    type BestiaryMonsterListItem,
  } from './api'

  const props = defineProps<{
    item: BestiaryMonsterListItem
  }>()

  const emit = defineEmits<{
    (e: 'open', monsterId: number): void
    (e: 'error', err: unknown): void
  }>()

  const isFavorite = ref(props.item.is_favorite)

  watch(
    () => props.item.is_favorite,
    (value) => {
      isFavorite.value = value
    },
  )

  async function toggleFavorite() {
    try {
      const updated = isFavorite.value
        ? await unfavoriteMonster(props.item.id)
        : await favoriteMonster(props.item.id)
      isFavorite.value = updated.is_favorite
    } catch (err) {
      emit('error', err)
    }
  }
</script>

<template>
  <div class="monster-card">
    <button type="button" class="monster-card__body" @click="emit('open', item.id)">
      <h3>{{ item.name }}</h3>
      <p>{{ item.creature_type }} &middot; CR {{ formatChallengeRating(item.challenge_rating) }}</p>
    </button>
    <button
      type="button"
      class="monster-card__favorite"
      :aria-pressed="isFavorite"
      @click="toggleFavorite"
    >
      {{ isFavorite ? '★' : '☆' }}
    </button>
  </div>
</template>

<style scoped>
  .monster-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 0.5rem 0.75rem;
  }

  .monster-card__body {
    flex: 1;
    text-align: left;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
  }

  .monster-card__favorite {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.25rem;
  }
</style>
