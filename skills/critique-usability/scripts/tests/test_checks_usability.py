"""Tests for critique-usability's scripts/checks.py scripted lane:
NNG-H3-DEADEND, NNG-H4-CONTROL-NAMING, NNG-H6-LABELED.

what-it-is:   the unit suite for this skill's scripted lane
what-it-does: exercises each NNG-H* scripted check, in both the HTML and
              markdown grammars checks.py documents, against small
              in-memory artifacts: a triggering case, a clean case, and
              the edge cases each check's own logic carries (self-loops,
              undefined link targets, the instances-array minItems-2
              boundary, container-severity boundaries), plus determinism
              both at the check() level and through the shared
              run_scripted_lane CLI
why:          docs/internal/skill-template.md requires pytest coverage of
              every scripted check
used-by:      `python -m pytest`, and `scripts/skill-selftest.py`'s own
              pytest check when it validates this directory

The module basename carries the skill's domain (`_usability`) on purpose:
two skills shipping `scripts/tests/test_checks.py` collide at pytest
collection time and abort the whole repository run. See
`scripts/skill-selftest.py`'s `check_test_module_names`.

`critique-usability` (like every real `skills/critique-<domain>/`
directory) has a hyphen in its own directory name, so `checks.py` cannot
be reached with a normal `import` statement. It is loaded here by file
path via `importlib.util`, the same technique the template fixture's own
test module and `scripts/skill-selftest.py`'s own `_load_module` use.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
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
    spec = importlib.util.spec_from_file_location("usability_checks_under_test", _CHECKS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checks = _load_checks_module()

FIXED_NOW = lambda: datetime(2026, 7, 31, 9, 0, 0, tzinfo=timezone.utc)  # noqa: E731


def _artifact(text: str, path: str = "fixture.html") -> Artifact:
    return Artifact(path=path, text=text, sha256="0" * 64, disk_path=Path(path))


def _criteria(findings):
    return sorted(f.criterion for f in findings)


def _only(findings, criterion):
    return [f for f in findings if f.criterion == criterion]


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------


def test_looks_like_html_true_for_a_leading_tag():
    assert checks._looks_like_html("<html><body></body></html>")
    assert checks._looks_like_html("   \n<section id=\"a\"></section>")


def test_looks_like_html_false_for_markdown():
    assert not checks._looks_like_html("# Title\n\nSome prose.")
    assert not checks._looks_like_html("")
    assert not checks._looks_like_html("   \n  ")


# ---------------------------------------------------------------------------
# NNG-H3-DEADEND, HTML
# ---------------------------------------------------------------------------

HTML_TWO_STATES_CLEAN = """
<html><body>
<section id="dashboard">
<h2>Dashboard</h2>
<a href="#settings">Settings</a>
</section>
<section id="settings">
<h2>Settings</h2>
<a href="#dashboard">Back</a>
</section>
</body></html>
"""


def test_deadend_html_clean_two_state_flow_has_no_finding():
    findings = checks.check(_artifact(HTML_TWO_STATES_CLEAN))
    assert "NNG-H3-DEADEND" not in _criteria(findings)


def test_deadend_html_single_section_is_not_flagged():
    """One <section id=...> wrapping an entire single-screen mockup is one
    screen, not a multi-state flow with an exitless screen. Flagging it
    would be a false positive on an extremely ordinary page shape."""
    text = """
    <html><body>
    <section id="only">
    <button>Save</button>
    </section>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    assert findings == []


def test_deadend_html_no_sections_at_all_is_not_flagged():
    findings = checks.check(_artifact("<html><body><p>Hello</p></body></html>"))
    assert findings == []


