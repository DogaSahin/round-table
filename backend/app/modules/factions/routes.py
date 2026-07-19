# backend/app/modules/factions/routes.py
from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.modules.factions import service
from app.modules.factions.models import Faction, FactionClock
from app.modules.factions.schemas import (
    ActivityCreate,
    ActivityOut,
    ClockCreate,
    ClockOut,
    Disposition,
    FactionCreate,
    FactionDetailOut,
    FactionListItemOut,
    FactionUpdate,
    FillClockRequest,
)
from app.shared.errors import NotFound

router = APIRouter(prefix="/api/factions", tags=["factions"])


def _clock_out(clock: FactionClock) -> ClockOut:
    return ClockOut(id=clock.id, name=clock.name, segments=clock.segments, filled=clock.filled)


def _detail_out(faction_row: Faction) -> FactionDetailOut:
    return FactionDetailOut(
        id=faction_row.id,
        name=faction_row.name,
        description=faction_row.description,
        disposition=cast(Disposition, faction_row.disposition),
        goals=faction_row.goals,
        clocks=[_clock_out(c) for c in faction_row.clocks],
        activity=[
            ActivityOut(id=a.id, entry=a.entry, occurred_at=a.occurred_at)
            for a in faction_row.activity
        ],
    )


def _get_owned(db: Session, faction_id: int, campaign: Campaign) -> Faction:
    row = service.owned(db, faction_id, campaign.id)
    if row is None:
        raise NotFound(f"faction {faction_id} not found")
    return row


def _get_owned_clock(db: Session, clock_id: int, campaign: Campaign) -> FactionClock:
    clock = service.owned_clock(db, clock_id, campaign.id)
    if clock is None:
        raise NotFound(f"faction clock {clock_id} not found")
    return clock


@router.post("", response_model=FactionDetailOut)
def create(
    payload: FactionCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> FactionDetailOut:
    row = service.create_faction(
        db, campaign.id, payload.name, payload.disposition, payload.goals, payload.description
    )
    return _detail_out(row)


@router.get("", response_model=list[FactionListItemOut])
def list_factions(
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> list[FactionListItemOut]:
    rows = service.roster(db, campaign.id)
    return [
        FactionListItemOut(id=r.id, name=r.name, disposition=cast(Disposition, r.disposition))
        for r in rows
    ]


@router.get("/{faction_id}", response_model=FactionDetailOut)
def detail(
    faction_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> FactionDetailOut:
    return _detail_out(_get_owned(db, faction_id, campaign))


@router.patch("/{faction_id}", response_model=FactionDetailOut)
def update(
    faction_id: int,
    payload: FactionUpdate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> FactionDetailOut:
    row = _get_owned(db, faction_id, campaign)
    row = service.update_faction(
        db, row, payload.name, payload.disposition, payload.goals, payload.description
    )
    return _detail_out(row)


@router.delete("/{faction_id}", status_code=204, response_model=None)
def delete(
    faction_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    row = _get_owned(db, faction_id, campaign)
    service.delete_faction(db, row)


@router.post("/{faction_id}/clocks", response_model=ClockOut)
def create_clock(
    faction_id: int,
    payload: ClockCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> ClockOut:
    row = _get_owned(db, faction_id, campaign)
    clock = service.create_clock(db, row, payload.name, payload.segments)
    return _clock_out(clock)


@router.delete("/clocks/{clock_id}", status_code=204, response_model=None)
def delete_clock(
    clock_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    clock = _get_owned_clock(db, clock_id, campaign)
    service.delete_clock(db, clock)


@router.post("/clocks/{clock_id}/fill", response_model=ClockOut)
def fill_clock(
    clock_id: int,
    payload: FillClockRequest,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> ClockOut:
    clock = _get_owned_clock(db, clock_id, campaign)
    return _clock_out(service.fill_clock(db, clock, payload.segment))


@router.post("/{faction_id}/activity", response_model=ActivityOut)
def append_activity(
    faction_id: int,
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> ActivityOut:
    row = _get_owned(db, faction_id, campaign)
    activity = service.append_activity(db, row, payload.entry)
    return ActivityOut(id=activity.id, entry=activity.entry, occurred_at=activity.occurred_at)
