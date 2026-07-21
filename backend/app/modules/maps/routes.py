# backend/app/modules/maps/routes.py
from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.models import Campaign
from app.core.realtime import broadcast
from app.core.realtime.manager import manager
from app.engine.encounter import hp_band
from app.engine.maps import token_is_player_visible
from app.modules.maps import service
from app.modules.maps.models import Map, Token
from app.modules.maps.schemas import (
    FogOp,
    FogOpRequest,
    FogRegionOut,
    HpBand,
    MapCreate,
    MapDetailOut,
    MapListItemOut,
    MapUpdate,
    MoveTokenRequest,
    PlayerMapOut,
    PlayerTokenOut,
    TokenCreate,
    TokenOut,
    TokenUpdate,
)
from app.shared.errors import NotFound

router = APIRouter(prefix="/api/maps", tags=["maps"])


def _token_out(token: Token) -> TokenOut:
    return TokenOut(
        id=token.id,
        layer=token.layer,  # type: ignore[arg-type]
        kind=token.kind,  # type: ignore[arg-type]
        x=token.x,
        y=token.y,
        size_squares=token.size_squares,
        color=token.color,
        image_path=token.image_path,
        name=token.name,
        hp_current=token.hp_current,
        hp_max=token.hp_max,
        hp_visible_to_players=token.hp_visible_to_players,
        visible_to_players=token.visible_to_players,
        status_markers=service.get_status_markers(token),
        is_pc=token.is_pc,
        npc_id=token.npc_id,
        combatant_id=token.combatant_id,
    )


def _fog_out_list(db: Session, map_id: int) -> list[FogRegionOut]:
    # service.fog_ops() returns the post-reduction view (see reduce_fog_ops): a
    # collapsed reveal/hide list that no longer maps 1:1 onto FogRegion rows (a
    # single reveal-all can absorb any number of prior rows), so there is no
    # real row id/order_index left to surface. We synthesize both from the
    # resulting list position, which is stable for a given fog state and is
    # only ever used by the frontend as a list key, never as a foreign key
    # back into the DB.
    ops = service.fog_ops(db, map_id)
    return [
        FogRegionOut(
            id=index,
            order_index=index,
            kind=cast(FogOp, op["op"]),
            geom=cast(dict[str, Any], op["geom"]),
        )
        for index, op in enumerate(ops)
    ]


def _map_out(db: Session, map_row: Map) -> MapDetailOut:
    return MapDetailOut(
        id=map_row.id,
        name=map_row.name,
        image_path=map_row.image_path,
        image_w=map_row.image_w,
        image_h=map_row.image_h,
        grid_size_px=map_row.grid_size_px,
        grid_offset_x=map_row.grid_offset_x,
        grid_offset_y=map_row.grid_offset_y,
        grid_visible=map_row.grid_visible,
        feet_per_square=map_row.feet_per_square,
        diagonal_rule=map_row.diagonal_rule,  # type: ignore[arg-type]
        is_active=map_row.is_active,
        tokens=[_token_out(t) for t in map_row.tokens],
        fog=_fog_out_list(db, map_row.id),
    )


def _list_item_out(map_row: Map) -> MapListItemOut:
    return MapListItemOut(id=map_row.id, name=map_row.name, is_active=map_row.is_active)


def _player_token_out(token: Token) -> PlayerTokenOut:
    # hp_band is withheld entirely (not just the raw numbers) when
    # hp_visible_to_players is False -- unlike combat's player projection,
    # which always shows a coarse band. We also guard against hp_current/
    # hp_max being unset (None), since hp_band() divides by hp_max and would
    # raise on a token whose HP was never configured.
    band: HpBand | None = None
    if token.hp_visible_to_players and token.hp_current is not None and token.hp_max is not None:
        band = cast(HpBand, hp_band(token.hp_current, token.hp_max))
    return PlayerTokenOut(
        id=token.id,
        x=token.x,
        y=token.y,
        size_squares=token.size_squares,
        color=token.color,
        kind=token.kind,  # type: ignore[arg-type]
        image_path=token.image_path,
        name=token.name,
        hp_band=band,
    )


