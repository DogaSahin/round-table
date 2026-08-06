# backend/app/modules/bestiary/routes.py
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.modules.bestiary import service
from app.modules.bestiary.models import BestiaryMonster
from app.modules.bestiary.schemas import (
    BestiaryMonsterCreate,
    BestiaryMonsterDetailOut,
    BestiaryMonsterListItemOut,
    BestiaryMonsterUpdate,
)
from app.shared.errors import NotFound

router = APIRouter(prefix="/api/bestiary", tags=["bestiary"])


def _list_item_out(row: BestiaryMonster) -> BestiaryMonsterListItemOut:
    return BestiaryMonsterListItemOut(
        id=row.id,
        name=row.name,
        slug=row.slug,
        creature_type=row.creature_type,
        challenge_rating=row.challenge_rating,
        is_favorite=row.is_favorite,
        image_url=row.image_url,
    )


def _detail_out(row: BestiaryMonster) -> BestiaryMonsterDetailOut:
    return BestiaryMonsterDetailOut(
        id=row.id,
        name=row.name,
        slug=row.slug,
        statblock=service.load_statblock(row),
        image_url=row.image_url,
        is_favorite=row.is_favorite,
        cloned_from_content_id=row.cloned_from_content_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _get_owned(db: Session, monster_id: int, campaign: Campaign) -> BestiaryMonster:
    row = service.owned(db, monster_id, campaign.id)
    if row is None:
        raise NotFound(f"bestiary monster {monster_id} not found")
    return row


@router.post("", response_model=BestiaryMonsterDetailOut)
def create(
    payload: BestiaryMonsterCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> BestiaryMonsterDetailOut:
    row = service.create_monster(
        db, campaign.id, payload.name, payload.statblock, payload.image_url
    )
    return _detail_out(row)


@router.get("", response_model=list[BestiaryMonsterListItemOut])
def list_monsters(
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
    search: str | None = Query(default=None),
    creature_type: str | None = Query(default=None, alias="type"),
    cr_min: float | None = Query(default=None),
    cr_max: float | None = Query(default=None),
    favorites_only: bool = Query(default=False),
    sort: Literal["name", "cr", "created_at"] = Query(default="name"),
) -> list[BestiaryMonsterListItemOut]:
    rows = service.roster(
        db, campaign.id, search, creature_type, cr_min, cr_max, favorites_only, sort
    )
    return [_list_item_out(r) for r in rows]


@router.get("/{monster_id}", response_model=BestiaryMonsterDetailOut)
def detail(
    monster_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> BestiaryMonsterDetailOut:
    return _detail_out(_get_owned(db, monster_id, campaign))


@router.patch("/{monster_id}", response_model=BestiaryMonsterDetailOut)
def update(
    monster_id: int,
    payload: BestiaryMonsterUpdate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> BestiaryMonsterDetailOut:
    row = _get_owned(db, monster_id, campaign)
    row = service.update_monster(db, row, payload.name, payload.statblock, payload.image_url)
    return _detail_out(row)


@router.delete("/{monster_id}", status_code=204, response_model=None)
def delete(
    monster_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    row = _get_owned(db, monster_id, campaign)
    service.delete_monster(db, row)


@router.post("/{monster_id}/favorite", response_model=BestiaryMonsterDetailOut)
def favorite(
    monster_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> BestiaryMonsterDetailOut:
    row = _get_owned(db, monster_id, campaign)
    row = service.set_favorite(db, row, True)
    return _detail_out(row)


@router.delete("/{monster_id}/favorite", response_model=BestiaryMonsterDetailOut)
def unfavorite(
    monster_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> BestiaryMonsterDetailOut:
    row = _get_owned(db, monster_id, campaign)
    row = service.set_favorite(db, row, False)
    return _detail_out(row)
