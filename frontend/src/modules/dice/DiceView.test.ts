import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import DiceView from './DiceView.vue'
import * as diceApi from './api'

describe('DiceView', () => {
  it('loads history on mount', async () => {
    vi.spyOn(diceApi, 'fetchHistory').mockResolvedValue([
      { id: 1, expression: '1d20', result: 15, rolled_at: '2026-01-01T00:00:00Z' },
    ])

    const wrapper = mount(DiceView)
    await flushPromises()

    expect(wrapper.text()).toContain('1d20')
    expect(wrapper.text()).toContain('15')
  })

  it('rolls the entered expression and displays the total', async () => {
    vi.spyOn(diceApi, 'fetchHistory').mockResolvedValue([])
    vi.spyOn(diceApi, 'rollDice').mockResolvedValue({
      expression: '2d6+3',
      total: 12,
      terms: [],
    })

    const wrapper = mount(DiceView)
    await flushPromises()

    await wrapper.find('input').setValue('2d6+3')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(diceApi.rollDice).toHaveBeenCalledWith('2d6+3')
    expect(wrapper.text()).toContain('12')
  })
})
