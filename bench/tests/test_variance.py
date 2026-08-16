"""Tests for bench/variance.py: repetition decomposition, the reproduction guard, and the band.

No test here reaches a model. `bench/variance.py` has no transport at all: it reads committed
manifests and envelopes and computes, which is the point of it.

The split below is deliberate. Everything that can be tested against hand-built `ArtifactScore`
values is, because those tests are fast and say exactly which rule broke. Exactly one test scores
real committed envelopes, to prove the wiring holds end to end, and it uses `runs-cal1` (40
envelopes, 2 cells) rather than the 460-envelope grid so the suite does not pay for the point twice.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from bench import variance
from bench.metrics import score
from bench.variance import (
    VarianceError,
    _reproduction_failures,
    bootstrap_band,
    build_variance,
    parse_repetition_index,
    scoring_view,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = REPO_ROOT / "bench" / "corpus"
CAL1_DIR = REPO_ROOT / "bench" / "results" / "runs-cal1"
COMMITTED_RESULTS = REPO_ROOT / "bench" / "results" / "results.json"


def _artifact_score(*, defects_total: int, defects_matched: int, claims_total: int, claims_matched: int):
    return score.ArtifactScore(
        artifact="bench/corpus/toy/toy-001.md",
        domain="toy",
        artifact_type="markdown",
        is_clean=False,
        defects_total=defects_total,
        defects_matched=defects_matched,
        claims_total=claims_total,
        claims_matched=claims_matched,
        unresolvable_claims=0,
    )


# ---------------------------------------------------------------------------
# The repetition index, which is a filename convention and not a contract field
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("stem", "expected"),
    [
        ("haiku-r1", 1),
        ("sonnet-r5", 5),
        ("claude-haiku-4-5-r12", 12),
        ("steer-r2", 2),
        ("results", None),
        ("haiku", None),
        ("haiku-r", None),
        ("haiku-rx", None),
    ],
)
def test_parse_repetition_index(stem: str, expected: int | None) -> None:
    assert parse_repetition_index(Path(f"{stem}.json")) == expected


def test_an_envelope_with_no_repetition_index_is_refused(tmp_path) -> None:
    """A run set written under another naming convention cannot be decomposed, and saying so is
    better than silently banding a cell at k=1."""
    (tmp_path / "critique-toy" / "toy-001").mkdir(parents=True)
    (tmp_path / "critique-toy" / "toy-001" / "whenever.json").write_text("{}", encoding="utf-8")

    with pytest.raises(VarianceError) as excinfo:
        build_variance(CORPUS_DIR, [(tmp_path, "toy-run-set")], generated_at="2026-08-15T00:00:00Z")

    assert "carries no repetition index" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Scoping: probe run sets share identity fields with the grid and must not pool into it
# ---------------------------------------------------------------------------


def test_scoring_view_separates_probe_directories(tmp_path) -> None:
    for rel in ("critique-clarity/clarity-001/haiku-r1.json", "steering/clarity-001/steer-r1.json"):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    scored, excluded = scoring_view(tmp_path, exclude_top=("steering",))

    assert [p.name for p in scored] == ["haiku-r1.json"]
    assert [p.name for p in excluded] == ["steer-r1.json"]


def test_scoring_view_skips_computed_outputs(tmp_path) -> None:
    """results.json and variance.json live beside envelopes and are not envelopes."""
    for name in ("results.json", "variance.json"):
        (tmp_path / name).write_text("{}", encoding="utf-8")

    scored, excluded = scoring_view(tmp_path, exclude_top=())

    assert scored == []
    assert excluded == []


def test_the_default_exclusion_is_the_documented_probe_set() -> None:
    """bench/results/README.md excludes runs/steering/ by hand in its reproduction recipe, and
    records that as a fragility. Making it the default turns a step someone must remember into a
    property of the tool."""
    assert variance.DEFAULT_EXCLUDED_TOP_LEVEL == ("steering",)


# ---------------------------------------------------------------------------
# The reproduction guard: the whole file rests on this
# ---------------------------------------------------------------------------


def _cells_totalling(defects_matched: int, defects_total: int):
    """One cell, two repetitions, whose pooled recall is defects_matched / defects_total."""
    half_matched, half_total = defects_matched // 2, defects_total // 2
    per_repetition = {
        r: [_artifact_score(defects_total=half_total, defects_matched=half_matched, claims_total=10, claims_matched=half_matched)]
        for r in (1, 2)
    }
    return {
        ("p3", "critique-toy", "0.1.0", "model-a", "toy"): {
            "recall": per_repetition,
            "precision": per_repetition,
            "recall_location": per_repetition,
            "precision_location": per_repetition,
        }
    }


def test_the_guard_passes_when_repetitions_pool_back_to_the_committed_figure() -> None:
    cells = _cells_totalling(defects_matched=6, defects_total=10)
    committed = {
        ("critique-toy", "0.1.0", "model-a", "toy"): {
            "recall": {"numerator": 6, "denominator": 10},
            "precision": {"numerator": 6, "denominator": 20},
            "recall_location": {"numerator": 6, "denominator": 10},
            "precision_location": {"numerator": 6, "denominator": 20},
        }
    }

    failures, checked, matched = _reproduction_failures(cells, committed)

    assert failures == []
    assert (checked, matched) == (4, 4)


def test_the_guard_catches_a_decomposition_that_does_not_sum_back() -> None:
    """A decomposition that does not reproduce the published figure is measuring something else,
    and a band computed on top of it would be a number about nothing."""
    cells = _cells_totalling(defects_matched=6, defects_total=10)
    committed = {
        ("critique-toy", "0.1.0", "model-a", "toy"): {
            "recall": {"numerator": 7, "denominator": 10},  # the tamper
            "precision": {"numerator": 6, "denominator": 20},
            "recall_location": {"numerator": 6, "denominator": 10},
            "precision_location": {"numerator": 6, "denominator": 20},
        }
    }

    failures, checked, matched = _reproduction_failures(cells, committed)

    assert len(failures) == 1
    assert "recall" in failures[0]
    assert "6/10" in failures[0] and "7/10" in failures[0]
    assert (checked, matched) == (4, 3)


def test_a_cell_absent_from_the_committed_results_is_not_counted_as_checked() -> None:
    """Otherwise a run that lined up with nothing would report a clean verification."""
    failures, checked, matched = _reproduction_failures(_cells_totalling(6, 10), {})

    assert failures == []
    assert (checked, matched) == (0, 0)


def test_build_variance_refuses_when_nothing_was_verified(tmp_path) -> None:
    """Silence is not verification: a mismatched --corpus or --runs must fail loudly rather than
    emit a confident-looking band nothing checked."""
    empty_committed = {"entries": []}

    with pytest.raises(VarianceError) as excinfo:
        build_variance(
            CORPUS_DIR,
            [(CAL1_DIR, "cal1-2026-08-01")],
            generated_at="2026-08-15T00:00:00Z",
            repo_root=REPO_ROOT,
            committed_results=empty_committed,
        )

    assert "not verified against anything" in str(excinfo.value)


# ---------------------------------------------------------------------------
# The band itself
# ---------------------------------------------------------------------------


def test_the_band_is_seeded_and_reproducible() -> None:
    totals = {1: (6, 10), 2: (8, 10), 3: (5, 10), 4: (9, 10), 5: (7, 10)}

    first = bootstrap_band(totals, draws=2000, rng=random.Random(7))
    second = bootstrap_band(totals, draws=2000, rng=random.Random(7))

    assert first == second


def test_the_band_brackets_the_pooled_figure() -> None:
    totals = {1: (6, 10), 2: (8, 10), 3: (5, 10), 4: (9, 10), 5: (7, 10)}
    pooled = sum(n for n, _ in totals.values()) / sum(d for _, d in totals.values())

    low, high, sd = bootstrap_band(totals, draws=5000, rng=random.Random(1))

    assert low <= pooled <= high
    assert sd > 0


def test_a_cell_with_no_run_to_run_variation_gets_a_zero_width_band() -> None:
    """critique-docs on sonnet scored 1.000 in every repetition. A zero-width band is the honest
    answer for that, and it is why such a cell makes a brittle gate rather than a strong one."""
    totals = {r: (5, 5) for r in range(1, 6)}

    low, high, sd = bootstrap_band(totals, draws=1000, rng=random.Random(3))

    assert (low, high, sd) == (1.0, 1.0, 0.0)


def test_resampling_takes_whole_repetitions_not_individual_scores() -> None:
    """The published statistic is a ratio of sums across repetitions, so a resample must keep a
    repetition's numerator and denominator together. If it did not, a cell whose repetitions all
    share one denominator could produce a band value no repetition could ever yield."""
    totals = {1: (0, 10), 2: (10, 10)}

    low, high, _sd = bootstrap_band(totals, draws=4000, rng=random.Random(11))

    # Every resample of two repetitions drawn from {0/10, 10/10} pools to 0.0, 0.5 or 1.0.
    assert low in (0.0, 0.5, 1.0)
    assert high in (0.0, 0.5, 1.0)


# ---------------------------------------------------------------------------
# One end-to-end pass over real committed evidence
# ---------------------------------------------------------------------------


def test_the_calibration_run_set_decomposes_and_validates() -> None:
    committed = json.loads(COMMITTED_RESULTS.read_text(encoding="utf-8"))

    document = build_variance(
        CORPUS_DIR,
        [(CAL1_DIR, "cal1-2026-08-01")],
        generated_at="2026-08-15T00:00:00Z",
        repo_root=REPO_ROOT,
        committed_results=committed,
        draws=1000,
    )

    # 2 cells (haiku, sonnet) x 4 metrics. build_variance schema-validates before returning, so
    # reaching this line is itself the schema assertion.
    assert len(document["entries"]) == 8
    assert document["verification"] == {
        "performed": True,
        "cell_metrics_checked": 8,
        "cell_metrics_matched": 8,
    }
    assert document["envelopes_scored"] == 40

    for entry in document["entries"]:
        assert entry["run_set"] == "cal1-2026-08-01"
        assert entry["skill_version"] == "0.1.1"
        assert entry["k"] == 5
        assert len(entry["per_repetition"]) == 5
        assert entry["band_low"] <= entry["pooled"] <= entry["band_high"]
        assert entry["repetition_spread"] >= entry["band_width"] or entry["band_width"] == 0
