# backend/tests/test_sessions_models.py
from __future__ import annotations

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.sessions.models import THREAD_TAG, GameSession, SessionLog


def _make_campaign(session) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def test_game_session_roundtrip_and_defaults() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        row = GameSession(campaign_id=campaign.id, number=1, title="Session One")
        session.add(row)
        session.commit()
        session.refresh(row)
        assert row.id is not None
        assert row.date is not None
        assert row.status == "planned"
        assert row.summary is None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_session_log_roundtrip_defaults_and_relationship() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        row = GameSession(campaign_id=campaign.id, number=1, title="Session One")
        session.add(row)
        session.commit()
        session.refresh(row)

        log = SessionLog(session_id=row.id, text="The party enters the crypt.", tag=THREAD_TAG)
        session.add(log)
        session.commit()
        session.refresh(log)

        assert log.id is not None
        assert log.tag == THREAD_TAG
        assert log.logged_at is not None
        assert log.resolved_at is None

        session.refresh(row)
        assert len(row.logs) == 1
        assert row.logs[0].id == log.id
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_deleting_session_cascades_logs() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        row = GameSession(campaign_id=campaign.id, number=1, title="Session One")
        session.add(row)
        session.commit()
        session.refresh(row)

        row.logs.append(SessionLog(text="loot found", tag="loot"))
        session.commit()

        session.delete(row)
        session.commit()

        assert session.query(SessionLog).count() == 0
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
