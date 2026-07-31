"""critique-usability scripted lane: NNG-H3-DEADEND, NNG-H4-CONTROL-NAMING,
NNG-H6-LABELED.

This skill's artifact claim is HTML or markdown UI specs and page mockups
(SKILL.md, "Artifact claim"). This module tells the two formats apart with
one heuristic, `_looks_like_html`: the artifact is HTML when its first
non-whitespace character is "<", markdown otherwise.

Each of the three scripted criteria needs a structural notion of "screen or
state" and "control" that neither format states explicitly, so this module
owns a small, documented grammar for each, the same way
bench/generator/README.md's toy domain owns the grammar its injectors
invert ("Transforms operate on a grammar you own"). An artifact that does
not use these conventions produces no finding for the criterion that needs
them, never a guessed one; the judged lane, run inline or by the critic
subagent, covers what the scripted lane cannot see.

HTML conventions (matching the "<section id=...>" shape already used by
this repository's own HTML test fixtures, bench/metrics/tests/
test_resolve_html.py):

  - A **state** is any `<section>` element that carries a non-empty `id`.
  - An **edge** out of a state is an `<a href="#target-id">` inside that
    section, whose target names another defined state's id. A link
    pointing at its own enclosing state's id is not an edge: it cannot be
    how a user leaves that state.
  - The dead-end sweep only runs when the artifact defines two or more
    states. One `<section id=...>` wrapping an entire single-screen mockup
    is not a multi-state flow with an exitless screen; it is one screen,
    and flagging it would be a false positive on an extremely common,
    perfectly ordinary page shape.
  - **Control labels** (NNG-H4-CONTROL-NAMING) come from `<button>` text,
    `<a href>` text, `<input type="submit"|"button"|"reset">` `value`, and
    an element carrying `role="menuitem"` with no nested `<a>`/`<button>`
    (so a menu item built from a plain link is not counted twice).
  - **NNG-H6-LABELED** checks two kinds of control. A generic interactive
    element (`<button>`, an `<a>` with an `href`, or `role="button"`,
    `"link"`, or `"menuitem"`) is unnamed when it has neither text content
    nor an `aria-label`, `aria-labelledby`, or `title` attribute. A field
    (`<input>` other than type hidden/submit/button/reset/image, `<select>`,
    `<textarea>`) is unnamed when it has no associated `<label>` that
    itself carries text, whether by wrapping or by a matching `for`/`id`
    pair; an `aria-label` alone does not save a field from this stricter
    test, matching the severity-3 anchor in references/NNG-HEURISTICS.md
    ("only placeholder text, so ... nothing on screen names what any field
    holds"). Alt text on a wrapped `<img>` is deliberately not read as an
    accessible name here: whether AT can reach a name is
    critique-accessibility's claim (WCAG-*), not this skill's ("Boundaries
    with sibling skills" in references/NNG-HEURISTICS.md).

Markdown conventions:

  - A **state** is a level-2 (`##`) heading; its id is a GitHub-style slug
    of the heading text, collision-suffixed exactly as GitHub numbers
    repeated headings (`foo`, `foo-1`, `foo-2`, ...). A state's content
    runs from just after its heading to the next `##` heading (or the end
    of the document), so a `###` subsection belongs to its enclosing `##`
    state.
  - An **edge** is a markdown link `[text](#slug)` inside a state's content
    whose slug names another defined state.
  - **Control labels** are the text of every markdown link `[text](...)`
    in the document, any target, since markdown draws no syntactic line
    between a button and a link.
  - **NNG-H6-LABELED**'s "spec list entry that names a control by role
    alone" is read from a bullet or numbered list whose nearest preceding
    heading (any level) contains the word "control" or "field". An item in
    such a list is unnamed when, after stripping markdown emphasis markers
    and a leading article and a trailing "control"/"field" word, its text
    is exactly one bare role noun (button, link, icon, field, toggle,
    checkbox, menu, control, input, dropdown, tab) with no name of its own
    attached. "Save button" keeps its name and passes; "Button" and "The
    toggle control" do not.

Severities for all three criteria are fixed by rule, per
references/severity-anchors.md, "Fixed severities for the scripted lane";
this module computes them, it does not invent its own scale. Locations
name the enclosing state (when one exists) and the control inside it, per
SKILL.md's "Contract" section.
"""

