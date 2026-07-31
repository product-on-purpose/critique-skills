"""Tests for bench.generator.blockparse: the independent re-parse used for
the generator's own round-trip check at build time."""

from __future__ import annotations

from bench.generator.blockparse import (
    parse_markdown_blocks,
    reparsed_heading_path,
    reparsed_paragraph_index,
)


def test_parses_heading_and_paragraph_kinds():
    text = "# Title\n\n## Section one\n\nFirst paragraph.\n\nSecond paragraph."
    parsed = parse_markdown_blocks(text)
    kinds = [b.kind for b in parsed]
    assert kinds == ["heading", "heading", "paragraph", "paragraph"]


def test_heading_levels_and_titles():
    text = "# Title\n\n## Section one\n\n### Subsection"
    parsed = parse_markdown_blocks(text)
    assert [(b.level, b.title) for b in parsed] == [
        (1, "Title"),
        (2, "Section one"),
        (3, "Subsection"),
    ]


def test_heading_requires_space_after_hashes():
    text = "#NotAHeading\n\nParagraph text."
    parsed = parse_markdown_blocks(text)
    assert parsed[0].kind == "paragraph"


def test_trailing_hash_markers_are_stripped():
    text = "## Section title ##"
    parsed = parse_markdown_blocks(text)
    assert parsed[0].title == "Section title"


def test_blank_line_separates_paragraphs():
    text = "One.\n\nTwo.\n\nThree."
    parsed = parse_markdown_blocks(text)
    assert len(parsed) == 3
    assert all(b.kind == "paragraph" for b in parsed)


def test_multiline_paragraph_is_one_block():
    text = "Line one\nline two continues.\n\nSecond block."
    parsed = parse_markdown_blocks(text)
    assert len(parsed) == 2


def test_fenced_code_block_absorbs_blank_lines():
    text = "```\ncode line one\n\ncode line two\n```\n\nAfter."
    parsed = parse_markdown_blocks(text)
    assert [b.kind for b in parsed] == ["other", "paragraph"]


def test_list_and_blockquote_and_table_are_not_paragraphs():
    text = "- item one\n- item two\n\n> quoted\n\n| a | b |\n| - | - |"
    parsed = parse_markdown_blocks(text)
    assert all(b.kind == "other" for b in parsed)


def test_indented_code_is_not_a_paragraph():
    text = "    indented code line"
    parsed = parse_markdown_blocks(text)
    assert parsed[0].kind == "other"


def test_setext_heading_levels():
    text = "Level one\n=========\n\nLevel two\n---------"
    parsed = parse_markdown_blocks(text)
    assert [(b.kind, b.level, b.title) for b in parsed] == [
        ("heading", 1, "Level one"),
        ("heading", 2, "Level two"),
    ]


def test_reparsed_paragraph_index_counts_document_wide():
    text = "# Title\n\nFirst.\n\nSecond.\n\n## Section\n\nThird."
    parsed = parse_markdown_blocks(text)
    # positions: 0=heading, 1=paragraph(First), 2=paragraph(Second),
    # 3=heading, 4=paragraph(Third)
    assert reparsed_paragraph_index(parsed, 1) == 1
    assert reparsed_paragraph_index(parsed, 2) == 2
    assert reparsed_paragraph_index(parsed, 4) == 3


def test_reparsed_heading_path_tracks_nesting():
    text = "# Title\n\n## Section one\n\nBody.\n\n## Section two\n\nOther body."
    parsed = parse_markdown_blocks(text)
    # positions: 0=h1, 1=h2 (Section one), 2=paragraph, 3=h2 (Section two), 4=paragraph
    assert reparsed_heading_path(parsed, 2) == ("Title", "Section one")
    assert reparsed_heading_path(parsed, 4) == ("Title", "Section two")
    assert reparsed_heading_path(parsed, 1) == ("Title", "Section one")
