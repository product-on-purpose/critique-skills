"""Tests for this skill's scripts/checks.py scripted lane: the 13
WCAG 2.2 AA criteria in SKILL.md's checks.scripted.

what-it-is:   the unit suite for critique-accessibility's scripted lane
what-it-does: exercises every check function against small in-memory
              HTML fixtures: a violation is detected, a clean fixture
              produces no finding for that criterion, and the whole
              lane is deterministic across two runs
why:          the template requires pytest coverage of every scripted
              check (docs/internal/skill-template.md, "scripts/tests/")
used-by:      `python -m pytest`, and `scripts/skill-selftest.py`'s own
              pytest check when it validates this directory

`critique-accessibility` has a hyphen in its own directory name, so
`checks.py` cannot be reached with a normal `import` statement. It is
loaded here by file path via `importlib.util`, the same technique
`scripts/skill-selftest.py`'s own `_load_module` uses, and the same
reason `scripts/checks.py`'s own bootstrap puts the repository root on
`sys.path` unconditionally rather than assuming pytest already did.

The module basename carries the skill's domain (`_accessibility`) on
purpose: two skills shipping `scripts/tests/test_checks.py` collide at
pytest collection and abort the whole repository run. See
`scripts/skill-selftest.py`'s `check_test_module_names`.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from skills._shared.artifact import Artifact
from skills._shared.runner import run_scripted_lane

_CHECKS_PATH = Path(__file__).resolve().parents[1] / "checks.py"


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())


def _load_checks_module():
    spec = importlib.util.spec_from_file_location("accessibility_checks_under_test", _CHECKS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checks = _load_checks_module()

FIXED_NOW = lambda: datetime(2026, 7, 31, 12, 0, 0, tzinfo=timezone.utc)  # noqa: E731


def _artifact(html: str) -> Artifact:
    return Artifact(path="fixture.html", text=html, sha256="0" * 64, disk_path=Path("fixture.html"))


def _by_criterion(findings, criterion):
    return [f for f in findings if f.criterion == criterion]


# ---------------------------------------------------------------------------
# A comprehensive clean page: every criterion's happy path in one
# document. The equivalent of the toy fixture's CLEAN_TEXT.
# ---------------------------------------------------------------------------

CLEAN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<title>Quarterly Field Report</title>
</head>
<body>
<a href="#main-content">Skip to main content</a>
<header>
<nav><a href="/">Home</a></nav>
</header>
<main id="main-content">
<h1>Quarterly Field Report</h1>
<h2>Service window</h2>
<p>The crew reviews the meter log before the shift ends.</p>
<img src="crew.jpg" alt="Field crew inspecting a meter panel">
<img src="divider.png" alt="" role="presentation">
<table>
<tr><th scope="col">Region</th><th scope="col">Q1</th><th scope="col">Q2</th></tr>
<tr><th scope="row">North</th><td>12</td><td>15</td></tr>
</table>
<p><a href="/reports/full">Download the full quarterly report</a></p>
<h2>Contact</h2>
<form>
<label for="email">Email address</label>
<input id="email" type="text">
</form>
</main>
</body>
</html>
"""


def test_clean_page_has_no_findings():
    findings = checks.check(_artifact(CLEAN_PAGE))
    assert findings == []


def test_empty_artifact_has_no_findings():
    findings = checks.check(_artifact(""))
    assert findings == []


# ---------------------------------------------------------------------------
# WCAG-1.1.1: text alternatives
# ---------------------------------------------------------------------------


def test_missing_alt_is_flagged_severity_2():
    html = '<html lang="en"><body><img src="hero.jpg"></body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.1.1")
    assert len(findings) == 1
    assert findings[0].severity == 2
    assert findings[0].lane == "scripted"
    assert findings[0].confidence == "high"


def test_multiple_missing_alt_escalates_to_severity_3():
    html = '<html lang="en"><body><img src="a.jpg"><img src="b.jpg"></body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.1.1")
    assert len(findings) == 2
    assert all(f.severity == 3 for f in findings)


def test_placeholder_alt_text_is_flagged():
    html = '<html lang="en"><body><img src="a.jpg" alt="icon"></body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.1.1")
    assert len(findings) == 1
    assert "placeholder" in findings[0].violation


