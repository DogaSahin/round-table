# backend/tests/test_npcs_routes.py
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


def test_create_list_and_detail_roundtrip() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        create_resp = client.post("/api/npcs", json={"name": "Old Man Grigg"})
        assert create_resp.status_code == 200
        npc_id = create_resp.json()["id"]
        assert create_resp.json()["disposition"] == "neutral"
        assert create_resp.json()["player_visible"] is False
        assert create_resp.json()["portrait_path"] is None

        list_resp = client.get("/api/npcs")
        assert len(list_resp.json()) == 1

        detail_resp = client.get(f"/api/npcs/{npc_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["name"] == "Old Man Grigg"
    finally:
        _teardown()


def test_create_rejects_empty_name_with_validation_envelope() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.post("/api/npcs", json={"name": ""})
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "validation_error"
    finally:
        _teardown()


def test_detail_for_nonexistent_npc_returns_not_found_envelope() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.get("/api/npcs/999999")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"
    finally:
        _teardown()


def test_update_partial_fields() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        npc_id = client.post("/api/npcs", json={"name": "Original"}).json()["id"]

        resp = client.patch(f"/api/npcs/{npc_id}", json={"disposition": "hostile"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Original"
        assert resp.json()["disposition"] == "hostile"
    finally:
        _teardown()


def test_delete_npc_returns_204_and_removes_it() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        npc_id = client.post("/api/npcs", json={"name": "Doomed"}).json()["id"]

        resp = client.delete(f"/api/npcs/{npc_id}")
        assert resp.status_code == 204
        assert client.get("/api/npcs").json() == []
    finally:
        _teardown()


def test_npc_with_faction_id_and_secrets_roundtrips() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.post(
            "/api/npcs",
            json={
                "name": "Old Man Grigg",
                "faction_id": 7,
                "secrets": "Actually a retired assassin.",
                "player_visible": True,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["faction_id"] == 7
        assert body["secrets"] == "Actually a retired assassin."
        assert body["player_visible"] is True
    finally:
        _teardown()
