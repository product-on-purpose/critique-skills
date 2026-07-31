"""critique-argument scripted lane: TOULMIN-CLAIM-MARKER, TOULMIN-HEDGE-DENSITY.

Both criteria are document-level measurements, not verdicts on the argument
itself (ADR 0017, ../../../docs/internal/decisions/0017-argument-lane-split-
scripted-assists-as-criteria.md): a closed-lexicon match plus a word count
or a sentence ratio, exactly the shape docs/internal/skill-template.md's
"Wiring scripts/checks.py" calls scriptable with no judgment call. The six
Toulmin elements themselves (TOULMIN-CLAIM, TOULMIN-GROUNDS, and so on) stay
judged; see references/TOULMIN.md, "Lane split", for why none of them
qualifies.

The two lexicons and both thresholds are references/TOULMIN.md's own
"Registry" and "Thresholds" sections, copied here as the single source a
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
IMPLEMENTED_CRITERIA = frozenset({"TOULMIN-CLAIM-MARKER", "TOULMIN-HEDGE-DENSITY"})

# references/TOULMIN.md's own closed conclusion-marker lexicon
# (TOULMIN-CLAIM-MARKER's operational test). Matched case-insensitively,
# whole-phrase, so "thus" does not match inside "enthusiastic".
CLAIM_MARKERS = (
    "therefore",
    "thus",
    "hence",
    "it follows that",
    "we recommend",
    "this paper argues",
    "i argue that",
    "the conclusion is",
    "in conclusion",
    "we should",
    "the case for",
)

# references/TOULMIN.md's own closed hedging lexicon
# (TOULMIN-HEDGE-DENSITY's operational test), matched the same way.
HEDGES = (
    "may",
    "might",
    "could",
    "possibly",
    "perhaps",
    "arguably",
    "somewhat",
    "relatively",
    "it seems",
    "appears to",
    "tends to",
    "to a degree",
)

# references/TOULMIN.md, "Thresholds": v0.1 defaults, not measured values.
CLAIM_MARKER_WORD_THRESHOLD = 300
HEDGE_DENSITY_FIRE_RATIO = 0.35
HEDGE_DENSITY_SEVERITY_3_RATIO = 0.50

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
# A word is a whitespace-separated token carrying at least one letter or
# digit. references/TOULMIN.md states TOULMIN-CLAIM-MARKER's threshold in
# words, and a bare markdown token ("-", "*", ">", "|") is not one; a
# plain \S+ count treats each of them as a word, which is enough to push
# a heavily bulleted artifact over the 300-word boundary on punctuation
# alone. Tokens that merely carry punctuation ("40", "2,400", "top-of-
# funnel") still count once each, as they should.
_WORD_RE = re.compile(r"\S*\w\S*")


def _compile_lexicon(phrases):
    """One case-insensitive alternation over a closed phrase list, each
    phrase bounded by \\b so "may" does not match inside "maybe" and
    "thus" does not match inside "enthusiast". A phrase's internal
    spaces become \\s+ rather than a literal space, so a phrase that a
    hard-wrapped markdown paragraph happens to split across a line break
    ("it follows\\nthat") still matches; this is a closed-lexicon
    substring match, not a natural-language parse, and whitespace
    variation is not a defect in the artifact worth missing over."""
    ordered = sorted(phrases, key=len, reverse=True)
    parts = [r"\s+".join(re.escape(word) for word in phrase.split()) for phrase in ordered]
    pattern = "|".join(parts)
    return re.compile(rf"\b(?:{pattern})\b", re.IGNORECASE)


_CLAIM_MARKER_RE = _compile_lexicon(CLAIM_MARKERS)
_HEDGE_RE = _compile_lexicon(HEDGES)


def _parse_blocks(text):
    """A minimal markdown block parser: ATX headings (one to six '#'
    characters, a space, then text) and paragraphs (contiguous
    non-blank, non-heading lines, joined with a single space). Blank
    lines separate blocks and are otherwise discarded. Scoped to what
    this skill's artifact claim covers (markdown or plain-text
    argumentative prose), the same shape as the template fixture's own
    _parse_blocks (docs/internal/skill-template.md, "Wiring
    scripts/checks.py")."""
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
        para_lines = []
        while i < n and lines[i].strip() and not _HEADING_RE.match(lines[i]):
            para_lines.append(lines[i])
            i += 1
        blocks.append({"kind": "paragraph", "text": " ".join(para_lines).strip()})
    return blocks


def _document_location(blocks):
    """Both scripted criteria are document-level: references/TOULMIN.md's
    own operational tests count occurrences "across the whole artifact"
    and divide by "total sentence count", not by paragraph, so neither
    finding has one single paragraph to point at. Per the corpus anchor
    grammar (bench/README.md, "markdown-prose"), a heading title in
    quotes resolves to a section anchor that, for a level-1 heading,
    covers every paragraph beneath it, which for a document's own title
    heading is the entire document: a genuinely navigable stand-in for
    "the whole document" that the free-text phrase "throughout the
    document" is not (bench/README.md, "Unresolvable locations"). Plain
    text with no heading at all falls back to naming line 1, the point a
    reader's scan actually starts from."""
    for block in blocks:
        if block["kind"] == "heading" and block["level"] == 1:
            return f'the whole document, under its "{block["text"]}" heading'
    return "the whole document, starting at line 1"


def _prose_text(blocks):
    """Every parsed block's text, joined by a single space: the artifact
    as a reader reads it, with markdown's own structural tokens gone.
    `_parse_blocks` has already dropped a heading's leading '#' run and
    joined a paragraph's hard-wrapped lines, so what is left is words.

    Both criteria below are stated over that, not over the raw source, so
    the lexicon search and the word count read exactly one text and the
    evidence string cannot disagree with the severity band about how long
    the artifact is. Detection is unaffected by the switch: no marker
    phrase can hide inside a token `_parse_blocks` strips. Tokens the
    parser does not strip (list bullets, table pipes) are excluded from
    the count by _WORD_RE instead."""
    return " ".join(block["text"] for block in blocks if block["text"])


def _word_count(text):
    return len(_WORD_RE.findall(text))


def _check_claim_marker(artifact, blocks):
    """TOULMIN-CLAIM-MARKER: flag one document-level violation when the
    fixed conclusion-marker lexicon has zero matches anywhere in the
    artifact's prose (headings included, since a heading is exactly where
    a reader scanning for the conclusion looks first). Severity 2 under
    300 words, severity 3 at 300 words or more, counted over prose rather
    than raw markdown (see _prose_text). An empty artifact makes no claim
    to signpost, so it is not scanned at all."""
    text = _prose_text(blocks)
    if not text.strip():
        return []
    if _CLAIM_MARKER_RE.search(text):
        return []
    words = _word_count(text)
    severity = 3 if words >= CLAIM_MARKER_WORD_THRESHOLD else 2
    return [
        RawFinding(
            criterion="TOULMIN-CLAIM-MARKER",
            severity=severity,
            location=_document_location(blocks),
            evidence=f"0 conclusion-marker phrases found across {words} words.",
            violation=(
                "No phrase from the conclusion-marker lexicon (therefore, thus, hence, "
                "it follows that, we recommend, this paper argues, I argue that, the "
                "conclusion is, in conclusion, we should, the case for) appears anywhere "
                "in the artifact, so a reader scanning rather than reading straight "
                "through has no signpost to where the conclusion is asserted."
            ),
            fix=(
                "Add an explicit conclusion-signalling phrase at the point the artifact "
                "states its central claim, for example \"therefore\" or \"we recommend\"."
            ),
        )
    ]


def _check_hedge_density(artifact, blocks):
    """TOULMIN-HEDGE-DENSITY: the ratio of sentences containing at least
    one hedging term to total sentence count, counted over paragraph
    text only (a heading is not a sentence). Flags when the ratio
    exceeds 0.35; severity 2 at or below 0.50, severity 3 above it. A
    document with no paragraph sentences has nothing to measure a ratio
    over, so it produces no finding rather than a division by zero."""
    sentences = []
    for block in blocks:
        if block["kind"] != "paragraph":
            continue
        sentences.extend(part for part in _SENTENCE_SPLIT_RE.split(block["text"]) if part.strip())
    total = len(sentences)
    if total == 0:
        return []
    hedged = sum(1 for sentence in sentences if _HEDGE_RE.search(sentence))
    ratio = hedged / total
    if ratio <= HEDGE_DENSITY_FIRE_RATIO:
        return []
    severity = 3 if ratio > HEDGE_DENSITY_SEVERITY_3_RATIO else 2
    return [
        RawFinding(
            criterion="TOULMIN-HEDGE-DENSITY",
            severity=severity,
            location=_document_location(blocks),
            evidence=f"{hedged} of {total} sentences ({ratio:.2f}) carry at least one hedging term.",
            violation=(
                "More than 0.35 of the artifact's sentences carry a term from the hedging "
                "lexicon (may, might, could, possibly, perhaps, arguably, somewhat, "
                "relatively, it seems, appears to, tends to, to a degree), spread across "
                "the whole document rather than concentrated where the evidence actually "
                "underdetermines the claim."
            ),
            fix=(
                "Remove the hedge from sentences whose claim the evidence actually "
                "supports, reserving qualification for the claims that genuinely need it."
            ),
        )
    ]


def check(artifact):
    """artifact: skills._shared.artifact.Artifact (artifact.path,
    artifact.text, artifact.sha256). Returns RawFindings, unranked and
    unbounded; run_scripted_lane does the rest."""
    blocks = _parse_blocks(artifact.text)
    findings = []
    findings.extend(_check_claim_marker(artifact, blocks))
    findings.extend(_check_hedge_density(artifact, blocks))
    return findings


def main(argv=None):
    return run_scripted_lane(
        skill_name="critique-argument",
        skill_version="0.1.0",
        rubrics=["TOULMIN"],
        check_fn=check,
        argv=argv,
    )


if __name__ == "__main__":
    sys.exit(main())
