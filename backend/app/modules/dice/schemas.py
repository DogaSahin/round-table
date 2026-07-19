from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RollRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=200)


class RollTermOut(BaseModel):
    source: str
    sign: int
    is_dice: bool
    total: int
    kept: list[int]
    discarded: list[int]
    flat: int | None


class RollResultOut(BaseModel):
    expression: str
    total: int
    terms: list[RollTermOut]


class HistoryEntryOut(BaseModel):
    id: int
    expression: str
    result: int
    rolled_at: datetime


class SavedRollCreate(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    expression: str = Field(min_length=1, max_length=200)


class SavedRollOut(BaseModel):
    id: int
    label: str
    expression: str
