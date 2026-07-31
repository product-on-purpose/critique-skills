"""Tests for bench.generator.api.Domain.validate(): the self-validation
checklist bench/generator/README.md, "Self-validation" requires."""

from __future__ import annotations

import pytest

from bench.generator.api import Domain, DomainValidationError, Plant, Recipe, Target


def _noop_injector(rng, doc, target):  # pragma: no cover - never called by validate()
    raise NotImplementedError


def _make_domain(**overrides) -> Domain:
    defaults = dict(
        name="fake",
        artifact_type="markdown-prose",
        extension=".md",
        namespaces=("FAKE",),
        compose=lambda rng, shape: None,
        render=lambda composed: "",
        address=lambda composed, slot, sentence=None: None,
        injectors={"FAKE-ONE": _noop_injector},
        recipes=(
            Recipe(
                id="fake-001",
                shape={"paragraphs": (2, 1)},
                plants=(Plant("FAKE-ONE", Target(section=1, block=1), severity_expected=2),),
            ),
            Recipe(id="fake-002", shape={"paragraphs": (1,)}, plants=()),
        ),
    )
    defaults.update(overrides)
    return Domain(**defaults)


def test_baseline_domain_is_valid():
    _make_domain().validate()  # must not raise


def test_bad_artifact_type_rejected():
    domain = _make_domain(artifact_type="pdf")
    with pytest.raises(DomainValidationError, match="artifact_type"):
        domain.validate()


def test_injector_key_must_match_criterion_grammar():
    domain = _make_domain(
        injectors={"fake-one": _noop_injector},
        recipes=(Recipe(id="fake-001", shape={"paragraphs": (1,)}, plants=()),),
    )
    with pytest.raises(DomainValidationError, match="criterion ID grammar"):
        domain.validate()


def test_injector_namespace_must_be_declared():
    domain = _make_domain(
        injectors={"OTHER-ONE": _noop_injector},
        recipes=(Recipe(id="fake-001", shape={"paragraphs": (1,)}, plants=()),),
    )
    with pytest.raises(DomainValidationError, match="namespace"):
        domain.validate()


def test_plant_must_reference_a_registered_injector():
    domain = _make_domain(
        recipes=(
            Recipe(
                id="fake-001",
                shape={"paragraphs": (1,)},
                plants=(Plant("FAKE-MISSING", Target(section=1, block=1), severity_expected=2),),
            ),
            Recipe(id="fake-002", shape={"paragraphs": (1,)}, plants=()),
        )
    )
    with pytest.raises(DomainValidationError, match="no registered injector"):
        domain.validate()


@pytest.mark.parametrize("severity", [0, 5, -1])
def test_severity_expected_out_of_range_rejected(severity):
    domain = _make_domain(
        recipes=(
            Recipe(
                id="fake-001",
                shape={"paragraphs": (1,)},
                plants=(Plant("FAKE-ONE", Target(section=1, block=1), severity_expected=severity),),
            ),
            Recipe(id="fake-002", shape={"paragraphs": (1,)}, plants=()),
        )
    )
    with pytest.raises(DomainValidationError, match="severity_expected"):
        domain.validate()


def test_plant_target_section_out_of_range_rejected():
    domain = _make_domain(
        recipes=(
            Recipe(
                id="fake-001",
                shape={"paragraphs": (1,)},
                plants=(Plant("FAKE-ONE", Target(section=5, block=1), severity_expected=2),),
            ),
            Recipe(id="fake-002", shape={"paragraphs": (1,)}, plants=()),
        )
    )
    with pytest.raises(DomainValidationError, match="section"):
        domain.validate()


def test_plant_target_block_out_of_range_rejected():
    domain = _make_domain(
        recipes=(
            Recipe(
                id="fake-001",
                shape={"paragraphs": (1,)},
                plants=(Plant("FAKE-ONE", Target(section=1, block=9), severity_expected=2),),
            ),
            Recipe(id="fake-002", shape={"paragraphs": (1,)}, plants=()),
        )
    )
    with pytest.raises(DomainValidationError, match="block"):
        domain.validate()


def test_more_than_six_paragraphs_per_section_rejected():
    domain = _make_domain(
        recipes=(
            Recipe(id="fake-001", shape={"paragraphs": (7,)}, plants=()),
            Recipe(id="fake-002", shape={"paragraphs": (1,)}, plants=()),
        )
    )
    with pytest.raises(DomainValidationError, match="exceeding the corpus invariant"):
        domain.validate()


def test_two_plants_same_criterion_same_section_rejected():
    domain = _make_domain(
        recipes=(
            Recipe(
                id="fake-001",
                shape={"paragraphs": (2,)},
                plants=(
                    Plant("FAKE-ONE", Target(section=1, block=1), severity_expected=2),
                    Plant("FAKE-ONE", Target(section=1, block=2), severity_expected=2),
                ),
            ),
            Recipe(id="fake-002", shape={"paragraphs": (1,)}, plants=()),
        )
    )
    with pytest.raises(DomainValidationError, match="at most once"):
        domain.validate()


def test_recipe_id_with_banned_token_rejected():
    domain = _make_domain(
        recipes=(
            Recipe(id="fake-clean-1", shape={"paragraphs": (1,)}, plants=()),
        )
    )
    with pytest.raises(DomainValidationError, match="banned token"):
        domain.validate()


def test_recipe_id_encoding_criterion_rejected():
    domain = _make_domain(
        recipes=(
            Recipe(id="fake-one-1", shape={"paragraphs": (1,)}, plants=()),
        )
    )
    with pytest.raises(DomainValidationError, match="encodes criterion"):
        domain.validate()


def test_duplicate_recipe_ids_rejected():
    domain = _make_domain(
        recipes=(
            Recipe(id="fake-001", shape={"paragraphs": (1,)}, plants=()),
            Recipe(id="fake-001", shape={"paragraphs": (1,)}, plants=()),
        )
    )
    with pytest.raises(DomainValidationError, match="not unique"):
        domain.validate()


def test_no_clean_recipe_rejected():
    domain = _make_domain(
        recipes=(
            Recipe(
                id="fake-001",
                shape={"paragraphs": (1,)},
                plants=(Plant("FAKE-ONE", Target(section=1, block=1), severity_expected=2),),
            ),
        )
    )
    with pytest.raises(DomainValidationError, match="plants=\\(\\)"):
        domain.validate()


def test_recipe_id_must_be_a_lowercase_slug():
    domain = _make_domain(
        recipes=(Recipe(id="Fake_001", shape={"paragraphs": (1,)}, plants=()),)
    )
    with pytest.raises(DomainValidationError, match="slug"):
        domain.validate()


def test_error_collects_every_problem_not_just_the_first():
    domain = _make_domain(artifact_type="pdf", namespaces=("OTHER",))
    with pytest.raises(DomainValidationError) as excinfo:
        domain.validate()
    assert len(excinfo.value.problems) >= 2