def _player_map_out(db: Session, map_row: Map) -> PlayerMapOut:
    return PlayerMapOut(
        id=map_row.id,
        name=map_row.name,
        image_path=map_row.image_path,
        image_w=map_row.image_w,
        image_h=map_row.image_h,
        grid_size_px=map_row.grid_size_px,
        grid_offset_x=map_row.grid_offset_x,
        grid_offset_y=map_row.grid_offset_y,
        grid_visible=map_row.grid_visible,
        feet_per_square=map_row.feet_per_square,
        diagonal_rule=map_row.diagonal_rule,  # type: ignore[arg-type]
        tokens=[_player_token_out(t) for t in service.player_visible_tokens(map_row)],
        fog=_fog_out_list(db, map_row.id),
    )


def _get_owned_map(db: Session, map_id: int, campaign: Campaign) -> Map:
    row = service.owned_map(db, map_id, campaign.id)
    if row is None:
        raise NotFound(f"map {map_id} not found")
    return row


def _get_owned_token(db: Session, token_id: int, campaign: Campaign) -> Token:
    row = service.owned_token(db, token_id, campaign.id)
    if row is None:
        raise NotFound(f"token {token_id} not found")
    return row


async def _notify(map_id: int) -> None:
    await manager.publish(f"map:{map_id}", {"action": "map_changed", "map_id": map_id})


async def _notify_token_move(token: Token) -> None:
    player_safe = token_is_player_visible(token.visible_to_players, token.layer)
    topic = f"map:{token.map_id}" if player_safe else f"map:{token.map_id}:dm"
    await manager.publish(
        topic,
        {
            "action": "token.move",
            "map_id": token.map_id,
            "token_id": token.id,
            "x": token.x,
            "y": token.y,
        },
    )


