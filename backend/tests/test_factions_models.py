from __future__ import annotations

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.factions.models import Faction, FactionActivity, FactionClock


def _make_campaign(session) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def test_faction_roundtrip_and_defaults() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        row = Faction(campaign_id=campaign.id, name="The Ashen Circle")
        session.add(row)
        session.commit()
        session.refresh(row)
        assert row.id is not None
        assert row.disposition == "neutral"
        assert row.description is None
        assert row.goals is None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_faction_clock_roundtrip_defaults_and_relationship() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        row = Faction(campaign_id=campaign.id, name="The Ashen Circle")
        session.add(row)
        session.commit()
        session.refresh(row)

        clock = FactionClock(faction_id=row.id, name="Ritual complete")
        session.add(clock)
        session.commit()
        session.refresh(clock)

        assert clock.id is not None
        assert clock.segments == 6
        assert clock.filled == 0

        session.refresh(row)
        assert len(row.clocks) == 1
        assert row.clocks[0].id == clock.id
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_faction_activity_roundtrip_and_relationship() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        row = Faction(campaign_id=campaign.id, name="The Ashen Circle")
        session.add(row)
        session.commit()
        session.refresh(row)

        activity = FactionActivity(faction_id=row.id, entry="Seized the old mill.")
        session.add(activity)
        session.commit()
        session.refresh(activity)

        assert activity.id is not None
        assert activity.occurred_at is not None

        session.refresh(row)
        assert len(row.activity) == 1
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_deleting_faction_cascades_clocks_and_activity() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        row = Faction(campaign_id=campaign.id, name="The Ashen Circle")
        session.add(row)
        session.commit()
        session.refresh(row)

        row.clocks.append(FactionClock(name="Ritual complete"))
        row.activity.append(FactionActivity(entry="Seized the old mill."))
        session.commit()

        session.delete(row)
        session.commit()

        assert session.query(FactionClock).count() == 0
        assert session.query(FactionActivity).count() == 0
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
