"""Location resolution and tolerance for `markdown-prose` and
`markdown-tree` (bench/README.md, "Location tolerance"). One module for
both artifact types: `markdown-tree` is `markdown-prose` plus the page
check, applied in front (see `is_hit`, `tree=True`).

Resolution is a best-effort regex parse of a finding's free-text location
against the artifact's own structure. Two simplifications are accepted,
each documented at the point it is made, in the spirit of the greedy-vs-
maximum-matching simplification bench/README.md itself names and accepts:
the "fuller path matches as a suffix" clause of the heading-path rule is
not checked beyond the last path element, and a `lines <n>-<m>` anchor
that spans more than one paragraph contributes every paragraph it
touches rather than picking one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from bench.metrics.markdown_blocks import Document
from bench.metrics.ordinals import LAST, WORD_TO_ORDINAL, ordinal_to_int
from bench.metrics.text_util import normalize_heading, normalize_loose

_PARA_NUM = re.compile(r"\b(?:paragraph|para)\s+(\d+)\b", re.IGNORECASE)
_PARA_ORD_AFTER = re.compile(r"\b(?:paragraph|para)\s+([A-Za-z]+)\b", re.IGNORECASE)
_ORD_PARA_BEFORE = re.compile(r"\b([A-Za-z]+)\s+paragraph\b", re.IGNORECASE)
_LINE_RANGE = re.compile(r"\blines\s+(\d+)\s*-\s*(\d+)\b", re.IGNORECASE)
_LINE_SINGLE = re.compile(r"\bline\s+(\d+)\b", re.IGNORECASE)
_SECTION_NUM = re.compile(r"\bsection\s+(\d+)\b", re.IGNORECASE)
_QUOTED = re.compile(r"[`\"“]([^`\"”]{1,200})[`\"”]")
_MD_PATH = re.compile(r"\b[\w][\w./-]*?\.md\b", re.IGNORECASE)


def _extract_paragraph_request(text: str) -> int | str | None:
    """An explicit paragraph number, or a recognized ordinal word
    (including "last"), or None. Ordinal-looking words that are not in
    the frozen table are ignored rather than mistaken for one, so "the
    meter paragraph" does not falsely resolve."""
    m = _PARA_NUM.search(text)
    if m:
        return int(m.group(1))
    for pattern in (_PARA_ORD_AFTER, _ORD_PARA_BEFORE):
        m = pattern.search(text)
        if m:
            word = m.group(1).lower()
            if word in WORD_TO_ORDINAL or word == LAST:
                return word
    return None


def _extract_line_paragraphs(text: str, doc: Document) -> set[int] | None:
    """Block positions of the paragraph(s) a `line <n>` or `lines <n>-<m>`
    anchor falls in, or None when no line anchor is present at all (as
    opposed to an empty set, which means a line anchor was present but
    named no paragraph, for example a line inside a heading)."""
    m = _LINE_RANGE.search(text)
    if m:
        lo, hi = sorted((int(m.group(1)), int(m.group(2))))
        out = set()
        for ln in range(lo, hi + 1):
            pos = doc.block_at_line(ln)
            if pos is not None and doc.blocks[pos].kind == "paragraph":
                out.add(pos)
        return out
    m = _LINE_SINGLE.search(text)
    if m:
        pos = doc.block_at_line(int(m.group(1)))
        if pos is not None and doc.blocks[pos].kind == "paragraph":
            return {pos}
        return set()
    return None


def _extract_section_number(text: str) -> int | None:
    m = _SECTION_NUM.search(text)
    return int(m.group(1)) if m else None


