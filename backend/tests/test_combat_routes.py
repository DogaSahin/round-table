# backend/tests/test_combat_routes.py
from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.campaigns import get_active_campaign
from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.core.realtime.broadcast import get_state
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
        create_resp = client.post("/api/combat", json={"name": "Goblin Ambush"})
        assert create_resp.status_code == 200
        body = create_resp.json()
        encounter_id = body["id"]
        assert body["name"] == "Goblin Ambush"
        assert body["round"] == 1
        assert body["is_active"] is False
        assert body["active_combatant_id"] is None
        assert body["combatants"] == []

        list_resp = client.get("/api/combat")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1
        assert list_resp.json()[0]["id"] == encounter_id

        detail_resp = client.get(f"/api/combat/{encounter_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["name"] == "Goblin Ambush"
    finally:
        _teardown()


def test_patch_rename_never_changes_anything_else() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Original"}).json()["id"]
        client.post(
            f"/api/combat/{encounter_id}/combatants",
            json={"name": "Guard", "initiative": 3, "hp_current": 8, "hp_max": 8},
        )

        resp = client.patch(f"/api/combat/{encounter_id}", json={"name": "Renamed"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Renamed"
        assert body["round"] == 1
        assert body["is_active"] is False
        assert len(body["combatants"]) == 1
        assert body["combatants"][0]["name"] == "Guard"
    finally:
        _teardown()


def test_delete_encounter_returns_204_and_cascades_combatants() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Doomed"}).json()["id"]
        client.post(f"/api/combat/{encounter_id}/combatants", json={"name": "Goblin"})

        resp = client.delete(f"/api/combat/{encounter_id}")
        assert resp.status_code == 204

        assert client.get("/api/combat").json() == []
        assert client.get(f"/api/combat/{encounter_id}").status_code == 404
    finally:
        _teardown()


def test_combatant_damage_and_heal_clamp_at_zero_and_max() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Fight"}).json()["id"]
        combatant_resp = client.post(
            f"/api/combat/{encounter_id}/combatants",
            json={"name": "Fighter", "hp_current": 10, "hp_max": 10},
        )
        assert combatant_resp.status_code == 200
        combatant_id = combatant_resp.json()["id"]

        damage_resp = client.post(
            f"/api/combat/combatants/{combatant_id}/damage", json={"amount": 25}
        )
        assert damage_resp.status_code == 200
        assert damage_resp.json()["hp_current"] == 0

        heal_resp = client.post(f"/api/combat/combatants/{combatant_id}/heal", json={"amount": 100})
        assert heal_resp.status_code == 200
        assert heal_resp.json()["hp_current"] == 10
    finally:
        _teardown()


def test_condition_add_then_remove_roundtrips_through_detail() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Fight"}).json()["id"]
        combatant_id = client.post(
            f"/api/combat/{encounter_id}/combatants", json={"name": "Fighter"}
        ).json()["id"]

        add_resp = client.post(
            f"/api/combat/combatants/{combatant_id}/condition",
            json={"name": "prone", "op": "add"},
        )
        assert add_resp.status_code == 200
        assert add_resp.json()["conditions"] == ["prone"]

        detail = client.get(f"/api/combat/{encounter_id}").json()
        assert detail["combatants"][0]["conditions"] == ["prone"]

        remove_resp = client.post(
            f"/api/combat/combatants/{combatant_id}/condition",
            json={"name": "prone", "op": "remove"},
        )
        assert remove_resp.status_code == 200
        assert remove_resp.json()["conditions"] == []

        detail = client.get(f"/api/combat/{encounter_id}").json()
        assert detail["combatants"][0]["conditions"] == []
    finally:
        _teardown()


def test_next_turn_advances_and_wraps_round_over_full_cycle() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Fight"}).json()["id"]
        c1 = client.post(f"/api/combat/{encounter_id}/combatants", json={"name": "A"}).json()["id"]
        c2 = client.post(f"/api/combat/{encounter_id}/combatants", json={"name": "B"}).json()["id"]
        c3 = client.post(f"/api/combat/{encounter_id}/combatants", json={"name": "C"}).json()["id"]

        resp = client.post(f"/api/combat/{encounter_id}/next-turn")
        assert resp.status_code == 200
        assert resp.json()["active_combatant_id"] == c1
        assert resp.json()["round"] == 1

        resp = client.post(f"/api/combat/{encounter_id}/next-turn")
        assert resp.json()["active_combatant_id"] == c2
        assert resp.json()["round"] == 1

        resp = client.post(f"/api/combat/{encounter_id}/next-turn")
        assert resp.json()["active_combatant_id"] == c3
        assert resp.json()["round"] == 1

        # Wrapping past the last combatant advances the round back to c1.
        resp = client.post(f"/api/combat/{encounter_id}/next-turn")
        assert resp.json()["active_combatant_id"] == c1
        assert resp.json()["round"] == 2
    finally:
        _teardown()


def test_player_view_hides_hp_for_invisible_and_reveals_for_visible() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Fight"}).json()["id"]
        client.post(
            f"/api/combat/{encounter_id}/combatants",
            json={
                "name": "Hidden Monster",
                "hp_current": 7,
                "hp_max": 20,
                "visible_to_players": False,
            },
        )
        client.post(
            f"/api/combat/{encounter_id}/combatants",
            json={
                "name": "Hero",
                "hp_current": 5,
                "hp_max": 10,
                "is_pc": True,
                "visible_to_players": True,
            },
        )

        resp = client.get(f"/api/combat/{encounter_id}/player")
        assert resp.status_code == 200
        body = resp.json()
        assert body["combatants"][0]["hp_current"] is None
        assert body["combatants"][0]["hp_max"] is None
        assert body["combatants"][1]["hp_current"] == 5
        assert body["combatants"][1]["hp_max"] == 10

        for combatant in body["combatants"]:
            assert "ac" not in combatant
            assert "conditions" not in combatant
            assert "concentration" not in combatant
            assert "band" in combatant
    finally:
        _teardown()


def test_ws_receives_combat_changed_on_damage() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Fight"}).json()["id"]
        combatant_id = client.post(
            f"/api/combat/{encounter_id}/combatants",
            json={"name": "Fighter", "hp_current": 10, "hp_max": 10},
        ).json()["id"]

        with client.websocket_connect(f"/ws?topic=combat:{encounter_id}") as ws:
            damage_resp = client.post(
                f"/api/combat/combatants/{combatant_id}/damage", json={"amount": 3}
            )
            assert damage_resp.status_code == 200
            data = ws.receive_json()
            assert data == {"action": "combat_changed", "encounter_id": encounter_id}
    finally:
        _teardown()


def test_activate_updates_broadcast_state() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Fight"}).json()["id"]

        resp = client.post(f"/api/combat/{encounter_id}/activate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

        session = SessionLocal()
        try:
            state = get_state(session, campaign.id)
            assert state.active_encounter_id == encounter_id
        finally:
            session.close()
    finally:
        _teardown()


def test_activate_broadcasts_on_core_broadcast_topic() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Fight"}).json()["id"]

        with client.websocket_connect("/ws?topic=broadcast") as ws:
            resp = client.post(f"/api/combat/{encounter_id}/activate")
            assert resp.status_code == 200
            data = ws.receive_json()
            assert data == {"action": "broadcast_changed", "campaign_id": campaign.id}
    finally:
        _teardown()


def test_404_envelope_for_nonexistent_encounter() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.get("/api/combat/999999")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"
    finally:
        _teardown()


def test_404_envelope_for_nonexistent_combatant() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.post("/api/combat/combatants/999999/damage", json={"amount": 1})
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"
    finally:
        _teardown()


def test_update_combatant_partial_fields() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Fight"}).json()["id"]
        combatant_id = client.post(
            f"/api/combat/{encounter_id}/combatants",
            json={"name": "Original", "initiative": 5},
        ).json()["id"]

        resp = client.patch(f"/api/combat/combatants/{combatant_id}", json={"is_pc": True})
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Original"
        assert body["initiative"] == 5
        assert body["is_pc"] is True
    finally:
        _teardown()


def test_delete_combatant_returns_204_and_reassigns_active_marker() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Fight"}).json()["id"]
        c1 = client.post(f"/api/combat/{encounter_id}/combatants", json={"name": "A"}).json()["id"]
        c2 = client.post(f"/api/combat/{encounter_id}/combatants", json={"name": "B"}).json()["id"]

        client.post(f"/api/combat/{encounter_id}/next-turn")  # active -> c1

        resp = client.delete(f"/api/combat/combatants/{c1}")
        assert resp.status_code == 204

        detail = client.get(f"/api/combat/{encounter_id}").json()
        assert detail["active_combatant_id"] == c2
        assert len(detail["combatants"]) == 1
    finally:
        _teardown()


def test_set_ac_and_toggle_concentration() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Fight"}).json()["id"]
        combatant_id = client.post(
            f"/api/combat/{encounter_id}/combatants", json={"name": "Fighter"}
        ).json()["id"]

        ac_resp = client.post(f"/api/combat/combatants/{combatant_id}/ac", json={"ac": 16})
        assert ac_resp.status_code == 200
        assert ac_resp.json()["ac"] == 16

        conc_resp = client.post(f"/api/combat/combatants/{combatant_id}/concentration")
        assert conc_resp.status_code == 200
        assert conc_resp.json()["concentration"] is True

        conc_resp2 = client.post(f"/api/combat/combatants/{combatant_id}/concentration")
        assert conc_resp2.status_code == 200
        assert conc_resp2.json()["concentration"] is False
    finally:
        _teardown()


def test_reorder_and_sort_by_initiative() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        encounter_id = client.post("/api/combat", json={"name": "Fight"}).json()["id"]
        c1 = client.post(
            f"/api/combat/{encounter_id}/combatants", json={"name": "A", "initiative": 1}
        ).json()["id"]
        c2 = client.post(
            f"/api/combat/{encounter_id}/combatants", json={"name": "B", "initiative": 20}
        ).json()["id"]
        c3 = client.post(
            f"/api/combat/{encounter_id}/combatants", json={"name": "C", "initiative": 10}
        ).json()["id"]

        sort_resp = client.post(f"/api/combat/{encounter_id}/sort")
        assert sort_resp.status_code == 200
        ordered = sorted(sort_resp.json()["combatants"], key=lambda c: c["sort_order"])
        assert [c["id"] for c in ordered] == [c2, c3, c1]

        reorder_resp = client.post(
            f"/api/combat/{encounter_id}/reorder", json={"order": [c1, c2, c3]}
        )
        assert reorder_resp.status_code == 200
        ordered = sorted(reorder_resp.json()["combatants"], key=lambda c: c["sort_order"])
        assert [c["id"] for c in ordered] == [c1, c2, c3]
    finally:
        _teardown()
