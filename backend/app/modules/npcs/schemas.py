from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Disposition = Literal["hostile", "unfriendly", "neutral", "friendly", "allied"]

TEXT_FIELD_MAX_LENGTH = 4000


class NpcCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    disposition: Disposition = "neutral"
    faction_id: int | None = None
    statblock: str | None = Field(default=None, max_length=TEXT_FIELD_MAX_LENGTH)
    motivation: str | None = Field(default=None, max_length=TEXT_FIELD_MAX_LENGTH)
    secrets: str | None = Field(default=None, max_length=TEXT_FIELD_MAX_LENGTH)
    voice: str | None = Field(default=None, max_length=TEXT_FIELD_MAX_LENGTH)
    player_visible: bool = False


class NpcUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    disposition: Disposition | None = None
    faction_id: int | None = None
    statblock: str | None = Field(default=None, max_length=TEXT_FIELD_MAX_LENGTH)
    motivation: str | None = Field(default=None, max_length=TEXT_FIELD_MAX_LENGTH)
    secrets: str | None = Field(default=None, max_length=TEXT_FIELD_MAX_LENGTH)
    voice: str | None = Field(default=None, max_length=TEXT_FIELD_MAX_LENGTH)
    player_visible: bool | None = None


class NpcListItemOut(BaseModel):
    id: int
    name: str
    disposition: Disposition
    faction_id: int | None


class NpcDetailOut(BaseModel):
    id: int
    name: str
    disposition: Disposition
    faction_id: int | None
    statblock: str | None
    motivation: str | None
    secrets: str | None
    voice: str | None
    portrait_path: str | None
    player_visible: bool
