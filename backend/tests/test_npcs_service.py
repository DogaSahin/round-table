# backend/tests/test_npcs_service.py
from __future__ import annotations

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.npcs import service


def _make_campaign(db) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def test_create_and_roster_scoped_to_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        service.create_npc(
            db, c1.id, "Old Man Grigg", "neutral", None, None, None, None, None, False
        )
        service.create_npc(
            db, c2.id, "Other Campaign NPC", "neutral", None, None, None, None, None, False
        )

        assert len(service.roster(db, c1.id)) == 1
        assert len(service.roster(db, c2.id)) == 1
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_owned_scoped_to_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        row = service.create_npc(
            db, c1.id, "Old Man Grigg", "neutral", None, None, None, None, None, False
        )

        assert service.owned(db, row.id, c1.id) is not None
        assert service.owned(db, row.id, c2.id) is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_npc_stores_all_fields() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_npc(
            db,
            campaign.id,
            "Old Man Grigg",
            "friendly",
            7,
            "AC 10, HP 4",
            "Wants his cat back.",
            "Actually a retired assassin.",
            "Raspy, trails off mid-sentence.",
            True,
        )
        assert row.faction_id == 7
        assert row.secrets == "Actually a retired assassin."
        assert row.player_visible is True
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_update_npc_only_touches_given_fields() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_npc(
            db, campaign.id, "Original", "neutral", None, None, None, None, None, False
        )

        updated = service.update_npc(
            db,
            row,
            name=None,
            disposition="hostile",
            faction_id=None,
            statblock=None,
            motivation=None,
            secrets=None,
            voice=None,
            player_visible=None,
        )

        assert updated.name == "Original"
        assert updated.disposition == "hostile"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_delete_npc() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_npc(
            db, campaign.id, "Doomed", "neutral", None, None, None, None, None, False
        )

        service.delete_npc(db, row)
        assert service.roster(db, campaign.id) == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
