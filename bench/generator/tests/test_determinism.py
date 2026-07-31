"""The determinism proof S-03 AC-1 requires: running the generator twice
with the same seeds produces byte-identical artifacts and manifests, with
no dependence on process-level nondeterminism such as PYTHONHASHSEED.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from bench.generator.build import build
from bench.generator.domains import toy
from bench.generator.pipeline import generate
from bench.generator.registry import load_domains

REPO_ROOT = Path(__file__).resolve().parents[3]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize("recipe_id", [r.id for r in toy.DOMAIN.recipes])
def test_generate_twice_in_process_is_byte_identical(recipe_id):
    recipe = next(r for r in toy.DOMAIN.recipes if r.id == recipe_id)
    first = generate(toy.DOMAIN, recipe)
    second = generate(toy.DOMAIN, recipe)
    assert first.artifact_bytes == second.artifact_bytes
    assert first.manifest_bytes == second.manifest_bytes
    assert first.manifest == second.manifest


def test_generate_twice_is_byte_identical_across_fresh_rng_state():
    """A regression guard against any hidden mutable module-level state:
    generating toy-002 (which plants a structural injector) before and
    after generating every other recipe must not perturb its bytes."""
    recipe_002 = next(r for r in toy.DOMAIN.recipes if r.id == "toy-002")
    before = generate(toy.DOMAIN, recipe_002)
    for recipe in toy.DOMAIN.recipes:
        generate(toy.DOMAIN, recipe)
    after = generate(toy.DOMAIN, recipe_002)
    assert before.artifact_bytes == after.artifact_bytes
    assert before.manifest_bytes == after.manifest_bytes


def test_build_twice_into_separate_directories_is_byte_identical(tmp_path):
    domains = load_domains()
    out_a = tmp_path / "run-a"
    out_b = tmp_path / "run-b"
    result_a = build(out_a, domains)
    result_b = build(out_b, domains)

    files_a = sorted(p.relative_to(out_a).as_posix() for p in out_a.rglob("*") if p.is_file())
    files_b = sorted(p.relative_to(out_b).as_posix() for p in out_b.rglob("*") if p.is_file())
    assert files_a == files_b
    assert files_a  # sanity: something was actually generated

    for rel in files_a:
        assert (out_a / rel).read_bytes() == (out_b / rel).read_bytes(), rel

    assert result_a.lock_bytes == result_b.lock_bytes


def test_build_output_matches_generate_output_directly(tmp_path):
    """The files build() writes must be byte-identical to what generate()
    computes in memory: build() must not silently transform anything on
    the way to disk."""
    recipe = next(r for r in toy.DOMAIN.recipes if r.id == "toy-001")
    in_memory = generate(toy.DOMAIN, recipe)
    build(tmp_path, (toy.DOMAIN,))
    on_disk_artifact = (tmp_path / "toy" / "toy-001.md").read_bytes()
    on_disk_manifest = (tmp_path / "toy" / "toy-001.manifest.json").read_bytes()
    assert on_disk_artifact == in_memory.artifact_bytes
    assert on_disk_manifest == in_memory.manifest_bytes


def test_determinism_is_independent_of_pythonhashseed(tmp_path):
    """CI's corpus job runs the generator under two different
    PYTHONHASHSEED values and compares hashes: identical output proves no
    set or dict iteration order leaked into the bytes. Reproduced here as
    a fast, self-contained check against the toy corpus."""

    def build_with_hashseed(hashseed: str) -> Path:
        out_dir = tmp_path / f"hashseed-{hashseed}"
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = hashseed
        subprocess.run(
            [sys.executable, "-m", "bench.generator", "build", "--out", str(out_dir)],
            cwd=REPO_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        return out_dir

    out_0 = build_with_hashseed("0")
    out_12345 = build_with_hashseed("12345")

    files_0 = sorted(p.relative_to(out_0).as_posix() for p in out_0.rglob("*") if p.is_file())
    files_12345 = sorted(
        p.relative_to(out_12345).as_posix() for p in out_12345.rglob("*") if p.is_file()
    )
    assert files_0 == files_12345
    assert files_0

    mismatches = [
        rel
        for rel in files_0
        if _sha256((out_0 / rel).read_bytes()) != _sha256((out_12345 / rel).read_bytes())
    ]
    assert mismatches == []
