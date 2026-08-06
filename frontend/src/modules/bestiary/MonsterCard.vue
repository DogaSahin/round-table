<script setup lang="ts">
  // frontend/src/modules/bestiary/MonsterCard.vue
  import { ref, watch } from 'vue'
  import {
    favoriteMonster,
    formatChallengeRating,
    unfavoriteMonster,
    type BestiaryMonsterListItem,
  } from './api'
  import Card from '@/components/Card.vue'

  const props = defineProps<{
    item: BestiaryMonsterListItem
  }>()

  const emit = defineEmits<{
    (e: 'open', monsterId: number): void
    (e: 'error', err: unknown): void
    (e: 'favorite-changed', monsterId: number, isFavorite: boolean): void
  }>()

  const isFavorite = ref(props.item.is_favorite)

  watch(
    () => props.item.is_favorite,
    (value) => {
      isFavorite.value = value
    },
  )

  async function toggleFavorite() {
    const next = !isFavorite.value
    isFavorite.value = next
    emit('favorite-changed', props.item.id, next)
    try {
      const updated = next
        ? await favoriteMonster(props.item.id)
        : await unfavoriteMonster(props.item.id)
      isFavorite.value = updated.is_favorite
    } catch (err) {
      isFavorite.value = !next
      emit('error', err)
    }
  }
</script>

<template>
  <Card class="monster-card">
    <button type="button" class="monster-card__body" @click="emit('open', item.id)">
      <div class="monster-card__portrait">
        <img v-if="item.image_url" :src="item.image_url" :alt="item.name" />
        <span v-else class="monster-card__initial">{{ item.name.charAt(0).toUpperCase() }}</span>
        <span class="monster-card__cr">
          CR {{ formatChallengeRating(item.challenge_rating) }}
        </span>
      </div>
      <div class="monster-card__info">
        <h3 class="monster-card__name">{{ item.name }}</h3>
        <span class="monster-card__type">{{ item.creature_type }}</span>
      </div>
    </button>
    <button
      type="button"
      class="monster-card__favorite"
      :aria-pressed="isFavorite"
      @click="toggleFavorite"
    >
      {{ isFavorite ? '★' : '☆' }}
    </button>
  </Card>
</template>

<style scoped>
  .monster-card {
    position: relative;
    overflow: hidden;
    transition:
      box-shadow var(--transition-fast),
      transform var(--transition-fast);
  }

  .monster-card:hover {
    box-shadow: var(--shadow-modal);
    transform: translateY(-2px);
  }

  .monster-card__body {
    display: block;
    width: 100%;
    text-align: left;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    color: inherit;
    font-family: var(--font-body);
  }

  .monster-card__portrait {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 6rem;
    margin: calc(-1 * var(--space-4)) calc(-1 * var(--space-4)) 0;
    background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-surface-raised) 140%);
  }

  .monster-card__portrait img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .monster-card__initial {
    font-family: var(--font-heading);
    font-size: var(--text-2xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-accent-contrast);
    opacity: 0.85;
  }

  .monster-card__cr {
    position: absolute;
    bottom: var(--space-2);
    right: var(--space-2);
    background: var(--color-surface);
    color: var(--color-text);
    font-size: var(--text-xs);
    font-weight: var(--font-weight-bold);
    padding: var(--space-1) var(--space-2);
    border-radius: 999px;
    box-shadow: var(--shadow-card);
  }

  .monster-card__info {
    padding-top: var(--space-3);
  }

  .monster-card__name {
    margin: 0 0 var(--space-1);
    font-family: var(--font-heading);
    color: var(--color-text);
    font-size: var(--text-base);
  }

  .monster-card__type {
    display: block;
    color: var(--color-text-muted);
    font-size: var(--text-sm);
    text-transform: capitalize;
  }

  .monster-card__favorite {
    position: absolute;
    top: var(--space-2);
    left: var(--space-2);
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    background: var(--color-surface);
    border: none;
    border-radius: 50%;
    cursor: pointer;
    font-size: var(--text-lg);
    color: var(--color-warning);
    box-shadow: var(--shadow-card);
  }
</style>
