"""Tests for critique-docs's scripts/checks.py scripted lane:
DIATAXIS-HEADING-DEPTH, DIATAXIS-MODE, DIATAXIS-NAV-LENGTH.

what-it-is:   the unit suite for this skill's scripted lane
what-it-does: exercises each DIATAXIS-* scripted check against small
              in-memory artifacts, including the fire/no-fire boundary
              for each of references/DIATAXIS.md's own "Marker registry
              and thresholds" numbers, and checks determinism both at
              the check() level and through the shared run_scripted_lane
              CLI
why:          docs/internal/skill-template.md requires pytest coverage
              of every scripted check
used-by:      `python -m pytest`, and `scripts/skill-selftest.py`'s own
              pytest check when it validates this directory

DIATAXIS-ORPHAN is not covered here: it moved to the judged lane while
scripts/checks.py was written (references/DIATAXIS.md, "Why
DIATAXIS-ORPHAN moved to the judged lane"), so it is not in
IMPLEMENTED_CRITERIA and has no scripted check to test.

The module basename carries the skill's domain (`_docs`) on purpose:
two skills shipping `scripts/tests/test_checks.py` collide at pytest
collection time and abort the whole repository run. See
`scripts/skill-selftest.py`'s `check_test_module_names`.

`critique-docs` (like every real `skills/critique-<domain>/` directory)
has a hyphen in its own directory name, so `checks.py` cannot be reached
with a normal `import` statement. It is loaded here by file path via
`importlib.util`, the same technique the template fixture's own test
module and `scripts/skill-selftest.py`'s own `_load_module` use.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from skills._shared.artifact import Artifact

_CHECKS_PATH = Path(__file__).resolve().parents[1] / "checks.py"


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())


def _load_checks_module():
    spec = importlib.util.spec_from_file_location("docs_checks_under_test", _CHECKS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checks = _load_checks_module()


def _artifact(text: str) -> Artifact:
    return Artifact(path="fixture.md", text=text, sha256="0" * 64, disk_path=Path("fixture.md"))


def _criteria(findings):
    return sorted(f.criterion for f in findings)


def _page(mode, body):
    """A markdown page, optionally carrying a "mode:" frontmatter block.
    mode=None omits frontmatter entirely."""
    if mode is None:
        return body
    return f"---\nmode: {mode}\n---\n{body}"


def _flat_list(n, heading="## Navigation"):
    items = "\n".join(f"- Item {i}" for i in range(1, n + 1))
    return f"{heading}\n\n{items}\n"


# ---------------------------------------------------------------------------
# A clean artifact: reference mode (checked against both marker groups),
# consistent heading depth, a short list. Exercises all three checks at
# once and expects nothing from any of them.
# ---------------------------------------------------------------------------

CLEAN_TEXT = _page(
    "reference",
    """# Widget configuration reference

## timeout

The timeout field accepts a duration in milliseconds. Values below 1000 are rejected by the validator.

## retries

