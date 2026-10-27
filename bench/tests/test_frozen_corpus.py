"""Integrity tests for bench/corpus/_frozen/: the pre-E67 accessibility snapshot kept so that
already-committed run envelopes bound to the old accessibility bytes stay scorable.

See bench/corpus/_frozen/README.md for why this directory exists, what it holds, and which
committed run sets bind to it. No test here regenerates or edits anything under _frozen/; that
directory's whole point is to never change. `FROZEN_FILE_SHA256` pins each frozen manifest's and
each frozen html's own file hash to a literal, on top of `test_frozen_manifest_artifact_hashes_to_
its_recorded_sha`'s check that a manifest's `artifact_sha256` field matches its artifact's bytes: a
silent edit to a manifest's description or severity, or to an html file's content, changes neither
`artifact_sha256` nor `artifact` and so passes every other test in this file, but it changes the
file's own hash and fails here.
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
FROZEN_HTML_PATHS = sorted(FROZEN_DIR.rglob("*.html"))

# Literal sha256 of every frozen manifest and every frozen html, computed once against the
# committed bytes and pinned here so a silent edit to either (a changed description, a changed
# severity, a reworded defect) fails this test even though it may leave `artifact_sha256` and
# `artifact` untouched. Recomputing these after a deliberate change to a frozen file is a
# contradiction in terms: see bench/corpus/_frozen/README.md, "The rule".
FROZEN_FILE_SHA256 = {
    "v1/accessibility/accessibility-001.html": "f620e43c2035d9380934dbe1b09dba438bb38bc1fb7f1feeb58010af44eaf176",
    "v1/accessibility/accessibility-001.manifest.json": "163a693f708bc001b14e0d29dfdfabadccbce627d9fd868c539bf08130db2c82",
    "v1/accessibility/accessibility-002.html": "b49ce74681df60732a6ef3b5309ce82264ad1b6ad48c6fa8b85989f2c712f113",
    "v1/accessibility/accessibility-002.manifest.json": "869aee89c5b7b7bb3ff093628e1237c6870cc6dbc34967a7c9c3f734cb22e57b",
    "v1/accessibility/accessibility-003.html": "69ff628078a107c11bd403359666e3fafdba2d4ab204fdec80881f7db5374db6",
    "v1/accessibility/accessibility-003.manifest.json": "8721b44985432b8caad1dd959b1ce9449b81dd812c3b53b894a0e157e1b1324e",
    "v1/accessibility/accessibility-004.html": "393fe58fac52d6953cd372944cd352ef9181df5c42ae778bd6d17214acb080c7",
    "v1/accessibility/accessibility-004.manifest.json": "a5ab580752f1900d52cbf330c1511a6c49e8ac2204afa069a3463e9a0545c07a",
}

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


def test_frozen_file_pins_cover_exactly_the_discovered_manifests_and_htmls():
    """Guards FROZEN_FILE_SHA256 itself: an added or removed frozen manifest or html, which
    bench/corpus/_frozen/README.md's "The rule" says should never happen, fails here rather
    than silently being skipped by the parametrized test below."""
    discovered = {
        p.relative_to(FROZEN_DIR).as_posix() for p in (*FROZEN_MANIFEST_PATHS, *FROZEN_HTML_PATHS)
    }
    assert discovered == set(FROZEN_FILE_SHA256)


@pytest.mark.parametrize(
    "rel_path", sorted(FROZEN_FILE_SHA256), ids=lambda p: p
)
def test_frozen_file_hash_matches_its_pinned_literal(rel_path):
    """Pins each frozen manifest's and each frozen html's own file hash, so a silent edit to a
    manifest's description or severity, or to an html file's content, fails here even when it
    leaves `artifact_sha256` and `artifact` untouched (see the module docstring)."""
    digest = hashlib.sha256((FROZEN_DIR / rel_path).read_bytes()).hexdigest()
    assert digest == FROZEN_FILE_SHA256[rel_path]


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
