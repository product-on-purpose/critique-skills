"""Tests that this skill's registry and its list of unchecked criteria account for all of WCAG 2.2
Level A and AA, with nothing counted twice and nothing missing.

what-it-is:   the coverage guard for critique-accessibility's scope statement
what-it-does: reads the 27 registered criteria from SKILL.md's checks.scripted and checks.judged,
              and the unchecked criteria from references/WCAG.md's "The 28 criteria this skill
              does not check" table, and asserts the two sets are disjoint and together equal the
              55 Level A and AA success criteria of the WCAG 2.2 Recommendation
why:          until 2026-10-15 the scope statement claimed A and AA coverage while 29 criteria
              were never mentioned anywhere (E68, narrow the accessibility scope claim). When a
              criterion joins the registry (E67, the static-markup expansion), this test fails
              until it also leaves the unchecked list, so the two cannot drift apart again
used-by:      `python -m pytest`
"""

from __future__ import annotations

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
SKILL_MD = SKILL_DIR / "SKILL.md"
WCAG_MD = SKILL_DIR / "references" / "WCAG.md"
UNCHECKED_HEADING = "### The 28 criteria this skill does not check"

# Every Level A and AA success criterion in the WCAG 2.2 W3C Recommendation,
# https://www.w3.org/TR/WCAG22/, checked against its text on 2026-10-15: 31 at A and 24 at AA.
# 4.1.1 Parsing is obsolete in 2.2 and is not listed.
WCAG22_LEVEL_A = {
    "1.1.1", "1.2.1", "1.2.2", "1.2.3", "1.3.1", "1.3.2", "1.3.3", "1.4.1", "1.4.2",
    "2.1.1", "2.1.2", "2.1.4", "2.2.1", "2.2.2", "2.3.1", "2.4.1", "2.4.2", "2.4.3", "2.4.4",
    "2.5.1", "2.5.2", "2.5.3", "2.5.4", "3.1.1", "3.2.1", "3.2.2", "3.2.6", "3.3.1", "3.3.2",
    "3.3.7", "4.1.2",
}
WCAG22_LEVEL_AA = {
    "1.2.4", "1.2.5", "1.3.4", "1.3.5", "1.4.3", "1.4.4", "1.4.5", "1.4.10", "1.4.11", "1.4.12",
    "1.4.13", "2.4.5", "2.4.6", "2.4.7", "2.4.11", "2.5.7", "2.5.8", "3.1.2", "3.2.3", "3.2.4",
    "3.3.3", "3.3.4", "3.3.8", "4.1.3",
}
REACH_VALUES = {"Out of reach", "Checkable, not implemented", "Partly checkable, not implemented"}


def _registry() -> set[str]:
    frontmatter = SKILL_MD.read_text(encoding="utf-8").split("---", 2)[1]
    return set(re.findall(r"^\s+-\s+WCAG-(\d+\.\d+\.\d+)\s*$", frontmatter, re.M))


def _unchecked_rows() -> list[list[str]]:
    text = WCAG_MD.read_text(encoding="utf-8")
    assert UNCHECKED_HEADING in text, f"references/WCAG.md has no '{UNCHECKED_HEADING}' section"
    section = text.split(UNCHECKED_HEADING, 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if re.fullmatch(r"\d+\.\d+\.\d+", cells[0]):
            rows.append(cells)
    return rows


def test_the_reference_set_is_the_whole_of_wcag22_a_and_aa() -> None:
    assert len(WCAG22_LEVEL_A) == 31
    assert len(WCAG22_LEVEL_AA) == 24
    assert not WCAG22_LEVEL_A & WCAG22_LEVEL_AA


def test_the_registry_is_27_criteria_all_inside_a_and_aa() -> None:
    registry = _registry()
    assert len(registry) == 27
    assert registry <= WCAG22_LEVEL_A | WCAG22_LEVEL_AA


def test_registry_and_unchecked_list_are_disjoint_and_cover_all_55() -> None:
    registry = _registry()
    unchecked = [row[0] for row in _unchecked_rows()]
    assert len(unchecked) == len(set(unchecked)), "a criterion is listed twice as unchecked"
    assert not registry & set(unchecked), f"listed as unchecked but registered: {sorted(registry & set(unchecked))}"
    missing = (WCAG22_LEVEL_A | WCAG22_LEVEL_AA) - registry - set(unchecked)
    assert not missing, f"neither registered nor listed as unchecked: {sorted(missing)}"
    assert len(registry) + len(unchecked) == 55


def test_the_heading_count_matches_the_table() -> None:
    count = int(re.search(r"The (\d+) criteria", UNCHECKED_HEADING).group(1))
    assert count == len(_unchecked_rows())


def test_each_unchecked_row_has_its_true_level_a_reach_and_a_reason() -> None:
    for number, _name, level, reach, reason in _unchecked_rows():
        expected = "A" if number in WCAG22_LEVEL_A else "AA"
        assert level == expected, f"{number} is Level {expected} in WCAG 2.2, not {level}"
        assert reach in REACH_VALUES, f"{number} has an unknown reach value: {reach}"
        assert reason, f"{number} gives no reason"
        assert '"' not in reason, f"{number}'s reason carries a quotation mark (ADR 0006 paraphrase policy)"
