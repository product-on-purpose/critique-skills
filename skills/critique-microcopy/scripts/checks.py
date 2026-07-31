"""critique-microcopy scripted lane: NNG-EM-CONSTRUCTIVE, NNG-EM-NEUTRAL-TONE,
NNG-EM-NOT-COLOR-ONLY, NNG-EM-PLAIN-LANGUAGE, NNG-EM-PRESERVE-INPUT,
NNG-EM-TIMING. See docs/internal/skill-template.md, "Wiring scripts/checks.py",
for the pattern this file follows, and skills/critique-microcopy/references/NNG-EM.md
for the operational test and lane rationale each check below implements.

Artifact grammar. Per ADR 0018 (microcopy artifact format), the artifact is
one or more screens, each a markdown heading naming the screen or state, and
under each heading one labeled block per message:

    ## Signup form, email field

    Message: Please enter a valid email address.
    Placement: directly below the email input field
    Container: inline
    Signal: same weight as the label text, icon
    Fires: on-blur
    Predictable mistake: yes
    Input on resubmission: preserved
    Suggested fix: none

Each field is its own physical line, "Label: value"; a value that wraps onto
a further physical line with no label of its own is folded into the previous
field. A message block is recognized by its first line reading exactly
"Message: ..."; everything else under the heading is ignored (free prose
introducing the screen, for instance). ADR 0018 leaves the concrete line
syntax for this grammar to "the first corpus-module and checks.py authors to
build against it"; the one-field-per-line form above is this file's choice,
and it is what bench/generator/domains/microcopy.py and this skill's
examples/*.json must compose artifacts in to stay parseable by this module.

Bare-message fallback. SKILL.md's protocol also accepts a bare list of
message strings with no screen annotation, for which the three annotation
field checks below (NOT-COLOR-ONLY, PRESERVE-INPUT, TIMING) have nothing to
evaluate. A bare message is either a plain paragraph (one paragraph is one
message) or one item of a markdown bullet list (one item is one message);
either way, the three message-text-only checks (CONSTRUCTIVE, NEUTRAL-TONE,
PLAIN-LANGUAGE) still run against it in full.
"""

from __future__ import annotations

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
# name exactly the same set. All six of NNG-EM.md's declared scripted
# criteria stayed genuinely scriptable during implementation; none moved to
# the judged lane.
IMPLEMENTED_CRITERIA = frozenset({
    "NNG-EM-CONSTRUCTIVE",
    "NNG-EM-NEUTRAL-TONE",
    "NNG-EM-NOT-COLOR-ONLY",
    "NNG-EM-PLAIN-LANGUAGE",
    "NNG-EM-PRESERVE-INPUT",
    "NNG-EM-TIMING",
})

# --------------------------------------------------------------------------
# Fixed vocabularies. Every one of these is this file's own closed list,
# invented for this v0.1 implementation the same way ADR 0018 anticipated
# ("a downstream ... scripts/checks.py author ... extends the set
# additively, never repurposes an existing token's meaning"). Extend rather
# than repurpose.
# --------------------------------------------------------------------------

# NNG-EM-CONSTRUCTIVE. Concrete action verbs and named next-step phrases.
# Deliberately excludes bare "try" / "try again": docs/reference/
# severity-scale.md's own Microcopy domain anchor cites "Something went
# wrong. Try again." as the canonical severity-3 example of a message with
# no real instruction, so treating "try" alone as an instruction would
# fail to flag the library's own worked example.
INSTRUCTION_MARKERS = (
    "enter", "re-enter", "reenter", "re-type", "retype", "choose", "select",
    "remove", "delete", "check", "verify", "confirm", "add", "update",
    "correct", "fix", "provide", "attach", "upload", "click", "tap",
    "contact", "reduce", "increase", "review", "change", "edit", "complete",
    "fill in", "submit", "reset", "refresh", "sign in", "log in", "close",
    "clear the", "shorten", "include", "specify", "wait",
)

# NNG-EM-NEUTRAL-TONE. Second-person accusatory constructions.
BLAME_PHRASES = (
    "you failed to", "you forgot", "your mistake", "you should have",
    "your fault", "you didn't", "you did not", "you neglected",
    "you incorrectly", "you keep", "your error", "you clearly",
    "you obviously",
)

