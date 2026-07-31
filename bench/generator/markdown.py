"""The shared composition model for `markdown-prose` and `markdown-tree`
domains. A domain module supplies vocabulary, shape, and injectors on top of
`Block` and `Document`; it never reinvents a document model of its own. See
`bench/generator/README.md`, "Shared composition models".

Slots are identities; indices are derived. Every `Block` carries a slot id
assigned at creation, and that id never changes. `paragraph_index` and
`heading_path` are computed from the final composition, after every
injection has run, exactly as the README's "two rules that shape everything
else" require.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace as _dc_replace
from typing import Sequence


@dataclass(frozen=True, slots=True)
class Block:
    """One structural unit of a markdown document: a heading or a paragraph.

    `text` is the rendered markdown for this block, including its own `#`
    prefix for a heading. `slot` is the block's permanent identity, assigned
    once at composition time and never renumbered.
    """

    kind: str  # "heading" | "paragraph"
    level: int  # heading level (1, 2, 3, ...); 0 for a paragraph
    text: str
    slot: str


@dataclass(frozen=True, slots=True)
class Document:
    """An ordered, immutable sequence of blocks. Every mutation returns a
    new Document; nothing here is ever changed in place."""

    blocks: tuple[Block, ...]

    def block(self, slot: str) -> Block:
        for b in self.blocks:
            if b.slot == slot:
                return b
        raise KeyError(f"slot not found: {slot!r}")

    def slot_index(self, slot: str) -> int:
        """The block's 0-based position in document order. Used by the
        harness to sort a manifest's defects in document order; not part of
        the domain-facing API a compose/injector function needs."""
        for i, b in enumerate(self.blocks):
            if b.slot == slot:
                return i
        raise KeyError(f"slot not found: {slot!r}")

    def replace(self, slot: str, text: str) -> "Document":
        """Return a new Document with the block at `slot` carrying `text`
        in place of its own. Kind, level, and slot are unchanged: a text
        injector rewrites a block's contents, never its identity or shape."""
        if not any(b.slot == slot for b in self.blocks):
            raise KeyError(f"slot not found: {slot!r}")
        new_blocks = tuple(
            _dc_replace(b, text=text) if b.slot == slot else b for b in self.blocks
        )
        return Document(new_blocks)

    def insert_after_section(self, anchor_slot: str, new_block: Block) -> "Document":
        """Return a new Document with `new_block` inserted at the end of
        the section headed by `anchor_slot`: immediately before the next
        heading of equal or higher rank (lower or equal level number), or
        at the end of the document if `anchor_slot` heads the last section.

        `new_block` carries its own new slot; nothing already in the
        document is renumbered, per the README's "slots are identities"
        rule."""
        blocks = list(self.blocks)
        anchor_index = next(
            (i for i, b in enumerate(blocks) if b.slot == anchor_slot), None
        )
        if anchor_index is None:
            raise KeyError(f"slot not found: {anchor_slot!r}")
        anchor_level = blocks[anchor_index].level
        insert_at = len(blocks)
        for i in range(anchor_index + 1, len(blocks)):
            if blocks[i].kind == "heading" and blocks[i].level <= anchor_level:
                insert_at = i
                break
        blocks.insert(insert_at, new_block)
        return Document(tuple(blocks))


def _heading_title(raw_heading_text: str) -> str:
    """Strip a heading block's leading `#` markers, one following space,
    and any trailing `#` markers, then trim. Matches bench/README.md's
    normative block parser rule for heading-path titles."""
    text = raw_heading_text.lstrip("#")
    if text.startswith(" "):
        text = text[1:]
    return text.rstrip("#").strip()


def heading_path(doc: Document, slot: str) -> tuple[str, ...]:
    """Titles of the enclosing ATX headings, outermost first, plus the
    block itself when it is a heading. Computed by walking the final
    composition in document order and tracking a heading stack keyed by
    level, never by parsing the slot id."""
    doc.block(slot)  # existence check with a clear error; walk finds it again below
    path: list[str] = []
    for b in doc.blocks:
        if b.kind == "heading":
            del path[b.level - 1 :]
            path.append(_heading_title(b.text))
        if b.slot == slot:
            return tuple(path)
    raise AssertionError("unreachable: block() above already confirmed the slot exists")


def paragraph_index(doc: Document, slot: str) -> int:
    """1-based index of the paragraph at `slot` among paragraph blocks in
    document order, counting the whole document, not just its section."""
    count = 0
    for b in doc.blocks:
        if b.kind == "paragraph":
            count += 1
            if b.slot == slot:
                return count
    raise KeyError(f"slot not found or not a paragraph: {slot!r}")


def render_blocks(blocks: Sequence[Block]) -> str:
    """Blocks joined by one blank line. Does not add a trailing newline:
    the harness's emit stage is responsible for the single trailing
    newline every artifact carries, uniformly across artifact types."""
    return "\n\n".join(b.text for b in blocks)
