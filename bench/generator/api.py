"""The domain-plugin API. Frozen in `bench/generator/README.md`; this module
implements it exactly as specified there.

A domain module declares vocabulary, structure, composition, injectors, and
recipes (see the README's "What a domain module owes the harness"). It never
opens a file, never touches the clock, never imports `random`, and never
writes a manifest: everything else belongs to the harness, in
`bench/generator/pipeline.py` and the modules it calls.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import Callable, Iterable, Literal, Mapping

from bench.generator.rng import SeededRng

Phase = Literal["structure", "text"]

# The four artifact types the manifest schema enumerates. A domain module
# declaring anything else fails Domain.validate() immediately.
ARTIFACT_TYPES: tuple[str, ...] = ("markdown-prose", "markdown-tree", "html", "string-list")

# Copied from bench/generator/manifest.schema.json's $defs/criterionId and
# $defs/slug, which are themselves copied from the critique contract. Kept
# here as plain Python regexes (rather than a jsonschema round trip) because
# Domain.validate() runs at import time, before any file is written, and
# needs no schema document to do it.
CRITERION_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+(?:\.[A-Z0-9]+)*)+$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# bench/README.md, "Invariants": "Recipe ids and paths reveal nothing: no
# criterion, no count, no 'clean' or 'defect' token." A recipe id is opaque
# by rule because the artifact path reaches the skill under test.
BANNED_PATH_TOKENS: frozenset[str] = frozenset({"clean", "defect", "seed", "plant", "bug"})


@dataclass(frozen=True, slots=True)
class Target:
    """Where a plant goes, declared in the recipe. Statically checked
    against the shape."""

    section: int  # 1-based section ordinal
    block: int | None = None  # 1-based paragraph ordinal within the section
    item: int | None = None  # 1-based list item, string-list domains
    element: str | None = None  # element slot id, html domains


@dataclass(frozen=True, slots=True)
class Plant:
    criterion: str  # must match the contract's criterion ID grammar
    target: Target
    severity_expected: int  # 1 to 4


@dataclass(frozen=True, slots=True)
class Recipe:
    id: str  # opaque slug, unique in the domain, reveals nothing
    shape: Mapping[str, object]  # declared structure, domain-defined keys
    plants: tuple[Plant, ...]  # empty tuple means a clean artifact


@dataclass(frozen=True, slots=True)
class Location:
    """Mirrors the location object in manifest.schema.json, field for field."""

    kind: str
    text: str
    paragraph: int | None = None
    sentence: int | None = None
    heading_path: tuple[str, ...] = ()
    css: str | None = None
    element_id: str | None = None
    item_index: int | None = None
    item_key: str | None = None
    page_path: str | None = None


@dataclass(frozen=True, slots=True)
class InjectionResult:
    composed: object  # the new composition; never mutate the input in place
    slot: str  # the slot the defect now lives at
    severity_expected: int
    description: str  # meta-language only, never a quote of the artifact
    sentence: int | None = None  # optional refinement, markdown domains


Injector = Callable[[SeededRng, object, Target], InjectionResult]


def injector(criterion: str, *, phase: Phase = "text"):
    """Decorator factory a domain module uses to register one of its own
    injectors, keyed by criterion ID.

    Writes into the *calling module's* own module-level `INJECTORS` dict
    (created on first use if the module has not declared one), never into a
    dict owned by this module. That is what keeps registration module-local,
    per the README: two domain modules never share a dict, so import order
    between them cannot matter, and the harness reads each domain's
    injectors off its own `Domain.injectors` rather than off anything
    global here.
    """

    def wrap(fn: Injector) -> Injector:
        fn.criterion = criterion  # type: ignore[attr-defined]
        fn.phase = phase  # type: ignore[attr-defined]
        caller_globals = sys._getframe(1).f_globals
        registry: dict[str, Injector] = caller_globals.setdefault("INJECTORS", {})
        registry[criterion] = fn
        return fn

    return wrap


class DomainValidationError(Exception):
    """Raised by Domain.validate() with every problem found, not just the first."""

    def __init__(self, domain_name: str, problems: list[str]) -> None:
        self.domain_name = domain_name
        self.problems = problems
        joined = "\n  - ".join(problems)
        super().__init__(f"domain '{domain_name}' failed validation:\n  - {joined}")


@dataclass(frozen=True, slots=True)
class Domain:
    name: str  # slug, matches the owning skill's suffix
    artifact_type: str  # markdown-prose | markdown-tree | html | string-list
    extension: str  # ".md", ".html", ".json"
    namespaces: tuple[str, ...]  # criterion namespaces this domain seeds
    compose: Callable[[SeededRng, Mapping[str, object]], object]
    render: Callable[[object], str]
    address: Callable[..., Location]
    injectors: Mapping[str, Injector]
    recipes: tuple[Recipe, ...]

    def validate(self) -> None:
        """Self-validation, run before any generation. Raises
        DomainValidationError with every problem found, not just the first.
        See bench/generator/README.md, "Self-validation"."""
        problems: list[str] = []
        problems.extend(_check_artifact_type(self))
        problems.extend(_check_namespaces(self))
        problems.extend(_check_injector_keys(self))
        problems.extend(_check_recipe_ids(self))
        problems.extend(_check_plants_reference_injectors(self))
        problems.extend(_check_plants_target_shape(self))
        problems.extend(_check_one_criterion_per_section(self))
        problems.extend(_check_at_least_one_clean_recipe(self))
        if problems:
            raise DomainValidationError(self.name, problems)


# --------------------------------------------------------------------------
# Self-validation checks. Each returns a list of human-readable problems;
# an empty list means the check passed.
# --------------------------------------------------------------------------


def _check_artifact_type(domain: Domain) -> list[str]:
    if domain.artifact_type not in ARTIFACT_TYPES:
        return [
            f"artifact_type {domain.artifact_type!r} is not one of {ARTIFACT_TYPES}"
        ]
    return []


def _check_namespaces(domain: Domain) -> list[str]:
    problems = []
    if not domain.namespaces:
        problems.append("namespaces must declare at least one criterion namespace")
    for ns in domain.namespaces:
        if not re.fullmatch(r"[A-Z][A-Z0-9]*", ns):
            problems.append(f"namespace {ns!r} is not uppercase alphanumeric starting with a letter")
    return problems


def _namespace_of(criterion: str) -> str | None:
    if "-" not in criterion:
        return None
    return criterion.split("-", 1)[0]


def _check_injector_keys(domain: Domain) -> list[str]:
    problems = []
    for criterion in sorted(domain.injectors):
        if not CRITERION_ID_RE.match(criterion):
            problems.append(f"injector key {criterion!r} does not match the criterion ID grammar")
            continue
        ns = _namespace_of(criterion)
        if ns not in domain.namespaces:
            problems.append(
                f"injector key {criterion!r} has namespace {ns!r}, "
                f"not in declared namespaces {domain.namespaces}"
            )
    return problems


def _check_recipe_ids(domain: Domain) -> list[str]:
    problems = []
    seen: set[str] = set()
    criteria = sorted(domain.injectors)
    for recipe in domain.recipes:
        if not SLUG_RE.match(recipe.id):
            problems.append(f"recipe id {recipe.id!r} is not a lowercase hyphen-separated slug")
        if recipe.id in seen:
            problems.append(f"recipe id {recipe.id!r} is not unique in domain {domain.name!r}")
        seen.add(recipe.id)
        problems.extend(_check_recipe_id_leak(recipe.id, criteria))
    return problems


def _check_recipe_id_leak(recipe_id: str, criteria: Iterable[str]) -> list[str]:
    """bench/README.md invariant: 'Recipe ids and paths reveal nothing: no
    criterion, no count, no clean or defect token.'"""
    problems = []
    segments = set(recipe_id.split("-"))
    banned_hit = BANNED_PATH_TOKENS & segments
    if banned_hit:
        problems.append(
            f"recipe id {recipe_id!r} contains banned token(s) {sorted(banned_hit)}"
        )
    lowered = recipe_id.lower()
    for criterion in criteria:
        if criterion.lower() in lowered:
            problems.append(f"recipe id {recipe_id!r} encodes criterion {criterion!r}")
    return problems


