<script setup lang="ts">
  // frontend/src/modules/bestiary/MonsterFormModal.vue
  import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
  import { ApiError } from '@/api/client'
  import {
    ALLOWED_CHALLENGE_RATINGS,
    createMonster,
    fetchMonster,
    formatChallengeRating,
    updateMonster,
    type AbilityName,
    type BestiaryMonsterDetail,
    type Statblock,
  } from './api'
  import TagListField from './TagListField.vue'

  const SKILL_OPTIONS = [
    'Acrobatics',
    'Animal Handling',
    'Arcana',
    'Athletics',
    'Deception',
    'History',
    'Insight',
    'Intimidation',
    'Investigation',
    'Medicine',
    'Nature',
    'Perception',
    'Performance',
    'Persuasion',
    'Religion',
    'Sleight of Hand',
    'Stealth',
    'Survival',
  ]

  const DAMAGE_TYPE_OPTIONS = [
    'acid',
    'bludgeoning',
    'cold',
    'fire',
    'force',
    'lightning',
    'necrotic',
    'piercing',
    'poison',
    'psychic',
    'radiant',
    'slashing',
    'thunder',
  ].map((value) => ({ value, label: value }))

  const CONDITION_OPTIONS = [
    'blinded',
    'charmed',
    'deafened',
    'exhaustion',
    'frightened',
    'grappled',
    'incapacitated',
    'invisible',
    'paralyzed',
    'petrified',
    'poisoned',
    'prone',
    'restrained',
    'stunned',
    'unconscious',
  ].map((value) => ({ value, label: value }))

  const SAVING_THROW_ABILITIES: { key: AbilityName; label: string }[] = [
    { key: 'strength', label: 'STR' },
    { key: 'dexterity', label: 'DEX' },
    { key: 'constitution', label: 'CON' },
    { key: 'intelligence', label: 'INT' },
    { key: 'wisdom', label: 'WIS' },
    { key: 'charisma', label: 'CHA' },
  ]

  const SKILL_CUSTOM_OPTION = '__custom__'

  const props = defineProps<{
    monsterId: number | null
  }>()

  const emit = defineEmits<{
    (e: 'saved', monster: BestiaryMonsterDetail): void
    (e: 'close'): void
  }>()

  function defaultStatblock(): Statblock {
    return {
      size: 'Medium',
      creature_type: '',
      subtype: null,
      alignment: 'unaligned',
      armor_class: 10,
      armor_class_notes: null,
      hit_points: 1,
      hit_dice: '1d8',
      speed: { walk: null, fly: null, swim: null, climb: null, burrow: null, hover: false },
      ability_scores: {
        strength: 10,
        dexterity: 10,
        constitution: 10,
        intelligence: 10,
        wisdom: 10,
        charisma: 10,
      },
      saving_throws: [],
      skills: [],
      damage_vulnerabilities: [],
      damage_resistances: [],
      damage_immunities: [],
      condition_immunities: [],
      senses: [],
      languages: [],
      challenge_rating: 0,
      experience_points: 0,
      special_abilities: [],
      actions: [],
      legendary_actions: [],
      legendary_actions_per_turn: null,
    }
  }

  interface FormState {
    name: string
    size: string
    creatureType: string
    subtype: string
    alignment: string
    armorClass: number
    armorClassNotes: string
    hitPoints: number
    hitDice: string
    speedWalk: number | null
    speedFly: number | null
    speedSwim: number | null
    speedClimb: number | null
    speedBurrow: number | null
    speedHover: boolean
    strength: number
    dexterity: number
    constitution: number
    intelligence: number
    wisdom: number
    charisma: number
    challengeRating: number
    experiencePoints: number
    savingThrows: Record<AbilityName, number | null>
    skills: Array<{ skill: string; bonus: number | null }>
    damageVulnerabilities: string[]
    damageResistances: string[]
    damageImmunities: string[]
    conditionImmunities: string[]
    senses: string[]
    languages: string[]
  }

  function formFromStatblock(name: string, sb: Statblock): FormState {
    const savingThrows: Record<AbilityName, number | null> = {
      strength: null,
      dexterity: null,
      constitution: null,
      intelligence: null,
      wisdom: null,
      charisma: null,
    }
    for (const st of sb.saving_throws) {
      savingThrows[st.ability] = st.bonus
    }

    return {
      name,
      size: sb.size,
      creatureType: sb.creature_type,
      subtype: sb.subtype ?? '',
      alignment: sb.alignment,
      armorClass: sb.armor_class,
      armorClassNotes: sb.armor_class_notes ?? '',
      hitPoints: sb.hit_points,
      hitDice: sb.hit_dice,
      speedWalk: sb.speed.walk,
      speedFly: sb.speed.fly,
      speedSwim: sb.speed.swim,
      speedClimb: sb.speed.climb,
      speedBurrow: sb.speed.burrow,
      speedHover: sb.speed.hover,
      strength: sb.ability_scores.strength,
      dexterity: sb.ability_scores.dexterity,
      constitution: sb.ability_scores.constitution,
      intelligence: sb.ability_scores.intelligence,
      wisdom: sb.ability_scores.wisdom,
      charisma: sb.ability_scores.charisma,
      challengeRating: sb.challenge_rating,
      experiencePoints: sb.experience_points,
      savingThrows,
      skills: sb.skills.map((s) => ({ skill: s.skill, bonus: s.bonus })),
      damageVulnerabilities: [...sb.damage_vulnerabilities],
      damageResistances: [...sb.damage_resistances],
      damageImmunities: [...sb.damage_immunities],
      conditionImmunities: [...sb.condition_immunities],
      senses: [...sb.senses],
      languages: [...sb.languages],
    }
  }

  const baseStatblock = ref<Statblock>(defaultStatblock())
  const form = ref<FormState>(formFromStatblock('', baseStatblock.value))
  const errors = ref<Record<string, string>>({})
  const errorMessage = ref<string | null>(null)
  const saving = ref(false)
  const baseLoaded = ref(false)
  const customSkillRows = ref<boolean[]>([])

  const crOptions = computed(() =>
    ALLOWED_CHALLENGE_RATINGS.map((cr) => ({ value: cr, label: formatChallengeRating(cr) })),
  )

  function onKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') emit('close')
  }

  async function load(monsterId: number | null) {
    if (monsterId === null) {
      baseStatblock.value = defaultStatblock()
      form.value = formFromStatblock('', baseStatblock.value)
      customSkillRows.value = []
      baseLoaded.value = true
      return
    }
    try {
      const detail = await fetchMonster(monsterId)
      baseStatblock.value = detail.statblock
      form.value = formFromStatblock(detail.name, detail.statblock)
      customSkillRows.value = detail.statblock.skills.map((s) => !SKILL_OPTIONS.includes(s.skill))
      baseLoaded.value = true
    } catch (err) {
      errorMessage.value = err instanceof ApiError ? err.message : 'Unknown error'
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', onKeydown)
    void load(props.monsterId)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', onKeydown)
  })

  function addSkillRow() {
    form.value.skills.push({ skill: '', bonus: null })
    customSkillRows.value.push(false)
  }

  function removeSkillRow(index: number) {
    form.value.skills.splice(index, 1)
    customSkillRows.value.splice(index, 1)
  }

  function onSkillSelectChange(index: number, value: string) {
    if (value === SKILL_CUSTOM_OPTION) {
      customSkillRows.value[index] = true
      form.value.skills[index].skill = ''
    } else {
      customSkillRows.value[index] = false
      form.value.skills[index].skill = value
    }
  }

  function skillOptionsFor(index: number): string[] {
    const usedElsewhere = new Set(
      form.value.skills.filter((_, i) => i !== index).map((s) => s.skill),
    )
    return SKILL_OPTIONS.filter((opt) => !usedElsewhere.has(opt))
  }

  function validateForm(f: FormState): Record<string, string> {
    const validationErrors: Record<string, string> = {}
    if (!f.name.trim()) validationErrors.name = 'Name is required.'
    if (!f.size.trim()) validationErrors.size = 'Size is required.'
    if (!f.creatureType.trim()) validationErrors.creatureType = 'Type is required.'
    if (!f.alignment.trim()) validationErrors.alignment = 'Alignment is required.'
    if (!f.hitDice.trim()) validationErrors.hitDice = 'Hit dice is required.'
    if (!Number.isFinite(f.armorClass) || f.armorClass < 0) {
      validationErrors.armorClass = 'Armor class cannot be negative.'
    }
    if (!Number.isFinite(f.hitPoints) || f.hitPoints < 0) {
      validationErrors.hitPoints = 'Hit points cannot be negative.'
    }
    if (!Number.isFinite(f.experiencePoints) || f.experiencePoints < 0) {
      validationErrors.experiencePoints = 'Experience points cannot be negative.'
    }
    const abilityScores: Array<[string, number]> = [
      ['strength', f.strength],
      ['dexterity', f.dexterity],
      ['constitution', f.constitution],
      ['intelligence', f.intelligence],
      ['wisdom', f.wisdom],
      ['charisma', f.charisma],
    ]
    for (const [key, value] of abilityScores) {
      if (value < 1 || value > 30) validationErrors[key] = 'Must be between 1 and 30.'
    }
    return validationErrors
  }

  function buildStatblock(f: FormState): Statblock {
    return {
      ...baseStatblock.value,
      size: f.size,
      creature_type: f.creatureType,
      subtype: f.subtype.trim() || null,
      alignment: f.alignment,
      armor_class: f.armorClass,
      armor_class_notes: f.armorClassNotes.trim() || null,
      hit_points: f.hitPoints,
      hit_dice: f.hitDice,
      speed: {
        walk: f.speedWalk,
        fly: f.speedFly,
        swim: f.speedSwim,
        climb: f.speedClimb,
        burrow: f.speedBurrow,
        hover: f.speedHover,
      },
      ability_scores: {
        strength: f.strength,
        dexterity: f.dexterity,
        constitution: f.constitution,
        intelligence: f.intelligence,
        wisdom: f.wisdom,
        charisma: f.charisma,
      },
      challenge_rating: f.challengeRating,
      experience_points: f.experiencePoints,
      saving_throws: (Object.entries(f.savingThrows) as [AbilityName, number | null][])
        .filter(([, bonus]) => bonus !== null && Number.isFinite(bonus))
        .map(([ability, bonus]) => ({ ability, bonus: bonus as number })),
      skills: f.skills
        .filter((s) => s.skill.trim() && Number.isFinite(s.bonus))
        .map((s) => ({ skill: s.skill.trim(), bonus: s.bonus as number })),
      damage_vulnerabilities: f.damageVulnerabilities.map((v) => v.trim()).filter(Boolean),
      damage_resistances: f.damageResistances.map((v) => v.trim()).filter(Boolean),
      damage_immunities: f.damageImmunities.map((v) => v.trim()).filter(Boolean),
      condition_immunities: f.conditionImmunities.map((v) => v.trim()).filter(Boolean),
      senses: f.senses.map((v) => v.trim()).filter(Boolean),
      languages: f.languages.map((v) => v.trim()).filter(Boolean),
    }
  }

  async function submit() {
    if (saving.value) return

    if (props.monsterId !== null && !baseLoaded.value) {
      errorMessage.value = 'Could not load monster details. Please close and try again.'
      return
    }

    const validationErrors = validateForm(form.value)
    errors.value = validationErrors
    if (Object.keys(validationErrors).length > 0) return

    errorMessage.value = null
    saving.value = true
    try {
      const statblock = buildStatblock(form.value)
      const monster =
        props.monsterId === null
          ? await createMonster({ name: form.value.name, statblock })
          : await updateMonster(props.monsterId, { name: form.value.name, statblock })
      emit('saved', monster)
    } catch (err) {
      errorMessage.value = err instanceof ApiError ? err.message : 'Unknown error'
    } finally {
      saving.value = false
    }
  }
