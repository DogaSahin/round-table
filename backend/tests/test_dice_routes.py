# backend/tests/test_dice_routes.py
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


def test_roll_returns_result_and_persists_history() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.post("/api/dice/roll", json={"expression": "2d6+3"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["expression"] == "2d6+3"
        assert isinstance(body["total"], int)

        history_resp = client.get("/api/dice/history")
        assert len(history_resp.json()) == 1
    finally:
        _teardown()


def test_roll_invalid_expression_returns_validation_error_envelope() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.post("/api/dice/roll", json={"expression": "1d1"})
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "validation_error"
    finally:
        _teardown()


def test_saved_roll_create_list_delete() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        create_resp = client.post(
            "/api/dice/saved", json={"label": "Fireball", "expression": "8d6"}
        )
        assert create_resp.status_code == 200
        saved_id = create_resp.json()["id"]

        list_resp = client.get("/api/dice/saved")
        assert len(list_resp.json()) == 1

        delete_resp = client.delete(f"/api/dice/saved/{saved_id}")
        assert delete_resp.status_code == 204

        assert client.get("/api/dice/saved").json() == []
    finally:
        _teardown()


def test_delete_nonexistent_saved_roll_returns_not_found_envelope() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.delete("/api/dice/saved/999999")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"
    finally:
        _teardown()
