# backend/app/modules/dice/service.py
from __future__ import annotations

import json
from dataclasses import asdict

from sqlalchemy.orm import Session

from app.engine.dice import RollResult, evaluate
from app.modules.dice.models import RollHistory, SavedRoll

HISTORY_LIMIT = 50


def roll_and_log(db: Session, campaign_id: int, expression: str) -> RollResult:
    result = evaluate(expression)
    db.add(
        RollHistory(
            campaign_id=campaign_id,
            expression=expression,
            result=result.total,
            breakdown_json=json.dumps(asdict(result)),
        )
    )
    db.commit()
    return result


def list_history(db: Session, campaign_id: int) -> list[RollHistory]:
    return (
        db.query(RollHistory)
        .filter_by(campaign_id=campaign_id)
        .order_by(RollHistory.rolled_at.desc(), RollHistory.id.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )


def list_saved(db: Session, campaign_id: int) -> list[SavedRoll]:
    return db.query(SavedRoll).filter_by(campaign_id=campaign_id).order_by(SavedRoll.label).all()


def create_saved(db: Session, campaign_id: int, label: str, expression: str) -> SavedRoll:
    obj = SavedRoll(campaign_id=campaign_id, label=label.strip(), expression=expression.strip())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_saved(db: Session, campaign_id: int, saved_id: int) -> bool:
    obj = db.get(SavedRoll, saved_id)
    if obj is None or obj.campaign_id != campaign_id:
        return False
    db.delete(obj)
    db.commit()
    return True
