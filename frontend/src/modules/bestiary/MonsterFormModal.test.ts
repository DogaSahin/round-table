import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import MonsterFormModal from './MonsterFormModal.vue'
import ActionEditor from './ActionEditor.vue'
import SpecialAbilityEditor from './SpecialAbilityEditor.vue'
import * as bestiaryApi from './api'
import type { BestiaryMonsterDetail, Statblock } from './api'

const EXISTING_STATBLOCK: Statblock = {
  size: 'Small',
  creature_type: 'beast',
  subtype: null,
  alignment: 'unaligned',
  armor_class: 12,
  armor_class_notes: null,
  hit_points: 7,
  hit_dice: '2d6',
  speed: { walk: 30, fly: null, swim: null, climb: null, burrow: null, hover: false },
  ability_scores: {
    strength: 8,
    dexterity: 15,
    constitution: 11,
    intelligence: 2,
    wisdom: 10,
    charisma: 4,
  },
  saving_throws: [{ ability: 'wisdom', bonus: 2 }],
  skills: [{ skill: 'Perception', bonus: 4 }],
  damage_vulnerabilities: [],
  damage_resistances: ['fire'],
  damage_immunities: [],
  condition_immunities: ['poisoned'],
  senses: ['darkvision 60 ft.'],
  languages: ['Common'],
  challenge_rating: 0.125,
  experience_points: 25,
  special_abilities: [
    {
      id: 'keen-smell',
      name: 'Keen Smell',
      description: 'The rat has advantage on Wisdom (Perception) checks that rely on smell.',
      recharge: null,
      uses_per_day: null,
    },
  ],
  actions: [
    {
      id: 'bite',
      name: 'Bite',
      description: 'A bite attack.',
      attack_bonus: 4,
      reach_or_range: '5 ft.',
      target: 'one target',
      damage: [{ dice: '1d4', damage_type: 'piercing' }],
      save: null,
      recharge: null,
      uses_per_day: null,
      multiattack_refs: [],
    },
    {
      id: 'multiattack',
      name: 'Multiattack',
      description: 'The rat makes two bite attacks.',
      attack_bonus: null,
      reach_or_range: null,
      target: null,
      damage: [],
      save: null,
      recharge: null,
      uses_per_day: null,
      multiattack_refs: ['bite'],
    },
  ],
  legendary_actions: [
    {
      id: 'detect',
      name: 'Detect',
      description: 'The rat makes a Wisdom (Perception) check.',
      attack_bonus: null,
      reach_or_range: null,
      target: null,
      damage: [],
      save: null,
      recharge: null,
      uses_per_day: null,
      multiattack_refs: [],
      cost: 1,
    },
  ],
  legendary_actions_per_turn: 3,
}

const EXISTING_DETAIL: BestiaryMonsterDetail = {
  id: 1,
  name: 'Giant Rat',
  slug: 'giant-rat',
  statblock: EXISTING_STATBLOCK,
  image_url: null,
  is_favorite: false,
  cloned_from_content_id: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

// One real action ("bite") plus a "multiattack" action whose multiattack_refs includes both a
// resolvable id and an id that matches no action in the list (orphaned/unresolvable data).
const STATBLOCK_WITH_ORPHAN_REF: Statblock = {
  ...EXISTING_STATBLOCK,
  actions: [
    {
      id: 'bite',
      name: 'Bite',
      description: 'A bite attack.',
      attack_bonus: null,
      reach_or_range: null,
      target: null,
      damage: [],
      save: null,
      recharge: null,
      uses_per_day: null,
      multiattack_refs: [],
    },
    {
      id: 'multiattack',
      name: 'Multiattack',
      description: 'Two bite attacks.',
      attack_bonus: null,
      reach_or_range: null,
      target: null,
      damage: [],
      save: null,
      recharge: null,
      uses_per_day: null,
      multiattack_refs: ['bite', 'nonexistent-action'],
    },
  ],
  legendary_actions: [],
}

const DETAIL_WITH_ORPHAN_REF: BestiaryMonsterDetail = {
  ...EXISTING_DETAIL,
  statblock: STATBLOCK_WITH_ORPHAN_REF,
}

let wrapper: VueWrapper | null = null

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
})

