"""Tests for bench.generator.verify: the regenerate-and-diff checker CI's
corpus job runs."""

from __future__ import annotations

from bench.generator.build import build
from bench.generator.domains import toy
from bench.generator.verify import verify_corpus


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
