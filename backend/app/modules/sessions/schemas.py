from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Tag = Literal["none", "combat", "roleplay", "loot", "thread"]


class SessionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    date: date_type | None = None


class SessionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    date: date_type | None = None
    summary: str | None = None


class LogCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    tag: Tag = "none"


class SessionLogOut(BaseModel):
    id: int
    text: str
    tag: Tag
    logged_at: datetime
    resolved_at: datetime | None


class SessionListItemOut(BaseModel):
    id: int
    number: int
    date: date_type
    title: str
    status: str


class SessionDetailOut(BaseModel):
    id: int
    number: int
    date: date_type
    title: str
    summary: str | None
    status: str
    logs: list[SessionLogOut]


class RecapRequest(BaseModel):
    tags: list[Tag] = []


class RecapOut(BaseModel):
    text: str
