# backend/app/modules/factions/service.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.engine.clocks import toggle_fill
from app.modules.factions.models import Faction, FactionActivity, FactionClock


def roster(db: Session, campaign_id: int) -> list[Faction]:
    return db.query(Faction).filter_by(campaign_id=campaign_id).order_by(Faction.name).all()


def owned(db: Session, faction_id: int, campaign_id: int) -> Faction | None:
    row = db.get(Faction, faction_id)
    return row if row is not None and row.campaign_id == campaign_id else None


def owned_clock(db: Session, clock_id: int, campaign_id: int) -> FactionClock | None:
    clock = db.get(FactionClock, clock_id)
    if clock is None or clock.faction.campaign_id != campaign_id:
        return None
    return clock


def create_faction(
    db: Session,
    campaign_id: int,
    name: str,
    disposition: str,
    goals: str | None,
    description: str | None,
) -> Faction:
    row = Faction(
        campaign_id=campaign_id,
        name=name,
        disposition=disposition,
        goals=goals,
        description=description,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_faction(
    db: Session,
    faction_row: Faction,
    name: str | None,
    disposition: str | None,
    goals: str | None,
    description: str | None,
) -> Faction:
    if name is not None:
        faction_row.name = name
    if disposition is not None:
        faction_row.disposition = disposition
    if goals is not None:
        faction_row.goals = goals
    if description is not None:
        faction_row.description = description
    db.commit()
    db.refresh(faction_row)
    return faction_row


def delete_faction(db: Session, faction_row: Faction) -> None:
    db.delete(faction_row)
    db.commit()


def create_clock(db: Session, faction_row: Faction, name: str, segments: int) -> FactionClock:
    clock = FactionClock(faction_id=faction_row.id, name=name, segments=segments, filled=0)
    db.add(clock)
    db.commit()
    db.refresh(clock)
    return clock


def delete_clock(db: Session, clock: FactionClock) -> None:
    db.delete(clock)
    db.commit()


def fill_clock(db: Session, clock: FactionClock, segment_clicked: int) -> FactionClock:
    clock.filled = toggle_fill(clock.filled, segment_clicked, clock.segments)
    db.commit()
    db.refresh(clock)
    return clock


def append_activity(db: Session, faction_row: Faction, entry: str) -> FactionActivity:
    activity = FactionActivity(faction_id=faction_row.id, entry=entry)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity
