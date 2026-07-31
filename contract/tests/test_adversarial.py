"""AC-8: envelopes built to pass the schema while breaking the contract.

Every test here is a recorded attack. The attacks that the validator can
answer are answered, and each one fails the way its rule says it should;
the attacks nobody can answer from an envelope alone are recorded in
docs/internal/decisions/0016-contract-enforcement-boundary.md and are
asserted here to be exactly as permissive as that ADR says, so the
boundary cannot move without a test going red.

The dash characters are built with chr(), never written as literals, so
this file carries none of the punctuation it exists to reject.
"""

from __future__ import annotations

import json

import pytest

from contract.validate import (
    gate_exit_code,
    main,
    validate_document,
    validate_finding,
)

from .fixtures import (
    envelope_for,
    example_disposition_log,
    example_envelope,
    example_finding,
    findings_with_severities,
)

EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)


def _write(tmp_path, name, doc):
    path = tmp_path / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


# --------------------------------------------------------------------------
# Attack 1: hide a finding behind a float. JSON Schema's "integer" type
# accepts 3.0, so every count in the summary can be written as a float
# that the schema admits and that a naive cross-check reads as absent.
# --------------------------------------------------------------------------


def test_float_histogram_cannot_hide_a_severity_4_finding():
    """The whole attack, end to end: a real severity-4 finding, a
    histogram of 0.0, a self-declared 'pass'. Before rule 6 this was a
    contract-valid envelope that exited the gate at 0."""
    envelope = envelope_for(findings_with_severities([4]), gate="fail")
    envelope["summary"]["by_severity"] = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0.0}
    envelope["summary"]["gate"] = "pass"

    result = validate_document(envelope)

    assert not result.ok
    rules = {issue.rule for issue in result.errors}
    # Rule 6 names the float, and rules 2 and 3 still fire underneath it:
    # the coercion in _as_count is what stops a float from silently
    # switching the cross-checks off. Rule 4 is silent here and correctly
    # so, because an all-zero histogram really does recompute to 'pass';
    # what makes the envelope a lie is that the histogram does not match
    # the findings array, which is exactly rules 2 and 3.
    assert "integer-literal" in rules
    assert "histogram-reconciles" in rules
    assert "severity-3-4-not-suppressed" in rules


def test_float_histogram_value_is_reported_at_its_own_path():
    envelope = example_envelope()
    envelope["summary"]["by_severity"]["3"] = 1.0

    result = validate_document(envelope)

    named = [i for i in result.errors if i.rule == "integer-literal"]
    assert [i.path for i in named] == ["summary.by_severity.3"]


def test_float_suppressed_count_cannot_disable_the_histogram_check():
    envelope = envelope_for(findings_with_severities([2]), gate="pass")
    envelope["summary"]["suppressed_count"] = 5.0

    result = validate_document(envelope)

    assert not result.ok
    rules = {issue.rule for issue in result.errors}
    assert "integer-literal" in rules
    assert "histogram-reconciles" in rules


def test_float_threshold_cannot_disable_the_gate_recomputation():
    envelope = envelope_for(findings_with_severities([3]), gate="pass")
    envelope["summary"]["severity_3_threshold"] = 0.0

    result = validate_document(envelope)

    assert not result.ok
    rules = {issue.rule for issue in result.errors}
    assert "integer-literal" in rules
    assert "gate-recomputed" in rules


def test_float_envelope_is_rejected_by_the_gate_cli(tmp_path):
    envelope = envelope_for(findings_with_severities([4]), gate="fail")
    envelope["summary"]["by_severity"] = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0.0}
    envelope["summary"]["gate"] = "pass"
    path = _write(tmp_path, "float.json", envelope)

    # 3, not 0: a malformed envelope must never read as a passing gate.
    assert main([path, "--gate"]) == 3


def test_float_written_as_json_text_still_parses_to_a_float():
    """The attack only exists because "0.0" survives a round trip; if it
    did not, rule 6 would be unnecessary."""
    doc = json.loads('{"by_severity": {"4": 0.0}}')
    assert isinstance(doc["by_severity"]["4"], float)


# --------------------------------------------------------------------------
# Attack 2: smuggle a dash through the one object the schema does not
# constrain. `selector` is reserved and unvalidated, so no pattern reaches
# either its values or its keys.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("dash", [EM_DASH, EN_DASH], ids=["em-dash", "en-dash"])
def test_dash_in_a_selector_value_is_rejected(dash):
    finding = example_finding()
    finding["selector"] = {"css": f"main{dash}section"}

    issues = validate_finding(finding)

    assert any(i.rule == "no-dash" for i in issues)
    assert any(i.path == "selector.css" for i in issues)


