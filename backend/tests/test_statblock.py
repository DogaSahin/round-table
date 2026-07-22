from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.shared.statblock import (
    AbilityScores,
    Action,
    DamageComponent,
    LegendaryAction,
    SavingThrowEffect,
    SavingThrowProficiency,
    SkillProficiency,
    SpecialAbility,
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


def test_action_minimal_requires_only_id_name_description() -> None:
    action = Action(id="bite", name="Bite", description="Melee Weapon Attack.")
    assert action.damage == []
    assert action.save is None
    assert action.multiattack_refs == []


def test_action_with_damage_and_attack_bonus() -> None:
    action = Action(
        id="claw",
        name="Claw",
        description="Melee Weapon Attack: +7 to hit, reach 5 ft., one target.",
        attack_bonus=7,
        reach_or_range="5 ft.",
        target="one target",
        damage=[DamageComponent(dice="2d6+4", damage_type="slashing")],
    )
    assert action.damage[0].damage_type == "slashing"


def test_action_with_save_effect() -> None:
    action = Action(
        id="breath",
        name="Fire Breath",
        description="The dragon exhales fire in a 60-foot cone.",
        save=SavingThrowEffect(ability="dexterity", dc=17, effect_on_save="half"),
        damage=[DamageComponent(dice="16d6", damage_type="fire")],
        recharge="5-6",
    )
    assert action.save is not None
    assert action.save.dc == 17
    assert action.recharge == "5-6"


def test_action_multiattack_refs() -> None:
    action = Action(
        id="multiattack",
        name="Multiattack",
        description="The creature makes two claw attacks and one bite attack.",
        multiattack_refs=["claw", "bite"],
    )
    assert action.multiattack_refs == ["claw", "bite"]


def test_legendary_action_defaults_to_cost_one() -> None:
    legendary = LegendaryAction(
        id="tail-attack", name="Tail Attack", description="One tail attack."
    )
    assert legendary.cost == 1


def test_legendary_action_custom_cost() -> None:
    legendary = LegendaryAction(
        id="wing-attack", name="Wing Attack", description="Beats wings.", cost=2
    )
    assert legendary.cost == 2


def test_special_ability_round_trip() -> None:
    ability = SpecialAbility(
        id="legendary-resistance",
        name="Legendary Resistance",
        description="If the creature fails a saving throw, it can choose to succeed instead.",
        uses_per_day=3,
    )
    assert ability.uses_per_day == 3
