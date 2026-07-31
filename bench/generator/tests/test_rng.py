"""Tests for bench.generator.rng: the seeded PRNG and key derivation."""

from __future__ import annotations

from bench.generator.rng import CORPUS_SEED, PERSON, SeededRng, derive, root_seed


def test_root_seed_is_stable_and_documented_value():
    """The corpus root seed is a pure function of CORPUS_SEED and PERSON.
    This exact value is also published in bench/generator/README.md's
    worked example, so a change here is a change to that document first.
    """
    assert root_seed().hex() == "b7470f08a0096e0192161ee2b062cb16"


def test_derive_toy_001_matches_documented_seed():
    seed = derive(root_seed(), "toy", "toy-001")
    assert seed.hex() == "95f4393141bd0f4c0611135bcba857f6"


def test_derive_is_deterministic():
    a = derive(root_seed(), "toy", "toy-001")
    b = derive(root_seed(), "toy", "toy-001")
    assert a == b


def test_derive_separates_parts_with_unit_separator():
    """("ab", "c") must not derive the same key as ("a", "bc")."""
    parent = root_seed()
    assert derive(parent, "ab", "c") != derive(parent, "a", "bc")


def test_derive_is_sensitive_to_every_part():
    parent = root_seed()
    assert derive(parent, "toy", "toy-001") != derive(parent, "toy", "toy-002")
    assert derive(parent, "toy", "toy-001") != derive(parent, "clarity", "toy-001")


def test_seeded_rng_is_deterministic_across_instances():
    seed = derive(root_seed(), "toy", "toy-001")
    a = SeededRng(seed)
    b = SeededRng(seed)
    draws_a = [a.below(97) for _ in range(200)]
    draws_b = [b.below(97) for _ in range(200)]
    assert draws_a == draws_b


def test_seeded_rng_below_respects_bounds():
    rng = SeededRng(derive(root_seed(), "bounds-check"))
    for n in (1, 2, 3, 5, 8, 100, 257):
        for _ in range(50):
            assert 0 <= rng.below(n) < n


def test_seeded_rng_below_one_is_always_zero():
    rng = SeededRng(derive(root_seed(), "below-one"))
    assert all(rng.below(1) == 0 for _ in range(10))


def test_seeded_rng_choice_and_shuffle_and_sample():
    rng = SeededRng(derive(root_seed(), "choice-check"))
    items = ["a", "b", "c", "d", "e"]
    assert rng.choice(items) in items

    to_shuffle = list(range(20))
    original = list(to_shuffle)
    rng.shuffle(to_shuffle)
    assert sorted(to_shuffle) == sorted(original)

    sampled = rng.sample(range(10), 4)
    assert len(sampled) == 4
    assert len(set(sampled)) == 4
    assert all(0 <= v < 10 for v in sampled)


def test_child_stream_is_pure_function_of_parts_not_of_parent_state():
    """child() must not consume from the parent stream: creating two
    children in different orders, or drawing from the parent in between,
    must not change what either child produces."""
    seed = derive(root_seed(), "child-purity")

    rng1 = SeededRng(seed)
    child_a1 = rng1.child("a")
    child_b1 = rng1.child("b")

    rng2 = SeededRng(seed)
    # Draw from the parent, and create the children in the opposite order.
    rng2.bits(8)
    child_b2 = rng2.child("b")
    rng2.bits(8)
    child_a2 = rng2.child("a")

    assert child_a1.below(1000) == child_a2.below(1000)
    assert child_b1.below(1000) == child_b2.below(1000)


def test_child_streams_differ_by_key():
    seed = derive(root_seed(), "child-distinct")
    rng = SeededRng(seed)
    a = rng.child("para", 1, 1)
    b = rng.child("para", 1, 2)
    assert a.below(10_000) != b.below(10_000) or a.below(10_000) != b.below(10_000)
    # A stronger, deterministic check: the underlying seeds differ.
    assert derive(seed, "para", 1, 1) != derive(seed, "para", 1, 2)


def test_corpus_seed_constant_unchanged():
    """Rotating CORPUS_SEED regenerates every artifact and invalidates
    every published number; it requires its own ADR (bench/generator/
    README.md). This test exists so an accidental edit fails loudly."""
    assert CORPUS_SEED == "critique-skills/bench/corpus/v1"
    assert PERSON == b"critique-bench"
