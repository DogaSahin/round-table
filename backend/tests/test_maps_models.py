from __future__ import annotations

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.maps.models import FogRegion, Map, Token


def _make_campaign(session) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def test_map_defaults() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        map_row = Map(campaign_id=campaign.id, name="Test Map")
        session.add(map_row)
        session.commit()
        session.refresh(map_row)

        assert map_row.grid_size_px == 70
        assert map_row.grid_offset_x == 0
        assert map_row.grid_offset_y == 0
        assert map_row.grid_visible is True
        assert map_row.feet_per_square == 5
        assert map_row.diagonal_rule == "chebyshev"
        assert map_row.is_active is False
        assert map_row.image_path is None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_token_defaults() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        map_row = Map(campaign_id=campaign.id, name="Test Map")
        session.add(map_row)
        session.commit()
        session.refresh(map_row)

        token = Token(map_id=map_row.id)
        session.add(token)
        session.commit()
        session.refresh(token)

        assert token.layer == "tokens"
        assert token.kind == "disc"
        assert token.x == 0
        assert token.y == 0
        assert token.size_squares == 1
        assert token.color == "#888888"
        assert token.image_path is None
        assert token.name == ""
        assert token.hp_current is None
        assert token.hp_max is None
        assert token.hp_visible_to_players is False
        assert token.visible_to_players is True
        assert token.status_markers_json == "[]"
        assert token.is_pc is False
        assert token.npc_id is None
        assert token.combatant_id is None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_fog_region_defaults() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        map_row = Map(campaign_id=campaign.id, name="Test Map")
        session.add(map_row)
        session.commit()
        session.refresh(map_row)

        fog = FogRegion(map_id=map_row.id, kind="reveal", geometry_json='{"type": "rect"}')
        session.add(fog)
        session.commit()
        session.refresh(fog)

        assert fog.order_index == 0
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_map_cascade_delete_tokens_and_fog_regions() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        map_row = Map(campaign_id=campaign.id, name="Test Map")
        session.add(map_row)
        session.commit()
        session.refresh(map_row)

        token = Token(map_id=map_row.id, name="Test Token")
        fog = FogRegion(map_id=map_row.id, kind="reveal", geometry_json='{"type": "rect"}')
        session.add(token)
        session.add(fog)
        session.commit()
        session.refresh(token)
        session.refresh(fog)

        token_id = token.id
        fog_id = fog.id

        # Delete the map
        session.delete(map_row)
        session.commit()

        # Verify token and fog are deleted
        found_token = session.query(Token).filter_by(id=token_id).first()
        found_fog = session.query(FogRegion).filter_by(id=fog_id).first()

        assert found_token is None
        assert found_fog is None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
