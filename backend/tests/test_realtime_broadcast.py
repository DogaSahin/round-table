# backend/tests/test_realtime_broadcast.py
from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.core.realtime.broadcast import (
    BROADCAST_TOPIC,
    get_state,
    publish_changed,
    set_active_encounter,
    set_active_map,
    snapshot,
)
from app.core.realtime.manager import manager


def _make_campaign(session: Session) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def test_get_state_creates_row_on_first_access() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        state = get_state(session, campaign.id)
        assert state.campaign_id == campaign.id
        assert state.active_encounter_id is None
        assert state.active_map_id is None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_get_state_returns_same_row_on_second_access() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        first = get_state(session, campaign.id)
        second = get_state(session, campaign.id)
        assert first.id == second.id
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_set_active_encounter_persists() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        set_active_encounter(session, campaign.id, 42)
        assert snapshot(session, campaign.id) == {"active_encounter_id": 42, "active_map_id": None}
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_set_active_map_persists() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        set_active_map(session, campaign.id, 7)
        assert snapshot(session, campaign.id) == {"active_encounter_id": None, "active_map_id": 7}
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_snapshot_has_only_the_two_pointer_fields() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        assert set(snapshot(session, campaign.id).keys()) == {
            "active_encounter_id",
            "active_map_id",
        }
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_publish_changed_sends_contentless_signal() -> None:
    class _FakeWebSocket:
        def __init__(self) -> None:
            self.sent: list[dict[str, Any]] = []

        async def send_json(self, message: dict[str, Any]) -> None:
            self.sent.append(message)

    ws = _FakeWebSocket()
    manager.subscribe(BROADCAST_TOPIC, ws)
    try:
        asyncio.run(publish_changed(99))
        assert ws.sent == [{"action": "broadcast_changed", "campaign_id": 99}]
    finally:
        manager.unsubscribe(ws)
