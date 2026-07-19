from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Disposition = Literal["hostile", "unfriendly", "neutral", "friendly", "allied"]

CLOCK_MIN_SEGMENTS = 2
CLOCK_MAX_SEGMENTS = 12


class FactionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    disposition: Disposition = "neutral"
    goals: str | None = None
    description: str | None = None


class FactionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    disposition: Disposition | None = None
    goals: str | None = None
    description: str | None = None


class ClockCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    segments: int = Field(default=6, ge=CLOCK_MIN_SEGMENTS, le=CLOCK_MAX_SEGMENTS)


class FillClockRequest(BaseModel):
    segment: int = Field(ge=0)


class ActivityCreate(BaseModel):
    entry: str = Field(min_length=1, max_length=2000)


class ClockOut(BaseModel):
    id: int
    name: str
    segments: int
    filled: int


class ActivityOut(BaseModel):
    id: int
    entry: str
    occurred_at: datetime


class FactionListItemOut(BaseModel):
    id: int
    name: str
    disposition: Disposition


class FactionDetailOut(BaseModel):
    id: int
    name: str
    description: str | None
    disposition: Disposition
    goals: str | None
    clocks: list[ClockOut]
    activity: list[ActivityOut]
