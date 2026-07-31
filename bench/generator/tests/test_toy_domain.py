"""Tests for bench.generator.domains.toy: the worked example, exercised
directly rather than only through the pipeline."""

from __future__ import annotations

from bench.generator.domains import toy
from bench.generator.markdown import Document
from bench.generator.rng import SeededRng, derive, root_seed


def _rng(*parts) -> SeededRng:
    return SeededRng(derive(root_seed(), "toy-domain-test", *parts))


def test_domain_self_validates():
    toy.DOMAIN.validate()  # must not raise


def test_domain_declares_the_frozen_shape():
    assert toy.DOMAIN.name == "toy"
    assert toy.DOMAIN.artifact_type == "markdown-prose"
    assert toy.DOMAIN.extension == ".md"
    assert toy.DOMAIN.namespaces == ("TOY",)
    assert set(toy.DOMAIN.injectors) == {"TOY-ACTIVE", "TOY-HEDGE", "TOY-ORPHAN"}


def test_at_least_one_clean_recipe():
    assert any(not r.plants for r in toy.DOMAIN.recipes)


def test_recipe_ids_are_slugs_with_no_criterion_or_count_encoded():
    for recipe in toy.DOMAIN.recipes:
        assert recipe.id.startswith("toy-")
        assert "active" not in recipe.id
        assert "hedge" not in recipe.id
        assert "orphan" not in recipe.id


def test_compose_assigns_one_slot_per_declared_paragraph():
    doc = toy.compose(_rng("compose"), {"paragraphs": (2, 1, 3)})
    assert isinstance(doc, Document)
    paragraph_slots = [b.slot for b in doc.blocks if b.kind == "paragraph"]
    assert paragraph_slots == ["s1.p1", "s1.p2", "s2.p1", "s3.p1", "s3.p2", "s3.p3"]
    heading_slots = [b.slot for b in doc.blocks if b.kind == "heading"]
    assert heading_slots == ["h0", "s1.h", "s2.h", "s3.h"]


def test_compose_is_deterministic_for_the_same_rng_state():
    doc_a = toy.compose(_rng("determinism"), {"paragraphs": (2, 1)})
    doc_b = toy.compose(_rng("determinism"), {"paragraphs": (2, 1)})
    assert doc_a == doc_b


def test_inject_active_recasts_lead_sentence_and_keeps_the_rest():
    from bench.generator.api import Target

    doc = toy.compose(_rng("active"), {"paragraphs": (1,)})
    original = doc.block("s1.p1").text
    tail = original.split(". ", 1)[1]
    result = toy.inject_active(_rng("active-inject"), doc, Target(section=1, block=1))
    new_text = result.composed.block("s1.p1").text
    assert new_text != original
    assert new_text.endswith(tail)
    assert result.slot == "s1.p1"
    assert result.severity_expected == 2
    assert "acting party" in result.description
    # The description is meta-language, never a quote of either sentence.
    assert original.split(".")[0] not in result.description
    assert new_text.split(".")[0] not in result.description


def test_inject_hedge_prefixes_a_hedge_and_keeps_the_rest():
    from bench.generator.api import Target

    doc = toy.compose(_rng("hedge"), {"paragraphs": (1,)})
    original = doc.block("s1.p1").text
    result = toy.inject_hedge(_rng("hedge-inject"), doc, Target(section=1, block=1))
    new_text = result.composed.block("s1.p1").text
    assert new_text != original
    assert any(new_text.startswith(h) for h in toy.HEDGES)
    assert result.slot == "s1.p1"
    assert result.severity_expected == 2


def test_inject_orphan_adds_heading_with_no_body_before_next_section():
    from bench.generator.api import Target

    doc = toy.compose(_rng("orphan"), {"paragraphs": (1, 1)})
    result = toy.inject_orphan(_rng("orphan-inject"), doc, Target(section=1))
    new_doc = result.composed
    slots = [b.slot for b in new_doc.blocks]
    # The orphan heading sits right before the next section's heading.
    assert slots.index(result.slot) == slots.index("s2.h") - 1
    assert new_doc.block(result.slot).kind == "heading"
    assert new_doc.block(result.slot).level == 3
    assert result.severity_expected == 3


def test_address_for_paragraph_reports_expected_fields():
    doc = toy.compose(_rng("address-para"), {"paragraphs": (2, 1)})
    loc = toy.address(doc, "s1.p2", sentence=1)
    assert loc.kind == "paragraph"
    assert loc.paragraph == 2
    assert loc.sentence == 1
    assert loc.heading_path[-1] == "Service window"
    assert "second paragraph" in loc.text
    assert "first sentence" in loc.text


def test_address_for_heading_reports_heading_path_kind():
    doc = toy.compose(_rng("address-heading"), {"paragraphs": (1,)})
    loc = toy.address(doc, "s1.h")
    assert loc.kind == "heading-path"
    assert loc.heading_path == ("Field operations notice", "Service window")
    assert loc.text == "the Service window heading"


def test_ordinal_within_section_resets_per_top_level_section():
    doc = toy.compose(_rng("ordinal"), {"paragraphs": (2, 2)})
    assert toy._ordinal_within_section(doc, "s1.p1") == 1
    assert toy._ordinal_within_section(doc, "s1.p2") == 2
    assert toy._ordinal_within_section(doc, "s2.p1") == 1
    assert toy._ordinal_within_section(doc, "s2.p2") == 2