- max_retries
- backoff_seconds
- retry_on_timeout
""",
)


def test_clean_artifact_has_no_findings():
    findings = checks.check(_artifact(CLEAN_TEXT))
    assert findings == []


# ---------------------------------------------------------------------------
# DIATAXIS-HEADING-DEPTH
# ---------------------------------------------------------------------------


def test_heading_depth_normal_progression_passes():
    text = "# Title\n\n## Section A\n\nSome text.\n\n### Subsection\n\nMore text.\n"
    findings = checks.check(_artifact(text))
    assert "DIATAXIS-HEADING-DEPTH" not in _criteria(findings)


def test_heading_depth_single_jump_is_flagged_severity_2():
    text = "# Title\n\n## Section A\n\nSome text.\n\n#### Deep subsection\n\nMore text.\n"
    findings = checks.check(_artifact(text))
    depth_findings = [f for f in findings if f.criterion == "DIATAXIS-HEADING-DEPTH"]
    assert len(depth_findings) == 1
    finding = depth_findings[0]
    assert finding.severity == 2
    assert finding.lane == "scripted"
    assert finding.confidence == "high"
    assert finding.location == "the Deep subsection heading"
    assert "jumped from 2" in finding.evidence
    assert "to 4" in finding.evidence


def test_heading_depth_two_jumps_is_severity_3_for_both():
    text = (
        "# Title\n\n"
        "## Section A\n\n#### Sub A\n\nText.\n\n"
        "## Section B\n\n#### Sub B\n\nText.\n"
    )
    findings = checks.check(_artifact(text))
    depth_findings = [f for f in findings if f.criterion == "DIATAXIS-HEADING-DEPTH"]
    assert len(depth_findings) == 2
    assert all(f.severity == 3 for f in depth_findings)


def test_heading_depth_decreasing_level_is_never_flagged():
    """Going from a deep heading back up to a shallower one is always
    fine; only a jump deeper by more than one level is a violation."""
    text = "# Title\n\n## Section A\n\n### Sub A\n\nText.\n\n## Section B\n\nText.\n"
    findings = checks.check(_artifact(text))
    assert "DIATAXIS-HEADING-DEPTH" not in _criteria(findings)


def test_heading_depth_first_heading_on_page_is_never_flagged():
    """The first heading has no preceding heading to compare against."""
    text = "#### Title starts at level 4\n\nText.\n"
    findings = checks.check(_artifact(text))
    assert "DIATAXIS-HEADING-DEPTH" not in _criteria(findings)


# ---------------------------------------------------------------------------
# DIATAXIS-NAV-LENGTH
# ---------------------------------------------------------------------------


def test_nav_length_at_threshold_passes():
    """references/DIATAXIS.md: the threshold is 7 items; exactly 7 is
    not yet a violation."""
    findings = checks.check(_artifact(_flat_list(7)))
    assert "DIATAXIS-NAV-LENGTH" not in _criteria(findings)


def test_nav_length_just_over_threshold_is_severity_2():
    findings = checks.check(_artifact(_flat_list(8)))
    nav_findings = [f for f in findings if f.criterion == "DIATAXIS-NAV-LENGTH"]
    assert len(nav_findings) == 1
    finding = nav_findings[0]
    assert finding.severity == 2
    assert finding.location == "the Navigation listing"
    assert "8 flat items" in finding.evidence


def test_nav_length_at_severity_3_boundary_is_still_severity_2():
    """references/DIATAXIS.md: severity 3 is "more than twenty flat
    items", so exactly 20 stays severity 2."""
    findings = checks.check(_artifact(_flat_list(20)))
    nav_findings = [f for f in findings if f.criterion == "DIATAXIS-NAV-LENGTH"]
    assert len(nav_findings) == 1
    assert nav_findings[0].severity == 2


def test_nav_length_over_twenty_is_severity_3():
    findings = checks.check(_artifact(_flat_list(21)))
    nav_findings = [f for f in findings if f.criterion == "DIATAXIS-NAV-LENGTH"]
    assert len(nav_findings) == 1
    assert nav_findings[0].severity == 3


def test_nav_length_with_nested_subgrouping_passes():
    """A list past the threshold with at least one nested sub-item is
    already subgrouped, so it is not flagged even though the top-level
    count alone would be over threshold."""
    text = (
        "## Navigation\n\n"
        "- Item 1\n"
        "  - Sub item 1a\n"
        "- Item 2\n- Item 3\n- Item 4\n- Item 5\n- Item 6\n- Item 7\n- Item 8\n"
    )
    findings = checks.check(_artifact(text))
    assert "DIATAXIS-NAV-LENGTH" not in _criteria(findings)


def test_nav_length_split_by_subheadings_passes():
    """A long run of items broken up by sub-headings becomes several
    separate list blocks, each under threshold on its own."""
    text = "## Group A\n\n" + "\n".join(f"- A{i}" for i in range(1, 6))
    text += "\n\n## Group B\n\n" + "\n".join(f"- B{i}" for i in range(1, 6)) + "\n"
    findings = checks.check(_artifact(text))
    assert "DIATAXIS-NAV-LENGTH" not in _criteria(findings)


def test_nav_length_two_listings_under_one_heading_get_distinguishable_locations():
    """The enclosing heading names a listing only while that heading has
    one listing under it. With two, both findings would otherwise carry
    the identical location string, which the contract's navigable-unaided
    rule does not allow."""
    text = (
        "## Navigation\n\n"
        + "\n".join(f"- A{i}" for i in range(1, 10))
        + "\n\nA paragraph between the two listings.\n\n"
        + "\n".join(f"- B{i}" for i in range(1, 10))
        + "\n"
    )
    findings = checks.check(_artifact(text))
    nav_findings = [f for f in findings if f.criterion == "DIATAXIS-NAV-LENGTH"]
    assert len(nav_findings) == 2
    locations = [f.location for f in nav_findings]
    assert len(set(locations)) == 2
    assert locations == [
        "the Navigation listing starting at line 3",
        "the Navigation listing starting at line 15",
    ]


def test_nav_length_single_listing_under_a_heading_is_named_by_the_heading_alone():
    """The disambiguating line number appears only when it is needed, so
    the common case keeps the shorter location."""
    findings = checks.check(_artifact(_flat_list(8)))
    nav_findings = [f for f in findings if f.criterion == "DIATAXIS-NAV-LENGTH"]
    assert nav_findings[0].location == "the Navigation listing"


def test_nav_length_without_a_preceding_heading_falls_back_to_line_number():
    text = _flat_list(8, heading="").lstrip("\n")
    findings = checks.check(_artifact(text))
    nav_findings = [f for f in findings if f.criterion == "DIATAXIS-NAV-LENGTH"]
    assert len(nav_findings) == 1
    assert nav_findings[0].location == "the listing starting at line 1"


# ---------------------------------------------------------------------------
# DIATAXIS-MODE
# ---------------------------------------------------------------------------


def test_mode_howto_page_flags_explanation_marker():
    body = (
        "# Configure the widget\n\n"
        "## Step 1\n\n"
        "- First, open the settings panel.\n"
        "- Because the panel loads asynchronously, wait a moment before continuing.\n"
        "- Then, click Save.\n"
    )
    findings = checks.check(_artifact(_page("how-to", body)))
    mode_findings = [f for f in findings if f.criterion == "DIATAXIS-MODE"]
    assert len(mode_findings) == 1
    finding = mode_findings[0]
    assert finding.severity == 2
    assert finding.location == "Step 1, list item 2"
    assert finding.evidence == "Because the panel loads asynchronously, wait a moment before continuing."


def test_mode_howto_page_with_only_its_own_register_passes():
    body = (
        "# Configure the widget\n\n"
        "## Step 1\n\n"
        "- First, open the settings panel.\n"
        "- Then, click Save.\n"
    )
    findings = checks.check(_artifact(_page("how-to", body)))
    assert "DIATAXIS-MODE" not in _criteria(findings)


def test_mode_reference_page_flags_action_marker():
    body = "# Config reference\n\n## timeout\n\nFirst, set the timeout value in milliseconds. The default is 30000.\n"
    findings = checks.check(_artifact(_page("reference", body)))
    mode_findings = [f for f in findings if f.criterion == "DIATAXIS-MODE"]
    assert len(mode_findings) == 1
    finding = mode_findings[0]
    assert finding.location == "timeout, paragraph 1"
    assert finding.evidence == "First, set the timeout value in milliseconds."


def test_mode_reference_page_flags_both_marker_groups():
    body = (
        "# Config reference\n\n"
        "## timeout\n\n"
        "First, set the timeout value in milliseconds.\n\n"
        "## retries\n\n"
        "Because retries compound latency, the default is kept low.\n"
    )
    findings = checks.check(_artifact(_page("reference", body)))
    mode_findings = [f for f in findings if f.criterion == "DIATAXIS-MODE"]
    assert len(mode_findings) == 2
    assert all(f.severity == 3 for f in mode_findings)  # recurrence: two on one page


def test_mode_undeclared_produces_no_mode_findings():
    """No frontmatter at all: the page has no declared mode, so
    DIATAXIS-MODE is not evaluated, even though the sentence below would
    trip an explanation marker on a declared how-to page."""
    body = "# Configure the widget\n\nBecause the setting is sensitive, confirm before saving.\n"
    findings = checks.check(_artifact(_page(None, body)))
    assert "DIATAXIS-MODE" not in _criteria(findings)


