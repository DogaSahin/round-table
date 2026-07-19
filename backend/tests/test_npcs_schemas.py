from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.npcs.schemas import NpcCreate, NpcUpdate


def test_npc_create_requires_nonempty_name() -> None:
    with pytest.raises(ValidationError):
        NpcCreate(name="")


def test_npc_create_defaults_disposition_and_player_visible() -> None:
    payload = NpcCreate(name="Old Man Grigg")
    assert payload.disposition == "neutral"
    assert payload.player_visible is False
    assert payload.faction_id is None


def test_npc_create_rejects_invalid_disposition() -> None:
    with pytest.raises(ValidationError):
        NpcCreate(name="Old Man Grigg", disposition="furious")  # type: ignore[arg-type]


def test_npc_update_all_fields_optional() -> None:
    payload = NpcUpdate()
    assert payload.name is None
    assert payload.disposition is None
    assert payload.faction_id is None
    assert payload.statblock is None
    assert payload.motivation is None
    assert payload.secrets is None
    assert payload.voice is None
    assert payload.player_visible is None


def test_npc_create_accepts_full_payload() -> None:
    payload = NpcCreate(
        name="Old Man Grigg",
        disposition="friendly",
        faction_id=7,
        statblock="AC 10, HP 4",
        motivation="Wants his cat back.",
        secrets="Actually a retired assassin.",
        voice="Raspy, trails off mid-sentence.",
        player_visible=True,
    )
    assert payload.faction_id == 7
    assert payload.player_visible is True
