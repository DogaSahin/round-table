# backend/app/modules/bestiary/schemas.py
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.shared.statblock import Statblock


class BestiaryMonsterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    statblock: Statblock
    image_url: str | None = Field(default=None, max_length=500)


class BestiaryMonsterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    statblock: Statblock | None = None
    image_url: str | None = Field(default=None, max_length=500)


class BestiaryMonsterListItemOut(BaseModel):
    id: int
    name: str
    slug: str
    creature_type: str
    challenge_rating: float
    is_favorite: bool
    image_url: str | None


class BestiaryMonsterDetailOut(BaseModel):
    id: int
    name: str
    slug: str
    statblock: Statblock
    image_url: str | None
    is_favorite: bool
    cloned_from_content_id: int | None
    created_at: datetime
    updated_at: datetime