@router.post("", response_model=MapDetailOut)
def create_map(
    payload: MapCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> MapDetailOut:
    row = service.create_map(db, campaign.id, payload.name)
    return _map_out(db, row)


@router.get("", response_model=list[MapListItemOut])
def list_maps(
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> list[MapListItemOut]:
    rows = service.roster(db, campaign.id)
    return [_list_item_out(r) for r in rows]


@router.get("/{map_id}", response_model=MapDetailOut)
def detail(
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> MapDetailOut:
    return _map_out(db, _get_owned_map(db, map_id, campaign))


@router.patch("/{map_id}", response_model=MapDetailOut)
async def update_map(
    map_id: int,
    payload: MapUpdate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> MapDetailOut:
    row = _get_owned_map(db, map_id, campaign)
    row = service.update_map(
        db,
        row,
        payload.name,
        payload.grid_size_px,
        payload.grid_offset_x,
        payload.grid_offset_y,
        payload.grid_visible,
        payload.feet_per_square,
        payload.diagonal_rule,
    )
    await _notify(map_id)
    return _map_out(db, row)


@router.delete("/{map_id}", status_code=204, response_model=None)
async def delete_map(
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    row = _get_owned_map(db, map_id, campaign)
    service.delete_map(db, row)
    await _notify(map_id)


@router.post("/{map_id}/activate", response_model=MapDetailOut)
async def activate(
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> MapDetailOut:
    row = _get_owned_map(db, map_id, campaign)
    row = service.set_active_map(db, campaign.id, row)
    broadcast.set_active_map(db, campaign.id, row.id)
    await broadcast.publish_changed(campaign.id)
    await _notify(map_id)
    return _map_out(db, row)


@router.post("/stop-sharing", status_code=204, response_model=None)
async def stop_sharing(
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    service.stop_sharing(db, campaign.id)
    broadcast.set_active_map(db, campaign.id, None)
    await broadcast.publish_changed(campaign.id)


@router.get("/{map_id}/player", response_model=PlayerMapOut)
def player_view(
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> PlayerMapOut:
    row = _get_owned_map(db, map_id, campaign)
    return _player_map_out(db, row)


@router.post("/{map_id}/image", response_model=MapDetailOut)
async def upload_map_image(
    map_id: int,
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
    settings: Settings = Depends(get_settings),
) -> MapDetailOut:
    row = _get_owned_map(db, map_id, campaign)
    data = await upload.read()
    row = service.set_map_image(db, row, data, upload.filename or "", settings.media_dir)
    await _notify(map_id)
    return _map_out(db, row)


@router.post("/{map_id}/tokens", response_model=TokenOut)
async def add_token(
    map_id: int,
    payload: TokenCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> TokenOut:
    map_row = _get_owned_map(db, map_id, campaign)
    token = service.create_token(
        db,
        map_row,
        payload.name,
        payload.layer,
        payload.kind,
        payload.size_squares,
        payload.color,
        payload.is_pc,
        payload.visible_to_players,
        payload.npc_id,
        payload.combatant_id,
    )
    await _notify(map_id)
    return _token_out(token)


@router.patch("/tokens/{token_id}", response_model=TokenOut)
async def update_token(
    token_id: int,
    payload: TokenUpdate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> TokenOut:
    token = _get_owned_token(db, token_id, campaign)
    map_id = token.map_id
    token = service.update_token(
        db,
        token,
        payload.name,
        payload.layer,
        payload.size_squares,
        payload.color,
        payload.is_pc,
        payload.visible_to_players,
        payload.npc_id,
        payload.combatant_id,
        payload.hp_current,
        payload.hp_max,
        payload.hp_visible_to_players,
        payload.status_markers,
    )
    await _notify(map_id)
    return _token_out(token)


@router.delete("/tokens/{token_id}", status_code=204, response_model=None)
async def delete_token(
    token_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    token = _get_owned_token(db, token_id, campaign)
    map_id = token.map_id
    service.delete_token(db, token)
    await _notify(map_id)


@router.post("/tokens/{token_id}/image", response_model=TokenOut)
async def upload_token_image(
    token_id: int,
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
    settings: Settings = Depends(get_settings),
) -> TokenOut:
    token = _get_owned_token(db, token_id, campaign)
    map_id = token.map_id
    data = await upload.read()
    token = service.set_token_image(db, token, data, upload.filename or "", settings.media_dir)
    await _notify(map_id)
    return _token_out(token)


@router.post("/tokens/{token_id}/move", response_model=TokenOut)
async def move_token(
    token_id: int,
    payload: MoveTokenRequest,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> TokenOut:
    token = _get_owned_token(db, token_id, campaign)
    token = service.move_token(db, token, payload.x, payload.y, payload.snap)
    await _notify_token_move(token)
    return _token_out(token)


@router.post("/{map_id}/fog", response_model=MapDetailOut)
async def add_fog(
    map_id: int,
    payload: FogOpRequest,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> MapDetailOut:
    map_row = _get_owned_map(db, map_id, campaign)
    service.add_fog_op(db, map_row, payload.op, payload.geom)
    await _notify(map_id)
    return _map_out(db, map_row)


@router.post("/{map_id}/fog/reveal-all", response_model=MapDetailOut)
async def fog_reveal_all(
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> MapDetailOut:
    map_row = _get_owned_map(db, map_id, campaign)
    service.fog_reveal_all(db, map_row)
    await _notify(map_id)
    return _map_out(db, map_row)


@router.post("/{map_id}/fog/hide-all", response_model=MapDetailOut)
async def fog_hide_all(
    map_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> MapDetailOut:
    map_row = _get_owned_map(db, map_id, campaign)
    service.fog_hide_all(db, map_row)
    await _notify(map_id)
    return _map_out(db, map_row)
