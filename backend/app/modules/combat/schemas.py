# backend/app/modules/combat/schemas.py
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

HpBand = Literal["low", "mid", "high"]


class EncounterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class EncounterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)


class CombatantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    initiative: int = 0
    hp_current: int = 0
    hp_max: int = 0
    ac: int | None = None
    is_pc: bool = False
    visible_to_players: bool = False
    npc_id: int | None = None


class CombatantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    initiative: int | None = None
    is_pc: bool | None = None
    visible_to_players: bool | None = None
    npc_id: int | None = None


class DamageRequest(BaseModel):
    amount: int = Field(ge=0)


class HealRequest(BaseModel):
    amount: int = Field(ge=0)


class SetAcRequest(BaseModel):
    ac: int | None = None


class ConditionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    op: Literal["add", "remove"] = "add"


class ReorderRequest(BaseModel):
    order: list[int]


class CombatantOut(BaseModel):
    id: int
    name: str
    initiative: int
    hp_current: int
    hp_max: int
    ac: int | None
    conditions: list[str]
    concentration: bool
    sort_order: int
    is_pc: bool
    visible_to_players: bool
    npc_id: int | None
    token_id: int | None


class EncounterListItemOut(BaseModel):
    id: int
    name: str
    round: int
    is_active: bool


class EncounterDetailOut(BaseModel):
    id: int
    name: str
    round: int
    active_combatant_id: int | None
    is_active: bool
    combatants: list[CombatantOut]


class PlayerCombatantOut(BaseModel):
    id: int
    name: str
    is_pc: bool
    is_active: bool
    band: HpBand
    hp_current: int | None
    hp_max: int | None


class PlayerEncounterOut(BaseModel):
    id: int
    name: str
    round: int
    is_active: bool
    combatants: list[PlayerCombatantOut]
