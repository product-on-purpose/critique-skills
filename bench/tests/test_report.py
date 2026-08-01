"""Tests for bench/report.py: the results-table generator and its
--check drift mode (S-03 AC-6)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bench.report import (
    END_MARKER,
    START_MARKER,
    main,
    render_baseline_comparison_location,
    render_block,
    render_criterion_table,
    render_entries_table,
    splice,
)


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
        "recall_location": _metric(0.667, 2, 3),
        "precision_location": _metric(1.0, 2, 2),
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


def test_render_entries_table_header_names_the_k() -> None:
    """The artifact-count column is artifact-*runs* at k=5 (a 4-artifact
    domain shows 20), not a count of distinct artifacts; the header must
    say so rather than read as a plain artifact count."""
    table = render_entries_table([_entry("critique-toy")])
    assert "Artifact-runs (k=5)" in table
    assert "| Artifacts |" not in table


def test_criterion_table_has_no_baseline_or_verdict_columns() -> None:
    """The criterion-level cut is not a baseline comparison: baseline
    recall and precision are structurally 0.000 in every row by
    construction (`baseline-generic` carries a criterion no manifest
    plants a defect under), so a baseline column or a verdict built on
    it would be vacuous. Neither is rendered; only the skill's own
    recall and precision are, because those are measured."""
    entries = [
        _entry("critique-toy", recall=_metric(0.8, 4, 5), precision=_metric(0.9, 9, 10)),
        _entry("baseline-generic", recall=_metric(0.0, 0, 5), precision=_metric(0.0, 0, 3)),
    ]
    table = render_criterion_table(entries)
    assert "critique-toy" in table
    assert "0.800" in table and "0.900" in table
    assert "baseline-generic" not in table
    assert "Verdict" not in table
    assert "beats baseline" not in table
    header = table.splitlines()[0]
    assert header == "| Skill | Version | Domain | Model | Recall | Precision |"


def test_criterion_table_absent_says_so() -> None:
    entries = [_entry("baseline-generic")]
    assert render_criterion_table(entries) == "_No rubric-operationalization figures available yet._"


def test_baseline_comparison_location_reads_location_fields_not_criterion_fields() -> None:
    """Criterion-level and location-level must read independent columns:
    a skill can beat the baseline criterion-level while losing to it
    location-level, which is exactly the accessibility-domain finding
    this table exists to surface (bench/results/README.md, "Baseline
    comparison")."""
    entries = [
        _entry(
            "critique-weak",
            recall=_metric(0.2, 2, 10),  # beats baseline criterion-level
            recall_location=_metric(0.3, 3, 10),  # but loses location-level
            precision_location=_metric(0.4, 3, 8),
        ),
        _entry(
            "baseline-generic",
            recall=_metric(0.0, 0, 10),
            recall_location=_metric(0.5, 5, 10),
            precision_location=_metric(0.6, 5, 9),
        ),
    ]
    criterion_table = render_criterion_table(entries)
    location_table = render_baseline_comparison_location(entries)

    assert "0.200" in criterion_table  # criterion-level recall is shown, unlike baseline's 0.000
    assert "below baseline" in location_table  # 0.3 < 0.5, location-level
    assert "0.300" in location_table and "0.500" in location_table
    assert "0.400" in location_table and "0.600" in location_table


def test_baseline_comparison_location_absent_says_so() -> None:
    entries = [_entry("critique-toy")]
    assert render_baseline_comparison_location(entries) == "_No baseline comparison available yet._"


def test_baseline_comparison_location_ties_verdict() -> None:
    entries = [
        _entry("critique-toy", recall_location=_metric(0.5, 5, 10), precision_location=_metric(0.9, 9, 10)),
        _entry("baseline-generic", recall_location=_metric(0.5, 5, 10), precision_location=_metric(0.5, 5, 10)),
    ]
    table = render_baseline_comparison_location(entries)
    assert "ties baseline" in table


def test_baseline_comparison_location_wins_recall_loses_precision_is_not_a_pass() -> None:
    """A tier that wins recall but loses precision does not dominate the
    baseline and must not read "beats baseline": this is the exact
    critique-usability/sonnet shape (recall 0.857 against 0.829, precision
    0.169 against 0.181; bench/results/README.md, "Core skills, S-05
    AC-6")."""
    entries = [
        _entry(
            "critique-usability",
            skill_version="0.1.0",
            domain="usability",
            model="claude-sonnet-5",
            recall_location=_metric(0.857),
            precision_location=_metric(0.169),
        ),
        _entry(
            "baseline-generic",
            domain="usability",
            model="claude-sonnet-5",
            recall_location=_metric(0.829),
            precision_location=_metric(0.181),
        ),
    ]
    table = render_baseline_comparison_location(entries)
    assert "no pass on this tier" in table
    assert "beats baseline" not in table


def test_baseline_comparison_location_mixed_loss_annotates_qualifying_sibling_tier() -> None:
    """A skill that fails dominance on one tier but passes on the other
    ships on the strength of the passing tier; the failing row is
    annotated with which tier qualifies it, so a reader does not need to
    cross-reference the whole table to see whether "no pass on this
    tier" means the skill held or not."""
    entries = [
        _entry(
            "critique-usability",
            skill_version="0.1.0",
            domain="usability",
            model="claude-haiku-4-5-20251001",
            recall_location=_metric(0.8),
            precision_location=_metric(0.231),
        ),
        _entry(
            "baseline-generic",
            domain="usability",
            model="claude-haiku-4-5-20251001",
            recall_location=_metric(0.0),
            precision_location=_metric(0.0),
        ),
        _entry(
            "critique-usability",
            skill_version="0.1.0",
            domain="usability",
            model="claude-sonnet-5",
            recall_location=_metric(0.857),
            precision_location=_metric(0.169),
        ),
        _entry(
            "baseline-generic",
            domain="usability",
            model="claude-sonnet-5",
            recall_location=_metric(0.829),
            precision_location=_metric(0.181),
        ),
    ]
    table = render_baseline_comparison_location(entries)
    assert "no pass on this tier (qualifies via haiku)" in table


def test_baseline_comparison_location_mixed_loss_with_no_qualifying_sibling_stays_unannotated() -> None:
    """A mixed-result tier with no passing sibling (only one tier
    measured, or both fail) gets the plain "no pass on this tier" text,
    not a fabricated qualification."""
    entries = [
        _entry(
            "critique-lonely",
            recall_location=_metric(0.6),
            precision_location=_metric(0.2),
        ),
        _entry(
            "baseline-generic",
            recall_location=_metric(0.5),
            precision_location=_metric(0.3),
        ),
    ]
    table = render_baseline_comparison_location(entries)
    assert "no pass on this tier" in table
    assert "qualifies via" not in table


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


def test_render_block_leads_with_the_fair_location_level_table() -> None:
    """The front page must lead with the fair comparison: the
    location-level table's own header has to appear before the
    criterion-level table's header, and before the per-run entries
    table, in the rendered block."""
    entries = [
        _entry("critique-toy", recall=_metric(0.8, 4, 5)),
        _entry("baseline-generic", recall=_metric(0.0, 0, 5)),
    ]
    results = {"run_set": "rs-1", "generated_at": "2026-07-31T00:00:00Z", "entries": entries}
    block = render_block(results)

    location_pos = block.index("Skill recall (location)")
    entries_pos = block.index("Artifact-runs (k=5)")
    criterion_pos = block.index("Rubric operationalization (criterion-level)")

    assert location_pos < entries_pos < criterion_pos


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
