import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { router } from '@/router'
import AppShell from './AppShell.vue'

let wrapper: VueWrapper | null = null

beforeEach(() => {
  localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
})

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
})

async function mountShell() {
  await router.push('/')
  await router.isReady()
  return mount(AppShell, { global: { plugins: [router] } })
}

describe('AppShell', () => {
  // Order matters: useTheme's `theme` ref is module-level singleton state. This test must run
  // before any test that calls toggleTheme, or it would observe an already-toggled in-memory
  // value instead of a genuine first-load default.
  it('defaults to dark theme on first mount', async () => {
    wrapper = await mountShell()

    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('toggles the theme and persists the choice to localStorage', async () => {
    wrapper = await mountShell()

    await wrapper.find('.app-shell__theme-toggle').trigger('click')

    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(localStorage.getItem('roundtable-theme')).toBe('light')
  })
})
