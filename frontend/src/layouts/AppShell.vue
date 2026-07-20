<script setup lang="ts"></script>

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
      </nav>
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
    padding: 0.75rem 1.5rem;
    border-bottom: 1px solid #ccc;
  }

  .app-shell__title {
    font-weight: 600;
  }

  .app-shell__content {
    flex: 1;
    padding: 1.5rem;
  }
</style>
