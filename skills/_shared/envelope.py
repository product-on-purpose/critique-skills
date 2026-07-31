"""Envelope assembly: pass 4 of the four-pass protocol (rank and bound,
methodology section 7) plus the run record and summary, producing one
contract-valid run envelope from a skill's raw scripted-lane findings.

This is the one place in the library that decides what "rank and bound"
means in code, so every skill's checks.py bounds output the same way.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from skills._shared.findings import RawFinding, to_finding_dict

SEVERITY_KEYS: tuple[str, ...] = ("0", "1", "2", "3", "4")

# methodology section 7, "Output bounding": all severity 3 and 4 findings,
# plus at most five below that threshold. Mirrors
# contract/validate.py's OUTPUT_BOUND_BELOW_SEVERITY_3, which is the
# validator's own copy of the same number; kept as a plain constant here
# rather than imported, because contract/validate.py's constant is
# private to that module's warning rule, not part of its public API.
OUTPUT_BOUND_BELOW_SEVERITY_3 = 5

# contract/critique-contract.schema.json's own header: "This file is
# contract version 1.0.0". Not machine-readable from the schema file
# itself (the version lives in prose, not a queryable field), so it is
# duplicated here; bump it if that header's version ever changes.
CONTRACT_VERSION = "1.0.0"


def _rank_key(raw: RawFinding) -> tuple[int, str, str]:
    """Deterministic ranking key: severity descending, then criterion,
    then location, both ascending. Two check functions run against the
    same artifact in the same order always produce the same ranking,
    which is what "same artifact, same output bytes" (S-04 spec)
    requires of findings[] and summary; see docs/internal/skill-template.md,
    "What determinism does and does not cover", for the one field this
    guarantee explicitly excludes (run.timestamp).
    """
    return (-raw.severity, raw.criterion, raw.location)


def by_severity_histogram(raw_findings: Sequence[RawFinding]) -> dict[str, int]:
    """The complete severity histogram over every finding a run
    produced, including ones the output bound will go on to suppress.
    Contract field: summary.by_severity.
    """
    counts = {key: 0 for key in SEVERITY_KEYS}
    for raw in raw_findings:
        counts[str(raw.severity)] += 1
    return counts


def rank_and_bound(raw_findings: Sequence[RawFinding]) -> tuple[list[RawFinding], int]:
    """Pass 4: order by severity (then criterion, then location) and
    bound. Every severity 3 and 4 finding is kept; severities 0-2 are
    kept up to OUTPUT_BOUND_BELOW_SEVERITY_3, in ranked order. Returns
    (emitted, suppressed_count).
    """
    ordered = sorted(raw_findings, key=_rank_key)
    at_or_above_3 = [r for r in ordered if r.severity >= 3]
    below_3 = [r for r in ordered if r.severity < 3]
    kept_below = below_3[:OUTPUT_BOUND_BELOW_SEVERITY_3]
    suppressed_count = len(below_3) - len(kept_below)
    return at_or_above_3 + kept_below, suppressed_count


def build_summary(
    *,
    histogram: Mapping[str, int],
    suppressed_count: int,
    severity_3_threshold: int,
) -> dict[str, Any]:
    """summary.gate is recomputed here using the same rule
    contract/validate.py's validator independently recomputes and checks
    (rule 4): fail when any severity-4 finding exists or the severity-3
    count exceeds the threshold, pass otherwise. Computing it the same
    way here is what makes that validator rule a no-op on this library's
    own output rather than a real risk.
    """
    severity_4 = int(histogram["4"])
    severity_3 = int(histogram["3"])
    gate = "fail" if (severity_4 > 0 or severity_3 > severity_3_threshold) else "pass"
    return {
        "by_severity": {key: int(histogram[key]) for key in SEVERITY_KEYS},
        "suppressed_count": suppressed_count,
        "gate": gate,
        "severity_3_threshold": severity_3_threshold,
    }


def assemble_envelope(
    *,
    skill: str,
    skill_version: str,
    artifact_path: str,
    artifact_sha256: str,
    model: str,
    timestamp: str,
    rubrics: Sequence[str],
    raw_findings: Sequence[RawFinding],
    severity_3_threshold: int = 0,
    stripped_context: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble one contract-valid run envelope. `raw_findings` is every
    breach the scripted lane detected, unranked and unbounded; this
    function performs pass 4 (rank_and_bound), assigns finding ids only
    to what survives bounding, and builds `run` and `summary`.

    Callers (skills/_shared/runner.py, or a judged-lane critic merging
    both lanes) still owe the result one thing this function cannot
    check: that `rubrics` actually lists every namespace `raw_findings`
    draws on. contract.validate.validate_document catches a mismatch,
    which is why runner.py validates its own output before printing it.
    """
    histogram = by_severity_histogram(raw_findings)
    emitted_raw, suppressed_count = rank_and_bound(raw_findings)
    findings = [
        to_finding_dict(raw, finding_id=f"F-{index:03d}")
        for index, raw in enumerate(emitted_raw, start=1)
    ]

    run: dict[str, Any] = {
        "skill": skill,
        "skill_version": skill_version,
        "contract_version": CONTRACT_VERSION,
        "artifact": artifact_path,
        "artifact_sha256": artifact_sha256,
        "model": model,
        "timestamp": timestamp,
        "rubrics": list(rubrics),
    }
    if stripped_context:
        run["stripped_context"] = [dict(entry) for entry in stripped_context]

    summary = build_summary(
        histogram=histogram,
        suppressed_count=suppressed_count,
        severity_3_threshold=severity_3_threshold,
    )

    return {"run": run, "findings": findings, "summary": summary}
