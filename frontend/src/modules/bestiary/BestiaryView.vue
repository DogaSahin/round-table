<script setup lang="ts">
  // frontend/src/modules/bestiary/BestiaryView.vue
  import { computed, onMounted, ref, watch } from 'vue'
  import { watchDebounced } from '@vueuse/core'
  import { ApiError } from '@/api/client'
  import {
    ALLOWED_CHALLENGE_RATINGS,
    formatChallengeRating,
    listBestiary,
    type BestiaryMonsterListItem,
    type BestiarySort,
  } from './api'
  import MonsterCard from './MonsterCard.vue'
  import MonsterDetailModal from './MonsterDetailModal.vue'
  import MonsterFormModal from './MonsterFormModal.vue'
  import Button from '@/components/Button.vue'
  import TextInput from '@/components/TextInput.vue'

  const DEFAULT_SORT: BestiarySort = 'name'

  const monsters = ref<BestiaryMonsterListItem[]>([])
  const availableTypes = ref<string[]>([])
  const errorMessage = ref<string | null>(null)
  const openMonsterId = ref<number | null>(null)
  const showFormModal = ref(false)
  const editingMonsterId = ref<number | null>(null)

  const search = ref('')
  const creatureType = ref('')
  const crMin = ref<number | null>(null)
  const crMax = ref<number | null>(null)
  const favoritesOnly = ref(false)
  const sort = ref<BestiarySort>(DEFAULT_SORT)

  const crOptions = computed(() =>
    ALLOWED_CHALLENGE_RATINGS.map((cr) => ({ value: cr, label: formatChallengeRating(cr) })),
  )

  function handleError(err: unknown) {
    errorMessage.value = err instanceof ApiError ? err.message : 'Unknown error'
  }

  async function loadTypes() {
    try {
      const all = await listBestiary({})
      availableTypes.value = [...new Set(all.map((m) => m.creature_type))].sort()
    } catch (err) {
      handleError(err)
    }
  }

  async function loadMonsters() {
    errorMessage.value = null
    try {
      monsters.value = await listBestiary({
        search: search.value || undefined,
        type: creatureType.value || undefined,
        cr_min: crMin.value ?? undefined,
        cr_max: crMax.value ?? undefined,
        favorites_only: favoritesOnly.value,
        sort: sort.value,
      })
    } catch (err) {
      handleError(err)
    }
  }

  function clearFilters() {
    search.value = ''
    creatureType.value = ''
    crMin.value = null
    crMax.value = null
    favoritesOnly.value = false
    sort.value = DEFAULT_SORT
  }

  function openMonster(monsterId: number) {
    openMonsterId.value = monsterId
  }

  function closeMonster() {
    openMonsterId.value = null
  }

  function onFavoriteChanged(monsterId: number, isFavorite: boolean) {
    if (favoritesOnly.value && !isFavorite) {
      monsters.value = monsters.value.filter((m) => m.id !== monsterId)
    }
  }

  function openCreateForm() {
    editingMonsterId.value = null
    showFormModal.value = true
  }

  function openEditForm(monsterId: number) {
    openMonsterId.value = null
    editingMonsterId.value = monsterId
    showFormModal.value = true
  }

  function closeFormModal() {
    showFormModal.value = false
  }

  async function onMonsterSaved() {
    showFormModal.value = false
    await loadMonsters()
    await loadTypes()
  }

  watchDebounced(search, loadMonsters, { debounce: 300 })
  watch([creatureType, crMin, crMax, favoritesOnly, sort], loadMonsters)

  onMounted(() => {
    void loadTypes()
    void loadMonsters()
  })
</script>

<template>
  <section class="bestiary-view">
    <div class="bestiary-view__header">
      <h1>Bestiary</h1>
      <Button variant="primary" class="bestiary-new-monster" @click="openCreateForm">
        + New Monster
      </Button>
    </div>
    <p v-if="errorMessage" class="bestiary-view__error">Error: {{ errorMessage }}</p>

    <form class="bestiary-filters" @submit.prevent>
      <button
        type="button"
        class="bestiary-filters__favorites-chip"
        :aria-pressed="favoritesOnly"
        @click="favoritesOnly = !favoritesOnly"
      >
        ★ Favorites
      </button>

      <TextInput v-model="search" placeholder="Search" />

      <select v-model="creatureType" class="native-select">
        <option value="">All types</option>
        <option v-for="t in availableTypes" :key="t" :value="t">{{ t }}</option>
      </select>

      <select v-model="crMin" class="native-select">
        <option :value="null">Min CR</option>
        <option v-for="opt in crOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <select v-model="crMax" class="native-select">
        <option :value="null">Max CR</option>
        <option v-for="opt in crOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <select v-model="sort" class="native-select">
        <option value="name">Name</option>
        <option value="cr">Challenge Rating</option>
        <option value="created_at">Recently added</option>
      </select>

      <Button variant="ghost" @click="clearFilters">Clear filters</Button>
    </form>

    <p v-if="monsters.length === 0" class="bestiary-empty">
      No monsters match these filters.
      <Button variant="ghost" @click="clearFilters">Clear filters</Button>
    </p>

    <div v-else class="bestiary-grid">
      <MonsterCard
        v-for="m in monsters"
        :key="m.id"
        :item="m"
        @open="openMonster"
        @error="handleError"
        @favorite-changed="onFavoriteChanged"
      />
    </div>

    <MonsterDetailModal
      :monster-id="openMonsterId"
      @close="closeMonster"
      @error="handleError"
      @edit="openEditForm"
    />

    <MonsterFormModal
      v-if="showFormModal"
      :monster-id="editingMonsterId"
      @saved="onMonsterSaved"
      @close="closeFormModal"
    />
  </section>
</template>

<style scoped>
  .bestiary-view__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--space-4);
  }

  .bestiary-view__error {
    color: var(--color-danger);
  }

  .bestiary-filters {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-2);
    margin-bottom: var(--space-4);
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

  .bestiary-filters__favorites-chip {
    border: 1px solid var(--color-border);
    border-radius: 999px;
    background: var(--color-surface);
    color: var(--color-text);
    padding: var(--space-2) var(--space-3);
    font-family: var(--font-body);
    font-size: var(--text-sm);
    cursor: pointer;
    transition:
      background-color var(--transition-fast),
      border-color var(--transition-fast);
  }

  .bestiary-filters__favorites-chip[aria-pressed='true'] {
    background: var(--color-warning-bg);
    border-color: var(--color-warning);
    color: var(--color-warning);
  }

  .bestiary-empty {
    color: var(--color-text-muted);
  }

  .bestiary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: var(--space-3);
  }
</style>
