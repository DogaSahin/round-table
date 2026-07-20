# backend/app/modules/wiki/service.py
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.wiki.links import extract_wikilinks, render_markdown, slugify
from app.modules.wiki.models import Tag, WikiLink, WikiPage, WikiPageTag


def roster(
    db: Session, campaign_id: int, category: str | None = None, tag: str | None = None
) -> list[WikiPage]:
    query = db.query(WikiPage).filter_by(campaign_id=campaign_id)
    if category:
        query = query.filter(WikiPage.category == category)
    if tag:
        query = (
            query.join(WikiPageTag, WikiPageTag.page_id == WikiPage.id)
            .join(Tag, Tag.id == WikiPageTag.tag_id)
            .filter(Tag.campaign_id == campaign_id, Tag.name == tag)
        )
    return query.order_by(WikiPage.title).all()


def search(db: Session, campaign_id: int, query: str) -> list[WikiPage]:
    needle = query.strip()
    if not needle:
        return []
    like = f"%{needle}%"
    return (
        db.query(WikiPage)
        .filter(
            WikiPage.campaign_id == campaign_id,
            (WikiPage.title.ilike(like)) | (WikiPage.body_md.ilike(like)),
        )
        .order_by(WikiPage.title)
        .all()
    )


def owned_by_slug(db: Session, slug: str, campaign_id: int) -> WikiPage | None:
    return db.query(WikiPage).filter_by(campaign_id=campaign_id, slug=slug).first()


def categories(db: Session, campaign_id: int) -> list[str]:
    rows = (
        db.query(WikiPage.category)
        .filter(WikiPage.campaign_id == campaign_id, WikiPage.category.isnot(None))
        .distinct()
        .all()
    )
    return sorted({r[0] for r in rows if r[0]})


def all_tags(db: Session, campaign_id: int) -> list[Tag]:
    return db.query(Tag).filter_by(campaign_id=campaign_id).order_by(Tag.name).all()


def page_tags(db: Session, page_id: int) -> list[Tag]:
    return (
        db.query(Tag)
        .join(WikiPageTag, WikiPageTag.tag_id == Tag.id)
        .filter(WikiPageTag.page_id == page_id)
        .order_by(Tag.name)
        .all()
    )


def page_links(db: Session, page_id: int) -> list[WikiLink]:
    return db.query(WikiLink).filter_by(source_page_id=page_id).all()


def unique_slug(db: Session, campaign_id: int, title: str) -> str:
    base = slugify(title)
    slug = base
    n = 2
    while db.query(WikiPage).filter_by(campaign_id=campaign_id, slug=slug).first() is not None:
        slug = f"{base}-{n}"
        n += 1
    return slug


def _find_linked_page(db: Session, campaign_id: int, name: str) -> WikiPage | None:
    return (
        db.query(WikiPage)
        .filter(WikiPage.campaign_id == campaign_id, func.lower(WikiPage.title) == name.lower())
        .first()
    )


def rebuild_links(db: Session, page_row: WikiPage) -> None:
    db.query(WikiLink).filter_by(source_page_id=page_row.id).delete(synchronize_session=False)
    for name in extract_wikilinks(page_row.body_md):
        target = _find_linked_page(db, page_row.campaign_id, name)
        db.add(
            WikiLink(
                source_page_id=page_row.id,
                target_type="page",
                target_id=target.id if target is not None else None,
                target_title=name,
            )
        )
    db.commit()


def backlinks(db: Session, page_row: WikiPage) -> list[WikiPage]:
    rows = db.query(WikiLink).filter_by(target_type="page", target_id=page_row.id).all()
    source_ids = {r.source_page_id for r in rows}
    if not source_ids:
        return []
    return db.query(WikiPage).filter(WikiPage.id.in_(source_ids)).order_by(WikiPage.title).all()


def render_page_html(db: Session, page_row: WikiPage) -> str:
    def resolve_href(name: str) -> tuple[str, bool]:
        target = _find_linked_page(db, page_row.campaign_id, name)
        if target is not None:
            return (f"/wiki/{target.slug}", True)
        return (f"/wiki/new?title={name}", False)

    return render_markdown(page_row.body_md, resolve_href)


def create_page(
    db: Session,
    campaign_id: int,
    title: str,
    category: str | None,
    body_md: str | None,
    player_visible: bool,
) -> WikiPage:
    page = WikiPage(
        campaign_id=campaign_id,
        title=title,
        slug=unique_slug(db, campaign_id, title),
        category=category,
        body_md=body_md,
        player_visible=player_visible,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    rebuild_links(db, page)
    return page


def update_page(
    db: Session,
    page_row: WikiPage,
    title: str | None,
    category: str | None,
    body_md: str | None,
    player_visible: bool | None,
) -> WikiPage:
    if title is not None:
        page_row.title = title
        # Slug is intentionally NOT regenerated (keeps inbound [[links]] + URLs stable).
    if category is not None:
        page_row.category = category
    if body_md is not None:
        page_row.body_md = body_md
    if player_visible is not None:
        page_row.player_visible = player_visible
    page_row.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(page_row)
    rebuild_links(db, page_row)
    return page_row


def delete_page(db: Session, page_row: WikiPage) -> None:
    db.query(WikiLink).filter_by(source_page_id=page_row.id).delete(synchronize_session=False)
    db.query(WikiPageTag).filter_by(page_id=page_row.id).delete(synchronize_session=False)
    db.delete(page_row)
    db.commit()


def add_tag(db: Session, campaign_id: int, page_row: WikiPage, name: str) -> Tag:
    tag = db.query(Tag).filter_by(campaign_id=campaign_id, name=name).first()
    if tag is None:
        tag = Tag(campaign_id=campaign_id, name=name)
        db.add(tag)
        db.flush()
    exists = db.query(WikiPageTag).filter_by(page_id=page_row.id, tag_id=tag.id).first() is not None
    if not exists:
        db.add(WikiPageTag(page_id=page_row.id, tag_id=tag.id))
    db.commit()
    return tag


def remove_tag(db: Session, page_row: WikiPage, tag_id: int) -> None:
    db.query(WikiPageTag).filter_by(page_id=page_row.id, tag_id=tag_id).delete(
        synchronize_session=False
    )
    db.commit()
