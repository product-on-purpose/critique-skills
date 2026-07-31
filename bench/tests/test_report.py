"""Tests for bench/report.py: the results-table generator and its
--check drift mode (S-03 AC-6)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bench.report import END_MARKER, START_MARKER, main, render_baseline_comparison, render_block, render_entries_table, splice


def _metric(value, numerator=0, denominator=0) -> dict:
    return {"value": value, "numerator": numerator, "denominator": denominator}


def _consistency(value, artifacts_with_pairs=0, total_pairs=0) -> dict:
    return {"value": value, "artifacts_with_pairs": artifacts_with_pairs, "total_pairs": total_pairs}


def _entry(skill: str, **overrides) -> dict:
    base = {
        "skill": skill,
        "skill_version": "1.0.0",
        "model": "claude-sonnet-4-5-20250929",
        "domain": "toy",
        "artifact_type": "markdown-prose",
        "artifacts_scored": 3,
        "unresolvable_claims": 0,
        "recall": _metric(0.667, 2, 3),
        "precision": _metric(1.0, 2, 2),
        "clean_fp_rate": _metric(0.0, 0, 1),
        "consistency": _consistency(0.8, 2, 4),
        "consistency_exact": _consistency(0.6, 2, 4),
    }
    base.update(overrides)
    return base


def test_render_entries_table_empty_says_so() -> None:
    assert render_entries_table([]) == "_No run set has been scored yet._"


def test_render_entries_table_formats_values_to_three_decimals() -> None:
    table = render_entries_table([_entry("critique-toy")])
    assert "critique-toy" in table
    assert "0.667" in table
    assert "1.000" in table


def test_render_entries_table_null_metric_renders_as_na() -> None:
    table = render_entries_table([_entry("critique-toy", recall=_metric(None, 0, 0))])
    assert "n/a" in table


def test_baseline_comparison_matches_by_domain_and_model() -> None:
    entries = [
        _entry("critique-toy", recall=_metric(0.8, 4, 5), precision=_metric(0.9, 9, 10)),
        _entry("baseline-generic", recall=_metric(0.0, 0, 5), precision=_metric(0.0, 0, 3)),
    ]
    table = render_baseline_comparison(entries)
    assert "critique-toy" in table
    assert "beats baseline" in table
    assert "0.800" in table and "0.000" in table


def test_baseline_comparison_absent_says_so() -> None:
    entries = [_entry("critique-toy")]
    assert render_baseline_comparison(entries) == "_No baseline comparison available yet._"


def test_baseline_comparison_below_baseline_verdict() -> None:
    entries = [
        _entry("critique-weak", recall=_metric(0.1, 1, 10)),
        _entry("baseline-generic", recall=_metric(0.3, 3, 10)),
    ]
    table = render_baseline_comparison(entries)
    assert "below baseline" in table


def test_render_block_empty_entries_is_a_short_placeholder() -> None:
    results = {"run_set": "none", "generated_at": "1970-01-01T00:00:00Z", "entries": []}
    block = render_block(results)
    assert block.startswith(START_MARKER)
    assert block.endswith(END_MARKER)
    assert "No run set has been scored yet" in block
    assert "1970-01-01" not in block


def test_render_block_contains_markers() -> None:
    results = {"run_set": "rs-1", "generated_at": "2026-07-31T00:00:00Z", "entries": [_entry("critique-toy")]}
    block = render_block(results)
    assert block.startswith(START_MARKER)
    assert block.endswith(END_MARKER)
    assert "rs-1" in block


def test_splice_replaces_only_the_marked_region() -> None:
    target = f"# Title\n\nBefore text.\n\n{START_MARKER}\nold content\n{END_MARKER}\n\nAfter text.\n"
    new_text = splice(target, f"{START_MARKER}\nnew content\n{END_MARKER}")
    assert "Before text." in new_text
    assert "After text." in new_text
    assert "old content" not in new_text
    assert "new content" in new_text


def test_splice_without_markers_raises() -> None:
    with pytest.raises(ValueError):
        splice("no markers here", f"{START_MARKER}\nx\n{END_MARKER}")


def test_cli_check_reports_no_drift_after_update(tmp_path: Path) -> None:
    results = {
        "results_version": "1.0.0",
        "run_set": "rs-1",
        "generated_at": "2026-07-31T00:00:00Z",
        "entries": [_entry("critique-toy")],
    }
    results_path = tmp_path / "results.json"
    results_path.write_text(json.dumps(results), encoding="utf-8")

    target_path = tmp_path / "README.md"
    target_path.write_text(f"# Bench\n\n{START_MARKER}\nplaceholder\n{END_MARKER}\n", encoding="utf-8")

    exit_code = main(["table", "--results", str(results_path), "--target", str(target_path)])
    assert exit_code == 0
    assert "critique-toy" in target_path.read_text(encoding="utf-8")

    check_code = main(["table", "--results", str(results_path), "--target", str(target_path), "--check"])
    assert check_code == 0


def test_cli_check_detects_drift_before_update(tmp_path: Path) -> None:
    results = {
        "results_version": "1.0.0",
        "run_set": "rs-1",
        "generated_at": "2026-07-31T00:00:00Z",
        "entries": [_entry("critique-toy")],
    }
    results_path = tmp_path / "results.json"
    results_path.write_text(json.dumps(results), encoding="utf-8")

    target_path = tmp_path / "README.md"
    target_path.write_text(f"# Bench\n\n{START_MARKER}\nplaceholder\n{END_MARKER}\n", encoding="utf-8")

    check_code = main(["table", "--results", str(results_path), "--target", str(target_path), "--check"])
    assert check_code == 1
    # --check must not have written anything.
    assert "placeholder" in target_path.read_text(encoding="utf-8")
