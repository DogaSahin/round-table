import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import BestiaryView from './BestiaryView.vue'
import * as bestiaryApi from './api'
import type { BestiaryMonsterListItem } from './api'

const RAT: BestiaryMonsterListItem = {
  id: 1,
  name: 'Giant Rat',
  slug: 'giant-rat',
  creature_type: 'beast',
  challenge_rating: 0.125,
  is_favorite: false,
  image_url: null,
}

const OWLBEAR: BestiaryMonsterListItem = {
  id: 2,
  name: 'Owlbear',
  slug: 'owlbear',
  creature_type: 'monstrosity',
  challenge_rating: 3,
  is_favorite: false,
  image_url: null,
}

let wrapper: VueWrapper | null = null

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
  vi.useRealTimers()
})

describe('BestiaryView', () => {
  it('loads the roster and the type-options list once on mount', async () => {
    const listSpy = vi.spyOn(bestiaryApi, 'listBestiary').mockResolvedValue([RAT, OWLBEAR])

    wrapper = mount(BestiaryView)
    await flushPromises()

    expect(wrapper.text()).toContain('Giant Rat')
    expect(wrapper.text()).toContain('Owlbear')
    // Once for the unfiltered type-options fetch, once for the initial roster load.
    expect(listSpy).toHaveBeenCalledTimes(2)
    expect(listSpy).toHaveBeenCalledWith({})
  })

  it('does not refetch type options when other filters change', async () => {
    const listSpy = vi.spyOn(bestiaryApi, 'listBestiary').mockResolvedValue([RAT])
    wrapper = mount(BestiaryView)
    await flushPromises()
    listSpy.mockClear()

    await wrapper.find('input[type="checkbox"]').setValue(true)
    await flushPromises()

    expect(listSpy).toHaveBeenCalledTimes(1)
    expect(listSpy).toHaveBeenCalledWith(expect.objectContaining({ favorites_only: true }))
  })

  it('debounces the search input before fetching', async () => {
    vi.useFakeTimers()
    const listSpy = vi.spyOn(bestiaryApi, 'listBestiary').mockResolvedValue([RAT])
    wrapper = mount(BestiaryView)
    await flushPromises()
    listSpy.mockClear()

    await wrapper.find('input[type="text"]').setValue('rat')
    expect(listSpy).not.toHaveBeenCalled()

    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(listSpy).toHaveBeenCalledWith(expect.objectContaining({ search: 'rat' }))
  })

  it('shows an empty state and resets filters on "Clear filters"', async () => {
    const listSpy = vi.spyOn(bestiaryApi, 'listBestiary').mockResolvedValue([])
    wrapper = mount(BestiaryView)
    await flushPromises()

    expect(wrapper.text()).toContain('No monsters match')

    listSpy.mockClear()
    await wrapper.find('input[type="checkbox"]').setValue(true)
    await flushPromises()

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Clear filters')
      ?.trigger('click')
    await flushPromises()

    expect((wrapper.find('input[type="checkbox"]').element as HTMLInputElement).checked).toBe(false)
  })
})