# Frequency markers (severity-scale.md's weighing order, factor 2): a blame
# phrase paired with one of these reads as framing a recurring mistake as a
# personal failing, which NNG-EM.md's own severity-3 anchor for this
# criterion is built on ("you keep entering the wrong password").
REPETITION_MARKERS = ("keep", "again", "repeatedly", "every time", "once more", "still")

# NNG-EM-PLAIN-LANGUAGE. A fixed engineering-jargon phrase list plus two
# patterns for bare codes: SCREAMING_SNAKE / hex / ERR-prefixed tokens, and
# an explicit status/error-code phrase.
JARGON_TERMS = (
    "null", "undefined", "nullpointerexception", "stack trace", "stacktrace",
    "traceback", "segmentation fault", "segfault", "backend", "api error",
    "runtime error", "internal server error", "regex", "json parse",
    "syntax error", "sql error",
)
CODE_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:[A-Z]{2,}[_-][A-Z0-9_-]*|0x[0-9A-Fa-f]+|ERR\d+|E\d{3,4})(?![A-Za-z0-9])"
)
STATUS_CODE_RE = re.compile(
    r"\b(?:status\s+code|error\s+code|http\s+status)\s*[:#]?\s*\d{3}\b", re.IGNORECASE
)

# NNG-EM-TIMING. The Fires field's disallowed tokens (bench README /
# NNG-EM.md controlled vocabulary), and a fixed error-tone marker list used
# only to tier severity, not to decide the violation itself.
TIMING_VIOLATION_TOKENS = frozenset({"mid-keystroke", "on-load-before-input"})
ERROR_TONE_MARKERS = (
    "invalid", "incorrect", "not valid", "must be", "is required", "wrong",
    "please enter a valid", "failed", "error",
)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_MARKER_RE = re.compile(r"^[-*+]\s+(.*)$")
_FIELD_LABELS = (
    "Message", "Placement", "Container", "Signal", "Fires",
    "Predictable mistake", "Input on resubmission", "Suggested fix",
)
_FIELD_LINE_RE = re.compile(
    r"^(" + "|".join(re.escape(label) for label in _FIELD_LABELS) + r"):\s*(.*)$"
)


def _matches_any(text: str, phrases) -> bool:
    return any(re.search(rf"\b{re.escape(phrase)}\b", text, re.IGNORECASE) for phrase in phrases)


