from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.factions.schemas import (
    ClockCreate,
    FactionCreate,
    FactionUpdate,
    FillClockRequest,
)


def test_faction_create_requires_nonempty_name() -> None:
    with pytest.raises(ValidationError):
        FactionCreate(name="")


def test_faction_create_defaults_disposition_to_neutral() -> None:
    payload = FactionCreate(name="The Ashen Circle")
    assert payload.disposition == "neutral"


def test_faction_create_rejects_invalid_disposition() -> None:
    with pytest.raises(ValidationError):
        FactionCreate(name="The Ashen Circle", disposition="furious")  # type: ignore[arg-type]


def test_faction_update_all_fields_optional() -> None:
    payload = FactionUpdate()
    assert payload.name is None
    assert payload.disposition is None
    assert payload.goals is None
    assert payload.description is None


def test_clock_create_defaults_to_six_segments() -> None:
    payload = ClockCreate(name="Ritual complete")
    assert payload.segments == 6


def test_clock_create_rejects_out_of_range_segments() -> None:
    with pytest.raises(ValidationError):
        ClockCreate(name="Too big", segments=13)
    with pytest.raises(ValidationError):
        ClockCreate(name="Too small", segments=1)


def test_fill_clock_request_rejects_negative_segment() -> None:
    with pytest.raises(ValidationError):
        FillClockRequest(segment=-1)
