# backend/app/modules/npcs/routes.py
from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.modules.npcs import service
from app.modules.npcs.models import Npc
from app.modules.npcs.schemas import Disposition, NpcCreate, NpcDetailOut, NpcListItemOut, NpcUpdate
from app.shared.errors import NotFound

router = APIRouter(prefix="/api/npcs", tags=["npcs"])


def _detail_out(npc_row: Npc) -> NpcDetailOut:
    return NpcDetailOut(
        id=npc_row.id,
        name=npc_row.name,
        disposition=cast(Disposition, npc_row.disposition),
        faction_id=npc_row.faction_id,
        statblock=npc_row.statblock,
        motivation=npc_row.motivation,
        secrets=npc_row.secrets,
        voice=npc_row.voice,
        portrait_path=npc_row.portrait_path,
        player_visible=npc_row.player_visible,
    )


def _get_owned(db: Session, npc_id: int, campaign: Campaign) -> Npc:
    row = service.owned(db, npc_id, campaign.id)
    if row is None:
        raise NotFound(f"npc {npc_id} not found")
    return row


@router.post("", response_model=NpcDetailOut)
def create(
    payload: NpcCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> NpcDetailOut:
    row = service.create_npc(
        db,
        campaign.id,
        payload.name,
        payload.disposition,
        payload.faction_id,
        payload.statblock,
        payload.motivation,
        payload.secrets,
        payload.voice,
        payload.player_visible,
    )
    return _detail_out(row)


@router.get("", response_model=list[NpcListItemOut])
def list_npcs(
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> list[NpcListItemOut]:
    rows = service.roster(db, campaign.id)
    return [
        NpcListItemOut(
            id=r.id,
            name=r.name,
            disposition=cast(Disposition, r.disposition),
            faction_id=r.faction_id,
        )
        for r in rows
    ]


@router.get("/{npc_id}", response_model=NpcDetailOut)
def detail(
    npc_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> NpcDetailOut:
    return _detail_out(_get_owned(db, npc_id, campaign))


@router.patch("/{npc_id}", response_model=NpcDetailOut)
def update(
    npc_id: int,
    payload: NpcUpdate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> NpcDetailOut:
    row = _get_owned(db, npc_id, campaign)
    row = service.update_npc(
        db,
        row,
        payload.name,
        payload.disposition,
        payload.faction_id,
        payload.statblock,
        payload.motivation,
        payload.secrets,
        payload.voice,
        payload.player_visible,
    )
    return _detail_out(row)


@router.delete("/{npc_id}", status_code=204, response_model=None)
def delete(
    npc_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    row = _get_owned(db, npc_id, campaign)
    service.delete_npc(db, row)
