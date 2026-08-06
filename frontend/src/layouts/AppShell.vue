<script setup lang="ts">
  // frontend/src/layouts/AppShell.vue
  import { onMounted } from 'vue'
  import Button from '@/components/Button.vue'
  import { useTheme } from '@/composables/useTheme'

  const { theme, toggleTheme, initTheme } = useTheme()

  onMounted(() => {
    initTheme()
  })
</script>

<template>
  <div class="app-shell">
    <header class="app-shell__header">
      <span class="app-shell__title">Round Table</span>
      <nav class="app-shell__nav">
        <router-link to="/dice">Dice</router-link>
        <router-link to="/sessions">Sessions</router-link>
        <router-link to="/factions">Factions</router-link>
        <router-link to="/npcs">NPCs</router-link>
        <router-link to="/wiki">Wiki</router-link>
        <router-link to="/combat">Combat</router-link>
        <router-link to="/maps">Maps</router-link>
      </nav>
      <Button
        variant="ghost"
        class="app-shell__theme-toggle"
        :aria-label="theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'"
        @click="toggleTheme"
      >
        {{ theme === 'dark' ? '☀️' : '🌙' }}
      </Button>
    </header>
    <main class="app-shell__content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
  .app-shell {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  .app-shell__header {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-3) var(--space-5);
    border-bottom: 1px solid var(--color-border);
    background: var(--color-surface);
  }

  .app-shell__title {
    font-family: var(--font-heading);
    font-weight: var(--font-weight-bold);
    font-size: var(--text-lg);
    color: var(--color-text);
  }

  .app-shell__nav {
    display: flex;
    gap: var(--space-4);
    flex: 1;
  }

  .app-shell__nav a {
    color: var(--color-text-muted);
    text-decoration: none;
    font-size: var(--text-sm);
  }

  .app-shell__nav a:hover {
    color: var(--color-text);
  }

  .app-shell__content {
    flex: 1;
    padding: var(--space-5);
    background: var(--color-bg);
  }
</style>
