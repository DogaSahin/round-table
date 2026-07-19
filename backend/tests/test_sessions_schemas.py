from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.sessions.schemas import (
    LogCreate,
    RecapRequest,
    SessionCreate,
    SessionUpdate,
)


def test_session_create_requires_nonempty_title() -> None:
    with pytest.raises(ValidationError):
        SessionCreate(title="")


def test_session_create_allows_omitted_date() -> None:
    payload = SessionCreate(title="Session One")
    assert payload.date is None


def test_session_update_all_fields_optional() -> None:
    payload = SessionUpdate()
    assert payload.title is None
    assert payload.date is None
    assert payload.summary is None


def test_log_create_defaults_to_none_tag() -> None:
    payload = LogCreate(text="A scratch note.")
    assert payload.tag == "none"


def test_log_create_rejects_invalid_tag() -> None:
    with pytest.raises(ValidationError):
        LogCreate(text="bad tag", tag="not-a-real-tag")  # type: ignore[arg-type]


def test_recap_request_defaults_to_empty_tags() -> None:
    payload = RecapRequest()
    assert payload.tags == []
