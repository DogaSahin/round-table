# backend/tests/test_campaigns.py
from __future__ import annotations

import pytest
from starlette.requests import Request

from app.core.campaigns import COOKIE_NAME, get_active_campaign, list_campaigns
from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.shared.errors import NotFound


def _make_request(cookie_value: str | None = None) -> Request:
    headers = []
    if cookie_value is not None:
        headers.append((b"cookie", f"{COOKIE_NAME}={cookie_value}".encode()))
    scope = {"type": "http", "headers": headers, "method": "GET", "path": "/"}
    return Request(scope)


def test_resolves_from_cookie_when_present() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        a = Campaign(name="A", active=False)
        b = Campaign(name="B", active=True)
        session.add_all([a, b])
        session.commit()
        session.refresh(a)

        result = get_active_campaign(_make_request(str(a.id)), session)
        assert result.id == a.id
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_falls_back_to_active_flag_when_no_cookie() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        session.add(Campaign(name="Inactive", active=False))
        active = Campaign(name="Active", active=True)
        session.add(active)
        session.commit()
        session.refresh(active)

        result = get_active_campaign(_make_request(), session)
        assert result.id == active.id
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_falls_back_to_first_by_id_when_no_cookie_and_no_active_flag() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        first = Campaign(name="First", active=False)
        session.add(first)
        session.add(Campaign(name="Second", active=False))
        session.commit()
        session.refresh(first)

        result = get_active_campaign(_make_request(), session)
        assert result.id == first.id
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_raises_not_found_when_no_campaign_exists() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        with pytest.raises(NotFound):
            get_active_campaign(_make_request(), session)
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_cookie_with_nonexistent_id_falls_back() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        real = Campaign(name="Real", active=True)
        session.add(real)
        session.commit()
        session.refresh(real)

        result = get_active_campaign(_make_request("999999"), session)
        assert result.id == real.id
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_list_campaigns_orders_by_name() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        session.add(Campaign(name="Zeta", active=False))
        session.add(Campaign(name="Alpha", active=False))
        session.commit()

        names = [c.name for c in list_campaigns(session)]
        assert names == ["Alpha", "Zeta"]
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
