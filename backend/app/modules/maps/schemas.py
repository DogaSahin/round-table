# backend/app/modules/maps/schemas.py
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

DiagonalRule = Literal["chebyshev", "five_ten_five", "euclidean", "manhattan"]
TokenLayer = Literal["tokens", "dm"]
TokenKind = Literal["disc", "image"]
FogOp = Literal["reveal", "hide"]
HpBand = Literal["low", "mid", "high"]


class MapCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class MapUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    grid_size_px: int | None = None
    grid_offset_x: int | None = None
    grid_offset_y: int | None = None
    grid_visible: bool | None = None
    feet_per_square: int | None = None
    diagonal_rule: DiagonalRule | None = None


class TokenCreate(BaseModel):
    name: str = ""
    layer: TokenLayer = "tokens"
    kind: TokenKind = "disc"
    size_squares: int = 1
    color: str = "#888888"
    is_pc: bool = False
    visible_to_players: bool = True
    npc_id: int | None = None
    combatant_id: int | None = None


class TokenUpdate(BaseModel):
    name: str | None = None
    layer: TokenLayer | None = None
    size_squares: int | None = None
    color: str | None = None
    is_pc: bool | None = None
    visible_to_players: bool | None = None
    npc_id: int | None = None
    combatant_id: int | None = None
    hp_current: int | None = None
    hp_max: int | None = None
    hp_visible_to_players: bool | None = None
    status_markers: list[str] | None = None


class MoveTokenRequest(BaseModel):
    x: int
    y: int
    snap: bool = False


class FogOpRequest(BaseModel):
    op: FogOp
    geom: dict[str, Any]


class TokenOut(BaseModel):
    id: int
    layer: TokenLayer
    kind: TokenKind
    x: int
    y: int
    size_squares: int
    color: str
    image_path: str | None
    name: str
    hp_current: int | None
    hp_max: int | None
    hp_visible_to_players: bool
    visible_to_players: bool
    status_markers: list[str]
    is_pc: bool
    npc_id: int | None
    combatant_id: int | None


class FogRegionOut(BaseModel):
    id: int
    order_index: int
    kind: FogOp
    geom: dict[str, Any]


class MapListItemOut(BaseModel):
    id: int
    name: str
    is_active: bool


class MapDetailOut(BaseModel):
    id: int
    name: str
    image_path: str | None
    image_w: int | None
    image_h: int | None
    grid_size_px: int
    grid_offset_x: int
    grid_offset_y: int
    grid_visible: bool
    feet_per_square: int
    diagonal_rule: DiagonalRule
    is_active: bool
    tokens: list[TokenOut]
    fog: list[FogRegionOut]


class PlayerTokenOut(BaseModel):
    id: int
    x: int
    y: int
    size_squares: int
    color: str
    kind: TokenKind
    image_path: str | None
    name: str
    hp_band: HpBand | None


class PlayerMapOut(BaseModel):
    id: int
    name: str
    image_path: str | None
    image_w: int | None
    image_h: int | None
    grid_size_px: int
    grid_offset_x: int
    grid_offset_y: int
    grid_visible: bool
    feet_per_square: int
    diagonal_rule: DiagonalRule
    tokens: list[PlayerTokenOut]
    fog: list[FogRegionOut]
