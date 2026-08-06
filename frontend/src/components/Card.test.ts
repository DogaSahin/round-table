import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import Card from './Card.vue'

describe('Card', () => {
  it('renders slot content inside a card surface', () => {
    const wrapper = mount(Card, { slots: { default: '<p>Contents</p>' } })

    expect(wrapper.find('.card').exists()).toBe(true)
    expect(wrapper.html()).toContain('<p>Contents</p>')
  })
})
