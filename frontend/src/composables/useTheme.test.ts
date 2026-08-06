import { beforeEach, describe, expect, it, vi } from 'vitest'

// theme is module-level singleton state, initialized once at import time from localStorage —
// vi.resetModules() + a fresh dynamic import is required per test to observe a clean initial load,
// rather than the shared in-memory ref left over from a previous test in this file.
async function freshUseTheme() {
  vi.resetModules()
  const mod = await import('./useTheme')
  return mod.useTheme()
}

beforeEach(() => {
  localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
})

describe('useTheme', () => {
  it('defaults to dark when no theme is stored', async () => {
    const { theme } = await freshUseTheme()

    expect(theme.value).toBe('dark')
  })

  it('uses the stored theme when one is present', async () => {
    localStorage.setItem('roundtable-theme', 'light')

    const { theme } = await freshUseTheme()

    expect(theme.value).toBe('light')
  })

  it('toggleTheme flips the value and persists it', async () => {
    const { theme, toggleTheme } = await freshUseTheme()

    toggleTheme()

    expect(theme.value).toBe('light')
    expect(localStorage.getItem('roundtable-theme')).toBe('light')

    toggleTheme()

    expect(theme.value).toBe('dark')
    expect(localStorage.getItem('roundtable-theme')).toBe('dark')
  })

  it('toggleTheme updates the data-theme attribute on the document', async () => {
    const { toggleTheme } = await freshUseTheme()

    toggleTheme()

    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('initTheme applies the current value without changing it', async () => {
    localStorage.setItem('roundtable-theme', 'light')
    const { theme, initTheme } = await freshUseTheme()

    initTheme()

    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(theme.value).toBe('light')
  })
})
