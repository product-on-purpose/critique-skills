"""End-to-end test of `python -m bench.metrics score`'s library entry
point, `build_results`: writes synthetic manifests and envelopes to a
temporary directory tree and confirms the assembled results.json is
schema-valid and numerically correct. Doubles as the "sample metric
computation on synthetic data" this module's deliverable report points
to.
"""

from __future__ import annotations

import json
from pathlib import Path

from bench.metrics.__main__ import build_results
from bench.metrics.tests.fixtures import TOY_MD, envelope, finding, manifest, paragraph_defect


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8", newline="\n")


def test_build_results_end_to_end(tmp_path: Path) -> None:
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

    # A "perfect" run: both defects found, nothing extra.
    good = envelope(
        artifact=artifact_rel,
        artifact_sha256=m["artifact_sha256"],
        findings=[
            finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2"),
            finding(finding_id="F-002", criterion="TOY-HEDGE", location="paragraph 4"),
        ],
    )
    _write(runs_dir / "run-1.json", good)

    # A second run of the same skill, same artifact, that misses one and
    # adds an extra unplanted claim: exercises consistency (k=2 here) and
    # drags precision down in the aggregate.
    noisier = envelope(
        artifact=artifact_rel,
        artifact_sha256=m["artifact_sha256"],
        findings=[
            finding(finding_id="F-001", criterion="TOY-ACTIVE", location="paragraph 2"),
            finding(finding_id="F-002", criterion="TOY-HEDGE", location="paragraph 1"),
        ],
    )
    _write(runs_dir / "run-2.json", noisier)

    results = build_results(
        corpus_dir, runs_dir, run_set="test-run-set", generated_at="2026-07-31T00:00:00Z", repo_root=repo_root
    )

    assert results["results_version"] == "1.1.0"
    assert results["run_set"] == "test-run-set"
    assert len(results["entries"]) == 1

    entry = results["entries"][0]
    assert entry["skill"] == "critique-toy"
    assert entry["domain"] == "toy"
    assert entry["artifact_type"] == "markdown-prose"
    assert entry["artifacts_scored"] == 2  # two envelopes scored against the one artifact

    # Pooled recall: run 1 finds 2/2, run 2 finds 1/2 -> 3/4.
    assert entry["recall"]["numerator"] == 3
    assert entry["recall"]["denominator"] == 4
    assert entry["recall"]["value"] == 0.75

    # Pooled precision: run 1 both claims match (2/2), run 2 one claim
    # matches and one does not (1/2) -> 3/4.
    assert entry["precision"]["numerator"] == 3
    assert entry["precision"]["denominator"] == 4
    assert entry["precision"]["value"] == 0.75

    assert entry["clean_fp_rate"] == {"value": None, "numerator": 0, "denominator": 0}

    # Consistency over the k=2 runs: one shared claim (TOY-ACTIVE, para 2)
    # out of three distinct claims total -> J = 1 / (2 + 2 - 1) = 1/3.
    assert entry["consistency"]["artifacts_with_pairs"] == 1
    assert entry["consistency"]["total_pairs"] == 1
    assert entry["consistency"]["value"] == round(1 / 3, 3)


def test_build_results_is_empty_but_valid_when_nothing_matches(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "bench" / "corpus"
    runs_dir = tmp_path / "bench" / "results" / "empty-run-set"
    corpus_dir.mkdir(parents=True)
    runs_dir.mkdir(parents=True)

    results = build_results(
        corpus_dir, runs_dir, run_set="empty-run-set", generated_at="2026-07-31T00:00:00Z", repo_root=tmp_path
    )
    assert results["entries"] == []
