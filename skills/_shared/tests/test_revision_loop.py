"""N4 (the revision-loop chain): the deterministic steps in skills/_shared/revision_loop.py.

Every test runs on committed fixtures or on documents built from them, with no model call
(N4 decision D9). AC numbers refer to
docs/internal/release-plans/_unassigned/N4_revision-loop-chain/spec.md.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from contract.validate import document_kind, validate_document
from skills._shared import revision_loop as rl

REPO_ROOT = Path(__file__).resolve().parents[3]
DOMAINS = ("accessibility", "argument", "clarity", "docs", "forms", "microcopy", "usability")


def _envelope(domain: str = "argument") -> dict:
    return rl.load_envelope(REPO_ROOT / "examples" / domain / "envelope.json")


def _log(domain: str = "argument") -> dict:
    return json.loads((REPO_ROOT / "examples" / domain / "dispositions.json").read_text("utf-8"))


def _converged(envelope: dict) -> dict:
    """The same run with every severity-3 and severity-4 finding removed, histogram reconciled."""
    env = copy.deepcopy(envelope)
    env["findings"] = [f for f in env["findings"] if f["severity"] < 3]
    by = env["summary"]["by_severity"]
    by["3"] = 0
    by["4"] = 0
    env["summary"]["gate"] = "pass"
    assert validate_document(env).ok
    return env


# --------------------------------------------------------------------------
# AC-2: the stop-check
# --------------------------------------------------------------------------


def test_stop_check_converged_when_no_severity_3_or_4_remains():
    check = rl.stop_check(_converged(_envelope()), 1)
    assert check.decision == rl.STOP_CONVERGED
    assert check.severity_3_or_4 == 0


def test_converged_beats_the_bound_on_the_third_iteration():
    assert rl.stop_check(_converged(_envelope()), 3).decision == rl.STOP_CONVERGED


@pytest.mark.parametrize("iteration", [3, 4])
def test_stop_check_bound_reached_at_iteration_3(iteration: int):
    check = rl.stop_check(_envelope(), iteration)
    assert check.decision == rl.STOP_BOUND
    assert check.severity_3_or_4 == 2


@pytest.mark.parametrize("iteration", [1, 2])
def test_stop_check_continues_below_the_bound(iteration: int):
    assert rl.stop_check(_envelope(), iteration).decision == rl.CONTINUE


def test_stop_check_rejects_iteration_zero():
    with pytest.raises(rl.UsageError):
        rl.stop_check(_envelope(), 0)


def test_pause_writes_no_brief_when_the_loop_stops():
    log = _log()
    log["iteration"] = 3
    check, brief = rl.pause(_envelope(), log)
    assert check.decision == rl.STOP_BOUND
    assert brief is None


def test_pause_stops_when_nothing_was_accepted():
    log = _log()
    for entry in log["dispositions"]:
        entry["disposition"] = "reject"
    check, brief = rl.pause(_envelope(), log)
    assert check.decision == rl.STOP_NOTHING_ACCEPTED
    assert brief is None


# --------------------------------------------------------------------------
# AC-3 and AC-4: the brief
# --------------------------------------------------------------------------


@pytest.mark.parametrize("domain", DOMAINS)
def test_brief_holds_one_item_per_accepted_finding(domain: str):
    envelope, log = _envelope(domain), _log(domain)
    brief = rl.build_brief(envelope, log)
    accepted = []
    for entry in log["dispositions"]:
        if entry["disposition"] == "accept" and entry["finding_id"] not in accepted:
            accepted.append(entry["finding_id"])
    assert [item["finding_id"] for item in brief["items"]] == accepted
    findings = {f["id"]: f for f in envelope["findings"]}
    for item in brief["items"]:
        finding = findings[item["finding_id"]]
        for field in ("criterion", "location", "fix"):
            assert item[field] == finding[field]
    assert document_kind(brief) == "revisionBrief"
    result = validate_document(brief, referenced_envelope=envelope)
    assert result.ok, result.errors


def test_brief_is_byte_identical_across_two_runs(tmp_path: Path):
    out1, out2 = tmp_path / "one.json", tmp_path / "two.json"
    args = [
        "brief",
        "--envelope", str(REPO_ROOT / "examples/argument/envelope.json"),
        "--dispositions", str(REPO_ROOT / "examples/argument/dispositions.json"),
    ]
    assert rl.main([*args, "--out", str(out1)]) == 0
    assert rl.main([*args, "--out", str(out2)]) == 0
    assert out1.read_bytes() == out2.read_bytes()


def test_brief_carries_the_logs_iteration():
    log = _log()
    log["iteration"] = 2
    assert rl.build_brief(_envelope(), log)["iteration"] == 2
    assert rl.build_brief(_envelope(), _log())["iteration"] == 1


def test_brief_refuses_a_log_for_a_different_run():
    log = _log()
    log["envelope"]["timestamp"] = "2026-08-01T00:00:00Z"
    with pytest.raises(rl.LoopError, match="different run"):
        rl.build_brief(_envelope(), log)


def test_default_brief_path_is_beside_the_artifact():
    path = rl.default_brief_path(_envelope())
    assert path.as_posix() == (
        "skills/critique-argument/examples/argument-golden-02-hedge-and-marker.revision-brief.json"
    )


# --------------------------------------------------------------------------
# AC-1: the steps in order, and the artifact is never written
# --------------------------------------------------------------------------


def _workspace(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A copy of the argument example laid out as a person would have it: the artifact at the
    path its envelope records, relative to a working directory, plus the envelope and the log."""
    envelope = _envelope()
    artifact_rel = Path(envelope["run"]["artifact"])
    artifact = tmp_path / artifact_rel
    artifact.parent.mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / artifact_rel, artifact)
    env_path = tmp_path / "examples/argument/envelope.json"
    env_path.parent.mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / "examples/argument/envelope.json", env_path)
    log_path = tmp_path / "examples/argument/dispositions.json"
    shutil.copyfile(REPO_ROOT / "examples/argument/dispositions.json", log_path)
    return artifact, env_path, log_path


