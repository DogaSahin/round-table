from __future__ import annotations

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.dice.models import RollHistory, SavedRoll


def _make_campaign(session) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def test_saved_roll_roundtrip() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        saved = SavedRoll(campaign_id=campaign.id, label="Fireball", expression="8d6")
        session.add(saved)
        session.commit()
        session.refresh(saved)
        assert saved.id is not None
        assert saved.label == "Fireball"
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_roll_history_roundtrip_and_default_timestamp() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        entry = RollHistory(
            campaign_id=campaign.id,
            expression="1d20+5",
            result=17,
            breakdown_json='{"total": 17}',
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        assert entry.id is not None
        assert entry.rolled_at is not None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
