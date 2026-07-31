"""Shared fixtures for the contract validator test suite.

Every builder returns a fresh dict so tests can mutate the result without
affecting other tests. `example_finding`, `example_run`, `example_summary`,
and `example_envelope` are adapted from the worked example in
docs/explanation/methodology.md section 5 (source draft:
_local/initial-discovery/2026-07-27_claude-opus_methodology.md), filled
out so every schema-required field is present.
"""

from __future__ import annotations

from typing import Any

FINDING_REQUIRED_FIELDS = [
    "id",
    "criterion",
    "lane",
    "severity",
    "location",
    "evidence",
    "violation",
    "fix",
    "confidence",
]

EXAMPLE_ARTIFACT_SHA256 = "3f9a1c" + "0" * 58


def example_finding() -> dict[str, Any]:
    """The methodology's worked example finding (section 5), adapted to
    the shipped schema: every required field present, confidence forced
    high because lane is scripted."""
    return {
        "id": "F-007",
        "criterion": "WCAG-1.4.3",
        "lane": "scripted",
        "severity": 3,
        "location": "Section 2, hero banner",
        "evidence": "body text #8a8a8a on background #f5f5f5",
        "violation": "Contrast ratio 2.9:1, below the 4.5:1 AA minimum",
        "fix": "Darken text to #595959 or darker",
        "confidence": "high",
    }


def example_run(**overrides: Any) -> dict[str, Any]:
    """The methodology's worked example run record (section 5), adapted
    to the shipped schema's required run fields."""
    run: dict[str, Any] = {
        "skill": "critique-clarity",
        "skill_version": "1.2.0",
        "contract_version": "1.0.0",
        "artifact": "docs/prd.md",
        "artifact_sha256": EXAMPLE_ARTIFACT_SHA256,
        "model": "claude-sonnet-4-5-20250929",
        "timestamp": "2026-07-17T14:22:03Z",
        "rubrics": ["WCAG"],
    }
    run.update(overrides)
    return run


def example_summary(**overrides: Any) -> dict[str, Any]:
    """The methodology's worked example summary (section 5): one
    severity-3 finding, nothing suppressed, gate fails."""
    summary: dict[str, Any] = {
        "by_severity": {"0": 0, "1": 0, "2": 0, "3": 1, "4": 0},
        "suppressed_count": 0,
        "gate": "fail",
        "severity_3_threshold": 0,
    }
    summary.update(overrides)
    return summary


def example_envelope() -> dict[str, Any]:
    """The methodology's worked example envelope (section 5), fully
    adapted to the shipped schema: one severity-3 finding, gate fail."""
    return {
        "run": example_run(),
        "findings": [example_finding()],
        "summary": example_summary(),
    }


def example_disposition_log() -> dict[str, Any]:
    """A disposition log referencing example_envelope()'s single finding."""
    return {
        "contract_version": "1.0.0",
        "envelope": {
            "skill": "critique-clarity",
            "skill_version": "1.2.0",
            "artifact": "docs/prd.md",
            "artifact_sha256": EXAMPLE_ARTIFACT_SHA256,
            "timestamp": "2026-07-17T14:22:03Z",
        },
        "dispositions": [
            {
                "finding_id": "F-007",
                "disposition": "accept",
                "note": "Confirmed against the rendered page.",
                "criterion": "WCAG-1.4.3",
            }
        ],
    }


def findings_with_severities(severities: list[int]) -> list[dict[str, Any]]:
    """N findings sharing one criterion, sequential F-NNN ids, and the
    given severities in order."""
    findings = []
    for index, severity in enumerate(severities, start=1):
        finding = example_finding()
        finding["id"] = f"F-{index:03d}"
        finding["severity"] = severity
        findings.append(finding)
    return findings


def by_severity_for(findings: list[dict[str, Any]]) -> dict[str, int]:
    """A by_severity histogram that exactly reconciles with `findings`,
    with nothing suppressed."""
    counts = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0}
    for finding in findings:
        counts[str(finding["severity"])] += 1
    return counts


def envelope_for(
    findings: list[dict[str, Any]],
    *,
    gate: str,
    severity_3_threshold: int = 0,
    suppressed_count: int = 0,
    rubrics: list[str] | None = None,
) -> dict[str, Any]:
    """A minimal, internally consistent envelope wrapping `findings`,
    for tests that need to control the summary precisely."""
    return {
        "run": example_run(rubrics=rubrics if rubrics is not None else ["WCAG"]),
        "findings": findings,
        "summary": {
            "by_severity": by_severity_for(findings),
            "suppressed_count": suppressed_count,
            "gate": gate,
            "severity_3_threshold": severity_3_threshold,
        },
    }
