from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.wiki.schemas import TagCreate, WikiPageCreate, WikiPageUpdate


def test_wiki_page_create_requires_nonempty_title() -> None:
    with pytest.raises(ValidationError):
        WikiPageCreate(title="")


def test_wiki_page_create_defaults() -> None:
    payload = WikiPageCreate(title="The Ashen Keep")
    assert payload.category is None
    assert payload.body_md is None
    assert payload.player_visible is False


def test_wiki_page_update_all_fields_optional() -> None:
    payload = WikiPageUpdate()
    assert payload.title is None
    assert payload.category is None
    assert payload.body_md is None
    assert payload.player_visible is None


def test_tag_create_requires_nonempty_name() -> None:
    with pytest.raises(ValidationError):
        TagCreate(name="")


def test_wiki_page_create_accepts_full_payload() -> None:
    payload = WikiPageCreate(
        title="The Ashen Keep",
        category="Locations",
        body_md="A crumbling fortress. See [[Old Man Grigg]].",
        player_visible=True,
    )
    assert payload.category == "Locations"
    assert payload.player_visible is True
