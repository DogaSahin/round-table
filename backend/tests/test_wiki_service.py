# backend/tests/test_wiki_service.py
from __future__ import annotations

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.wiki import service


def _make_campaign(db) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def test_create_page_generates_unique_slug_and_persists() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        page = service.create_page(db, campaign.id, "The Ashen Keep", None, None, False)
        assert page.slug == "the-ashen-keep"
        assert page.player_visible is False

        dup = service.create_page(db, campaign.id, "The Ashen Keep", None, None, False)
        assert dup.slug == "the-ashen-keep-2"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_roster_and_owned_by_slug_scoped_to_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        page = service.create_page(db, c1.id, "Foo", None, None, False)
        service.create_page(db, c2.id, "Bar", None, None, False)

        assert len(service.roster(db, c1.id)) == 1
        assert service.owned_by_slug(db, page.slug, c1.id) is not None
        assert service.owned_by_slug(db, page.slug, c2.id) is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_update_page_only_touches_given_fields_and_never_regenerates_slug() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        page = service.create_page(db, campaign.id, "Original", None, None, False)
        original_slug = page.slug

        updated = service.update_page(
            db, page, title="Renamed Completely", category=None, body_md=None, player_visible=None
        )
        assert updated.title == "Renamed Completely"
        assert updated.slug == original_slug
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_rebuild_links_resolves_page_links_and_leaves_others_unresolved() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        service.create_page(db, campaign.id, "Old Man Grigg", None, None, False)
        source = service.create_page(
            db,
            campaign.id,
            "The Ashen Keep",
            None,
            "See [[Old Man Grigg]] and [[Nonexistent Page]].",
            False,
        )

        links = db.query(service.WikiLink).filter_by(source_page_id=source.id).all()
        by_title = {link.target_title: link for link in links}
        assert by_title["Old Man Grigg"].target_id is not None
        assert by_title["Old Man Grigg"].target_type == "page"
        assert by_title["Nonexistent Page"].target_id is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_backlinks_returns_pages_linking_to_target() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        target = service.create_page(db, campaign.id, "Old Man Grigg", None, None, False)
        source = service.create_page(
            db, campaign.id, "The Ashen Keep", None, "See [[Old Man Grigg]].", False
        )

        back = service.backlinks(db, target)
        assert [p.id for p in back] == [source.id]
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_render_page_html_produces_resolved_and_unresolved_anchor_classes() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        service.create_page(db, campaign.id, "Old Man Grigg", None, None, False)
        source = service.create_page(
            db, campaign.id, "The Ashen Keep", None, "See [[Old Man Grigg]] and [[Nowhere]].", False
        )

        html = service.render_page_html(db, source)
        assert 'class="wikilink"' in html
        assert 'class="wikilink wikilink-new"' in html
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_add_and_remove_tag() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        page = service.create_page(db, campaign.id, "Foo", None, None, False)

        tag = service.add_tag(db, campaign.id, page, "location")
        assert len(service.page_tags(db, page.id)) == 1

        # Adding the same tag name again reuses the existing Tag row, no duplicate link.
        service.add_tag(db, campaign.id, page, "location")
        assert len(service.page_tags(db, page.id)) == 1

        service.remove_tag(db, page, tag.id)
        assert service.page_tags(db, page.id) == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_delete_page_removes_outbound_links() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        service.create_page(db, campaign.id, "Old Man Grigg", None, None, False)
        source = service.create_page(
            db, campaign.id, "The Ashen Keep", None, "See [[Old Man Grigg]].", False
        )

        service.delete_page(db, source)
        remaining = service.roster(db, campaign.id)
        assert [p.title for p in remaining] == ["Old Man Grigg"]
        assert db.query(service.WikiLink).filter_by(source_page_id=source.id).all() == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
