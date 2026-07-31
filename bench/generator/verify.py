"""Regenerates the corpus into a scratch directory and diffs it byte for
byte against a committed corpus tree.

This is what CI's corpus job runs to prove AC-1: running the generator
twice with the same seeds produces byte-identical `bench/corpus/` trees.
Also reachable as `python -m bench.generator verify --corpus bench/corpus`.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from bench.generator.api import Domain
from bench.generator.build import build
from bench.generator.registry import load_domains


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


def _corpus_files(corpus_dir: Path) -> dict[str, Path]:
    """Every regular file under corpus_dir, keyed by its path relative to
    corpus_dir, POSIX-separated so the comparison is stable across OSes."""
    files: dict[str, Path] = {}
    if not corpus_dir.exists():
        return files
    for path in corpus_dir.rglob("*"):
        if path.is_file():
            files[path.relative_to(corpus_dir).as_posix()] = path
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
        committed_files = _corpus_files(corpus_dir)

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
