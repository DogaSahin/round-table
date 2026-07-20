<script setup lang="ts">
  import { onMounted, ref } from 'vue'
  import { ApiError } from '@/api/client'
  import {
    addTag,
    createPage,
    deletePage,
    fetchPage,
    listPages,
    removeTag,
    searchPages,
    updatePage,
    type WikiPageDetail,
    type WikiPageListItem,
  } from './api'

  const pages = ref<WikiPageListItem[]>([])
  const selected = ref<WikiPageDetail | null>(null)
  const editing = ref(false)
  const newTitle = ref('')
  const newCategory = ref('')
  const newBody = ref('')
  const newPlayerVisible = ref(false)
  const searchQuery = ref('')
  const searchResults = ref<WikiPageListItem[] | null>(null)
  const newTagName = ref('')
  const errorMessage = ref<string | null>(null)

  const editTitle = ref('')
  const editCategory = ref('')
  const editBody = ref('')
  const editPlayerVisible = ref(false)

  function handleError(err: unknown) {
    errorMessage.value = err instanceof ApiError ? err.message : 'Unknown error'
  }

  async function loadPages() {
    pages.value = await listPages()
  }

  async function selectPage(slug: string) {
    errorMessage.value = null
    editing.value = false
    try {
      selected.value = await fetchPage(slug)
    } catch (err) {
      handleError(err)
    }
  }

  async function submitCreate() {
    errorMessage.value = null
    try {
      const created = await createPage(
        newTitle.value,
        newCategory.value || null,
        newBody.value || null,
        newPlayerVisible.value,
      )
      newTitle.value = ''
      newCategory.value = ''
      newBody.value = ''
      newPlayerVisible.value = false
      await loadPages()
      selected.value = created
    } catch (err) {
      handleError(err)
    }
  }

  function startEdit() {
    if (selected.value === null) return
    editTitle.value = selected.value.title
    editCategory.value = selected.value.category ?? ''
    editBody.value = selected.value.body_md ?? ''
    editPlayerVisible.value = selected.value.player_visible
    editing.value = true
  }

  async function submitEdit() {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      selected.value = await updatePage(selected.value.slug, {
        title: editTitle.value,
        category: editCategory.value || null,
        body_md: editBody.value || null,
        player_visible: editPlayerVisible.value,
      })
      editing.value = false
      await loadPages()
    } catch (err) {
      handleError(err)
    }
  }

  async function remove(slug: string) {
    errorMessage.value = null
    try {
      await deletePage(slug)
      if (selected.value?.slug === slug) selected.value = null
      await loadPages()
    } catch (err) {
      handleError(err)
    }
  }

  async function runSearch() {
    errorMessage.value = null
    try {
      searchResults.value = searchQuery.value.trim() ? await searchPages(searchQuery.value) : null
    } catch (err) {
      handleError(err)
    }
  }

  async function submitTag() {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await addTag(selected.value.slug, newTagName.value)
      newTagName.value = ''
      selected.value = await fetchPage(selected.value.slug)
    } catch (err) {
      handleError(err)
    }
  }

  async function removeSelectedTag(tagId: number) {
    if (selected.value === null) return
    errorMessage.value = null
    try {
      await removeTag(selected.value.slug, tagId)
      selected.value = await fetchPage(selected.value.slug)
    } catch (err) {
      handleError(err)
    }
  }

  onMounted(loadPages)
</script>

<template>
  <section>
    <h1>Wiki</h1>
    <p v-if="errorMessage">Error: {{ errorMessage }}</p>

    <form @submit.prevent="submitCreate">
      <input v-model="newTitle" type="text" placeholder="Page title" />
      <input v-model="newCategory" type="text" placeholder="Category" />
      <textarea v-model="newBody" placeholder="Markdown body"></textarea>
      <label>
        <input v-model="newPlayerVisible" type="checkbox" />
        Visible to players
      </label>
      <button type="submit">New Page</button>
    </form>

    <form @submit.prevent="runSearch">
      <input v-model="searchQuery" type="text" placeholder="Search" />
      <button type="submit">Search</button>
    </form>

    <ul v-if="searchResults">
      <li v-for="p in searchResults" :key="p.id">
        <button type="button" @click="selectPage(p.slug)">{{ p.title }}</button>
      </li>
    </ul>
    <ul v-else>
      <li v-for="p in pages" :key="p.id">
        <button type="button" @click="selectPage(p.slug)">{{ p.title }}</button>
        <button type="button" @click="remove(p.slug)">Delete</button>
      </li>
    </ul>

    <div v-if="selected && !editing">
      <h2>{{ selected.title }}</h2>
      <p v-if="selected.category">{{ selected.category }}</p>
      <div v-html="selected.body_html"></div>

      <h3>Tags</h3>
      <ul>
        <li v-for="tag in selected.tags" :key="tag.id">
          {{ tag.name }}
          <button type="button" @click="removeSelectedTag(tag.id)">Remove</button>
        </li>
      </ul>
      <form @submit.prevent="submitTag">
        <input v-model="newTagName" type="text" placeholder="Tag name" />
        <button type="submit">Add Tag</button>
      </form>

      <h3>Backlinks</h3>
      <ul>
        <li v-for="b in selected.backlinks" :key="b.id">{{ b.title }}</li>
      </ul>

      <button type="button" @click="startEdit">Edit</button>
    </div>

    <form v-if="selected && editing" class="wiki-edit-form" @submit.prevent="submitEdit">
      <input v-model="editTitle" type="text" placeholder="Page title" />
      <input v-model="editCategory" type="text" placeholder="Category" />
      <textarea v-model="editBody" placeholder="Markdown body"></textarea>
      <label>
        <input v-model="editPlayerVisible" type="checkbox" />
        Visible to players
      </label>
      <button type="submit">Save</button>
    </form>
  </section>
</template>
