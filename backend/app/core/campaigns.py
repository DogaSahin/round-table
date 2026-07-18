# backend/app/core/campaigns.py
from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import Campaign
from app.shared.errors import NotFound

COOKIE_NAME = "roundtable_campaign_id"


def get_active_campaign(request: Request, db: Session = Depends(get_db)) -> Campaign:
    raw = request.cookies.get(COOKIE_NAME)
    campaign: Campaign | None = None
    if raw and raw.isdigit():
        campaign = db.get(Campaign, int(raw))
    if campaign is None:
        campaign = db.query(Campaign).filter_by(active=True).first()
    if campaign is None:
        campaign = db.query(Campaign).order_by(Campaign.id).first()
    if campaign is None:
        raise NotFound("no campaign exists")
    return campaign


def list_campaigns(db: Session) -> list[Campaign]:
    return db.query(Campaign).order_by(Campaign.name).all()
