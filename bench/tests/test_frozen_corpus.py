"""Integrity tests for bench/corpus/_frozen/: the pre-E67 accessibility snapshot kept so that
already-committed run envelopes bound to the old accessibility bytes stay scorable.

See bench/corpus/_frozen/README.md for why this directory exists, what it holds, and which
committed run sets bind to it. No test here regenerates or edits anything under _frozen/; that
directory's whole point is to never change.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bench.metrics.__main__ import _discover_manifests, _load_envelope, _load_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = REPO_ROOT / "bench" / "corpus"
FROZEN_DIR = CORPUS_DIR / "_frozen"
RESULTS_DIR = REPO_ROOT / "bench" / "results"

FROZEN_MANIFEST_PATHS = sorted(FROZEN_DIR.rglob("*.manifest.json"))

# Every directory under bench/results/ that holds committed run envelopes, by the same "runs*"
# convention bench/variance.py and bench/README.md use. results.json and variance.json live
# beside them and are excluded by name, matching bench.variance.scoring_view.
RUN_SET_DIRS = sorted(p for p in RESULTS_DIR.iterdir() if p.is_dir() and p.name.startswith("runs"))


def _committed_envelope_paths() -> list[Path]:
    paths = []
    for runs_dir in RUN_SET_DIRS:
        for path in sorted(runs_dir.rglob("*.json")):
            if path.name in ("results.json", "variance.json"):
                continue
            paths.append(path)
    return paths


def test_frozen_directory_is_not_empty():
    assert FROZEN_MANIFEST_PATHS, "expected at least one frozen manifest under bench/corpus/_frozen/"


@pytest.mark.parametrize(
    "manifest_path", FROZEN_MANIFEST_PATHS, ids=lambda p: p.relative_to(FROZEN_DIR).as_posix()
)
def test_frozen_manifest_is_schema_valid(manifest_path):
    # _load_manifest both parses and schema-validates; it raises ScoreError (a subclass of
    # Exception) on any violation, which pytest reports as this test's failure.
    _load_manifest(manifest_path)


@pytest.mark.parametrize(
    "manifest_path", FROZEN_MANIFEST_PATHS, ids=lambda p: p.relative_to(FROZEN_DIR).as_posix()
)
def test_frozen_manifest_artifact_hashes_to_its_recorded_sha(manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact_path = REPO_ROOT / manifest["artifact"]
    digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    assert digest == manifest["artifact_sha256"]


@pytest.mark.parametrize(
    "manifest_path", FROZEN_MANIFEST_PATHS, ids=lambda p: p.relative_to(FROZEN_DIR).as_posix()
)
def test_frozen_manifest_artifact_path_is_under_frozen(manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["artifact"].startswith("bench/corpus/_frozen/")


def test_no_frozen_sha_equals_a_live_manifest_sha():
    """bench/metrics and bench/variance both key a by_sha dict on artifact_sha256 alone. A
    collision between a frozen and a live manifest would let one silently win the dict and the
    other vanish from scoring with no error."""
    frozen_shas = {
        json.loads(p.read_text(encoding="utf-8"))["artifact_sha256"] for p in FROZEN_MANIFEST_PATHS
    }
    live_manifest_paths = [
        p for p in CORPUS_DIR.rglob("*.manifest.json") if "_frozen" not in p.relative_to(CORPUS_DIR).parts
    ]
    live_shas = {json.loads(p.read_text(encoding="utf-8"))["artifact_sha256"] for p in live_manifest_paths}
    assert frozen_shas.isdisjoint(live_shas)


def test_every_frozen_manifest_is_bound_by_at_least_one_committed_envelope():
    manifests = _discover_manifests(CORPUS_DIR)
    frozen_shas = {m["artifact_sha256"] for m in manifests if m["artifact"].startswith("bench/corpus/_frozen/")}
    by_sha = {m["artifact_sha256"]: m for m in manifests}

    bound_shas = set()
    for path in _committed_envelope_paths():
        env = _load_envelope(path)
        if env is None:
            continue
        sha = env["run"].get("artifact_sha256")
        if sha in by_sha:
            bound_shas.add(sha)

    unbound = frozen_shas - bound_shas
    assert not unbound, f"frozen manifest sha(s) with no binding committed envelope: {sorted(unbound)}"


def test_every_committed_envelope_binds_to_some_manifest():
    """The orphan guard.

    Scope: every envelope under bench/results/runs*/ (results.json and variance.json excluded,
    matching bench.variance.scoring_view's own exclusions). As of 2026-10-27, a full inventory of
    every committed run-set directory found zero unbound envelopes: every one of them, across
    every run set from p3-2026-07-31 through bench-2026-10-15, resolves to either a live or a
    frozen manifest by artifact_sha256. This test asserts that fact holds, not a looser one. If a
    future committed run set is ever deliberately left unscorable (a probe misplaced outside
    bench/results/probes/, for instance), narrow this assertion's scope explicitly here and say
    why, rather than widening it silently.
    """
    manifests = _discover_manifests(CORPUS_DIR)
    by_sha = {m["artifact_sha256"]: m for m in manifests}

    unbound = []
    for path in _committed_envelope_paths():
        env = _load_envelope(path)
        if env is None:
            continue
        sha = env["run"].get("artifact_sha256")
        if sha not in by_sha:
            unbound.append(str(path.relative_to(REPO_ROOT)))

    assert unbound == []
