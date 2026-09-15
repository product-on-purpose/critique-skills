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

    assert results["results_version"] == "1.2.0"
    assert results["run_set"] == "test-run-set"
    # Three entries per cell since 1.2.0: one per lane. The overall lane is the pre-1.2.0 figure.
    assert len(results["entries"]) == 3
    assert sorted(e["lane"] for e in results["entries"]) == ["judged", "overall", "scripted"]
    assert {e["run_set"] for e in results["entries"]} == {"test-run-set"}

    entry = next(e for e in results["entries"] if e["lane"] == "overall")
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


def test_lanes_partition_the_overall_claim_set() -> None:
    """judged + scripted claims must equal overall claims, on the committed file.

    This is the invariant that makes a lane column trustworthy rather than merely present. If a
    finding carried no lane, or carried one outside the two, it would be scored into `overall` and
    into neither of the others, and the three entries would quietly stop describing the same run.
    Ground-truth denominators (recall) are a property of the corpus and must instead be IDENTICAL
    across lanes; a lane filter that changed them would mean the filter had reached the manifest.
    """
    import json
    from pathlib import Path

    results_path = Path(__file__).resolve().parents[2] / "results" / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    by_cell: dict[tuple[str, ...], dict[str, dict]] = {}
    for e in results["entries"]:
        by_cell.setdefault((e["skill"], e["skill_version"], e["model"], e["domain"]), {})[e["lane"]] = e

    assert by_cell, "committed results.json carries no entries"
    for cell, lanes in by_cell.items():
        assert set(lanes) == {"overall", "judged", "scripted"}, (cell, sorted(lanes))
        overall, judged, scripted = lanes["overall"], lanes["judged"], lanes["scripted"]
        assert (
            judged["precision"]["denominator"] + scripted["precision"]["denominator"]
            == overall["precision"]["denominator"]
        ), (cell, "claims do not partition")
        assert (
            overall["recall"]["denominator"]
            == judged["recall"]["denominator"]
            == scripted["recall"]["denominator"]
        ), (cell, "ground-truth denominator moved with the lane filter")


def test_every_committed_entry_names_its_run_set() -> None:
    """The defect per-entry run_set exists to fix: a committed file may concatenate run sets, and
    before 1.2.0 it carried one invented top-level identifier for the pair."""
    import json
    from pathlib import Path

    results_path = Path(__file__).resolve().parents[2] / "results" / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    run_sets = {e["run_set"] for e in results["entries"]}
    assert all(e.get("run_set") for e in results["entries"]), "an entry does not name its run set"
    assert len(run_sets) > 1, (
        "the committed file is expected to hold more than one run set; if it no longer does, the "
        "top-level run_set is sufficient again and this test should be revisited"
    )
