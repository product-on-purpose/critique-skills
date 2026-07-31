"""Tests for skills/_shared/envelope.py.

`assemble_envelope`'s output is also checked against the real contract
validator (contract/validate.py), not just against this module's own
expectations, because AC-4's whole point is that a skill's checks.py
produces exactly what the contract validator accepts.
"""

from __future__ import annotations

from contract.validate import validate_document

from skills._shared.envelope import (
    OUTPUT_BOUND_BELOW_SEVERITY_3,
    assemble_envelope,
    by_severity_histogram,
    rank_and_bound,
)
from skills._shared.findings import RawFinding

ARTIFACT_SHA256 = "a" * 64


def _raw(criterion="TOY-ACTIVE", severity=2, location="s1.p1") -> RawFinding:
    return RawFinding(
        criterion=criterion,
        severity=severity,
        location=location,
        evidence="evidence text",
        violation="violation text",
        fix="fix text",
    )


def test_by_severity_histogram_counts_every_finding():
    findings = [_raw(severity=4), _raw(severity=3), _raw(severity=2), _raw(severity=2)]

    histogram = by_severity_histogram(findings)

    assert histogram == {"0": 0, "1": 0, "2": 2, "3": 1, "4": 1}


def test_rank_and_bound_keeps_all_severity_3_and_4():
    findings = [_raw(severity=4), _raw(severity=3), _raw(severity=3)]

    emitted, suppressed = rank_and_bound(findings)

    assert len(emitted) == 3
    assert suppressed == 0


def test_rank_and_bound_caps_below_threshold_findings_and_counts_the_rest():
    below = [_raw(severity=1, location=f"s1.p{i}") for i in range(OUTPUT_BOUND_BELOW_SEVERITY_3 + 3)]

    emitted, suppressed = rank_and_bound(below)

    assert len(emitted) == OUTPUT_BOUND_BELOW_SEVERITY_3
    assert suppressed == 3


def test_rank_and_bound_orders_severity_descending_then_criterion_then_location():
    findings = [
        _raw(criterion="B", severity=2, location="z"),
        _raw(criterion="A", severity=4, location="y"),
        _raw(criterion="A", severity=4, location="x"),
    ]

    emitted, _ = rank_and_bound(findings)

    assert [(f.criterion, f.severity, f.location) for f in emitted] == [
        ("A", 4, "x"),
        ("A", 4, "y"),
        ("B", 2, "z"),
    ]


def _assemble(raw_findings, **overrides):
    kwargs = dict(
        skill="critique-toy",
        skill_version="0.1.0",
        artifact_path="bench/corpus/toy/toy-001.md",
        artifact_sha256=ARTIFACT_SHA256,
        model="none",
        timestamp="2026-07-17T14:22:03Z",
        rubrics=["TOY"],
        raw_findings=raw_findings,
    )
    kwargs.update(overrides)
    return assemble_envelope(**kwargs)


def test_assemble_envelope_is_contract_valid_with_no_findings():
    envelope = _assemble([])

    result = validate_document(envelope)

    assert result.ok, [str(issue) for issue in result.errors]
    assert envelope["summary"]["gate"] == "pass"
    assert envelope["findings"] == []


def test_assemble_envelope_is_contract_valid_with_findings():
    envelope = _assemble([_raw(severity=3), _raw(severity=2)])

    result = validate_document(envelope)

    assert result.ok, [str(issue) for issue in result.errors]
    assert envelope["summary"]["gate"] == "fail"
    assert [f["id"] for f in envelope["findings"]] == ["F-001", "F-002"]


def test_assemble_envelope_suppresses_and_still_validates():
    below = [_raw(severity=1, location=f"s1.p{i}") for i in range(OUTPUT_BOUND_BELOW_SEVERITY_3 + 4)]

    envelope = _assemble(below)

    result = validate_document(envelope)

    assert result.ok, [str(issue) for issue in result.errors]
    assert envelope["summary"]["suppressed_count"] == 4
    assert len(envelope["findings"]) == OUTPUT_BOUND_BELOW_SEVERITY_3
    assert envelope["summary"]["by_severity"]["1"] == OUTPUT_BOUND_BELOW_SEVERITY_3 + 4


def test_assemble_envelope_gate_fails_on_severity_4():
    envelope = _assemble([_raw(severity=4)])

    assert envelope["summary"]["gate"] == "fail"


def test_assemble_envelope_respects_declared_threshold():
    envelope = _assemble([_raw(severity=3)], severity_3_threshold=1)

    assert envelope["summary"]["gate"] == "pass"
    assert envelope["summary"]["severity_3_threshold"] == 1


def test_assemble_envelope_carries_stripped_context_when_given():
    envelope = _assemble(
        [],
        stripped_context=[{"kind": "requester-opinion", "note": "Author said section 2 is fine."}],
    )

    result = validate_document(envelope)

    assert result.ok, [str(issue) for issue in result.errors]
    assert envelope["run"]["stripped_context"][0]["kind"] == "requester-opinion"


def test_assemble_envelope_omits_stripped_context_when_absent():
    envelope = _assemble([])

    assert "stripped_context" not in envelope["run"]