</script>

<template>
  <div class="monster-form-modal__backdrop" @click.self="emit('close')">
    <div class="monster-form-modal__body">
      <h2>{{ monsterId === null ? 'New Monster' : 'Edit Monster' }}</h2>
      <p v-if="errorMessage">Error: {{ errorMessage }}</p>

      <form class="monster-form-modal__form" @submit.prevent="submit">
        <label>
          Name
          <input v-model="form.name" type="text" name="name" />
          <span v-if="errors.name" class="field-error">{{ errors.name }}</span>
        </label>

        <label>
          Size
          <input v-model="form.size" type="text" name="size" />
          <span v-if="errors.size" class="field-error">{{ errors.size }}</span>
        </label>

        <label>
          Type
          <input v-model="form.creatureType" type="text" name="creatureType" />
          <span v-if="errors.creatureType" class="field-error">{{ errors.creatureType }}</span>
        </label>

        <label>
          Subtype
          <input v-model="form.subtype" type="text" name="subtype" />
        </label>

        <label>
          Alignment
          <input v-model="form.alignment" type="text" name="alignment" />
          <span v-if="errors.alignment" class="field-error">{{ errors.alignment }}</span>
        </label>

        <label>
          Armor Class
          <input v-model.number="form.armorClass" type="number" name="armorClass" />
          <span v-if="errors.armorClass" class="field-error">{{ errors.armorClass }}</span>
        </label>

        <label>
          Armor Class Notes
          <input v-model="form.armorClassNotes" type="text" name="armorClassNotes" />
        </label>

        <label>
          Hit Points
          <input v-model.number="form.hitPoints" type="number" name="hitPoints" />
          <span v-if="errors.hitPoints" class="field-error">{{ errors.hitPoints }}</span>
        </label>

        <label>
          Hit Dice
          <input v-model="form.hitDice" type="text" name="hitDice" />
          <span v-if="errors.hitDice" class="field-error">{{ errors.hitDice }}</span>
        </label>

        <fieldset>
          <legend>Speed</legend>
          <label>
            Walk
            <input v-model.number="form.speedWalk" type="number" name="speedWalk" />
          </label>
          <label>
            Fly
            <input v-model.number="form.speedFly" type="number" name="speedFly" />
          </label>
          <label>
            Swim
            <input v-model.number="form.speedSwim" type="number" name="speedSwim" />
          </label>
          <label>
            Climb
            <input v-model.number="form.speedClimb" type="number" name="speedClimb" />
          </label>
          <label>
            Burrow
            <input v-model.number="form.speedBurrow" type="number" name="speedBurrow" />
          </label>
          <label>
            <input v-model="form.speedHover" type="checkbox" name="speedHover" />
            Hover
          </label>
        </fieldset>

        <fieldset>
          <legend>Ability Scores</legend>
          <label>
            STR
            <input v-model.number="form.strength" type="number" name="strength" />
            <span v-if="errors.strength" class="field-error">{{ errors.strength }}</span>
          </label>
          <label>
            DEX
            <input v-model.number="form.dexterity" type="number" name="dexterity" />
            <span v-if="errors.dexterity" class="field-error">{{ errors.dexterity }}</span>
          </label>
          <label>
            CON
            <input v-model.number="form.constitution" type="number" name="constitution" />
            <span v-if="errors.constitution" class="field-error">{{ errors.constitution }}</span>
          </label>
          <label>
            INT
            <input v-model.number="form.intelligence" type="number" name="intelligence" />
            <span v-if="errors.intelligence" class="field-error">{{ errors.intelligence }}</span>
          </label>
          <label>
            WIS
            <input v-model.number="form.wisdom" type="number" name="wisdom" />
            <span v-if="errors.wisdom" class="field-error">{{ errors.wisdom }}</span>
          </label>
          <label>
            CHA
            <input v-model.number="form.charisma" type="number" name="charisma" />
            <span v-if="errors.charisma" class="field-error">{{ errors.charisma }}</span>
          </label>
        </fieldset>

        <fieldset>
          <legend>Saving Throws</legend>
          <label v-for="ability in SAVING_THROW_ABILITIES" :key="ability.key">
            {{ ability.label }}
            <input
              v-model.number="form.savingThrows[ability.key]"
              type="number"
              :name="`savingThrow-${ability.key}`"
            />
          </label>
        </fieldset>

        <fieldset>
          <legend>Skills</legend>
          <div v-for="(row, index) in form.skills" :key="index" class="skill-row">
            <select
              v-if="!customSkillRows[index]"
              :name="`skill-${index}`"
              :value="row.skill"
              @change="onSkillSelectChange(index, ($event.target as HTMLSelectElement).value)"
            >
              <option value="" disabled>Select skill…</option>
              <option v-for="opt in skillOptionsFor(index)" :key="opt" :value="opt">
                {{ opt }}
              </option>
              <option :value="SKILL_CUSTOM_OPTION">Other (custom)...</option>
            </select>
            <input v-else v-model="row.skill" type="text" :name="`skill-${index}`" />
            <input v-model.number="row.bonus" type="number" :name="`skillBonus-${index}`" />
            <button type="button" @click="removeSkillRow(index)">×</button>
          </div>
          <button type="button" @click="addSkillRow">+ Add skill</button>
        </fieldset>

        <TagListField
          v-model="form.damageVulnerabilities"
          label="Damage Vulnerabilities"
          field-name="damageVulnerabilities"
          :options="DAMAGE_TYPE_OPTIONS"
        />
        <TagListField
          v-model="form.damageResistances"
          label="Damage Resistances"
          field-name="damageResistances"
          :options="DAMAGE_TYPE_OPTIONS"
        />
        <TagListField
          v-model="form.damageImmunities"
          label="Damage Immunities"
          field-name="damageImmunities"
          :options="DAMAGE_TYPE_OPTIONS"
        />
        <TagListField
          v-model="form.conditionImmunities"
          label="Condition Immunities"
          field-name="conditionImmunities"
          :options="CONDITION_OPTIONS"
        />
        <TagListField v-model="form.senses" label="Senses" field-name="senses" />
        <TagListField v-model="form.languages" label="Languages" field-name="languages" />

        <label>
          Challenge Rating
          <select v-model="form.challengeRating" name="challengeRating">
            <option v-for="opt in crOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </label>

        <label>
          Experience Points
          <input v-model.number="form.experiencePoints" type="number" name="experiencePoints" />
          <span v-if="errors.experiencePoints" class="field-error">
            {{ errors.experiencePoints }}
          </span>
        </label>

        <button type="submit" :disabled="saving">Save</button>
        <button type="button" @click="emit('close')">Cancel</button>
      </form>
    </div>
  </div>
</template>

<style scoped>
  .monster-form-modal__backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .monster-form-modal__body {
    background: white;
    border-radius: 4px;
    padding: 1.5rem;
    max-width: 32rem;
    max-height: 80vh;
    overflow-y: auto;
  }

  .field-error {
    color: #c00;
    display: block;
    font-size: 0.85rem;
  }

  .skill-row {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
  }
</style>