def _extract_section_title(text: str, doc: Document) -> int | None:
    """Block position of the heading named by title, or None. Tries a
    backticked or quoted exact title first, then the longest heading
    title of at least 4 characters appearing as a substring of the
    location text, per bench/README.md."""
    headings = doc.heading_positions()
    if not headings:
        return None
    for qm in _QUOTED.finditer(text):
        candidate = normalize_heading(qm.group(1))
        matches = [i for i in headings if normalize_heading(doc.blocks[i].title or "") == candidate]
        if len(matches) == 1:
            return matches[0]
    norm_text = normalize_loose(text)
    by_title: dict[str, list[int]] = {}
    for i in headings:
        title_norm = normalize_heading(doc.blocks[i].title or "")
        if len(title_norm) < 4:
            continue
        if title_norm in norm_text:
            by_title.setdefault(title_norm, []).append(i)
    if not by_title:
        return None
    best = max(by_title, key=len)
    matches = by_title[best]
    return matches[0] if len(matches) == 1 else None


def _resolve_section(text: str, doc: Document) -> int | None:
    n = _extract_section_number(text)
    if n is not None:
        level2 = doc.level2_headings()
        return level2[n - 1] if 1 <= n <= len(level2) else None
    return _extract_section_title(text, doc)


def _resolve_ordinal_or_int(request: int | str, total: int) -> int | None:
    if isinstance(request, int):
        return request if 1 <= request <= total else None
    return ordinal_to_int(request, total=total)


def _extract_page_anchor(text: str) -> str | None:
    m = _MD_PATH.search(text.replace("\\", "/"))
    return m.group(0).lower() if m else None


def page_matches(text: str, own_artifact_path: str) -> bool | None:
    """True when `text` names `own_artifact_path` as a page anchor, False
    when it names a different page, None when it names no page at all
    (bench/README.md, "`markdown-tree` adds one step in front...")."""
    anchor = _extract_page_anchor(text)
    if anchor is None:
        return None
    own = own_artifact_path.replace("\\", "/").lower()
    own_stem = own[:-3] if own.endswith(".md") else own
    anchor_stem = anchor[:-3] if anchor.endswith(".md") else anchor
    return anchor == own or anchor_stem == own_stem or own.endswith("/" + anchor) or anchor == f"{own_stem}.md"


@dataclass(frozen=True, slots=True)
class ResolvedMdLocation:
    """The result of resolving one finding's free-text location against
    one markdown document.

    `paragraph_window` is the set of paragraph indices a truth of kind
    `paragraph` is credited against. `paragraph_exact` is the single
    definite paragraph a paragraph or line anchor resolved to, before
    windowing; None when only a section resolved, or when nothing did.
    `section_block` / `section_title_norm` describe the resolved section
    heading, if any. `page_anchor` is only meaningful for
    `markdown-tree`: True (names this page), False (names another page),
    or None (names no page).
    """

    resolvable: bool
    paragraph_window: frozenset[int] = frozenset()
    paragraph_exact: int | None = None
    section_block: int | None = None
    section_title_norm: str | None = None
    page_anchor: bool | None = None
    canonical_key: str = "?:"


def resolve(
    doc: Document,
    location_text: str,
    *,
    tree: bool = False,
    own_artifact_path: str | None = None,
) -> ResolvedMdLocation:
    page_anchor = page_matches(location_text, own_artifact_path) if (tree and own_artifact_path) else None
    section_pos = _resolve_section(location_text, doc)
    para_request = _extract_paragraph_request(location_text)
    line_paragraphs = _extract_line_paragraphs(location_text, doc)

    under_para_nums: list[int] = []
    if section_pos is not None:
        under_para_nums = [
            n for pos in doc.paragraphs_under(section_pos) if (n := doc.paragraph_index(pos)) is not None
        ]

    raw_window: set[int] = set()
    paragraph_exact: int | None = None
    had_direct_anchor = False

    if para_request is not None:
        had_direct_anchor = True
        if section_pos is not None:
            idx = _resolve_ordinal_or_int(para_request, len(under_para_nums))
            if idx is not None:
                p = under_para_nums[idx - 1]
                raw_window |= {p - 1, p, p + 1}
                paragraph_exact = p
        else:
            p = _resolve_ordinal_or_int(para_request, len(doc.paragraph_positions()))
            if p is not None:
                raw_window |= {p - 1, p, p + 1}
                paragraph_exact = p

    if line_paragraphs:
        had_direct_anchor = True
        line_ps = [n for pos in line_paragraphs if (n := doc.paragraph_index(pos)) is not None]
        for p in line_ps:
            raw_window |= {p - 1, p, p + 1}
        if paragraph_exact is None and len(line_ps) == 1:
            paragraph_exact = line_ps[0]

    if section_pos is not None:
        paragraph_window = raw_window & set(under_para_nums) if had_direct_anchor else set(under_para_nums)
    else:
        paragraph_window = raw_window

    resolvable = bool(paragraph_window) or section_pos is not None
    section_title_norm = (
        normalize_heading(doc.blocks[section_pos].title or "") if section_pos is not None else None
    )

    if paragraph_exact is not None:
        canonical_key = str(paragraph_exact)
    elif section_title_norm is not None:
        canonical_key = "H:" + section_title_norm
    else:
        canonical_key = "?:" + normalize_loose(location_text)

    return ResolvedMdLocation(
        resolvable=resolvable,
        paragraph_window=frozenset(x for x in paragraph_window if x >= 1),
        paragraph_exact=paragraph_exact,
        section_block=section_pos,
        section_title_norm=section_title_norm,
        page_anchor=page_anchor,
        canonical_key=canonical_key,
    )


