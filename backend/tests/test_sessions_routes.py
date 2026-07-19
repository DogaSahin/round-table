# backend/tests/test_sessions_routes.py
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
        create_resp = client.post("/api/sessions", json={"title": "Session One"})
        assert create_resp.status_code == 200
        session_id = create_resp.json()["id"]
        assert create_resp.json()["number"] == 1
        assert create_resp.json()["logs"] == []

        list_resp = client.get("/api/sessions")
        assert len(list_resp.json()) == 1

        detail_resp = client.get(f"/api/sessions/{session_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["title"] == "Session One"
    finally:
        _teardown()


def test_detail_for_nonexistent_session_returns_not_found_envelope() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.get("/api/sessions/999999")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"
    finally:
        _teardown()


def test_update_partial_fields() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        session_id = client.post("/api/sessions", json={"title": "Original"}).json()["id"]

        resp = client.patch(f"/api/sessions/{session_id}", json={"summary": "It happened."})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Original"
        assert resp.json()["summary"] == "It happened."
    finally:
        _teardown()


def test_delete_session_returns_204_and_removes_it() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        session_id = client.post("/api/sessions", json={"title": "Doomed"}).json()["id"]

        resp = client.delete(f"/api/sessions/{session_id}")
        assert resp.status_code == 204
        assert client.get("/api/sessions").json() == []
    finally:
        _teardown()


def test_activate_demotes_previous_active_session() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        first_id = client.post("/api/sessions", json={"title": "One"}).json()["id"]
        second_id = client.post("/api/sessions", json={"title": "Two"}).json()["id"]

        client.post(f"/api/sessions/{first_id}/activate")
        resp = client.post(f"/api/sessions/{second_id}/activate")
        assert resp.json()["status"] == "active"

        first_detail = client.get(f"/api/sessions/{first_id}").json()
        assert first_detail["status"] == "done"
    finally:
        _teardown()


def test_add_log_appears_in_detail() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        session_id = client.post("/api/sessions", json={"title": "One"}).json()["id"]

        log_resp = client.post(
            f"/api/sessions/{session_id}/logs", json={"text": "Goblins!", "tag": "combat"}
        )
        assert log_resp.status_code == 200
        log_id = log_resp.json()["id"]

        detail = client.get(f"/api/sessions/{session_id}").json()
        assert len(detail["logs"]) == 1
        assert detail["logs"][0]["id"] == log_id

        delete_resp = client.delete(f"/api/sessions/logs/{log_id}")
        assert delete_resp.status_code == 204
        assert client.get(f"/api/sessions/{session_id}").json()["logs"] == []
    finally:
        _teardown()


def test_resolve_nonthread_log_returns_validation_envelope() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        session_id = client.post("/api/sessions", json={"title": "One"}).json()["id"]
        log_id = client.post(
            f"/api/sessions/{session_id}/logs", json={"text": "Loot.", "tag": "loot"}
        ).json()["id"]

        resp = client.post(f"/api/sessions/logs/{log_id}/resolve")
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "validation_error"
    finally:
        _teardown()


def test_resolve_and_unresolve_thread_log() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        session_id = client.post("/api/sessions", json={"title": "One"}).json()["id"]
        log_id = client.post(
            f"/api/sessions/{session_id}/logs", json={"text": "Who sent them?", "tag": "thread"}
        ).json()["id"]

        resolved = client.post(f"/api/sessions/logs/{log_id}/resolve")
        assert resolved.json()["resolved_at"] is not None

        unresolved = client.post(f"/api/sessions/logs/{log_id}/unresolve")
        assert unresolved.json()["resolved_at"] is None
    finally:
        _teardown()


def test_recap_compiles_grouped_text() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        session_id = client.post("/api/sessions", json={"title": "One"}).json()["id"]
        client.post(f"/api/sessions/{session_id}/logs", json={"text": "Goblins!", "tag": "combat"})

        resp = client.post(f"/api/sessions/{session_id}/recap", json={"tags": ["combat"]})
        assert resp.status_code == 200
        assert "## Combat" in resp.json()["text"]
        assert "Goblins!" in resp.json()["text"]
    finally:
        _teardown()
