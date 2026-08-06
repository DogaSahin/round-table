import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import Checkbox from './Checkbox.vue'

describe('Checkbox', () => {
  it('reflects the current modelValue as checked state', () => {
    const wrapper = mount(Checkbox, { props: { modelValue: true }, slots: { default: 'Hover' } })

    expect((wrapper.find('input').element as HTMLInputElement).checked).toBe(true)
  })

  it('renders the slot content as the label', () => {
    const wrapper = mount(Checkbox, { props: { modelValue: false }, slots: { default: 'Hover' } })

    expect(wrapper.text()).toBe('Hover')
  })

  it('emits update:modelValue when toggled', async () => {
    const wrapper = mount(Checkbox, { props: { modelValue: false } })

    await wrapper.find('input').setValue(true)

    expect(wrapper.emitted('update:modelValue')).toEqual([[true]])
  })

  it('applies the name attribute when provided', () => {
    const wrapper = mount(Checkbox, { props: { modelValue: false, name: 'hover' } })

    expect(wrapper.find('input').attributes('name')).toBe('hover')
  })
})