def test_dash_in_a_selector_key_is_rejected():
    finding = example_finding()
    finding["selector"] = {f"heading{EM_DASH}path": "Section 2"}

    issues = validate_finding(finding)

    assert any(i.rule == "no-dash" for i in issues)


def test_dash_in_a_nested_selector_is_rejected_inside_an_envelope():
    envelope = example_envelope()
    envelope["findings"][0]["selector"] = {"page": {"heading": [f"Intro{EN_DASH}A"]}}

    result = validate_document(envelope)

    assert not result.ok
    named = [i for i in result.errors if i.rule == "no-dash"]
    assert named
    assert named[0].path == "findings[0].selector.page.heading[0]"


def test_dash_in_an_instance_selector_is_rejected():
    finding = example_finding()
    finding["instances"] = [
        {"location": "Section 3, first paragraph"},
        {"location": "Section 4, first paragraph", "selector": {"css": f"a{EM_DASH}b"}},
    ]

    issues = validate_finding(finding)

    assert any(i.rule == "no-dash" for i in issues)


def test_clean_selector_is_accepted():
    finding = example_finding()
    finding["selector"] = {"css": "main > section:nth-of-type(2)", "page": "index.html"}

    assert validate_finding(finding) == []


def test_prose_dash_is_reported_by_both_the_schema_and_rule_9():
    """Defence in depth is the point: the pattern and the walk overlap on
    every field the schema types as prose."""
    finding = example_finding()
    finding["violation"] = f"Contrast too low {EM_DASH} below the AA minimum"

    issues = validate_finding(finding)

    assert any(i.rule == "pattern" for i in issues)
    assert any(i.rule == "no-dash" for i in issues)


# --------------------------------------------------------------------------
# Attack 3: declare your own pass mark. The counts can all be honest and
# the gate can still be bought with severity_3_threshold.
# --------------------------------------------------------------------------


def test_producer_declared_threshold_is_warned_about():
    envelope = envelope_for(
        findings_with_severities([3, 3, 3, 3]), gate="pass", severity_3_threshold=99
    )

    result = validate_document(envelope)

    assert result.ok, result.errors
    warned = [w for w in result.warnings if w.rule == "producer-declared-threshold"]
    assert warned
    assert "99" in warned[0].message
    assert gate_exit_code(envelope["summary"]) == 0


def test_producer_declared_threshold_fails_under_strict(tmp_path):
    envelope = envelope_for(
        findings_with_severities([3, 3, 3, 3]), gate="pass", severity_3_threshold=99
    )
    path = _write(tmp_path, "selfgate.json", envelope)

    assert main([path, "--gate"]) == 0
    assert main([path, "--gate", "--strict"]) == 3
    # The consumer-side answer: do not trust the producer's number.
    assert main([path, "--gate", "--threshold", "0"]) == 2


def test_threshold_zero_run_is_not_warned_about():
    envelope = envelope_for(findings_with_severities([1, 2]), gate="pass")

    result = validate_document(envelope)

    assert result.warnings == []


def test_threshold_is_not_warned_about_when_it_did_not_change_the_verdict():
    """A declared threshold that nothing leans on is not worth a warning:
    no severity-3 findings, so the run passes at threshold 0 too."""
    envelope = envelope_for(
        findings_with_severities([1]), gate="pass", severity_3_threshold=3
    )

    result = validate_document(envelope)

    assert not any(w.rule == "producer-declared-threshold" for w in result.warnings)


def test_a_severity_4_is_never_rescued_by_a_threshold():
    envelope = envelope_for(
        findings_with_severities([4]), gate="fail", severity_3_threshold=99
    )

    result = validate_document(envelope)

    assert result.ok, result.errors
    assert gate_exit_code(envelope["summary"]) == 1


# --------------------------------------------------------------------------
# Attack 4: suppressed_count abuse. Suppression is the one place an
# envelope reports findings it does not show, so it is the natural place
# to try to park a finding.
# --------------------------------------------------------------------------


def test_a_suppressed_severity_3_is_rejected():
    """Rule 3 in its load-bearing form: severity 3 and 4 are never
    suppressed, so a histogram claiming a suppressed severity-3 finding
    cannot reconcile with an emitted list that does not carry it."""
    envelope = envelope_for(findings_with_severities([1]), gate="pass")
    envelope["summary"]["by_severity"] = {"0": 0, "1": 1, "2": 0, "3": 1, "4": 0}
    envelope["summary"]["suppressed_count"] = 1
    envelope["summary"]["gate"] = "fail"

    result = validate_document(envelope)

    assert not result.ok
    assert any(i.rule == "severity-3-4-not-suppressed" for i in result.errors)


