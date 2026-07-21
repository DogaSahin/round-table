# backend/app/modules/maps/service.py
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.engine.maps import reduce_fog_ops, snap_to_grid, token_is_player_visible
from app.modules.maps.models import FogRegion, Map, Token
from app.modules.maps.uploads import store_map_image, store_token_image


def roster(db: Session, campaign_id: int) -> list[Map]:
    return db.query(Map).filter_by(campaign_id=campaign_id).order_by(Map.name).all()


def owned_map(db: Session, map_id: int, campaign_id: int) -> Map | None:
    row = db.get(Map, map_id)
    return row if row is not None and row.campaign_id == campaign_id else None


def owned_token(db: Session, token_id: int, campaign_id: int) -> Token | None:
    row = db.get(Token, token_id)
    if row is None or row.map.campaign_id != campaign_id:
        return None
    return row


def create_map(db: Session, campaign_id: int, name: str) -> Map:
    row = Map(campaign_id=campaign_id, name=name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_map(
    db: Session,
    map_row: Map,
    name: str | None,
    grid_size_px: int | None,
    grid_offset_x: int | None,
    grid_offset_y: int | None,
    grid_visible: bool | None,
    feet_per_square: int | None,
    diagonal_rule: str | None,
) -> Map:
    if name is not None:
        map_row.name = name
    if grid_size_px is not None:
        map_row.grid_size_px = grid_size_px
    if grid_offset_x is not None:
        map_row.grid_offset_x = grid_offset_x
    if grid_offset_y is not None:
        map_row.grid_offset_y = grid_offset_y
    if grid_visible is not None:
        map_row.grid_visible = grid_visible
    if feet_per_square is not None:
        map_row.feet_per_square = feet_per_square
    if diagonal_rule is not None:
        map_row.diagonal_rule = diagonal_rule
    db.commit()
    db.refresh(map_row)
    return map_row


def delete_map(db: Session, map_row: Map) -> None:
    db.delete(map_row)
    db.commit()


def set_active_map(db: Session, campaign_id: int, map_row: Map) -> Map:
    db.query(Map).filter_by(campaign_id=campaign_id).update({"is_active": False})
    map_row.is_active = True
    db.commit()
    db.refresh(map_row)
    return map_row


def stop_sharing(db: Session, campaign_id: int) -> None:
    db.query(Map).filter_by(campaign_id=campaign_id).update({"is_active": False})
    db.commit()


def set_map_image(db: Session, map_row: Map, data: bytes, filename: str, media_dir: Path) -> Map:
    path, width, height = store_map_image(data, filename, media_dir)
    map_row.image_path = path
    map_row.image_w = width
    map_row.image_h = height
    db.commit()
    db.refresh(map_row)
    return map_row


def create_token(
    db: Session,
    map_row: Map,
    name: str,
    layer: str,
    kind: str,
    size_squares: int,
    color: str,
    is_pc: bool,
    visible_to_players: bool,
    npc_id: int | None,
    combatant_id: int | None,
) -> Token:
    origin = map_row.grid_size_px or 70
    row = Token(
        map_id=map_row.id,
        name=name,
        layer=layer,
        kind=kind,
        x=origin,
        y=origin,
        size_squares=size_squares,
        color=color,
        is_pc=is_pc,
        visible_to_players=visible_to_players,
        npc_id=npc_id,
        combatant_id=combatant_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_token(
    db: Session,
    token: Token,
    name: str | None,
    layer: str | None,
    size_squares: int | None,
    color: str | None,
    is_pc: bool | None,
    visible_to_players: bool | None,
    npc_id: int | None,
    combatant_id: int | None,
    hp_current: int | None,
    hp_max: int | None,
    hp_visible_to_players: bool | None,
    status_markers: list[str] | None,
) -> Token:
    updates = {
        "name": name,
        "layer": layer,
        "size_squares": size_squares,
        "color": color,
        "is_pc": is_pc,
        "visible_to_players": visible_to_players,
        "npc_id": npc_id,
        "combatant_id": combatant_id,
        "hp_current": hp_current,
        "hp_max": hp_max,
        "hp_visible_to_players": hp_visible_to_players,
    }
    for field, value in updates.items():
        if value is not None:
            setattr(token, field, value)
    if status_markers is not None:
        set_status_markers(token, status_markers)
    db.commit()
    db.refresh(token)
    return token


def delete_token(db: Session, token: Token) -> None:
    db.delete(token)
    db.commit()


def set_token_image(
    db: Session, token: Token, data: bytes, filename: str, media_dir: Path
) -> Token:
    path, _width, _height = store_token_image(data, filename, media_dir)
    token.image_path = path
    db.commit()
    db.refresh(token)
    return token


def move_token(db: Session, token: Token, x: int, y: int, snap: bool) -> Token:
    if snap:
        map_row = token.map
        x, y = snap_to_grid(
            x, y, map_row.grid_size_px, map_row.grid_offset_x, map_row.grid_offset_y
        )
    token.x = x
    token.y = y
    db.commit()
    db.refresh(token)
    return token


def get_status_markers(token: Token) -> list[str]:
    try:
        data = json.loads(token.status_markers_json)
    except (json.JSONDecodeError, TypeError):
        return []
    return data if isinstance(data, list) else []


def set_status_markers(token: Token, markers: list[str]) -> None:
    token.status_markers_json = json.dumps(markers)


def _fog_rows(db: Session, map_id: int) -> list[FogRegion]:
    return (
        db.query(FogRegion)
        .filter_by(map_id=map_id)
        .order_by(FogRegion.order_index, FogRegion.id)
        .all()
    )


def fog_ops(db: Session, map_id: int) -> list[dict[str, object]]:
    rows = _fog_rows(db, map_id)
    raw = [{"op": r.kind, "geom": json.loads(r.geometry_json)} for r in rows]
    return reduce_fog_ops(raw)


def add_fog_op(db: Session, map_row: Map, op: str, geom: dict[str, object]) -> None:
    next_order = max((r.order_index for r in map_row.fog_regions), default=-1) + 1
    db.add(
        FogRegion(
            map_id=map_row.id, order_index=next_order, kind=op, geometry_json=json.dumps(geom)
        )
    )
    db.commit()


def fog_reveal_all(db: Session, map_row: Map) -> None:
    db.query(FogRegion).filter_by(map_id=map_row.id).delete(synchronize_session=False)
    db.add(
        FogRegion(
            map_id=map_row.id,
            order_index=0,
            kind="reveal",
            geometry_json=json.dumps({"type": "all"}),
        )
    )
    db.commit()


def fog_hide_all(db: Session, map_row: Map) -> None:
    db.query(FogRegion).filter_by(map_id=map_row.id).delete(synchronize_session=False)
    db.commit()


def player_visible_tokens(map_row: Map) -> list[Token]:
    return [t for t in map_row.tokens if token_is_player_visible(t.visible_to_players, t.layer)]
