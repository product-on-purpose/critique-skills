"""The leak check. Manifest content must not be discoverable inside the
artifact. AC-8 tests this; the generator enforces it at build time so a
violation never reaches the corpus. See `bench/generator/README.md`,
"The leak rule", rules 1 through 4. Rule 5, content-derived HTML ids, is
not code in this module: it is a construction invariant an html domain
module upholds itself, by assigning an `id` attribute to every element of
an injectable class unconditionally in `compose`, before any injector
runs, in the clean recipe and every seeded one alike (see
`bench/generator/domains/usability.py`'s module docstring).
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Iterable

from bench.generator.api import BANNED_PATH_TOKENS

SHINGLE_SIZE = 6

_TOKEN_RE = re.compile(r"\S+")
_NON_ALNUM_RE = re.compile(r"[^0-9a-z]+")
_PATH_SEGMENT_RE = re.compile(r"[/._-]+")


def _normalize_tokens(text: str) -> list[str]:
    """NFC, casefold, split on whitespace, strip non-alphanumerics from
    each token. Rule 1."""
    normalized = unicodedata.normalize("NFC", text).casefold()
    tokens: list[str] = []
    for raw in _TOKEN_RE.findall(normalized):
        stripped = _NON_ALNUM_RE.sub("", raw)
        if stripped:
            tokens.append(stripped)
    return tokens


def _shingles(tokens: list[str], n: int = SHINGLE_SIZE) -> set[tuple[str, ...]]:
    """The set of contiguous n-token shingles. Rule 2. Fewer than n tokens
    yields no shingles, the conservative direction: a description too
    short to form one 6-token run cannot be flagged by this check, but it
    also cannot claim a leak that is not there."""
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def check_description_leak(artifact_text: str, criterion: str, description: str) -> list[str]:
    """Rules 1-2: no description shingle may appear in the artifact's
    shingle set."""
    artifact_shingles = _shingles(_normalize_tokens(artifact_text))
    description_shingles = _shingles(_normalize_tokens(description))
    overlap = artifact_shingles & description_shingles
    if overlap:
        example = " ".join(sorted(overlap)[0])
        return [
            f"defect {criterion!r} description shares a {SHINGLE_SIZE}-token "
            f"shingle with the artifact text: {example!r}"
        ]
    return []


def check_criterion_id_leak(artifact_text: str, criterion: str) -> list[str]:
    """Rule 3: no criterion ID may appear anywhere in the artifact text.
    Checked case-insensitively, stricter than the rule requires and costs
    nothing: criterion IDs are uppercase by grammar, so a case-insensitive
    hit is never a false positive worth ignoring."""
    if criterion.casefold() in artifact_text.casefold():
        return [f"criterion id {criterion!r} appears in the artifact text"]
    return []


def check_path_leak(path: str, criteria: Iterable[str]) -> list[str]:
    """Rule 4: no corpus path may contain a criterion ID or any of the
    banned tokens (clean, defect, seed, plant, bug). Applied here to a full
    repository-relative corpus path (artifact or manifest); a recipe id in
    isolation is additionally checked by `Domain.validate()` before
    generation ever runs."""
    problems: list[str] = []
    lowered = path.lower()
    segments = {s for s in _PATH_SEGMENT_RE.split(lowered) if s}
    banned_hit = BANNED_PATH_TOKENS & segments
    if banned_hit:
        problems.append(f"path {path!r} contains banned token(s) {sorted(banned_hit)}")
    for criterion in criteria:
        if criterion.lower() in lowered:
            problems.append(f"path {path!r} encodes criterion {criterion!r}")
    return problems


def check_artifact(
    *,
    artifact_text: str,
    artifact_path: str,
    manifest_path: str,
    defects: Iterable[tuple[str, str]],
    domain_criteria: Iterable[str],
) -> list[str]:
    """Run every leak rule this stage of the harness checks and return
    every problem found, not just the first. `defects` is an iterable of
    `(criterion, description)` pairs, `domain_criteria` the full set of
    criterion IDs the domain registers (checked against the artifact text
    and both paths regardless of which criteria this particular recipe
    happened to plant)."""
    domain_criteria = tuple(domain_criteria)
    problems: list[str] = []
    for criterion, description in defects:
        problems.extend(check_description_leak(artifact_text, criterion, description))
    for criterion in domain_criteria:
        problems.extend(check_criterion_id_leak(artifact_text, criterion))
    problems.extend(check_path_leak(artifact_path, domain_criteria))
    problems.extend(check_path_leak(manifest_path, domain_criteria))
    return problems


def leak_check_corpus(corpus_dir: Path) -> list[str]:
    """Run the leak rules over an existing, already-written corpus, for
    `python -m bench.generator leak-check --corpus bench/corpus`. Reads
    each `<recipe>.manifest.json` under `corpus_dir` and its sibling
    artifact from disk; does not import the domain registry, so
    `domain_criteria` here is the set of criteria this artifact's own
    manifest names, not the domain's full registered roster. Returns every
    problem found, not just the first.
    """
    problems: list[str] = []
    for manifest_path in sorted(corpus_dir.rglob("*.manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        recipe_stem = manifest_path.name[: -len(".manifest.json")]
        siblings = [
            p
            for p in manifest_path.parent.iterdir()
            if p.is_file() and p.stem == recipe_stem and p != manifest_path
        ]
        if len(siblings) != 1:
            problems.append(
                f"{manifest_path}: expected exactly one sibling artifact for "
                f"recipe {recipe_stem!r}, found {len(siblings)}"
            )
            continue
        artifact_path = siblings[0]
        artifact_text = artifact_path.read_text(encoding="utf-8")
        defects = manifest.get("defects", [])
        domain_criteria = sorted({d["criterion"] for d in defects})
        pairs = [(d["criterion"], d["description"]) for d in defects]
        found = check_artifact(
            artifact_text=artifact_text,
            artifact_path=manifest.get("artifact", str(artifact_path)),
            manifest_path=str(manifest_path),
            defects=pairs,
            domain_criteria=domain_criteria,
        )
        problems.extend(f"{manifest_path}: {p}" for p in found)
    return problems