from __future__ import annotations

import html.parser
import re
import string
import sys
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills._shared.runner import run_scripted_lane
from skills._shared.findings import RawFinding

# Every criterion this scripted lane checks. Cross-checked against
# SKILL.md's checks.scripted by scripts/skill-selftest.py; the two must
# name exactly the same set.
IMPLEMENTED_CRITERIA = frozenset({"NNG-H3-DEADEND", "NNG-H4-CONTROL-NAMING", "NNG-H6-LABELED"})


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------


def _looks_like_html(text):
    """The artifact is HTML when its first non-whitespace character opens a
    tag. A markdown document that opens with a raw HTML block is the one
    case this misreads; documented here rather than hidden."""
    return text.lstrip().startswith("<")


# ---------------------------------------------------------------------------
# HTML parsing: a minimal element tree over the stdlib html.parser
# ---------------------------------------------------------------------------

_VOID_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
})


class _Node:
    """One element. `children` holds a document-order mix of `_Node` and
    `str` (raw text), which is what lets `text()` walk descendants in
    reading order without a second pass."""

    __slots__ = ("tag", "attrs", "parent", "children")

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.children = []

    def text(self):
        parts = []

        def walk(node):
            for child in node.children:
                if isinstance(child, str):
                    parts.append(child)
                else:
                    walk(child)

        walk(self)
        return re.sub(r"\s+", " ", "".join(parts)).strip()


