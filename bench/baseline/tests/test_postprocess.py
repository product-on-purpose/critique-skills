"""Tests for bench.baseline.postprocess: the deterministic mapping from a
raw baseline response to a contract-valid run envelope."""

from __future__ import annotations

from contract.validate import validate_document

from bench.baseline.postprocess import (
    BASELINE_CRITERION,
    BASELINE_NAMESPACE,
    BASELINE_SEVERITY,
    BASELINE_SKILL,
    NO_PROBLEMS_TEXT,
    _apply_output_bound,
    parse_findings,
    postprocess,
)

RUN_KWARGS = dict(
    artifact="bench/corpus/toy/toy-001.md",
    artifact_sha256="a" * 64,
    model="claude-sonnet-4-5-20250929",
    timestamp="2026-07-31T00:00:00Z",
)

TWO_PROBLEM_RESPONSE = """Location: Section 2, hero banner
Evidence: body text #8a8a8a on background #f5f5f5
Problem: Contrast ratio 2.9:1, below the 4.5:1 AA minimum.
Fix: Darken text to #595959 or darker.

Location: Section 3, second paragraph
Evidence: "It may possibly be the case that the system will respond."
Problem: A stacked hedge weakens an otherwise direct statement.
Fix: Delete the hedge and state the claim directly.
"""


def test_well_formed_two_problem_response_produces_two_findings() -> None:
    envelope = postprocess(TWO_PROBLEM_RESPONSE, **RUN_KWARGS)
    assert len(envelope["findings"]) == 2
    ids = [f["id"] for f in envelope["findings"]]
    assert ids == ["F-001", "F-002"]
    first = envelope["findings"][0]
    assert first["criterion"] == BASELINE_CRITERION
    assert first["location"] == "Section 2, hero banner"
    assert first["evidence"] == "body text #8a8a8a on background #f5f5f5"
    assert first["violation"] == "Contrast ratio 2.9:1, below the 4.5:1 AA minimum."
    assert first["fix"] == "Darken text to #595959 or darker."
    assert first["severity"] == BASELINE_SEVERITY
    assert first["lane"] == "judged"


def test_no_problems_found_exact_match_yields_empty_envelope() -> None:
    envelope = postprocess(NO_PROBLEMS_TEXT, **RUN_KWARGS)
    assert envelope["findings"] == []
    assert envelope["summary"]["gate"] == "pass"
    assert envelope["summary"]["by_severity"] == {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0}


def test_no_problems_found_tolerates_surrounding_whitespace() -> None:
    envelope = postprocess(f"  \n{NO_PROBLEMS_TEXT}\n\n  ", **RUN_KWARGS)
    assert envelope["findings"] == []


def test_malformed_block_missing_a_field_is_dropped_not_fabricated() -> None:
    raw = (
        "Location: Section 1\n"
        "Evidence: some text\n"
        "Fix: do the thing\n"
        "\n"
        "Location: Section 2\n"
        "Evidence: other text\n"
        "Problem: it is wrong\n"
        "Fix: fix it\n"
    )
    findings = parse_findings(raw)
    assert len(findings) == 1  # only the second, complete block survives
    assert findings[0]["location"] == "Section 2"


def test_completely_unparseable_response_yields_no_findings() -> None:
    envelope = postprocess("I looked at the document and it seemed fine overall.", **RUN_KWARGS)
    assert envelope["findings"] == []


def test_wrapped_field_continuation_lines_are_joined() -> None:
    raw = (
        "Location: Section 4\n"
        "Evidence: a long quotation that a model\n"
        "wrapped across two lines for readability\n"
        "Problem: it is unclear\n"
        "Fix: rewrite it\n"
    )
    findings = parse_findings(raw)
    assert len(findings) == 1
    assert findings[0]["evidence"] == "a long quotation that a model wrapped across two lines for readability"


def test_dash_characters_are_sanitized_out_of_every_field() -> None:
    # Built with chr() so this test file carries no literal em dash or en
    # dash characters on disk, per the project's own house style.
    em = chr(0x2014)
    en = chr(0x2013)
    raw = (
        f"Location: Section 2{em} hero banner\n"
        f"Evidence: pages 3{en}5 show the same issue\n"
        f"Problem: contrast is low{em} readers will struggle\n"
        f"Fix: darken the text{en} then re-check contrast\n"
    )
    envelope = postprocess(raw, **RUN_KWARGS)
    finding = envelope["findings"][0]
    for field in ("location", "evidence", "violation", "fix"):
        assert em not in finding[field]
        assert en not in finding[field]
    assert finding["location"] == "Section 2 - hero banner"


def test_overlong_field_is_truncated_to_schema_maximum() -> None:
    long_fix = "x" * 5000
    raw = f"Location: Section 1\nEvidence: e\nProblem: p\nFix: {long_fix}\n"
    envelope = postprocess(raw, **RUN_KWARGS)
    assert len(envelope["findings"][0]["fix"]) <= 1000


def test_envelope_is_contract_valid() -> None:
    envelope = postprocess(TWO_PROBLEM_RESPONSE, **RUN_KWARGS)
    result = validate_document(envelope)
    assert result.ok, [str(e) for e in result.errors]
    assert envelope["run"]["skill"] == BASELINE_SKILL
    assert envelope["run"]["rubrics"] == [BASELINE_NAMESPACE]


def test_clean_envelope_is_also_contract_valid() -> None:
    envelope = postprocess(NO_PROBLEMS_TEXT, **RUN_KWARGS)
    result = validate_document(envelope)
    assert result.ok, [str(e) for e in result.errors]


def test_gate_fails_when_findings_are_present_severity_three() -> None:
    envelope = postprocess(TWO_PROBLEM_RESPONSE, **RUN_KWARGS)
    assert envelope["summary"]["gate"] == "fail"
    assert envelope["summary"]["by_severity"]["3"] == 2
    assert envelope["summary"]["suppressed_count"] == 0


def test_output_bound_keeps_every_high_severity_finding_and_caps_low_ones() -> None:
    """Exercises the output-bound mechanism directly with synthetic
    severities. Unreachable through the public postprocess() API today,
    since every real baseline finding is BASELINE_SEVERITY (3); this
    pins the mechanism itself so a future change to that constant cannot
    silently break the bound."""
    findings = [{"severity": 4}] * 2 + [{"severity": 1}] * 8
    emitted, suppressed = _apply_output_bound(findings)
    assert sum(1 for f in emitted if f["severity"] == 4) == 2
    assert sum(1 for f in emitted if f["severity"] == 1) == 5
    assert suppressed == 3
