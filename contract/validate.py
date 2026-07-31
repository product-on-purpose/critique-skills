"""Validator for the critique-skills machine-parseable contract.

This module is both an importable library and a CLI. It validates a
document against `critique-contract.schema.json` (JSON Schema draft
2020-12) and then applies the rules the schema cannot express: the ones
listed in `contract/README.md` under "Rules the validator enforces
beyond the schema". Where this module and `contract/README.md` disagree,
the README is correct and this module is a bug.

Library usage:

    from contract.validate import validate_document, load_document

    doc = load_document("envelope.json")
    result = validate_document(doc)
    if not result.ok:
        for issue in result.errors:
            print(issue)

CLI usage:

    python -m contract.validate <file.json>
    python -m contract.validate <file.json> --gate [--threshold N] [--strict]

Without --gate the CLI exits 0 when the document is valid and 1 when it
is not. With --gate it exits 0 (clean), 1 (any severity 4), 2 (severity-3
count above the threshold), 3 (not a contract-valid document), or 4
(usage error: bad arguments, unreadable or unparseable file).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent / "critique-contract.schema.json"

SEVERITY_KEYS = ("0", "1", "2", "3", "4")

# Rule 8 (methodology section 7 output bounding): at most five emitted
# findings below severity 3. A warning in contract 1.x; --strict promotes
# it to an error.
OUTPUT_BOUND_BELOW_SEVERITY_3 = 5

# Rule 9: house style, enforced over the whole document rather than only
# over the prose fields the schema patterns reach. `finding.selector` is
# the one object the schema leaves unvalidated, so a pattern-only defence
# leaves it open as a smuggling channel, for keys as well as values. The
# characters are built with chr() so this file carries none of the
# punctuation it exists to reject.
DASH_CHARACTERS = {chr(0x2014): "U+2014 em dash", chr(0x2013): "U+2013 en dash"}

# Rule 10: the shape of a timestamp is a schema pattern; whether it names
# a real instant is not. RFC 3339 permits second 60 for a leap second,
# which datetime cannot represent, so it is clamped before the check.
_TIMESTAMP_RE = re.compile(
    r"^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.[0-9]{1,9})?Z$"
)


# --------------------------------------------------------------------------
# Schema loading
# --------------------------------------------------------------------------


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    """Load and return the contract schema document.

    Cached: the file is read once per process.
    """
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def _root_validator() -> jsonschema.Draft202012Validator:
    """A validator for the schema root (envelope or disposition log, per
    the root's own if/then/else dispatch on the 'dispositions' key)."""
    schema = load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


@lru_cache(maxsize=1)
def _finding_validator() -> jsonschema.Draft202012Validator:
    """A validator scoped to a single bare finding (#/$defs/finding).

    The root schema only dispatches to envelope or disposition log, so a
    bare finding is validated against this narrower schema instead. See
    contract/README.md: "To validate a bare finding, reference
    #/$defs/finding directly."
    """
    schema = load_schema()
    finding_schema = {"$ref": "#/$defs/finding", "$defs": schema["$defs"]}
    return jsonschema.Draft202012Validator(finding_schema)


# --------------------------------------------------------------------------
# Issues and results
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Issue:
    """One validation problem: where it is and what is wrong.

    `path` is a dotted, bracketed instance path such as
    "findings[0].location" or "run.timestamp"; the empty string means the
    document root. `rule` names the check that raised the issue, either a
    jsonschema validator keyword (e.g. "required", "pattern") or one of
    this module's own rule names (e.g. "unique-finding-ids").
    """

    path: str
    message: str
    rule: str

    def __str__(self) -> str:
        location = self.path if self.path else "<root>"
        return f"{location}: {self.message}"


@dataclass
class ValidationResult:
    """Errors block validity; warnings do not unless promoted by --strict."""

    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def with_strict(self) -> "ValidationResult":
        """Return a result with warnings promoted to errors."""
        return ValidationResult(errors=self.errors + self.warnings, warnings=[])


# --------------------------------------------------------------------------
# Path formatting and schema-level errors
# --------------------------------------------------------------------------


_REQUIRED_FIELD_RE = re.compile(r"^'([^']+)' is a required property$")


def _format_instance_path(path: Any) -> str:
    """Render a jsonschema error's instance path as "a.b[2].c"."""
    parts: list[str] = []
    for step in path:
        if isinstance(step, int):
            if parts:
                parts[-1] = f"{parts[-1]}[{step}]"
            else:
                parts.append(f"[{step}]")
        else:
            parts.append(str(step))
    return ".".join(parts)


def _format_schema_error(error: jsonschema.exceptions.ValidationError) -> Issue:
    base_path = _format_instance_path(list(error.path))
    if error.validator == "required":
        match = _REQUIRED_FIELD_RE.match(error.message)
        field_name = match.group(1) if match else error.message
        full_path = f"{base_path}.{field_name}" if base_path else field_name
        return Issue(
            path=full_path,
            message=f"missing required field '{field_name}'",
            rule="required",
        )
    return Issue(path=base_path, message=error.message, rule=str(error.validator))


def _schema_errors(validator: jsonschema.Draft202012Validator, instance: Any) -> list[Issue]:
    return [_format_schema_error(e) for e in validator.iter_errors(instance)]


# --------------------------------------------------------------------------
# Document classification
# --------------------------------------------------------------------------


def document_kind(doc: Any) -> str:
    """Classify a document the way the schema root does: a document
    carrying a 'dispositions' key is a disposition log, everything else
    (including a malformed document) is treated as a run envelope."""
    if isinstance(doc, dict) and "dispositions" in doc:
        return "dispositionLog"
    return "envelope"


def load_document(path: str | Path) -> Any:
    """Read and parse a JSON document from disk.

    Raises OSError if the file cannot be read and json.JSONDecodeError if
    it is not valid JSON; the CLI treats both as usage errors.
    """
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)


