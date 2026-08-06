<script setup lang="ts">
  // frontend/src/components/Modal.vue
  import { onBeforeUnmount, onMounted } from 'vue'

  const emit = defineEmits<{
    (e: 'close'): void
  }>()

  function onKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') emit('close')
  }

  onMounted(() => {
    window.addEventListener('keydown', onKeydown)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', onKeydown)
  })
</script>

<template>
  <div class="modal__backdrop" @click.self="emit('close')">
    <div class="modal__body">
      <header v-if="$slots.header" class="modal__header">
        <slot name="header" />
      </header>
      <div class="modal__content">
        <slot />
      </div>
      <footer v-if="$slots.footer" class="modal__footer">
        <slot name="footer" />
      </footer>
    </div>
  </div>
</template>

<style scoped>
  .modal__backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }

  .modal__body {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-modal);
    padding: var(--space-5);
    max-width: 32rem;
    max-height: 80vh;
    overflow-y: auto;
  }

  .modal__header {
    margin-bottom: var(--space-4);
    font-family: var(--font-heading);
  }

  .modal__footer {
    margin-top: var(--space-4);
    display: flex;
    justify-content: flex-end;
    gap: var(--space-2);
  }
</style>
