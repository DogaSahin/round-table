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

  const DEFAULT_SORT: BestiarySort = 'name'

  const monsters = ref<BestiaryMonsterListItem[]>([])
  const availableTypes = ref<string[]>([])
  const errorMessage = ref<string | null>(null)
  const openMonsterId = ref<number | null>(null)

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

  watchDebounced(search, loadMonsters, { debounce: 300 })
  watch([creatureType, crMin, crMax, favoritesOnly, sort], loadMonsters)

  onMounted(() => {
    void loadTypes()
    void loadMonsters()
  })
</script>

<template>
  <section>
    <h1>Bestiary</h1>
    <p v-if="errorMessage">Error: {{ errorMessage }}</p>

    <form class="bestiary-filters" @submit.prevent>
      <input v-model="search" type="text" placeholder="Search" />

      <select v-model="creatureType">
        <option value="">All types</option>
        <option v-for="t in availableTypes" :key="t" :value="t">{{ t }}</option>
      </select>

      <select v-model="crMin">
        <option :value="null">Min CR</option>
        <option v-for="opt in crOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <select v-model="crMax">
        <option :value="null">Max CR</option>
        <option v-for="opt in crOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <label>
        <input v-model="favoritesOnly" type="checkbox" />
        Favorites only
      </label>

      <select v-model="sort">
        <option value="name">Name</option>
        <option value="cr">Challenge Rating</option>
        <option value="created_at">Recently added</option>
      </select>

      <button type="button" @click="clearFilters">Clear filters</button>
    </form>

    <p v-if="monsters.length === 0" class="bestiary-empty">
      No monsters match these filters.
      <button type="button" @click="clearFilters">Clear filters</button>
    </p>

    <div v-else class="bestiary-grid">
      <MonsterCard
        v-for="m in monsters"
        :key="m.id"
        :item="m"
        @open="openMonster"
        @error="handleError"
      />
    </div>

    <MonsterDetailModal :monster-id="openMonsterId" @close="closeMonster" @error="handleError" />
  </section>
</template>

<style scoped>
  .bestiary-filters {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .bestiary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 0.75rem;
  }
</style>
