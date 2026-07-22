from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

AbilityName = Literal["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]


class AbilityScores(BaseModel):
    strength: int = Field(ge=1, le=30)
    dexterity: int = Field(ge=1, le=30)
    constitution: int = Field(ge=1, le=30)
    intelligence: int = Field(ge=1, le=30)
    wisdom: int = Field(ge=1, le=30)
    charisma: int = Field(ge=1, le=30)


class Speed(BaseModel):
    walk: int | None = Field(default=None, ge=0)
    fly: int | None = Field(default=None, ge=0)
    swim: int | None = Field(default=None, ge=0)
    climb: int | None = Field(default=None, ge=0)
    burrow: int | None = Field(default=None, ge=0)
    hover: bool = False


class SavingThrowProficiency(BaseModel):
    ability: AbilityName
    bonus: int


class SkillProficiency(BaseModel):
    skill: str = Field(min_length=1)
    bonus: int


class DamageComponent(BaseModel):
    dice: str = Field(min_length=1)
    damage_type: str = Field(min_length=1)


class SavingThrowEffect(BaseModel):
    ability: AbilityName
    dc: int = Field(ge=0)
    effect_on_save: str = Field(min_length=1)


class Action(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str
    attack_bonus: int | None = None
    reach_or_range: str | None = None
    target: str | None = None
    damage: list[DamageComponent] = Field(default_factory=list)
    save: SavingThrowEffect | None = None
    recharge: str | None = None
    uses_per_day: int | None = Field(default=None, ge=1)
    multiattack_refs: list[str] = Field(default_factory=list)


class LegendaryAction(Action):
    cost: int = Field(default=1, ge=1)


class SpecialAbility(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str
    recharge: str | None = None
    uses_per_day: int | None = Field(default=None, ge=1)


ALLOWED_CHALLENGE_RATINGS: frozenset[float] = frozenset(
    {0.0, 0.125, 0.25, 0.5} | {float(n) for n in range(1, 31)}
)

_CHALLENGE_RATING_FRACTIONS: dict[float, str] = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}


def format_challenge_rating(challenge_rating: float) -> str:
    """Renders a numeric CR (0, 0.125, 0.25, 0.5, or a whole number) as the
    traditional 5e display string ("1/8", "1/4", "1/2", or the integer)."""
    if challenge_rating in _CHALLENGE_RATING_FRACTIONS:
        return _CHALLENGE_RATING_FRACTIONS[challenge_rating]
    return str(int(challenge_rating))


class Statblock(BaseModel):
    size: str = Field(min_length=1)
    creature_type: str = Field(min_length=1)
    subtype: str | None = None
    alignment: str = Field(min_length=1)
    armor_class: int = Field(ge=0)
    armor_class_notes: str | None = None
    hit_points: int = Field(ge=0)
    hit_dice: str = Field(min_length=1)
    speed: Speed
    ability_scores: AbilityScores
    saving_throws: list[SavingThrowProficiency] = Field(default_factory=list)
    skills: list[SkillProficiency] = Field(default_factory=list)
    damage_vulnerabilities: list[str] = Field(default_factory=list)
    damage_resistances: list[str] = Field(default_factory=list)
    damage_immunities: list[str] = Field(default_factory=list)
    condition_immunities: list[str] = Field(default_factory=list)
    senses: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    challenge_rating: float
    experience_points: int = Field(ge=0)
    special_abilities: list[SpecialAbility] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)
    legendary_actions: list[LegendaryAction] = Field(default_factory=list)
    legendary_actions_per_turn: int | None = Field(default=None, ge=1)

    @field_validator("challenge_rating")
    @classmethod
    def _validate_challenge_rating(cls, value: float) -> float:
        if value not in ALLOWED_CHALLENGE_RATINGS:
            allowed = sorted(ALLOWED_CHALLENGE_RATINGS)
            raise ValueError(f"challenge_rating must be one of {allowed}, got {value}")
        return value