# --------------------------------------------------------------------------
# Bare finding validation
# --------------------------------------------------------------------------


def validate_finding(finding: Any) -> list[Issue]:
    """Validate a single finding object against #/$defs/finding.

    Applies the schema plus rule 9 (no em dash, no en dash anywhere),
    which is the one validator rule scoped to a finding rather than to an
    envelope. See contract/README.md, "What the schema does not check",
    for the review-lane rules this function cannot enforce.
    """
    return _schema_errors(_finding_validator(), finding) + _rule_no_dash(finding)


# --------------------------------------------------------------------------
# Rules the schema cannot express (contract/README.md rules 1-7, 9, 10)
# --------------------------------------------------------------------------


def _as_namespace(criterion: Any) -> str | None:
    if not isinstance(criterion, str) or "-" not in criterion:
        return None
    return criterion.split("-", 1)[0]


def _rule_unique_finding_ids(doc: dict[str, Any]) -> list[Issue]:
    """Rule 1: finding IDs are unique within an envelope."""
    findings = doc.get("findings")
    if not isinstance(findings, list):
        return []
    seen: dict[str, list[int]] = {}
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            continue
        finding_id = finding.get("id")
        if not isinstance(finding_id, str):
            continue
        seen.setdefault(finding_id, []).append(index)
    issues: list[Issue] = []
    for finding_id, indices in seen.items():
        if len(indices) > 1:
            where = ", ".join(f"findings[{i}]" for i in indices)
            issues.append(
                Issue(
                    path="findings",
                    message=f"duplicate finding id '{finding_id}' at {where}",
                    rule="unique-finding-ids",
                )
            )
    return issues


