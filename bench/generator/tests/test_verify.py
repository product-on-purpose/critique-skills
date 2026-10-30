"""Tests for bench.generator.verify: the regenerate-and-diff checker, and
the corpus-composition check (AC-3), CI's corpus job runs."""

from __future__ import annotations

import json
from pathlib import Path

from bench.generator.build import build
from bench.generator.domains import toy
from bench.generator.verify import verify_composition, verify_corpus

REPO_ROOT = Path(__file__).resolve().parents[3]
CORPUS_DIR = REPO_ROOT / "bench" / "corpus"


class _FakeDomain:
    """A minimal stand-in for a registered Domain: verify_composition only
    reads `.name` off whatever `domains` it is given."""

    def __init__(self, name: str) -> None:
        self.name = name


def _write_manifest(domain_dir: Path, recipe_id: str, defects: list) -> None:
    domain_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "artifact": f"{domain_dir.name}/{recipe_id}.md",
        "defects": defects,
    }
    (domain_dir / f"{recipe_id}.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_verify_ok_against_freshly_built_corpus(tmp_path):
    build(tmp_path, (toy.DOMAIN,))
    result = verify_corpus(tmp_path, domains=(toy.DOMAIN,))
    assert result.ok
    assert result.mismatched == []
    assert result.missing == []
    assert result.extra == []
    assert result.matched  # something was actually compared


def test_verify_detects_a_mutated_byte(tmp_path):
    build(tmp_path, (toy.DOMAIN,))
    target = tmp_path / "toy" / "toy-001.md"
    original = target.read_bytes()
    target.write_bytes(original.replace(b"the", b"THE", 1))
    result = verify_corpus(tmp_path, domains=(toy.DOMAIN,))
    assert not result.ok
    assert "toy/toy-001.md" in result.mismatched


def test_verify_flags_a_file_the_committed_corpus_dropped_as_extra(tmp_path):
    """Deleting a file from the committed side after building it: the
    regenerated side still produces it, so relative to the committed
    corpus it is reported as "extra" (regenerated, not committed)."""
    build(tmp_path, (toy.DOMAIN,))
    (tmp_path / "toy" / "toy-001.manifest.json").unlink()
    result = verify_corpus(tmp_path, domains=(toy.DOMAIN,))
    assert not result.ok
    assert "toy/toy-001.manifest.json" in result.extra


def test_verify_flags_a_stray_committed_file_as_missing(tmp_path):
    """A file present in the committed corpus that no recipe produces:
    the regenerated side never writes it, so it is reported as "missing"
    (committed, not regenerated)."""
    build(tmp_path, (toy.DOMAIN,))
    (tmp_path / "toy" / "not-generated.md").write_bytes(b"stray file\n")
    result = verify_corpus(tmp_path, domains=(toy.DOMAIN,))
    assert not result.ok
    assert "toy/not-generated.md" in result.missing


def test_verify_against_nonexistent_corpus_directory_reports_everything_missing(tmp_path):
    empty = tmp_path / "does-not-exist"
    result = verify_corpus(empty, domains=(toy.DOMAIN,))
    assert not result.ok
    assert result.missing == []
    assert result.extra  # everything regenerated counts as "extra" vs nothing committed


def test_verify_excludes_a_frozen_file_from_missing_and_extra(tmp_path):
    """`bench/corpus/_frozen/` holds byte-identical copies the generator
    deliberately never regenerates (see `bench/corpus/_frozen/README.md`).
    A file there must be neither "missing" (the scratch build never
    produces it) nor "extra" (it is not regenerated, so it can never
    appear on that side either)."""
    build(tmp_path, (toy.DOMAIN,))
    frozen_dir = tmp_path / "_frozen" / "v1" / "toy"
    frozen_dir.mkdir(parents=True)
    (frozen_dir / "toy-001.md").write_bytes(b"frozen copy\n")
    result = verify_corpus(tmp_path, domains=(toy.DOMAIN,))
    assert result.ok
    assert "_frozen/v1/toy/toy-001.md" not in result.missing
    assert "_frozen/v1/toy/toy-001.md" not in result.extra
    assert "_frozen/v1/toy/toy-001.md" not in result.matched


def test_report_string_mentions_every_kind_of_mismatch(tmp_path):
    build(tmp_path, (toy.DOMAIN,))
    (tmp_path / "toy" / "toy-001.manifest.json").unlink()
    (tmp_path / "toy" / "not-generated.md").write_bytes(b"stray\n")
    (tmp_path / "toy" / "toy-002.md").write_bytes(b"mutated\n")
    result = verify_corpus(tmp_path, domains=(toy.DOMAIN,))
    report = result.report()
    assert "missing" in report
    assert "extra" in report
    assert "mismatched" in report


# --------------------------------------------------------------------------
# verify_composition: AC-3 (corpus composition thresholds)
# --------------------------------------------------------------------------


def test_verify_composition_passes_against_the_committed_corpus():
    """The real, committed `bench/corpus/`: 7 skill domains, each with at
    least 3 artifacts and at least 1 clean one, 28 artifacts total. This is
    the check that closes S-03 AC-3 against the live corpus."""
    result = verify_composition(CORPUS_DIR)
    assert result.ok, result.report()
    assert sum(result.counts.values()) >= 20
    assert all(count >= 1 for count in result.clean_counts.values())


def _clean_corpus(tmp_path: Path, domain_names: tuple[str, ...], per_domain: int) -> None:
    """Writes `per_domain` manifests under each of `domain_names`, the
    first per domain clean (`defects: []`), the rest carrying one defect."""
    for name in domain_names:
        domain_dir = tmp_path / name
        for i in range(per_domain):
            defects = [] if i == 0 else [{"criterion": "X-1", "description": "d", "location": {}}]
            _write_manifest(domain_dir, f"{name}-{i + 1:03d}", defects)


def test_verify_composition_passes_a_corpus_that_clears_every_threshold(tmp_path):
    names = ("d1", "d2", "d3", "d4", "d5", "d6", "d7")  # 7 * 3 = 21 >= MIN_TOTAL_ARTIFACTS
    _clean_corpus(tmp_path, names, per_domain=3)
    domains = tuple(_FakeDomain(name) for name in names)
    result = verify_composition(tmp_path, domains=domains)
    assert result.ok, result.report()


def test_verify_composition_excludes_toy_even_when_toy_is_thin(tmp_path):
    names = ("d1", "d2", "d3", "d4", "d5", "d6", "d7")
    _clean_corpus(tmp_path, names, per_domain=3)
    _write_manifest(tmp_path / "toy", "toy-001", [])  # one artifact: below the per-domain floor
    domains = tuple(_FakeDomain(name) for name in names + ("toy",))
    result = verify_composition(tmp_path, domains=domains)
    assert result.ok, result.report()
    assert "toy" not in result.counts


def test_verify_composition_flags_a_domain_under_the_per_domain_floor(tmp_path):
    names = ("d1", "d2", "d3", "d4", "d5", "d6", "d7")
    _clean_corpus(tmp_path, names, per_domain=3)
    # Thin one domain down to 2 artifacts by removing its third manifest.
    (tmp_path / "d7" / "d7-003.manifest.json").unlink()
    domains = tuple(_FakeDomain(name) for name in names)
    result = verify_composition(tmp_path, domains=domains)
    assert not result.ok
    assert any("d7" in p and "2 artifact" in p for p in result.problems)


def test_verify_composition_flags_a_domain_missing_its_clean_artifact(tmp_path):
    names = ("d1", "d2", "d3", "d4", "d5", "d6", "d7")
    _clean_corpus(tmp_path, names, per_domain=3)
    # Replace d2's clean manifest with a defective one: 3 artifacts, 0 clean.
    (tmp_path / "d2" / "d2-001.manifest.json").unlink()
    _write_manifest(tmp_path / "d2", "d2-001", [{"criterion": "X-1", "description": "d", "location": {}}])
    domains = tuple(_FakeDomain(name) for name in names)
    result = verify_composition(tmp_path, domains=domains)
    assert not result.ok
    assert any("d2" in p and "clean" in p for p in result.problems)


def test_verify_composition_flags_the_total_even_when_every_domain_clears_its_own_floor(tmp_path):
    names = ("d1", "d2", "d3", "d4", "d5", "d6")  # 6 * 3 = 18 < MIN_TOTAL_ARTIFACTS
    _clean_corpus(tmp_path, names, per_domain=3)
    domains = tuple(_FakeDomain(name) for name in names)
    result = verify_composition(tmp_path, domains=domains)
    assert not result.ok
    assert any("18 artifact" in p for p in result.problems)


def test_verify_composition_report_string_distinguishes_ok_from_failed(tmp_path):
    names = ("d1", "d2", "d3", "d4", "d5", "d6", "d7")
    _clean_corpus(tmp_path, names, per_domain=3)
    domains = tuple(_FakeDomain(name) for name in names)
    ok_result = verify_composition(tmp_path, domains=domains)
    assert "OK" in ok_result.report()

    (tmp_path / "d1" / "d1-003.manifest.json").unlink()
    failing_result = verify_composition(tmp_path, domains=domains)
    assert "FAILED" in failing_result.report()
    assert "d1" in failing_result.report()