def test_deadend_html_reachable_dead_end_is_severity_3():
    text = """
    <html><body>
    <section id="dashboard">
    <a href="#trap">Go</a>
    </section>
    <section id="trap">
    <p>No way out.</p>
    </section>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    dead_ends = _only(findings, "NNG-H3-DEADEND")
    assert len(dead_ends) == 1
    assert dead_ends[0].severity == 3
    assert dead_ends[0].location == 'the "trap" section'
    assert dead_ends[0].lane == "scripted"
    assert dead_ends[0].confidence == "high"


def test_deadend_html_unreachable_dead_end_is_severity_2():
    text = """
    <html><body>
    <section id="dashboard">
    <a href="#dashboard">Refresh</a>
    </section>
    <section id="orphan">
    <p>Nothing links here, and this links nowhere.</p>
    </section>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    dead_ends = {f.location: f for f in _only(findings, "NNG-H3-DEADEND")}
    assert 'the "orphan" section' in dead_ends
    assert dead_ends['the "orphan" section'].severity == 2


def test_deadend_html_self_link_does_not_count_as_an_exit():
    text = """
    <html><body>
    <section id="a">
    <a href="#a">Refresh this screen</a>
    </section>
    <section id="b">
    <a href="#a">Go to a</a>
    </section>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    dead_ends = {f.location: f for f in _only(findings, "NNG-H3-DEADEND")}
    assert 'the "a" section' in dead_ends
    assert dead_ends['the "a" section'].severity == 3  # b links into it


def test_deadend_html_link_to_undefined_target_does_not_count_as_an_exit():
    text = """
    <html><body>
    <section id="a">
    <a href="#does-not-exist">Go</a>
    </section>
    <section id="b">
    <a href="#a">Back</a>
    </section>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    dead_ends = {f.location: f for f in _only(findings, "NNG-H3-DEADEND")}
    assert 'the "a" section' in dead_ends


# ---------------------------------------------------------------------------
# NNG-H3-DEADEND, markdown
# ---------------------------------------------------------------------------

MD_TWO_STATES_CLEAN = """# Title

## Dashboard

[Go to settings](#settings)

## Settings

[Back to dashboard](#dashboard)
"""


def test_deadend_markdown_clean_two_state_flow_has_no_finding():
    findings = checks.check(_artifact(MD_TWO_STATES_CLEAN, path="fixture.md"))
    assert "NNG-H3-DEADEND" not in _criteria(findings)


def test_deadend_markdown_single_state_is_not_flagged():
    text = "# Title\n\n## Only screen\n\nNo links anywhere.\n"
    findings = checks.check(_artifact(text, path="fixture.md"))
    assert findings == []


def test_deadend_markdown_reachable_dead_end_is_severity_3():
    text = """# Title

## Dashboard

[Go](#trap)

## Trap

No way out.
"""
    findings = checks.check(_artifact(text, path="fixture.md"))
    dead_ends = _only(findings, "NNG-H3-DEADEND")
    assert len(dead_ends) == 1
    assert dead_ends[0].severity == 3
    assert dead_ends[0].location == 'the "Trap" state'


def test_deadend_markdown_unreachable_dead_end_is_severity_2():
    text = """# Title

## Dashboard

[Refresh](#dashboard)

## Orphan

Nothing links here, and this links nowhere.
"""
    findings = checks.check(_artifact(text, path="fixture.md"))
    dead_ends = {f.location: f for f in _only(findings, "NNG-H3-DEADEND")}
    assert 'the "Orphan" state' in dead_ends
    assert dead_ends['the "Orphan" state'].severity == 2


def test_deadend_markdown_subsection_content_counts_toward_its_h2_state():
    """A level-3 heading's content belongs to its enclosing level-2 state,
    so a link inside the subsection is an exit for the ## state."""
    text = """# Title

## Dashboard

### Filters

[Go to settings](#settings)

## Settings

[Back](#dashboard)
"""
    findings = checks.check(_artifact(text, path="fixture.md"))
    assert "NNG-H3-DEADEND" not in _criteria(findings)


