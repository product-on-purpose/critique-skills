"""The six-stage generation pipeline, per `bench/generator/README.md`,
"The pipeline". Everything here is harness responsibility: seeding,
addressing, hashing, manifest assembly, the leak check, and the round-trip
check. A domain module never runs any of this; it only supplies `compose`,
`render`, `address`, and its injectors.

`generate()` does not touch the filesystem. `bench/generator/build.py`
calls it once per recipe and writes the result to disk.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath

import jsonschema

from bench.generator import blockparse, leak
from bench.generator.api import Domain, InjectionResult, Location, Plant, Recipe
from bench.generator.markdown import Document
from bench.generator.rng import SeededRng, derive, root_seed
from bench.metrics import resolve_html

MANIFEST_VERSION = "1.0.0"
CORPUS_ROOT = "bench/corpus"

MANIFEST_SCHEMA_PATH = Path(__file__).resolve().parent / "manifest.schema.json"


class GenerationError(Exception):
    """Raised when a recipe fails leak checking, the round-trip check, or
    manifest schema validation. Carries every problem found, not just the
    first, so a build failure is diagnosable in one read."""

    def __init__(self, domain: str, recipe: str, stage: str, problems: list[str]) -> None:
        self.domain = domain
        self.recipe = recipe
        self.stage = stage
        self.problems = problems
        joined = "\n  - ".join(problems)
        super().__init__(
            f"{domain}/{recipe} failed at stage {stage!r}:\n  - {joined}"
        )


@dataclass(frozen=True, slots=True)
class GeneratedArtifact:
    artifact_path: str  # repository-relative POSIX path
    artifact_bytes: bytes
    manifest_path: str
    manifest_bytes: bytes
    manifest: dict


@dataclass(frozen=True, slots=True)
class _DefectRecord:
    criterion: str
    slot: str
    sentence: int | None
    severity_expected: int
    description: str


# --------------------------------------------------------------------------
# Seeding (Stage 1: Resolve)
# --------------------------------------------------------------------------


def artifact_seed(domain_name: str, recipe_id: str) -> bytes:
    """The artifact seed: `derive(root_seed(), domain, recipe_id)`. Alone
    sufficient to regenerate this artifact; nothing in the pipeline reaches
    back to the corpus root seed beyond this one derivation."""
    return derive(root_seed(), domain_name, recipe_id)


def _injection_rng(artifact_rng: SeededRng, plant: Plant) -> SeededRng:
    """The harness's derivation for an injector's randomness: a pure
    function of the artifact seed and (criterion, target), independent of
    injection order and of how many draws `compose` made. This is the
    harness-owned counterpart to `compose`'s own `rng.child("para", ...)`
    convention: it keeps the README's "editing one recipe changes only its
    own bytes" guarantee for injectors too. Not specified field-for-field
    in `bench/generator/README.md`, which leaves injector-rng derivation to
    the harness; this is the harness's one deliberate design choice beyond
    the frozen API."""
    t = plant.target
    return artifact_rng.child("inject", plant.criterion, t.section, t.block, t.item, t.element)


def _phase_sort_key(plant: Plant) -> tuple:
    """Canonical order within a phase: (target.section, target.block,
    criterion). `None` sorts before any block number, for a plant that
    targets a whole section."""
    t = plant.target
    block_key = (0, 0) if t.block is None else (1, t.block)
    return (t.section, block_key, plant.criterion)


def _apply_injections(
    domain: Domain, artifact_rng: SeededRng, composed: object, plants: tuple[Plant, ...]
) -> tuple[object, list[_DefectRecord]]:
    """Stages 3-4: Inject. Structural injectors always run first, in
    canonical order; then text injectors, in canonical order."""
    structure_plants = sorted(
        (p for p in plants if domain.injectors[p.criterion].phase == "structure"),
        key=_phase_sort_key,
    )
    text_plants = sorted(
        (p for p in plants if domain.injectors[p.criterion].phase == "text"),
        key=_phase_sort_key,
    )
    records: list[_DefectRecord] = []
    for plant in (*structure_plants, *text_plants):
        fn = domain.injectors[plant.criterion]
        result: InjectionResult = fn(_injection_rng(artifact_rng, plant), composed, plant.target)
        composed = result.composed
        records.append(
            _DefectRecord(
                criterion=plant.criterion,
                slot=result.slot,
                sentence=result.sentence,
                severity_expected=result.severity_expected,
                description=result.description,
            )
        )
    return composed, records


# --------------------------------------------------------------------------
# Manifest shaping (Stage 6: Emit)
# --------------------------------------------------------------------------


def _location_to_dict(loc: Location) -> dict:
    """Only the fields the manifest schema's per-kind `allOf` branch allows
    for `loc.kind`, matching manifest.schema.json's `$defs/location`."""
    d: dict = {"kind": loc.kind, "text": loc.text}
    if loc.kind == "paragraph":
        d["paragraph"] = loc.paragraph
        if loc.sentence is not None:
            d["sentence"] = loc.sentence
        if loc.heading_path:
            d["heading_path"] = list(loc.heading_path)
    elif loc.kind == "heading-path":
        d["heading_path"] = list(loc.heading_path)
    elif loc.kind == "css":
        d["css"] = loc.css
    elif loc.kind == "element-id":
        d["element_id"] = loc.element_id
    elif loc.kind == "item-index":
        d["item_index"] = loc.item_index
        if loc.item_key is not None:
            d["item_key"] = loc.item_key
    elif loc.kind == "page-path":
        d["page_path"] = loc.page_path
    else:
        raise ValueError(f"unknown location kind: {loc.kind!r}")
    return d