def _check_plants_reference_injectors(domain: Domain) -> list[str]:
    problems = []
    for recipe in domain.recipes:
        for plant in recipe.plants:
            if plant.criterion not in domain.injectors:
                problems.append(
                    f"recipe {recipe.id!r} plants {plant.criterion!r}, "
                    f"which has no registered injector"
                )
            if not (1 <= plant.severity_expected <= 4):
                problems.append(
                    f"recipe {recipe.id!r} plant {plant.criterion!r} has "
                    f"severity_expected {plant.severity_expected}, must be 1 to 4"
                )
    return problems


# bench/README.md, "Invariants": at most 6 paragraphs per section in
# markdown-prose and markdown-tree, so a heading-only location is worth at
# most a 1-in-6 guess. This bound is load-bearing for ADR 0015; a domain
# that violates it silently changes what every published recall figure
# means, so it fails validation rather than generating.
MAX_PARAGRAPHS_PER_SECTION = 6


def _check_plants_target_shape(domain: Domain) -> list[str]:
    """Checks a plant's target against the declared shape, for the shape
    conventions this stage of the harness understands. markdown-prose and
    markdown-tree use `shape["paragraphs"]`, a tuple of per-section
    paragraph counts, exactly as bench/generator/README.md's toy example
    declares it; that convention is checked here. html and string-list
    conventions are established when their first domain module lands and
    are not checked here."""
    if domain.artifact_type not in ("markdown-prose", "markdown-tree"):
        return []
    problems: list[str] = []
    for recipe in domain.recipes:
        paragraphs = recipe.shape.get("paragraphs")
        if not isinstance(paragraphs, (tuple, list)) or not paragraphs:
            problems.append(
                f"recipe {recipe.id!r} shape must declare a non-empty 'paragraphs' "
                f"sequence for artifact_type {domain.artifact_type!r}"
            )
            continue
        for count in paragraphs:
            if not isinstance(count, int) or count < 0:
                problems.append(
                    f"recipe {recipe.id!r} shape 'paragraphs' entries must be "
                    f"non-negative integers, got {count!r}"
                )
            elif count > MAX_PARAGRAPHS_PER_SECTION:
                problems.append(
                    f"recipe {recipe.id!r} section has {count} paragraphs, "
                    f"exceeding the corpus invariant of at most "
                    f"{MAX_PARAGRAPHS_PER_SECTION} per section"
                )
        section_count = len(paragraphs)
        for plant in recipe.plants:
            target = plant.target
            if not (1 <= target.section <= section_count):
                problems.append(
                    f"recipe {recipe.id!r} plant {plant.criterion!r} targets "
                    f"section {target.section}, out of range 1..{section_count}"
                )
                continue
            if target.block is not None:
                para_count = paragraphs[target.section - 1]
                if not isinstance(para_count, int) or not (1 <= target.block <= para_count):
                    problems.append(
                        f"recipe {recipe.id!r} plant {plant.criterion!r} targets "
                        f"section {target.section} block {target.block}, out of "
                        f"range 1..{para_count}"
                    )
    return problems


def _check_one_criterion_per_section(domain: Domain) -> list[str]:
    """bench/README.md invariant: at most one planted defect per criterion
    per section. Makes the scorer's greedy match assignment unambiguous in
    practice, per ADR 0015."""
    problems = []
    for recipe in domain.recipes:
        seen: dict[tuple[int, str], int] = {}
        for plant in recipe.plants:
            key = (plant.target.section, plant.criterion)
            seen[key] = seen.get(key, 0) + 1
        for (section, criterion), count in seen.items():
            if count > 1:
                problems.append(
                    f"recipe {recipe.id!r} plants {criterion!r} {count} times "
                    f"in section {section}, at most once is allowed"
                )
    return problems


def _check_at_least_one_clean_recipe(domain: Domain) -> list[str]:
    if not any(not r.plants for r in domain.recipes):
        return [f"domain {domain.name!r} has no recipe with plants=() (a clean artifact)"]
    return []
