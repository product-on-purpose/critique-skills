"""Tests for bench.generator.leak: the leak check itself, unit-tested
against synthetic text, plus a scan of the freshly built toy corpus."""

from __future__ import annotations

from bench.generator import leak
from bench.generator.build import build
from bench.generator.domains import toy


def test_description_leak_detects_a_verbatim_quote():
    artifact = "The quick brown fox jumps over the lazy dog in the yard."
    description = "the quick brown fox jumps over the lazy"
    problems = leak.check_description_leak(artifact, "TOY-ACTIVE", description)
    assert problems


def test_description_leak_ignores_unrelated_text():
    artifact = "The quick brown fox jumps over the lazy dog in the yard."
    description = "One sentence recast into passive voice with the acting party deleted."
    problems = leak.check_description_leak(artifact, "TOY-ACTIVE", description)
    assert problems == []


def test_description_leak_is_normalized_case_and_punctuation_insensitive():
    artifact = "The Quick, Brown fox jumps over the LAZY dog!"
    description = "the quick brown fox jumps over the lazy"
    problems = leak.check_description_leak(artifact, "TOY-ACTIVE", description)
    assert problems


def test_description_leak_needs_a_full_shingle_run():
    """Five shared tokens do not leak; six do. Guards the exact SHINGLE_SIZE
    boundary rather than a looser substring check."""
    artifact = "alpha beta gamma delta epsilon zeta eta theta"
    five_shared = "alpha beta gamma delta epsilon"
    six_shared = "alpha beta gamma delta epsilon zeta"
    assert leak.check_description_leak(artifact, "X-ONE", five_shared) == []
    assert leak.check_description_leak(artifact, "X-ONE", six_shared) != []


def test_criterion_id_leak_detects_presence():
    assert leak.check_criterion_id_leak("This mentions TOY-ACTIVE directly.", "TOY-ACTIVE")
    assert leak.check_criterion_id_leak("This mentions toy-active directly.", "TOY-ACTIVE")
    assert leak.check_criterion_id_leak("Nothing here.", "TOY-ACTIVE") == []


def test_path_leak_detects_banned_token():
    problems = leak.check_path_leak("bench/corpus/toy/toy-clean-001.md", ["TOY-ACTIVE"])
    assert problems


def test_path_leak_detects_criterion_encoding():
    problems = leak.check_path_leak("bench/corpus/toy/toy-active-001.md", ["TOY-ACTIVE"])
    assert problems


def test_path_leak_clean_path_is_fine():
    problems = leak.check_path_leak("bench/corpus/toy/toy-001.md", ["TOY-ACTIVE", "TOY-HEDGE"])
    assert problems == []


def test_check_artifact_aggregates_every_rule():
    problems = leak.check_artifact(
        artifact_text="TOY-ACTIVE appears here and shares six tokens alpha beta gamma delta epsilon zeta.",
        artifact_path="bench/corpus/toy/toy-defect-001.md",
        manifest_path="bench/corpus/toy/toy-defect-001.manifest.json",
        defects=[("TOY-ACTIVE", "alpha beta gamma delta epsilon zeta")],
        domain_criteria=["TOY-ACTIVE", "TOY-HEDGE"],
    )
    # Expect: description shingle leak, criterion id leak (twice: artifact
    # text once), and path leak on both the artifact and manifest path.
    assert len(problems) >= 3


def test_leak_check_corpus_over_a_freshly_built_toy_corpus_finds_nothing(tmp_path):
    build(tmp_path, (toy.DOMAIN,))
    problems = leak.leak_check_corpus(tmp_path)
    assert problems == []