def _as_count(value: Any) -> int | None:
    """Read a count that the schema has typed as an integer.

    Integral floats are accepted here on purpose. JSON Schema's "integer"
    type admits 3.0, so `json.loads` hands this module a float for a
    document written with "3.0"; rule 6 reports that separately. If this
    helper rejected the float instead, rules 2, 3, and 4 would silently
    skip, and an envelope could hide a severity-4 finding behind a
    histogram of 0.0 and pass the gate. Returns None only for a value
    that is not a number at all, which the schema has already reported.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _by_severity_counts(by_severity: Any) -> dict[str, int] | None:
    if not isinstance(by_severity, dict):
        return None
    counts: dict[str, int] = {}
    for key in SEVERITY_KEYS:
        count = _as_count(by_severity.get(key))
        if count is None:
            return None
        counts[key] = count
    return counts


def _emitted_severity_counts(findings: list[Any]) -> dict[str, int]:
    counts = {key: 0 for key in SEVERITY_KEYS}
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        severity = finding.get("severity")
        if isinstance(severity, bool) or not isinstance(severity, int):
            continue
        key = str(severity)
        if key in counts:
            counts[key] += 1
    return counts


def _rule_histogram_reconciles(doc: dict[str, Any]) -> list[Issue]:
    """Rule 2: sum(by_severity) equals len(findings) plus suppressed_count."""
    findings = doc.get("findings")
    summary = doc.get("summary")
    if not isinstance(findings, list) or not isinstance(summary, dict):
        return []
    counts = _by_severity_counts(summary.get("by_severity"))
    suppressed = _as_count(summary.get("suppressed_count"))
    if counts is None or suppressed is None:
        return []
    total = sum(counts.values())
    expected = len(findings) + suppressed
    if total != expected:
        return [
            Issue(
                path="summary.by_severity",
                message=(
                    f"histogram total {total} does not equal len(findings) "
                    f"({len(findings)}) plus suppressed_count ({suppressed})"
                ),
                rule="histogram-reconciles",
            )
        ]
    return []


def _rule_severity_3_4_not_suppressed(doc: dict[str, Any]) -> list[Issue]:
    """Rule 3: severity 3 and 4 counts equal emitted counts exactly;
    severity 0-2 counts are at least the emitted counts."""
    findings = doc.get("findings")
    summary = doc.get("summary")
    if not isinstance(findings, list) or not isinstance(summary, dict):
        return []
    counts = _by_severity_counts(summary.get("by_severity"))
    if counts is None:
        return []
    emitted = _emitted_severity_counts(findings)
    issues: list[Issue] = []
    for key in ("3", "4"):
        if counts[key] != emitted[key]:
            issues.append(
                Issue(
                    path=f"summary.by_severity.{key}",
                    message=(
                        f"severity {key} is never suppressed: recorded count "
                        f"{counts[key]} must equal the emitted count {emitted[key]}"
                    ),
                    rule="severity-3-4-not-suppressed",
                )
            )
    for key in ("0", "1", "2"):
        if counts[key] < emitted[key]:
            issues.append(
                Issue(
                    path=f"summary.by_severity.{key}",
                    message=(
                        f"recorded count {counts[key]} is less than the emitted "
                        f"count {emitted[key]}"
                    ),
                    rule="severity-3-4-not-suppressed",
                )
            )
    return issues


def _rule_gate_recomputed(doc: dict[str, Any]) -> list[Issue]:
    """Rule 4: summary.gate must equal the recomputed verdict."""
    summary = doc.get("summary")
    if not isinstance(summary, dict):
        return []
    counts = _by_severity_counts(summary.get("by_severity"))
    threshold = _as_count(summary.get("severity_3_threshold"))
    gate = summary.get("gate")
    if counts is None or threshold is None:
        return []
    if gate not in ("pass", "fail"):
        return []
    expected = "fail" if (counts["4"] > 0 or counts["3"] > threshold) else "pass"
    if gate != expected:
        return [
            Issue(
                path="summary.gate",
                message=f"gate is '{gate}', recomputed verdict is '{expected}'",
                rule="gate-recomputed",
            )
        ]
    return []


def _rule_rubrics_cover_findings(doc: dict[str, Any]) -> list[Issue]:
    """Rule 5: every finding's criterion namespace appears in run.rubrics."""
    run = doc.get("run")
    findings = doc.get("findings")
    if not isinstance(run, dict) or not isinstance(findings, list):
        return []
    rubrics = run.get("rubrics")
    if not isinstance(rubrics, list):
        return []
    rubric_set = {r for r in rubrics if isinstance(r, str)}
    issues: list[Issue] = []
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            continue
        namespace = _as_namespace(finding.get("criterion"))
        if namespace is None:
            continue
        if namespace not in rubric_set:
            issues.append(
                Issue(
                    path=f"findings[{index}].criterion",
                    message=(
                        f"namespace '{namespace}' is not listed in run.rubrics "
                        f"{sorted(rubric_set)}"
                    ),
                    rule="rubrics-cover-findings",
                )
            )
    return issues


def _integer_literal_issue(path: str, value: Any) -> Issue | None:
    if not isinstance(value, float):
        return None
    return Issue(
        path=path,
        message=(
            f"must be a JSON integer literal (e.g. {int(value)} if that is the "
            f"intended value, not {value!r})"
        ),
        rule="integer-literal",
    )