def test_deadend_markdown_duplicate_heading_slugs_get_github_style_suffixes():
    """Two "## Step" headings slugify to "step" and "step-1", matching
    GitHub's own anchor-collision numbering, so a hand-written link against
    either heading still resolves to the right state."""
    text = """# Title

## Step

[Next](#step-1)

## Step

[Back](#step)
"""
    findings = checks.check(_artifact(text, path="fixture.md"))
    assert "NNG-H3-DEADEND" not in _criteria(findings)


# ---------------------------------------------------------------------------
# NNG-H4-CONTROL-NAMING, HTML
# ---------------------------------------------------------------------------


def test_control_naming_html_consistent_label_has_no_finding():
    text = """
    <html><body>
    <section id="a"><button>Save</button></section>
    <section id="b"><button>Save</button></section>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    assert "NNG-H4-CONTROL-NAMING" not in _criteria(findings)


def test_control_naming_html_two_distinct_commit_labels_is_severity_2_and_two_findings():
    """Exactly two occurrences cannot use the instances array (contract
    minItems 2 on further locations), so this is two separate findings,
    not one finding with an instance list."""
    text = """
    <html><body>
    <section id="a"><button>Save</button></section>
    <section id="b"><button>Apply changes</button></section>
    </body></html>
    """
    findings = _only(checks.check(_artifact(text)), "NNG-H4-CONTROL-NAMING")
    assert len(findings) == 2
    assert {f.severity for f in findings} == {2}
    assert all(f.instances == () for f in findings)
    locations = {f.location for f in findings}
    assert len(locations) == 2


def test_control_naming_html_three_distinct_commit_labels_is_severity_3_with_instances():
    text = """
    <html><body>
    <section id="a">
    <button>Save</button>
    <button>Apply</button>
    <button>Submit</button>
    </section>
    </body></html>
    """
    findings = _only(checks.check(_artifact(text)), "NNG-H4-CONTROL-NAMING")
    assert len(findings) == 1
    assert findings[0].severity == 3
    assert len(findings[0].instances) == 2


def test_control_naming_html_cancel_set_flagged_independently_of_commit_set():
    text = """
    <html><body>
    <section id="a">
    <button>Save</button>
    <button>Cancel</button>
    <button>Close</button>
    </section>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    naming = _only(findings, "NNG-H4-CONTROL-NAMING")
    # Commit set has only one distinct member (Save), so it is not flagged.
    # Cancel set has two distinct members (Cancel, Close): exactly two
    # occurrences cannot use the instances array, so this is two findings.
    assert len(naming) == 2
    assert all("cancel" in f.violation for f in naming)


def test_control_naming_html_back_set_flagged():
    text = """
    <html><body>
    <section id="a">
    <a href="#b">Back</a>
    </section>
    <section id="b">
    <a href="#a">Previous</a>
    </section>
    </body></html>
    """
    findings = _only(checks.check(_artifact(text)), "NNG-H4-CONTROL-NAMING")
    assert len(findings) == 2
    assert all("back" in f.violation for f in findings)


def test_control_naming_html_comparison_is_case_insensitive_and_ignores_ellipsis_and_punctuation():
    text = """
    <html><body>
    <section id="a"><button>save</button></section>
    <section id="b"><button>SAVE...</button></section>
    <section id="c"><button>"Save."</button></section>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    assert "NNG-H4-CONTROL-NAMING" not in _criteria(findings)  # all one canonical member: "save"


def test_control_naming_html_unrelated_labels_are_not_flagged():
    text = """
    <html><body>
    <section id="a">
    <button>Export report</button>
    <button>Import data</button>
    </section>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    assert "NNG-H4-CONTROL-NAMING" not in _criteria(findings)


def test_control_naming_html_menuitem_role_without_nested_link_is_counted():
    text = """
    <html><body>
    <section id="a">
    <ul role="menu">
    <li role="menuitem">Save</li>
    <li role="menuitem">Apply</li>
    </ul>
    </section>
    </body></html>
    """
    findings = _only(checks.check(_artifact(text)), "NNG-H4-CONTROL-NAMING")
    assert len(findings) == 2


