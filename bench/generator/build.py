"""Writes generated artifacts and manifests to disk, and the
`corpus.lock.json` root manifest.

Byte rules per `bench/generator/README.md`, "Output bytes": UTF-8, no BOM,
LF line endings, exactly one trailing newline, NFC-normalized. Every write
here is `Path.write_bytes`, which writes the given bytes exactly with no
platform-dependent newline translation, satisfying the rule by
construction rather than by an `open(..., newline="\\n")` convention that
would be easy to forget at one call site.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from bench.generator.api import Domain
from bench.generator.pipeline import CORPUS_ROOT, GeneratedArtifact, generate
from bench.generator.rng import CORPUS_SEED, root_seed

# Matches library.json's version for this release. Recorded in
# corpus.lock.json so a reader can tell which generator produced a corpus
# without recomputing every hash first.
GENERATOR_VERSION = "0.1.0"

CORPUS_LOCK_FILENAME = "corpus.lock.json"


@dataclass(frozen=True, slots=True)
class BuildResult:
    generated: tuple[GeneratedArtifact, ...]
    lock_path: Path
    lock_bytes: bytes


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _within_corpus(repo_relative_path: str) -> PurePosixPath:
    """Strip the `bench/corpus/` prefix a manifest's `artifact` or a
    generated manifest's own path always carries, leaving the part
    relative to the corpus root itself: `bench/corpus/toy/toy-001.md`
    becomes `toy/toy-001.md`."""
    return PurePosixPath(repo_relative_path).relative_to(CORPUS_ROOT)


def generate_domain(domain: Domain) -> tuple[GeneratedArtifact, ...]:
    """Generate every recipe of one domain, in the domain's own declared
    recipe order. Raises pipeline.GenerationError on the first recipe that
    fails verification."""
    return tuple(generate(domain, recipe) for recipe in domain.recipes)


def _corpus_lock(out_dir: Path, generated: tuple[GeneratedArtifact, ...]) -> dict:
    manifests = {
        item.manifest_path: hashlib.sha256(item.manifest_bytes).hexdigest()
        for item in generated
    }
    return {
        "corpus_seed": CORPUS_SEED,
        "root_seed": root_seed().hex(),
        "generator_version": GENERATOR_VERSION,
        "manifest_count": len(generated),
        "manifest_sha256": dict(sorted(manifests.items())),
    }


def build(
    out_dir: Path,
    domains: tuple[Domain, ...],
    *,
    write_lock: bool = True,
) -> BuildResult:
    """Generate every recipe of every given domain and write it under
    `out_dir`, which stands in for `bench/corpus/` itself: an artifact
    whose manifest records path `bench/corpus/toy/toy-001.md` is written to
    `out_dir/toy/toy-001.md`. This matches the frozen CLI command,
    `python -m bench.generator build --out bench/corpus`, where `--out`
    names the corpus directory directly, and lets `verify()` point `out_dir`
    at a scratch directory and compare it against a real `bench/corpus`
    checkout with no path translation on either side.
    """
    generated: list[GeneratedArtifact] = []
    for domain in domains:
        for item in generate_domain(domain):
            _write_bytes(out_dir / _within_corpus(item.artifact_path), item.artifact_bytes)
            _write_bytes(out_dir / _within_corpus(item.manifest_path), item.manifest_bytes)
            generated.append(item)

    lock = _corpus_lock(out_dir, tuple(generated))
    lock_text = unicodedata.normalize(
        "NFC", json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    lock_bytes = lock_text.encode("utf-8")
    lock_path = out_dir / CORPUS_LOCK_FILENAME
    if write_lock:
        _write_bytes(lock_path, lock_bytes)

    return BuildResult(generated=tuple(generated), lock_path=lock_path, lock_bytes=lock_bytes)
