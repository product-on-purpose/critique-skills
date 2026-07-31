"""critique-docs scripted lane: DIATAXIS-HEADING-DEPTH, DIATAXIS-MODE,
DIATAXIS-NAV-LENGTH.

DIATAXIS-ORPHAN moved to the judged lane while this file was written;
see references/DIATAXIS.md, "Why DIATAXIS-ORPHAN moved to the judged
lane", and SKILL.md, "What the scripted lane does not decide", for the
full reasoning. In short: skills._shared.runner.run_scripted_lane hands
a check function exactly one loaded artifact per invocation
(skills/_shared/artifact.py, load_artifact), and bench/README.md's own
tolerance rule states "one artifact is one page" for the markdown-tree
type this skill's tree artifacts use. DIATAXIS-ORPHAN's operational
test needs every other page's outbound links to decide whether this
page has zero inbound links; that data does not exist inside a single
page's own bytes, so no script invoked on one page can compute it,
however little judgment the arithmetic itself needs once the data
exists.

The three criteria implemented here are each fully decidable from the
one page this script is handed, with no judgment call and no data this
one artifact does not carry:

- DIATAXIS-HEADING-DEPTH reads only this page's own heading sequence.
- DIATAXIS-NAV-LENGTH reads only this page's own list blocks.
- DIATAXIS-MODE reads only this page's own declared mode (a minimal
  frontmatter convention this file defines, see _split_frontmatter and
  references/DIATAXIS.md's "Marker registry and thresholds") and this
  page's own sentences.

See docs/internal/skill-template.md, "Wiring scripts/checks.py", for
the pattern this file follows. The closed marker lexicons and the
numeric thresholds below are references/DIATAXIS.md's own "Marker
registry and thresholds" section, copied here as the single source a
reader can diff against that file rather than re-derived.
"""

import re
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
IMPLEMENTED_CRITERIA = frozenset({"DIATAXIS-HEADING-DEPTH", "DIATAXIS-MODE", "DIATAXIS-NAV-LENGTH"})

# --- DIATAXIS-NAV-LENGTH thresholds. references/DIATAXIS.md's own
# severity anchors for this criterion fix these numbers: "nine flat
# items, two past the threshold" stays severity 2, so the threshold is
# 7; "more than twenty flat items" is severity 3. -------------------------
NAV_LENGTH_ITEM_THRESHOLD = 7
NAV_LENGTH_SEVERITY_3_THRESHOLD = 20

# --- DIATAXIS-MODE: the declared-mode convention and the two closed
# marker lexicons. references/DIATAXIS.md, "Marker registry and
# thresholds", is the single source these constants are copied from. --

# A page declares its Diataxis mode in a minimal frontmatter block at
# the very top of the file: a "mode:" key inside a "---"-delimited
# block, whose value is one of the aliases below. A page with no such
# block, or a "mode" value outside this closed set, has no declared
# mode this check can read, so it produces no DIATAXIS-MODE findings
# rather than guessing one; this is the scripted-lane discipline's
# "no judgment call" rule applied to missing data the same way it
# applies to ambiguous data.
MODE_ALIASES = {
    "tutorial": "tutorial",
    "how-to": "how-to",
    "howto": "how-to",
    "how_to": "how-to",
    "reference": "reference",
    "explanation": "explanation",
}

# Sentence-initial imperative/sequencing markers: the register tutorial
# and how-to pages both use natively (references/DIATAXIS.md:
# "imperative and action-first for tutorial and how-to pages").
ACTION_MARKERS = ("first,", "next,", "then,", "finally,", "after that,", "once you have", "now,")

# Sentence-initial reason-giving markers: the register explanation
# pages use natively (references/DIATAXIS.md: "discursive for
# explanation pages").
EXPLANATION_MARKERS = (
    "because",
    "since",
    "this is because",
    "the reason is",
    "as a result,",
    "in other words,",
    "consequently,",
)