def test_the_first_invocation_never_writes_the_artifact(tmp_path: Path, monkeypatch, capsys):
    artifact, env_path, log_path = _workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    recorded = _envelope()["run"]["artifact_sha256"]
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == recorded

    assert rl.main(["stop-check", "--envelope", str(env_path), "--dispositions", str(log_path)]) == 0
    assert json.loads(capsys.readouterr().out)["decision"] == rl.CONTINUE
    assert rl.main(["brief", "--envelope", str(env_path), "--dispositions", str(log_path)]) == 0
    result = json.loads(capsys.readouterr().out)

    brief_path = artifact.with_name(artifact.stem + rl.BRIEF_SUFFIX)
    assert result["brief"] == brief_path.relative_to(tmp_path).as_posix()
    assert brief_path.is_file()
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == recorded


def test_brief_refuses_to_overwrite_the_artifact(tmp_path: Path, monkeypatch, capsys):
    artifact, env_path, log_path = _workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    before = artifact.read_bytes()
    code = rl.main(
        ["brief", "--envelope", str(env_path), "--dispositions", str(log_path), "--out", str(artifact)]
    )
    assert code == rl.EXIT_USAGE
    assert artifact.read_bytes() == before


# --------------------------------------------------------------------------
# AC-6: resume
# --------------------------------------------------------------------------


def _revise(artifact: Path) -> None:
    artifact.write_bytes(artifact.read_bytes() + b"\nRevised.\n")


def test_resume_finds_the_prior_run_from_the_log(tmp_path: Path, monkeypatch):
    artifact, env_path, log_path = _workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    _revise(artifact)
    result = rl.resume(artifact, log_path)
    assert result["prior_envelope"] == "examples/argument/envelope.json"
    assert result["prior_iteration"] == 1
    assert result["iteration"] == 2
    assert result["skill"] == "critique-argument"


def test_resume_accepts_the_same_envelope_named_twice(tmp_path: Path, monkeypatch):
    artifact, env_path, log_path = _workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    _revise(artifact)
    assert rl.resume(artifact, log_path, env_path)["iteration"] == 2


