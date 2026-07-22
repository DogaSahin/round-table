from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.bestiary.models import BestiaryMonster


def _make_campaign(session) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def test_bestiary_monster_roundtrip_and_defaults() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        row = BestiaryMonster(
            campaign_id=campaign.id,
            name="Giant Rat",
            slug="giant-rat",
            statblock='{"hit_points": 7}',
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        assert row.id is not None
        assert row.is_favorite is False
        assert row.image_url is None
        assert row.cloned_from_content_id is None
        assert row.created_at is not None
        assert row.updated_at is not None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_slug_unique_per_campaign_not_across_campaigns() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        c1, c2 = _make_campaign(session), _make_campaign(session)
        session.add(
            BestiaryMonster(campaign_id=c1.id, name="Goblin", slug="goblin", statblock="{}")
        )
        session.commit()

        # Same slug in a different campaign is fine.
        session.add(
            BestiaryMonster(campaign_id=c2.id, name="Goblin", slug="goblin", statblock="{}")
        )
        session.commit()

        # Same slug in the SAME campaign violates the unique constraint.
        session.add(
            BestiaryMonster(campaign_id=c1.id, name="Goblin Again", slug="goblin", statblock="{}")
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_bestiary_monster_soft_content_reference_and_favorite_toggle() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        row = BestiaryMonster(
            campaign_id=campaign.id,
            name="Cloned Owlbear",
            slug="cloned-owlbear",
            statblock="{}",
            image_url="/media/owlbear.png",
            is_favorite=True,
            # deliberately not a real content.creature row — soft ref, no FK
            cloned_from_content_id=999999,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        assert row.cloned_from_content_id == 999999
        assert row.is_favorite is True
        assert row.image_url == "/media/owlbear.png"
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
