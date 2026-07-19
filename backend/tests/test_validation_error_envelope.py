# backend/tests/test_validation_error_envelope.py
"""Reproduces the bug where FastAPI's built-in RequestValidationError (raised
when a request body fails Pydantic field constraints, e.g. Field(min_length=1))
bypasses the shared JSON error envelope and falls through to FastAPI's raw
{"detail": [...]} shape instead of {"error": {"code", "message", "details"}}.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.campaigns import get_active_campaign
from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.main import app


def _setup_campaign() -> Campaign:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    campaign = Campaign(name="Test Campaign", active=True)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    session.close()
    return campaign


def _teardown() -> None:
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_active_campaign, None)


def test_pydantic_field_validation_error_uses_shared_envelope() -> None:
    """An empty `expression` fails RollRequest's Field(min_length=1) constraint,
    which FastAPI raises as RequestValidationError -- a different exception
    type than the app's own Validation(AppError). This must still produce the
    shared envelope shape, not FastAPI's raw {"detail": [...]}."""
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.post("/api/dice/roll", json={"expression": ""})
        assert resp.status_code == 422
        body = resp.json()
        assert "detail" not in body
        assert body["error"]["code"] == "validation_error"
        assert isinstance(body["error"]["message"], str) and body["error"]["message"]
        assert "details" in body["error"]
    finally:
        _teardown()
