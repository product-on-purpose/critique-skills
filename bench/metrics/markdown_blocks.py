"""The normative block parser (bench/README.md, "The block parser
(normative)"). Used to resolve locations against `markdown-prose` and
`markdown-tree` artifacts.

This is the scoring side of a contract the generator's own
`bench/generator/markdown.py` asserts against at build time by re-parsing
its own rendered output with this same rule (bench/generator/README.md,
"round-trip check"): the two must never disagree about where a paragraph
or heading falls. If this file's behavior ever needs to change, the
generator's copy of the rule needs the same change first.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_FENCE = re.compile(r"^ {0,3}(```|~~~)")
_INDENTED_CODE = re.compile(r"^(?: {4}|\t)")
_ATX_HEADING = re.compile(r"^(#{1,6})(?:\s+(.*?)\s*#*\s*)?$")
_LIST = re.compile(r"^(?:[-*+] |[0-9]+[.)] )")
_BLOCKQUOTE = re.compile(r"^>")
_TABLE_ROW = re.compile(r"^\|")
_HTML_BLOCK = re.compile(r"^<[A-Za-z!/]")
_SETEXT_UNDERLINE = re.compile(r"^(=+|-+)\s*$")
_LEADING_SPACES = re.compile(r"^( {0,3})(.*)$", re.S)


@dataclass(frozen=True, slots=True)
class Block:
    """One block in document order. `line_start` and `line_end` are
    1-based and inclusive. `level` is the heading level (1-6) for a
    heading block and None otherwise; `title` is the heading title
    (leading `#` markers, one following space, and trailing `#` markers
    removed, then trimmed), present only for heading blocks.
    """

    kind: str  # "heading" | "paragraph" | "other"
    line_start: int
    line_end: int
    lines: tuple[str, ...]
    level: int | None = None
    title: str | None = None

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def _classify(lines: tuple[str, ...]) -> tuple[str, int | None, str | None]:
    """Classify a block by its first line, per bench/README.md's rule.
    Indented code is checked against the raw first line, before the "up
    to 3 leading spaces" allowance the other kinds get, because 4 spaces
    (or a tab) is exactly the whitespace that allowance would strip.
    """
    first = lines[0]
    if _INDENTED_CODE.match(first):
        return "other", None, None
    m = _LEADING_SPACES.match(first)
    rest = m.group(2) if m else first
    atx = _ATX_HEADING.match(rest)
    if atx:
        level = len(atx.group(1))
        title = (atx.group(2) or "").strip()
        return "heading", level, title
    if _LIST.match(rest):
        return "other", None, None
    if _BLOCKQUOTE.match(rest):
        return "other", None, None
    if _FENCE.match(first):
        return "other", None, None
    if _TABLE_ROW.match(rest):
        return "other", None, None
    if _HTML_BLOCK.match(rest):
        return "other", None, None
    if len(lines) == 2 and lines[0].strip() and _SETEXT_UNDERLINE.match(lines[1]):
        level = 1 if lines[1].lstrip().startswith("=") else 2
        return "heading", level, lines[0].strip()
    return "paragraph", None, None


def parse_blocks(text: str) -> tuple[Block, ...]:
    """Split `text` into blocks per bench/README.md's normative rule.

    Blocks are maximal runs of non-blank lines separated by blank lines,
    except that a fenced code block (opened by ``` or ~~~, after up to 3
    leading spaces) runs to its closing fence regardless of blank lines
    inside it.
    """
    raw_lines = text.split("\n")
    n = len(raw_lines)
    blocks: list[Block] = []
    i = 0
    while i < n:
        if raw_lines[i].strip() == "":
            i += 1
            continue
        start = i
        if _FENCE.match(raw_lines[i]):
            j = i + 1
            closed_at: int | None = None
            while j < n:
                if _FENCE.match(raw_lines[j]):
                    closed_at = j
                    break
                j += 1
            end = closed_at if closed_at is not None else n - 1
            block_lines = tuple(raw_lines[start:end + 1])
            i = end + 1
        else:
            j = i
            while j < n and raw_lines[j].strip() != "":
                j += 1
            end = j - 1
            block_lines = tuple(raw_lines[start:j])
            i = j
        kind, level, title = _classify(block_lines)
        blocks.append(
            Block(
                kind=kind,
                line_start=start + 1,
                line_end=end + 1,
                lines=block_lines,
                level=level,
                title=title,
            )
        )
    return tuple(blocks)


@dataclass(frozen=True, slots=True)
class Document:
    """A parsed markdown artifact: its blocks, plus the structural queries
    location resolution needs. Block positions (`block_pos`) are indices
    into `self.blocks`; paragraph and section numbers are the 1-based
    document quantities bench/README.md and manifest.schema.json use.
    """

    blocks: tuple[Block, ...]

    def paragraph_positions(self) -> tuple[int, ...]:
        """Block positions of every paragraph block, in document order."""
        return tuple(i for i, b in enumerate(self.blocks) if b.kind == "paragraph")

    def paragraph_index(self, block_pos: int) -> int | None:
        """1-based position of the block at `block_pos` among paragraph
        blocks (manifest.schema.json's `location.paragraph`), or None if
        that block is not a paragraph."""
        if self.blocks[block_pos].kind != "paragraph":
            return None
        return self.paragraph_positions().index(block_pos) + 1

    def heading_positions(self) -> tuple[int, ...]:
        return tuple(i for i, b in enumerate(self.blocks) if b.kind == "heading")

    def level2_headings(self) -> tuple[int, ...]:
        """Block positions of the level-2 headings, in document order:
        "section <n>" means the nth of these (bench/README.md)."""
        return tuple(i for i in self.heading_positions() if self.blocks[i].level == 2)

    def heading_path(self, block_pos: int) -> tuple[str, ...]:
        """Titles of the enclosing headings, outermost first, plus the
        block itself when it is a heading
        (bench/generator/README.md: "enclosing headings, plus the block
        itself when it is a heading")."""
        stack: list[tuple[int, str]] = []
        for i in range(block_pos):
            b = self.blocks[i]
            if b.kind != "heading":
                continue
            while stack and stack[-1][0] >= (b.level or 0):
                stack.pop()
            stack.append((b.level or 0, b.title or ""))
        titles = [title for _, title in stack]
        here = self.blocks[block_pos]
        if here.kind == "heading":
            titles.append(here.title or "")
        return tuple(titles)

    def paragraphs_under(self, heading_pos: int) -> tuple[int, ...]:
        """Block positions of every paragraph under this heading,
        including nested subsections: every paragraph strictly after
        `heading_pos` and before the next heading whose level is <= this
        heading's level."""
        h = self.blocks[heading_pos]
        out: list[int] = []
        for i in range(heading_pos + 1, len(self.blocks)):
            b = self.blocks[i]
            if b.kind == "heading" and (b.level or 0) <= (h.level or 0):
                break
            if b.kind == "paragraph":
                out.append(i)
        return tuple(out)

    def block_at_line(self, line_no: int) -> int | None:
        """Block position whose line span contains `line_no`, or None."""
        for i, b in enumerate(self.blocks):
            if b.line_start <= line_no <= b.line_end:
                return i
        return None


def parse_markdown(text: str) -> Document:
    return Document(parse_blocks(text))
