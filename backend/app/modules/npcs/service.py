# backend/app/modules/npcs/service.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.npcs.models import Npc


def roster(db: Session, campaign_id: int) -> list[Npc]:
    return db.query(Npc).filter_by(campaign_id=campaign_id).order_by(Npc.name).all()


def owned(db: Session, npc_id: int, campaign_id: int) -> Npc | None:
    row = db.get(Npc, npc_id)
    return row if row is not None and row.campaign_id == campaign_id else None


def create_npc(
    db: Session,
    campaign_id: int,
    name: str,
    disposition: str,
    faction_id: int | None,
    statblock: str | None,
    motivation: str | None,
    secrets: str | None,
    voice: str | None,
    player_visible: bool,
) -> Npc:
    row = Npc(
        campaign_id=campaign_id,
        name=name,
        disposition=disposition,
        faction_id=faction_id,
        statblock=statblock,
        motivation=motivation,
        secrets=secrets,
        voice=voice,
        player_visible=player_visible,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_npc(
    db: Session,
    npc_row: Npc,
    name: str | None,
    disposition: str | None,
    faction_id: int | None,
    statblock: str | None,
    motivation: str | None,
    secrets: str | None,
    voice: str | None,
    player_visible: bool | None,
) -> Npc:
    if name is not None:
        npc_row.name = name
    if disposition is not None:
        npc_row.disposition = disposition
    if faction_id is not None:
        npc_row.faction_id = faction_id
    if statblock is not None:
        npc_row.statblock = statblock
    if motivation is not None:
        npc_row.motivation = motivation
    if secrets is not None:
        npc_row.secrets = secrets
    if voice is not None:
        npc_row.voice = voice
    if player_visible is not None:
        npc_row.player_visible = player_visible
    db.commit()
    db.refresh(npc_row)
    return npc_row


def delete_npc(db: Session, npc_row: Npc) -> None:
    db.delete(npc_row)
    db.commit()
