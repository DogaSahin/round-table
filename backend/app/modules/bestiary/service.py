# backend/app/modules/bestiary/service.py
from __future__ import annotations

import json
import re
from datetime import UTC, datetime

from sqlalchemy import asc, or_
from sqlalchemy.orm import Session

from app.modules.bestiary.models import BestiaryMonster
from app.shared.statblock import Statblock

_SLUG_RE = re.compile(r"[^a-z0-9]+")

_SORT_COLUMNS = {
    "name": BestiaryMonster.name,
    "cr": BestiaryMonster.challenge_rating,
    "created_at": BestiaryMonster.created_at,
}


def _slugify(text: str) -> str:
    slug = _SLUG_RE.sub("-", (text or "").strip().lower()).strip("-")
    return slug or "monster"


def unique_slug(db: Session, campaign_id: int, name: str) -> str:
    base = _slugify(name)
    slug = base
    n = 2
    while (
        db.query(BestiaryMonster).filter_by(campaign_id=campaign_id, slug=slug).first() is not None
    ):
        slug = f"{base}-{n}"
        n += 1
    return slug


def roster(
    db: Session,
    campaign_id: int,
    search: str | None,
    creature_type: str | None,
    cr_min: float | None,
    cr_max: float | None,
    favorites_only: bool,
    sort: str,
) -> list[BestiaryMonster]:
    query = db.query(BestiaryMonster).filter_by(campaign_id=campaign_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(BestiaryMonster.name.ilike(like), BestiaryMonster.creature_type.ilike(like))
        )
    if creature_type:
        query = query.filter(BestiaryMonster.creature_type == creature_type)
    if cr_min is not None:
        query = query.filter(BestiaryMonster.challenge_rating >= cr_min)
    if cr_max is not None:
        query = query.filter(BestiaryMonster.challenge_rating <= cr_max)
    if favorites_only:
        query = query.filter(BestiaryMonster.is_favorite.is_(True))

    column = _SORT_COLUMNS.get(sort, BestiaryMonster.name)
    return query.order_by(asc(column)).all()


def owned(db: Session, monster_id: int, campaign_id: int) -> BestiaryMonster | None:
    row = db.get(BestiaryMonster, monster_id)
    return row if row is not None and row.campaign_id == campaign_id else None


def create_monster(
    db: Session,
    campaign_id: int,
    name: str,
    statblock: Statblock,
    image_url: str | None,
) -> BestiaryMonster:
    row = BestiaryMonster(
        campaign_id=campaign_id,
        name=name,
        slug=unique_slug(db, campaign_id, name),
        statblock=statblock.model_dump_json(),
        creature_type=statblock.creature_type,
        challenge_rating=statblock.challenge_rating,
        image_url=image_url,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_monster(
    db: Session,
    monster_row: BestiaryMonster,
    name: str | None,
    statblock: Statblock | None,
    image_url: str | None,
) -> BestiaryMonster:
    if name is not None:
        monster_row.name = name
        # Slug is intentionally NOT regenerated (keeps any stable reference stable).
    if statblock is not None:
        monster_row.statblock = statblock.model_dump_json()
        monster_row.creature_type = statblock.creature_type
        monster_row.challenge_rating = statblock.challenge_rating
    if image_url is not None:
        monster_row.image_url = image_url
    monster_row.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(monster_row)
    return monster_row


def set_favorite(db: Session, monster_row: BestiaryMonster, value: bool) -> BestiaryMonster:
    monster_row.is_favorite = value
    monster_row.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(monster_row)
    return monster_row


def delete_monster(db: Session, monster_row: BestiaryMonster) -> None:
    db.delete(monster_row)
    db.commit()


def load_statblock(monster_row: BestiaryMonster) -> Statblock:
    return Statblock.model_validate(json.loads(monster_row.statblock))
