from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

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