def test_suppression_must_be_absorbed_by_severities_0_to_2():
    """The arithmetic of rules 2 and 3 together: whatever suppression
    adds to the histogram has to land below severity 3."""
    envelope = envelope_for(findings_with_severities([1]), gate="pass")
    envelope["summary"]["by_severity"] = {"0": 0, "1": 1, "2": 4, "3": 0, "4": 0}
    envelope["summary"]["suppressed_count"] = 4

    result = validate_document(envelope)

    assert result.ok, result.errors


def test_suppressed_count_cannot_be_invented_without_the_histogram():
    envelope = envelope_for(findings_with_severities([1]), gate="pass")
    envelope["summary"]["suppressed_count"] = 4  # histogram left untouched

    result = validate_document(envelope)

    assert not result.ok
    assert any(i.rule == "histogram-reconciles" for i in result.errors)


def test_an_empty_run_that_suppressed_everything_is_valid():
    """Not an attack, a boundary: a run may emit nothing and still record
    what it found, which is the case the histogram exists for."""
    envelope = envelope_for([], gate="pass")
    envelope["summary"]["by_severity"] = {"0": 0, "1": 2, "2": 3, "3": 0, "4": 0}
    envelope["summary"]["suppressed_count"] = 5

    result = validate_document(envelope)

    assert result.ok, result.errors


# --------------------------------------------------------------------------
# Attack 5: severity inflation and deflation in the histogram.
# --------------------------------------------------------------------------


def test_histogram_cannot_claim_a_severity_4_that_was_not_emitted():
    """Inflation: claiming severity-4 findings that are not in findings[]
    would let a run fail a gate it should pass, or pad a results table."""
    envelope = envelope_for(findings_with_severities([2]), gate="fail")
    envelope["summary"]["by_severity"] = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 1}

    result = validate_document(envelope)

    assert not result.ok
    assert any(i.rule == "severity-3-4-not-suppressed" for i in result.errors)


def test_histogram_cannot_relabel_an_emitted_severity_3_as_a_2():
    """Deflation inside the histogram. Relabelling the finding itself is
    a different matter and is ADR 0016's accepted residue."""
    envelope = envelope_for(findings_with_severities([3]), gate="pass")
    envelope["summary"]["by_severity"] = {"0": 0, "1": 0, "2": 1, "3": 0, "4": 0}

    result = validate_document(envelope)

    assert not result.ok
    assert any(i.rule == "severity-3-4-not-suppressed" for i in result.errors)


# --------------------------------------------------------------------------
# Attack 6: timestamps that are shaped right and mean nothing.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stamp",
    ["2026-13-01T00:00:00Z", "2026-02-31T00:00:00Z", "2026-07-17T25:00:00Z",
     "2026-00-10T00:00:00Z", "2026-07-17T14:61:03Z"],
)
def test_calendar_invalid_timestamps_are_rejected(stamp):
    envelope = example_envelope()
    envelope["run"]["timestamp"] = stamp

    result = validate_document(envelope)

    assert not result.ok
    assert any(i.rule == "calendar-valid-timestamp" for i in result.errors)


@pytest.mark.parametrize(
    "stamp",
    ["2026-07-17T14:22:03Z", "2024-02-29T00:00:00Z", "2026-07-17T14:22:03.123456789Z",
     "2026-06-30T23:59:60Z"],
)
def test_real_timestamps_are_accepted(stamp):
    """The last case is a leap second, which RFC 3339 permits."""
    envelope = example_envelope()
    envelope["run"]["timestamp"] = stamp

    result = validate_document(envelope)

    assert result.ok, result.errors


def test_calendar_invalid_timestamp_in_a_disposition_log_is_rejected():
    log = example_disposition_log()
    log["envelope"]["timestamp"] = "2026-02-30T00:00:00Z"
    log["dispositions"][0]["decided_at"] = "2026-19-01T00:00:00Z"

    result = validate_document(log)

    assert not result.ok
    paths = {i.path for i in result.errors if i.rule == "calendar-valid-timestamp"}
    assert paths == {"envelope.timestamp", "dispositions[0].decided_at"}


def test_malformed_timestamp_is_reported_once_by_the_schema():
    """A shape error belongs to the pattern; rule 10 stays quiet so the
    same mistake is not reported twice."""
    envelope = example_envelope()
    envelope["run"]["timestamp"] = "2026-07-17 14:22:03+02:00"

    result = validate_document(envelope)

    assert not result.ok
    assert not any(i.rule == "calendar-valid-timestamp" for i in result.errors)