def test_decorative_image_is_not_flagged():
    html = '<html lang="en"><body><img src="a.jpg" alt=""></body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.1.1")
    assert findings == []


def test_aria_hidden_image_is_not_flagged():
    html = '<html lang="en"><body><img src="a.jpg" aria-hidden="true"></body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.1.1")
    assert findings == []


def test_descriptive_alt_text_is_not_flagged():
    html = '<html lang="en"><body><img src="a.jpg" alt="Field crew inspecting a meter panel"></body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.1.1")
    assert findings == []


# ---------------------------------------------------------------------------
# WCAG-1.3.1: heading-level skips and table headers
# ---------------------------------------------------------------------------


def test_heading_skip_is_flagged():
    html = "<h1>Report</h1><h2>Section</h2><h4>Detail</h4>"
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.3.1")
    assert len(findings) == 1
    assert findings[0].severity == 2
    assert "Detail" in findings[0].location


def test_multiple_heading_skips_escalate_to_severity_3():
    html = "<h1>Report</h1><h2>A</h2><h4>B</h4><h2>C</h2><h5>D</h5>"
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.3.1")
    assert len([f for f in findings if "level skips" in f.violation]) == 2
    assert all(f.severity == 3 for f in findings if "level skips" in f.violation)


def test_sequential_headings_are_not_flagged():
    html = "<h1>Report</h1><h2>Section</h2><h3>Subsection</h3>"
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.3.1")
    assert findings == []


def test_data_table_with_no_header_markup_is_flagged():
    html = """
    <table>
    <tr><td>Region</td><td>Q1</td><td>Q2</td></tr>
    <tr><td>North</td><td>12</td><td>15</td></tr>
    </table>
    """
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.3.1")
    table_findings = [f for f in findings if "data table" in f.violation]
    assert len(table_findings) == 1
    assert table_findings[0].severity == 3


def test_data_table_with_th_is_not_flagged():
    html = """
    <table>
    <tr><th scope="col">Region</th><th scope="col">Q1</th><th scope="col">Q2</th></tr>
    <tr><th scope="row">North</th><td>12</td><td>15</td></tr>
    </table>
    """
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.3.1")
    assert not [f for f in findings if "data table" in f.violation]


def test_single_row_table_is_not_flagged():
    html = "<table><tr><td>Only</td><td>Row</td></tr></table>"
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.3.1")
    assert findings == []


# ---------------------------------------------------------------------------
# WCAG-1.4.3: text contrast
# ---------------------------------------------------------------------------


def test_low_contrast_text_just_under_threshold_is_severity_2():
    html = '<p style="color: #808080; background-color: #ffffff;">Body copy for the report.</p>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.3")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_low_contrast_text_well_under_threshold_is_severity_3():
    html = '<p style="color: #bbbbbb; background-color: #ffffff;">Body copy for the report.</p>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.3")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_black_on_white_is_not_flagged():
    html = '<p style="color: #000000; background-color: #ffffff;">Body copy for the report.</p>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.3")
    assert findings == []


def test_default_colors_with_no_css_are_not_flagged():
    html = "<p>Body copy for the report with no declared color at all.</p>"
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.3")
    assert findings == []


def test_large_text_uses_the_lower_threshold():
    html = '<p style="color: #808080; background-color: #ffffff; font-size: 24px;">Large heading copy.</p>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.3")
    assert findings == []  # 3.95:1 clears the 3:1 large-text minimum


def test_inherited_background_from_ancestor_is_used():
    html = (
        '<div style="background-color: #ffffff;">'
        '<p style="color: #bbbbbb;">Body copy that inherits its background.</p>'
        "</div>"
    )
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.3")
    assert len(findings) == 1
    assert "#ffffff" in findings[0].evidence


# ---------------------------------------------------------------------------
# WCAG-1.4.4: resize text (viewport zoom)
# ---------------------------------------------------------------------------


def test_user_scalable_no_is_flagged_severity_3():
    html = '<html lang="en"><head><meta name="viewport" content="width=device-width, user-scalable=no"></head></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.4")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_maximum_scale_below_2_is_flagged_severity_2():
    html = '<html lang="en"><head><meta name="viewport" content="width=device-width, maximum-scale=1.5"></head></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.4")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_unrestricted_viewport_is_not_flagged():
    html = '<html lang="en"><head><meta name="viewport" content="width=device-width, initial-scale=1"></head></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.4")
    assert findings == []


