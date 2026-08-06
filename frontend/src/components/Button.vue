<script setup lang="ts">
  // frontend/src/components/Button.vue
  withDefaults(
    defineProps<{
      variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
      disabled?: boolean
      type?: 'button' | 'submit'
    }>(),
    {
      variant: 'secondary',
      disabled: false,
      type: 'button',
    },
  )
</script>

<template>
  <button :type="type" :disabled="disabled" :class="['button', `button--${variant}`]">
    <slot />
  </button>
</template>

<style scoped>
  .button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    border-radius: var(--radius-sm);
    border: 1px solid transparent;
    font-family: var(--font-body);
    font-size: var(--text-sm);
    font-weight: var(--font-weight-bold);
    cursor: pointer;
    transition:
      background-color var(--transition-fast),
      border-color var(--transition-fast),
      color var(--transition-fast);
  }

  .button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .button--primary {
    background: var(--color-accent);
    color: var(--color-accent-contrast);
  }

  .button--primary:not(:disabled):hover {
    background: var(--color-accent-hover);
  }

  .button--secondary {
    background: var(--color-surface);
    color: var(--color-text);
    border-color: var(--color-border);
  }

  .button--secondary:not(:disabled):hover {
    background: var(--color-surface-raised);
  }

  .button--danger {
    background: var(--color-danger);
    color: var(--color-accent-contrast);
  }

  .button--danger:not(:disabled):hover {
    opacity: 0.9;
  }

  .button--ghost {
    background: transparent;
    color: var(--color-text);
    border-color: transparent;
  }

  .button--ghost:not(:disabled):hover {
    background: var(--color-surface-raised);
  }
</style>