describe('MonsterFormModal', () => {
  it('renders create-mode defaults', () => {
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })

    expect(wrapper.text()).toContain('New Monster')
    expect((wrapper.find('input[name="name"]').element as HTMLInputElement).value).toBe('')
    expect((wrapper.find('input[name="size"]').element as HTMLInputElement).value).toBe('Medium')
    expect((wrapper.find('input[name="strength"]').element as HTMLInputElement).valueAsNumber).toBe(
      10,
    )
    expect(
      (wrapper.find('select[name="challengeRating"]').element as HTMLSelectElement).value,
    ).toBe('0')
    expect(
      (wrapper.find('input[name="savingThrow-strength"]').element as HTMLInputElement).value,
    ).toBe('')
    expect(wrapper.find('[name^="skill-"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Damage Vulnerabilities')
    expect(wrapper.text()).toContain('Languages')
    expect(wrapper.find('[name^="languages-"]').exists()).toBe(false)
    expect(wrapper.findAllComponents(ActionEditor)).toHaveLength(0)
    expect(wrapper.findAllComponents(SpecialAbilityEditor)).toHaveLength(0)
    expect(
      (wrapper.find('input[name="legendaryActionsPerTurn"]').element as HTMLInputElement).value,
    ).toBe('')
  })

  it('pre-fills every visible field from a fetched monster in edit mode', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(EXISTING_DETAIL)

    wrapper = mount(MonsterFormModal, { props: { monsterId: 1 } })
    await flushPromises()

    expect(wrapper.text()).toContain('Edit Monster')
    expect((wrapper.find('input[name="name"]').element as HTMLInputElement).value).toBe('Giant Rat')
    expect((wrapper.find('input[name="size"]').element as HTMLInputElement).value).toBe('Small')
    expect((wrapper.find('input[name="creatureType"]').element as HTMLInputElement).value).toBe(
      'beast',
    )
    expect((wrapper.find('input[name="strength"]').element as HTMLInputElement).valueAsNumber).toBe(
      8,
    )
    expect(
      (wrapper.find('input[name="hitPoints"]').element as HTMLInputElement).valueAsNumber,
    ).toBe(7)
    expect(
      (wrapper.find('input[name="savingThrow-wisdom"]').element as HTMLInputElement).valueAsNumber,
    ).toBe(2)
    expect((wrapper.find('select[name="skill-0"]').element as HTMLSelectElement).value).toBe(
      'Perception',
    )
    expect(
      (wrapper.find('select[name="damageResistances-0"]').element as HTMLSelectElement).value,
    ).toBe('fire')
    expect((wrapper.find('input[name="languages-0"]').element as HTMLInputElement).value).toBe(
      'Common',
    )

    const actionEditors = wrapper.findAllComponents(ActionEditor)
    expect(actionEditors).toHaveLength(3) // 2 actions + 1 legendary action
    expect((actionEditors[0].find('input[name="name"]').element as HTMLInputElement).value).toBe(
      'Bite',
    )
    expect(
      (actionEditors[0].find('input[name="damageDice-0"]').element as HTMLInputElement).value,
    ).toBe('1d4')
    expect((actionEditors[1].find('input[name="name"]').element as HTMLInputElement).value).toBe(
      'Multiattack',
    )
    // "Multiattack"'s multiattack_refs: ['bite'] must resolve to a checked reference to "Bite" —
    // the only other action in the same list. The checkbox's exact name is keyed by a randomly
    // generated clientKey (not the original "bite" id), but it is always prefixed
    // "multiattack-", which distinguishes it from the editor's other checkbox ("hasSave").
    const multiattackCheckbox = actionEditors[1].find('input[name^="multiattack-"]')
    expect(multiattackCheckbox.exists()).toBe(true)
    expect((multiattackCheckbox.element as HTMLInputElement).checked).toBe(true)
    expect(actionEditors[1].text()).toContain('Bite')
    expect(actionEditors[2].props('showCost')).toBe(true)
    expect(
      (actionEditors[2].find('input[name="cost"]').element as HTMLInputElement).valueAsNumber,
    ).toBe(1)
    expect(
      (wrapper.find('input[name="legendaryActionsPerTurn"]').element as HTMLInputElement)
        .valueAsNumber,
    ).toBe(3)

    const abilityEditors = wrapper.findAllComponents(SpecialAbilityEditor)
    expect(abilityEditors).toHaveLength(1)
    expect((abilityEditors[0].find('input[name="name"]').element as HTMLInputElement).value).toBe(
      'Keen Smell',
    )
  })

  it('blocks submit and shows inline errors for missing required text fields', async () => {
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster')
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })

    await wrapper.find('input[name="size"]').setValue('')
    await wrapper.find('input[name="alignment"]').setValue('')
    await wrapper.find('input[name="hitDice"]').setValue('')
    // name and creatureType are already empty in create mode.
    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.text()).toContain('Name is required.')
    expect(wrapper.text()).toContain('Size is required.')
    expect(wrapper.text()).toContain('Type is required.')
    expect(wrapper.text()).toContain('Alignment is required.')
    expect(wrapper.text()).toContain('Hit dice is required.')
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('blocks submit and shows inline errors for negative numeric fields', async () => {
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster')
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })

    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('input[name="armorClass"]').setValue('-1')
    await wrapper.find('input[name="hitPoints"]').setValue('-1')
    await wrapper.find('input[name="experiencePoints"]').setValue('-1')
    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.text()).toContain('Armor class cannot be negative.')
    expect(wrapper.text()).toContain('Hit points cannot be negative.')
    expect(wrapper.text()).toContain('Experience points cannot be negative.')
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('blocks submit and shows inline errors for out-of-range ability scores', async () => {
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster')
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })

    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('input[name="strength"]').setValue('0')
    await wrapper.find('input[name="charisma"]').setValue('31')
    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.text()).toContain('Must be between 1 and 30.')
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('creates a new monster with the schema-default base merged with form values', async () => {
    const created: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Test Monster' }
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster').mockResolvedValue(created)

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    const payload = createSpy.mock.calls[0][0]
    expect(payload.name).toBe('Test Monster')
    expect(payload.statblock.creature_type).toBe('beast')
    expect(payload.statblock.saving_throws).toEqual([])
    expect(payload.statblock.skills).toEqual([])
    expect(payload.statblock.actions).toEqual([])
    expect(payload.statblock.legendary_actions).toEqual([])
    expect(payload.statblock.legendary_actions_per_turn).toBe(null)
    expect(payload.statblock.special_abilities).toEqual([])
    expect(payload.image_url).toBe(null)
    expect(wrapper.emitted('saved')).toEqual([[created]])
  })

  it('shows an image preview only when a URL is entered', async () => {
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })

    expect(wrapper.find('.monster-form-modal__image-preview').exists()).toBe(false)

    await wrapper.find('input[name="imageUrl"]').setValue('https://example.com/owlbear.png')

    const preview = wrapper.find('.monster-form-modal__image-preview')
    expect(preview.exists()).toBe(true)
    expect(preview.attributes('src')).toBe('https://example.com/owlbear.png')

    await wrapper.find('input[name="imageUrl"]').setValue('')
    expect(wrapper.find('.monster-form-modal__image-preview').exists()).toBe(false)
  })

  it('includes a trimmed image_url in a create submission when provided', async () => {
    const created: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Test Monster' }
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster').mockResolvedValue(created)

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('input[name="imageUrl"]').setValue('  https://example.com/owlbear.png  ')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    expect(createSpy.mock.calls[0][0].image_url).toBe('https://example.com/owlbear.png')
  })

  it('pre-fills the image URL from a fetched monster in edit mode', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue({
      ...EXISTING_DETAIL,
      image_url: 'https://example.com/giant-rat.png',
    })

    wrapper = mount(MonsterFormModal, { props: { monsterId: 1 } })
    await flushPromises()

    expect((wrapper.find('input[name="imageUrl"]').element as HTMLInputElement).value).toBe(
      'https://example.com/giant-rat.png',
    )
    expect(wrapper.find('.monster-form-modal__image-preview').attributes('src')).toBe(
      'https://example.com/giant-rat.png',
    )
  })

  it('includes saving throws, skills, and tag-list entries in a create submission', async () => {
    const created: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Test Monster' }
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster').mockResolvedValue(created)

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('input[name="savingThrow-dexterity"]').setValue('3')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add skill')
      ?.trigger('click')
    await wrapper.find('select[name="skill-0"]').setValue('Stealth')
    await wrapper.find('input[name="skillBonus-0"]').setValue('5')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add Damage Resistances')
      ?.trigger('click')
    await wrapper.find('select[name="damageResistances-0"]').setValue('cold')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add Languages')
      ?.trigger('click')
    await wrapper.find('input[name="languages-0"]').setValue('Elvish')

    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    const payload = createSpy.mock.calls[0][0]
    expect(payload.statblock.saving_throws).toEqual([{ ability: 'dexterity', bonus: 3 }])
    expect(payload.statblock.skills).toEqual([{ skill: 'Stealth', bonus: 5 }])
    expect(payload.statblock.damage_resistances).toEqual(['cold'])
    expect(payload.statblock.languages).toEqual(['Elvish'])
  })

  it('drops incomplete skill and tag-list rows from the submitted payload without blocking submit', async () => {
    const created: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Test Monster' }
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster').mockResolvedValue(created)

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add skill')
      ?.trigger('click')
    // Leave the skill row's select and bonus unfilled.

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add Languages')
      ?.trigger('click')
    // Leave the language row blank.

    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    const payload = createSpy.mock.calls[0][0]
    expect(payload.statblock.skills).toEqual([])
    expect(payload.statblock.languages).toEqual([])
  })

  it('creates a monster with an action, a damage component, and a checked save effect', async () => {
    const created: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Test Monster' }
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster').mockResolvedValue(created)

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add action')
      ?.trigger('click')

    const actionEditor = wrapper.findComponent(ActionEditor)
    await actionEditor.find('input[name="name"]').setValue('Bite')
    await actionEditor.find('textarea[name="description"]').setValue('A bite attack.')
    await actionEditor
      .findAll('button')
      .find((b) => b.text() === '+ Add damage')
      ?.trigger('click')
    await actionEditor.find('input[name="damageDice-0"]').setValue('1d4')
    await actionEditor.find('select[name="damageType-0"]').setValue('piercing')
    await actionEditor.find('input[name="hasSave"]').setValue(true)
    await actionEditor.find('select[name="saveAbility"]').setValue('dexterity')
    await actionEditor.find('input[name="saveDc"]').setValue('12')
    await actionEditor.find('input[name="saveEffect"]').setValue('Half damage.')

    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    const payload = createSpy.mock.calls[0][0]
    expect(payload.statblock.actions).toEqual([
      {
        id: 'bite',
        name: 'Bite',
        description: 'A bite attack.',
        attack_bonus: null,
        reach_or_range: null,
        target: null,
        damage: [{ dice: '1d4', damage_type: 'piercing' }],
        save: { ability: 'dexterity', dc: 12, effect_on_save: 'Half damage.' },
        recharge: null,
        uses_per_day: null,
        multiattack_refs: [],
      },
    ])
  })

  it('resolves a multiattack reference to the referenced action id on submit', async () => {
    const created: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Test Monster' }
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster').mockResolvedValue(created)

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')

    const addAction = () =>
      wrapper!
        .findAll('button')
        .find((b) => b.text() === '+ Add action')
        ?.trigger('click')

    await addAction()
    await addAction()

    const editors = wrapper.findAllComponents(ActionEditor)
    await editors[0].find('input[name="name"]').setValue('Bite')
    await editors[0].find('textarea[name="description"]').setValue('A bite attack.')
    await editors[1].find('input[name="name"]').setValue('Multiattack')
    await editors[1].find('textarea[name="description"]').setValue('Two bite attacks.')

    // The second editor's multiattack fieldset now has exactly one checkbox, referencing the
    // first action ("Bite") — the checkbox's exact name is keyed by a randomly generated
    // clientKey, but it is always prefixed "multiattack-", which distinguishes it from the
    // editor's other checkbox ("hasSave").
    const multiattackEditor = wrapper.findAllComponents(ActionEditor)[1]
    await multiattackEditor.find('input[name^="multiattack-"]').setValue(true)

    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    const payload = createSpy.mock.calls[0][0]
    const multiattackAction = payload.statblock.actions.find((a) => a.name === 'Multiattack')
    expect(multiattackAction?.multiattack_refs).toEqual(['bite'])
  })

  it('keeps a multiattack reference resolved to the correct action after it is renamed', async () => {
    const created: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Test Monster' }
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster').mockResolvedValue(created)

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')

    const addAction = () =>
      wrapper!
        .findAll('button')
        .find((b) => b.text() === '+ Add action')
        ?.trigger('click')

    await addAction()
    await addAction()

    const editors = wrapper.findAllComponents(ActionEditor)
    await editors[0].find('input[name="name"]').setValue('Bite')
    await editors[0].find('textarea[name="description"]').setValue('A bite attack.')
    await editors[1].find('input[name="name"]').setValue('Multiattack')
    await editors[1].find('textarea[name="description"]').setValue('Two bite attacks.')

    // Check the reference to "Bite" while it is still named "Bite" — the checkbox tracks the
    // action's clientKey, not its name, so this must survive the rename below.
    const multiattackEditor = wrapper.findAllComponents(ActionEditor)[1]
    await multiattackEditor.find('input[name^="multiattack-"]').setValue(true)

    // Rename the referenced action *after* the reference was checked.
    await wrapper
      .findAllComponents(ActionEditor)[0]
      .find('input[name="name"]')
      .setValue('Vicious Bite')

    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    const payload = createSpy.mock.calls[0][0]
    const multiattackAction = payload.statblock.actions.find((a) => a.name === 'Multiattack')
    expect(multiattackAction?.multiattack_refs).toEqual(['vicious-bite'])
  })

  it('includes a non-default legendary action cost in a create submission', async () => {
    const created: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Test Monster' }
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster').mockResolvedValue(created)

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add legendary action')
      ?.trigger('click')

    const legendaryEditor = wrapper.findComponent(ActionEditor)
    await legendaryEditor.find('input[name="name"]').setValue('Tail Swipe')
    await legendaryEditor.find('textarea[name="description"]').setValue('A swipe of the tail.')
    await legendaryEditor.find('input[name="cost"]').setValue('3')

    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    const payload = createSpy.mock.calls[0][0]
    expect(payload.statblock.legendary_actions[0]?.cost).toBe(3)
  })

  it('silently drops an unresolvable multiattack reference when loading a monster', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(DETAIL_WITH_ORPHAN_REF)

    wrapper = mount(MonsterFormModal, { props: { monsterId: 1 } })
    await flushPromises()

    const actionEditors = wrapper.findAllComponents(ActionEditor)
    expect(actionEditors).toHaveLength(2)

    // The "Multiattack" action's multiattack_refs is ['bite', 'nonexistent-action']. Only 'bite'
    // resolves to a real action, so exactly one checkbox should exist (and be checked) — the
    // orphaned reference must not crash the load or surface as a phantom checked entry.
    const multiattackEditor = actionEditors[1]
    const multiattackCheckboxes = multiattackEditor.findAll('input[name^="multiattack-"]')
    expect(multiattackCheckboxes).toHaveLength(1)
    expect((multiattackCheckboxes[0].element as HTMLInputElement).checked).toBe(true)
  })

  it('blocks submit and shows an inline error when an action has no name', async () => {
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster')
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add action')
      ?.trigger('click')
    // Leave the action's name and description blank.

    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.text()).toContain('Name is required.')
    expect(wrapper.text()).toContain('Description is required.')
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('includes a special ability in a create submission', async () => {
    const created: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Test Monster' }
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster').mockResolvedValue(created)

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add special ability')
      ?.trigger('click')

    const abilityEditor = wrapper.findComponent(SpecialAbilityEditor)
    await abilityEditor.find('input[name="name"]').setValue('Keen Smell')
    await abilityEditor
      .find('textarea[name="description"]')
      .setValue('Advantage on smell-based Perception checks.')
    await abilityEditor.find('input[name="recharge"]').setValue('5-6')
    await abilityEditor.find('input[name="usesPerDay"]').setValue('2')

    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createSpy).toHaveBeenCalledTimes(1)
    const payload = createSpy.mock.calls[0][0]
    expect(payload.statblock.special_abilities).toEqual([
      {
        id: 'keen-smell',
        name: 'Keen Smell',
        description: 'Advantage on smell-based Perception checks.',
        recharge: '5-6',
        uses_per_day: 2,
      },
    ])
  })

  it('blocks submit and shows an inline error when a special ability has no name', async () => {
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster')
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')

    await wrapper
      .findAll('button')
      .find((b) => b.text() === '+ Add special ability')
      ?.trigger('click')
    // Leave the special ability's name and description blank.

    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.text()).toContain('Name is required.')
    expect(wrapper.text()).toContain('Description is required.')
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('submits a changed saving throw during edit, proving it is genuinely editable', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockResolvedValue(EXISTING_DETAIL)
    const updated: BestiaryMonsterDetail = { ...EXISTING_DETAIL, name: 'Giant Rat' }
    const updateSpy = vi.spyOn(bestiaryApi, 'updateMonster').mockResolvedValue(updated)

    wrapper = mount(MonsterFormModal, { props: { monsterId: 1 } })
    await flushPromises()

    await wrapper.find('input[name="savingThrow-wisdom"]').setValue('5')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(updateSpy).toHaveBeenCalledTimes(1)
    const [, payload] = updateSpy.mock.calls[0]
    expect(payload.statblock?.saving_throws).toEqual([{ ability: 'wisdom', bonus: 5 }])
  })

  it('shows an error and does not emit saved when the save fails', async () => {
    vi.spyOn(bestiaryApi, 'createMonster').mockRejectedValue(new Error('server error'))

    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })
    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(wrapper.text()).toContain('Error:')
    expect(wrapper.emitted('saved')).toBeUndefined()
  })

  it('blocks submit and shows an error when the edit-mode detail fetch fails', async () => {
    vi.spyOn(bestiaryApi, 'fetchMonster').mockRejectedValue(new Error('network blip'))
    const updateSpy = vi.spyOn(bestiaryApi, 'updateMonster')

    wrapper = mount(MonsterFormModal, { props: { monsterId: 1 } })
    await flushPromises()

    await wrapper.find('input[name="name"]').setValue('Renamed Rat')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(updateSpy).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Could not load monster details. Please close and try again.')
    expect(wrapper.emitted('saved')).toBeUndefined()
  })

  it('blocks submit and shows the negative-number error when a numeric field is cleared', async () => {
    const createSpy = vi.spyOn(bestiaryApi, 'createMonster')
    wrapper = mount(MonsterFormModal, { props: { monsterId: null } })

    await wrapper.find('input[name="name"]').setValue('Test Monster')
    await wrapper.find('input[name="creatureType"]').setValue('beast')
    await wrapper.find('input[name="armorClass"]').setValue('')
    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.text()).toContain('Armor class cannot be negative.')
    expect(createSpy).not.toHaveBeenCalled()
  })
})
