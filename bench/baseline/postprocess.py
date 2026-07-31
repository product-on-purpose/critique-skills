"""The envelope post-processing rule: a fixed, deterministic mapping from
the baseline model's raw text response (`prompt.txt`) to a contract-valid
run envelope.

S-03 requires the baseline runner's mapping to be "documented, fixed", so
that a skill-versus-baseline comparison is like-for-like. Every choice
this module makes that is not dictated by the raw text itself is a fixed
policy constant, named and explained at its definition, rather than
something inferred from what the text says: a benchmark comparison is
only fair if the same rule applies no matter what the model wrote.

This module is pure: it reads no file and calls no model. The caller (the
P3 baseline runner, out of this module's scope; see `README.md`) is
responsible for obtaining the raw response and for supplying the run
identity fields (`artifact`, `artifact_sha256`, `model`, `timestamp`) that
only the runner knows.
"""

from __future__ import annotations

import re
from typing import Any

# Bumping any of these three invalidates every published baseline
# comparison and requires a new run set (bench/README.md, "Baseline
# comparison (next stage)": "Any change to the prompt text or the mapping
# rule after the first published run invalidates the comparison").
BASELINE_SKILL = "baseline-generic"
BASELINE_VERSION = "1.0.0"
CONTRACT_VERSION = "1.0.0"

# The baseline has no rubric, so it gets one criterion in a namespace of
# its own: every baseline finding claims BASELINE-GENERIC, and
# run.rubrics always lists exactly ["BASELINE"]. This is the one place in
# the library where a finding's criterion does not cite a published
# source, which is the whole point of a baseline: it is what
# unaccountable generic critique looks like, held up next to skills that
# are accountable by construction.
BASELINE_NAMESPACE = "BASELINE"
BASELINE_CRITERION = "BASELINE-GENERIC"

# The prompt never asks for severity or confidence (asking would require
# rubric-shaped judgment the baseline is deliberately not given), so both
# are fixed policy constants rather than inferred from the text. Severity
# 3 (major) means the baseline's findings are exactly the ones that would
# fail the gate at the default threshold, which is the right default for
# a comparison point: v0.1 metrics do not score severity agreement
# (bench/README.md, "What the bench does not measure"), so this choice
# affects summary.gate and summary.suppressed_count and nothing else.
BASELINE_SEVERITY = 3
BASELINE_CONFIDENCE = "medium"
BASELINE_LANE = "judged"

NO_PROBLEMS_TEXT = "No problems found."

_MAX_LOCATION = 400
_MAX_EVIDENCE = 2000
_MAX_VIOLATION = 1000
_MAX_FIX = 1000

_FIELD_LINE = re.compile(r"^(Location|Evidence|Problem|Fix):\s*(.*)$")
_BLANK_RUN = re.compile(r"\n[ \t]*\n+")
# Built with chr() rather than written literally, so this file carries
# none of the punctuation it exists to strip out of the model's text
# (matching contract/validate.py's own convention for the same reason).
_DASHES = {chr(0x2014): " - ", chr(0x2013): " - "}
_WHITESPACE = re.compile(r"\s+")

# Methodology section 7 (output bounding): report every severity 3 and 4
# finding, plus at most this many below that threshold.
_OUTPUT_BOUND_BELOW_SEVERITY_3 = 5