def _defect_document_position(composed: object, slot: str) -> int:
    """Document order key for manifest.schema.json's defects ordering
    ("in document order, ties broken by criterion ID"). Any composition
    model the harness works with is expected to provide `slot_index`;
    `markdown.Document` does. A composition without one sorts all its
    defects as position 0, falling back to criterion-only ordering, which
    is stable but not document-ordered."""
    slot_index = getattr(composed, "slot_index", None)
    if slot_index is None:
        return 0
    return slot_index(slot)


# --------------------------------------------------------------------------
# The round-trip check (independent re-parse of the rendered bytes)
# --------------------------------------------------------------------------


def _round_trip_check_markdown(
    doc: Document,
    rendered_text: str,
    records: list[_DefectRecord],
    locations: list[Location],
) -> list[str]:
    problems: list[str] = []
    parsed = blockparse.parse_markdown_blocks(rendered_text)
    if len(parsed) != len(doc.blocks):
        problems.append(
            f"round-trip block count mismatch: composition has {len(doc.blocks)} "
            f"blocks, reparsed text has {len(parsed)}"
        )
        return problems
    for record, location in zip(records, locations):
        position = doc.slot_index(record.slot)
        if location.kind == "paragraph":
            expected = blockparse.reparsed_paragraph_index(parsed, position)
            if expected != location.paragraph:
                problems.append(
                    f"round-trip paragraph index mismatch at slot {record.slot!r}: "
                    f"domain reported {location.paragraph}, reparse computed {expected}"
                )
        elif location.kind == "heading-path":
            expected_path = blockparse.reparsed_heading_path(parsed, position)
            if expected_path != location.heading_path:
                problems.append(
                    f"round-trip heading path mismatch at slot {record.slot!r}: "
                    f"domain reported {location.heading_path}, reparse computed {expected_path}"
                )
    return problems


def _round_trip_check_html(
    rendered_text: str,
    records: list[_DefectRecord],
    locations: list[Location],
) -> list[str]:
    """Re-parses the rendered bytes with `bench/metrics/resolve_html.py`,
    the metrics module's own normative HTML parser, the same relationship
    `_round_trip_check_markdown` has with the metrics block parser: this
    is what keeps the generator and the scorer honest with each other,
    rather than a second, independently-written HTML parser here. An
    `element-id` location round-trips when the reparsed document has
    exactly one element carrying that id; a `css` location round-trips
    when the reparsed document's own bounded selector engine resolves it
    to exactly one element."""
    problems: list[str] = []
    doc = resolve_html.parse_html(rendered_text)
    for record, location in zip(records, locations):
        if location.kind == "element-id":
            if doc.by_id(location.element_id) is None:
                problems.append(
                    f"round-trip: element id {location.element_id!r} not found in the "
                    f"reparsed HTML for slot {record.slot!r}"
                )
        elif location.kind == "css":
            matched = resolve_html.resolve_css(doc, location.css)
            if len(matched) != 1:
                problems.append(
                    f"round-trip: css {location.css!r} resolved to {len(matched)} element(s) "
                    f"in the reparsed HTML, expected exactly 1, for slot {record.slot!r}"
                )
    return problems


