from __future__ import annotations

from app.modules.wiki.links import extract_wikilinks, render_markdown, slugify


def test_slugify_basic() -> None:
    assert slugify("The Ashen Keep") == "the-ashen-keep"
    assert slugify("  Multiple   Spaces! ") == "multiple-spaces"
    assert slugify("") == "page"


def test_extract_wikilinks_distinct_in_document_order() -> None:
    body = "See [[The Ashen Keep]] and [[Old Man Grigg]]. Also [[The Ashen Keep]] again."
    assert extract_wikilinks(body) == ["The Ashen Keep", "Old Man Grigg"]


def test_extract_wikilinks_skips_fenced_and_inline_code() -> None:
    body = "Real [[Link]] but not `[[NotALink]]` or:\n```\n[[AlsoNotALink]]\n```"
    assert extract_wikilinks(body) == ["Link"]


def test_extract_wikilinks_none_body_returns_empty() -> None:
    assert extract_wikilinks(None) == []


def test_render_markdown_basic_formatting() -> None:
    html = render_markdown("**bold** and *italic*", lambda name: (f"/wiki/{name}", True))
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html


def test_render_markdown_rewrites_wikilinks_via_resolver() -> None:
    def resolver(name: str) -> tuple[str, bool]:
        if name == "Known Page":
            return ("/wiki/known-page", True)
        return ("/wiki/new?title=Known+Page", False)

    html = render_markdown("See [[Known Page]] and [[Missing Page]].", resolver)
    assert 'class="wikilink"' in html
    assert 'href="/wiki/known-page"' in html
    assert 'class="wikilink wikilink-new"' in html


def test_render_markdown_none_body_returns_empty_string() -> None:
    assert render_markdown(None, lambda name: (name, True)) == ""