# --------------------------------------------------------------------------
# Attack 7: criterion IDs that pass the regex but break the grammar's
# stated rules, and the namespace bound the two definitions disagree on.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "criterion",
    ["nng-h4", "WCAG", "WCAG-", "-H4", "WCAG--1", "WCAG-1.", "WCAG_1", "W CAG-1",
     "WCAG-1.4.3 ", "WCAG-1.4.3\n"],
)
def test_criterion_ids_outside_the_grammar_are_rejected(criterion):
    finding = example_finding()
    finding["criterion"] = criterion

    issues = validate_finding(finding)

    assert any(i.path == "criterion" for i in issues), criterion


@pytest.mark.parametrize(
    "criterion", ["NNG-H4", "WCAG-1.4.3", "A-1", "NNG-EM-CONSTRUCTIVE", "B-Y-O-R"]
)
def test_criterion_ids_inside_the_grammar_are_accepted(criterion):
    finding = example_finding()
    finding["criterion"] = criterion

    assert validate_finding(finding) == []


def test_a_namespace_longer_than_32_characters_cannot_form_a_valid_envelope():
    """criterionId allows 64 characters and rubricNamespace allows 32, so
    a criterion with a 40-character namespace is well formed on its own
    and can never satisfy rule 5. Documented in criterion-ids.md rather
    than fixed, because narrowing a frozen pattern is a major bump."""
    finding = example_finding()
    finding["criterion"] = "A" * 40 + "-X"
    envelope = envelope_for([finding], gate="fail", rubrics=["A" * 40])

    assert validate_finding(finding) == []
    result = validate_document(envelope)
    assert not result.ok
    assert any(i.path == "run.rubrics[0]" for i in result.errors)


def test_a_byor_criterion_forces_the_byor_rubric_source():
    finding = example_finding()
    finding["criterion"] = "BYOR-BRAND-VOICE"
    finding["rubric_source"] = "bundled"

    issues = validate_finding(finding)

    assert issues


def test_a_byor_lookalike_namespace_is_not_caught():
    """Accepted, per the schema's own comment: BYORX is a different
    namespace, and a user rubric may declare any namespace it likes."""
    finding = example_finding()
    finding["criterion"] = "BYORX-BRAND-VOICE"

    assert validate_finding(finding) == []


# --------------------------------------------------------------------------
# Attack 8: the CLI itself.
# --------------------------------------------------------------------------


def test_negative_threshold_is_a_usage_error(tmp_path):
    """A negative threshold would fail a run with zero severity-3
    findings. severity_3_threshold is a count in the schema, minimum 0,
    and the CLI override now agrees with it."""
    envelope = envelope_for(findings_with_severities([1]), gate="pass")
    path = _write(tmp_path, "clean.json", envelope)

    assert main([path, "--gate", "--threshold", "-1"]) == 4
    assert main([path, "--threshold", "-1"]) == 1
    assert main([path, "--gate", "--threshold", "0"]) == 0


def test_gate_on_a_disposition_log_is_a_usage_error(tmp_path):
    """A valid document that carries no summary cannot produce a gate
    verdict, and must not be reported as a clean one. This behaviour was
    already correct at the freeze; the test pins it, because exit 0 here
    would be a passing gate for a document that never had one."""
    path = _write(tmp_path, "log.json", example_disposition_log())

    assert main([path]) == 0
    assert main([path, "--gate"]) == 4


def test_an_envelope_carrying_a_dispositions_key_cannot_pose_as_a_log():
    """Root dispatch is on one key, so the natural attack is to attach
    that key to an envelope. additionalProperties closes it."""
    envelope = example_envelope()
    envelope["dispositions"] = [{"finding_id": "F-007", "disposition": "accept"}]

    result = validate_document(envelope)

    assert not result.ok


# --------------------------------------------------------------------------
# Attack 9: the methodology's own worked example. AC-7 requires the
# constitution's examples to match the shipped schema, which includes the
# bound the constitution sets for itself in section 7.
# --------------------------------------------------------------------------


def test_methodology_section_5_example_envelope_is_contract_clean():
    """The section 5 summary is by_severity {0:0, 1:3, 2:5, 3:2, 4:0}
    with suppressed_count 3: eight findings below severity 3 were found,
    five were emitted, three were suppressed by the section 7 output
    bound. Written with suppressed_count 0 it would emit eight, which is
    the constitution contradicting its own bounding rule."""
    findings = findings_with_severities([1, 1, 2, 2, 2, 3, 3])
    envelope = envelope_for(findings, gate="fail", suppressed_count=3)
    envelope["summary"]["by_severity"] = {"0": 0, "1": 3, "2": 5, "3": 2, "4": 0}

    result = validate_document(envelope)

    assert result.ok, result.errors
    assert result.warnings == []
    assert gate_exit_code(envelope["summary"]) == 2
