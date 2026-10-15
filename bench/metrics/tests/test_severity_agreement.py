"""Severity agreement (E22): of the claims matched to planted defects, the
share that carry exactly the defect's `severity_expected`
(`bench/metrics/match.match_pairs`, `bench/metrics/score.aggregate_severity_agreement`).

Every corpus manifest has recorded `severity_expected` since v0.1.0 and
nothing read it. The matcher used to return only the two matched index sets,
which discards which claim matched which defect; severity can only be
compared once the pairing is kept.
"""

from __future__ import annotations

from bench.metrics import claims as claims_mod
from bench.metrics import locate, match, score
from bench.metrics.tests.fixtures import TOY_MD, envelope, finding, manifest, paragraph_defect

ARTIFACT = "bench/corpus/toy/toy-001.md"


def _manifest(defects: list[dict]) -> dict:
    return manifest(artifact=ARTIFACT, artifact_text=TOY_MD, defects=defects)


def _envelope(m: dict, findings: list[dict]) -> dict:
    return envelope(artifact=ARTIFACT, artifact_sha256=m["artifact_sha256"], findings=findings)


def test_match_pairs_agrees_with_the_two_matched_sets() -> None:
    """`match_claims_to_defects` is now derived from `match_pairs`; both must
    describe the same assignment."""
    m = _manifest([paragraph_defect("TOY-ACTIVE", 2), paragraph_defect("TOY-HEDGE", 4)])
    env = _envelope(
        m,
        [
            finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2"),
            finding(finding_id="F-002", criterion="TOY-HEDGE", location="paragraph 1"),
        ],
    )
    claim_list = claims_mod.claims_from_envelope(env)
    parsed = locate.parse_artifact("markdown-prose", TOY_MD)
    resolved = [locate.resolve_location(parsed, "markdown-prose", c.location, artifact_path=ARTIFACT) for c in claim_list]

    pairs = match.match_pairs(parsed, "markdown-prose", claim_list, resolved, m["defects"])
    defect_set, claim_set = match.match_claims_to_defects(parsed, "markdown-prose", claim_list, resolved, m["defects"])

    assert {d for d, _ in pairs} == defect_set
    assert {c for _, c in pairs} == claim_set
    assert len(pairs) == len(defect_set) == len(claim_set)


def test_score_artifact_counts_exact_severity_agreement_on_matched_pairs() -> None:
    m = _manifest(
        [paragraph_defect("TOY-ACTIVE", 2, severity=2), paragraph_defect("TOY-HEDGE", 4, severity=3)]
    )
    env = _envelope(
        m,
        [
            finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2", severity=2),
            # Matched, but rated one step below the planted severity: a disagreement.
            finding(finding_id="F-002", criterion="TOY-HEDGE", location="paragraph 4", severity=2),
        ],
    )
    s = score.score_artifact(m, env, TOY_MD)
    assert s.defects_matched == 2
    assert (s.severity_pairs, s.severity_agreements) == (2, 1)


def test_unmatched_claims_and_missed_defects_do_not_enter_the_ratio() -> None:
    """Severity agreement reads matched pairs only. Recall and precision
    already measure misses and stray claims; counting them here would make
    this a third copy of the same signal."""
    m = _manifest([paragraph_defect("TOY-ACTIVE", 2, severity=2), paragraph_defect("TOY-HEDGE", 4, severity=3)])
    env = _envelope(
        m,
        [
            finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2", severity=2),
            finding(finding_id="F-002", criterion="TOY-WRONG", location="paragraph 1", severity=4),
        ],
    )
    s = score.score_artifact(m, env, TOY_MD)
    assert (s.severity_pairs, s.severity_agreements) == (1, 1)


def test_a_defect_without_severity_expected_is_left_out() -> None:
    defect = paragraph_defect("TOY-ACTIVE", 2)
    del defect["severity_expected"]
    m = _manifest([defect])
    env = _envelope(m, [finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2")])
    s = score.score_artifact(m, env, TOY_MD)
    assert s.defects_matched == 1
    assert s.severity_pairs == 0


def test_aggregate_pools_integers_and_is_none_with_no_pairs() -> None:
    m = _manifest([paragraph_defect("TOY-ACTIVE", 2, severity=2)])
    agree = score.score_artifact(
        m, _envelope(m, [finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2", severity=2)]), TOY_MD
    )
    disagree = score.score_artifact(
        m, _envelope(m, [finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2", severity=4)]), TOY_MD
    )
    pooled = score.aggregate_severity_agreement([agree, disagree, agree])
    assert (pooled.numerator, pooled.denominator) == (2, 3)

    nothing = score.score_artifact(m, _envelope(m, []), TOY_MD)
    assert score.aggregate_severity_agreement([nothing]).value is None