# Which foreign-register marker group(s) each declared mode is checked
# against. Reference pages are neutral and descriptive by default
# rather than by a positive marker set of their own, so both other
# registers are foreign to it; tutorial and how-to share the action
# register natively, so only explanation markers are foreign to them;
# an explanation page's own register is discursive, so action markers
# are foreign to it.
FOREIGN_MARKERS_BY_MODE = {
    "tutorial": (EXPLANATION_MARKERS,),
    "how-to": (EXPLANATION_MARKERS,),
    "reference": (ACTION_MARKERS, EXPLANATION_MARKERS),
    "explanation": (ACTION_MARKERS,),
}

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_ITEM_RE = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.*)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_FRONTMATTER_MODE_RE = re.compile(r'^mode:\s*"?([A-Za-z][A-Za-z_-]*)"?\s*$', re.IGNORECASE)


def _split_frontmatter(text):
    """Read a minimal, single-key frontmatter block: a "---" delimiter
    line, a "mode:" scalar somewhere inside it, and a closing "---"
    line. This is not the SKILL.md frontmatter dialect
    (docs/internal/skill-template.md, "Format"); it is a narrower,
    locally defined convention scoped to the one key DIATAXIS-MODE
    needs, documented normatively in references/DIATAXIS.md, "Marker
    registry and thresholds".

    Returns (declared_mode_or_None, body_text, line_offset). line_offset
    is how many lines were stripped from the front, so line numbers
    recorded by _parse_blocks against body_text still name the
    original file's own lines.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text, 0
    close_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            close_index = index
            break
    if close_index is None:
        return None, text, 0
    declared_mode = None
    for line in lines[1:close_index]:
        match = _FRONTMATTER_MODE_RE.match(line.strip())
        if match:
            declared_mode = MODE_ALIASES.get(match.group(1).lower())
            break
    remaining_lines = lines[close_index + 1:]
    body_text = "\n".join(remaining_lines)
    return declared_mode, body_text, close_index + 1


def _parse_blocks(text, line_offset=0):
    """A markdown block parser scoped to what this skill's scripted
    checks need: ATX headings, list blocks (bullet or ordered, flat or
    nested), and paragraphs (contiguous non-blank, non-heading,
    non-list-item lines, joined with a single space). Blank lines
    separate blocks, except a blank line immediately followed by
    another list-item line does not end a list block, so a "loose"
    list with blank lines between its items still counts as one
    listing. A list item's indentation greater than the block's first
    item's indentation makes it a nested (sub-grouped) item, never
    counted as a top-level item by DIATAXIS-NAV-LENGTH.

    line_offset shifts every recorded line number so it still names
    the original file's own line, after _split_frontmatter has already
    removed the frontmatter block this function never sees.
    """
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
                "line": line_offset + i + 1,
            })
            i += 1
            continue
        list_match = _LIST_ITEM_RE.match(line)
        if list_match:
            items = []
            base_indent = None
            while i < n:
                current = lines[i]
                if not current.strip():
                    lookahead = i + 1
                    while lookahead < n and not lines[lookahead].strip():
                        lookahead += 1
                    if lookahead < n and _LIST_ITEM_RE.match(lines[lookahead]):
                        i += 1
                        continue
                    break
                item_match = _LIST_ITEM_RE.match(current)
                if item_match:
                    indent = len(item_match.group(1))
                    if base_indent is None:
                        base_indent = indent
                    items.append({
                        "text": item_match.group(2).strip(),
                        "indent": indent,
                        "line": line_offset + i + 1,
                    })
                    i += 1
                    continue
                leading_spaces = len(current) - len(current.lstrip(" "))
                if items and leading_spaces > base_indent:
                    items[-1]["text"] += " " + current.strip()
                    i += 1
                    continue
                break
            blocks.append({
                "kind": "list",
                "items": items,
                "line": items[0]["line"] if items else line_offset + i + 1,
            })
            continue
        start_line = line_offset + i + 1
        para_lines = []
        while i < n and lines[i].strip() and not _HEADING_RE.match(lines[i]) and not _LIST_ITEM_RE.match(lines[i]):
            para_lines.append(lines[i])
            i += 1
        blocks.append({
            "kind": "paragraph",
            "text": " ".join(para_lines).strip(),
            "line": start_line,
        })
    return blocks


def _split_sentences(text):
    return [part for part in _SENTENCE_SPLIT_RE.split(text.strip()) if part]


def _check_heading_depth(blocks):
    """DIATAXIS-HEADING-DEPTH: flag any heading whose level exceeds the
    immediately preceding heading's level by more than one. The first
    heading on the page has no preceding heading to compare against, so
    it is never flagged on its own. Severity follows this skill's own
    recurrence anchors (references/DIATAXIS.md): a single jump stays
    severity 2, two or more jumps on the same page read as the page's
    own habitual structure and rise to severity 3.
    """
    headings = [block for block in blocks if block["kind"] == "heading"]
    violations = [
        (previous, current)
        for previous, current in zip(headings, headings[1:])
        if current["level"] > previous["level"] + 1
    ]
    severity = 3 if len(violations) >= 2 else 2
    findings = []
    for previous, current in violations:
        findings.append(
            RawFinding(
                criterion="DIATAXIS-HEADING-DEPTH",
                severity=severity,
                location=f"the {current['text']} heading",
                evidence=(
                    f"Heading level jumped from {previous['level']} ({previous['text']}) to "
                    f"{current['level']} ({current['text']}) with no intermediate level between them."
                ),
                violation=(
                    "This heading is nested more than one level deeper than the heading "
                    "immediately before it, so a reader or a tool relying on heading level "
                    "cannot reconstruct which section this one belongs under."
                ),
                fix=(
                    f"Insert a level {previous['level'] + 1} heading between {previous['text']} "
                    f"and {current['text']}, or promote {current['text']} to level "
                    f"{previous['level'] + 1}."
                ),
            )
        )
    return findings


def _listings_per_heading_scope(blocks):
    """How many list blocks sit under each heading scope, keyed by the
    scope's 0-based ordinal (scope 0 is whatever precedes the page's
    first heading). Used only to decide whether naming a listing by its
    enclosing heading identifies it uniquely.
    """
    counts = {}
    scope = 0
    for block in blocks:
        if block["kind"] == "heading":
            scope += 1
            continue
        if block["kind"] == "list":
            counts[scope] = counts.get(scope, 0) + 1
    return counts


def _check_nav_length(blocks):
    """DIATAXIS-NAV-LENGTH: flag any list block whose top-level item
    count exceeds NAV_LENGTH_ITEM_THRESHOLD and that carries no nested
    (sub-grouped) items. A heading interposed between two runs of items
    already starts a new block at _parse_blocks's own heading branch,
    which is the "split into named subgroups" case this criterion
    credits; a run broken up that way never reaches this function as
    one long list in the first place.

    The enclosing heading names the listing, which identifies it only
    while that heading has one listing under it. A heading with two or
    more listings beneath it gets the offending listing's own start line
    appended, because the contract requires a location a reader can
    navigate to unaided (docs/reference/critique-contract.md) and
    "the Related pages listing" does not say which of two it means.
    """
    findings = []
    listing_counts = _listings_per_heading_scope(blocks)
    heading_text = None
    scope = 0
    for block in blocks:
        if block["kind"] == "heading":
            heading_text = block["text"]
            scope += 1
            continue
        if block["kind"] != "list":
            continue
        items = block["items"]
        if not items:
            continue
        base_indent = items[0]["indent"]
        top_level = [item for item in items if item["indent"] == base_indent]
        has_subgrouping = any(item["indent"] > base_indent for item in items)
        count = len(top_level)
        if count > NAV_LENGTH_ITEM_THRESHOLD and not has_subgrouping:
            severity = 3 if count > NAV_LENGTH_SEVERITY_3_THRESHOLD else 2
            if not heading_text:
                location = f"the listing starting at line {block['line']}"
            elif listing_counts.get(scope, 0) > 1:
                location = f"the {heading_text} listing starting at line {block['line']}"
            else:
                location = f"the {heading_text} listing"
            findings.append(
                RawFinding(
                    criterion="DIATAXIS-NAV-LENGTH",
                    severity=severity,
                    location=location,
                    evidence=f"{count} flat items, no sub-headings or nested items breaking them into groups.",
                    violation=(
                        f"This listing holds {count} items, more than "
                        f"{NAV_LENGTH_ITEM_THRESHOLD} a reader can scan in one glance, with no "
                        "subgrouping to break it up."
                    ),
                    fix=(
                        "Split this listing into named subgroups, either nested sub-lists or "
                        "sub-headings, each holding a smaller set of related items."
                    ),
                )
            )
    return findings


def _iter_sentence_units(blocks):
    """Yields (heading_text, unit_kind, unit_index, sentence_index,
    sentence) for every sentence in every paragraph and every list item
    on the page, in document order. unit_index restarts at 1 under each
    heading, tracked separately for paragraphs and for list items.
    """
    heading_text = None
    paragraph_number = 0
    list_item_number = 0
    for block in blocks:
        if block["kind"] == "heading":
            heading_text = block["text"]
            paragraph_number = 0
            list_item_number = 0
            continue
        if block["kind"] == "paragraph":
            paragraph_number += 1
            for sentence_index, sentence in enumerate(_split_sentences(block["text"]), start=1):
                yield heading_text, "paragraph", paragraph_number, sentence_index, sentence
        elif block["kind"] == "list":
            for item in block["items"]:
                list_item_number += 1
                for sentence_index, sentence in enumerate(_split_sentences(item["text"]), start=1):
                    yield heading_text, "list item", list_item_number, sentence_index, sentence


def _starts_with_marker(sentence_lower, marker):
    """True when sentence_lower opens with marker at a word boundary,
    so "because" matches "Because the file..." but not "Becausement...".
    """
    if not sentence_lower.startswith(marker):
        return False
    rest = sentence_lower[len(marker):]
    return rest == "" or not rest[0].isalnum()


def _mode_location(heading_text, unit_kind, unit_index, sentence_index):
    base = f"{heading_text}, " if heading_text else ""
    unit = f"{unit_kind} {unit_index}"
    if sentence_index > 1:
        return f"{base}{unit}, sentence {sentence_index}"
    return f"{base}{unit}"


def _check_mode(declared_mode, blocks):
    """DIATAXIS-MODE: flag any sentence, in a paragraph or a list item,
    that opens with a fixed lexical marker belonging to a mode's
    register other than the page's own declared mode
    (FOREIGN_MARKERS_BY_MODE). A page with no recognized declared mode
    is not scanned at all: without a declared mode there is no register
    to hold the page's sentences to, and guessing one would be exactly
    the judgment call this criterion is scoped to avoid (see
    references/DIATAXIS.md, "Why DIATAXIS-MODE and the four
    per-mode-fit criteria are not the same criterion"). Severity
    follows the same recurrence rule as DIATAXIS-HEADING-DEPTH: a
    single flagged sentence is severity 2, two or more on the same page
    read as the page's own habitual register and rise to severity 3.
    """
    if declared_mode not in FOREIGN_MARKERS_BY_MODE:
        return []
    foreign_marker_groups = FOREIGN_MARKERS_BY_MODE[declared_mode]
    matches = []
    for heading_text, unit_kind, unit_index, sentence_index, sentence in _iter_sentence_units(blocks):
        lowered = sentence.strip().lower()
        for marker_group in foreign_marker_groups:
            if any(_starts_with_marker(lowered, marker) for marker in marker_group):
                matches.append((heading_text, unit_kind, unit_index, sentence_index, sentence))
                break
    severity = 3 if len(matches) >= 2 else 2
    findings = []
    for heading_text, unit_kind, unit_index, sentence_index, sentence in matches:
        findings.append(
            RawFinding(
                criterion="DIATAXIS-MODE",
                severity=severity,
                location=_mode_location(heading_text, unit_kind, unit_index, sentence_index),
                evidence=sentence,
                violation=(
                    f"This sentence opens with a lexical marker belonging to a different mode's "
                    f"register than this page's declared {declared_mode} mode."
                ),
                fix=(
                    "Rewrite the sentence in the page's own declared mode's register, or move "
                    "this content to a page in the mode it actually belongs to."
                ),
            )
        )
    return findings


def check(artifact):
    """artifact: skills._shared.artifact.Artifact (artifact.path,
    artifact.text, artifact.sha256). Returns RawFindings, unranked and
    unbounded; run_scripted_lane does the rest."""
    declared_mode, body_text, line_offset = _split_frontmatter(artifact.text)
    blocks = _parse_blocks(body_text, line_offset=line_offset)
    findings = []
    findings.extend(_check_heading_depth(blocks))
    findings.extend(_check_mode(declared_mode, blocks))
    findings.extend(_check_nav_length(blocks))
    return findings


def main(argv=None):
    return run_scripted_lane(
        skill_name="critique-docs",
        skill_version="0.1.0",
        rubrics=["DIATAXIS"],
        check_fn=check,
        argv=argv,
    )


if __name__ == "__main__":
    sys.exit(main())