def test_no_viewport_meta_tag_is_not_flagged():
    html = '<html lang="en"><head></head><body>No viewport tag at all.</body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.4")
    assert findings == []


# ---------------------------------------------------------------------------
# WCAG-1.4.10: reflow (fixed width)
# ---------------------------------------------------------------------------


def test_fixed_width_960px_is_severity_3():
    html = '<div style="width: 960px;">Wide wrapper</div>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.10")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_fixed_width_400px_is_severity_2():
    html = '<div style="width: 400px;">Promotional banner</div>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.10")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_fixed_width_under_320_is_not_flagged():
    html = '<div style="width: 300px;">Narrow box</div>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.10")
    assert findings == []


def test_fixed_width_with_relative_max_width_override_is_not_flagged():
    html = '<div style="width: 960px; max-width: 100%;">Wrapper with a responsive cap</div>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.10")
    assert findings == []


def test_percentage_width_is_not_flagged():
    html = '<div style="width: 80%;">Relative-width wrapper</div>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.10")
    assert findings == []


def test_media_query_override_is_not_flagged():
    html = """
    <style>
    .banner { width: 960px; }
    @media (max-width: 480px) { .banner { width: 100%; } }
    </style>
    <div class="banner">Wrapper with a media-query override</div>
    """
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.10")
    assert findings == []


# ---------------------------------------------------------------------------
# WCAG-1.4.11: contrast, non-text (component boundaries)
# ---------------------------------------------------------------------------


def test_low_contrast_button_border_just_under_is_severity_2():
    html = '<button style="border: 1px solid #999999; background-color: #ffffff;">Cancel</button>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.11")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_low_contrast_button_border_well_under_is_severity_3():
    html = '<button style="border: 1px solid #bbbbbb; background-color: #ffffff;">Cancel</button>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.11")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_high_contrast_button_border_is_not_flagged():
    html = '<button style="border: 1px solid #000000; background-color: #ffffff;">Cancel</button>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.11")
    assert findings == []


def test_button_with_no_declared_border_is_not_flagged():
    html = "<button>Cancel</button>"
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.11")
    assert findings == []


def test_border_style_none_is_not_flagged():
    html = '<button style="border: 1px solid #999999; border-style: none;">Cancel</button>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.11")
    assert findings == []


# ---------------------------------------------------------------------------
# WCAG-1.4.12: text spacing (fixed height plus clipped overflow)
# ---------------------------------------------------------------------------


