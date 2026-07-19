from __future__ import annotations

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.npcs.models import Npc


def _make_campaign(session) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def test_npc_roundtrip_and_defaults() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        row = Npc(campaign_id=campaign.id, name="Old Man Grigg")
        session.add(row)
        session.commit()
        session.refresh(row)
        assert row.id is not None
        assert row.disposition == "neutral"
        assert row.player_visible is False
        assert row.faction_id is None
        assert row.statblock is None
        assert row.motivation is None
        assert row.secrets is None
        assert row.voice is None
        assert row.portrait_path is None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_npc_stores_all_optional_fields_and_soft_faction_reference() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        row = Npc(
            campaign_id=campaign.id,
            name="Old Man Grigg",
            disposition="friendly",
            faction_id=999999,  # deliberately not a real faction row — soft ref, no FK
            statblock="AC 10, HP 4",
            motivation="Wants his cat back.",
            secrets="Actually a retired assassin.",
            voice="Raspy, trails off mid-sentence.",
            player_visible=True,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        assert row.faction_id == 999999
        assert row.secrets == "Actually a retired assassin."
        assert row.player_visible is True
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
