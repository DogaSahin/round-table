# backend/tests/test_database.py
from __future__ import annotations

from sqlalchemy import inspect

from app.core.database import Base, SessionLocal, engine, get_db
from app.core.models import AppSetting, Campaign  # noqa: F401 - exercises models import surface


def test_tables_create_from_metadata() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert "campaign" in tables
    assert "app_setting" in tables
    Base.metadata.drop_all(bind=engine)


def test_campaign_roundtrip() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = Campaign(name="Test Campaign", active=True)
        session.add(campaign)
        session.commit()
        session.refresh(campaign)
        assert campaign.id is not None
        assert campaign.created_at is not None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_get_db_yields_and_closes_session() -> None:
    gen = get_db()
    session = next(gen)
    assert session.is_active
    gen_exhausted = False
    try:
        next(gen)
    except StopIteration:
        gen_exhausted = True
    assert gen_exhausted