def test_resume_reports_a_conflict_by_name(tmp_path: Path, monkeypatch):
    artifact, env_path, log_path = _workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    _revise(artifact)
    other = tmp_path / "other.envelope.json"
    shutil.copyfile(env_path, other)
    with pytest.raises(rl.LoopError, match="conflicting prior envelopes") as excinfo:
        rl.resume(artifact, log_path, other)
    assert "envelope.path" in str(excinfo.value) and "--envelope" in str(excinfo.value)


def test_resume_needs_an_envelope_when_the_log_records_no_path(tmp_path: Path, monkeypatch):
    artifact, env_path, log_path = _workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    _revise(artifact)
    log = json.loads(log_path.read_text("utf-8"))
    del log["envelope"]["path"]
    del log["envelope"]["envelope_sha256"]
    log_path.write_text(json.dumps(log), encoding="utf-8")
    with pytest.raises(rl.UsageError, match="--envelope"):
        rl.resume(artifact, log_path)
    assert rl.resume(artifact, log_path, env_path)["iteration"] == 2


def test_resume_rejects_an_envelope_whose_bytes_changed(tmp_path: Path, monkeypatch):
    artifact, env_path, log_path = _workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    _revise(artifact)
    env_path.write_text(json.dumps(json.loads(env_path.read_text("utf-8"))), encoding="utf-8")
    with pytest.raises(rl.LoopError, match="envelope_sha256"):
        rl.resume(artifact, log_path)


def test_resume_rejects_an_unrevised_artifact(tmp_path: Path, monkeypatch):
    artifact, env_path, log_path = _workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(rl.LoopError, match="byte-identical"):
        rl.resume(artifact, log_path)


def test_resume_refuses_to_start_a_fourth_iteration(tmp_path: Path, monkeypatch):
    artifact, env_path, log_path = _workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    _revise(artifact)
    log = json.loads(log_path.read_text("utf-8"))
    log["contract_version"] = "1.1.0"
    log["iteration"] = 3
    log_path.write_text(json.dumps(log), encoding="utf-8")
    with pytest.raises(rl.LoopError, match="bound"):
        rl.resume(artifact, log_path)


def test_every_example_log_binds_its_envelope_bytes():
    """A recorded envelope_sha256 is only a binding while it matches. The argument example's went
    stale when PR 78 (E5) rewrote its envelope, and nothing noticed until resume checked it."""
    for log_path in sorted(REPO_ROOT.glob("examples/*/dispositions.json")):
        ref = json.loads(log_path.read_text("utf-8"))["envelope"]
        if "envelope_sha256" not in ref:
            continue
        actual = hashlib.sha256((REPO_ROOT / ref["path"]).read_bytes()).hexdigest()
        assert actual == ref["envelope_sha256"], log_path


# --------------------------------------------------------------------------
# AC-7: compare
# --------------------------------------------------------------------------


def test_compare_reports_criterion_and_severity_deltas():
    previous = _envelope()
    current = _converged(previous)
    result = rl.compare(previous, current)
    assert result["by_criterion"]["TOULMIN-CLAIM"] == {"previous": 1, "current": 0, "delta": -1}
    assert result["by_criterion"]["TOULMIN-CLAIM-MARKER"] == {"previous": 1, "current": 1, "delta": 0}
    assert result["by_severity"]["3"] == {"previous": 2, "current": 0, "delta": -2}
    assert set(result["by_severity"]) == {"0", "1", "2", "3", "4"}
    # It never pairs findings across runs.
    assert "findings" not in json.dumps(result)


def test_compare_refuses_two_different_skills():
    with pytest.raises(rl.LoopError, match="different skills"):
        rl.compare(_envelope("argument"), _envelope("clarity"))


def test_cli_exit_codes(tmp_path: Path):
    assert rl.main(["compare", "--previous", "nope.json", "--current", "nope.json"]) == rl.EXIT_USAGE
    assert rl.main(["stop-check"]) == rl.EXIT_USAGE
    bad = tmp_path / "bad.json"
    bad.write_text('{"run": {}}', encoding="utf-8")
    assert rl.main(["stop-check", "--envelope", str(bad)]) == rl.EXIT_INVALID
