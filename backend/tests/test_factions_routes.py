# backend/tests/test_factions_routes.py
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
        create_resp = client.post("/api/factions", json={"name": "The Ashen Circle"})
        assert create_resp.status_code == 200
        faction_id = create_resp.json()["id"]
        assert create_resp.json()["disposition"] == "neutral"
        assert create_resp.json()["clocks"] == []

        list_resp = client.get("/api/factions")
        assert len(list_resp.json()) == 1

        detail_resp = client.get(f"/api/factions/{faction_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["name"] == "The Ashen Circle"
    finally:
        _teardown()


def test_detail_for_nonexistent_faction_returns_not_found_envelope() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.get("/api/factions/999999")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"
    finally:
        _teardown()


def test_update_partial_fields() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        faction_id = client.post("/api/factions", json={"name": "Original"}).json()["id"]

        resp = client.patch(f"/api/factions/{faction_id}", json={"disposition": "hostile"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Original"
        assert resp.json()["disposition"] == "hostile"
    finally:
        _teardown()


def test_delete_faction_returns_204_and_removes_it() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        faction_id = client.post("/api/factions", json={"name": "Doomed"}).json()["id"]

        resp = client.delete(f"/api/factions/{faction_id}")
        assert resp.status_code == 204
        assert client.get("/api/factions").json() == []
    finally:
        _teardown()


def test_clock_create_rejects_out_of_range_segments() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        faction_id = client.post("/api/factions", json={"name": "One"}).json()["id"]

        resp = client.post(
            f"/api/factions/{faction_id}/clocks", json={"name": "Too big", "segments": 13}
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "validation_error"
    finally:
        _teardown()


def test_clock_create_fill_and_delete() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        faction_id = client.post("/api/factions", json={"name": "One"}).json()["id"]

        clock_resp = client.post(
            f"/api/factions/{faction_id}/clocks", json={"name": "Ritual complete", "segments": 6}
        )
        assert clock_resp.status_code == 200
        clock_id = clock_resp.json()["id"]

        fill_resp = client.post(f"/api/factions/clocks/{clock_id}/fill", json={"segment": 2})
        assert fill_resp.status_code == 200
        assert fill_resp.json()["filled"] == 3

        detail = client.get(f"/api/factions/{faction_id}").json()
        assert len(detail["clocks"]) == 1

        delete_resp = client.delete(f"/api/factions/clocks/{clock_id}")
        assert delete_resp.status_code == 204
        assert client.get(f"/api/factions/{faction_id}").json()["clocks"] == []
    finally:
        _teardown()


def test_append_activity_appears_in_detail() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        faction_id = client.post("/api/factions", json={"name": "One"}).json()["id"]

        activity_resp = client.post(
            f"/api/factions/{faction_id}/activity", json={"entry": "Seized the old mill."}
        )
        assert activity_resp.status_code == 200

        detail = client.get(f"/api/factions/{faction_id}").json()
        assert len(detail["activity"]) == 1
        assert detail["activity"][0]["entry"] == "Seized the old mill."
    finally:
        _teardown()
