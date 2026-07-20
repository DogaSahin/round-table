# backend/tests/test_wiki_routes.py
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
        create_resp = client.post(
            "/api/wiki", json={"title": "The Ashen Keep", "body_md": "A crumbling fortress."}
        )
        assert create_resp.status_code == 200
        body = create_resp.json()
        assert body["slug"] == "the-ashen-keep"
        assert "<p>A crumbling fortress.</p>" in body["body_html"]
        assert body["player_visible"] is False

        list_resp = client.get("/api/wiki")
        assert len(list_resp.json()) == 1

        detail_resp = client.get(f"/api/wiki/{body['slug']}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["title"] == "The Ashen Keep"
    finally:
        _teardown()


def test_create_rejects_empty_title_with_validation_envelope() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.post("/api/wiki", json={"title": ""})
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "validation_error"
    finally:
        _teardown()


def test_detail_for_nonexistent_page_returns_not_found_envelope() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.get("/api/wiki/does-not-exist")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"
    finally:
        _teardown()


def test_update_partial_fields_never_changes_slug() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        slug = client.post("/api/wiki", json={"title": "Original"}).json()["slug"]

        resp = client.patch(f"/api/wiki/{slug}", json={"title": "Renamed Completely"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Renamed Completely"
        assert resp.json()["slug"] == slug
    finally:
        _teardown()


def test_delete_page_returns_204_and_removes_it() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        slug = client.post("/api/wiki", json={"title": "Doomed"}).json()["slug"]

        resp = client.delete(f"/api/wiki/{slug}")
        assert resp.status_code == 204
        assert client.get("/api/wiki").json() == []
    finally:
        _teardown()


def test_search_matches_title_and_body() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        client.post("/api/wiki", json={"title": "The Ashen Keep", "body_md": "A ruin."})
        client.post("/api/wiki", json={"title": "Unrelated Page", "body_md": "Nothing here."})

        resp = client.get("/api/wiki/search", params={"q": "Ashen"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "The Ashen Keep"
    finally:
        _teardown()


def test_wikilinks_resolve_to_existing_pages_and_appear_in_backlinks() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        target_slug = client.post("/api/wiki", json={"title": "Old Man Grigg"}).json()["slug"]
        source_resp = client.post(
            "/api/wiki",
            json={"title": "The Ashen Keep", "body_md": "See [[Old Man Grigg]]."},
        )
        assert source_resp.status_code == 200
        links = source_resp.json()["links"]
        assert len(links) == 1
        assert links[0]["resolved"] is True
        assert links[0]["target_title"] == "Old Man Grigg"

        target_detail = client.get(f"/api/wiki/{target_slug}").json()
        assert len(target_detail["backlinks"]) == 1
        assert target_detail["backlinks"][0]["title"] == "The Ashen Keep"
    finally:
        _teardown()


def test_add_and_remove_tag() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        slug = client.post("/api/wiki", json={"title": "Foo"}).json()["slug"]

        tag_resp = client.post(f"/api/wiki/{slug}/tags", json={"name": "location"})
        assert tag_resp.status_code == 200
        tag_id = tag_resp.json()["id"]

        detail = client.get(f"/api/wiki/{slug}").json()
        assert [t["name"] for t in detail["tags"]] == ["location"]

        delete_resp = client.delete(f"/api/wiki/{slug}/tags/{tag_id}")
        assert delete_resp.status_code == 204
        assert client.get(f"/api/wiki/{slug}").json()["tags"] == []
    finally:
        _teardown()
