# backend/tests/test_dice_service.py
from __future__ import annotations

import pytest

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.engine.dice import DiceError
from app.modules.dice import service


def _make_campaign(session) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def test_roll_and_log_persists_history() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        result = service.roll_and_log(session, campaign.id, "2d6+3")
        assert result.expression == "2d6+3"
        history = service.list_history(session, campaign.id)
        assert len(history) == 1
        assert history[0].result == result.total
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_roll_and_log_raises_dice_error_without_persisting() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        with pytest.raises(DiceError):
            service.roll_and_log(session, campaign.id, "")
        assert service.list_history(session, campaign.id) == []
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_list_history_scoped_to_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        c1, c2 = _make_campaign(session), _make_campaign(session)
        service.roll_and_log(session, c1.id, "1d4")
        service.roll_and_log(session, c2.id, "1d6")
        assert len(service.list_history(session, c1.id)) == 1
        assert len(service.list_history(session, c2.id)) == 1
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_saved_roll_crud() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        created = service.create_saved(session, campaign.id, "  Fireball  ", "  8d6  ")
        assert created.label == "Fireball"
        assert created.expression == "8d6"

        saved = service.list_saved(session, campaign.id)
        assert len(saved) == 1

        deleted = service.delete_saved(session, campaign.id, created.id)
        assert deleted is True
        assert service.list_saved(session, campaign.id) == []
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_delete_saved_returns_false_for_wrong_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        c1, c2 = _make_campaign(session), _make_campaign(session)
        created = service.create_saved(session, c1.id, "Guard", "1d20")
        deleted = service.delete_saved(session, c2.id, created.id)
        assert deleted is False
        assert len(service.list_saved(session, c1.id)) == 1
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
