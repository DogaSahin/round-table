import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import SpecialAbilityEditor from './SpecialAbilityEditor.vue'

interface SpecialAbilityFormState {
  name: string
  description: string
  recharge: string
  usesPerDay: number | null
}

function emptyAbility(): SpecialAbilityFormState {
  return { name: '', description: '', recharge: '', usesPerDay: null }
}

describe('SpecialAbilityEditor', () => {
  it('renders error messages from the errors prop', () => {
    const wrapper = mount(SpecialAbilityEditor, {
      props: {
        modelValue: emptyAbility(),
        errors: { name: 'Name is required.', description: 'Description is required.' },
      },
    })

    expect(wrapper.text()).toContain('Name is required.')
    expect(wrapper.text()).toContain('Description is required.')
  })

  it('does not show errors for optional fields left blank', () => {
    const wrapper = mount(SpecialAbilityEditor, {
      props: { modelValue: emptyAbility(), errors: {} },
    })

    expect(wrapper.find('.field-error').exists()).toBe(false)
  })

  it('renders the pre-filled values from modelValue', () => {
    const wrapper = mount(SpecialAbilityEditor, {
      props: {
        modelValue: {
          name: 'Keen Smell',
          description: 'Advantage on smell-based Perception checks.',
          recharge: '',
          usesPerDay: 3,
        },
        errors: {},
      },
    })

    expect((wrapper.find('input[name="name"]').element as HTMLInputElement).value).toBe(
      'Keen Smell',
    )
    expect(
      (wrapper.find('textarea[name="description"]').element as HTMLTextAreaElement).value,
    ).toBe('Advantage on smell-based Perception checks.')
    expect(
      (wrapper.find('input[name="usesPerDay"]').element as HTMLInputElement).valueAsNumber,
    ).toBe(3)
  })

  it('emits remove when the remove button is clicked', async () => {
    const wrapper = mount(SpecialAbilityEditor, {
      props: { modelValue: emptyAbility(), errors: {} },
    })

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Remove special ability')
      ?.trigger('click')

    expect(wrapper.emitted('remove')).toHaveLength(1)
  })
})
