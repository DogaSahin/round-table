import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import TagListField from './TagListField.vue'

describe('TagListField', () => {
  it('renders one text input per existing entry in free-text mode', () => {
    const wrapper = mount(TagListField, {
      props: { modelValue: ['Common', 'Draconic'], label: 'Languages', fieldName: 'languages' },
    })

    const inputs = wrapper.findAll('input[type="text"]')
    expect(inputs).toHaveLength(2)
    expect((inputs[0].element as HTMLInputElement).value).toBe('Common')
    expect((inputs[1].element as HTMLInputElement).value).toBe('Draconic')
  })

  it('emits a new blank row when Add is clicked', async () => {
    const wrapper = mount(TagListField, {
      props: { modelValue: [], label: 'Languages', fieldName: 'languages' },
    })

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add Languages')
      ?.trigger('click')

    expect(wrapper.emitted('update:modelValue')).toEqual([[['']]])
  })

  it('emits the typed value for a free-text row', async () => {
    const wrapper = mount(TagListField, {
      props: { modelValue: ['Common'], label: 'Languages', fieldName: 'languages' },
    })

    await wrapper.find('input[type="text"]').setValue('Draconic')

    expect(wrapper.emitted('update:modelValue')).toEqual([[['Draconic']]])
  })

  it('removes only the targeted row', async () => {
    const wrapper = mount(TagListField, {
      props: { modelValue: ['Common', 'Draconic'], label: 'Languages', fieldName: 'languages' },
    })

    await wrapper.findAll('button[aria-label="Remove Languages entry"]')[0].trigger('click')

    expect(wrapper.emitted('update:modelValue')).toEqual([[['Draconic']]])
  })

  it('renders a select with the given options plus "Other (custom)..." in dropdown mode', () => {
    const wrapper = mount(TagListField, {
      props: {
        modelValue: ['fire'],
        label: 'Damage Resistances',
        fieldName: 'damageResistances',
        options: [
          { value: 'fire', label: 'fire' },
          { value: 'cold', label: 'cold' },
        ],
      },
    })

    const select = wrapper.find('select')
    expect(select.exists()).toBe(true)
    expect((select.element as HTMLSelectElement).value).toBe('fire')
    expect(wrapper.text()).toContain('Other (custom)...')
  })

  it('excludes options already chosen in other rows of the same field', () => {
    const wrapper = mount(TagListField, {
      props: {
        modelValue: ['fire', 'cold'],
        label: 'Damage Resistances',
        fieldName: 'damageResistances',
        options: [
          { value: 'fire', label: 'fire' },
          { value: 'cold', label: 'cold' },
          { value: 'acid', label: 'acid' },
        ],
      },
    })

    const secondRowOptionTexts = wrapper
      .findAll('select')[1]
      .findAll('option')
      .map((o) => o.text())
    expect(secondRowOptionTexts).not.toContain('fire')
    expect(secondRowOptionTexts).toContain('cold')
    expect(secondRowOptionTexts).toContain('acid')
  })

  it('swaps to a text input when "Other (custom)..." is selected', async () => {
    const wrapper = mount(TagListField, {
      props: {
        modelValue: [''],
        label: 'Damage Resistances',
        fieldName: 'damageResistances',
        options: [{ value: 'fire', label: 'fire' }],
      },
    })

    await wrapper.find('select').setValue('__custom__')

    expect(wrapper.find('select').exists()).toBe(false)
    expect(wrapper.find('input[type="text"]').exists()).toBe(true)
  })

  it('re-derives custom-row detection when modelValue is replaced wholesale (async parent load)', async () => {
    const wrapper = mount(TagListField, {
      props: {
        modelValue: [],
        label: 'Damage Resistances',
        fieldName: 'damageResistances',
        options: [{ value: 'fire', label: 'fire' }],
      },
    })

    await wrapper.setProps({
      modelValue: ['fire', 'bludgeoning from nonmagical attacks'],
    })

    const selects = wrapper.findAll('select')
    const textInputs = wrapper.findAll('input[type="text"]')
    expect(selects).toHaveLength(1)
    expect((selects[0].element as HTMLSelectElement).value).toBe('fire')
    expect(textInputs).toHaveLength(1)
    expect((textInputs[0].element as HTMLInputElement).value).toBe(
      'bludgeoning from nonmagical attacks',
    )
  })
})
