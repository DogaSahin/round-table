import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ActionEditor from './ActionEditor.vue'
import type { AbilityName } from './api'

interface DamageRowState {
  dice: string
  damageType: string
}

interface ActionFormState {
  clientKey: string
  name: string
  description: string
  attackBonus: number | null
  reachOrRange: string
  target: string
  damage: DamageRowState[]
  hasSave: boolean
  saveAbility: AbilityName | null
  saveDc: number | null
  saveEffect: string
  recharge: string
  usesPerDay: number | null
  cost: number
  multiattackRefs: string[]
}

const DAMAGE_TYPE_OPTIONS = [
  { value: 'fire', label: 'fire' },
  { value: 'cold', label: 'cold' },
]

function emptyAction(): ActionFormState {
  return {
    clientKey: 'key-1',
    name: '',
    description: '',
    attackBonus: null,
    reachOrRange: '',
    target: '',
    damage: [],
    hasSave: false,
    saveAbility: null,
    saveDc: null,
    saveEffect: '',
    recharge: '',
    usesPerDay: null,
    cost: 1,
    multiattackRefs: [],
  }
}

describe('ActionEditor', () => {
  it('does not render a Cost field when showCost is false', () => {
    const wrapper = mount(ActionEditor, {
      props: {
        modelValue: emptyAction(),
        showCost: false,
        otherActionNames: [],
        errors: {},
        damageTypeOptions: DAMAGE_TYPE_OPTIONS,
      },
    })

    expect(wrapper.find('input[name="cost"]').exists()).toBe(false)
  })

  it('renders a Cost field defaulting to 1 when showCost is true', () => {
    const wrapper = mount(ActionEditor, {
      props: {
        modelValue: emptyAction(),
        showCost: true,
        otherActionNames: [],
        errors: {},
        damageTypeOptions: DAMAGE_TYPE_OPTIONS,
      },
    })

    expect((wrapper.find('input[name="cost"]').element as HTMLInputElement).valueAsNumber).toBe(1)
  })

  it('renders error messages from the errors prop', () => {
    const wrapper = mount(ActionEditor, {
      props: {
        modelValue: emptyAction(),
        showCost: false,
        otherActionNames: [],
        errors: { name: 'Name is required.', description: 'Description is required.' },
        damageTypeOptions: DAMAGE_TYPE_OPTIONS,
      },
    })

    expect(wrapper.text()).toContain('Name is required.')
    expect(wrapper.text()).toContain('Description is required.')
  })

  it('emits remove when the remove button is clicked', async () => {
    const wrapper = mount(ActionEditor, {
      props: {
        modelValue: emptyAction(),
        showCost: false,
        otherActionNames: [],
        errors: {},
        damageTypeOptions: DAMAGE_TYPE_OPTIONS,
      },
    })

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Remove action')
      ?.trigger('click')

    expect(wrapper.emitted('remove')).toHaveLength(1)
  })

  it('adds a blank damage row and updates the model', async () => {
    const wrapper = mount(ActionEditor, {
      props: {
        modelValue: emptyAction(),
        showCost: false,
        otherActionNames: [],
        errors: {},
        damageTypeOptions: DAMAGE_TYPE_OPTIONS,
      },
    })

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add damage')
      ?.trigger('click')

    const emitted = wrapper.emitted('update:modelValue')
    expect(emitted).toBeTruthy()
    const last = emitted![emitted!.length - 1][0] as ActionFormState
    expect(last.damage).toEqual([{ dice: '', damageType: '' }])
  })

  it('removes only the targeted damage row', async () => {
    const action = { ...emptyAction(), damage: [{ dice: '1d6', damageType: 'fire' }] }
    const wrapper = mount(ActionEditor, {
      props: {
        modelValue: action,
        showCost: false,
        otherActionNames: [],
        errors: {},
        damageTypeOptions: DAMAGE_TYPE_OPTIONS,
      },
    })

    await wrapper.find('button[aria-label="Remove damage entry"]').trigger('click')

    const emitted = wrapper.emitted('update:modelValue')
    const last = emitted![emitted!.length - 1][0] as ActionFormState
    expect(last.damage).toEqual([])
  })

  it('shows the save-effect fields only when "Has saving throw" is checked', async () => {
    const wrapper = mount(ActionEditor, {
      props: {
        modelValue: emptyAction(),
        showCost: false,
        otherActionNames: [],
        errors: {},
        damageTypeOptions: DAMAGE_TYPE_OPTIONS,
      },
    })

    expect(wrapper.find('select[name="saveAbility"]').exists()).toBe(false)

    await wrapper.find('input[name="hasSave"]').setValue(true)

    expect(wrapper.find('select[name="saveAbility"]').exists()).toBe(true)
    expect(wrapper.find('input[name="saveDc"]').exists()).toBe(true)
    expect(wrapper.find('input[name="saveEffect"]').exists()).toBe(true)
  })

  it('renders otherActionNames as a checkbox list and toggles multiattackRefs', async () => {
    const action = { ...emptyAction(), clientKey: 'multiattack-key' }
    const wrapper = mount(ActionEditor, {
      props: {
        modelValue: action,
        showCost: false,
        otherActionNames: [
          { clientKey: 'bite-key', name: 'Bite' },
          { clientKey: 'claw-key', name: 'Claw' },
        ],
        errors: {},
        damageTypeOptions: DAMAGE_TYPE_OPTIONS,
      },
    })

    expect(wrapper.text()).toContain('Bite')
    expect(wrapper.text()).toContain('Claw')

    await wrapper.find('input[name="multiattack-bite-key"]').setValue(true)

    const emitted = wrapper.emitted('update:modelValue')
    const last = emitted![emitted!.length - 1][0] as ActionFormState
    expect(last.multiattackRefs).toEqual(['bite-key'])
  })
})
