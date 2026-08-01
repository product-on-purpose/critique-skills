"""Tests for contract/validate_envelopes.py: the CI schema job's discovery glob and CLI.

Covers the P3 self-audit's "Known validator wiring gap" (docs/internal/execution/P3-report.md):
the original glob was scoped one level too shallow to ever reach
bench/results/runs/<skill>/<artifact>/<run>.json, so it reported "nothing to validate" despite
462 committed envelopes on disk.

Also covers the P4 integration follow-up: once `bench/results/runs-cal1/` (a second, differently
named run-set root; docs/internal/execution/P3-cal1-report.md) was committed, the single-root
`RUNS_DIR` glob could not see it. Discovery now walks every `bench/results/runs*` directory, not
just `bench/results/runs/`.
"""

from __future__ import annotations

import json
from pathlib import Path

from contract.tests.fixtures import example_envelope
from contract.validate_envelopes import discover_run_roots, find_envelope_files, main


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_find_envelope_files_reaches_the_real_harness_depth(tmp_path: Path) -> None:
    """The real layout: runs/<skill>/<artifact>/<run>.json and
    runs/baseline/<domain>/<artifact>/<run>.json, three and four levels deep respectively."""
    runs_dir = tmp_path / "runs"
    _write(runs_dir / "critique-clarity" / "clarity-001" / "haiku-r1.json", example_envelope())
    _write(runs_dir / "baseline" / "clarity" / "clarity-001" / "haiku-r1.json", example_envelope())

    found = find_envelope_files(runs_dir)

    assert len(found) == 2


def test_find_envelope_files_excludes_results_json_and_schema_and_raw_txt(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    _write(runs_dir / "critique-clarity" / "clarity-001" / "haiku-r1.json", example_envelope())
    _write(runs_dir / "results.json", {"entries": []})
    (runs_dir / "results.schema.json").parent.mkdir(parents=True, exist_ok=True)
    (runs_dir / "results.schema.json").write_text("{}", encoding="utf-8")
    (runs_dir / "baseline" / "clarity" / "clarity-001").mkdir(parents=True, exist_ok=True)
    (runs_dir / "baseline" / "clarity" / "clarity-001" / "haiku-r1.json.raw.txt").write_text(
        "raw model text, not json", encoding="utf-8"
    )

    found = find_envelope_files(runs_dir)

    assert len(found) == 1
    assert found[0].name == "haiku-r1.json"


def test_find_envelope_files_missing_root_is_empty() -> None:
    assert find_envelope_files(Path("this/does/not/exist")) == []


def test_find_envelope_files_is_sorted(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    _write(runs_dir / "critique-usability" / "usability-001" / "sonnet-r1.json", example_envelope())
    _write(runs_dir / "critique-clarity" / "clarity-001" / "haiku-r1.json", example_envelope())

    found = find_envelope_files(runs_dir)

    assert found == sorted(found)
    assert "critique-clarity" in str(found[0])


def test_discover_run_roots_finds_the_primary_and_calibration_sets(tmp_path: Path) -> None:
    """bench/results/runs/ and bench/results/runs-cal1/ are sibling run-set roots; discovery must
    find both, sorted, and not be fooled by an unrelated directory that merely starts with the
    same letters as something else in bench/results/ (e.g. a staging directory)."""
    (tmp_path / "runs").mkdir()
    (tmp_path / "runs-cal1").mkdir()
    (tmp_path / "staging-cal1").mkdir()  # not a runs* root; must be excluded

    roots = discover_run_roots(tmp_path)

    assert roots == [tmp_path / "runs", tmp_path / "runs-cal1"]


def test_discover_run_roots_missing_results_dir_is_empty() -> None:
    assert discover_run_roots(Path("this/does/not/exist")) == []


def test_main_reports_nothing_to_validate_before_any_run(tmp_path: Path, monkeypatch, capsys) -> None:
    import contract.validate_envelopes as ve

    monkeypatch.setattr(ve, "RESULTS_DIR", tmp_path)

    exit_code = main([])

    assert exit_code == 0
    assert "nothing to validate yet" in capsys.readouterr().out


def test_main_all_valid_exits_zero_and_reports_the_count(tmp_path: Path, monkeypatch, capsys) -> None:
    import contract.validate_envelopes as ve

    monkeypatch.setattr(ve, "RESULTS_DIR", tmp_path)
    runs_dir = tmp_path / "runs"
    _write(runs_dir / "critique-clarity" / "clarity-001" / "haiku-r1.json", example_envelope())
    _write(runs_dir / "critique-clarity" / "clarity-001" / "haiku-r2.json", example_envelope())

    exit_code = main([])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "2 file(s) valid." in out


def test_main_reaches_a_second_run_root_like_runs_cal1(tmp_path: Path, monkeypatch, capsys) -> None:
    """Regression test for the P4 discovery-glob gap: envelopes committed under a second run-set
    root (bench/results/runs-cal1/ in the real repo) must be discovered and validated alongside
    bench/results/runs/, not silently skipped."""
    import contract.validate_envelopes as ve

    monkeypatch.setattr(ve, "RESULTS_DIR", tmp_path)
    _write(
        tmp_path / "runs" / "critique-clarity" / "clarity-001" / "haiku-r1.json",
        example_envelope(),
    )
    _write(
        tmp_path / "runs-cal1" / "critique-accessibility" / "accessibility-001" / "haiku-r1.json",
        example_envelope(),
    )

    exit_code = main([])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "2 file(s) valid." in out


def test_main_an_invalid_envelope_exits_one_and_is_reported(tmp_path: Path, monkeypatch, capsys) -> None:
    import contract.validate_envelopes as ve

    monkeypatch.setattr(ve, "RESULTS_DIR", tmp_path)
    runs_dir = tmp_path / "runs"
    bad = example_envelope()
    del bad["summary"]  # required field missing
    _write(runs_dir / "critique-clarity" / "clarity-001" / "haiku-r1.json", bad)

    exit_code = main([])

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "FAIL" in err
    assert "1 of 1 file(s) failed" in err


def test_main_not_json_is_reported_as_a_failure_not_a_crash(tmp_path: Path, monkeypatch, capsys) -> None:
    import contract.validate_envelopes as ve

    monkeypatch.setattr(ve, "RESULTS_DIR", tmp_path)
    path = tmp_path / "runs" / "critique-clarity" / "clarity-001" / "haiku-r1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json", encoding="utf-8")

    exit_code = main([])

    assert exit_code == 1
    assert "not valid JSON" in capsys.readouterr().err