def test_mode_unrecognized_declared_value_produces_no_findings():
    body = "# Configure the widget\n\nBecause the setting is sensitive, confirm before saving.\n"
    findings = checks.check(_artifact(_page("potato", body)))
    assert "DIATAXIS-MODE" not in _criteria(findings)


def test_mode_alias_is_normalized():
    """"howto" (no hyphen) is a recognized alias for "how-to"."""
    body = "# Configure the widget\n\nBecause the setting is sensitive, confirm before saving.\n"
    findings = checks.check(_artifact(_page("howto", body)))
    assert "DIATAXIS-MODE" in _criteria(findings)


def test_mode_marker_uses_word_boundaries_not_substrings():
    """"Becausement" (not a real word, chosen to isolate the boundary
    check) must not match the "because" marker."""
    body = "# Configure the widget\n\nBecausement is not a real opening word here.\n"
    findings = checks.check(_artifact(_page("how-to", body)))
    assert "DIATAXIS-MODE" not in _criteria(findings)


# ---------------------------------------------------------------------------
# Empty / degenerate artifacts
# ---------------------------------------------------------------------------


def test_empty_artifact_has_no_findings():
    findings = checks.check(_artifact(""))
    assert findings == []


def test_whitespace_only_artifact_has_no_findings():
    findings = checks.check(_artifact("   \n\n   \n"))
    assert findings == []


# ---------------------------------------------------------------------------
# Multiple defects together
# ---------------------------------------------------------------------------


def test_multiple_defects_in_one_artifact_are_all_reported():
    body = (
        "# Configure the widget\n\n"
        "## Step 1\n\n"
        "#### Too deep\n\n"
        "Because this is here, the mode marker also fires.\n\n"
        + "\n".join(f"- Item {i}" for i in range(1, 9))
        + "\n"
    )
    findings = checks.check(_artifact(_page("how-to", body)))
    assert _criteria(findings) == [
        "DIATAXIS-HEADING-DEPTH",
        "DIATAXIS-MODE",
        "DIATAXIS-NAV-LENGTH",
    ]


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_check_is_deterministic_across_repeated_calls():
    """S-04 spec: checks.py MUST be deterministic, same artifact, same
    output. RawFinding is a frozen dataclass, so list equality compares
    every field."""
    artifact = _artifact(_flat_list(21))
    first = checks.check(artifact)
    second = checks.check(artifact)
    assert first == second


def test_full_scripted_lane_is_deterministic_via_run_scripted_lane(tmp_path, monkeypatch):
    """The same determinism claim, exercised through the shared CLI body
    (skills/_shared/runner.run_scripted_lane) rather than check() alone,
    mirroring skills/_shared/tests/test_runner.py::
    test_same_artifact_twice_produces_identical_findings_and_summary.
    run.timestamp is excluded from the comparison, per
    docs/internal/skill-template.md, "What determinism does and does not
    cover"."""
    import contextlib
    import io

    target = tmp_path / "doc.md"
    target.write_text(_flat_list(21), encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    def run_once():
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            checks.main([str(target)])
        return json.loads(buf.getvalue())

    first = run_once()
    second = run_once()

    assert first["findings"] == second["findings"]
    assert first["summary"] == second["summary"]
    assert first["run"]["skill"] == "critique-docs"
    assert first["run"]["rubrics"] == ["DIATAXIS"]


def test_gate_exits_two_for_a_severity_3_finding_at_default_threshold(tmp_path, monkeypatch):
    target = tmp_path / "doc.md"
    target.write_text(_flat_list(21), encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    code = checks.main([str(target), "--gate"])

    assert code == 2


def test_gate_exits_zero_for_a_clean_artifact(tmp_path, monkeypatch):
    target = tmp_path / "doc.md"
    target.write_text(CLEAN_TEXT, encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    code = checks.main([str(target), "--gate"])

    assert code == 0
