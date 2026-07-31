"""Tests for bench.generator.pipeline: the six-stage generation pipeline,
run end to end against the toy domain.

Includes the leak-rule test S-03 AC-8 requires: a defect's description
text never appears verbatim in the artifact it describes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema
import pytest

from bench.generator.domains import toy
from bench.generator.pipeline import GeneratedArtifact, generate
from bench.generator.rng import derive, root_seed

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "manifest.schema.json"


def _manifest_schema() -> dict:
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def manifest_validator() -> jsonschema.Draft202012Validator:
    schema = _manifest_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


@pytest.fixture(params=[r.id for r in toy.DOMAIN.recipes])
def generated(request) -> GeneratedArtifact:
    recipe = next(r for r in toy.DOMAIN.recipes if r.id == request.param)
    return generate(toy.DOMAIN, recipe)


def test_artifact_bytes_are_valid_utf8_no_bom():
    generated = generate(toy.DOMAIN, toy.RECIPES[0])
    assert not generated.artifact_bytes.startswith(b"\xef\xbb\xbf")
    generated.artifact_bytes.decode("utf-8")  # must not raise


def test_artifact_bytes_end_with_exactly_one_trailing_newline():
    for recipe in toy.DOMAIN.recipes:
        text = generate(toy.DOMAIN, recipe).artifact_bytes.decode("utf-8")
        assert text.endswith("\n")
        assert not text.endswith("\n\n")


def test_artifact_bytes_have_no_crlf():
    for recipe in toy.DOMAIN.recipes:
        assert b"\r\n" not in generate(toy.DOMAIN, recipe).artifact_bytes


def test_manifest_is_schema_valid(generated, manifest_validator):
    manifest_validator.validate(generated.manifest)


def test_manifest_artifact_sha256_matches_artifact_bytes(generated):
    assert generated.manifest["artifact_sha256"] == hashlib.sha256(
        generated.artifact_bytes
    ).hexdigest()


def test_clean_recipe_has_empty_defects_list():
    clean_recipe = next(r for r in toy.DOMAIN.recipes if not r.plants)
    generated = generate(toy.DOMAIN, clean_recipe)
    assert generated.manifest["defects"] == []


def test_seeded_recipe_has_one_defect_per_plant():
    for recipe in toy.DOMAIN.recipes:
        generated = generate(toy.DOMAIN, recipe)
        assert len(generated.manifest["defects"]) == len(recipe.plants)


def test_defect_criteria_match_planted_criteria():
    for recipe in toy.DOMAIN.recipes:
        generated = generate(toy.DOMAIN, recipe)
        expected = sorted(p.criterion for p in recipe.plants)
        actual = sorted(d["criterion"] for d in generated.manifest["defects"])
        assert actual == expected


def test_defects_are_sorted_in_document_order():
    generated = generate(toy.DOMAIN, next(r for r in toy.DOMAIN.recipes if r.id == "toy-002"))
    defects = generated.manifest["defects"]
    # toy-002 plants TOY-ORPHAN (section 4, a heading at the end of the
    # document), TOY-ACTIVE (section 2), TOY-HEDGE (section 1): document
    # order puts the hedge first, the active recast second, the orphan last.
    assert [d["criterion"] for d in defects] == ["TOY-HEDGE", "TOY-ACTIVE", "TOY-ORPHAN"]


def test_seed_recorded_in_manifest_matches_derivation():
    for recipe in toy.DOMAIN.recipes:
        generated = generate(toy.DOMAIN, recipe)
        expected = derive(root_seed(), "toy", recipe.id).hex()
        assert generated.manifest["seed"] == expected


def test_manifest_paths_are_posix_and_repo_relative():
    generated = generate(toy.DOMAIN, toy.RECIPES[0])
    assert generated.artifact_path == "bench/corpus/toy/toy-001.md"
    assert generated.manifest_path == "bench/corpus/toy/toy-001.manifest.json"
    assert "\\" not in generated.artifact_path


# --------------------------------------------------------------------------
# S-03 AC-8: the leak rule. A defect's description must never appear
# verbatim (nor as a shared 6-token shingle) in the artifact it describes.
# --------------------------------------------------------------------------


def test_defect_descriptions_never_appear_verbatim_in_the_artifact():
    for recipe in toy.DOMAIN.recipes:
        generated = generate(toy.DOMAIN, recipe)
        artifact_text = generated.artifact_bytes.decode("utf-8")
        for defect in generated.manifest["defects"]:
            assert defect["description"] not in artifact_text, (
                f"{recipe.id}: description for {defect['criterion']} "
                f"appears verbatim in the artifact"
            )


def test_criterion_ids_never_appear_in_artifact_text():
    for recipe in toy.DOMAIN.recipes:
        generated = generate(toy.DOMAIN, recipe)
        artifact_text = generated.artifact_bytes.decode("utf-8")
        for criterion in toy.DOMAIN.injectors:
            assert criterion not in artifact_text
            assert criterion.casefold() not in artifact_text.casefold()


def test_generation_raises_if_a_description_shingles_with_the_artifact(monkeypatch):
    """A synthetic negative control: an injector whose description quotes
    the artifact must be caught, so the positive tests above are not
    passing merely because nothing exercises the check."""
    from bench.generator import api
    from bench.generator.pipeline import GenerationError

    original = toy.INJECTORS["TOY-HEDGE"]

    def leaking_injector(rng, doc, target):
        result = original(rng, doc, target)
        leaked_description = result.composed.block(result.slot).text
        return api.InjectionResult(
            composed=result.composed,
            slot=result.slot,
            severity_expected=result.severity_expected,
            description=leaked_description,
            sentence=result.sentence,
        )

    # The @injector decorator normally stamps these; a hand-built
    # replacement must carry them too, since the pipeline reads .phase to
    # order structure injectors ahead of text injectors.
    leaking_injector.criterion = original.criterion
    leaking_injector.phase = original.phase

    monkeypatch.setitem(toy.INJECTORS, "TOY-HEDGE", leaking_injector)
    recipe = next(r for r in toy.DOMAIN.recipes if r.id == "toy-001")
    with pytest.raises(GenerationError, match="shingle"):
        generate(toy.DOMAIN, recipe)
