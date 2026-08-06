import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import Badge from './Badge.vue'

describe('Badge', () => {
  it('renders slot content and defaults to the default variant', () => {
    const wrapper = mount(Badge, { slots: { default: 'CR 1/8' } })

    expect(wrapper.text()).toBe('CR 1/8')
    expect(wrapper.classes()).toContain('badge--default')
  })

  it('applies the requested variant class', () => {
    const wrapper = mount(Badge, { props: { variant: 'success' }, slots: { default: 'Resist' } })

    expect(wrapper.classes()).toContain('badge--success')
  })
})
