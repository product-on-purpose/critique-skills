# what-it-is:   the structural guard on the joint-routing eval fixture
# what-it-does: validates evals/joint-routing.eval.json's shape and asserts every contested sibling
#               pair carries a boundary clause in BOTH descriptions naming the other skill
# why:          six sibling skills in one namespace collide on triggering, and nothing else in the
#               pipeline compares two descriptions to each other; this holds the fix in place
# used-by:      python -m pytest (the CI unit-python job)
"""Tests the joint-routing eval fixture and the description boundaries it depends on.

Scope, stated plainly: this file does **not** measure routing. Routing is a
model decision over descriptions in context, and a lexical proxy scored in CI
would measure string overlap rather than routing. This library does not
publish numbers produced by a mechanism other than the one being described,
so the measurement stays a dispatch-only job (see the fixture's ``scoring``
block) and this file guards the two things that can be checked
deterministically:

1. The fixture is well formed and every skill it names exists.
2. For every contested pair, both siblings' descriptions carry a boundary
   clause naming the other. That is what makes the pair separable at all; it
   was added after an external review found the pairs indistinguishable, and
   without a test it would rot the next time a description is edited.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "evals" / "joint-routing.eval.json"
VALID_KINDS = {"contested", "ambiguous", "control"}


@pytest.fixture(scope="module")
def eval_data() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _description(skill: str) -> str:
    text = (REPO_ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"^description:\s*(.+)$", text, re.M)
    assert match, f"{skill}/SKILL.md has no single-line description in its frontmatter"
    return match.group(1)


def test_every_named_skill_exists(eval_data: dict) -> None:
    for skill in eval_data["skills"]:
        assert (REPO_ROOT / "skills" / skill / "SKILL.md").is_file(), f"no such skill: {skill}"


def test_the_fixture_covers_every_skill(eval_data: dict) -> None:
    """A fixture that silently drops a skill would leave that skill's collisions untested."""
    on_disk = {p.parent.name for p in REPO_ROOT.glob("skills/critique-*/SKILL.md")}
    assert set(eval_data["skills"]) == on_disk, "fixture skill list and skills/ disagree"


def test_cases_are_well_formed(eval_data: dict) -> None:
    known = set(eval_data["skills"])
    assert eval_data["cases"], "fixture has no cases"
    for case in eval_data["cases"]:
        query, kind = case.get("query"), case.get("kind")
        assert query, "every case needs a query"
        assert kind in VALID_KINDS, f"{query!r}: kind must be one of {sorted(VALID_KINDS)}"
        assert case.get("rationale"), f"{query!r}: every case must say why its answer is right"

        if kind == "ambiguous":
            acceptable = case.get("acceptable") or []
            assert len(acceptable) >= 2, (
                f"{query!r}: an ambiguous case needs at least two acceptable skills, "
                "otherwise it is a contested or control case mislabelled"
            )
            assert set(acceptable) <= known, f"{query!r}: unknown skill in acceptable"
            assert "expected" not in case, (
                f"{query!r}: an ambiguous case must not name a single expected winner"
            )
        else:
            assert case.get("expected") in known, f"{query!r}: expected must name a real skill"
            if kind == "contested":
                contested = case.get("contested_with") or []
                assert contested, f"{query!r}: a contested case must name what it is contested with"
                assert set(contested) <= known, f"{query!r}: unknown skill in contested_with"
                assert case["expected"] not in contested, (
                    f"{query!r}: a case cannot be contested with its own expected winner"
                )


def test_every_contested_case_maps_to_a_declared_boundary_pair(eval_data: dict) -> None:
    declared = {frozenset(p["pair"]) for p in eval_data["boundary_pairs"]}
    for case in eval_data["cases"]:
        if case["kind"] != "contested":
            continue
        for other in case["contested_with"]:
            pair = frozenset({case["expected"], other})
            assert pair in declared, (
                f"{case['query']!r}: {sorted(pair)} is contested but not declared in boundary_pairs"
            )


@pytest.mark.parametrize(
    "pair",
    [
        ("critique-argument", "critique-clarity"),
        ("critique-microcopy", "critique-usability"),
    ],
    ids=lambda p: f"{p[0]}-vs-{p[1]}",
)
def test_contested_pairs_name_each_other_in_their_descriptions(pair: tuple[str, str]) -> None:
    """Each sibling must state, in its own description, what it does not cover.

    A boundary stated only in the SKILL.md body cannot inform routing: the body
    is not loaded until after a skill has already been selected.
    """
    left, right = pair
    for skill, sibling in ((left, right), (right, left)):
        description = _description(skill)
        assert sibling in description, (
            f"{skill}'s description must name {sibling} so the two are separable at trigger time; "
            "a boundary in the SKILL.md body is read only after selection has already happened"
        )


def test_accessibility_and_docs_no_longer_share_the_heading_structure_bigram() -> None:
    """The two meant different things by one identical phrase, and routing saw only the string."""
    accessibility = _description("critique-accessibility")
    assert "heading structure" not in accessibility, (
        "critique-accessibility shared the literal phrase 'heading structure' with critique-docs "
        "while meaning semantic hierarchy for assistive technology, not Diataxis heading depth"
    )
    assert "screen readers" in accessibility, "it should say what the hierarchy is actually for"


def test_scoring_status_is_declared_honestly(eval_data: dict) -> None:
    """The fixture must not imply it has been scored when it has not."""
    scoring = eval_data["scoring"]
    assert scoring["status"] in {"not-yet-run", "scored"}
    assert scoring["mechanism"] == "model"
    if scoring["status"] == "not-yet-run":
        assert "results" not in eval_data, "an unscored fixture must publish no results"
