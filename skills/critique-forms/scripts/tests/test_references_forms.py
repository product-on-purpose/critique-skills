"""Tests that critique-forms' criterion table cites the registry's sources faithfully.

what-it-is:   the AC-2 and AC-4 check for `references/FORMS.md`
what-it-does: parses every row's Sources list, and checks it against the
              committed bibliography (every handle resolves) and against
              the criterion registry's evidence paragraphs (every source
              the registry lists is cited, nothing is added unannounced,
              and every grade the registry states is the grade cited)
why:          the N2 (critique-forms) spec, AC-2, says the self-test checks
              neither citation granularity nor citations themselves, so
              AC-2 is verified "by review or by a script over the rows and
              the bibliography". This is that script, made permanent so a
              later edit to the table cannot drift from the research record
used-by:      `python -m pytest`, and `scripts/skill-selftest.py`'s own
              pytest check when it validates this directory

The two research files live with the effort's spec. If the effort folder
moves (a release plan promotes it out of `_unassigned/`), this module's
`EFFORT_DIR` and the links in `references/FORMS.md` move with it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = SKILL_DIR.parents[1]
EFFORT_DIR = REPO_ROOT / "docs" / "internal" / "release-plans" / "_unassigned" / "N2_critique-forms"
FORMS_MD = SKILL_DIR / "references" / "FORMS.md"
SOURCES_MD = EFFORT_DIR / "sources.md"
REGISTRY_MD = EFFORT_DIR / "criterion-registry-draft.md"

GRADES = ("PR", "LS", "AB", "US", "OG", "EX", "AN")

# The 24 ruled criteria and their lanes, from the spec's Requirements 1.
RULED = {
    "FORMS-INPUT-TYPE": "scripted",
    "FORMS-NUMERIC-INPUTMODE": "scripted",
    "FORMS-AUTOCOMPLETE": "scripted",
    "FORMS-AUTOCORRECT": "scripted",
    "FORMS-PLACEHOLDER-INSTRUCTION": "scripted",
    "FORMS-REQUIRED-OPTIONAL": "scripted",
    "FORMS-SPLIT-ENTITY": "scripted",
    "FORMS-FIELD-WIDTH": "scripted",
    "FORMS-FORMAT-TOLERANCE": "scripted",
    "FORMS-PASSWORD-RULES": "scripted",
    "FORMS-CONFIRM-PASSWORD": "scripted",
    "FORMS-ACTION-LABEL": "scripted",
    "FORMS-RESET-BUTTON": "scripted",
    "FORMS-INPUT-FONT-SIZE": "scripted",
    "FORMS-OPTION-CONTROL": "scripted",
    "FORMS-DATE-SELECTS": "scripted",
    "FORMS-PHONE-REASON": "scripted",
    "FORMS-ADDRESS-FORMAT": "scripted",
    "FORMS-FIELD-NECESSITY": "judged",
    "FORMS-SINGLE-COLUMN": "judged",
    "FORMS-LABEL-POSITION": "judged",
    "FORMS-ACTION-HIERARCHY": "judged",
    "FORMS-SELECTION-DEPENDENT": "judged",
    "FORMS-TOUCH-TARGET": "judged",
}

# Handles the registry names in a criterion's paragraph only to explain an
# exclusion, not as evidence for the criterion. Each entry says why.
REGISTRY_CONTEXT_ONLY = {
    # Paragraph 11 names it among the sources against confirm-email, which the
    # registry excludes from the criterion.
    ("FORMS-CONFIRM-PASSWORD", "silver-58-form-design-ux-best-practices"),
}

# Sources a row cites that its registry paragraph counts without naming.
ROW_ADDITIONS = {
    # Paragraph 7: "EX: three practitioner articles." These are the three
    # research-stream notes on splitting one value across several inputs.
    ("FORMS-SPLIT-ENTITY", "silver-58-form-design-ux-best-practices"),
    ("FORMS-SPLIT-ENTITY", "silver-form-design-principles-cxl"),
    ("FORMS-SPLIT-ENTITY", "silver-form-ui-design-designlab"),
}

# Handles that fail the bibliography's URL-or-ISBN rule; no row may cite them.
UNCITABLE = {"ciotti-conversion-psychology", "hoober-berkman-mobile-interfaces-2011"}

BOOK_ALIASES = (
    (re.compile(r"\bSilver pp?\. \d"), "silver-form-design-patterns"),
    (re.compile(r"\bWroblewski pp?\. \d"), "wroblewski-web-form-design"),
)


def _table_rows(text: str) -> list[list[str]]:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| ID | Operationalization |"))
    rows = []
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        rows.append([cell.strip() for cell in line.strip().strip("|").split(" | ")])
    return rows


def _bibliography_handles() -> set[str]:
    handles = set()
    for line in SOURCES_MD.read_text(encoding="utf-8").splitlines():
        if line.startswith("| `"):
            first_cell = line.split("|")[1]
            handles.update(re.findall(r"`([a-z0-9-]+)`", first_cell))
    return handles


def _graded_handles(text: str, known: set[str]) -> list[tuple[str, str | None]]:
    """Walk text in order, pairing each known handle with the grade in force.

    A grade is in force from a grade token followed by a colon, a comma, the
    word `with` (the registry's prose) or a backticked handle (the table's
    lists) until the end of its sentence. A sentence ends at a full stop
    followed by a space and anything other than a digit, so `p. 34` does not
    end one.
    """
    token = re.compile(
        r"\b(" + "|".join(GRADES) + r")\b(?=:|,| with | `)"
        r"|`([a-z0-9-]+)`"
        r"|(\bSilver pp?\. \d|\bWroblewski pp?\. \d)"
        r"|(\.\s+(?!\d))"
    )
    grade: str | None = None
    found: list[tuple[str, str | None]] = []
    for match in token.finditer(text):
        g, handle, book, stop = match.groups()
        if stop:
            grade = None
        elif g:
            grade = g
        elif handle and handle in known:
            found.append((handle, grade))
        elif book:
            for pattern, alias in BOOK_ALIASES:
                if pattern.match(book):
                    found.append((alias, grade))
    return found


def _registry_paragraphs() -> dict[str, str]:
    text = REGISTRY_MD.read_text(encoding="utf-8")
    section = text.split("## Evidence per criterion", 1)[1].split("\n## ", 1)[0]
    paragraphs: dict[str, str] = {}
    current = None
    for line in section.splitlines():
        start = re.match(r"\s*\d+\. \*\*`(FORMS-[A-Z-]+)`\.\*\*(.*)", line)
        if start:
            current = start.group(1)
            paragraphs[current] = start.group(2)
        elif current and line.strip():
            paragraphs[current] += " " + line.strip()
    return paragraphs


def _first_grades(pairs: list[tuple[str, str | None]]) -> dict[str, str | None]:
    """Each handle's grade at its first graded mention, or None if never graded."""
    grades: dict[str, str | None] = {}
    for handle, grade in pairs:
        if grades.get(handle) is None:
            grades[handle] = grade
    return grades


