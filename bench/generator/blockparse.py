"""An independent re-implementation of the normative markdown block parser
documented in `bench/README.md`, "The block parser (normative)".

Used only for the generator's own round-trip check at stage 6 of the
pipeline: re-deriving block structure from the *rendered bytes* and
confirming it agrees with what `bench/generator/markdown.py`'s `Document`
model (built from the in-memory composition) already knows. The two
implementations are deliberately independent, so a bug in one is unlikely
to be mirrored in the other; if they ever disagree, generation fails rather
than publishing a corpus whose ground truth the scorer cannot resolve. The
`bench/metrics` module owns the normative definition for scoring; this
module is the generator's own copy of the rule, used only to check itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParsedBlock:
    """One block as independently re-derived from rendered text."""

    kind: str  # "heading" | "paragraph" | "other"
    level: int  # ATX or setext heading level; 0 for anything else
    title: str | None  # heading title, leading/trailing '#' and space stripped


def _is_blank(line: str) -> bool:
    return line.strip() == ""


def _fence_opener(line: str) -> tuple[str, int] | None:
    """(fence_char, run_length) if `line` opens a fenced code block: up to
    3 leading spaces, then a run of 3 or more backticks or tildes."""
    stripped = line.lstrip(" ")
    if len(line) - len(stripped) > 3:
        return None
    for ch in ("`", "~"):
        if stripped.startswith(ch * 3):
            run = len(stripped) - len(stripped.lstrip(ch))
            return ch, run
    return None


def _closes_fence(line: str, fence_char: str, fence_len: int) -> bool:
    stripped = line.lstrip(" ")
    if len(line) - len(stripped) > 3:
        return False
    if not stripped.startswith(fence_char * fence_len):
        return False
    return stripped.rstrip(fence_char) == ""


def _split_into_raw_blocks(text: str) -> list[list[str]]:
    """Maximal runs of non-blank lines, split on blank lines, except that a
    fenced code block opened at the start of a run absorbs everything
    (blank lines included) up to its closing fence."""
    lines = text.split("\n")
    blocks: list[list[str]] = []
    current: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0

    for line in lines:
        if in_fence:
            current.append(line)
            if _closes_fence(line, fence_char, fence_len):
                in_fence = False
            continue
        if _is_blank(line):
            if current:
                blocks.append(current)
                current = []
            continue
        if not current:
            opener = _fence_opener(line)
            if opener is not None:
                fence_char, fence_len = opener
                in_fence = True
        current.append(line)

    if current:
        blocks.append(current)
    return blocks


_LIST_RE = re.compile(r"^(?:[-*+][ \t]|[0-9]+[.)][ \t])")
_HTML_BLOCK_START_RE = re.compile(r"^<[A-Za-z/!]")


def _atx_heading(stripped_first_line: str) -> tuple[int, str] | None:
    if not stripped_first_line.startswith("#"):
        return None
    hashes = len(stripped_first_line) - len(stripped_first_line.lstrip("#"))
    if hashes < 1 or hashes > 6:
        return None
    rest = stripped_first_line[hashes:]
    if rest and not rest.startswith(" "):
        return None  # "#no-space" is not a heading marker
    title = rest[1:] if rest.startswith(" ") else rest
    return hashes, title.rstrip("#").strip()


def _classify(raw_lines: list[str]) -> ParsedBlock:
    first = raw_lines[0]

    # Indented code: 4 spaces or a tab, checked before any stripping.
    if first.startswith("\t") or first.startswith("    "):
        return ParsedBlock(kind="other", level=0, title=None)

    stripped = first.lstrip(" ")
    leading = len(first) - len(stripped)

    if leading <= 3:
        atx = _atx_heading(stripped)
        if atx is not None:
            level, title = atx
            return ParsedBlock(kind="heading", level=level, title=title)
        if (
            _fence_opener(first) is not None
            or stripped.startswith(">")
            or _LIST_RE.match(stripped)
            or stripped.startswith("|")
            or _HTML_BLOCK_START_RE.match(stripped)
        ):
            return ParsedBlock(kind="other", level=0, title=None)

    # Setext heading: a two-line block whose second line is all '=' or all '-'.
    if len(raw_lines) == 2:
        second = raw_lines[1].strip()
        if second and set(second) == {"="}:
            return ParsedBlock(kind="heading", level=1, title=raw_lines[0].strip())
        if second and set(second) == {"-"}:
            return ParsedBlock(kind="heading", level=2, title=raw_lines[0].strip())

    return ParsedBlock(kind="paragraph", level=0, title=None)


def parse_markdown_blocks(text: str) -> tuple[ParsedBlock, ...]:
    """Independently re-derive block structure from rendered markdown text."""
    return tuple(_classify(raw) for raw in _split_into_raw_blocks(text))


def reparsed_paragraph_index(parsed: tuple[ParsedBlock, ...], position: int) -> int:
    """1-based paragraph index at `position`, counting paragraph blocks in
    document order over the whole reparsed sequence."""
    count = 0
    for i, b in enumerate(parsed):
        if b.kind == "paragraph":
            count += 1
        if i == position:
            if b.kind != "paragraph":
                raise ValueError(f"reparsed position {position} is not a paragraph")
            return count
    raise IndexError(position)


def reparsed_heading_path(parsed: tuple[ParsedBlock, ...], position: int) -> tuple[str, ...]:
    """Enclosing heading titles for `position`, outermost first, plus the
    block itself when it is a heading. Independent of markdown.heading_path:
    walks the reparsed sequence rather than the in-memory Document."""
    path: list[str] = []
    for i, b in enumerate(parsed):
        if b.kind == "heading":
            del path[b.level - 1 :]
            path.append(b.title or "")
        if i == position:
            return tuple(path)
    raise IndexError(position)
