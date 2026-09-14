"""critique-clarity scripted lane: the 15 PLAIN-* and WILLIAMS-* criteria
docs/reference/criterion-ids.md and this skill's own SKILL.md declare
scripted (checks.scripted). Every criterion below is a closed lexicon, a
fixed structural pattern, or a measurable threshold, exactly the shape
docs/internal/skill-template.md, "Scripted lane discipline," calls
scriptable with no judgment call; the eight judged criteria
(PLAIN-AUDIENCE, PLAIN-CONSISTENT-TERMS, PLAIN-MAIN-IDEA-FIRST,
PLAIN-ORGANIZE, WILLIAMS-CHARACTER-ACTION, WILLIAMS-COHERENCE,
WILLIAMS-COHESION, WILLIAMS-STRESS) stay judged because they require
reading the artifact's meaning, not a pattern match, per their own
Lane rationale in references/PLAIN.md and references/WILLIAMS.md.

None of these checks is a real parser or a part-of-speech tagger; each is
a deterministic, closed-vocabulary heuristic that approximates its
criterion's operational test (references/PLAIN.md, references/WILLIAMS.md,
"Operational test" column). A heuristic that occasionally over- or
under-fires on genuinely ambiguous prose is an accepted cost of the
scripted lane (docs/internal/skill-template.md: "a wrong criterion in the
scripted lane is a determinism claim the library cannot back up", so the
bar is determinism, not linguistic perfection); every one of these
functions produces the same findings for the same artifact bytes on every
run, which is the claim this file actually has to keep.
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
IMPLEMENTED_CRITERIA = frozenset({
    "PLAIN-ACTIVE",
    "PLAIN-CONCISE",
    "PLAIN-DOUBLE-NEGATIVE",
    "PLAIN-HEADINGS",
    "PLAIN-JARGON",
    "PLAIN-LISTS",
    "PLAIN-MUST",
    "PLAIN-NOMINALIZATION",
    "PLAIN-PARAGRAPH",
    "PLAIN-PRONOUNS",
    "PLAIN-SENTENCE-LENGTH",
    "PLAIN-SUBJECT-VERB-OBJECT",
    "PLAIN-TRANSITIONS",
    "WILLIAMS-PARALLELISM",
    "WILLIAMS-SHAPE",
})

# ---------------------------------------------------------------------------
# Shared parsing helpers. Same minimal markdown block shape as the toy
# fixture and critique-argument's own checks.py (ATX headings plus
# contiguous-line paragraphs, blank lines as separators), scoped to this
# skill's own artifact claim: markdown or plain-text prose documents.
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"\S+")


def _parse_blocks(text):
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


def _split_sentences(text):
    return [part for part in _SENTENCE_SPLIT_RE.split(text.strip()) if part]


def _word_count(text):
    return len(_WORD_RE.findall(text))


def _first_words(text, count):
    words = _WORD_RE.findall(text)
    snippet = " ".join(words[:count])
    return snippet + ("..." if len(words) > count else "")


def _iter_paragraphs(blocks):
    """Yield (heading_text, paragraph_number, block, first_after_heading)
    for every paragraph block, in document order. heading_text is the
    most recently seen heading at any level, or None before the first
    heading.

    paragraph_number is **relative to heading_text**: it restarts at 1
    after every heading, and is a whole-document counter only for the
    paragraphs that precede the document's first heading (where
    heading_text is None). See `_location` for why the two cases differ.

    first_after_heading is True for a paragraph immediately following a
    heading (or starting the document with no heading at all), which is
    the condition PLAIN-TRANSITIONS and PLAIN-PARAGRAPH's own callers use
    to know a paragraph is opening a topic rather than continuing one.
    """
    heading_text = None
    paragraph_number = 0
    prev_was_heading_or_start = True
    for block in blocks:
        if block["kind"] == "heading":
            heading_text = block["text"]
            paragraph_number = 0
            prev_was_heading_or_start = True
            continue
        paragraph_number += 1
        yield heading_text, paragraph_number, block, prev_was_heading_or_start
        prev_was_heading_or_start = False


def _location(heading_text, paragraph_number, suffix=None):
    """The finding's `location` string.

    The numbering convention is not cosmetic. `bench/metrics`'s
    `markdown-prose` resolver reads a location that names both a heading
    and a paragraph number as *the nth paragraph under that heading*
    (`resolve_markdown._resolve_section` then indexes into
    `Document.paragraphs_under`), and a location that names only a
    paragraph number as the nth paragraph of the whole document. A
    whole-document number printed next to a heading name therefore
    resolves to the wrong paragraph, or, once the number exceeds the
    section's paragraph count, to no paragraph at all: every such finding
    scores as a miss against the seeded corpus no matter how correct the
    check that produced it was.

    So: heading present, number counted within that heading; no heading,
    number counted across the document. Both forms then mean to the
    scorer exactly what they mean to a reader, which is the same thing.

    Two documented limits, both properties of the resolver rather than of
    this function. A document with two identically titled headings gives
    the resolver no way to pick between them, and a heading title under
    four characters is below the length the resolver will match on; in
    either case the section does not resolve and the number is read as a
    whole-document index. Neither occurs in this skill's corpus segment.
    """
    base = f"{heading_text}, paragraph {paragraph_number}" if heading_text else f"paragraph {paragraph_number}"
    return f"{base}, {suffix}" if suffix else base


def _compile_lexicon(phrases):
    """One case-insensitive alternation over a closed phrase list, each
    phrase bounded by \\b so short entries do not match inside a longer
    word (see critique-argument's scripts/checks.py, _compile_lexicon,
    the same technique). Sorted longest-first so a multi-word phrase
    wins over a shorter phrase it contains."""
    ordered = sorted(phrases, key=len, reverse=True)
    parts = [r"\s+".join(re.escape(word) for word in phrase.split()) for phrase in ordered]
    pattern = "|".join(parts)
    return re.compile(rf"\b(?:{pattern})\b", re.IGNORECASE)


_COORDINATOR_RE = re.compile(r",?\s+(?:and|or)\s+(?=\S)", re.IGNORECASE)


def _split_series_items(sentence):
    """Normalize a sentence's coordinated series, Oxford comma or not,
    into an item list: every " and "/" or " conjunction becomes a comma
    boundary, then the result is split on commas and semicolons. A
    sentence with no " and "/" or " coordinator anywhere in it is not
    treated as a series at all (a single-item list is returned) even if
    it contains commas: an ordinary sentence built from subordinate
    clauses and asides also splits into multiple comma-separated
    segments, and without a coordinator there is no lexical signal this
    is an enumerated series rather than one clause interrupting another,
    which is PLAIN-SUBJECT-VERB-OBJECT and WILLIAMS-SHAPE's case instead.
    A semicolon-joined list with no terminal "and"/"or" ("File the log;
    update the roster; close the ticket.") is outside this heuristic's
    reach for the same reason; the numbered-marker path in PLAIN-LISTS
    still catches an enumerated list of that shape when it uses ordinal
    words. Shared by PLAIN-LISTS (item count) and WILLIAMS-PARALLELISM
    (item grammatical form), since both criteria's operational test
    starts from the same "comma- or semicolon-separated, and/or-joined
    series" structure."""
    text = sentence.strip().rstrip(".!?")
    if not text:
        return []
    text = text.replace(";", ",")
    if "," not in text or not _COORDINATOR_RE.search(text):
        return [text]
    normalized = _COORDINATOR_RE.sub(", ", text)
    return [part.strip() for part in normalized.split(",") if part.strip()]


def _leading_asides(sentence, *, max_lead_words=8):
    """Approximate "how many comma-set-off clauses intervene between this
    sentence's subject and its verb" without a real parser: split on
    commas, treat a short leading segment as the subject candidate, and
    count the segments fully enclosed by commas after it (excluding the
    sentence's own final segment, which is what comes after the
    interruption, not part of it). Returns (num_asides, interior_word_count).
    A sentence whose leading segment already reads as a full clause (long,
    or itself a coordinated-series item) is not this pattern at all; see
    the len(items) >= 3 guard in the two callers below, which excludes a
    parallel list already claimed by PLAIN-LISTS from being double-counted
    here as a subject-verb interruption."""
    segments = [s.strip() for s in sentence.split(",")]
    if len(segments) < 3:
        return 0, 0
    if _word_count(segments[0]) > max_lead_words:
        return 0, 0
    interior = segments[1:-1]
    interior_words = sum(_word_count(s) for s in interior)
    return len(interior), interior_words


_SUBORDINATE_MARKERS = (
    "which", "that", "because", "although", "though", "while", "since",
    "unless", "whereas", "who", "whom", "whose", "if", "when",
)
_SUBORDINATE_MARKER_RE = _compile_lexicon(_SUBORDINATE_MARKERS)


def _subordinate_marker_count(sentence):
    return len(_SUBORDINATE_MARKER_RE.findall(sentence))


def _ratio_severity(hit_count, total_count, *, high_ratio, min_total_for_high=3):
    """A density-based severity rule reused by every criterion whose
    severity 2 / severity 3 anchors distinguish "one isolated lapse" from
    "the construction repeats across most of a paragraph": severity 3
    only once there is enough material to call it a pattern
    (min_total_for_high) and the hit ratio crosses high_ratio; severity 2
    otherwise, for any actual hit."""
    if total_count == 0:
        return 2
    ratio = hit_count / total_count
    if total_count >= min_total_for_high and ratio >= high_ratio:
        return 3
    return 2


# ---------------------------------------------------------------------------
# PLAIN-ACTIVE
# ---------------------------------------------------------------------------

_BE_FORMS = ("is", "are", "was", "were", "am", "be", "been", "being")
_AUX_MODALS = (
    "has", "have", "had", "will", "would", "shall", "should", "can",
    "could", "may", "might", "must", "did", "does", "do",
)
_IRREGULAR_PARTICIPLES = (
    "given", "taken", "made", "done", "written", "sent", "held", "told",
    "shown", "known", "seen", "put", "set", "kept", "left", "brought",
    "thought", "found", "said", "paid", "built", "spent", "meant",
    "chosen", "broken", "spoken", "driven", "begun", "gone", "grown",
    "drawn", "worn", "torn", "sworn", "frozen", "stolen", "sold",
)
_PASSIVE_RE = re.compile(
    r"\b(?:(?:" + "|".join(_AUX_MODALS) + r")\s+)?"
    r"(?:" + "|".join(_BE_FORMS) + r")\s+"
    r"(?:\w+ed\b|\b(?:" + "|".join(_IRREGULAR_PARTICIPLES) + r")\b)",
    re.IGNORECASE,
)


def _check_active(blocks):
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        sentences = _split_sentences(block["text"])
        if not sentences:
            continue
        hits = [s for s in sentences if _PASSIVE_RE.search(s)]
        if not hits:
            continue
        severity = _ratio_severity(len(hits), len(sentences), high_ratio=0.75)
        for sentence in hits:
            findings.append(
                RawFinding(
                    criterion="PLAIN-ACTIVE",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=sentence,
                    violation=(
                        "The sentence uses a be-verb plus past-participle passive construction "
                        "in a context where the actor is recoverable and worth naming directly."
                    ),
                    fix="Rewrite the sentence in active voice, naming the actor that performs the action.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# PLAIN-CONCISE
# ---------------------------------------------------------------------------

_WORDY_PHRASES = ("in order to", "due to the fact that", "at this point in time", "a number of")
_WORDY_RE = _compile_lexicon(_WORDY_PHRASES)


def _check_concise(blocks):
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        sentences = _split_sentences(block["text"])
        matches = [(s, _WORDY_RE.findall(s)) for s in sentences]
        total_hits = sum(len(m) for _, m in matches)
        if total_hits == 0:
            continue
        severity = 3 if total_hits >= 3 else 2
        for sentence, hits in matches:
            if not hits:
                continue
            findings.append(
                RawFinding(
                    criterion="PLAIN-CONCISE",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=sentence,
                    violation=(
                        "The sentence uses a wordy construction from the fixed wordy-phrase list "
                        "that a shorter equivalent would carry with no loss of meaning."
                    ),
                    fix="Replace the wordy phrase with its plain equivalent (for example, because for due to the fact that).",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# PLAIN-DOUBLE-NEGATIVE
# ---------------------------------------------------------------------------

_NEGATION_MARKERS = (
    "not", "no", "never", "none", "neither", "nor", "nothing", "nobody",
    "cannot", "can't", "won't", "isn't", "aren't", "doesn't", "don't",
    "didn't", "without", "unless", "except", "excluding", "ineligible",
    "invalid", "unable", "unavailable", "noncompliant",
)
_NEGATION_RE = _compile_lexicon(_NEGATION_MARKERS)


def _check_double_negative(blocks):
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        for sentence in _split_sentences(block["text"]):
            hits = _NEGATION_RE.findall(sentence)
            if len(hits) < 2:
                continue
            severity = 3 if len(hits) >= 3 else 2
            findings.append(
                RawFinding(
                    criterion="PLAIN-DOUBLE-NEGATIVE",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=sentence,
                    violation=(
                        f"{len(hits)} negation markers from the fixed negation list co-occur in "
                        "one clause, so the reader has to work out the statement's logical sign "
                        "before understanding it."
                    ),
                    fix="Restate the sentence with at most one negation, or recast it as a positive statement.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# PLAIN-HEADINGS
# ---------------------------------------------------------------------------

_NON_SPECIFIC_HEADINGS = ("overview", "general", "miscellaneous", "other", "details")
# A section is a container of paragraphs, so its scannability threshold has
# to sit well above the single-paragraph threshold PLAIN-PARAGRAPH uses
# (_PARAGRAPH_LENGTH_THRESHOLD, below). When the two constants are equal, a
# section's word count is never less than its longest paragraph's, so every
# over-long paragraph automatically drags its own section past the heading
# threshold and the same underlying fact gets reported twice, once as a
# paragraph defect and once as a heading defect. 400 is roughly the point at
# which a section of ordinary 100-to-150-word paragraphs stops being
# scannable without an intervening subheading; 800 is the doubled hard
# threshold, matching the soft-to-hard ratio every other check here uses.
_SECTION_LENGTH_SOFT = 400
_SECTION_LENGTH_HARD = 800


def _check_headings(blocks):
    findings = []
    for index, block in enumerate(blocks):
        if block["kind"] != "heading":
            continue
        heading_text = block["text"]
        if heading_text.strip().lower() in _NON_SPECIFIC_HEADINGS:
            findings.append(
                RawFinding(
                    criterion="PLAIN-HEADINGS",
                    severity=2,
                    location=f"the {heading_text} heading",
                    evidence=f"heading: {heading_text}",
                    violation=(
                        "The heading text matches the fixed list of non-specific heading labels, "
                        "so a reader scanning headings cannot tell whether the section applies to them."
                    ),
                    fix="Replace the heading with text specific enough to be found by scanning.",
                )
            )
        section_words = 0
        for later in blocks[index + 1:]:
            if later["kind"] == "heading":
                break
            section_words += _word_count(later["text"])
        if section_words > _SECTION_LENGTH_SOFT:
            severity = 3 if section_words > _SECTION_LENGTH_HARD else 2
            findings.append(
                RawFinding(
                    criterion="PLAIN-HEADINGS",
                    severity=severity,
                    location=f"the {heading_text} heading",
                    evidence=f"{section_words} words follow this heading before the next heading of any level.",
                    violation=(
                        "The section beneath this heading exceeds the length threshold with no "
                        "intervening subheading to keep it scannable."
                    ),
                    fix="Split the section with an intervening subheading, or shorten it.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# PLAIN-JARGON
# ---------------------------------------------------------------------------

_JARGON_TERMS = ("pursuant to", "notwithstanding", "aforementioned", "herein")
_JARGON_RE = _compile_lexicon(_JARGON_TERMS)
_DEFINITION_MARKERS = ("meaning", "that is", "i.e.", "in other words")


def _has_nearby_definition(sentences, index):
    window = sentences[index : index + 2]
    lowered = " ".join(window).lower()
    if any(marker in lowered for marker in _DEFINITION_MARKERS):
        return True
    return "(" in sentences[index]


def _check_jargon(blocks):
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        sentences = _split_sentences(block["text"])
        qualifying = []
        for i, sentence in enumerate(sentences):
            if not _JARGON_RE.search(sentence):
                continue
            if _has_nearby_definition(sentences, i):
                continue
            qualifying.append(sentence)
        if not qualifying:
            continue
        severity = 3 if len(qualifying) >= 3 else 2
        for sentence in qualifying:
            findings.append(
                RawFinding(
                    criterion="PLAIN-JARGON",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=sentence,
                    violation=(
                        "The sentence uses a legal or foreign-language jargon term from the fixed "
                        "list with no plain-language definition in the same or the following sentence."
                    ),
                    fix="Replace the jargon term with a plain equivalent, or define it at first use.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# PLAIN-LISTS
# ---------------------------------------------------------------------------

_STEP_MARKER_RE = re.compile(r"\b(?:first|second|third|fourth|fifth)\b,", re.IGNORECASE)


def _check_lists(blocks):
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        for sentence in _split_sentences(block["text"]):
            items = _split_series_items(sentence)
            step_markers = len(_STEP_MARKER_RE.findall(sentence))
            if len(items) < 3 and step_markers < 3:
                continue
            severity = 3 if len(items) >= 5 or step_markers >= 5 else 2
            findings.append(
                RawFinding(
                    criterion="PLAIN-LISTS",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=sentence,
                    violation=(
                        "The sentence embeds three or more comma- or semicolon-separated parallel "
                        "items inline rather than presenting them as a formatted list."
                    ),
                    fix="Reformat the inline items as a numbered or bulleted list.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# PLAIN-MUST
# ---------------------------------------------------------------------------

_MUST_TERMS = ("shall", "is required to", "are required to", "it is necessary that")
_MUST_RE = _compile_lexicon(_MUST_TERMS)
_MIXING_INDICATOR_RE = _compile_lexicon(("must", "should"))


def _check_must(artifact, blocks):
    # Severity follows the two anchors in references/PLAIN.md directly.
    # Severity 2 is a single lapse in an otherwise must-consistent
    # document; severity 3 is a document that alternates registers across
    # several separate requirements, so the reader cannot tell which of
    # them are actually mandatory. A document therefore has to carry at
    # least two non-must requirement statements *and* use must or should
    # somewhere before this escalates. Escalating on the mere presence of
    # must anywhere in the document, which an earlier revision did, turned
    # the severity 2 anchor's own scenario into a severity 3 finding.
    non_must_statements = len(_MUST_RE.findall(artifact.text))
    alternates = non_must_statements >= 2 and bool(_MIXING_INDICATOR_RE.search(artifact.text))
    severity = 3 if alternates else 2
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        for sentence in _split_sentences(block["text"]):
            if not _MUST_RE.search(sentence):
                continue
            findings.append(
                RawFinding(
                    criterion="PLAIN-MUST",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=sentence,
                    violation=(
                        "The sentence states a binding requirement using shall or an indirect "
                        "requirement phrasing instead of must."
                    ),
                    fix="Restate the requirement using must.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# PLAIN-NOMINALIZATION
# ---------------------------------------------------------------------------

_SUPPORT_VERBS = (
    "make", "makes", "made", "perform", "performs", "performed",
    "conduct", "conducts", "conducted", "provide", "provides", "provided",
    "give", "gives", "gave", "take", "takes", "took",
)
_NOMINAL_RE = re.compile(
    r"\b(?:" + "|".join(_SUPPORT_VERBS) + r")\b(?:\s+\w+){0,3}?\s+"
    r"(\w+(?:tion|sion|ment|ance|ence))\b",
    re.IGNORECASE,
)


def _check_nominalization(blocks):
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        sentences = _split_sentences(block["text"])
        hits = [s for s in sentences if _NOMINAL_RE.search(s)]
        if not hits:
            continue
        severity = _ratio_severity(len(hits), len(sentences), high_ratio=0.8)
        for sentence in hits:
            match = _NOMINAL_RE.search(sentence)
            findings.append(
                RawFinding(
                    criterion="PLAIN-NOMINALIZATION",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=sentence,
                    violation=(
                        f"The action is buried inside the noun {match.group(1)!r}, carried by a "
                        "generic support verb, instead of stated as the sentence's own main verb."
                    ),
                    fix="Restate the nominalized noun as the sentence's main verb.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# PLAIN-PARAGRAPH
# ---------------------------------------------------------------------------

_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for",
    "with", "is", "are", "was", "were", "be", "been", "being", "this",
    "that", "these", "those", "it", "as", "at", "from", "will", "shall",
    "must", "should", "may", "can", "could", "by", "not",
})
_WORD_TOKEN_RE = re.compile(r"[A-Za-z']+")
_PARAGRAPH_LENGTH_THRESHOLD = 150


def _significant_words(text):
    return [w for w in (t.lower() for t in _WORD_TOKEN_RE.findall(text)) if w not in _STOPWORDS and len(w) > 2]


def _check_paragraph(blocks):
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        text = block["text"]
        sentences = _split_sentences(text)
        if not sentences:
            continue
        word_count = _word_count(text)
        first_sig = set(_significant_words(sentences[0]))
        rest_sig = set()
        for sentence in sentences[1:]:
            rest_sig.update(_significant_words(sentence))

        if len(sentences) >= 3 and first_sig:
            overlap_ratio = len(first_sig & rest_sig) / len(first_sig)
        else:
            overlap_ratio = 1.0

        if len(sentences) >= 3 and overlap_ratio < 0.15:
            findings.append(
                RawFinding(
                    criterion="PLAIN-PARAGRAPH",
                    severity=3,
                    location=_location(heading_text, paragraph_number),
                    evidence=sentences[0],
                    violation=(
                        "The paragraph's opening sentence shares almost no vocabulary with the "
                        "rest of the paragraph, so it does not preview the paragraph's actual topic."
                    ),
                    fix="Rewrite the opening sentence to state the topic the rest of the paragraph covers.",
                )
            )
        elif word_count > _PARAGRAPH_LENGTH_THRESHOLD:
            findings.append(
                RawFinding(
                    criterion="PLAIN-PARAGRAPH",
                    severity=2,
                    location=_location(heading_text, paragraph_number),
                    evidence=f"{word_count} words in one paragraph.",
                    violation=f"The paragraph exceeds the {_PARAGRAPH_LENGTH_THRESHOLD}-word scannability threshold.",
                    fix="Split the paragraph so each part covers one topic.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# PLAIN-PRONOUNS
# ---------------------------------------------------------------------------

_INSTITUTIONAL_SUBSTITUTES = ("the applicant", "the undersigned", "this office", "the department")
_SUBSTITUTE_RE = _compile_lexicon(_INSTITUTIONAL_SUBSTITUTES)


def _check_pronouns(blocks):
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        sentences = _split_sentences(block["text"])
        hits = [s for s in sentences if _SUBSTITUTE_RE.search(s)]
        if not hits:
            continue
        severity = _ratio_severity(len(hits), len(sentences), high_ratio=0.75)
        for sentence in hits:
            findings.append(
                RawFinding(
                    criterion="PLAIN-PRONOUNS",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=sentence,
                    violation=(
                        "The sentence routes the reader or the writer's organization through a "
                        "third-person institutional substitute instead of direct address."
                    ),
                    fix="Address the reader as you and the writer's organization as we.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# PLAIN-SENTENCE-LENGTH
# ---------------------------------------------------------------------------

_SENTENCE_LENGTH_SOFT = 30
_SENTENCE_LENGTH_HARD = 50
_CLAUSE_MARKER_SOFT = 3
_CLAUSE_MARKER_HARD = 4


def _check_sentence_length(blocks):
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        for sentence in _split_sentences(block["text"]):
            words = _word_count(sentence)
            markers = _subordinate_marker_count(sentence)
            if words <= _SENTENCE_LENGTH_SOFT and markers <= _CLAUSE_MARKER_SOFT:
                continue
            severity = 3 if words >= _SENTENCE_LENGTH_HARD or markers >= _CLAUSE_MARKER_HARD else 2
            findings.append(
                RawFinding(
                    criterion="PLAIN-SENTENCE-LENGTH",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=f"{words}-word sentence, {markers} subordinate-clause markers: {sentence}",
                    violation=(
                        f"The sentence runs to {words} words with {markers} subordinate-clause "
                        "markers, longer than the reader can hold in mind on a single pass."
                    ),
                    fix="Split the sentence at a subordinate-clause boundary.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# PLAIN-SUBJECT-VERB-OBJECT
# ---------------------------------------------------------------------------


def _check_subject_verb_object(blocks):
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        for sentence in _split_sentences(block["text"]):
            if len(_split_series_items(sentence)) >= 3:
                continue  # a parallel list, not a subject-verb interruption; PLAIN-LISTS' case
            num_asides, interior_words = _leading_asides(sentence)
            if num_asides < 2 and interior_words < 6:
                continue
            severity = 3 if num_asides >= 2 and interior_words >= 15 else 2
            findings.append(
                RawFinding(
                    criterion="PLAIN-SUBJECT-VERB-OBJECT",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=sentence,
                    violation=(
                        f"{num_asides} comma-set-off clause(s) totalling {interior_words} words "
                        "intervene between the sentence's apparent subject and its verb."
                    ),
                    fix="Move the interrupting clause elsewhere, or split it into its own sentence.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# PLAIN-TRANSITIONS
# ---------------------------------------------------------------------------

_TRANSITION_WORDS = (
    "however", "therefore", "in addition", "as a result", "moreover",
    "furthermore", "consequently", "nevertheless", "meanwhile",
    "similarly", "in contrast", "for example", "for instance", "in fact",
    "indeed", "likewise", "thus", "hence", "accordingly", "otherwise",
    "additionally", "also", "then", "next", "finally", "in summary",
)
_TRANSITION_START_RE = re.compile(
    r"^(?:" + "|".join(re.escape(w) for w in sorted(_TRANSITION_WORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
_TRANSITION_RUN_THRESHOLD = 4


def _check_transitions(blocks):
    findings = []
    pending = []

    def flush():
        if not pending:
            return
        severity = 3 if len(pending) >= _TRANSITION_RUN_THRESHOLD else 2
        for heading_text, paragraph_number, block in pending:
            findings.append(
                RawFinding(
                    criterion="PLAIN-TRANSITIONS",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=_first_words(block["text"], 12),
                    violation=(
                        "The paragraph opens with none of the fixed transition words, so the "
                        "reader is not told how it relates to the paragraph before it."
                    ),
                    fix="Open the paragraph with a transition word that states its relationship to the prior paragraph.",
                )
            )
        pending.clear()

    for heading_text, paragraph_number, block, first_after_heading in _iter_paragraphs(blocks):
        if first_after_heading:
            flush()
            continue
        if _TRANSITION_START_RE.match(block["text"].strip()):
            flush()
            continue
        pending.append((heading_text, paragraph_number, block))
    flush()
    return findings


# ---------------------------------------------------------------------------
# WILLIAMS-PARALLELISM
# ---------------------------------------------------------------------------

_GERUND_RE = re.compile(r"^[a-z]+ing$")

# _split_series_items' first item is whatever precedes the series' first
# comma, which for a series that is the object of a shared verb ("The
# manual covers filing the report, reviewing the log, and closing the
# ticket") still carries that verb's own subject and verb, not the
# item itself; classifying "The" as the head word would always read
# "other" regardless of the series' real form. A closed lexicon of common
# list-introducing verbs strips exactly that leading clause from the
# first item only, before its head word is classified; the other items
# never have this contamination, because everything after the first
# comma is already just the item.
_SERIES_INTRODUCER_RE = re.compile(
    r"\b(?:covers|cover|includes|include|requires|require|involves|involve|"
    r"lists|list|comprises|comprise|needs|need)\s+",
    re.IGNORECASE,
)


def _classify_head(item, *, strip_introducer=False):
    text = item
    if strip_introducer:
        introducer_matches = list(_SERIES_INTRODUCER_RE.finditer(text))
        if introducer_matches:
            text = text[introducer_matches[-1].end():]
    words = text.split()
    if not words:
        return "other"
    first = words[0].lower().strip(".,;:")
    if first == "to" and len(words) > 1:
        return "infinitive"
    if _GERUND_RE.match(first):
        return "gerund"
    return "other"


def _check_parallelism(blocks):
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        for sentence in _split_sentences(block["text"]):
            items = _split_series_items(sentence)
            if len(items) < 2:
                continue
            classes = sorted({
                _classify_head(item, strip_introducer=(index == 0))
                for index, item in enumerate(items)
            })
            if len(classes) < 2:
                continue
            severity = 3 if len(items) >= 4 and len(classes) >= 3 else 2
            findings.append(
                RawFinding(
                    criterion="WILLIAMS-PARALLELISM",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=sentence,
                    violation=(
                        f"The series' {len(items)} items mix grammatical forms ({', '.join(classes)}) "
                        "at their head words instead of sharing one form."
                    ),
                    fix="Restate every item in the series with the same grammatical form.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# WILLIAMS-SHAPE
# ---------------------------------------------------------------------------

_SHAPE_LENGTH_SOFT = 40
_SHAPE_LENGTH_HARD = 60


def _check_shape(blocks):
    findings = []
    for heading_text, paragraph_number, block, _ in _iter_paragraphs(blocks):
        for sentence in _split_sentences(block["text"]):
            words = _word_count(sentence)
            if words < _SHAPE_LENGTH_SOFT:
                continue
            if len(_split_series_items(sentence)) >= 3:
                continue  # a parallel list, not a subordinate-clause pileup; PLAIN-LISTS' case
            num_asides, _interior_words = _leading_asides(sentence)
            markers = _subordinate_marker_count(sentence)
            if num_asides < 2 and markers < 2:
                continue
            severity = 3 if words >= _SHAPE_LENGTH_HARD else 2
            findings.append(
                RawFinding(
                    criterion="WILLIAMS-SHAPE",
                    severity=severity,
                    location=_location(heading_text, paragraph_number),
                    evidence=f"{words}-word sentence: {sentence}",
                    violation=(
                        f"At {words} words, with {num_asides} comma-set-off clause(s) and "
                        f"{markers} subordinate-clause marker(s), the sentence stacks interruptions "
                        "between its subject and its main verb instead of holding the main clause together."
                    ),
                    fix="Move subordinate clauses and modifiers after the main clause, not between its subject and verb.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------


def check(artifact):
    """artifact: skills._shared.artifact.Artifact (artifact.path,
    artifact.text, artifact.sha256). Returns RawFindings, unranked and
    unbounded; run_scripted_lane does the rest."""
    blocks = _parse_blocks(artifact.text)
    findings = []
    findings.extend(_check_active(blocks))
    findings.extend(_check_concise(blocks))
    findings.extend(_check_double_negative(blocks))
    findings.extend(_check_headings(blocks))
    findings.extend(_check_jargon(blocks))
    findings.extend(_check_lists(blocks))
    findings.extend(_check_must(artifact, blocks))
    findings.extend(_check_nominalization(blocks))
    findings.extend(_check_paragraph(blocks))
    findings.extend(_check_pronouns(blocks))
    findings.extend(_check_sentence_length(blocks))
    findings.extend(_check_subject_verb_object(blocks))
    findings.extend(_check_transitions(blocks))
    findings.extend(_check_parallelism(blocks))
    findings.extend(_check_shape(blocks))
    return findings


def main(argv=None):
    return run_scripted_lane(
        skill_name="critique-clarity",
        skill_version="0.1.0",
        rubrics=["PLAIN", "WILLIAMS"],
        check_fn=check,
        argv=argv,
    )


if __name__ == "__main__":
    sys.exit(main())
