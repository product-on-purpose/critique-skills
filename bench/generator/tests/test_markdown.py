"""Tests for bench.generator.markdown: the shared markdown-prose /
markdown-tree composition model."""

from __future__ import annotations

import pytest

from bench.generator.markdown import Block, Document, heading_path, paragraph_index, render_blocks


def _sample_document() -> Document:
    return Document(
        (
            Block(kind="heading", level=1, text="# Title", slot="h0"),
            Block(kind="heading", level=2, text="## Section one", slot="s1.h"),
            Block(kind="paragraph", level=0, text="First paragraph.", slot="s1.p1"),
            Block(kind="paragraph", level=0, text="Second paragraph.", slot="s1.p2"),
            Block(kind="heading", level=2, text="## Section two", slot="s2.h"),
            Block(kind="paragraph", level=0, text="Third paragraph.", slot="s2.p1"),
        )
    )


def test_block_lookup():
    doc = _sample_document()
    assert doc.block("s1.p2").text == "Second paragraph."


def test_block_missing_slot_raises_keyerror():
    doc = _sample_document()
    with pytest.raises(KeyError):
        doc.block("no-such-slot")


def test_slot_index():
    doc = _sample_document()
    assert doc.slot_index("h0") == 0
    assert doc.slot_index("s2.p1") == 5


def test_replace_changes_only_the_named_block():
    doc = _sample_document()
    new_doc = doc.replace("s1.p1", "Rewritten first paragraph.")
    assert new_doc.block("s1.p1").text == "Rewritten first paragraph."
    # Every other block is unchanged, and the original Document is untouched.
    assert new_doc.block("s1.p2").text == "Second paragraph."
    assert doc.block("s1.p1").text == "First paragraph."
    assert len(new_doc.blocks) == len(doc.blocks)


def test_replace_preserves_kind_level_and_slot():
    doc = _sample_document()
    new_doc = doc.replace("s1.p1", "New text.")
    original = doc.block("s1.p1")
    replaced = new_doc.block("s1.p1")
    assert replaced.kind == original.kind
    assert replaced.level == original.level
    assert replaced.slot == original.slot


def test_replace_missing_slot_raises_keyerror():
    doc = _sample_document()
    with pytest.raises(KeyError):
        doc.replace("no-such-slot", "text")


def test_insert_after_section_lands_before_next_heading():
    doc = _sample_document()
    new_heading = Block(kind="heading", level=3, text="### Orphan", slot="s1.x1")
    new_doc = doc.insert_after_section("s1.h", new_heading)
    slots = [b.slot for b in new_doc.blocks]
    # Inserted right before s2.h, after everything already in section 1.
    assert slots == ["h0", "s1.h", "s1.p1", "s1.p2", "s1.x1", "s2.h", "s2.p1"]


def test_insert_after_section_at_end_of_document():
    doc = _sample_document()
    new_heading = Block(kind="heading", level=3, text="### Orphan", slot="s2.x1")
    new_doc = doc.insert_after_section("s2.h", new_heading)
    slots = [b.slot for b in new_doc.blocks]
    assert slots[-1] == "s2.x1"


def test_insert_after_section_does_not_mutate_original():
    doc = _sample_document()
    original_len = len(doc.blocks)
    new_heading = Block(kind="heading", level=3, text="### Orphan", slot="s1.x1")
    doc.insert_after_section("s1.h", new_heading)
    assert len(doc.blocks) == original_len


def test_insert_after_section_missing_anchor_raises_keyerror():
    doc = _sample_document()
    new_heading = Block(kind="heading", level=3, text="### Orphan", slot="x")
    with pytest.raises(KeyError):
        doc.insert_after_section("no-such-anchor", new_heading)


def test_heading_path_for_paragraph():
    doc = _sample_document()
    assert heading_path(doc, "s1.p1") == ("Title", "Section one")
    assert heading_path(doc, "s2.p1") == ("Title", "Section two")


def test_heading_path_for_heading_includes_itself():
    doc = _sample_document()
    assert heading_path(doc, "s1.h") == ("Title", "Section one")
    assert heading_path(doc, "h0") == ("Title",)


def test_heading_path_strips_markers_and_trims():
    doc = Document(
        (Block(kind="heading", level=1, text="#   Padded Title   ##", slot="h0"),)
    )
    assert heading_path(doc, "h0") == ("Padded Title",)


def test_paragraph_index_is_document_wide():
    doc = _sample_document()
    assert paragraph_index(doc, "s1.p1") == 1
    assert paragraph_index(doc, "s1.p2") == 2
    assert paragraph_index(doc, "s2.p1") == 3


def test_paragraph_index_rejects_a_heading_slot():
    doc = _sample_document()
    with pytest.raises(KeyError):
        paragraph_index(doc, "s1.h")


def test_render_blocks_joins_on_one_blank_line():
    doc = _sample_document()
    text = render_blocks(doc.blocks)
    assert text == (
        "# Title\n\n"
        "## Section one\n\n"
        "First paragraph.\n\n"
        "Second paragraph.\n\n"
        "## Section two\n\n"
        "Third paragraph."
    )
    # render_blocks never adds a trailing newline; that is the emit stage's job.
    assert not text.endswith("\n\n")
