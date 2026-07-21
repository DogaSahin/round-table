# backend/tests/test_maps_service.py
from __future__ import annotations

import io
import json

from PIL import Image

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.engine.maps import snap_to_grid
from app.modules.maps import service
from app.modules.maps.models import FogRegion, Map, Token


def _make_campaign(db) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def _png_bytes(size: tuple[int, int] = (12, 8)) -> bytes:
    image = Image.new("RGB", size, color=(50, 100, 150))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_create_and_delete_map_cascades_tokens_and_fog() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_row = service.create_map(db, campaign.id, "Dungeon Level 1")
        token = service.create_token(
            db,
            map_row,
            name="Goblin",
            layer="tokens",
            kind="disc",
            size_squares=1,
            color="#ff0000",
            is_pc=False,
            visible_to_players=True,
            npc_id=None,
            combatant_id=None,
        )
        service.add_fog_op(db, map_row, "hide", {"type": "rect", "x": 0, "y": 0})
        token_id = token.id
        map_id = map_row.id

        service.delete_map(db, map_row)

        assert db.get(Map, map_id) is None
        assert db.query(Token).filter_by(id=token_id).first() is None
        assert db.query(Token).filter_by(map_id=map_id).count() == 0
        assert db.query(FogRegion).filter_by(map_id=map_id).count() == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_owned_map_scoped_to_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        map_row = service.create_map(db, c1.id, "Map")

        assert service.owned_map(db, map_row.id, c1.id) is not None
        assert service.owned_map(db, map_row.id, c2.id) is None
        assert service.owned_map(db, 999_999, c1.id) is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_owned_token_traverses_map_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        map_row = service.create_map(db, c1.id, "Map")
        token = service.create_token(
            db,
            map_row,
            name="Goblin",
            layer="tokens",
            kind="disc",
            size_squares=1,
            color="#ff0000",
            is_pc=False,
            visible_to_players=True,
            npc_id=None,
            combatant_id=None,
        )

        assert service.owned_token(db, token.id, c1.id) is not None
        assert service.owned_token(db, token.id, c2.id) is None
        assert service.owned_token(db, 999_999, c1.id) is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_set_active_map_isolated_per_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        m1a = service.create_map(db, c1.id, "M1A")
        m1b = service.create_map(db, c1.id, "M1B")
        m2a = service.create_map(db, c2.id, "M2A")

        service.set_active_map(db, c1.id, m1a)
        db.refresh(m1a)
        db.refresh(m1b)
        db.refresh(m2a)
        assert m1a.is_active is True
        assert m1b.is_active is False
        assert m2a.is_active is False

        # Activating a map in campaign 2 must not touch campaign 1's rows.
        service.set_active_map(db, c2.id, m2a)
        db.refresh(m1a)
        db.refresh(m2a)
        assert m1a.is_active is True
        assert m2a.is_active is True

        # Switching the active map within campaign 1 clears the old one.
        service.set_active_map(db, c1.id, m1b)
        db.refresh(m1a)
        db.refresh(m1b)
        db.refresh(m2a)
        assert m1a.is_active is False
        assert m1b.is_active is True
        assert m2a.is_active is True
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_stop_sharing_isolated_per_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        m1 = service.create_map(db, c1.id, "M1")
        m2 = service.create_map(db, c2.id, "M2")
        service.set_active_map(db, c1.id, m1)
        service.set_active_map(db, c2.id, m2)

        service.stop_sharing(db, c1.id)
        db.refresh(m1)
        db.refresh(m2)

        assert m1.is_active is False
        assert m2.is_active is True
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_token_places_at_map_grid_origin_not_hardcoded() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_a = service.create_map(db, campaign.id, "Map A")
        map_a.grid_size_px = 50
        db.commit()
        map_b = service.create_map(db, campaign.id, "Map B")
        map_b.grid_size_px = 120
        db.commit()

        token_a = service.create_token(
            db,
            map_a,
            name="A",
            layer="tokens",
            kind="disc",
            size_squares=1,
            color="#fff",
            is_pc=False,
            visible_to_players=True,
            npc_id=None,
            combatant_id=None,
        )
        token_b = service.create_token(
            db,
            map_b,
            name="B",
            layer="tokens",
            kind="disc",
            size_squares=1,
            color="#fff",
            is_pc=False,
            visible_to_players=True,
            npc_id=None,
            combatant_id=None,
        )

        assert (token_a.x, token_a.y) == (50, 50)
        assert (token_b.x, token_b.y) == (120, 120)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_move_token_with_snap_uses_server_side_snap_not_client_value() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_row = service.create_map(db, campaign.id, "Map")
        map_row.grid_size_px = 70
        map_row.grid_offset_x = 3
        map_row.grid_offset_y = 7
        db.commit()
        token = service.create_token(
            db,
            map_row,
            name="A",
            layer="tokens",
            kind="disc",
            size_squares=1,
            color="#fff",
            is_pc=False,
            visible_to_players=True,
            npc_id=None,
            combatant_id=None,
        )

        # Intentionally unsnapped client coordinates.
        raw_x, raw_y = 133, 289
        expected_x, expected_y = snap_to_grid(raw_x, raw_y, 70, 3, 7)
        assert (expected_x, expected_y) != (raw_x, raw_y)

        moved = service.move_token(db, token, raw_x, raw_y, snap=True)

        assert (moved.x, moved.y) == (expected_x, expected_y)
        assert (moved.x, moved.y) != (raw_x, raw_y)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_move_token_without_snap_keeps_raw_value() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_row = service.create_map(db, campaign.id, "Map")
        token = service.create_token(
            db,
            map_row,
            name="A",
            layer="tokens",
            kind="disc",
            size_squares=1,
            color="#fff",
            is_pc=False,
            visible_to_players=True,
            npc_id=None,
            combatant_id=None,
        )

        moved = service.move_token(db, token, 133, 289, snap=False)

        assert (moved.x, moved.y) == (133, 289)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_update_token_applies_non_none_fields_including_falsy_values() -> None:
    """Proves update_token actually writes non-None values (not just skips None),
    and specifically that falsy-but-intentional values (is_pc=False,
    visible_to_players=False, hp_current=0) are applied rather than dropped —
    a regression to `if value:` instead of `if value is not None:` would silently
    ignore exactly these and still pass a test that only ever calls it with None."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_row = service.create_map(db, campaign.id, "Map")
        token = service.create_token(
            db,
            map_row,
            name="A",
            layer="tokens",
            kind="disc",
            size_squares=1,
            color="#fff",
            is_pc=True,
            visible_to_players=True,
            npc_id=None,
            combatant_id=None,
        )
        token.hp_current = 5
        token.hp_max = 10
        token.hp_visible_to_players = True
        db.commit()

        updated = service.update_token(
            db,
            token,
            name="Renamed",
            layer="dm",
            size_squares=2,
            color="#000000",
            is_pc=False,
            visible_to_players=False,
            npc_id=7,
            combatant_id=9,
            hp_current=0,
            hp_max=1,
            hp_visible_to_players=False,
            status_markers=None,
        )

        assert updated.name == "Renamed"
        assert updated.layer == "dm"
        assert updated.size_squares == 2
        assert updated.color == "#000000"
        assert updated.is_pc is False
        assert updated.visible_to_players is False
        assert updated.npc_id == 7
        assert updated.combatant_id == 9
        assert updated.hp_current == 0
        assert updated.hp_max == 1
        assert updated.hp_visible_to_players is False
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_status_markers_roundtrip_via_update_token() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_row = service.create_map(db, campaign.id, "Map")
        token = service.create_token(
            db,
            map_row,
            name="A",
            layer="tokens",
            kind="disc",
            size_squares=1,
            color="#fff",
            is_pc=False,
            visible_to_players=True,
            npc_id=None,
            combatant_id=None,
        )

        service.update_token(
            db,
            token,
            name=None,
            layer=None,
            size_squares=None,
            color=None,
            is_pc=None,
            visible_to_players=None,
            npc_id=None,
            combatant_id=None,
            hp_current=None,
            hp_max=None,
            hp_visible_to_players=None,
            status_markers=["prone", "stunned"],
        )

        assert service.get_status_markers(token) == ["prone", "stunned"]
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_get_status_markers_never_raises_on_malformed_json() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_row = service.create_map(db, campaign.id, "Map")
        token = service.create_token(
            db,
            map_row,
            name="A",
            layer="tokens",
            kind="disc",
            size_squares=1,
            color="#fff",
            is_pc=False,
            visible_to_players=True,
            npc_id=None,
            combatant_id=None,
        )

        token.status_markers_json = "not valid json {{{"
        assert service.get_status_markers(token) == []

        token.status_markers_json = json.dumps({"a": 1})
        assert service.get_status_markers(token) == []

        token.status_markers_json = json.dumps("just a string")
        assert service.get_status_markers(token) == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_add_fog_op_orders_by_max_existing_index() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_row = service.create_map(db, campaign.id, "Map")

        service.add_fog_op(db, map_row, "hide", {"type": "rect", "x": 0})
        db.refresh(map_row)
        service.add_fog_op(db, map_row, "hide", {"type": "rect", "x": 1})
        db.refresh(map_row)
        service.add_fog_op(db, map_row, "reveal", {"type": "rect", "x": 2})
        db.refresh(map_row)

        rows = (
            db.query(FogRegion).filter_by(map_id=map_row.id).order_by(FogRegion.order_index).all()
        )
        assert [r.order_index for r in rows] == [0, 1, 2]
        assert rows[-1].kind == "reveal"
        assert json.loads(rows[-1].geometry_json) == {"type": "rect", "x": 2}
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_fog_reveal_all_collapses_to_single_row() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_row = service.create_map(db, campaign.id, "Map")
        service.add_fog_op(db, map_row, "hide", {"type": "rect", "x": 0})
        db.refresh(map_row)
        service.add_fog_op(db, map_row, "hide", {"type": "rect", "x": 1})
        db.refresh(map_row)
        service.add_fog_op(db, map_row, "reveal", {"type": "rect", "x": 2})
        db.refresh(map_row)
        assert db.query(FogRegion).filter_by(map_id=map_row.id).count() == 3

        service.fog_reveal_all(db, map_row)

        rows = db.query(FogRegion).filter_by(map_id=map_row.id).all()
        assert len(rows) == 1
        assert rows[0].order_index == 0
        assert rows[0].kind == "reveal"
        assert json.loads(rows[0].geometry_json) == {"type": "all"}
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_fog_hide_all_removes_all_rows() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_row = service.create_map(db, campaign.id, "Map")
        service.add_fog_op(db, map_row, "reveal", {"type": "rect", "x": 0})
        db.refresh(map_row)
        service.add_fog_op(db, map_row, "reveal", {"type": "rect", "x": 1})
        db.refresh(map_row)
        assert db.query(FogRegion).filter_by(map_id=map_row.id).count() == 2

        service.fog_hide_all(db, map_row)

        assert db.query(FogRegion).filter_by(map_id=map_row.id).count() == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_player_visible_tokens_filters_hidden_and_dm_layer() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_row = service.create_map(db, campaign.id, "Map")

        visible = service.create_token(
            db,
            map_row,
            name="Visible PC",
            layer="tokens",
            kind="disc",
            size_squares=1,
            color="#fff",
            is_pc=True,
            visible_to_players=True,
            npc_id=None,
            combatant_id=None,
        )
        service.create_token(
            db,
            map_row,
            name="Hidden Monster",
            layer="tokens",
            kind="disc",
            size_squares=1,
            color="#fff",
            is_pc=False,
            visible_to_players=False,
            npc_id=None,
            combatant_id=None,
        )
        service.create_token(
            db,
            map_row,
            name="DM Marker",
            layer="dm",
            kind="disc",
            size_squares=1,
            color="#fff",
            is_pc=False,
            visible_to_players=True,
            npc_id=None,
            combatant_id=None,
        )
        db.refresh(map_row)

        result = service.player_visible_tokens(map_row)

        assert [t.id for t in result] == [visible.id]
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_set_map_image_persists_path_and_dimensions(tmp_path) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_row = service.create_map(db, campaign.id, "Map")
        data = _png_bytes((40, 30))

        updated = service.set_map_image(db, map_row, data, "battlemap.png", tmp_path)

        assert updated.image_path is not None
        assert updated.image_w == 40
        assert updated.image_h == 30
        assert (tmp_path / updated.image_path).is_file()
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_set_token_image_persists_path_only(tmp_path) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        map_row = service.create_map(db, campaign.id, "Map")
        token = service.create_token(
            db,
            map_row,
            name="A",
            layer="tokens",
            kind="image",
            size_squares=1,
            color="#fff",
            is_pc=False,
            visible_to_players=True,
            npc_id=None,
            combatant_id=None,
        )
        data = _png_bytes((16, 16))

        updated = service.set_token_image(db, token, data, "token.png", tmp_path)

        assert updated.image_path is not None
        assert (tmp_path / updated.image_path).is_file()
        assert not hasattr(updated, "image_w")
        assert not hasattr(updated, "image_h")
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
