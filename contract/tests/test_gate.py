"""AC-6: --gate exit codes (contract/README.md, "Gate exit codes"),
verified for a clean envelope, a severity-4 envelope, and a
severity-3-above-threshold envelope, plus the --threshold override and
the CLI's non-gate and usage-error paths."""

from __future__ import annotations

import json

import pytest

from contract.validate import gate_exit_code, main

from .fixtures import envelope_for, findings_with_severities


def _write(tmp_path, name, doc):
    path = tmp_path / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


def test_clean_envelope_gate_exit_code_is_zero(tmp_path, capsys):
    envelope = envelope_for(findings_with_severities([1, 2]), gate="pass")
    path = _write(tmp_path, "clean.json", envelope)

    code = main([path, "--gate"])

    assert code == 0
    assert "valid" in capsys.readouterr().out


def test_severity_4_envelope_gate_exit_code_is_one(tmp_path, capsys):
    envelope = envelope_for(findings_with_severities([4]), gate="fail")
    path = _write(tmp_path, "sev4.json", envelope)

    code = main([path, "--gate"])

    assert code == 1


def test_severity_3_above_threshold_gate_exit_code_is_two(tmp_path, capsys):
    envelope = envelope_for(
        findings_with_severities([3, 3]), gate="fail", severity_3_threshold=0
    )
    path = _write(tmp_path, "sev3.json", envelope)

    code = main([path, "--gate"])

    assert code == 2


def test_severity_4_takes_precedence_over_severity_3(tmp_path):
    findings = findings_with_severities([3, 3, 3, 4])
    envelope = envelope_for(findings, gate="fail", severity_3_threshold=0)
    path = _write(tmp_path, "both.json", envelope)

    code = main([path, "--gate"])

    assert code == 1


def test_threshold_flag_overrides_stored_threshold(tmp_path):
    # Stored threshold is 1, so the document's own gate is legitimately
    # 'pass' (1 severity-3 finding, not above 1). --threshold 0 must
    # still push the exit code to 2, independent of the stored verdict.
    envelope = envelope_for(
        findings_with_severities([3]), gate="pass", severity_3_threshold=1
    )
    path = _write(tmp_path, "threshold.json", envelope)

    default_code = main([path, "--gate"])
    overridden_code = main([path, "--gate", "--threshold", "0"])

    assert default_code == 0
    assert overridden_code == 2


def test_gate_exit_code_helper_matches_cli(tmp_path):
    summary = envelope_for(findings_with_severities([3]), gate="pass", severity_3_threshold=1)[
        "summary"
    ]
    assert gate_exit_code(summary) == 0
    assert gate_exit_code(summary, threshold=0) == 2


def test_invalid_document_gate_exit_code_is_three(tmp_path):
    envelope = envelope_for(findings_with_severities([2]), gate="pass")
    del envelope["findings"][0]["location"]
    path = _write(tmp_path, "invalid.json", envelope)

    code = main([path, "--gate"])

    assert code == 3


def test_unreadable_file_gate_exit_code_is_four(tmp_path):
    missing = str(tmp_path / "does-not-exist.json")

    code = main([missing, "--gate"])

    assert code == 4


def test_bad_argument_gate_exit_code_is_four(tmp_path):
    envelope = envelope_for(findings_with_severities([1]), gate="pass")
    path = _write(tmp_path, "ok.json", envelope)

    code = main([path, "--gate", "--threshold", "not-a-number"])

    assert code == 4


def test_non_gate_mode_valid_document_exits_zero(tmp_path):
    envelope = envelope_for(findings_with_severities([1]), gate="pass")
    path = _write(tmp_path, "ok.json", envelope)

    assert main([path]) == 0


def test_non_gate_mode_invalid_document_exits_one(tmp_path):
    envelope = envelope_for(findings_with_severities([1]), gate="pass")
    del envelope["findings"][0]["evidence"]
    path = _write(tmp_path, "bad.json", envelope)

    assert main([path]) == 1


def test_non_gate_mode_severity_4_still_exits_zero_when_valid(tmp_path):
    """Without --gate the CLI reports contract validity only, not the
    gate verdict; a valid severity-4 envelope still exits 0."""
    envelope = envelope_for(findings_with_severities([4]), gate="fail")
    path = _write(tmp_path, "sev4.json", envelope)

    assert main([path]) == 0


def test_non_gate_mode_unreadable_file_exits_one(tmp_path):
    missing = str(tmp_path / "does-not-exist.json")

    assert main([missing]) == 1


def test_strict_promotes_output_bound_warning_and_fails_gate(tmp_path):
    findings = findings_with_severities([1, 1, 1, 1, 1, 1])  # 6 > bound of 5
    envelope = envelope_for(findings, gate="pass")
    path = _write(tmp_path, "bounded.json", envelope)

    assert main([path, "--gate"]) == 0
    assert main([path, "--gate", "--strict"]) == 3