class _TreeBuilder(html.parser.HTMLParser):
    """Tolerant of unbalanced or malformed markup, which real hand-authored
    mockups routinely are: an unmatched end tag is ignored rather than
    raising, and a void element is never pushed onto the open-element
    stack, so it never waits for a closing tag that will never arrive."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("#root", {}, None)
        self._stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, dict(attrs), self._stack[-1])
        self._stack[-1].children.append(node)
        if tag not in _VOID_ELEMENTS:
            self._stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self._stack) - 1, 0, -1):
            if self._stack[i].tag == tag:
                del self._stack[i:]
                return
        # No matching open tag on the stack: ignore rather than raise.

    def handle_data(self, data):
        if data:
            self._stack[-1].children.append(data)


def _parse_html(text):
    builder = _TreeBuilder()
    builder.feed(text)
    builder.close()
    return builder.root


def _iter_elements(root):
    """Every element under `root`, in document order."""
    result = []

    def walk(node):
        for child in node.children:
            if isinstance(child, _Node):
                result.append(child)
                walk(child)

    walk(root)
    return result


def _nearest_ancestor(node, predicate):
    cur = node.parent
    while cur is not None and cur.tag != "#root":
        if predicate(cur):
            return cur
        cur = cur.parent
    return None


def _is_named_section(node):
    return node.tag == "section" and bool((node.attrs.get("id") or "").strip())


def _collect_sections(elements):
    """id -> the first `<section id=...>` node with that id, in document
    order. A duplicate id is invalid HTML; the first occurrence wins
    rather than raising, so a sloppy artifact still gets a usable graph."""
    sections = {}
    for node in elements:
        if _is_named_section(node):
            sid = node.attrs["id"].strip()
            if sid not in sections:
                sections[sid] = node
    return sections


_ORDINAL_WORDS = (
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
    "eighth", "ninth", "tenth", "eleventh", "twelfth", "thirteenth",
    "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth",
    "nineteenth", "twentieth",
)


def _ordinal_word(n):
    if 1 <= n <= len(_ORDINAL_WORDS):
        return _ORDINAL_WORDS[n - 1]
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


# The bench's own "element by kind and ordinal" noun table (bench/README.md,
# "Location tolerance", the html resolution table), reused here so a
# location this module writes is phrased the way the family's own resolver
# already expects to read.
_TAG_NOUNS = {
    "a": "link", "img": "image", "button": "button", "input": "field",
    "select": "field", "textarea": "field", "table": "table",
    "ul": "list", "ol": "list",
    "h1": "heading", "h2": "heading", "h3": "heading", "h4": "heading",
    "h5": "heading", "h6": "heading",
}


def _element_descriptor(node, elements):
    noun = _TAG_NOUNS.get(node.tag, node.tag)
    node_id = (node.attrs.get("id") or "").strip()
    if node_id:
        return f'the "{node_id}" {noun}'
    index = 0
    for el in elements:
        if el.tag == node.tag:
            index += 1
            if el is node:
                break
    return f"the {_ordinal_word(index)} {noun}"


def _control_location_html(node, elements):
    enclosing = _nearest_ancestor(node, _is_named_section)
    descriptor = _element_descriptor(node, elements)
    if enclosing is not None:
        section_id = enclosing.attrs["id"].strip()
        return f'the "{section_id}" section, {descriptor}'
    return descriptor


def _has_descendant_tag(node, tags):
    for child in node.children:
        if isinstance(child, _Node):
            if child.tag in tags or _has_descendant_tag(child, tags):
                return True
    return False


# ---------------------------------------------------------------------------
# Markdown parsing: headings, paragraphs, and bullet/numbered lists
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]*)\)")


def _parse_markdown_blocks(text):
    """Headings (ATX only), bullet/numbered lists (single-line items only),
    and paragraphs (contiguous non-blank, non-heading, non-list lines,
    joined with a single space). Scoped narrowly on purpose, the same way
    the toy and argument domains' own block parsers are
    (docs/internal/skill-template.md, "Wiring scripts/checks.py")."""
    blocks = []
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            blocks.append({
                "kind": "heading",
                "level": len(heading_match.group(1)),
                "text": heading_match.group(2).strip(),
            })
            i += 1
            continue
        if _LIST_ITEM_RE.match(line):
            items = []
            while i < n and _LIST_ITEM_RE.match(lines[i]):
                items.append({"text": _LIST_ITEM_RE.match(lines[i]).group(1).strip()})
                i += 1
            blocks.append({"kind": "list", "items": items})
            continue
        para_lines = []
        while i < n and lines[i].strip() and not _HEADING_RE.match(lines[i]) and not _LIST_ITEM_RE.match(lines[i]):
            para_lines.append(lines[i])
            i += 1
        blocks.append({"kind": "paragraph", "text": " ".join(para_lines).strip()})
    return blocks


def _block_texts(block):
    if block["kind"] == "paragraph":
        return [block["text"]]
    if block["kind"] == "list":
        return [item["text"] for item in block["items"]]
    if block["kind"] == "heading":
        return [block["text"]]
    return []


def _strip_markdown_emphasis(text):
    return re.sub(r"[*_`]", "", text)


def _slugify(text, counts):
    """GitHub's own heading-anchor algorithm: lowercase, drop everything
    but word characters/whitespace/hyphen, spaces to hyphens, collapse
    repeats. A repeated heading gets `-1`, `-2`, ... exactly as GitHub
    numbers them, so a link written the way an author would naturally
    write it against a real GitHub-flavoured heading still resolves."""
    base = re.sub(r"[^\w\s-]", "", text.strip().lower())
    base = re.sub(r"\s+", "-", base).strip("-")
    base = re.sub(r"-{2,}", "-", base)
    if not base:
        base = "section"
    n = counts.get(base, 0)
    counts[base] = n + 1
    return base if n == 0 else f"{base}-{n}"


def _markdown_states(blocks):
    """slug -> {label, block_index} for every level-2 heading, in document
    order."""
    states = {}
    counts = {}
    for i, block in enumerate(blocks):
        if block["kind"] == "heading" and block["level"] == 2:
            slug = _slugify(block["text"], counts)
            states[slug] = {"label": block["text"], "block_index": i}
    return states


def _markdown_state_ranges(blocks, states):
    """[(slug, start, end), ...]: the half-open block-index range each
    state's own content spans, up to (not including) the next level-2
    heading, so a level-3+ subsection's blocks belong to their enclosing
    state."""
    ordered = sorted(states.items(), key=lambda kv: kv[1]["block_index"])
    ranges = []
    for i, (slug, info) in enumerate(ordered):
        start = info["block_index"] + 1
        end = ordered[i + 1][1]["block_index"] if i + 1 < len(ordered) else len(blocks)
        ranges.append((slug, start, end))
    return ranges


# ---------------------------------------------------------------------------
# Shared: turn a list of (location, evidence) occurrences of one breach
# into contract-valid RawFindings.
# ---------------------------------------------------------------------------


def _findings_from_occurrences(*, criterion, severity, violation, fix, occurrences):
    """`occurrences`: (location, evidence) pairs for every place this one
    breach appears, in a deterministic order; the first is the
    representative. The contract's `instances` array requires at least two
    entries (contract/critique-contract.schema.json, $defs/finding,
    "instances"), so an instance list can only carry a breach's 2nd, 3rd,
    ... occurrence when there are at least 3 in total; with exactly 2 this
    returns two separate findings instead, which is the contract's other
    sanctioned shape for the same case ("Use either one finding per
    instance or one finding with an instance list, never both for the same
    occurrences"). Exact (location, evidence) duplicates are collapsed
    first, so a malformed artifact with colliding ids can never produce a
    duplicate `instances` entry, which the schema's `uniqueItems` would
    reject.
    """
    deduped = []
    seen = set()
    for location, evidence in occurrences:
        key = (location, evidence)
        if key in seen:
            continue
        seen.add(key)
        deduped.append((location, evidence))

    if not deduped:
        return []
    if len(deduped) == 1:
        location, evidence = deduped[0]
        return [RawFinding(criterion=criterion, severity=severity, location=location,
                            evidence=evidence, violation=violation, fix=fix)]
    if len(deduped) == 2:
        return [
            RawFinding(criterion=criterion, severity=severity, location=loc,
                       evidence=ev, violation=violation, fix=fix)
            for loc, ev in deduped
        ]
    representative_location, representative_evidence = deduped[0]
    instances = tuple({"location": loc, "evidence": ev} for loc, ev in deduped[1:])
    return [RawFinding(criterion=criterion, severity=severity, location=representative_location,
                        evidence=representative_evidence, violation=violation, fix=fix,
                        instances=instances)]


# ---------------------------------------------------------------------------
# NNG-H3-DEADEND
# ---------------------------------------------------------------------------


def _check_deadend_html(elements, sections):
    if len(sections) < 2:
        return []  # not a multi-state flow; nothing to walk a graph over

    outgoing = {sid: 0 for sid in sections}
    incoming = {sid: 0 for sid in sections}
    for node in elements:
        if node.tag != "a":
            continue
        href = (node.attrs.get("href") or "").strip()
        if not href.startswith("#") or len(href) <= 1:
            continue
        target = href[1:]
        if target not in sections:
            continue
        enclosing = _nearest_ancestor(node, _is_named_section)
        if enclosing is None:
            continue
        src = (enclosing.attrs.get("id") or "").strip()
        if not src or src == target:
            continue  # a link to the state's own id does not let a user leave it
        outgoing[src] = outgoing.get(src, 0) + 1
        incoming[target] += 1

    findings = []
    for sid, node in sections.items():
        if outgoing.get(sid, 0) > 0:
            continue
        severity = 3 if incoming[sid] > 0 else 2
        findings.append(RawFinding(
            criterion="NNG-H3-DEADEND",
            severity=severity,
            location=f'the "{sid}" section',
            evidence=(
                f'the "{sid}" section defines 0 controls whose target names another defined '
                f'state ({incoming[sid]} incoming link{"s" if incoming[sid] != 1 else ""} from '
                "elsewhere in the artifact)."
            ),
            violation=(
                "This state offers no control whose target names another state the artifact "
                "defines, so a user who reaches it has no path to leave it within the artifact."
            ),
            fix=(
                f'Add a control inside the "{sid}" section whose target is another state the '
                "artifact defines, for example a back, cancel, or continue control."
            ),
        ))
    return findings


def _check_deadend_markdown(blocks, states):
    if len(states) < 2:
        return []

    ranges = _markdown_state_ranges(blocks, states)
    outgoing = {slug: 0 for slug in states}
    incoming = {slug: 0 for slug in states}
    for slug, start, end in ranges:
        for block in blocks[start:end]:
            for text in _block_texts(block):
                for match in _MD_LINK_RE.finditer(text):
                    target_raw = match.group(2).strip()
                    if not target_raw.startswith("#"):
                        continue
                    target = target_raw[1:]
                    if target not in states or target == slug:
                        continue
                    outgoing[slug] += 1
                    incoming[target] += 1

    findings = []
    for slug, info in states.items():
        if outgoing[slug] > 0:
            continue
        severity = 3 if incoming[slug] > 0 else 2
        label = info["label"]
        findings.append(RawFinding(
            criterion="NNG-H3-DEADEND",
            severity=severity,
            location=f'the "{label}" state',
            evidence=(
                f'the "{label}" state defines 0 links to another defined state '
                f'({incoming[slug]} incoming link{"s" if incoming[slug] != 1 else ""} from '
                "elsewhere in the document)."
            ),
            violation=(
                "This state offers no link whose target names another state the artifact "
                "defines, so a user who reaches it has no path to leave it within the artifact."
            ),
            fix=(
                f'Add a link inside the "{label}" section whose target is another state the '
                "artifact defines, for example a back, cancel, or continue link."
            ),
        ))
    return findings


# ---------------------------------------------------------------------------
# NNG-H4-CONTROL-NAMING
# ---------------------------------------------------------------------------

# The three fixed synonym sets referenced by references/NNG-HEURISTICS.md's
# own operational test for this criterion ("the fixed synonym sets held in
# scripts/checks.py"), one per recurring action class.
COMMIT_SYNONYMS = ("Save", "Save changes", "Apply", "Apply changes", "Submit", "Confirm", "Update", "Done")
CANCEL_SYNONYMS = ("Cancel", "Dismiss", "Close", "Discard", "Discard changes", "Never mind", "No thanks")
BACK_SYNONYMS = ("Back", "Previous", "Go back", "Return")

_SYNONYM_SETS = (
    ("commit", COMMIT_SYNONYMS),
    ("cancel", CANCEL_SYNONYMS),
    ("back", BACK_SYNONYMS),
)

_ELLIPSIS_RE = re.compile(r"(?:\.\.\.|…)\s*$")
_LABEL_STRIP_CHARS = string.punctuation + " \t\r\n“”‘’"


def _canonicalize_label(text):
    """Case-insensitive, ignoring surrounding punctuation and a trailing
    ellipsis, per NNG-HEURISTICS.md's own operational test for this
    criterion."""
    t = text.strip()
    t = _ELLIPSIS_RE.sub("", t).strip()
    t = t.strip(_LABEL_STRIP_CHARS)
    t = re.sub(r"\s+", " ", t)
    return t.casefold()


_SYNONYM_LOOKUP = {}
for _set_name, _members in _SYNONYM_SETS:
    for _member in _members:
        _canon = _canonicalize_label(_member)
        assert _canon not in _SYNONYM_LOOKUP, f"duplicate synonym across NNG-H4-CONTROL-NAMING sets: {_member}"
        _SYNONYM_LOOKUP[_canon] = _set_name


def _extract_control_labels_html(elements):
    """(raw_label, location, evidence) for every button, link, submit-like
    input, and stand-alone menu item in the artifact, in document order."""
    occurrences = []
    for node in elements:
        raw = None
        if node.tag == "button":
            raw = node.text()
        elif node.tag == "a":
            if (node.attrs.get("href") or "").strip():
                raw = node.text()
        elif node.tag == "input":
            itype = (node.attrs.get("type") or "").strip().lower()
            if itype in ("submit", "button", "reset"):
                raw = (node.attrs.get("value") or "").strip()
        else:
            role = (node.attrs.get("role") or "").strip().lower()
            if role == "menuitem" and not _has_descendant_tag(node, ("a", "button")):
                raw = node.text()
        if not raw:
            continue
        location = _control_location_html(node, elements)
        evidence = f'control labeled "{raw}"'
        occurrences.append((raw, location, evidence))
    return occurrences


def _extract_control_labels_markdown(blocks):
    """(raw_label, location, evidence) for every markdown link's text, in
    document order. Locations carry a running occurrence number: two links
    with the same text under the same heading would otherwise produce the
    identical location string, which the shared occurrence-dedup step in
    `_findings_from_occurrences` would then collapse into one, silently
    dropping a real, distinct occurrence."""
    occurrences = []
    current_heading = None
    counter = 0
    for block in blocks:
        if block["kind"] == "heading":
            current_heading = block["text"]
            continue
        for text in _block_texts(block):
            for match in _MD_LINK_RE.finditer(text):
                label = _strip_markdown_emphasis(match.group(1)).strip()
                if not label:
                    continue
                counter += 1
                if current_heading:
                    location = f'the "{current_heading}" section, the "{label}" link, occurrence {counter}'
                else:
                    location = f'the "{label}" link, occurrence {counter}'
                evidence = f'link labeled "{label}"'
                occurrences.append((label, location, evidence))
    return occurrences


def _control_naming_findings(occurrences):
    """`occurrences`: (raw_label, location, evidence) in document order.
    One finding per synonym set in which two or more distinct members
    appear, listing every matching occurrence."""
    by_set = {"commit": [], "cancel": [], "back": []}
    for raw_label, location, evidence in occurrences:
        canon = _canonicalize_label(raw_label)
        set_name = _SYNONYM_LOOKUP.get(canon)
        if set_name is not None:
            by_set[set_name].append((canon, raw_label.strip(), location, evidence))

    findings = []
    for set_name in ("commit", "cancel", "back"):
        entries = by_set[set_name]
        display_by_canon = {}
        for canon, raw_label, _location, _evidence in entries:
            display_by_canon.setdefault(canon, raw_label)
        distinct = sorted(display_by_canon)
        if len(distinct) < 2:
            continue
        severity = 3 if len(distinct) >= 3 else 2
        display_forms = [display_by_canon[c] for c in distinct]
        quoted = ", ".join(f'"{d}"' for d in display_forms)
        violation = (
            f"This artifact uses {len(distinct)} different labels for what reads as the same "
            f"{set_name} action: {quoted}. A user cannot tell from the label alone whether "
            "these controls perform the same action or different ones."
        )
        fix = (
            f'Pick one label for this {set_name} action, for example "{display_forms[0]}", and '
            "use it everywhere the action appears."
        )
        occ = [(location, evidence) for _canon, _raw, location, evidence in entries]
        findings.extend(_findings_from_occurrences(
            criterion="NNG-H4-CONTROL-NAMING",
            severity=severity,
            violation=violation,
            fix=fix,
            occurrences=occ,
        ))
    return findings


# ---------------------------------------------------------------------------
# NNG-H6-LABELED
# ---------------------------------------------------------------------------

_FIELD_TAGS = ("input", "select", "textarea")
_NON_FIELD_INPUT_TYPES = ("hidden", "submit", "button", "reset", "image")
_CONTAINER_TAGS = ("form", "nav")
_CONTAINER_ROLES = ("toolbar", "menu", "menubar")


def _is_generic_interactive(node):
    if node.tag == "a":
        return bool((node.attrs.get("href") or "").strip())
    if node.tag == "button":
        return True
    role = (node.attrs.get("role") or "").strip().lower()
    return role in ("button", "link", "menuitem")


def _has_accessible_name(node):
    for attr in ("aria-label", "aria-labelledby", "title"):
        if (node.attrs.get(attr) or "").strip():
            return True
    return False


def _is_field(node):
    if node.tag not in _FIELD_TAGS:
        return False
    if node.tag == "input":
        itype = (node.attrs.get("type") or "text").strip().lower()
        if itype in _NON_FIELD_INPUT_TYPES:
            return False
    return True


def _label_text_by_for_id(elements):
    mapping = {}
    for node in elements:
        if node.tag == "label":
            for_id = (node.attrs.get("for") or "").strip()
            if for_id:
                text = node.text()
                if text:
                    mapping[for_id] = text
    return mapping


def _has_associated_label(node, label_text_by_for_id):
    """True only when the associated `<label>` itself carries text: a
    field wrapped in, or paired via for/id with, an empty `<label>` is not
    meaningfully named on screen either."""
    node_id = (node.attrs.get("id") or "").strip()
    if node_id and label_text_by_for_id.get(node_id):
        return True
    wrapping = _nearest_ancestor(node, lambda n: n.tag == "label")
    return wrapping is not None and bool(wrapping.text())


def _nearest_container(node):
    return _nearest_ancestor(
        node,
        lambda n: n.tag in _CONTAINER_TAGS or (n.attrs.get("role") or "").strip().lower() in _CONTAINER_ROLES,
    )


def _control_signature(node):
    """A cheap proxy for "the same control repeating": identical tag,
    class list, input type, and role. Two controls sharing a signature are
    treated as instances of one repeated component (an icon-only delete
    button on every row of a list, say); two controls that differ in any
    of these are different controls and get their own findings."""
    classes = tuple(sorted((node.attrs.get("class") or "").split()))
    itype = (node.attrs.get("type") or "").strip().lower() if node.tag == "input" else ""
    role = (node.attrs.get("role") or "").strip().lower()
    return (node.tag, classes, itype, role)


def _labeled_violation_html(node):
    if _is_field(node):
        return (
            "This field has no associated label element, so nothing on screen names what the "
            "field holds once the user starts entering a value."
        )
    return (
        "This control has neither visible text nor an accessible-name attribute, so nothing on "
        "screen names what the control does."
    )


def _labeled_fix_html(node):
    if _is_field(node):
        return "Add a label element associated with this field, either wrapping it or paired by a matching for and id attribute."
    return "Add visible text to this control, or an aria-label attribute naming what it does."


def _labeled_evidence_html(node):
    if _is_field(node):
        return f"<{node.tag}> with no associated label element carrying text"
    return f"<{node.tag}> with no text content and no accessible-name attribute"


def _check_labeled_html(elements):
    label_text_by_for_id = _label_text_by_for_id(elements)

    candidates = []
    for node in elements:
        if _is_generic_interactive(node):
            named = bool(node.text()) or _has_accessible_name(node)
            candidates.append((node, named))
        elif _is_field(node):
            named = _has_associated_label(node, label_text_by_for_id)
            candidates.append((node, named))

    container_totals = {}
    container_unnamed = {}
    for node, named in candidates:
        key = _nearest_container(node)
        container_totals[key] = container_totals.get(key, 0) + 1
        if not named:
            container_unnamed[key] = container_unnamed.get(key, 0) + 1

    groups = {}
    group_order = []
    for node, named in candidates:
        if named:
            continue
        sig = _control_signature(node)
        if sig not in groups:
            groups[sig] = []
            group_order.append(sig)
        groups[sig].append(node)

    findings = []
    for sig in group_order:
        by_severity = {}
        for node in groups[sig]:
            key = _nearest_container(node)
            severity = 3 if container_unnamed.get(key, 0) == container_totals.get(key, 0) else 2
            by_severity.setdefault(severity, []).append(node)
        for severity in sorted(by_severity):
            group_nodes = by_severity[severity]
            representative = group_nodes[0]
            occ = [
                (_control_location_html(node, elements), _labeled_evidence_html(node))
                for node in group_nodes
            ]
            findings.extend(_findings_from_occurrences(
                criterion="NNG-H6-LABELED",
                severity=severity,
                violation=_labeled_violation_html(representative),
                fix=_labeled_fix_html(representative),
                occurrences=occ,
            ))
    return findings


ROLE_NOUNS = frozenset({
    "button", "link", "icon", "field", "toggle", "checkbox", "menu",
    "control", "input", "dropdown", "tab",
})

_ARTICLE_RE = re.compile(r"^(?:a|an|the)\s+", re.IGNORECASE)
_TRAILING_ROLE_WORD_RE = re.compile(r"\s+(?:control|field)$", re.IGNORECASE)


def _normalize_role_entry(text):
    t = _strip_markdown_emphasis(text).strip()
    t = _ARTICLE_RE.sub("", t)
    t = _TRAILING_ROLE_WORD_RE.sub("", t)
    t = t.strip(" .:;,")
    return t.casefold()


def _is_control_or_field_heading(text):
    lowered = text.casefold()
    return "control" in lowered or "field" in lowered


def _check_labeled_markdown(blocks):
    findings = []
    current_heading = None
    for block in blocks:
        if block["kind"] == "heading":
            current_heading = block["text"]
            continue
        if block["kind"] != "list":
            continue
        if not current_heading or not _is_control_or_field_heading(current_heading):
            continue

        items = block["items"]
        unnamed_by_canon = {}
        for item_index, item in enumerate(items, start=1):
            normalized = _normalize_role_entry(item["text"])
            if normalized in ROLE_NOUNS:
                unnamed_by_canon.setdefault(normalized, []).append((item_index, item))
        total_unnamed = sum(len(v) for v in unnamed_by_canon.values())
        if total_unnamed == 0:
            continue
        severity = 3 if total_unnamed == len(items) else 2

        for canon in sorted(unnamed_by_canon):
            group_items = unnamed_by_canon[canon]
            # Each occurrence carries the item's 1-based position in the
            # list: two items with identical text (three bare "Field"
            # entries, say) would otherwise share one location string and
            # collapse under _findings_from_occurrences' dedup step.
            occ = [
                (
                    f'the "{current_heading}" list, item {item_index} ("{item["text"]}")',
                    f'list entry "{item["text"]}"',
                )
                for item_index, item in group_items
            ]
            findings.extend(_findings_from_occurrences(
                criterion="NNG-H6-LABELED",
                severity=severity,
                violation=(
                    "This control list entry names the control only by its role, with no "
                    "distinguishing label a user could read to tell it apart from another "
                    "control of the same kind."
                ),
                fix="Add the control's own label to this entry, alongside its role.",
                occurrences=occ,
            ))
    return findings


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def check(artifact):
    """artifact: skills._shared.artifact.Artifact (artifact.path,
    artifact.text, artifact.sha256). Returns RawFindings, unranked and
    unbounded; run_scripted_lane does the rest."""
    text = artifact.text
    findings = []
    if _looks_like_html(text):
        root = _parse_html(text)
        elements = _iter_elements(root)
        sections = _collect_sections(elements)
        findings.extend(_check_deadend_html(elements, sections))
        findings.extend(_control_naming_findings(_extract_control_labels_html(elements)))
        findings.extend(_check_labeled_html(elements))
    else:
        blocks = _parse_markdown_blocks(text)
        states = _markdown_states(blocks)
        findings.extend(_check_deadend_markdown(blocks, states))
        findings.extend(_control_naming_findings(_extract_control_labels_markdown(blocks)))
        findings.extend(_check_labeled_markdown(blocks))
    return findings


def main(argv=None):
    return run_scripted_lane(
        skill_name="critique-usability",
        skill_version="0.1.0",
        rubrics=["NNG"],
        check_fn=check,
        argv=argv,
    )


if __name__ == "__main__":
    sys.exit(main())
