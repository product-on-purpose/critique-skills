"""S-03 AC-4: `bench/metrics/` computes recall, precision, and Jaccard
consistency from envelopes plus manifests, with unit tests covering:
perfect run, empty run, duplicate findings, location-tolerance edge, and
clean-artifact false positive. This module is those five scenarios, one
test function each, plus the aggregation arithmetic they feed.
"""

from __future__ import annotations

from bench.metrics import score
from bench.metrics.tests.fixtures import TOY_MD, envelope, finding, manifest, paragraph_defect

ARTIFACT_SHA = None  # set per test via manifest()'s own hash of TOY_MD


def _sha() -> str:
    return manifest()["artifact_sha256"]


# --- 1. Perfect run --------------------------------------------------------


def test_perfect_run_matches_every_defect_at_full_precision() -> None:
    m = manifest(
        defects=[
            paragraph_defect("TOY-ACTIVE", 2),
            paragraph_defect("TOY-HEDGE", 4),
        ]
    )
    env = envelope(
        artifact_sha256=_sha(),
        findings=[
            finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2"),
            finding(finding_id="F-002", criterion="TOY-HEDGE", location="paragraph 4"),
        ],
    )
    result = score.score_artifact(m, env, TOY_MD)
    assert result.defects_total == 2
    assert result.defects_matched == 2
    assert result.claims_total == 2
    assert result.claims_matched == 2
    assert result.unresolvable_claims == 0

    recall = score.aggregate_recall([result])
    precision = score.aggregate_precision([result])
    assert recall.value == 1.0
    assert precision.value == 1.0


# --- 2. Empty run -----------------------------------------------------------


def test_empty_run_scores_zero_recall_and_undefined_precision() -> None:
    m = manifest(
        defects=[
            paragraph_defect("TOY-ACTIVE", 2),
            paragraph_defect("TOY-HEDGE", 4),
        ]
    )
    env = envelope(artifact_sha256=_sha(), findings=[])
    result = score.score_artifact(m, env, TOY_MD)
    assert result.defects_total == 2
    assert result.defects_matched == 0
    assert result.claims_total == 0
    assert result.claims_matched == 0

    recall = score.aggregate_recall([result])
    precision = score.aggregate_precision([result])
    assert recall.value == 0.0
    # No claims were emitted at all: precision is not computable, not zero.
    assert precision.value is None
    assert precision.denominator == 0


# --- 3. Duplicate findings --------------------------------------------------


def test_duplicate_findings_earn_recall_once_and_cost_precision_every_time() -> None:
    m = manifest(defects=[paragraph_defect("TOY-ACTIVE", 2)])
    env = envelope(
        artifact_sha256=_sha(),
        findings=[
            finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2"),
            finding(finding_id="F-002", criterion="TOY-ACTIVE", location="paragraph 2"),
        ],
    )
    result = score.score_artifact(m, env, TOY_MD)
    assert result.defects_total == 1
    assert result.defects_matched == 1  # earned once
    assert result.claims_total == 2
    assert result.claims_matched == 1  # the duplicate costs precision

    recall = score.aggregate_recall([result])
    precision = score.aggregate_precision([result])
    assert recall.value == 1.0
    assert precision.value == 0.5


# --- 4. Location-tolerance edge ---------------------------------------------


def test_location_tolerance_edge_hit_at_plus_one_miss_at_plus_two() -> None:
    m = manifest(defects=[paragraph_defect("TOY-ACTIVE", 2)])

    # Edge: paragraph 3 is one away from the planted paragraph 2, inside
    # the plus-or-minus-1 window, and must be scored a hit.
    env_edge = envelope(
        artifact_sha256=_sha(),
        findings=[finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 3")],
    )
    edge_result = score.score_artifact(m, env_edge, TOY_MD)
    assert edge_result.defects_matched == 1
    assert score.aggregate_recall([edge_result]).value == 1.0

    # Just outside: paragraph 4 is two away from paragraph 2, outside the
    # window, and must be scored a miss.
    env_beyond = envelope(
        artifact_sha256=_sha(),
        findings=[finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 4")],
    )
    beyond_result = score.score_artifact(m, env_beyond, TOY_MD)
    assert beyond_result.defects_matched == 0
    assert score.aggregate_recall([beyond_result]).value == 0.0


# --- 5. Clean-artifact false positive ---------------------------------------


def test_clean_artifact_claims_count_against_precision_and_fp_rate() -> None:
    m = manifest(defects=[])  # clean artifact
    env = envelope(
        artifact_sha256=_sha(),
        findings=[
            finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 1"),
            finding(finding_id="F-002", criterion="TOY-HEDGE", location="paragraph 3"),
        ],
    )
    result = score.score_artifact(m, env, TOY_MD)
    assert result.is_clean is True
    assert result.defects_total == 0
    assert result.claims_total == 2
    assert result.claims_matched == 0  # nothing planted, so nothing to match

    # Excluded from recall's denominator entirely, not scored as a miss.
    recall = score.aggregate_recall([result])
    assert recall.value is None
    assert recall.denominator == 0

    # Counted against precision.
    precision = score.aggregate_precision([result])
    assert precision.value == 0.0

    # Reported on its own as claims-per-clean-artifact.
    fp_rate = score.aggregate_clean_fp_rate([result])
    assert fp_rate.value == 2.0
    assert fp_rate.numerator == 2
    assert fp_rate.denominator == 1


# --- Aggregation across several artifacts (pooling convention) -------------


def test_aggregate_recall_pools_across_artifacts_defect_weighted() -> None:
    scores = [
        score.ArtifactScore(
            artifact="a", domain="toy", artifact_type="markdown-prose", is_clean=False,
            defects_total=4, defects_matched=2, claims_total=4, claims_matched=2, unresolvable_claims=0,
        ),
        score.ArtifactScore(
            artifact="b", domain="toy", artifact_type="markdown-prose", is_clean=False,
            defects_total=1, defects_matched=1, claims_total=1, claims_matched=1, unresolvable_claims=0,
        ),
        score.ArtifactScore(
            artifact="c", domain="toy", artifact_type="markdown-prose", is_clean=True,
            defects_total=0, defects_matched=0, claims_total=3, claims_matched=0, unresolvable_claims=0,
        ),
    ]
    recall = score.aggregate_recall(scores)
    assert recall.numerator == 3 and recall.denominator == 5
    assert recall.value == 0.6

    precision = score.aggregate_precision(scores)
    assert precision.numerator == 3 and precision.denominator == 8
    assert precision.value == 0.375

    fp_rate = score.aggregate_clean_fp_rate(scores)
    assert fp_rate.numerator == 3 and fp_rate.denominator == 1
    assert fp_rate.value == 3.0


def test_round3_rounds_only_at_serialization_and_preserves_none() -> None:
    assert score.round3(1 / 3) == 0.333
    assert score.round3(None) is None
