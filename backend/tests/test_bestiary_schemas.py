from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.bestiary.schemas import BestiaryMonsterCreate, BestiaryMonsterUpdate


def _statblock_payload(creature_type: str = "beast", challenge_rating: float = 0.25) -> dict:
    return {
        "size": "Small",
        "creature_type": creature_type,
        "alignment": "unaligned",
        "armor_class": 12,
        "hit_points": 7,
        "hit_dice": "2d6",
        "speed": {"walk": 30},
        "ability_scores": {
            "strength": 8,
            "dexterity": 15,
            "constitution": 11,
            "intelligence": 2,
            "wisdom": 10,
            "charisma": 4,
        },
        "challenge_rating": challenge_rating,
        "experience_points": 50,
    }


def test_create_requires_nonempty_name() -> None:
    with pytest.raises(ValidationError):
        BestiaryMonsterCreate(name="", statblock=_statblock_payload())


def test_create_rejects_invalid_nested_statblock() -> None:
    with pytest.raises(ValidationError):
        BestiaryMonsterCreate(name="Giant Rat", statblock=_statblock_payload(challenge_rating=0.9))


def test_create_accepts_full_payload() -> None:
    payload = BestiaryMonsterCreate(
        name="Giant Rat", statblock=_statblock_payload(), image_url="/media/rat.png"
    )
    assert payload.name == "Giant Rat"
    assert payload.statblock.creature_type == "beast"
    assert payload.image_url == "/media/rat.png"


def test_update_all_fields_optional() -> None:
    payload = BestiaryMonsterUpdate()
    assert payload.name is None
    assert payload.statblock is None
    assert payload.image_url is None
