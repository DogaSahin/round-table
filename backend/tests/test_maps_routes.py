# backend/tests/test_maps_routes.py
from __future__ import annotations

import io
import queue

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.campaigns import get_active_campaign
from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.core.realtime.broadcast import get_state
from app.engine.maps import snap_to_grid
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


def _png_bytes(size: tuple[int, int] = (10, 10)) -> bytes:
    image = Image.new("RGB", size, color=(120, 60, 200))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_create_list_and_detail_roundtrip() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        create_resp = client.post("/api/maps", json={"name": "Dungeon"})
        assert create_resp.status_code == 200
        body = create_resp.json()
        map_id = body["id"]
        assert body["name"] == "Dungeon"
        assert body["is_active"] is False
        assert body["tokens"] == []
        assert body["fog"] == []

        list_resp = client.get("/api/maps")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1
        assert list_resp.json()[0]["id"] == map_id

        detail_resp = client.get(f"/api/maps/{map_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["name"] == "Dungeon"
    finally:
        _teardown()


def test_patch_updates_grid_settings_without_touching_name_or_tokens() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        map_id = client.post("/api/maps", json={"name": "Original"}).json()["id"]
        client.post(f"/api/maps/{map_id}/tokens", json={"name": "Goblin"})

        resp = client.patch(
            f"/api/maps/{map_id}",
            json={"grid_size_px": 50, "grid_offset_x": 5, "diagonal_rule": "manhattan"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Original"
        assert body["grid_size_px"] == 50
        assert body["grid_offset_x"] == 5
        assert body["diagonal_rule"] == "manhattan"
        assert len(body["tokens"]) == 1
        assert body["tokens"][0]["name"] == "Goblin"
    finally:
        _teardown()


def test_delete_map_returns_204_and_cascades_tokens_and_fog() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        map_id = client.post("/api/maps", json={"name": "Doomed"}).json()["id"]
        client.post(f"/api/maps/{map_id}/tokens", json={"name": "Goblin"})
        client.post(f"/api/maps/{map_id}/fog", json={"op": "hide", "geom": {"type": "rect"}})

        resp = client.delete(f"/api/maps/{map_id}")
        assert resp.status_code == 204

        assert client.get("/api/maps").json() == []
        assert client.get(f"/api/maps/{map_id}").status_code == 404
    finally:
        _teardown()


def test_create_token_then_patch_roundtrips_through_detail() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        map_id = client.post("/api/maps", json={"name": "Map"}).json()["id"]
        token_resp = client.post(
            f"/api/maps/{map_id}/tokens", json={"name": "Goblin", "color": "#ff0000"}
        )
        assert token_resp.status_code == 200
        token_id = token_resp.json()["id"]

        patch_resp = client.patch(
            f"/api/maps/tokens/{token_id}",
            json={
                "name": "Renamed Goblin",
                "size_squares": 2,
                "color": "#00ff00",
                "visible_to_players": False,
            },
        )
        assert patch_resp.status_code == 200
        body = patch_resp.json()
        assert body["name"] == "Renamed Goblin"
        assert body["size_squares"] == 2
        assert body["color"] == "#00ff00"
        assert body["visible_to_players"] is False

        detail = client.get(f"/api/maps/{map_id}").json()
        assert detail["tokens"][0]["name"] == "Renamed Goblin"
    finally:
        _teardown()


def test_move_token_snap_false_persists_raw_and_snap_true_persists_snapped() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        map_id = client.post("/api/maps", json={"name": "Map"}).json()["id"]
        client.patch(
            f"/api/maps/{map_id}",
            json={"grid_size_px": 70, "grid_offset_x": 3, "grid_offset_y": 7},
        )
        token_id = client.post(f"/api/maps/{map_id}/tokens", json={"name": "A"}).json()["id"]

        raw_resp = client.post(
            f"/api/maps/tokens/{token_id}/move", json={"x": 133, "y": 289, "snap": False}
        )
        assert raw_resp.status_code == 200
        assert (raw_resp.json()["x"], raw_resp.json()["y"]) == (133, 289)

        expected_x, expected_y = snap_to_grid(133, 289, 70, 3, 7)
        assert (expected_x, expected_y) != (133, 289)

        snap_resp = client.post(
            f"/api/maps/tokens/{token_id}/move", json={"x": 133, "y": 289, "snap": True}
        )
        assert snap_resp.status_code == 200
        assert (snap_resp.json()["x"], snap_resp.json()["y"]) == (expected_x, expected_y)
    finally:
        _teardown()


def test_fog_reveal_then_reveal_all_then_hide_all() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        map_id = client.post("/api/maps", json={"name": "Map"}).json()["id"]

        resp = client.post(
            f"/api/maps/{map_id}/fog",
            json={"op": "reveal", "geom": {"type": "rect", "x": 0, "y": 0, "w": 10, "h": 10}},
        )
        assert resp.status_code == 200
        assert len(resp.json()["fog"]) == 1
        assert resp.json()["fog"][0]["kind"] == "reveal"

        detail = client.get(f"/api/maps/{map_id}").json()
        assert len(detail["fog"]) == 1

        client.post(
            f"/api/maps/{map_id}/fog",
            json={"op": "hide", "geom": {"type": "rect", "x": 1, "y": 1, "w": 5, "h": 5}},
        )

        reveal_all_resp = client.post(f"/api/maps/{map_id}/fog/reveal-all")
        assert reveal_all_resp.status_code == 200
        assert len(reveal_all_resp.json()["fog"]) == 1
        assert reveal_all_resp.json()["fog"][0]["kind"] == "reveal"

        hide_all_resp = client.post(f"/api/maps/{map_id}/fog/hide-all")
        assert hide_all_resp.status_code == 200
        assert hide_all_resp.json()["fog"] == []
    finally:
        _teardown()


def test_player_view_excludes_hidden_tokens_and_gates_hp_band() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        map_id = client.post("/api/maps", json={"name": "Map"}).json()["id"]

        visible_id = client.post(
            f"/api/maps/{map_id}/tokens",
            json={"name": "Hero", "visible_to_players": True, "layer": "tokens"},
        ).json()["id"]
        client.patch(
            f"/api/maps/tokens/{visible_id}",
            json={"hp_current": 5, "hp_max": 10, "hp_visible_to_players": True},
        )

        hidden_id = client.post(
            f"/api/maps/{map_id}/tokens",
            json={"name": "Sneaky Monster", "visible_to_players": False, "layer": "tokens"},
        ).json()["id"]

        dm_layer_id = client.post(
            f"/api/maps/{map_id}/tokens",
            json={"name": "DM Marker", "visible_to_players": True, "layer": "dm"},
        ).json()["id"]

        no_hp_visible_id = client.post(
            f"/api/maps/{map_id}/tokens",
            json={"name": "Mystery", "visible_to_players": True, "layer": "tokens"},
        ).json()["id"]
        client.patch(
            f"/api/maps/tokens/{no_hp_visible_id}",
            json={"hp_current": 3, "hp_max": 10, "hp_visible_to_players": False},
        )

        resp = client.get(f"/api/maps/{map_id}/player")
        assert resp.status_code == 200
        body = resp.json()
        token_ids = [t["id"] for t in body["tokens"]]
        assert hidden_id not in token_ids
        assert dm_layer_id not in token_ids
        assert visible_id in token_ids
        assert no_hp_visible_id in token_ids

        by_id = {t["id"]: t for t in body["tokens"]}
        assert by_id[visible_id]["hp_band"] is not None
        assert by_id[no_hp_visible_id]["hp_band"] is None
    finally:
        _teardown()


def test_ws_token_move_gating_player_safe_vs_dm_only() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        map_id = client.post("/api/maps", json={"name": "Map"}).json()["id"]
        visible_token_id = client.post(
            f"/api/maps/{map_id}/tokens",
            json={"name": "Hero", "layer": "tokens", "visible_to_players": True},
        ).json()["id"]
        dm_token_id = client.post(
            f"/api/maps/{map_id}/tokens",
            json={"name": "DM Note", "layer": "dm", "visible_to_players": True},
        ).json()["id"]

        with (
            client.websocket_connect(f"/ws?topic=map:{map_id}") as player_ws,
            client.websocket_connect(f"/ws?topic=map:{map_id}:dm") as dm_ws,
        ):
            resp = client.post(f"/api/maps/tokens/{visible_token_id}/move", json={"x": 10, "y": 20})
            assert resp.status_code == 200
            data = player_ws.receive_json()
            assert data == {
                "action": "token.move",
                "map_id": map_id,
                "token_id": visible_token_id,
                "x": 10,
                "y": 20,
            }
            # A player-safe move must never reach the DM-only topic.
            with pytest.raises(queue.Empty):
                dm_ws._send_queue.get(timeout=0.2)

            resp = client.post(f"/api/maps/tokens/{dm_token_id}/move", json={"x": 30, "y": 40})
            assert resp.status_code == 200
            data = dm_ws.receive_json()
            assert data == {
                "action": "token.move",
                "map_id": map_id,
                "token_id": dm_token_id,
                "x": 30,
                "y": 40,
            }
            # A DM-layer move must never reach a player-only subscriber.
            with pytest.raises(queue.Empty):
                player_ws._send_queue.get(timeout=0.2)
    finally:
        _teardown()


def test_activate_updates_broadcast_state() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        map_id = client.post("/api/maps", json={"name": "Map"}).json()["id"]

        resp = client.post(f"/api/maps/{map_id}/activate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

        session = SessionLocal()
        try:
            state = get_state(session, campaign.id)
            assert state.active_map_id == map_id
        finally:
            session.close()
    finally:
        _teardown()


def test_stop_sharing_clears_active_flag_and_broadcast_pointer() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        map_id = client.post("/api/maps", json={"name": "Map"}).json()["id"]
        client.post(f"/api/maps/{map_id}/activate")

        resp = client.post("/api/maps/stop-sharing")
        assert resp.status_code == 204

        detail = client.get(f"/api/maps/{map_id}").json()
        assert detail["is_active"] is False

        session = SessionLocal()
        try:
            state = get_state(session, campaign.id)
            assert state.active_map_id is None
        finally:
            session.close()
    finally:
        _teardown()


def test_upload_map_image_updates_path_and_dimensions() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        map_id = client.post("/api/maps", json={"name": "Map"}).json()["id"]
        data = _png_bytes((40, 30))

        resp = client.post(
            f"/api/maps/{map_id}/image",
            files={"upload": ("battlemap.png", data, "image/png")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["image_path"] is not None
        assert body["image_w"] == 40
        assert body["image_h"] == 30
    finally:
        _teardown()


def test_upload_map_image_rejects_bad_upload_with_validation_envelope() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        map_id = client.post("/api/maps", json={"name": "Map"}).json()["id"]

        resp = client.post(
            f"/api/maps/{map_id}/image",
            files={"upload": ("battlemap.bmp", b"not a real image", "image/bmp")},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "validation_error"
    finally:
        _teardown()


def test_upload_token_image_updates_path() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        map_id = client.post("/api/maps", json={"name": "Map"}).json()["id"]
        token_id = client.post(
            f"/api/maps/{map_id}/tokens", json={"name": "A", "kind": "image"}
        ).json()["id"]
        data = _png_bytes((16, 16))

        resp = client.post(
            f"/api/maps/tokens/{token_id}/image",
            files={"upload": ("token.png", data, "image/png")},
        )
        assert resp.status_code == 200
        assert resp.json()["image_path"] is not None
    finally:
        _teardown()


def test_404_envelope_for_nonexistent_map() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.get("/api/maps/999999")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"
    finally:
        _teardown()


def test_404_envelope_for_nonexistent_token() -> None:
    campaign = _setup_campaign()
    app.dependency_overrides[get_active_campaign] = lambda: campaign
    try:
        client = TestClient(app)
        resp = client.patch("/api/maps/tokens/999999", json={"name": "x"})
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"
    finally:
        _teardown()
