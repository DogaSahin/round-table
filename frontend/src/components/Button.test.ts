import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from './Button.vue'

describe('Button', () => {
  it('renders slot content and defaults to the secondary variant and button type', () => {
    const wrapper = mount(Button, { slots: { default: 'Click me' } })

    expect(wrapper.text()).toBe('Click me')
    expect(wrapper.classes()).toContain('button--secondary')
    expect(wrapper.attributes('type')).toBe('button')
  })

  it('applies the requested variant class', () => {
    const wrapper = mount(Button, { props: { variant: 'primary' }, slots: { default: 'Go' } })

    expect(wrapper.classes()).toContain('button--primary')
  })

  it('passes through the disabled attribute', () => {
    const wrapper = mount(Button, { props: { disabled: true } })

    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('passes through the type attribute', () => {
    const wrapper = mount(Button, { props: { type: 'submit' } })

    expect(wrapper.attributes('type')).toBe('submit')
  })

  it('forwards native click events to the parent via attribute fallthrough', async () => {
    const onClick = vi.fn()
    const wrapper = mount(Button, { attrs: { onClick }, slots: { default: 'Go' } })

    await wrapper.trigger('click')

    expect(onClick).toHaveBeenCalledTimes(1)
  })
})
