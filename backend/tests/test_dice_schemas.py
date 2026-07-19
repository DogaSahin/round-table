from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.modules.dice.schemas import (
    HistoryEntryOut,
    RollRequest,
    RollResultOut,
    RollTermOut,
    SavedRollCreate,
    SavedRollOut,
)


def test_roll_request_accepts_valid_expression() -> None:
    assert RollRequest(expression="2d6+3").expression == "2d6+3"


def test_roll_request_rejects_empty_expression() -> None:
    with pytest.raises(ValidationError):
        RollRequest(expression="")


def test_roll_result_out_nests_terms() -> None:
    result = RollResultOut(
        expression="1d20",
        total=15,
        terms=[
            RollTermOut(
                source="1d20",
                sign=1,
                is_dice=True,
                total=15,
                kept=[15],
                discarded=[],
                flat=None,
            )
        ],
    )
    assert result.terms[0].total == 15


def test_history_entry_out_requires_datetime() -> None:
    entry = HistoryEntryOut(id=1, expression="1d4", result=3, rolled_at=datetime.now(UTC))
    assert entry.result == 3


def test_saved_roll_create_rejects_overlong_label() -> None:
    with pytest.raises(ValidationError):
        SavedRollCreate(label="x" * 201, expression="1d6")


def test_saved_roll_out_roundtrip() -> None:
    out = SavedRollOut(id=1, label="Fireball", expression="8d6")
    assert out.label == "Fireball"
