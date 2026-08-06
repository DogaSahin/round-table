<script setup lang="ts">
  // frontend/src/components/Badge.vue
  withDefaults(
    defineProps<{
      variant?: 'default' | 'success' | 'danger' | 'warning'
    }>(),
    {
      variant: 'default',
    },
  )
</script>

<template>
  <span :class="['badge', `badge--${variant}`]">
    <slot />
  </span>
</template>

<style scoped>
  .badge {
    display: inline-block;
    font-family: var(--font-body);
    font-size: var(--text-xs);
    font-weight: var(--font-weight-bold);
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
  }

  .badge--default {
    background: var(--color-surface-raised);
    color: var(--color-text-muted);
  }

  .badge--success {
    background: var(--color-success-bg);
    color: var(--color-success);
  }

  .badge--danger {
    background: var(--color-danger-bg);
    color: var(--color-danger);
  }

  .badge--warning {
    background: var(--color-warning-bg);
    color: var(--color-warning);
  }
</style>
