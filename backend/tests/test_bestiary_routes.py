from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.campaigns import get_active_campaign
from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.main import app


def _statblock_payload(creature_type: str = "beast", challenge_rating: float = 0.25) -> dict:
    return {
        "size": "Small",
        "creature_type": creature_type,
        "alignment": "unaligned",
        "armor_class": 12,
        "hit_points": 7,
        "hit_dice": "2d6",
        "speed": {"walk": 30},
        "ability_scores": {
            "strength": 8,
            "dexterity": 15,
            "constitution": 11,
            "intelligence": 2,
            "wisdom": 10,
            "charisma": 4,
        },
        "challenge_rating": challenge_rating,
        "experience_points": 50,
    }


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
            "/api/bestiary", json={"name": "Giant Rat", "statblock": _statblock_payload()}
        )
        assert create_resp.status_code == 200
        body = create_resp.json()
        assert body["slug"] == "giant-rat"
        assert body["statblock"]["creature_type"] == "beast"
        assert body["is_favorite"] is False
        monster_id = body["id"]

        list_resp = client.get("/api/bestiary")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1
        assert list_resp.json()[0]["creature_type"] == "beast"

        detail_resp = client.get(f"/api/bestiary/{monster_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["name"] == "Giant Rat"
    finally:
        _teardown()


def test_create_rejects_invalid_nested_statblock_with_validation_envelope() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.post(
            "/api/bestiary",
            json={"name": "Giant Rat", "statblock": _statblock_payload(challenge_rating=0.9)},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "validation_error"
    finally:
        _teardown()


def test_detail_for_nonexistent_monster_returns_not_found_envelope() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.get("/api/bestiary/999999")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"
    finally:
        _teardown()


def test_monster_scoped_to_campaign() -> None:
    campaign_a = _setup_campaign()
    session = SessionLocal()
    campaign_b = Campaign(name="Other Campaign", active=False)
    session.add(campaign_b)
    session.commit()
    session.refresh(campaign_b)
    session.close()

    app.dependency_overrides[get_active_campaign] = lambda: campaign_a
    try:
        client = TestClient(app)
        monster_id = client.post(
            "/api/bestiary", json={"name": "Giant Rat", "statblock": _statblock_payload()}
        ).json()["id"]

        app.dependency_overrides[get_active_campaign] = lambda: campaign_b
        resp = client.get(f"/api/bestiary/{monster_id}")
        assert resp.status_code == 404
    finally:
        _teardown()


def test_update_partial_fields_preserves_slug() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        create_resp = client.post(
            "/api/bestiary", json={"name": "Goblin", "statblock": _statblock_payload()}
        )
        monster_id = create_resp.json()["id"]
        original_slug = create_resp.json()["slug"]

        resp = client.patch(f"/api/bestiary/{monster_id}", json={"name": "Goblin Boss"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Goblin Boss"
        assert resp.json()["slug"] == original_slug
    finally:
        _teardown()


def test_delete_monster_returns_204_and_removes_it() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        monster_id = client.post(
            "/api/bestiary", json={"name": "Doomed", "statblock": _statblock_payload()}
        ).json()["id"]

        resp = client.delete(f"/api/bestiary/{monster_id}")
        assert resp.status_code == 204
        assert client.get("/api/bestiary").json() == []
    finally:
        _teardown()


def test_favorite_toggle_endpoints() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        monster_id = client.post(
            "/api/bestiary", json={"name": "Goblin", "statblock": _statblock_payload()}
        ).json()["id"]

        fav_resp = client.post(f"/api/bestiary/{monster_id}/favorite")
        assert fav_resp.status_code == 200
        assert fav_resp.json()["is_favorite"] is True

        unfav_resp = client.delete(f"/api/bestiary/{monster_id}/favorite")
        assert unfav_resp.status_code == 200
        assert unfav_resp.json()["is_favorite"] is False
    finally:
        _teardown()


def test_list_filters_by_search_type_cr_range_and_favorites_only() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        client.post(
            "/api/bestiary",
            json={
                "name": "Giant Rat",
                "statblock": _statblock_payload(creature_type="beast", challenge_rating=0.125),
            },
        )
        client.post(
            "/api/bestiary",
            json={
                "name": "Owlbear",
                "statblock": _statblock_payload(creature_type="monstrosity", challenge_rating=3.0),
            },
        )

        by_search = client.get("/api/bestiary", params={"search": "owl"})
        assert [m["name"] for m in by_search.json()] == ["Owlbear"]

        by_type = client.get("/api/bestiary", params={"type": "beast"})
        assert [m["name"] for m in by_type.json()] == ["Giant Rat"]

        by_cr = client.get("/api/bestiary", params={"cr_min": 1.0, "cr_max": 5.0})
        assert [m["name"] for m in by_cr.json()] == ["Owlbear"]

        rat_id = client.get("/api/bestiary", params={"search": "rat"}).json()[0]["id"]
        client.post(f"/api/bestiary/{rat_id}/favorite")
        by_favorite = client.get("/api/bestiary", params={"favorites_only": True})
        assert [m["name"] for m in by_favorite.json()] == ["Giant Rat"]
    finally:
        _teardown()


def test_list_sort_options() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        client.post(
            "/api/bestiary",
            json={"name": "Zebra Swarm", "statblock": _statblock_payload(challenge_rating=2.0)},
        )
        client.post(
            "/api/bestiary",
            json={"name": "Ant Swarm", "statblock": _statblock_payload(challenge_rating=0.25)},
        )

        by_name = client.get("/api/bestiary", params={"sort": "name"})
        by_cr = client.get("/api/bestiary", params={"sort": "cr"})

        assert [m["name"] for m in by_name.json()] == ["Ant Swarm", "Zebra Swarm"]
        assert [m["name"] for m in by_cr.json()] == ["Ant Swarm", "Zebra Swarm"]
    finally:
        _teardown()
