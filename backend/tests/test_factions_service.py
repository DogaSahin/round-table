# backend/tests/test_factions_service.py
from __future__ import annotations

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.factions import service


def _make_campaign(db) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def test_create_and_roster_scoped_to_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        service.create_faction(db, c1.id, "The Ashen Circle", "neutral", None, None)
        service.create_faction(db, c2.id, "Other Campaign Faction", "neutral", None, None)

        assert len(service.roster(db, c1.id)) == 1
        assert len(service.roster(db, c2.id)) == 1
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_owned_scoped_to_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        row = service.create_faction(db, c1.id, "The Ashen Circle", "neutral", None, None)

        assert service.owned(db, row.id, c1.id) is not None
        assert service.owned(db, row.id, c2.id) is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_update_faction_only_touches_given_fields() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_faction(db, campaign.id, "Original", "neutral", None, None)

        updated = service.update_faction(
            db, row, name=None, disposition="hostile", goals=None, description=None
        )

        assert updated.name == "Original"
        assert updated.disposition == "hostile"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_delete_faction_cascades_clocks() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_faction(db, campaign.id, "Original", "neutral", None, None)
        service.create_clock(db, row, "Ritual complete", 6)

        service.delete_faction(db, row)
        assert service.roster(db, campaign.id) == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_and_delete_clock() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_faction(db, campaign.id, "Original", "neutral", None, None)
        clock = service.create_clock(db, row, "Ritual complete", 8)
        assert clock.segments == 8
        assert clock.filled == 0

        service.delete_clock(db, clock)
        db.refresh(row)
        assert len(row.clocks) == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_fill_clock_delegates_to_engine_toggle() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_faction(db, campaign.id, "Original", "neutral", None, None)
        clock = service.create_clock(db, row, "Ritual complete", 6)

        filled = service.fill_clock(db, clock, segment_clicked=2)
        assert filled.filled == 3

        toggled_off = service.fill_clock(db, clock, segment_clicked=2)
        assert toggled_off.filled == 2
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_append_activity() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_faction(db, campaign.id, "Original", "neutral", None, None)

        activity = service.append_activity(db, row, "Seized the old mill.")
        assert activity.id is not None
        db.refresh(row)
        assert len(row.activity) == 1
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
