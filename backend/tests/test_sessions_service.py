# backend/tests/test_sessions_service.py
from __future__ import annotations

import pytest

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.sessions import service
from app.shared.errors import Validation


def _make_campaign(db) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def test_create_session_assigns_incrementing_number_per_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        first = service.create_session(db, c1.id, "Session One", None)
        second = service.create_session(db, c1.id, "Session Two", None)
        other_campaign = service.create_session(db, c2.id, "Other Campaign S1", None)

        assert first.number == 1
        assert second.number == 2
        assert other_campaign.number == 1
        assert first.date is not None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_roster_and_owned_scoped_to_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        row = service.create_session(db, c1.id, "Session One", None)
        service.create_session(db, c2.id, "Other", None)

        assert len(service.roster(db, c1.id)) == 1
        assert service.owned(db, row.id, c1.id) is not None
        assert service.owned(db, row.id, c2.id) is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_update_session_only_touches_given_fields() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_session(db, campaign.id, "Original Title", None)
        original_date = row.date

        updated = service.update_session(db, row, title=None, date=None, summary="Recap text.")

        assert updated.title == "Original Title"
        assert updated.date == original_date
        assert updated.summary == "Recap text."
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_activate_demotes_incumbent_and_promotes_target() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        first = service.create_session(db, campaign.id, "Session One", None)
        second = service.create_session(db, campaign.id, "Session Two", None)

        service.activate(db, first)
        assert first.status == "active"

        service.activate(db, second)
        db.refresh(first)
        assert first.status == "done"
        assert second.status == "active"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_append_log_and_delete_log() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_session(db, campaign.id, "Session One", None)

        log = service.append_log(db, row, "The party rests.", "none")
        assert log.id is not None
        assert len(service.roster(db, campaign.id)[0].logs) == 1

        service.delete_log(db, log)
        db.refresh(row)
        assert len(row.logs) == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_resolve_log_raises_validation_for_non_thread_tag() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_session(db, campaign.id, "Session One", None)
        log = service.append_log(db, row, "Just loot.", "loot")

        with pytest.raises(Validation):
            service.resolve_log(db, log)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_resolve_and_unresolve_thread_log() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_session(db, campaign.id, "Session One", None)
        log = service.append_log(db, row, "Who sent the assassin?", "thread")

        resolved = service.resolve_log(db, log)
        assert resolved.resolved_at is not None

        unresolved = service.unresolve_log(db, log)
        assert unresolved.resolved_at is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_compile_recap_for_session_delegates_to_recap_module() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_session(db, campaign.id, "Session One", None)
        service.append_log(db, row, "Goblins ambush the party.", "combat")
        db.refresh(row)

        text = service.compile_recap_for_session(row, tags=[])
        assert "## Combat" in text
        assert "Goblins ambush the party." in text
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