def _round_trip_check(
    domain: Domain,
    composed: object,
    rendered_text: str,
    records: list[_DefectRecord],
    locations: list[Location],
) -> list[str]:
    if domain.artifact_type in ("markdown-prose", "markdown-tree"):
        if not isinstance(composed, Document):
            return [
                f"artifact_type {domain.artifact_type!r} requires a "
                f"markdown.Document composition, got {type(composed).__name__}"
            ]
        return _round_trip_check_markdown(composed, rendered_text, records, locations)
    if domain.artifact_type == "html":
        return _round_trip_check_html(rendered_text, records, locations)
    # string-list round-trip checks are established when their first
    # domain module lands; not exercised at this implementation stage.
    return []


# --------------------------------------------------------------------------
# Manifest schema validation
# --------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_manifest_schema() -> dict:
    with MANIFEST_SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def _manifest_validator() -> jsonschema.Draft202012Validator:
    schema = _load_manifest_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _manifest_schema_problems(manifest: dict) -> list[str]:
    return [
        f"{'.'.join(str(p) for p in error.path) or '<root>'}: {error.message}"
        for error in _manifest_validator().iter_errors(manifest)
    ]


# --------------------------------------------------------------------------
# The pipeline entry point
# --------------------------------------------------------------------------


def artifact_corpus_path(domain: Domain, recipe: Recipe) -> str:
    return str(PurePosixPath(CORPUS_ROOT, domain.name, f"{recipe.id}{domain.extension}"))


def manifest_corpus_path(domain: Domain, recipe: Recipe) -> str:
    return str(PurePosixPath(CORPUS_ROOT, domain.name, f"{recipe.id}.manifest.json"))


def generate(domain: Domain, recipe: Recipe) -> GeneratedArtifact:
    """Run the full pipeline for one (domain, recipe) pair: compose,
    inject, address, emit, then verify before returning. Raises
    GenerationError with every problem found if the leak check, the
    round-trip check, or manifest schema validation fails; nothing that
    fails any of these is ever handed to a caller to write."""
    seed = artifact_seed(domain.name, recipe.id)
    artifact_rng = SeededRng(seed)

    # Stage 2: Compose.
    composed = domain.compose(artifact_rng, recipe.shape)

    # Stages 3-4: Inject.
    composed, records = _apply_injections(domain, artifact_rng, composed, recipe.plants)

    # Stage 5: Address, on the final composition, after every injection.
    locations = [domain.address(composed, r.slot, sentence=r.sentence) for r in records]

    # Stage 6: Emit artifact bytes.
    rendered = domain.render(composed)
    artifact_text = unicodedata.normalize("NFC", rendered + "\n")
    artifact_bytes = artifact_text.encode("utf-8")

    artifact_path = artifact_corpus_path(domain, recipe)
    manifest_path = manifest_corpus_path(domain, recipe)

    problems: list[str] = []

    # Verify before writing: the round-trip check.
    problems.extend(_round_trip_check(domain, composed, artifact_text, records, locations))

    # Verify before writing: the leak check.
    domain_criteria = tuple(sorted(domain.injectors))
    problems.extend(
        leak.check_artifact(
            artifact_text=artifact_text,
            artifact_path=artifact_path,
            manifest_path=manifest_path,
            defects=[(r.criterion, r.description) for r in records],
            domain_criteria=domain_criteria,
        )
    )

    if problems:
        raise GenerationError(domain.name, recipe.id, "verify", problems)

    # Stage 6: Emit manifest bytes.
    defect_dicts = [
        {
            "criterion": record.criterion,
            "location": _location_to_dict(location),
            "severity_expected": record.severity_expected,
            "description": record.description,
        }
        for record, location in sorted(
            zip(records, locations),
            key=lambda pair: (_defect_document_position(composed, pair[0].slot), pair[0].criterion),
        )
    ]

    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "artifact": artifact_path,
        "artifact_sha256": hashlib.sha256(artifact_bytes).hexdigest(),
        "seed": seed.hex(),
        "domain": domain.name,
        "artifact_type": domain.artifact_type,
        "recipe": recipe.id,
        "defects": defect_dicts,
    }

    schema_problems = _manifest_schema_problems(manifest)
    if schema_problems:
        raise GenerationError(domain.name, recipe.id, "manifest-schema", schema_problems)

    manifest_text = unicodedata.normalize(
        "NFC", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    manifest_bytes = manifest_text.encode("utf-8")

    return GeneratedArtifact(
        artifact_path=artifact_path,
        artifact_bytes=artifact_bytes,
        manifest_path=manifest_path,
        manifest_bytes=manifest_bytes,
        manifest=manifest,
    )
