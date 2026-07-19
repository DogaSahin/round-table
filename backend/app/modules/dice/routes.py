# backend/app/modules/dice/routes.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.engine.dice import DiceError
from app.modules.dice import service
from app.modules.dice.schemas import (
    HistoryEntryOut,
    RollRequest,
    RollResultOut,
    RollTermOut,
    SavedRollCreate,
    SavedRollOut,
)
from app.shared.errors import NotFound, Validation

router = APIRouter(prefix="/api/dice", tags=["dice"])


@router.post("/roll", response_model=RollResultOut)
def roll(
    payload: RollRequest,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> RollResultOut:
    try:
        result = service.roll_and_log(db, campaign.id, payload.expression)
    except DiceError as exc:
        raise Validation(str(exc)) from exc
    return RollResultOut(
        expression=result.expression,
        total=result.total,
        terms=[
            RollTermOut(
                source=t.source,
                sign=t.sign,
                is_dice=t.is_dice,
                total=t.total,
                kept=t.kept,
                discarded=t.discarded,
                flat=t.flat,
            )
            for t in result.terms
        ],
    )


@router.get("/history", response_model=list[HistoryEntryOut])
def history(
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> list[HistoryEntryOut]:
    rows = service.list_history(db, campaign.id)
    return [
        HistoryEntryOut(id=r.id, expression=r.expression, result=r.result, rolled_at=r.rolled_at)
        for r in rows
    ]


@router.get("/saved", response_model=list[SavedRollOut])
def list_saved(
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> list[SavedRollOut]:
    rows = service.list_saved(db, campaign.id)
    return [SavedRollOut(id=r.id, label=r.label, expression=r.expression) for r in rows]


@router.post("/saved", response_model=SavedRollOut)
def create_saved(
    payload: SavedRollCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> SavedRollOut:
    obj = service.create_saved(db, campaign.id, payload.label, payload.expression)
    return SavedRollOut(id=obj.id, label=obj.label, expression=obj.expression)


@router.delete("/saved/{saved_id}", status_code=204, response_model=None)
def delete_saved(
    saved_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    deleted = service.delete_saved(db, campaign.id, saved_id)
    if not deleted:
        raise NotFound(f"saved roll {saved_id} not found")
