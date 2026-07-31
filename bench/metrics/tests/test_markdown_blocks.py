"""Tests for the normative markdown block parser
(bench/metrics/markdown_blocks.py)."""

from __future__ import annotations

from bench.metrics.markdown_blocks import parse_blocks, parse_markdown
from bench.metrics.tests.fixtures import TOY_MD


def test_toy_md_paragraph_and_heading_counts() -> None:
    doc = parse_markdown(TOY_MD)
    assert len(doc.paragraph_positions()) == 4
    assert len(doc.heading_positions()) == 4  # h1 + three h2s
    assert len(doc.level2_headings()) == 3


def test_toy_md_paragraph_indices_in_order() -> None:
    doc = parse_markdown(TOY_MD)
    for expected, pos in enumerate(doc.paragraph_positions(), start=1):
        assert doc.paragraph_index(pos) == expected


def test_heading_titles_stripped_of_markers() -> None:
    doc = parse_markdown(TOY_MD)
    titles = [doc.blocks[i].title for i in doc.heading_positions()]
    assert titles == ["Field operations notice", "Service window", "Meter replacement", "Billing adjustments"]


def test_heading_path_includes_self_for_heading_block() -> None:
    doc = parse_markdown(TOY_MD)
    service_window = doc.level2_headings()[0]
    assert doc.heading_path(service_window) == ("Field operations notice", "Service window")


def test_heading_path_for_paragraph_excludes_self() -> None:
    doc = parse_markdown(TOY_MD)
    first_paragraph = doc.paragraph_positions()[0]
    assert doc.heading_path(first_paragraph) == ("Field operations notice", "Service window")


def test_paragraphs_under_section_includes_only_that_section() -> None:
    doc = parse_markdown(TOY_MD)
    service_window = doc.level2_headings()[0]
    under = doc.paragraphs_under(service_window)
    assert [doc.paragraph_index(p) for p in under] == [1, 2]

    meter_replacement = doc.level2_headings()[1]
    under2 = doc.paragraphs_under(meter_replacement)
    assert [doc.paragraph_index(p) for p in under2] == [3]


def test_blank_line_only_whitespace_still_separates_blocks() -> None:
    text = "Paragraph one.\n   \nParagraph two.\n"
    blocks = parse_blocks(text)
    assert len(blocks) == 2
    assert all(b.kind == "paragraph" for b in blocks)


def test_fenced_code_runs_through_blank_lines() -> None:
    text = "Intro paragraph.\n\n```\ncode line one\n\ncode line two\n```\n\nAfter.\n"
    blocks = parse_blocks(text)
    kinds = [b.kind for b in blocks]
    assert kinds == ["paragraph", "other", "paragraph"]
    assert blocks[1].lines[0].startswith("```")
    assert blocks[1].lines[-1].startswith("```")


def test_setext_heading_level_one_and_two() -> None:
    text = "Title\n=====\n\nSubtitle\n--------\n\nBody text.\n"
    blocks = parse_blocks(text)
    assert blocks[0].kind == "heading" and blocks[0].level == 1 and blocks[0].title == "Title"
    assert blocks[1].kind == "heading" and blocks[1].level == 2 and blocks[1].title == "Subtitle"
    assert blocks[2].kind == "paragraph"


def test_list_blockquote_table_html_are_not_paragraphs() -> None:
    text = (
        "- item one\n- item two\n"
        "\n"
        "> a quotation\n"
        "\n"
        "| a | b |\n|---|---|\n"
        "\n"
        "<div>raw html</div>\n"
        "\n"
        "1. numbered item\n"
    )
    blocks = parse_blocks(text)
    assert all(b.kind == "other" for b in blocks)


def test_indented_code_is_not_a_paragraph() -> None:
    text = "Normal paragraph.\n\n    code here\n    more code\n"
    blocks = parse_blocks(text)
    assert blocks[0].kind == "paragraph"
    assert blocks[1].kind == "other"


def test_block_at_line_maps_line_numbers() -> None:
    doc = parse_markdown(TOY_MD)
    # Line 1 is the title heading.
    pos = doc.block_at_line(1)
    assert pos is not None and doc.blocks[pos].kind == "heading"
    # The first body paragraph starts at line 5.
    lines = TOY_MD.split("\n")
    assert "field crew reviews" in lines[4]
    pos2 = doc.block_at_line(5)
    assert pos2 is not None and doc.blocks[pos2].kind == "paragraph"
    assert doc.paragraph_index(pos2) == 1
