// frontend/src/composables/useTheme.ts
import { readonly, ref } from 'vue'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'roundtable-theme'

function loadInitialTheme(): Theme {
  const stored = localStorage.getItem(STORAGE_KEY)
  return stored === 'light' || stored === 'dark' ? stored : 'dark'
}

const theme = ref<Theme>(loadInitialTheme())

function applyTheme(t: Theme) {
  document.documentElement.setAttribute('data-theme', t)
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem(STORAGE_KEY, theme.value)
  applyTheme(theme.value)
}

function initTheme() {
  applyTheme(theme.value)
}

export function useTheme() {
  return { theme: readonly(theme), toggleTheme, initTheme }
}
