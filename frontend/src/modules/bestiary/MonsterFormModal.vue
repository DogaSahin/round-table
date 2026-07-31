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
    type BestiaryMonsterDetail,
    type Statblock,
  } from './api'

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
  }

  function formFromStatblock(name: string, sb: Statblock): FormState {
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
    }
  }

  const baseStatblock = ref<Statblock>(defaultStatblock())
  const form = ref<FormState>(formFromStatblock('', baseStatblock.value))
  const errors = ref<Record<string, string>>({})
  const errorMessage = ref<string | null>(null)
  const saving = ref(false)

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
      return
    }
    try {
      const detail = await fetchMonster(monsterId)
      baseStatblock.value = detail.statblock
      form.value = formFromStatblock(detail.name, detail.statblock)
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

  function validateForm(f: FormState): Record<string, string> {
    const validationErrors: Record<string, string> = {}
    if (!f.name.trim()) validationErrors.name = 'Name is required.'
    if (!f.size.trim()) validationErrors.size = 'Size is required.'
    if (!f.creatureType.trim()) validationErrors.creatureType = 'Type is required.'
    if (!f.alignment.trim()) validationErrors.alignment = 'Alignment is required.'
    if (!f.hitDice.trim()) validationErrors.hitDice = 'Hit dice is required.'
    if (f.armorClass < 0) validationErrors.armorClass = 'Armor class cannot be negative.'
    if (f.hitPoints < 0) validationErrors.hitPoints = 'Hit points cannot be negative.'
    if (f.experiencePoints < 0) {
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
    }
  }

  async function submit() {
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
</style>