def _split_blocks(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    return [b for b in _BLANK_RUN.split(normalized) if b.strip()]


def _parse_block(block_text: str) -> dict[str, str] | None:
    """Parse one block into its four labeled fields. A line that does not
    open a new field is treated as a continuation of whichever field
    opened most recently (joined with a space), so a model that wraps a
    long line across two lines is not silently truncated. A field named
    twice keeps its first occurrence. Returns None, meaning "drop this
    block", when any of the four required fields never appeared with
    non-empty content: the mapping rule reports only what it could
    parse, never invents a location or a fix.
    """
    fields: dict[str, str] = {}
    current: str | None = None
    for raw_line in block_text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        match = _FIELD_LINE.match(line)
        if match:
            key, value = match.group(1), match.group(2).strip()
            if key not in fields:
                fields[key] = value
                current = key
            else:
                current = None  # a repeated label is not a continuation target
        elif current is not None:
            fields[current] = f"{fields[current]} {line}".strip()
    required = ("Location", "Evidence", "Problem", "Fix")
    if not all(fields.get(k) for k in required):
        return None
    return fields


def _sanitize_prose(text: str, *, max_length: int) -> str:
    """Contract prose fields reject U+2014/U+2013 and require no leading
    or trailing whitespace (contract/README.md, "No em dash, no en
    dash"). The baseline model was never told this rule, so this
    function enforces it on its behalf rather than letting a stray dash
    turn a whole envelope contract-invalid. Overlong fields are
    truncated to the schema's max length: a truncated but contract-valid
    envelope is preferred to a faithful-but-invalid one.
    """
    for bad, replacement in _DASHES.items():
        text = text.replace(bad, replacement)
    text = _WHITESPACE.sub(" ", text).strip()
    if len(text) > max_length:
        text = text[:max_length].rstrip()
    return text


def _build_finding(fields: dict[str, str]) -> dict[str, Any]:
    return {
        "criterion": BASELINE_CRITERION,
        "lane": BASELINE_LANE,
        "severity": BASELINE_SEVERITY,
        "location": _sanitize_prose(fields["Location"], max_length=_MAX_LOCATION),
        "evidence": _sanitize_prose(fields["Evidence"], max_length=_MAX_EVIDENCE),
        "violation": _sanitize_prose(fields["Problem"], max_length=_MAX_VIOLATION),
        "fix": _sanitize_prose(fields["Fix"], max_length=_MAX_FIX),
        "confidence": BASELINE_CONFIDENCE,
    }


def _apply_output_bound(findings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Methodology section 7: every severity 3 and 4 finding is kept,
    plus at most `_OUTPUT_BOUND_BELOW_SEVERITY_3` below that threshold,
    ranked by severity descending. Every baseline finding is
    `BASELINE_SEVERITY` (3) by fixed policy, so this never actually
    suppresses anything today; it is applied rather than assumed, so a
    future change to that constant cannot silently violate the bound.
    """
    high = [f for f in findings if f["severity"] >= 3]
    low = sorted((f for f in findings if f["severity"] < 3), key=lambda f: -f["severity"])
    kept_low = low[: _OUTPUT_BOUND_BELOW_SEVERITY_3]
    return high + kept_low, len(low) - len(kept_low)


def parse_findings(raw_response: str) -> list[dict[str, Any]]:
    """Parse a raw baseline response into findings, before output
    bounding and before `id` assignment. Exposed on its own so a caller
    can inspect what was parsed independently of envelope assembly.
    """
    stripped = raw_response.strip()
    if stripped == NO_PROBLEMS_TEXT:
        return []
    findings = []
    for block_text in _split_blocks(stripped):
        fields = _parse_block(block_text)
        if fields is not None:
            findings.append(_build_finding(fields))
    return findings


def postprocess(
    raw_response: str,
    *,
    artifact: str,
    artifact_sha256: str,
    model: str,
    timestamp: str,
) -> dict[str, Any]:
    """Map one raw baseline response to a contract-valid run envelope.

    `artifact`, `artifact_sha256`, `model`, and `timestamp` are supplied
    by the caller (the P3 runner), which is the only place that knows
    them; this function does no file I/O and calls no model.
    """
    parsed = parse_findings(raw_response)
    emitted, suppressed_count = _apply_output_bound(parsed)
    for index, finding in enumerate(emitted, start=1):
        finding["id"] = f"F-{index:03d}"

    counts = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0}
    for finding in parsed:  # every finding produced, suppressed ones included
        counts[str(finding["severity"])] += 1
    gate = "fail" if (counts["4"] > 0 or counts["3"] > 0) else "pass"

    return {
        "run": {
            "skill": BASELINE_SKILL,
            "skill_version": BASELINE_VERSION,
            "contract_version": CONTRACT_VERSION,
            "artifact": artifact,
            "artifact_sha256": artifact_sha256,
            "model": model,
            "timestamp": timestamp,
            "rubrics": [BASELINE_NAMESPACE],
        },
        "findings": emitted,
        "summary": {
            "by_severity": counts,
            "suppressed_count": suppressed_count,
            "gate": gate,
            "severity_3_threshold": 0,
        },
    }
