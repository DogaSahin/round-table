from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.maps.schemas import (
    FogOpRequest,
    MapCreate,
    MapUpdate,
    MoveTokenRequest,
    PlayerTokenOut,
    TokenCreate,
    TokenUpdate,
)


def test_map_create_requires_nonempty_name() -> None:
    with pytest.raises(ValidationError):
        MapCreate(name="")


def test_map_update_partial_fields_default_to_none() -> None:
    payload = MapUpdate()
    assert payload.name is None
    assert payload.grid_size_px is None
    assert payload.grid_offset_x is None
    assert payload.grid_offset_y is None
    assert payload.grid_visible is None
    assert payload.feet_per_square is None
    assert payload.diagonal_rule is None


def test_token_create_has_no_position_fields() -> None:
    assert "x" not in TokenCreate.model_fields
    assert "y" not in TokenCreate.model_fields


def test_token_create_defaults() -> None:
    payload = TokenCreate()
    assert payload.size_squares == 1
    assert payload.color == "#888888"
    assert payload.layer == "tokens"
    assert payload.visible_to_players is True


def test_token_update_accepts_status_markers_list() -> None:
    payload = TokenUpdate(status_markers=["prone", "poisoned"])
    assert payload.status_markers == ["prone", "poisoned"]

    payload_none = TokenUpdate()
    assert payload_none.status_markers is None


def test_move_token_request_requires_x_and_y() -> None:
    with pytest.raises(ValidationError):
        MoveTokenRequest(x=1)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        MoveTokenRequest(y=1)  # type: ignore[call-arg]


def test_move_token_request_snap_defaults_to_false() -> None:
    payload = MoveTokenRequest(x=1, y=2)
    assert payload.snap is False


def test_fog_op_request_rejects_invalid_op() -> None:
    with pytest.raises(ValidationError):
        FogOpRequest(op="delete", geom={})  # type: ignore[arg-type]


def test_fog_op_request_accepts_reveal_and_hide() -> None:
    reveal = FogOpRequest(op="reveal", geom={"type": "rect"})
    hide = FogOpRequest(op="hide", geom={"type": "rect"})
    assert reveal.op == "reveal"
    assert hide.op == "hide"


def test_player_token_out_has_no_hp_current_or_hp_max_fields() -> None:
    assert "hp_current" not in PlayerTokenOut.model_fields
    assert "hp_max" not in PlayerTokenOut.model_fields
    assert "hp_band" in PlayerTokenOut.model_fields
