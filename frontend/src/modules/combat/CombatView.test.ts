import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import CombatView from './CombatView.vue'
import * as combatApi from './api'
import type { Combatant, EncounterDetail } from './api'

function makeCombatant(overrides: Partial<Combatant> = {}): Combatant {
  return {
    id: 1,
    name: 'Goblin',
    initiative: 10,
    hp_current: 7,
    hp_max: 7,
    ac: 15,
    conditions: [],
    concentration: false,
    sort_order: 0,
    is_pc: false,
    visible_to_players: false,
    npc_id: null,
    token_id: null,
    ...overrides,
  }
}

function makeEncounter(overrides: Partial<EncounterDetail> = {}): EncounterDetail {
  return {
    id: 1,
    name: 'Goblin Ambush',
    round: 1,
    active_combatant_id: null,
    is_active: false,
    combatants: [],
    ...overrides,
  }
}

describe('CombatView', () => {
  it('loads the roster on mount', async () => {
    vi.spyOn(combatApi, 'listEncounters').mockResolvedValue([
      { id: 1, name: 'Goblin Ambush', round: 1, is_active: false },
    ])

    const wrapper = mount(CombatView)
    await flushPromises()

    expect(wrapper.text()).toContain('Goblin Ambush')
  })

  it('creates an encounter and selects it', async () => {
    vi.spyOn(combatApi, 'listEncounters').mockResolvedValue([])
    vi.spyOn(combatApi, 'createEncounter').mockResolvedValue(makeEncounter())

    const wrapper = mount(CombatView)
    await flushPromises()

    await wrapper.find('input[placeholder="Encounter name"]').setValue('Goblin Ambush')
    await wrapper.find('form.combat-create-form').trigger('submit.prevent')
    await flushPromises()

    expect(combatApi.createEncounter).toHaveBeenCalledWith('Goblin Ambush')
    expect(wrapper.text()).toContain('Goblin Ambush')
  })

  it('damages a combatant and re-renders HP from the mocked response', async () => {
    const initialDetail = makeEncounter({ combatants: [makeCombatant()] })
    const afterDamage = makeEncounter({ combatants: [makeCombatant({ hp_current: 2 })] })

    vi.spyOn(combatApi, 'listEncounters').mockResolvedValue([
      { id: 1, name: 'Goblin Ambush', round: 1, is_active: false },
    ])
    const fetchSpy = vi
      .spyOn(combatApi, 'fetchEncounter')
      .mockResolvedValueOnce(initialDetail)
      .mockResolvedValueOnce(afterDamage)
    vi.spyOn(combatApi, 'damageCombatant').mockResolvedValue(makeCombatant({ hp_current: 2 }))

    const wrapper = mount(CombatView)
    await flushPromises()

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Goblin Ambush (round 1)')
      ?.trigger('click')
    await flushPromises()

    await wrapper.find('[data-damage-input="1"]').setValue(5)
    await wrapper.find('[data-damage-button="1"]').trigger('click')
    await flushPromises()

    expect(combatApi.damageCombatant).toHaveBeenCalledWith(1, 5)
    expect(fetchSpy).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('2/7')
  })

  it('advances the turn and marks the newly active combatant row', async () => {
    const initialDetail = makeEncounter({
      active_combatant_id: 1,
      combatants: [
        makeCombatant({ id: 1, name: 'Goblin' }),
        makeCombatant({ id: 2, name: 'Orc', sort_order: 1 }),
      ],
    })
    const afterNextTurn = makeEncounter({
      active_combatant_id: 2,
      combatants: [
        makeCombatant({ id: 1, name: 'Goblin' }),
        makeCombatant({ id: 2, name: 'Orc', sort_order: 1 }),
      ],
    })

    vi.spyOn(combatApi, 'listEncounters').mockResolvedValue([
      { id: 1, name: 'Goblin Ambush', round: 1, is_active: false },
    ])
    vi.spyOn(combatApi, 'fetchEncounter')
      .mockResolvedValueOnce(initialDetail)
      .mockResolvedValueOnce(afterNextTurn)
    vi.spyOn(combatApi, 'nextTurn').mockResolvedValue(afterNextTurn)

    const wrapper = mount(CombatView)
    await flushPromises()

    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Goblin Ambush (round 1)')
      ?.trigger('click')
    await flushPromises()

    await wrapper.find('[data-next-turn]').trigger('click')
    await flushPromises()

    expect(combatApi.nextTurn).toHaveBeenCalledWith(1)
    const activeRow = wrapper.find('[data-combatant-id="2"]')
    expect(activeRow.classes()).toContain('combatant-row--active')
    const previousRow = wrapper.find('[data-combatant-id="1"]')
    expect(previousRow.classes()).not.toContain('combatant-row--active')
  })
})