def _rule_integer_literal(doc: dict[str, Any]) -> list[Issue]:
    """Rule 6: every integer-typed contract field must be a JSON integer
    literal. JSON Schema's "integer" type accepts 3.0, so a document
    written with "3.0" parses to a Python float that the schema admits.

    This covers the whole summary, not just severity. A float in the
    histogram, in suppressed_count, or in severity_3_threshold is the
    load-bearing case: those three feed rules 2, 3, and 4, and a
    by_severity of {"4": 0.0} beside an emitted severity-4 finding would
    otherwise be a contract-valid envelope that exits the gate at 0.
    """
    issues: list[Issue] = []

    findings = doc.get("findings")
    if isinstance(findings, list):
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue
            issue = _integer_literal_issue(
                f"findings[{index}].severity", finding.get("severity")
            )
            if issue is not None:
                issues.append(issue)

    summary = doc.get("summary")
    if isinstance(summary, dict):
        for key in ("suppressed_count", "severity_3_threshold"):
            issue = _integer_literal_issue(f"summary.{key}", summary.get(key))
            if issue is not None:
                issues.append(issue)
        by_severity = summary.get("by_severity")
        if isinstance(by_severity, dict):
            for key in SEVERITY_KEYS:
                issue = _integer_literal_issue(
                    f"summary.by_severity.{key}", by_severity.get(key)
                )
                if issue is not None:
                    issues.append(issue)

    return issues