def _is_hit_paragraph(resolved: ResolvedMdLocation, truth_paragraph: int) -> bool:
    return truth_paragraph in resolved.paragraph_window


def _is_hit_heading_path(doc: Document, resolved: ResolvedMdLocation, truth_heading_path: list[str]) -> bool:
    """bench/README.md: "HIT if the finding resolves a section anchor
    whose normalized title equals the last element of
    `truth.heading_path` ..., or if the finding resolves a paragraph
    index whose block is immediately before or immediately after the
    heading in block order." The "fuller path matches as a suffix"
    clause is accepted but not independently checked here: a location
    resolver working from free text has no way to observe more than the
    one heading title a finding names, so a title match is treated as
    sufficient on its own, a documented simplification.
    """
    truth_last = normalize_heading(truth_heading_path[-1])
    if resolved.section_title_norm is not None and resolved.section_title_norm == truth_last:
        return True
    if resolved.paragraph_window:
        heading_positions = [
            i for i in doc.heading_positions() if normalize_heading(doc.blocks[i].title or "") == truth_last
        ]
        for hp in heading_positions:
            neighbors = []
            if hp - 1 >= 0 and doc.blocks[hp - 1].kind == "paragraph":
                neighbors.append(doc.paragraph_index(hp - 1))
            if hp + 1 < len(doc.blocks) and doc.blocks[hp + 1].kind == "paragraph":
                neighbors.append(doc.paragraph_index(hp + 1))
            if any(n is not None and n in resolved.paragraph_window for n in neighbors):
                return True
    return False


def is_hit(doc: Document, resolved: ResolvedMdLocation, truth: dict, *, tree: bool) -> bool:
    kind = truth["kind"]
    if tree:
        if kind == "page-path":
            return resolved.page_anchor is True
        if resolved.page_anchor is False:
            return False
    if kind == "paragraph":
        return _is_hit_paragraph(resolved, truth["paragraph"])
    if kind == "heading-path":
        return _is_hit_heading_path(doc, resolved, truth["heading_path"])
    return False


def self_match(a: ResolvedMdLocation, b: ResolvedMdLocation) -> bool:
    """Whether two *findings'* resolved locations name the same place
    (used for consistency, where there is no manifest truth to compare
    against, only two claims). Reciprocal: either side's exact paragraph
    falling in the other's window counts, so the check does not depend on
    which claim is passed first."""
    if a.paragraph_exact is not None and a.paragraph_exact in b.paragraph_window:
        return True
    if b.paragraph_exact is not None and b.paragraph_exact in a.paragraph_window:
        return True
    if a.section_title_norm is not None and a.section_title_norm == b.section_title_norm:
        return True
    if not a.resolvable and not b.resolvable:
        return a.canonical_key == b.canonical_key
    return False
