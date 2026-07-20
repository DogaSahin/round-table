from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.combat.schemas import (
    CombatantCreate,
    CombatantOut,
    ConditionRequest,
    DamageRequest,
    EncounterCreate,
    HealRequest,
)


def test_encounter_create_requires_nonempty_name() -> None:
    with pytest.raises(ValidationError):
        EncounterCreate(name="")


def test_combatant_create_requires_nonempty_name() -> None:
    with pytest.raises(ValidationError):
        CombatantCreate(name="")


def test_combatant_create_defaults() -> None:
    payload = CombatantCreate(name="Goblin")
    assert payload.initiative == 0
    assert payload.hp_current == 0
    assert payload.hp_max == 0
    assert payload.ac is None
    assert payload.is_pc is False
    assert payload.visible_to_players is False
    assert payload.npc_id is None


def test_damage_request_rejects_negative_amount() -> None:
    with pytest.raises(ValidationError):
        DamageRequest(amount=-1)


def test_heal_request_rejects_negative_amount() -> None:
    with pytest.raises(ValidationError):
        HealRequest(amount=-1)


def test_condition_request_defaults_op_to_add() -> None:
    payload = ConditionRequest(name="prone")
    assert payload.op == "add"


def test_condition_request_rejects_invalid_op() -> None:
    with pytest.raises(ValidationError):
        ConditionRequest(name="prone", op="toggle")  # type: ignore[arg-type]


def test_combatant_out_round_trips_conditions_list() -> None:
    payload = CombatantOut(
        id=1,
        name="Goblin",
        initiative=12,
        hp_current=7,
        hp_max=10,
        ac=13,
        conditions=["prone", "poisoned"],
        concentration=False,
        sort_order=0,
        is_pc=False,
        visible_to_players=True,
        npc_id=None,
        token_id=None,
    )
    assert payload.conditions == ["prone", "poisoned"]
