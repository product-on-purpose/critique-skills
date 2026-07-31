"""Tests for skills/_shared/runner.py: the shared checks.py CLI body."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from skills._shared.artifact import Artifact
from skills._shared.findings import RawFinding
from skills._shared.runner import run_scripted_lane

FIXED_NOW = lambda: datetime(2026, 7, 17, 14, 22, 3, tzinfo=timezone.utc)  # noqa: E731


def _clean_check(artifact: Artifact):
    return []


def _one_finding_check(artifact: Artifact):
    return [
        RawFinding(
            criterion="TOY-ACTIVE",
            severity=2,
            location="s1.p1",
            evidence="evidence",
            violation="violation",
            fix="fix",
        )
    ]


def _severity_4_check(artifact: Artifact):
    return [
        RawFinding(
            criterion="TOY-ORPHAN",
            severity=4,
            location="s1.h",
            evidence="evidence",
            violation="violation",
            fix="fix",
        )
    ]


def _write_artifact(tmp_path):
    target = tmp_path / "doc.md"
    target.write_text("Hello.\n", encoding="utf-8", newline="\n")
    return target


def test_clean_artifact_exits_zero_without_gate(tmp_path, capsys, monkeypatch):
    target = _write_artifact(tmp_path)
    monkeypatch.chdir(tmp_path)

    code = run_scripted_lane(
        skill_name="critique-toy",
        skill_version="0.1.0",
        rubrics=["TOY"],
        check_fn=_clean_check,
        argv=[str(target)],
        now=FIXED_NOW,
    )

    assert code == 0
    envelope = json.loads(capsys.readouterr().out)
    assert envelope["findings"] == []
    assert envelope["run"]["skill"] == "critique-toy"
    assert envelope["run"]["model"] == "none"
    assert envelope["run"]["timestamp"] == "2026-07-17T14:22:03Z"


def test_gate_exits_zero_for_a_clean_artifact(tmp_path, monkeypatch):
    target = _write_artifact(tmp_path)
    monkeypatch.chdir(tmp_path)

    code = run_scripted_lane(
        skill_name="critique-toy",
        skill_version="0.1.0",
        rubrics=["TOY"],
        check_fn=_clean_check,
        argv=[str(target), "--gate"],
        now=FIXED_NOW,
    )

    assert code == 0


def test_gate_exits_two_for_a_severity_3_finding_at_default_threshold(tmp_path, monkeypatch, capsys):
    target = _write_artifact(tmp_path)
    monkeypatch.chdir(tmp_path)

    def check(artifact):
        return [
            RawFinding(
                criterion="TOY-ORPHAN",
                severity=3,
                location="s1.h",
                evidence="evidence",
                violation="violation",
                fix="fix",
            )
        ]

    code = run_scripted_lane(
        skill_name="critique-toy",
        skill_version="0.1.0",
        rubrics=["TOY"],
        check_fn=check,
        argv=[str(target), "--gate"],
        now=FIXED_NOW,
    )

    assert code == 2


def test_gate_exits_one_for_a_severity_4_finding(tmp_path, monkeypatch):
    target = _write_artifact(tmp_path)
    monkeypatch.chdir(tmp_path)

    code = run_scripted_lane(
        skill_name="critique-toy",
        skill_version="0.1.0",
        rubrics=["TOY"],
        check_fn=_severity_4_check,
        argv=[str(target), "--gate"],
        now=FIXED_NOW,
    )

    assert code == 1


def test_gate_respects_explicit_threshold_override(tmp_path, monkeypatch):
    target = _write_artifact(tmp_path)
    monkeypatch.chdir(tmp_path)

    def check(artifact):
        return [
            RawFinding(
                criterion="TOY-ORPHAN",
                severity=3,
                location="s1.h",
                evidence="evidence",
                violation="violation",
                fix="fix",
            )
        ]

    code = run_scripted_lane(
        skill_name="critique-toy",
        skill_version="0.1.0",
        rubrics=["TOY"],
        check_fn=check,
        argv=[str(target), "--gate", "--threshold", "1"],
        now=FIXED_NOW,
    )

    assert code == 0


def test_missing_artifact_is_a_usage_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    code = run_scripted_lane(
        skill_name="critique-toy",
        skill_version="0.1.0",
        rubrics=["TOY"],
        check_fn=_clean_check,
        argv=["does-not-exist.md", "--gate"],
        now=FIXED_NOW,
    )

    assert code == 4
    assert "usage error" in capsys.readouterr().err


def test_invalid_envelope_is_exit_3_under_gate_and_1_without(tmp_path, monkeypatch, capsys):
    """Gate code 3 is "the envelope checks.py itself produced is invalid":
    a bug in the skill's check function, not a usage error. It is the one
    gate code a skill can reach without any bad input, so the shared
    runner owns it and no skill re-decides it (S-04 spec AC-4).

    The bug staged here is the realistic one: a check function emits a
    finding whose criterion namespace is not listed in `rubrics`, which
    assemble_envelope cannot detect and validate_document does.
    """
    target = _write_artifact(tmp_path)
    monkeypatch.chdir(tmp_path)

    def call(*extra):
        return run_scripted_lane(
            skill_name="critique-toy",
            skill_version="0.1.0",
            rubrics=["OTHER"],  # does not cover the TOY-ACTIVE finding below
            check_fn=_one_finding_check,
            argv=[str(target), *extra],
            now=FIXED_NOW,
        )

    assert call("--gate") == 3
    assert "internal error" in capsys.readouterr().err
    assert call() == 1


def test_same_artifact_twice_produces_identical_findings_and_summary(tmp_path, monkeypatch):
    """S-04 spec: checks.py MUST be deterministic. run.timestamp is
    excluded from that claim (see runner.py's docstring) since it is a
    real wall-clock instant by contract; findings[] and summary are not.
    """
    target = _write_artifact(tmp_path)
    monkeypatch.chdir(tmp_path)

    def run_once():
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_scripted_lane(
                skill_name="critique-toy",
                skill_version="0.1.0",
                rubrics=["TOY"],
                check_fn=_one_finding_check,
                argv=[str(target)],
                now=FIXED_NOW,
            )
        return json.loads(buf.getvalue())

    first = run_once()
    second = run_once()

    assert first["findings"] == second["findings"]
    assert first["summary"] == second["summary"]