def _split_blocks(text):
    """Split artifact text into (kind, lines, start_line) blocks: 'heading',
    'list', or 'body'. A blank line (whitespace only) always ends the
    current block. This is the shape bench/README.md's normative block
    parser ("The block parser (normative)") also uses for markdown-prose;
    fenced code blocks are not a shape this artifact grammar produces, so
    unlike that module this parser does not special-case them.
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
            blocks.append(("heading", [heading_match.group(2).strip()], i + 1))
            i += 1
            continue
        list_match = _LIST_MARKER_RE.match(line)
        if list_match:
            start_line = i + 1
            item_lines = []
            while i < n and lines[i].strip():
                match = _LIST_MARKER_RE.match(lines[i])
                if not match:
                    break
                item_lines.append(match.group(1).strip())
                i += 1
            blocks.append(("list", item_lines, start_line))
            continue
        start_line = i + 1
        body_lines = []
        while i < n and lines[i].strip() and not _HEADING_RE.match(lines[i]) and not _LIST_MARKER_RE.match(lines[i]):
            body_lines.append(lines[i].strip())
            i += 1
        blocks.append(("body", body_lines, start_line))
    return blocks


def _parse_annotated_block(body_lines):
    """Parse a body block's lines into a field dict, folding an unlabeled
    continuation line into whatever field preceded it. Returns None when
    the block does not open with a recognized 'Message:' line, meaning it
    is not a message annotation block at all (introductory screen prose,
    for instance)."""
    if not body_lines or not _FIELD_LINE_RE.match(body_lines[0]):
        return None
    fields: dict[str, str] = {}
    current_label = None
    for raw_line in body_lines:
        match = _FIELD_LINE_RE.match(raw_line)
        if match:
            current_label = match.group(1)
            fields[current_label] = match.group(2).strip()
        elif current_label is not None:
            fields[current_label] = (fields[current_label] + " " + raw_line).strip()
    return fields if "Message" in fields else None


def _parse_messages(text):
    """artifact.text -> list of message dicts: heading, index (1-based,
    reset per heading section), kind ('annotated' or 'bare'), fields (dict
    or None), text (the message string), section_total (message count in
    the same section, used by NNG-EM-PRESERVE-INPUT's severity signal).

    The bare-message fallback is a document-level mode, not a per-block
    one: SKILL.md's protocol describes "a bare-string-list artifact" as a
    whole-document shape, not a block that happens to lack labels. So if
    the document contains at least one recognized 'Message:' block
    anywhere, the whole document is annotated mode, and any other
    paragraph or list content (screen prose introducing a heading, for
    instance) is ignored rather than swept up as a bare message. Only a
    document with zero annotated blocks falls back to bare mode, in which
    every paragraph and every list item counts as one message.
    """
    blocks = _split_blocks(text)
    has_annotated_block = any(
        kind == "body" and content and _FIELD_LINE_RE.match(content[0])
        for kind, content, _start_line in blocks
    )

    heading_text = None
    section_counter = 0
    messages = []

    for kind, content, start_line in blocks:
        if kind == "heading":
            heading_text = content[0]
            section_counter = 0
            continue

        if kind == "list":
            if has_annotated_block:
                continue
            for item_text in content:
                if not item_text:
                    continue
                section_counter += 1
                messages.append({
                    "heading": heading_text,
                    "index": section_counter,
                    "kind": "bare",
                    "fields": None,
                    "text": item_text,
                    "line": start_line,
                })
            continue

        # kind == "body"
        fields = _parse_annotated_block(content)
        if fields is not None:
            section_counter += 1
            messages.append({
                "heading": heading_text,
                "index": section_counter,
                "kind": "annotated",
                "fields": fields,
                "text": fields["Message"],
                "line": start_line,
            })
            continue

        if has_annotated_block:
            continue

        message_text = " ".join(content).strip()
        if not message_text:
            continue
        section_counter += 1
        messages.append({
            "heading": heading_text,
            "index": section_counter,
            "kind": "bare",
            "fields": None,
            "text": message_text,
            "line": start_line,
        })

    totals: dict[str | None, int] = {}
    for message in messages:
        totals[message["heading"]] = totals.get(message["heading"], 0) + 1
    for message in messages:
        message["section_total"] = totals[message["heading"]]

    return messages


def _location(message, suffix=None):
    base = (
        f"{message['heading']}, message {message['index']}"
        if message["heading"]
        else f"message {message['index']}"
    )
    return f"{base}, {suffix}" if suffix else base


def _check_constructive(message):
    text = message["text"]
    if _matches_any(text, INSTRUCTION_MARKERS):
        return []
    fields = message["fields"] or {}
    suggested_token = (fields.get("Suggested fix") or "").split(",")[0].strip().lower()
    severity = 2 if suggested_token in ("described", "selectable") else 3
    return [
        RawFinding(
            criterion="NNG-EM-CONSTRUCTIVE",
            severity=severity,
            location=_location(message),
            evidence=text,
            violation=(
                "The message states that a problem exists with no imperative instruction "
                "or named next step anywhere in the text."
            ),
            fix="Add a concrete next step: name the action the reader should take to resolve this.",
        )
    ]


def _check_neutral_tone(message):
    text = message["text"]
    if not _matches_any(text, BLAME_PHRASES):
        return []
    severity = 3 if _matches_any(text, REPETITION_MARKERS) else 2
    return [
        RawFinding(
            criterion="NNG-EM-NEUTRAL-TONE",
            severity=severity,
            location=_location(message),
            evidence=text,
            violation=(
                "The message frames the problem as something the reader personally did wrong "
                "or should have known better than to do, using a second-person accusatory "
                "construction."
            ),
            fix="Rewrite the sentence to state the problem neutrally, without blaming the reader.",
        )
    ]


def _find_jargon_span(text):
    match = CODE_TOKEN_RE.search(text)
    if match:
        return match.span()
    match = STATUS_CODE_RE.search(text)
    if match:
        return match.span()
    # Whole words only. A bare substring scan matches JARGON_TERMS inside
    # ordinary vocabulary a real message can carry (null inside annulled,
    # for one), which is a false positive on a scripted criterion, where a
    # false positive is the expensive kind: the lane's whole claim is that
    # the same text produces the same, defensible verdict every run.
    for term in JARGON_TERMS:
        match = re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE)
        if match:
            return match.span()
    return None


def _check_plain_language(message):
    text = message["text"]
    span = _find_jargon_span(text)
    if span is None:
        return []
    remainder = (text[: span[0]] + " " + text[span[1]:]).strip()
    remaining_words = re.findall(r"[A-Za-z']+", remainder)
    severity = 3 if len(remaining_words) <= 3 else 2
    return [
        RawFinding(
            criterion="NNG-EM-PLAIN-LANGUAGE",
            severity=severity,
            location=_location(message),
            evidence=text,
            violation=(
                "The message text carries an internal error code, a code-style token, or an "
                "engineering-jargon term standing in for a plain-language explanation."
            ),
            fix="Replace the code or jargon term with a plain-language sentence a non-technical reader can act on.",
        )
    ]


def _signal_token(value):
    if not value:
        return None
    parts = [part.strip() for part in value.split(",")]
    return parts[-1].lower() if parts else None


def _check_not_color_only(message):
    fields = message["fields"]
    if not fields:
        return []
    token = _signal_token(fields.get("Signal"))
    if token != "none":
        return []
    container = (fields.get("Container") or "").strip().lower()
    severity = 3 if container == "toast" else 2
    return [
        RawFinding(
            criterion="NNG-EM-NOT-COLOR-ONLY",
            severity=severity,
            location=_location(message, "Signal field"),
            evidence=f"Signal: {fields.get('Signal', '')}",
            violation=(
                "The Signal field's non-color-cue token is none, so color or highlight is the "
                "message's only stated cue."
            ),
            fix="Add a non-color cue: an icon, a text label, a shape change, or bold or underline styling.",
        )
    ]


def _check_preserve_input(message):
    fields = message["fields"]
    if not fields:
        return []
    token = (fields.get("Input on resubmission") or "").strip().lower()
    if token != "cleared":
        return []
    severity = 3 if message["section_total"] >= 3 else 2
    return [
        RawFinding(
            criterion="NNG-EM-PRESERVE-INPUT",
            severity=severity,
            location=_location(message, "Input on resubmission field"),
            evidence=f"Input on resubmission: {fields.get('Input on resubmission', '')}",
            violation=(
                "A failed submission clears what the reader already entered instead of "
                "preserving it so they can correct the specific problem in place."
            ),
            fix="Preserve the reader's entered input across the failed submission.",
        )
    ]


def _check_timing(message):
    fields = message["fields"]
    if not fields:
        return []
    token = (fields.get("Fires") or "").strip().lower()
    if token not in TIMING_VIOLATION_TOKENS:
        return []
    severity = 3 if _matches_any(message["text"], ERROR_TONE_MARKERS) else 2
    return [
        RawFinding(
            criterion="NNG-EM-TIMING",
            severity=severity,
            location=_location(message, "Fires field"),
            evidence=f"Fires: {fields.get('Fires', '')}",
            violation=(
                "The message can appear before the reader has had a fair chance to finish "
                "entering the relevant input."
            ),
            fix="Delay the message until the field loses focus or the form is submitted, not while the reader is still typing or before they have entered anything.",
        )
    ]


def check(artifact):
    """artifact: skills._shared.artifact.Artifact (artifact.path,
    artifact.text, artifact.sha256). Returns RawFindings, unranked and
    unbounded; run_scripted_lane does the rest."""
    findings = []
    for message in _parse_messages(artifact.text):
        findings.extend(_check_constructive(message))
        findings.extend(_check_neutral_tone(message))
        findings.extend(_check_plain_language(message))
        findings.extend(_check_not_color_only(message))
        findings.extend(_check_preserve_input(message))
        findings.extend(_check_timing(message))
    return findings


def main(argv=None):
    return run_scripted_lane(
        skill_name="critique-microcopy",
        skill_version="0.1.0",
        # The criterion namespace, not the rubric_sources.id: NNG-EM-* IDs
        # carry namespace NNG (the text before the FIRST hyphen), shared on
        # purpose with critique-usability's NNG-H* IDs. See
        # docs/reference/criterion-ids.md, "Namespace registry".
        rubrics=["NNG"],
        check_fn=check,
        argv=argv,
    )


if __name__ == "__main__":
    sys.exit(main())