def test_control_naming_html_menuitem_with_nested_link_is_not_double_counted():
    """A role=menuitem wrapping an <a> is counted once, via the <a>, not
    again via the menuitem wrapper; otherwise every menu link would report
    two occurrences of the same label."""
    text = """
    <html><body>
    <section id="a">
    <ul role="menu">
    <li role="menuitem"><a href="#a">Save</a></li>
    <li role="menuitem"><a href="#a">Apply</a></li>
    </ul>
    </section>
    </body></html>
    """
    findings = _only(checks.check(_artifact(text)), "NNG-H4-CONTROL-NAMING")
    assert len(findings) == 2  # two occurrences total (one per <a>), not four


# ---------------------------------------------------------------------------
# NNG-H4-CONTROL-NAMING, markdown
# ---------------------------------------------------------------------------


def test_control_naming_markdown_consistent_label_has_no_finding():
    text = "# Title\n\n[Save](#a)\n\n[Save](#b)\n"
    findings = checks.check(_artifact(text, path="fixture.md"))
    assert "NNG-H4-CONTROL-NAMING" not in _criteria(findings)


def test_control_naming_markdown_two_distinct_commit_labels_is_flagged():
    text = "# Title\n\n[Save](#a)\n\n[Apply changes](#b)\n"
    findings = _only(checks.check(_artifact(text, path="fixture.md")), "NNG-H4-CONTROL-NAMING")
    assert len(findings) == 2
    assert all(f.severity == 2 for f in findings)


def test_control_naming_markdown_location_names_enclosing_heading():
    text = "# Title\n\n## Settings\n\n[Save](#a)\n\n[Apply](#b)\n"
    findings = _only(checks.check(_artifact(text, path="fixture.md")), "NNG-H4-CONTROL-NAMING")
    assert any('the "Settings" section' in f.location for f in findings)


# ---------------------------------------------------------------------------
# NNG-H6-LABELED, HTML
# ---------------------------------------------------------------------------


def test_labeled_html_all_named_controls_has_no_finding():
    text = """
    <html><body>
    <form>
    <label for="name">Name</label>
    <input type="text" id="name">
    <button>Save</button>
    </form>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    assert "NNG-H6-LABELED" not in _criteria(findings)


def test_labeled_html_icon_only_button_among_labeled_siblings_is_severity_2():
    text = """
    <html><body>
    <nav>
    <button>Home</button>
    <button>Settings</button>
    <button></button>
    </nav>
    </body></html>
    """
    findings = _only(checks.check(_artifact(text)), "NNG-H6-LABELED")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_labeled_html_every_control_in_container_unnamed_is_severity_3():
    text = """
    <html><body>
    <nav>
    <button></button>
    <button></button>
    </nav>
    </body></html>
    """
    findings = _only(checks.check(_artifact(text)), "NNG-H6-LABELED")
    # Same signature (both bare <button>): grouped as "the same control
    # repeating", but exactly 2 occurrences cannot use the instances array
    # (contract minItems 2), so this is two separate findings.
    assert len(findings) == 2
    assert all(f.severity == 3 for f in findings)
    assert all(f.instances == () for f in findings)


def test_labeled_html_input_with_no_label_at_all_is_flagged():
    text = """
    <html><body>
    <form>
    <input type="text">
    </form>
    </body></html>
    """
    findings = _only(checks.check(_artifact(text)), "NNG-H6-LABELED")
    assert len(findings) == 1
    assert "label" in findings[0].violation


def test_labeled_html_input_with_aria_label_only_is_still_flagged():
    """The input-specific test requires an associated <label> element; an
    aria-label alone does not satisfy it, matching the severity-3 anchor
    in references/NNG-HEURISTICS.md about placeholder-only fields."""
    text = """
    <html><body>
    <form>
    <input type="text" aria-label="Name">
    </form>
    </body></html>
    """
    findings = _only(checks.check(_artifact(text)), "NNG-H6-LABELED")
    assert len(findings) == 1


def test_labeled_html_input_wrapped_in_label_with_text_is_not_flagged():
    text = """
    <html><body>
    <form>
    <label>Name <input type="text"></label>
    </form>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    assert "NNG-H6-LABELED" not in _criteria(findings)


