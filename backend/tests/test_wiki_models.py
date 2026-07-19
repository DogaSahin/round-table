# backend/tests/test_wiki_models.py
from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.wiki.models import Tag, WikiLink, WikiPage, WikiPageTag


def _make_campaign(session) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def test_wiki_page_roundtrip_and_defaults() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        page = WikiPage(campaign_id=campaign.id, title="The Ashen Keep", slug="the-ashen-keep")
        session.add(page)
        session.commit()
        session.refresh(page)
        assert page.id is not None
        assert page.player_visible is False
        assert page.body_md is None
        assert page.category is None
        assert page.updated_at is not None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_slug_unique_per_campaign_not_across_campaigns() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        c1, c2 = _make_campaign(session), _make_campaign(session)
        session.add(WikiPage(campaign_id=c1.id, title="Foo", slug="foo"))
        session.commit()

        # Same slug in a different campaign is fine.
        session.add(WikiPage(campaign_id=c2.id, title="Foo", slug="foo"))
        session.commit()

        # Same slug in the SAME campaign violates the unique constraint.
        session.add(WikiPage(campaign_id=c1.id, title="Foo Again", slug="foo"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_wiki_link_roundtrip_with_unresolved_target() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        page = WikiPage(campaign_id=campaign.id, title="Foo", slug="foo")
        session.add(page)
        session.commit()
        session.refresh(page)

        link = WikiLink(
            source_page_id=page.id, target_type="page", target_id=None, target_title="Bar"
        )
        session.add(link)
        session.commit()
        session.refresh(link)
        assert link.id is not None
        assert link.target_id is None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_tag_and_wiki_page_tag_join() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        page = WikiPage(campaign_id=campaign.id, title="Foo", slug="foo")
        tag = Tag(campaign_id=campaign.id, name="location")
        session.add_all([page, tag])
        session.commit()
        session.refresh(page)
        session.refresh(tag)

        session.add(WikiPageTag(page_id=page.id, tag_id=tag.id))
        session.commit()

        joined = (
            session.query(Tag)
            .join(WikiPageTag, WikiPageTag.tag_id == Tag.id)
            .filter(WikiPageTag.page_id == page.id)
            .all()
        )
        assert [t.name for t in joined] == ["location"]
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
