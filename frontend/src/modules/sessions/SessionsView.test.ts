import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import SessionsView from './SessionsView.vue'
import * as sessionsApi from './api'

describe('SessionsView', () => {
  it('loads the roster on mount', async () => {
    vi.spyOn(sessionsApi, 'listSessions').mockResolvedValue([
      { id: 1, number: 1, date: '2026-01-01', title: 'Session One', status: 'planned' },
    ])

    const wrapper = mount(SessionsView)
    await flushPromises()

    expect(wrapper.text()).toContain('Session One')
  })

  it('creates a session and selects it', async () => {
    vi.spyOn(sessionsApi, 'listSessions').mockResolvedValue([])
    vi.spyOn(sessionsApi, 'createSession').mockResolvedValue({
      id: 1,
      number: 1,
      date: '2026-01-01',
      title: 'New Session',
      summary: null,
      status: 'planned',
      logs: [],
    })

    const wrapper = mount(SessionsView)
    await flushPromises()

    await wrapper.find('input[type="text"]').setValue('New Session')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(sessionsApi.createSession).toHaveBeenCalledWith('New Session')
    expect(wrapper.text()).toContain('New Session')
  })

  it('adds a log to the selected session', async () => {
    const detail = {
      id: 1,
      number: 1,
      date: '2026-01-01',
      title: 'Session One',
      summary: null,
      status: 'planned',
      logs: [],
    }
    vi.spyOn(sessionsApi, 'listSessions').mockResolvedValue([
      { id: 1, number: 1, date: '2026-01-01', title: 'Session One', status: 'planned' },
    ])
    vi.spyOn(sessionsApi, 'fetchSession').mockResolvedValue({
      ...detail,
      logs: [
        {
          id: 1,
          text: 'Goblins!',
          tag: 'combat',
          logged_at: '2026-01-01T00:00:00Z',
          resolved_at: null,
        },
      ],
    })
    vi.spyOn(sessionsApi, 'addLog').mockResolvedValue({
      id: 1,
      text: 'Goblins!',
      tag: 'combat',
      logged_at: '2026-01-01T00:00:00Z',
      resolved_at: null,
    })

    const wrapper = mount(SessionsView)
    await flushPromises()

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '#1 Session One (planned)')
      ?.trigger('click')
    await flushPromises()

    const logInput = wrapper.find('input[placeholder="Log entry"]')
    await logInput.setValue('Goblins!')
    const forms = wrapper.findAll('form')
    await forms[1].trigger('submit.prevent')
    await flushPromises()

    expect(sessionsApi.addLog).toHaveBeenCalledWith(1, 'Goblins!', 'none')
    expect(wrapper.text()).toContain('Goblins!')
  })
})