def test_labeled_html_input_associated_by_for_id_is_not_flagged():
    text = """
    <html><body>
    <form>
    <label for="email">Email</label>
    <input type="email" id="email">
    </form>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    assert "NNG-H6-LABELED" not in _criteria(findings)


def test_labeled_html_empty_label_association_does_not_count():
    text = """
    <html><body>
    <form>
    <label for="x"></label>
    <input type="text" id="x">
    </form>
    </body></html>
    """
    findings = _only(checks.check(_artifact(text)), "NNG-H6-LABELED")
    assert len(findings) == 1


def test_labeled_html_anchor_only_bookmark_is_not_treated_as_a_control():
    """An <a> with no href is a scroll target, not a link; it must not be
    checked for a readable name."""
    text = '<html><body><a id="top"></a><p>Hello</p></body></html>'
    findings = checks.check(_artifact(text))
    assert findings == []


def test_labeled_html_hidden_and_submit_inputs_are_not_treated_as_fields():
    text = """
    <html><body>
    <form>
    <input type="hidden" name="csrf" value="x">
    <input type="submit" value="Save">
    </form>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    assert "NNG-H6-LABELED" not in _criteria(findings)


def test_labeled_html_repeated_icon_buttons_are_grouped_by_signature():
    """Three icon-only delete buttons sharing tag, class, and role are
    read as one repeated control, not three unrelated ones: one finding
    with an instance list, since there are 3 total occurrences."""
    text = """
    <html><body>
    <section id="list">
    <button class="icon-delete" role="button"></button>
    <button class="icon-delete" role="button"></button>
    <button class="icon-delete" role="button"></button>
    </section>
    </body></html>
    """
    findings = _only(checks.check(_artifact(text)), "NNG-H6-LABELED")
    assert len(findings) == 1
    assert len(findings[0].instances) == 2


def test_labeled_html_different_signatures_are_not_merged():
    text = """
    <html><body>
    <section id="a">
    <button class="icon-delete"></button>
    <a href="#a"></a>
    </section>
    </body></html>
    """
    findings = _only(checks.check(_artifact(text)), "NNG-H6-LABELED")
    assert len(findings) == 2  # a <button> and an <a> are different signatures


# ---------------------------------------------------------------------------
# NNG-H6-LABELED, markdown
# ---------------------------------------------------------------------------


def test_labeled_markdown_named_control_list_entries_have_no_finding():
    text = "# Title\n\n## Controls\n\n- Save button\n- Cancel button\n"
    findings = checks.check(_artifact(text, path="fixture.md"))
    assert "NNG-H6-LABELED" not in _criteria(findings)


def test_labeled_markdown_bare_role_entries_mixed_with_named_ones_is_severity_2():
    text = "# Title\n\n## Controls\n\n- Save button\n- Icon\n"
    findings = _only(checks.check(_artifact(text, path="fixture.md")), "NNG-H6-LABELED")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_labeled_markdown_all_bare_role_entries_is_severity_3():
    text = "# Title\n\n## Controls\n\n- Button\n- Icon\n"
    findings = _only(checks.check(_artifact(text, path="fixture.md")), "NNG-H6-LABELED")
    assert len(findings) == 2  # two distinct roles, each its own finding
    assert all(f.severity == 3 for f in findings)


def test_labeled_markdown_list_not_under_a_control_or_field_heading_is_ignored():
    text = "# Title\n\n## Benefits\n\n- Button\n- Icon\n"
    findings = checks.check(_artifact(text, path="fixture.md"))
    assert findings == []


