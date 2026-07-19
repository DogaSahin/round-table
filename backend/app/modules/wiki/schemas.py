from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

BODY_MAX_LENGTH = 20000


class WikiPageCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=80)
    body_md: str | None = Field(default=None, max_length=BODY_MAX_LENGTH)
    player_visible: bool = False


class WikiPageUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=80)
    body_md: str | None = Field(default=None, max_length=BODY_MAX_LENGTH)
    player_visible: bool | None = None


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)


class TagOut(BaseModel):
    id: int
    name: str


class LinkOut(BaseModel):
    target_title: str
    target_type: str
    target_id: int | None
    resolved: bool


class PageListItemOut(BaseModel):
    id: int
    title: str
    slug: str
    category: str | None
    player_visible: bool


class PageDetailOut(BaseModel):
    id: int
    title: str
    slug: str
    category: str | None
    body_md: str | None
    body_html: str
    player_visible: bool
    updated_at: datetime
    tags: list[TagOut]
    links: list[LinkOut]
    backlinks: list[PageListItemOut]
