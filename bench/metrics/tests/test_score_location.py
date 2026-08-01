"""Location-level match mode: a finding scores a manifest defect when its
location resolves within the artifact type's tolerance to the defect's
location, criterion ID ignored entirely
(`bench/metrics/match.match_claims_to_defects(ignore_criterion=True)`,
`bench/metrics/score.score_artifact_location`).

This is the fair skill-versus-baseline comparison
(bench/results/README.md, "The baseline comparison, honestly measured"):
criterion-level recall and precision are pinned at exactly 0.0 for
`baseline-generic` in every domain, on every tier, because every baseline
finding carries the fixed criterion `BASELINE-GENERIC`
(`bench/baseline/postprocess.py`) that no manifest plants a defect under.
Location-level scoring drops the criterion-equality gate so a
criterion-less prompt can be measured on whether it pointed at the right
place at all. Computed from the same envelopes as the criterion-level
metrics, never a new run.

Test groups: (1) `match.match_claims_to_defects(ignore_criterion=True)`
directly, (2) `score.score_artifact_location`, (3) the end-to-end
`build_results` CLI entry point, confirming `recall_location` and
`precision_location` land in the assembled, schema-valid `results.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

from bench.metrics import locate, match, score
from bench.metrics.__main__ import build_results
from bench.metrics.claims import Claim
from bench.metrics.tests.fixtures import TOY_MD, envelope, finding, manifest, paragraph_defect

# --- 1. match.match_claims_to_defects(ignore_criterion=True) --------------


def _parsed():
    return locate.parse_artifact("markdown-prose", TOY_MD)


def test_ignore_criterion_matches_a_hit_location_under_any_criterion() -> None:
    """The scenario the criterion-level match exists to reject
    (bench/metrics/tests/test_match.py,
    test_wrong_criterion_never_matches_even_at_same_location) is exactly
    the scenario location-level scoring is built to credit."""
    parsed = _parsed()
    claims = [Claim(criterion="TOY-HEDGE", location="paragraph 2", finding_id="F-001", severity=2)]
    resolved = [locate.resolve_location(parsed, "markdown-prose", c.location) for c in claims]
    defects = [{"criterion": "TOY-ACTIVE", "location": {"kind": "paragraph", "paragraph": 2, "text": ""}}]

    criterion_level = match.match_claims_to_defects(parsed, "markdown-prose", claims, resolved, defects)
    assert criterion_level == (set(), set())

    location_level = match.match_claims_to_defects(
        parsed, "markdown-prose", claims, resolved, defects, ignore_criterion=True
    )
    assert location_level == ({0}, {0})


def test_ignore_criterion_still_assigns_each_claim_to_at_most_one_defect() -> None:
    """Greedy assignment stays one-to-one even with the criterion gate
    dropped: one claim at paragraph 2 cannot be double-counted against
    two different defects that both happen to sit there."""
    parsed = _parsed()
    claims = [Claim(criterion="TOY-MISC", location="paragraph 2", finding_id="F-001", severity=2)]
    resolved = [locate.resolve_location(parsed, "markdown-prose", c.location) for c in claims]
    defects = [
        {"criterion": "TOY-ACTIVE", "location": {"kind": "paragraph", "paragraph": 2, "text": ""}},
        {"criterion": "TOY-HEDGE", "location": {"kind": "paragraph", "paragraph": 2, "text": ""}},
    ]
    matched_defects, matched_claims = match.match_claims_to_defects(
        parsed, "markdown-prose", claims, resolved, defects, ignore_criterion=True
    )
    assert len(matched_defects) == 1
    assert matched_claims == {0}


def test_ignore_criterion_default_is_unchanged_criterion_level_behavior() -> None:
    """`ignore_criterion` defaults to False: every existing caller of
    `match_claims_to_defects` keeps the criterion-level predicate it had
    before this mode existed."""
    parsed = _parsed()
    claims = [Claim(criterion="TOY-HEDGE", location="paragraph 2", finding_id="F-001", severity=2)]
    resolved = [locate.resolve_location(parsed, "markdown-prose", c.location) for c in claims]
    defects = [{"criterion": "TOY-ACTIVE", "location": {"kind": "paragraph", "paragraph": 2, "text": ""}}]
    assert match.match_claims_to_defects(parsed, "markdown-prose", claims, resolved, defects) == (set(), set())


# --- 2. score.score_artifact_location --------------------------------------


def test_score_artifact_location_credits_right_location_wrong_criterion() -> None:
    m = manifest(defects=[paragraph_defect("TOY-ACTIVE", 2), paragraph_defect("TOY-HEDGE", 4)])
    env = envelope(
        artifact_sha256=manifest()["artifact_sha256"],
        findings=[
            finding(finding_id="F-001", criterion="TOY-MISC", location="paragraph 2"),
            finding(finding_id="F-002", criterion="TOY-MISC", location="paragraph 4"),
        ],
    )

    criterion_result = score.score_artifact(m, env, TOY_MD)
    assert criterion_result.defects_matched == 0
    assert criterion_result.claims_matched == 0
    assert score.aggregate_recall([criterion_result]).value == 0.0

    location_result = score.score_artifact_location(m, env, TOY_MD)
    assert location_result.defects_matched == 2
    assert location_result.claims_matched == 2
    assert score.aggregate_recall([location_result]).value == 1.0
    assert score.aggregate_precision([location_result]).value == 1.0

    # Everything but the match predicate is identical between the two scores.
    assert location_result.defects_total == criterion_result.defects_total
    assert location_result.claims_total == criterion_result.claims_total
    assert location_result.unresolvable_claims == criterion_result.unresolvable_claims


def test_score_artifact_location_matches_baseline_generic_style_envelope() -> None:
    """The motivating case: a criterion-less baseline (bench/baseline/
    postprocess.py assigns every finding the fixed criterion
    BASELINE-GENERIC, which no manifest plants a defect under) scores
    exactly 0.0 criterion-level no matter what it wrote, and something
    other than 0.0 location-level when its locations are actually good."""
    m = manifest(defects=[paragraph_defect("TOY-ACTIVE", 2), paragraph_defect("TOY-HEDGE", 4)])
    baseline_env = envelope(
        skill="baseline-generic",
        artifact_sha256=manifest()["artifact_sha256"],
        findings=[
            finding(finding_id="F-001", criterion="BASELINE-GENERIC", location="paragraph 2"),
            finding(finding_id="F-002", criterion="BASELINE-GENERIC", location="paragraph 1"),  # miss, both modes
        ],
    )

    criterion_result = score.score_artifact(m, baseline_env, TOY_MD)
    assert score.aggregate_recall([criterion_result]).value == 0.0
    assert score.aggregate_precision([criterion_result]).value == 0.0

    location_result = score.score_artifact_location(m, baseline_env, TOY_MD)
    assert location_result.defects_matched == 1  # paragraph 2 hits TOY-ACTIVE; paragraph 1 hits nothing
    assert location_result.claims_matched == 1
    assert score.aggregate_recall([location_result]).numerator == 1
    assert score.aggregate_recall([location_result]).denominator == 2
    assert score.aggregate_precision([location_result]).value == 0.5


def test_score_artifact_location_never_scores_fewer_matches_than_criterion_level() -> None:
    """Location-level match is criterion-level match with one condition
    dropped, so for any envelope its matched-defect and matched-claim
    counts are at least the criterion-level counts, never fewer."""
    m = manifest(defects=[paragraph_defect("TOY-ACTIVE", 2), paragraph_defect("TOY-HEDGE", 4)])
    env = envelope(
        artifact_sha256=manifest()["artifact_sha256"],
        findings=[
            finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2"),  # right both ways
            finding(finding_id="F-002", criterion="TOY-MISC", location="paragraph 4"),  # right location only
            finding(finding_id="F-003", criterion="TOY-MISC", location="paragraph 1"),  # miss both ways
        ],
    )
    criterion_result = score.score_artifact(m, env, TOY_MD)
    location_result = score.score_artifact_location(m, env, TOY_MD)
    assert location_result.defects_matched >= criterion_result.defects_matched
    assert location_result.claims_matched >= criterion_result.claims_matched
    assert location_result.defects_matched == 2
    assert location_result.claims_matched == 2


def test_score_artifact_location_clean_artifact_still_has_no_defects_to_match() -> None:
    """A clean artifact has nothing planted, so ignoring the criterion
    changes nothing: there is no defect at any location for a claim to
    hit, location-level or otherwise."""
    m = manifest(defects=[])
    env = envelope(
        artifact_sha256=manifest()["artifact_sha256"],
        findings=[finding(finding_id="F-001", criterion="TOY-MISC", location="paragraph 1")],
    )
    result = score.score_artifact_location(m, env, TOY_MD)
    assert result.is_clean is True
    assert result.defects_matched == 0
    assert result.claims_matched == 0
    assert score.aggregate_recall([result]).value is None  # excluded from the denominator, not scored a miss
    assert score.aggregate_precision([result]).value == 0.0


# --- 3. End-to-end: build_results carries recall_location/precision_location


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8", newline="\n")


def test_build_results_computes_recall_location_and_precision_location(tmp_path: Path) -> None:
    repo_root = tmp_path
    corpus_dir = repo_root / "bench" / "corpus"
    runs_dir = repo_root / "bench" / "results" / "test-run-set"

    artifact_rel = "bench/corpus/toy/toy-001.md"
    artifact_path = repo_root / artifact_rel
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(TOY_MD, encoding="utf-8", newline="\n")

    m = manifest(
        artifact=artifact_rel,
        artifact_text=TOY_MD,
        defects=[paragraph_defect("TOY-ACTIVE", 2), paragraph_defect("TOY-HEDGE", 4)],
    )
    _write(corpus_dir / "toy" / "toy-001.manifest.json", m)

    # A baseline-shaped run: right locations, one fixed foreign criterion.
    # Criterion-level recall/precision must read 0.0; location-level must
    # not.
    baseline_run = envelope(
        skill="baseline-generic",
        skill_version="1.0.0",
        artifact=artifact_rel,
        artifact_sha256=m["artifact_sha256"],
        rubrics=["BASELINE"],
        findings=[
            finding(finding_id="F-001", criterion="BASELINE-GENERIC", location="paragraph 2"),
            finding(finding_id="F-002", criterion="BASELINE-GENERIC", location="paragraph 4"),
        ],
    )
    _write(runs_dir / "baseline-run.json", baseline_run)

    results = build_results(
        corpus_dir, runs_dir, run_set="test-run-set", generated_at="2026-07-31T00:00:00Z", repo_root=repo_root
    )

    assert len(results["entries"]) == 1
    entry = results["entries"][0]

    assert entry["recall"] == {"value": 0.0, "numerator": 0, "denominator": 2}
    assert entry["precision"] == {"value": 0.0, "numerator": 0, "denominator": 2}

    assert entry["recall_location"] == {"value": 1.0, "numerator": 2, "denominator": 2}
    assert entry["precision_location"] == {"value": 1.0, "numerator": 2, "denominator": 2}


def test_build_results_location_fields_present_and_schema_valid_when_empty(tmp_path: Path) -> None:
    """`build_results` validates its own output against
    `results.schema.json` before returning (bench/metrics/__main__.py);
    an empty run set exercises the schema's `required` list for
    `recall_location` and `precision_location` without needing any
    scored entry, since `build_results` succeeding at all on a populated
    grid is the schema check for the populated case."""
    corpus_dir = tmp_path / "bench" / "corpus"
    runs_dir = tmp_path / "bench" / "results" / "empty-run-set"
    corpus_dir.mkdir(parents=True)
    runs_dir.mkdir(parents=True)

    results = build_results(
        corpus_dir, runs_dir, run_set="empty-run-set", generated_at="2026-07-31T00:00:00Z", repo_root=tmp_path
    )
    assert results["entries"] == []
    assert results["results_version"].startswith("1.")