def _iter_strings(node: Any, path: str = "") -> Iterator[tuple[str, str, bool]]:
    """Walk every string in a document, yielding (path, text, is_key).

    Object keys are yielded as well as values, because the one object the
    schema does not constrain (`selector`) accepts arbitrary keys.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}" if path else str(key)
            if isinstance(key, str):
                yield child, key, True
            yield from _iter_strings(value, child)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            child = f"{path}[{index}]" if path else f"[{index}]"
            yield from _iter_strings(item, child)
    elif isinstance(node, str):
        yield path, node, False


def _rule_no_dash(doc: Any) -> list[Issue]:
    """Rule 9: no em dash and no en dash anywhere in the document.

    The schema enforces this by pattern on every field it types as prose,
    which is every string field except the reserved `selector` object and
    its keys. The spec requires the validator to reject an envelope
    carrying either character in any string field, so the check runs over
    the parsed document rather than over the fields the schema happens to
    reach. This also holds for any field a later minor version adds.
    """
    issues: list[Issue] = []
    for path, text, is_key in _iter_strings(doc):
        for character, name in DASH_CHARACTERS.items():
            if character in text:
                where = "key" if is_key else "value"
                issues.append(
                    Issue(
                        path=path if path else "<root>",
                        message=(
                            f"{where} contains a {name}; use ' - ', a comma, or a "
                            f"colon, and a plain hyphen for numeric ranges"
                        ),
                        rule="no-dash",
                    )
                )
                break
    return issues


def _timestamp_names_a_real_instant(text: str) -> bool:
    """True when an RFC 3339 timestamp is also a calendar-valid date.

    A value whose shape is wrong returns True: the schema's pattern has
    already reported it, and reporting it twice helps nobody.
    """
    match = _TIMESTAMP_RE.match(text)
    if match is None:
        return True
    year, month, day, hour, minute, second = (int(g) for g in match.groups())
    if second == 60:  # RFC 3339 leap second; datetime stops at 59.
        second = 59
    try:
        datetime(year, month, day, hour, minute, second)
    except ValueError:
        return False
    return True


def _rule_calendar_valid_timestamps(doc: dict[str, Any]) -> list[Issue]:
    """Rule 10: a timestamp must name a real instant.

    The schema pattern fixes the shape and the trailing Z; it cannot
    reject month 13 or 31 February. A run timestamp is one third of the
    composite key a disposition log joins on, so an impossible date is a
    join key that can never be reproduced.
    """
    candidates: list[tuple[str, Any]] = []
    run = doc.get("run")
    if isinstance(run, dict):
        candidates.append(("run.timestamp", run.get("timestamp")))
    envelope_ref = doc.get("envelope")
    if isinstance(envelope_ref, dict):
        candidates.append(("envelope.timestamp", envelope_ref.get("timestamp")))
    dispositions = doc.get("dispositions")
    if isinstance(dispositions, list):
        for index, entry in enumerate(dispositions):
            if isinstance(entry, dict) and "decided_at" in entry:
                candidates.append(
                    (f"dispositions[{index}].decided_at", entry.get("decided_at"))
                )

    issues: list[Issue] = []
    for path, value in candidates:
        if isinstance(value, str) and not _timestamp_names_a_real_instant(value):
            issues.append(
                Issue(
                    path=path,
                    message=f"'{value}' is not a real date and time",
                    rule="calendar-valid-timestamp",
                )
            )
    return issues


def _rule_disposition_entries_resolve(
    doc: dict[str, Any], referenced_envelope: dict[str, Any] | None
) -> list[Issue]:
    """Rule 7: whenever the referenced envelope is available, every
    finding_id resolves in it and a denormalized criterion matches."""
    if referenced_envelope is None:
        return []
    dispositions = doc.get("dispositions")
    envelope_findings = referenced_envelope.get("findings")
    if not isinstance(dispositions, list) or not isinstance(envelope_findings, list):
        return []
    by_id: dict[str, dict[str, Any]] = {}
    for finding in envelope_findings:
        if isinstance(finding, dict) and isinstance(finding.get("id"), str):
            by_id[finding["id"]] = finding
    issues: list[Issue] = []
    for index, entry in enumerate(dispositions):
        if not isinstance(entry, dict):
            continue
        finding_id = entry.get("finding_id")
        if not isinstance(finding_id, str):
            continue
        finding = by_id.get(finding_id)
        if finding is None:
            issues.append(
                Issue(
                    path=f"dispositions[{index}].finding_id",
                    message=f"finding id '{finding_id}' does not exist in the referenced envelope",
                    rule="disposition-entries-resolve",
                )
            )
            continue
        entry_criterion = entry.get("criterion")
        if entry_criterion is not None and entry_criterion != finding.get("criterion"):
            issues.append(
                Issue(
                    path=f"dispositions[{index}].criterion",
                    message=(
                        f"'{entry_criterion}' does not match the referenced "
                        f"finding's criterion '{finding.get('criterion')}'"
                    ),
                    rule="disposition-entries-resolve",
                )
            )
    return issues


def _logical_errors(
    doc: Any, *, referenced_envelope: dict[str, Any] | None = None
) -> list[Issue]:
    if not isinstance(doc, dict):
        return _rule_no_dash(doc)
    if document_kind(doc) == "dispositionLog":
        issues = _rule_disposition_entries_resolve(doc, referenced_envelope)
        issues += _rule_no_dash(doc)
        issues += _rule_calendar_valid_timestamps(doc)
        return issues
    issues = _rule_unique_finding_ids(doc)
    issues += _rule_histogram_reconciles(doc)
    issues += _rule_severity_3_4_not_suppressed(doc)
    issues += _rule_gate_recomputed(doc)
    issues += _rule_rubrics_cover_findings(doc)
    issues += _rule_integer_literal(doc)
    issues += _rule_no_dash(doc)
    issues += _rule_calendar_valid_timestamps(doc)
    return issues


# --------------------------------------------------------------------------
# Rules 8 and 11: warnings, promoted to errors by --strict
# --------------------------------------------------------------------------


def _rule_output_bound(doc: Any) -> list[Issue]:
    if not isinstance(doc, dict) or document_kind(doc) != "envelope":
        return []
    findings = doc.get("findings")
    if not isinstance(findings, list):
        return []
    below_3 = 0
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        severity = finding.get("severity")
        if isinstance(severity, int) and not isinstance(severity, bool) and severity < 3:
            below_3 += 1
    if below_3 > OUTPUT_BOUND_BELOW_SEVERITY_3:
        return [
            Issue(
                path="findings",
                message=(
                    f"{below_3} emitted findings below severity 3 exceeds the "
                    f"output bound of {OUTPUT_BOUND_BELOW_SEVERITY_3}"
                ),
                rule="output-bound",
            )
        ]
    return []


# --------------------------------------------------------------------------
# Top-level validation entry point
# --------------------------------------------------------------------------


def _rule_producer_declared_threshold(doc: Any) -> list[Issue]:
    """Rule 11: warn when the gate passes only because of the threshold
    the envelope declares for itself.

    `severity_3_threshold` is policy, and the producer of an envelope is
    the skill under test. Rules 2, 3, and 4 make the counts honest, but
    nothing stops a run from carrying its own pass mark: ten severity-3
    findings under a declared threshold of ten is an internally
    consistent 'pass'. That cannot be an error, because a nonzero
    threshold is a legitimate project policy, so it is surfaced instead.
    A gating consumer that does not want to trust it passes --threshold.
    """
    if not isinstance(doc, dict) or document_kind(doc) != "envelope":
        return []
    summary = doc.get("summary")
    if not isinstance(summary, dict):
        return []
    counts = _by_severity_counts(summary.get("by_severity"))
    threshold = _as_count(summary.get("severity_3_threshold"))
    if counts is None or threshold is None:
        return []
    if threshold > 0 and counts["4"] == 0 and 0 < counts["3"] <= threshold:
        return [
            Issue(
                path="summary.severity_3_threshold",
                message=(
                    f"gate passes only because the envelope declares a severity-3 "
                    f"threshold of {threshold}: its {counts['3']} severity-3 "
                    f"findings would fail at the default threshold of 0. A gating "
                    f"consumer should pass --threshold explicitly rather than "
                    f"trust a value the producer set for itself"
                ),
                rule="producer-declared-threshold",
            )
        ]
    return []


def validate_document(
    doc: Any, *, referenced_envelope: dict[str, Any] | None = None
) -> ValidationResult:
    """Validate a full document (run envelope or disposition log) against
    the schema, then against the rules the schema cannot express.

    `referenced_envelope`, when given, is used to resolve rule 7
    (disposition entries resolve) for a disposition log document.
    """
    errors = _schema_errors(_root_validator(), doc)
    errors += _logical_errors(doc, referenced_envelope=referenced_envelope)
    warnings = _rule_output_bound(doc)
    warnings += _rule_producer_declared_threshold(doc)
    return ValidationResult(errors=errors, warnings=warnings)


# --------------------------------------------------------------------------
# Gate exit-code semantics (contract/README.md, "Gate exit codes")
# --------------------------------------------------------------------------


def gate_exit_code(summary: dict[str, Any], *, threshold: int | None = None) -> int:
    """Compute the --gate exit code (0, 1, or 2) from a valid summary
    object. `threshold` overrides summary.severity_3_threshold when given.

    Caller must have already confirmed the document is contract-valid;
    exit codes 3 and 4 are usage-level and are decided by the CLI, not
    here.
    """
    by_severity = summary["by_severity"]
    severity_4 = int(by_severity["4"])
    severity_3 = int(by_severity["3"])
    effective_threshold = (
        threshold if threshold is not None else int(summary["severity_3_threshold"])
    )
    if severity_4 > 0:
        return 1
    if severity_3 > effective_threshold:
        return 2
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


class _UsageError(Exception):
    """Raised for CLI argument errors, in place of argparse's default
    sys.exit, so main() controls the final exit code."""


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _UsageError(message)


def _build_parser() -> _ArgumentParser:
    parser = _ArgumentParser(
        prog="python -m contract.validate",
        description="Validate a critique-contract document (run envelope or disposition log).",
    )
    parser.add_argument("file", help="Path to the JSON document to validate.")
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Apply gate exit-code semantics (0 clean, 1 severity-4, 2 severity-3 above threshold).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=None,
        help="Severity-3 threshold for --gate. Defaults to summary.severity_3_threshold.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Promote warnings (output bounding, producer-declared threshold) "
            "to errors."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except _UsageError as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return 4 if _argv_requests_gate(argv) else 1

    if args.threshold is not None and args.threshold < 0:
        # severity_3_threshold is a count, minimum 0, in the schema. A
        # negative override is not "stricter than clean": it would fail a
        # run with zero severity-3 findings, which no policy can mean.
        print(
            f"usage error: --threshold must be 0 or greater, got {args.threshold}",
            file=sys.stderr,
        )
        return 4 if args.gate else 1

    try:
        doc = load_document(args.file)
    except OSError as exc:
        print(f"usage error: cannot read '{args.file}': {exc}", file=sys.stderr)
        return 4 if args.gate else 1
    except json.JSONDecodeError as exc:
        print(f"usage error: '{args.file}' is not valid JSON: {exc}", file=sys.stderr)
        return 4 if args.gate else 1

    result = validate_document(doc)
    if args.strict:
        result = result.with_strict()

    if not result.ok:
        for issue in result.errors:
            print(str(issue), file=sys.stderr)
        return 3 if args.gate else 1

    for issue in result.warnings:
        print(f"warning: {issue}", file=sys.stderr)

    if not args.gate:
        print("valid")
        return 0

    summary = doc.get("summary") if isinstance(doc, dict) else None
    if not isinstance(summary, dict):
        print(
            "usage error: --gate requires a run envelope with a 'summary' object",
            file=sys.stderr,
        )
        return 4

    print("valid")
    return gate_exit_code(summary, threshold=args.threshold)


def _argv_requests_gate(argv: list[str] | None) -> bool:
    """Best-effort check for --gate in raw argv, used only to pick the
    right exit code when argument parsing itself has already failed."""
    tokens = argv if argv is not None else sys.argv[1:]
    return "--gate" in tokens


if __name__ == "__main__":
    sys.exit(main())
