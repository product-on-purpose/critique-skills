"""The seven rules JSON Schema cannot express (contract/README.md,
"Rules the validator enforces beyond the schema"), plus rule 8 (output
bounding), which is a warning promoted to an error by --strict."""

from __future__ import annotations

from contract.validate import validate_document

from .fixtures import (
    envelope_for,
    example_envelope,
    example_finding,
    findings_with_severities,
)


def test_rule1_duplicate_finding_ids_rejected():
    findings = findings_with_severities([2, 2])
    findings[1]["id"] = findings[0]["id"]  # force a collision
    envelope = envelope_for(findings, gate="pass")

    result = validate_document(envelope)

    assert not result.ok
    assert any(i.rule == "unique-finding-ids" for i in result.errors)


def test_rule2_histogram_total_must_reconcile():
    envelope = envelope_for(findings_with_severities([2]), gate="pass")
    envelope["summary"]["suppressed_count"] = 5  # sum(by_severity) now != len+suppressed

    result = validate_document(envelope)

    assert not result.ok
    assert any(i.rule == "histogram-reconciles" for i in result.errors)


def test_rule3_severity_4_never_suppressed():
    envelope = envelope_for(findings_with_severities([4]), gate="fail")
    # Understate the severity-4 count while keeping the histogram total
    # reconciled, so only rule 3 is exercised.
    envelope["summary"]["by_severity"] = {"0": 1, "1": 0, "2": 0, "3": 0, "4": 0}

    result = validate_document(envelope)

    assert not result.ok
    assert any(i.rule == "severity-3-4-not-suppressed" for i in result.errors)


def test_rule3_severity_0_to_2_recorded_count_must_be_at_least_emitted():
    envelope = envelope_for(findings_with_severities([1, 2]), gate="pass")
    # Understate severity 1 while shifting the total into severity 2, so
    # the histogram still reconciles and only the 0-2 floor is broken.
    envelope["summary"]["by_severity"] = {"0": 0, "1": 0, "2": 2, "3": 0, "4": 0}

    result = validate_document(envelope)

    assert not result.ok
    assert any(i.rule == "severity-3-4-not-suppressed" for i in result.errors)


def test_rule4_gate_verdict_is_recomputed():
    envelope = envelope_for(findings_with_severities([3]), gate="pass")  # should be fail

    result = validate_document(envelope)

    assert not result.ok
    gate_issues = [i for i in result.errors if i.rule == "gate-recomputed"]
    assert gate_issues
    assert "fail" in gate_issues[0].message


def test_rule4_gate_verdict_fail_when_over_threshold():
    envelope = envelope_for(
        findings_with_severities([3, 3]), gate="fail", severity_3_threshold=1
    )
    # 2 severity-3 findings > threshold 1 => 'fail' is in fact correct.
    result = validate_document(envelope)
    assert result.ok, result.errors


def test_rule5_rubrics_must_cover_every_finding_namespace():
    finding = example_finding()
    finding["criterion"] = "AE-TITLE"
    envelope = envelope_for([finding], gate="pass", rubrics=["WCAG"])

    result = validate_document(envelope)

    assert not result.ok
    rubric_issues = [i for i in result.errors if i.rule == "rubrics-cover-findings"]
    assert rubric_issues
    assert rubric_issues[0].path == "findings[0].criterion"


def test_rule6_severity_must_be_a_json_integer_literal():
    # Built from example_envelope() rather than envelope_for(), because a
    # float severity cannot key the by_severity histogram the same way an
    # int does; the point of this test is the float itself, not a fully
    # reconciled summary around it.
    envelope = example_envelope()
    envelope["findings"][0]["severity"] = 3.0  # as json.loads("3.0") produces

    result = validate_document(envelope)

    assert not result.ok
    named = [i for i in result.errors if i.rule == "integer-literal"]
    assert named
    assert named[0].path == "findings[0].severity"


def test_rule6_severity_as_plain_int_is_accepted():
    envelope = example_envelope()
    envelope["findings"][0]["severity"] = 3

    result = validate_document(envelope)

    assert not any(i.rule == "integer-literal" for i in result.errors)


def test_rule8_output_bound_is_a_warning_not_an_error():
    findings = findings_with_severities([1, 1, 1, 1, 1, 1])  # 6 > the bound of 5
    envelope = envelope_for(findings, gate="pass")

    result = validate_document(envelope)

    assert result.ok, result.errors
    assert any(i.rule == "output-bound" for i in result.warnings)


def test_rule8_output_bound_promoted_to_error_by_strict():
    findings = findings_with_severities([1, 1, 1, 1, 1, 1])
    envelope = envelope_for(findings, gate="pass")

    result = validate_document(envelope).with_strict()

    assert not result.ok
    assert any(i.rule == "output-bound" for i in result.errors)
    assert result.warnings == []


def test_rule8_five_below_severity_3_is_within_bound():
    findings = findings_with_severities([1, 1, 1, 1, 1])  # exactly 5, not over
    envelope = envelope_for(findings, gate="pass")

    result = validate_document(envelope)

    assert result.ok, result.errors
    assert result.warnings == []
