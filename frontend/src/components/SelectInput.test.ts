import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import SelectInput from './SelectInput.vue'

const OPTIONS = [
  { value: 'a', label: 'Option A' },
  { value: 'b', label: 'Option B' },
]

describe('SelectInput', () => {
  it('renders one option per entry with the given labels', () => {
    const wrapper = mount(SelectInput, { props: { modelValue: 'a', options: OPTIONS } })

    const optionEls = wrapper.findAll('option')
    expect(optionEls).toHaveLength(2)
    expect(optionEls[0].text()).toBe('Option A')
    expect(optionEls[1].text()).toBe('Option B')
  })

  it('reflects the current modelValue as the selected option', () => {
    const wrapper = mount(SelectInput, { props: { modelValue: 'b', options: OPTIONS } })

    expect((wrapper.find('select').element as HTMLSelectElement).value).toBe('b')
  })

  it('emits update:modelValue when a new option is chosen', async () => {
    const wrapper = mount(SelectInput, { props: { modelValue: 'a', options: OPTIONS } })

    await wrapper.find('select').setValue('b')

    expect(wrapper.emitted('update:modelValue')).toEqual([['b']])
  })

  it('applies the name attribute when provided', () => {
    const wrapper = mount(SelectInput, {
      props: { modelValue: 'a', options: OPTIONS, name: 'creatureType' },
    })

    expect(wrapper.find('select').attributes('name')).toBe('creatureType')
  })
})