def test_fixed_height_with_overflow_hidden_is_flagged_severity_2():
    html = '<div style="height: 100px; overflow: hidden;">A pull-quote that may grow taller once spacing is applied.</div>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.12")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_multiple_clipped_elements_escalate_to_severity_3():
    html = (
        '<div style="height: 100px; overflow: hidden;">First card description text.</div>'
        '<div style="height: 100px; overflow: hidden;">Second card description text.</div>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.12")
    assert len(findings) == 2
    assert all(f.severity == 3 for f in findings)


def test_fixed_height_without_clipped_overflow_is_not_flagged():
    html = '<div style="height: 100px;">Description text with no clipping.</div>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.12")
    assert findings == []


def test_clipped_overflow_on_an_empty_element_is_not_flagged():
    html = '<div style="height: 20px; overflow: hidden;"></div>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-1.4.12")
    assert findings == []


# ---------------------------------------------------------------------------
# WCAG-2.4.1: bypass blocks
# ---------------------------------------------------------------------------


def test_no_main_and_no_skip_link_behind_a_nav_block_is_severity_3():
    html = """
    <html lang="en"><body>
    <header>Site header</header>
    <nav><a href="/billing">Billing</a><a href="/outages">Outages</a></nav>
    <h1>Report</h1>
    <p>Content.</p>
    </body></html>
    """
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.1")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_no_main_and_nothing_to_tab_past_is_severity_2():
    html = """
    <html lang="en"><body>
    <header><h1>Report</h1></header>
    <p>Content.</p>
    <a href="/billing">Billing</a>
    </body></html>
    """
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.1")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_main_landmark_present_is_not_flagged():
    html = """
    <html lang="en"><body>
    <header>Site header</header>
    <main><h1>Report</h1><p>Content.</p></main>
    </body></html>
    """
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.1")
    assert findings == []


def test_leading_skip_link_is_not_flagged():
    html = """
    <html lang="en"><body>
    <a href="#content">Skip to content</a>
    <header>Site header</header>
    <div id="content"><h1>Report</h1><p>Content.</p></div>
    </body></html>
    """
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.1")
    assert findings == []


def test_fragment_with_no_html_or_body_is_not_checked():
    html = "<p>A standalone snippet with no page shell at all.</p>"
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.1")
    assert findings == []


# ---------------------------------------------------------------------------
# WCAG-2.4.2: page titled
# ---------------------------------------------------------------------------


def test_missing_title_element_is_flagged():
    html = "<html lang=\"en\"><head></head><body>No title at all.</body></html>"
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.2")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_empty_title_element_is_flagged():
    html = '<html lang="en"><head><title></title></head><body>Body.</body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.2")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_placeholder_title_is_flagged_severity_2():
    html = '<html lang="en"><head><title>Untitled Document</title></head><body>Body.</body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.2")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_specific_title_is_not_flagged():
    html = '<html lang="en"><head><title>Quarterly Field Report</title></head><body>Body.</body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.2")
    assert findings == []


def test_fragment_with_no_html_element_is_not_checked_for_title():
    html = "<p>A standalone snippet with no page shell at all.</p>"
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.2")
    assert findings == []


# ---------------------------------------------------------------------------
# WCAG-2.4.4: link purpose (link text)
# ---------------------------------------------------------------------------


def test_click_here_link_is_flagged():
    html = '<a href="/report">Click here</a>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.4")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_repeated_generic_links_escalate_to_severity_3():
    html = '<a href="/a">Read more</a><a href="/b">Read more</a>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.4")
    assert len(findings) == 2
    assert all(f.severity == 3 for f in findings)


def test_descriptive_link_text_is_not_flagged():
    html = '<a href="/report">Download the quarterly field report</a>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.4")
    assert findings == []


def test_generic_text_with_aria_label_is_not_flagged():
    html = '<a href="/report" aria-label="Download the quarterly field report">Click here</a>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.4")
    assert findings == []


def test_link_without_href_is_not_checked():
    html = '<a name="anchor-target">Click here</a>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.4.4")
    assert findings == []


# ---------------------------------------------------------------------------
# WCAG-2.5.3: label in name
# ---------------------------------------------------------------------------


def test_aria_label_without_visible_text_substring_is_flagged():
    html = '<button aria-label="Send form now">Submit</button>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.5.3")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_aria_label_containing_visible_text_is_not_flagged():
    html = '<button aria-label="Save changes">Save</button>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.5.3")
    assert findings == []


def test_control_with_no_aria_label_is_not_checked():
    html = "<button>Save</button>"
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.5.3")
    assert findings == []


def test_multiple_mismatches_escalate_to_severity_3():
    html = (
        '<button aria-label="Send form now">Submit</button>'
        '<button aria-label="Discard everything">Cancel</button>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-2.5.3")
    assert len(findings) == 2
    assert all(f.severity == 3 for f in findings)


# ---------------------------------------------------------------------------
# WCAG-3.1.1: language of page
# ---------------------------------------------------------------------------


def test_missing_lang_attribute_is_flagged():
    html = "<html><head><title>Report</title></head><body>Body.</body></html>"
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.1.1")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_empty_lang_attribute_is_flagged():
    html = '<html lang=""><head><title>Report</title></head><body>Body.</body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.1.1")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_missing_page_lang_with_a_well_formed_subtree_lang_is_severity_2():
    html = (
        '<html><head><title>Report</title></head>'
        '<body><div lang="en"><p>Body copy inside a language-declared wrapper.</p></div></body></html>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.1.1")
    assert len(findings) == 1
    assert findings[0].severity == 2
    assert 'lang="en"' in findings[0].violation


def test_malformed_lang_attribute_is_flagged():
    html = '<html lang="english"><head><title>Report</title></head><body>Body.</body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.1.1")
    assert len(findings) == 1


def test_well_formed_lang_is_not_flagged():
    html = '<html lang="en"><head><title>Report</title></head><body>Body.</body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.1.1")
    assert findings == []


def test_well_formed_regional_lang_is_not_flagged():
    html = '<html lang="en-US"><head><title>Report</title></head><body>Body.</body></html>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.1.1")
    assert findings == []


def test_fragment_with_no_html_element_is_not_checked_for_lang():
    html = "<p>A standalone snippet with no page shell at all.</p>"
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.1.1")
    assert findings == []


# ---------------------------------------------------------------------------
# WCAG-3.3.2: labels or instructions
# ---------------------------------------------------------------------------


def test_unlabeled_input_is_flagged():
    html = '<form><input id="email" type="text"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.3.2")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_multiple_unlabeled_inputs_escalate_to_severity_3():
    html = '<form><input id="a" type="text"><input id="b" type="text"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.3.2")
    assert len(findings) == 2
    assert all(f.severity == 3 for f in findings)


def test_input_with_for_linked_label_is_not_flagged():
    html = '<form><label for="email">Email</label><input id="email" type="text"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.3.2")
    assert findings == []


def test_input_wrapped_in_label_is_not_flagged():
    html = '<form><label>Email <input type="text"></label></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.3.2")
    assert findings == []


def test_input_with_aria_label_is_not_flagged():
    html = '<form><input type="text" aria-label="Email address"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.3.2")
    assert findings == []


def test_hidden_input_is_not_flagged():
    html = '<form><input type="hidden" name="csrf" value="x"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.3.2")
    assert findings == []


def test_disabled_input_is_not_flagged():
    html = '<form><input id="promo" type="text" disabled></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "WCAG-3.3.2")
    assert findings == []


# ---------------------------------------------------------------------------
# Determinism: same artifact, same output, across two independent runs.
# ---------------------------------------------------------------------------

SEEDED_PAGE = """<html><head></head><body>
<header>Site header</header>
<img src="hero.jpg">
<h1>Report</h1>
<h4>Detail skipping levels</h4>
<a href="/x">Click here</a>
<p style="color: #bbbbbb; background-color: #ffffff;">Low-contrast body copy.</p>
<div style="width: 960px;">Wide wrapper</div>
<form><input id="email" type="text"></form>
</body></html>
"""


def test_direct_check_call_is_deterministic_across_two_runs():
    first = checks.check(_artifact(SEEDED_PAGE))
    second = checks.check(_artifact(SEEDED_PAGE))
    assert first == second
    assert len(first) > 5  # a real cross-criterion mix, not an accidental empty match


def test_cli_run_is_deterministic_across_two_runs(tmp_path, monkeypatch):
    target = tmp_path / "seeded.html"
    target.write_text(SEEDED_PAGE, encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    def run_once():
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_scripted_lane(
                skill_name="critique-accessibility",
                skill_version="0.1.0",
                rubrics=["WCAG"],
                check_fn=checks.check,
                argv=[str(target)],
                now=FIXED_NOW,
            )
        return json.loads(buf.getvalue())

    first = run_once()
    second = run_once()

    assert first["findings"] == second["findings"]
    assert first["summary"] == second["summary"]
    assert first["run"]["skill"] == "critique-accessibility"
    assert first["run"]["rubrics"] == ["WCAG"]


def test_clean_page_gate_exits_zero(tmp_path, monkeypatch):
    target = tmp_path / "clean.html"
    target.write_text(CLEAN_PAGE, encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    code = run_scripted_lane(
        skill_name="critique-accessibility",
        skill_version="0.1.0",
        rubrics=["WCAG"],
        check_fn=checks.check,
        argv=[str(target), "--gate"],
        now=FIXED_NOW,
    )
    assert code == 0


def test_seeded_page_gate_fails(tmp_path, monkeypatch):
    target = tmp_path / "seeded.html"
    target.write_text(SEEDED_PAGE, encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    code = run_scripted_lane(
        skill_name="critique-accessibility",
        skill_version="0.1.0",
        rubrics=["WCAG"],
        check_fn=checks.check,
        argv=[str(target), "--gate"],
        now=FIXED_NOW,
    )
    assert code in (1, 2)  # at least one severity 3 or 4 finding in the seeded mix
