"""Tests for bench/generator/manifest.schema.json itself: that it is a
valid draft 2020-12 schema, and that the definitions it copies from the
critique contract have not drifted. Mirrors the manual checks documented
in bench/README.md, "What works today"."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

MANIFEST_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "manifest.schema.json"
)
CONTRACT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "contract" / "critique-contract.schema.json"
)

# bench/generator/manifest.schema.json's own $comment: these six
# definitions are deliberate copies from contract/critique-contract.schema.json.
COPIED_DEFS = ("criterionId", "sha256", "artifactPath", "prose", "noEmDash", "trimmed")


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_manifest_schema_is_valid_draft_2020_12():
    schema = _load(MANIFEST_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)


def _patterns(node) -> set[str]:
    """Every string found under a "pattern" key, anywhere in a schema
    fragment (top level or nested inside allOf/anyOf/oneOf), so a def like
    `artifactPath` or `prose` whose pattern lives one level down inside
    `allOf` is still compared."""
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "pattern" and isinstance(value, str):
                found.add(value)
            else:
                found |= _patterns(value)
    elif isinstance(node, list):
        for item in node:
            found |= _patterns(item)
    return found


def test_copied_pattern_definitions_match_the_contract_byte_for_byte():
    """manifest.schema.json's own $comment: 'A CI drift check compares
    each copied pattern byte for byte against its contract original and
    fails on divergence.' Only the pattern (and type) is the copy;
    description and examples are free to differ, and do
    (manifest.schema.json's criterionId examples include 'TOY-ACTIVE',
    which is not a contract example)."""
    manifest_schema = _load(MANIFEST_SCHEMA_PATH)
    contract_schema = _load(CONTRACT_SCHEMA_PATH)
    for name in COPIED_DEFS:
        manifest_patterns = _patterns(manifest_schema["$defs"][name])
        contract_patterns = _patterns(contract_schema["$defs"][name])
        assert manifest_patterns == contract_patterns, (
            f"manifest.schema.json's $defs/{name} pattern(s) have drifted "
            f"from the contract's own"
        )
        assert manifest_schema["$defs"][name]["type"] == contract_schema["$defs"][name]["type"]


def test_artifact_type_enum_matches_bench_generator_api():
    from bench.generator.api import ARTIFACT_TYPES

    schema = _load(MANIFEST_SCHEMA_PATH)
    assert tuple(schema["$defs"]["artifactType"]["enum"]) == ARTIFACT_TYPES