def test_labeled_markdown_repeated_bare_role_is_one_grouped_finding():
    text = "# Title\n\n## Field list\n\n- Field\n- Field\n- Field\n"
    findings = _only(checks.check(_artifact(text, path="fixture.md")), "NNG-H6-LABELED")
    assert len(findings) == 1
    assert findings[0].severity == 3
    assert len(findings[0].instances) == 2


def test_labeled_markdown_article_and_trailing_role_word_are_stripped_before_matching():
    text = "# Title\n\n## Controls\n\n- A toggle control\n"
    findings = _only(checks.check(_artifact(text, path="fixture.md")), "NNG-H6-LABELED")
    assert len(findings) == 1


# ---------------------------------------------------------------------------
# Empty / degenerate artifacts
# ---------------------------------------------------------------------------


def test_empty_artifact_has_no_findings():
    assert checks.check(_artifact("")) == []


def test_whitespace_only_artifact_has_no_findings():
    assert checks.check(_artifact("   \n\n  \t\n")) == []


def test_html_with_no_interactive_content_has_no_findings():
    findings = checks.check(_artifact("<html><body><p>Static text only.</p></body></html>"))
    assert findings == []


def test_markdown_prose_with_no_headings_or_lists_has_no_findings():
    findings = checks.check(_artifact("Just a paragraph of prose with no structure at all.", path="fixture.md"))
    assert findings == []


# ---------------------------------------------------------------------------
# Multiple criteria together
# ---------------------------------------------------------------------------


def test_multiple_defects_in_one_artifact_are_all_reported():
    text = """
    <html><body>
    <section id="dashboard">
    <a href="#trap">Go</a>
    <button>Save</button>
    </section>
    <section id="trap">
    <button>Apply</button>
    <button></button>
    </section>
    </body></html>
    """
    findings = checks.check(_artifact(text))
    criteria = set(_criteria(findings))
    assert criteria == {"NNG-H3-DEADEND", "NNG-H4-CONTROL-NAMING", "NNG-H6-LABELED"}


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_check_is_deterministic_across_repeated_calls():
    """S-04 spec: checks.py MUST be deterministic, same artifact, same
    output. RawFinding is a frozen dataclass, so list equality compares
    every field, including instances tuples."""
    artifact = _artifact(HTML_TWO_STATES_CLEAN.replace("#settings", "#trap"))
    first = checks.check(artifact)
    second = checks.check(artifact)
    assert first == second


def test_check_is_deterministic_for_markdown_artifacts():
    artifact = _artifact(MD_TWO_STATES_CLEAN.replace("#dashboard)\n", "#trap)\n"), path="fixture.md")
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

    target = tmp_path / "doc.html"
    target.write_text(
        """
        <html><body>
        <section id="a"><button>Save</button><button>Apply</button></section>
        <section id="b"><a href="#a">Back</a></section>
        </body></html>
        """,
        encoding="utf-8",
        newline="\n",
    )
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
    assert first["run"]["skill"] == "critique-usability"
    assert first["run"]["rubrics"] == ["NNG"]


# ---------------------------------------------------------------------------
# Gate exit codes
# ---------------------------------------------------------------------------


def test_gate_exits_zero_for_a_clean_artifact(tmp_path, monkeypatch):
    target = tmp_path / "doc.html"
    target.write_text(HTML_TWO_STATES_CLEAN, encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    code = checks.main([str(target), "--gate"])

    assert code == 0


def test_gate_exits_two_for_a_severity_3_dead_end_at_default_threshold(tmp_path, monkeypatch):
    text = """
    <html><body>
    <section id="dashboard">
    <a href="#trap">Go</a>
    </section>
    <section id="trap">
    <p>No way out.</p>
    </section>
    </body></html>
    """
    target = tmp_path / "doc.html"
    target.write_text(text, encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    code = checks.main([str(target), "--gate"])

    assert code == 2
