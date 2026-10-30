"""Regenerates the corpus into a scratch directory and diffs it byte for
byte against a committed corpus tree, and separately checks the corpus
composition AC-3 (S-03's bench harness spec) requires.

This is what CI's corpus job runs to prove AC-1: running the generator
twice with the same seeds produces byte-identical `bench/corpus/` trees.
Also reachable as `python -m bench.generator verify --corpus bench/corpus`.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from bench.generator.api import Domain
from bench.generator.build import build
from bench.generator.registry import load_domains

# AC-3 (corpus composition: >=20 artifacts total, >=3 per core domain, >=1
# clean artifact per core domain) was written against S-03's own six launch
# domains. S-05 (skills slate spec, line 46) calls three of those "core" and
# three "stretch". But S-05's spec line 71 holds every skill's contributed
# domain, core or stretch, to the identical floor: >=3 artifacts, >=1 clean.
# P2-report.md's CORPUS row already noted that the flat bar AC-3 states is
# met by all six, not only the three core ones. `forms` joined later (ADR
# 0036, ADR 0037) under that same per-skill floor. So this check applies the
# per-domain floor to every registered generator domain except `toy`, since
# each registered domain backs a shipped skill (toy is the one exception: a
# harness fixture, bench/generator/README.md's worked example, never a
# component library.json lists).
NON_SKILL_DOMAINS = frozenset({"toy"})

MIN_TOTAL_ARTIFACTS = 20
MIN_ARTIFACTS_PER_DOMAIN = 3
MIN_CLEAN_ARTIFACTS_PER_DOMAIN = 1


@dataclass
class VerifyResult:
    missing: list[str] = field(default_factory=list)  # in the committed corpus, not regenerated
    extra: list[str] = field(default_factory=list)  # regenerated, not in the committed corpus
    mismatched: list[str] = field(default_factory=list)  # present both places, different bytes
    matched: list[str] = field(default_factory=list)  # present both places, identical bytes

    @property
    def ok(self) -> bool:
        return not (self.missing or self.extra or self.mismatched)

    def report(self) -> str:
        if self.ok:
            return f"verify OK: {len(self.matched)} file(s) byte-identical"
        lines = [
            f"verify FAILED: {len(self.matched)} matched, "
            f"{len(self.mismatched)} mismatched, {len(self.missing)} missing, "
            f"{len(self.extra)} extra"
        ]
        for rel in self.mismatched:
            lines.append(f"  mismatched: {rel}")
        for rel in self.missing:
            lines.append(f"  missing (committed but not regenerated): {rel}")
        for rel in self.extra:
            lines.append(f"  extra (regenerated but not committed): {rel}")
        return "\n".join(lines)


def _corpus_files(corpus_dir: Path, *, exclude_frozen: bool = False) -> dict[str, Path]:
    """Every regular file under corpus_dir, keyed by its path relative to
    corpus_dir, POSIX-separated so the comparison is stable across OSes.

    `exclude_frozen` leaves out anything under a top-level `_frozen/`
    directory. Frozen copies (`bench/corpus/_frozen/README.md`) are
    deliberately never regenerated, so they would otherwise report as
    "missing" on every run: present in the committed corpus, absent from
    the scratch directory this module builds fresh each time. Used only
    for the committed side of the comparison; a scratch build never has
    a `_frozen/` directory to begin with."""
    files: dict[str, Path] = {}
    if not corpus_dir.exists():
        return files
    for path in corpus_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(corpus_dir).as_posix()
        if exclude_frozen and (rel == "_frozen" or rel.startswith("_frozen/")):
            continue
        files[rel] = path
    return files


def verify_corpus(
    corpus_dir: Path,
    domains: tuple[Domain, ...] | None = None,
) -> VerifyResult:
    """Regenerate every recipe of `domains` (default: every registered
    domain) into a scratch directory and diff the result byte for byte
    against `corpus_dir`.

    `corpus_dir` is expected to hold what `bench/corpus/` holds in a real
    checkout: `<domain>/<recipe>.<ext>`, `<domain>/<recipe>.manifest.json`,
    and `corpus.lock.json`.
    """
    if domains is None:
        domains = load_domains()

    with tempfile.TemporaryDirectory(prefix="bench-verify-") as tmp:
        scratch_root = Path(tmp)
        build(scratch_root, domains)
        regenerated_files = _corpus_files(scratch_root)
        committed_files = _corpus_files(corpus_dir, exclude_frozen=True)

        result = VerifyResult()
        for rel in sorted(set(regenerated_files) | set(committed_files)):
            in_regenerated = rel in regenerated_files
            in_committed = rel in committed_files
            if in_regenerated and not in_committed:
                result.extra.append(rel)
            elif in_committed and not in_regenerated:
                result.missing.append(rel)
            elif regenerated_files[rel].read_bytes() != committed_files[rel].read_bytes():
                result.mismatched.append(rel)
            else:
                result.matched.append(rel)
        return result


@dataclass
class CompositionResult:
    counts: dict[str, int] = field(default_factory=dict)  # domain name -> artifact count
    clean_counts: dict[str, int] = field(default_factory=dict)  # domain name -> clean count
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def report(self) -> str:
        if self.ok:
            total = sum(self.counts.values())
            return (
                f"composition OK: {total} artifact(s) across {len(self.counts)} "
                "domain(s), AC-3's thresholds met"
            )
        lines = ["composition FAILED (AC-3, corpus composition):"]
        for problem in self.problems:
            lines.append(f"  {problem}")
        return "\n".join(lines)


def verify_composition(
    corpus_dir: Path,
    domains: tuple[Domain, ...] | None = None,
) -> CompositionResult:
    """Checks AC-3's corpus-composition thresholds directly against the
    manifests already on disk under `corpus_dir`. No regeneration here.

    AC-3's "every artifact with a schema-valid manifest" clause is covered
    transitively by `verify_corpus`. That call raises `GenerationError`
    before writing any manifest that fails schema validation (`pipeline.
    _manifest_schema_problems`, raised at `pipeline.py:381`), so a schema-
    invalid manifest can never reach the committed corpus this check reads.

    `domains` defaults to every registered domain; see the module docstring
    for which of those count as a "core domain" here, and why.
    """
    if domains is None:
        domains = load_domains()
    domain_names = tuple(d.name for d in domains if d.name not in NON_SKILL_DOMAINS)

    counts: dict[str, int] = {}
    clean_counts: dict[str, int] = {}
    problems: list[str] = []

    for name in domain_names:
        domain_dir = corpus_dir / name
        manifest_paths = sorted(domain_dir.glob("*.manifest.json")) if domain_dir.is_dir() else []
        counts[name] = len(manifest_paths)
        clean = 0
        for manifest_path in manifest_paths:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            # bench/README.md's invariants table: an empty `defects` array asserts
            # "clean"; a missing key asserts only "not recorded", so it does not count.
            if manifest.get("defects") == []:
                clean += 1
        clean_counts[name] = clean

        if counts[name] < MIN_ARTIFACTS_PER_DOMAIN:
            problems.append(
                f"{name}: {counts[name]} artifact(s), AC-3 requires "
                f">= {MIN_ARTIFACTS_PER_DOMAIN} per domain"
            )
        if clean_counts[name] < MIN_CLEAN_ARTIFACTS_PER_DOMAIN:
            problems.append(
                f"{name}: {clean_counts[name]} clean artifact(s), AC-3 requires "
                f">= {MIN_CLEAN_ARTIFACTS_PER_DOMAIN} clean per domain"
            )

    total = sum(counts.values())
    if total < MIN_TOTAL_ARTIFACTS:
        problems.append(f"corpus: {total} artifact(s) total, AC-3 requires >= {MIN_TOTAL_ARTIFACTS}")

    return CompositionResult(counts=counts, clean_counts=clean_counts, problems=problems)
