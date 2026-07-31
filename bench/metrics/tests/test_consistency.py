"""Tests for k-run consistency: mean pairwise Jaccard, tolerance-aware and
exact (bench/metrics/score.py `score_consistency`,
`aggregate_consistency`)."""

from __future__ import annotations

import pytest

from bench.metrics import score
from bench.metrics.tests.fixtures import TOY_MD, envelope, finding, manifest


def _sha() -> str:
    return manifest()["artifact_sha256"]


def test_identical_runs_score_perfect_consistency() -> None:
    m = manifest(defects=[])
    env = envelope(
        artifact_sha256=_sha(), findings=[finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2")]
    )
    envelopes = [env, env, env, env, env]  # k=5, identical
    result = score.score_consistency(m, envelopes, TOY_MD)
    assert result.runs == 5
    assert result.pairs == 10
    assert result.consistency == 1.0
    assert result.consistency_exact == 1.0


def test_two_runs_that_both_find_nothing_agree_perfectly() -> None:
    m = manifest(defects=[])
    env = envelope(artifact_sha256=_sha(), findings=[])
    result = score.score_consistency(m, [env, env], TOY_MD)
    assert result.consistency == 1.0
    assert result.consistency_exact == 1.0


def test_completely_disjoint_runs_score_zero() -> None:
    m = manifest(defects=[])
    env_a = envelope(
        artifact_sha256=_sha(), findings=[finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 1")]
    )
    env_b = envelope(
        artifact_sha256=_sha(), findings=[finding(finding_id="F-001", criterion="TOY-HEDGE", location="paragraph 4")]
    )
    result = score.score_consistency(m, [env_a, env_b], TOY_MD)
    assert result.consistency == 0.0
    assert result.consistency_exact == 0.0


def test_different_phrasing_same_paragraph_agrees_under_tolerant_not_penalized() -> None:
    m = manifest(defects=[])
    env_a = envelope(
        artifact_sha256=_sha(), findings=[finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2")]
    )
    env_b = envelope(
        artifact_sha256=_sha(),
        findings=[finding(finding_id="G-001", criterion="TOY-ACTIVE", location="Service window, second paragraph")],
    )
    result = score.score_consistency(m, [env_a, env_b], TOY_MD)
    assert result.consistency == 1.0
    assert result.consistency_exact == 1.0  # both resolve to the same canonical paragraph key


def test_fewer_than_two_runs_yields_no_computable_consistency() -> None:
    m = manifest(defects=[])
    env = envelope(artifact_sha256=_sha(), findings=[])
    result = score.score_consistency(m, [env], TOY_MD)
    assert result.runs == 1
    assert result.pairs == 0
    assert result.consistency is None
    assert result.consistency_exact is None


def test_aggregate_consistency_is_equal_weight_mean_skipping_uncomputable() -> None:
    scores = [
        score.ConsistencyScore(artifact="a", runs=5, pairs=10, consistency=0.8, consistency_exact=0.6),
        score.ConsistencyScore(artifact="b", runs=5, pairs=10, consistency=0.4, consistency_exact=0.2),
        score.ConsistencyScore(artifact="c", runs=1, pairs=0, consistency=None, consistency_exact=None),
    ]
    agg = score.aggregate_consistency(scores)
    assert agg.value == pytest.approx(0.6)
    assert agg.denominator == 2

    agg_exact = score.aggregate_consistency_exact(scores)
    assert agg_exact.value == pytest.approx(0.4)
