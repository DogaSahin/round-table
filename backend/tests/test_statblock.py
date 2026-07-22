from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.shared.statblock import (
    AbilityScores,
    DamageComponent,
    SavingThrowEffect,
    SavingThrowProficiency,
    SkillProficiency,
    Speed,
)


def test_ability_scores_round_trip() -> None:
    scores = AbilityScores(
        strength=18, dexterity=14, constitution=16, intelligence=6, wisdom=12, charisma=8
    )
    assert scores.model_dump() == {
        "strength": 18,
        "dexterity": 14,
        "constitution": 16,
        "intelligence": 6,
        "wisdom": 12,
        "charisma": 8,
    }


@pytest.mark.parametrize("value", [0, 31, -1])
def test_ability_scores_rejects_out_of_range(value: int) -> None:
    with pytest.raises(ValidationError):
        AbilityScores(
            strength=value, dexterity=10, constitution=10, intelligence=10, wisdom=10, charisma=10
        )


def test_speed_defaults_to_no_movement_modes() -> None:
    speed = Speed(walk=30)
    assert speed.fly is None
    assert speed.hover is False


def test_speed_rejects_negative_value() -> None:
    with pytest.raises(ValidationError):
        Speed(walk=-5)


def test_saving_throw_proficiency_requires_valid_ability_name() -> None:
    with pytest.raises(ValidationError):
        SavingThrowProficiency(ability="invalid_ability", bonus=3)  # type: ignore[arg-type]

    prof = SavingThrowProficiency(ability="wisdom", bonus=3)
    assert prof.bonus == 3


def test_skill_proficiency_round_trip() -> None:
    skill = SkillProficiency(skill="perception", bonus=5)
    assert skill.model_dump() == {"skill": "perception", "bonus": 5}


def test_damage_component_round_trip() -> None:
    dmg = DamageComponent(dice="2d6+3", damage_type="slashing")
    assert dmg.model_dump() == {"dice": "2d6+3", "damage_type": "slashing"}


def test_saving_throw_effect_round_trip() -> None:
    effect = SavingThrowEffect(ability="dexterity", dc=15, effect_on_save="half")
    assert effect.model_dump() == {"ability": "dexterity", "dc": 15, "effect_on_save": "half"}
