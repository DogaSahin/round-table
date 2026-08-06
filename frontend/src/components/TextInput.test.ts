import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import TextInput from './TextInput.vue'

describe('TextInput', () => {
  it('renders a text input by default and supports v-model', async () => {
    const wrapper = mount(TextInput, { props: { modelValue: '', name: 'title' } })

    const input = wrapper.find('input[name="title"]')
    expect(input.attributes('type')).toBe('text')

    await input.setValue('Hello')

    expect(wrapper.emitted('update:modelValue')).toEqual([['Hello']])
  })

  it('renders a number input and coerces the value to a number', async () => {
    const wrapper = mount(TextInput, { props: { modelValue: 0, type: 'number', name: 'hp' } })

    const input = wrapper.find('input[name="hp"]')
    expect(input.attributes('type')).toBe('number')

    await input.setValue('7')

    expect(wrapper.emitted('update:modelValue')).toEqual([[7]])
  })

  it('renders the placeholder when provided', () => {
    const wrapper = mount(TextInput, { props: { modelValue: '', placeholder: 'Enter a name' } })

    expect(wrapper.find('input').attributes('placeholder')).toBe('Enter a name')
  })

  it('renders an error message when provided', () => {
    const wrapper = mount(TextInput, { props: { modelValue: '', error: 'Name is required.' } })

    expect(wrapper.text()).toContain('Name is required.')
  })

  it('renders no error message when absent', () => {
    const wrapper = mount(TextInput, { props: { modelValue: '' } })

    expect(wrapper.find('.text-input__error').exists()).toBe(false)
  })
})