@pytest.fixture(scope="module")
def rows() -> dict[str, list[str]]:
    return {row[0]: row for row in _table_rows(FORMS_MD.read_text(encoding="utf-8"))}


@pytest.fixture(scope="module")
def bibliography() -> set[str]:
    return _bibliography_handles()


def _row_citations(row: list[str], known: set[str]) -> dict[str, str | None]:
    sources = row[1].split("Sources:", 1)[1]
    return _first_grades(_graded_handles(sources, known))


def test_the_table_declares_exactly_the_ruled_criteria_in_their_lanes(rows):
    assert {row_id: row[5] for row_id, row in rows.items()} == RULED


def test_rows_are_in_ascending_id_order():
    ids = [row[0] for row in _table_rows(FORMS_MD.read_text(encoding="utf-8"))]
    assert ids == sorted(ids)


def test_every_row_has_seven_cells_and_a_sources_list(rows):
    for row_id, row in rows.items():
        assert len(row) == 7, row_id
        assert "Sources:" in row[1], row_id


def test_every_cited_handle_resolves_in_the_bibliography(rows, bibliography):
    every_backticked = set()
    for row in rows.values():
        every_backticked.update(re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`", row[1].split("Sources:", 1)[1]))
    assert every_backticked <= bibliography, sorted(every_backticked - bibliography)
    assert not every_backticked & UNCITABLE


def test_every_citation_carries_a_grade(rows, bibliography):
    for row_id, row in rows.items():
        cited = _row_citations(row, bibliography)
        assert cited, row_id
        assert all(grade in GRADES for grade in cited.values()), (row_id, cited)


def test_each_row_cites_what_its_registry_paragraph_cites(rows, bibliography):
    paragraphs = _registry_paragraphs()
    assert set(paragraphs) == set(RULED)
    for row_id, row in rows.items():
        registry = set(_first_grades(_graded_handles(paragraphs[row_id], bibliography)))
        registry -= {h for c, h in REGISTRY_CONTEXT_ONLY if c == row_id}
        cited = set(_row_citations(row, bibliography))
        additions = {h for c, h in ROW_ADDITIONS if c == row_id}
        assert registry <= cited, (row_id, sorted(registry - cited))
        assert cited <= registry | additions, (row_id, sorted(cited - registry - additions))


def test_each_citation_carries_the_grade_its_registry_paragraph_states(rows, bibliography):
    paragraphs = _registry_paragraphs()
    for row_id, row in rows.items():
        registry = _first_grades(_graded_handles(paragraphs[row_id], bibliography))
        cited = _row_citations(row, bibliography)
        for handle, grade in registry.items():
            if grade is not None and handle in cited:
                assert cited[handle] == grade, (row_id, handle, grade, cited[handle])


def test_the_two_overlap_rows_name_their_wcag_criterion(rows):
    assert "WCAG 1.3.5" in rows["FORMS-AUTOCOMPLETE"][2]
    assert "WCAG 2.5.8" in rows["FORMS-TOUCH-TARGET"][2]
