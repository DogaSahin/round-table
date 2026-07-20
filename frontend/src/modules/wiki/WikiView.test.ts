import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import WikiView from './WikiView.vue'
import * as wikiApi from './api'

describe('WikiView', () => {
  it('loads the roster on mount', async () => {
    vi.spyOn(wikiApi, 'listPages').mockResolvedValue([
      {
        id: 1,
        title: 'The Ashen Keep',
        slug: 'the-ashen-keep',
        category: null,
        player_visible: false,
      },
    ])

    const wrapper = mount(WikiView)
    await flushPromises()

    expect(wrapper.text()).toContain('The Ashen Keep')
  })

  it('creates a page and selects it', async () => {
    vi.spyOn(wikiApi, 'listPages').mockResolvedValue([])
    vi.spyOn(wikiApi, 'createPage').mockResolvedValue({
      id: 1,
      title: 'New Page',
      slug: 'new-page',
      category: null,
      body_md: null,
      body_html: '',
      player_visible: false,
      updated_at: '2026-01-01T00:00:00Z',
      tags: [],
      links: [],
      backlinks: [],
    })

    const wrapper = mount(WikiView)
    await flushPromises()

    await wrapper.find('input[placeholder="Page title"]').setValue('New Page')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(wikiApi.createPage).toHaveBeenCalledWith('New Page', null, null, false)
    expect(wrapper.text()).toContain('New Page')
  })

  it('edits the selected page and saves via updatePage', async () => {
    const detail = {
      id: 1,
      title: 'Original',
      slug: 'original',
      category: null,
      body_md: 'Old body.',
      body_html: '<p>Old body.</p>',
      player_visible: false,
      updated_at: '2026-01-01T00:00:00Z',
      tags: [],
      links: [],
      backlinks: [],
    }
    vi.spyOn(wikiApi, 'listPages').mockResolvedValue([
      { id: 1, title: 'Original', slug: 'original', category: null, player_visible: false },
    ])
    vi.spyOn(wikiApi, 'fetchPage').mockResolvedValue(detail)
    vi.spyOn(wikiApi, 'updatePage').mockResolvedValue({ ...detail, body_md: 'New body.' })

    const wrapper = mount(WikiView)
    await flushPromises()

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Original')
      ?.trigger('click')
    await flushPromises()

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Edit')
      ?.trigger('click')
    await flushPromises()

    await wrapper.find('form.wiki-edit-form textarea').setValue('New body.')
    await wrapper.find('form.wiki-edit-form').trigger('submit.prevent')
    await flushPromises()

    expect(wikiApi.updatePage).toHaveBeenCalledWith('original', {
      title: 'Original',
      category: null,
      body_md: 'New body.',
      player_visible: false,
    })
  })
})
