# backend/app/modules/wiki/routes.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.modules.wiki import service
from app.modules.wiki.models import WikiLink, WikiPage
from app.modules.wiki.schemas import (
    LinkOut,
    PageDetailOut,
    PageListItemOut,
    TagCreate,
    TagOut,
    WikiPageCreate,
    WikiPageUpdate,
)
from app.shared.errors import NotFound

router = APIRouter(prefix="/api/wiki", tags=["wiki"])


def _list_item_out(page: WikiPage) -> PageListItemOut:
    return PageListItemOut(
        id=page.id,
        title=page.title,
        slug=page.slug,
        category=page.category,
        player_visible=page.player_visible,
    )


def _link_out(link: WikiLink) -> LinkOut:
    return LinkOut(
        target_title=link.target_title,
        target_type=link.target_type,
        target_id=link.target_id,
        resolved=link.target_id is not None,
    )


def _detail_out(db: Session, page: WikiPage) -> PageDetailOut:
    links = service.page_links(db, page.id)
    return PageDetailOut(
        id=page.id,
        title=page.title,
        slug=page.slug,
        category=page.category,
        body_md=page.body_md,
        body_html=service.render_page_html(db, page),
        player_visible=page.player_visible,
        updated_at=page.updated_at,
        tags=[TagOut(id=t.id, name=t.name) for t in service.page_tags(db, page.id)],
        links=[_link_out(link) for link in links],
        backlinks=[_list_item_out(p) for p in service.backlinks(db, page)],
    )


def _get_owned(db: Session, slug: str, campaign: Campaign) -> WikiPage:
    page = service.owned_by_slug(db, slug, campaign.id)
    if page is None:
        raise NotFound(f"wiki page '{slug}' not found")
    return page


@router.post("", response_model=PageDetailOut)
def create(
    payload: WikiPageCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> PageDetailOut:
    page = service.create_page(
        db, campaign.id, payload.title, payload.category, payload.body_md, payload.player_visible
    )
    return _detail_out(db, page)


@router.get("", response_model=list[PageListItemOut])
def list_pages(
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> list[PageListItemOut]:
    rows = service.roster(db, campaign.id)
    return [_list_item_out(p) for p in rows]


@router.get("/search", response_model=list[PageListItemOut])
def search(
    q: str = "",
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> list[PageListItemOut]:
    rows = service.search(db, campaign.id, q)
    return [_list_item_out(p) for p in rows]


@router.get("/{slug}", response_model=PageDetailOut)
def detail(
    slug: str,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> PageDetailOut:
    return _detail_out(db, _get_owned(db, slug, campaign))


@router.patch("/{slug}", response_model=PageDetailOut)
def update(
    slug: str,
    payload: WikiPageUpdate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> PageDetailOut:
    page = _get_owned(db, slug, campaign)
    page = service.update_page(
        db, page, payload.title, payload.category, payload.body_md, payload.player_visible
    )
    return _detail_out(db, page)


@router.delete("/{slug}", status_code=204, response_model=None)
def delete(
    slug: str,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    page = _get_owned(db, slug, campaign)
    service.delete_page(db, page)


@router.post("/{slug}/tags", response_model=TagOut)
def add_tag(
    slug: str,
    payload: TagCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> TagOut:
    page = _get_owned(db, slug, campaign)
    tag = service.add_tag(db, campaign.id, page, payload.name)
    return TagOut(id=tag.id, name=tag.name)


@router.delete("/{slug}/tags/{tag_id}", status_code=204, response_model=None)
def remove_tag(
    slug: str,
    tag_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    page = _get_owned(db, slug, campaign)
    service.remove_tag(db, page, tag_id)
