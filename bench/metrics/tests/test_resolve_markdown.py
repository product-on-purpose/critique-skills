"""Tests for markdown-prose / markdown-tree location resolution and
tolerance (bench/metrics/resolve_markdown.py). Includes S-03 AC-4's
"location-tolerance edge" scenario.
"""

from __future__ import annotations

from bench.metrics.markdown_blocks import parse_markdown
from bench.metrics.resolve_markdown import is_hit, page_matches, resolve
from bench.metrics.tests.fixtures import TOY_MD


def test_paragraph_anchor_hits_exactly_at_index() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, "paragraph 2")
    assert is_hit(doc, r, {"kind": "paragraph", "paragraph": 2}, tree=False)


def test_paragraph_anchor_tolerance_edge_plus_one_hits() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, "paragraph 1")
    # Plus-one edge: a finding naming paragraph 1 credits paragraph 2 too.
    assert is_hit(doc, r, {"kind": "paragraph", "paragraph": 2}, tree=False)


def test_paragraph_anchor_tolerance_edge_minus_one_hits() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, "paragraph 3")
    assert is_hit(doc, r, {"kind": "paragraph", "paragraph": 2}, tree=False)


def test_paragraph_anchor_two_away_is_a_miss() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, "paragraph 4")
    assert not is_hit(doc, r, {"kind": "paragraph", "paragraph": 2}, tree=False)


def test_ordinal_word_paragraph_resolves() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, "the second paragraph")
    assert is_hit(doc, r, {"kind": "paragraph", "paragraph": 2}, tree=False)


def test_section_and_paragraph_ordinal_scoped_within_section() -> None:
    doc = parse_markdown(TOY_MD)
    # "Meter replacement" has one paragraph, document-wide index 3.
    r = resolve(doc, "Meter replacement, first paragraph")
    assert is_hit(doc, r, {"kind": "paragraph", "paragraph": 3}, tree=False)
    # Clipped to the section: paragraph 2 (in a different section) must
    # not be credited even though 2 is adjacent to 3.
    assert not is_hit(doc, r, {"kind": "paragraph", "paragraph": 2}, tree=False)


def test_heading_only_location_credits_every_paragraph_in_section() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, "Service window")
    assert is_hit(doc, r, {"kind": "paragraph", "paragraph": 1}, tree=False)
    assert is_hit(doc, r, {"kind": "paragraph", "paragraph": 2}, tree=False)
    assert not is_hit(doc, r, {"kind": "paragraph", "paragraph": 3}, tree=False)


def test_section_by_number_is_nth_level_two_heading() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, "section 3")  # Billing adjustments
    assert is_hit(doc, r, {"kind": "paragraph", "paragraph": 4}, tree=False)


def test_quoted_heading_title_resolves_section() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, 'see "Billing adjustments" for detail')
    assert is_hit(doc, r, {"kind": "paragraph", "paragraph": 4}, tree=False)


def test_line_anchor_maps_to_containing_paragraph() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, "line 5")  # first body paragraph
    assert is_hit(doc, r, {"kind": "paragraph", "paragraph": 1}, tree=False)


def test_unresolvable_location_is_not_a_hit() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, "throughout the document")
    assert not r.resolvable
    assert not is_hit(doc, r, {"kind": "paragraph", "paragraph": 1}, tree=False)


def test_heading_path_hit_by_title_match() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, "the Meter replacement heading")
    assert is_hit(doc, r, {"kind": "heading-path", "heading_path": ["Field operations notice", "Meter replacement"]}, tree=False)


def test_heading_path_hit_by_adjacent_paragraph() -> None:
    doc = parse_markdown(TOY_MD)
    # Paragraph 3 sits immediately after the "Meter replacement" heading.
    r = resolve(doc, "paragraph 3")
    assert is_hit(
        doc, r, {"kind": "heading-path", "heading_path": ["Field operations notice", "Meter replacement"]}, tree=False
    )


def test_markdown_tree_page_anchor_wrong_page_is_a_miss() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, "paragraph 1, on other-page.md", tree=True, own_artifact_path="bench/corpus/docs/this-page.md")
    assert page_matches("paragraph 1, on other-page.md", "bench/corpus/docs/this-page.md") is False
    assert not is_hit(doc, r, {"kind": "paragraph", "paragraph": 1}, tree=True)


def test_markdown_tree_no_page_named_not_penalized() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(doc, "paragraph 1", tree=True, own_artifact_path="bench/corpus/docs/this-page.md")
    assert is_hit(doc, r, {"kind": "paragraph", "paragraph": 1}, tree=True)


def test_markdown_tree_own_page_named_still_hits() -> None:
    doc = parse_markdown(TOY_MD)
    r = resolve(
        doc, "this-page.md, paragraph 1", tree=True, own_artifact_path="bench/corpus/docs/this-page.md"
    )
    assert is_hit(doc, r, {"kind": "paragraph", "paragraph": 1}, tree=True)
