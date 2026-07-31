"""Tests for critique-microcopy's scripts/checks.py scripted lane:
NNG-EM-CONSTRUCTIVE, NNG-EM-NEUTRAL-TONE, NNG-EM-NOT-COLOR-ONLY,
NNG-EM-PLAIN-LANGUAGE, NNG-EM-PRESERVE-INPUT, NNG-EM-TIMING.

what-it-is:   the unit suite for this skill's scripted lane
what-it-does: exercises each NNG-EM-* scripted check against small
              in-memory artifacts, covering the annotated-context grammar
              (ADR 0018) and the bare-message fallback SKILL.md's protocol
              also accepts, plus a clean pass and a determinism double-run
why:          docs/internal/skill-template.md, "scripts/tests/", requires
              pytest coverage of every scripted check: a clean case, a
              triggering case, and edge cases
used-by:      `python -m pytest`, and `scripts/skill-selftest.py`'s own
              pytest check when it validates this directory

The module basename carries the skill's domain (`_microcopy`) on purpose:
two skills shipping `scripts/tests/test_checks.py` collide at pytest
collection time and abort the whole repository run. See
`scripts/skill-selftest.py`'s `check_test_module_names`.

`critique-microcopy` has a hyphen in its own directory name, so `checks.py`
cannot be reached with a normal `import` statement. It is loaded here by
file path via `importlib.util`, the same technique the template fixture's
own test module uses.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from skills._shared.artifact import Artifact
from skills._shared.runner import run_scripted_lane

_CHECKS_PATH = Path(__file__).resolve().parents[1] / "checks.py"

FIXED_NOW = lambda: datetime(2026, 7, 31, 9, 0, 0, tzinfo=timezone.utc)  # noqa: E731


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())


def _load_checks_module():
    spec = importlib.util.spec_from_file_location("microcopy_checks_under_test", _CHECKS_PATH)
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


def _one(findings, criterion):
    matches = [f for f in findings if f.criterion == criterion]
    assert len(matches) == 1, (criterion, findings)
    return matches[0]


# --------------------------------------------------------------------------
# A clean annotated screen: every field chosen so none of the six checks
# fire. Reused as the "clean artifact" baseline and as a template each
# violation fixture below perturbs exactly one field of.
# --------------------------------------------------------------------------

CLEAN_ANNOTATED = """# Signup flow

## Signup form, email field

Message: Please enter a valid email address in the format name@example.com.
Placement: directly below the email input field
Container: inline
Signal: same weight as the label text, icon
Fires: on-blur
Predictable mistake: yes
Input on resubmission: preserved
Suggested fix: none

## Signup form, password field

Message: Choose a password with at least eight characters.
Placement: directly below the password input field
Container: inline
Signal: same weight as the label text, text-label
Fires: on-blur
Predictable mistake: no
Input on resubmission: preserved
Suggested fix: none
"""


def test_clean_annotated_artifact_has_no_findings():
    findings = checks.check(_artifact(CLEAN_ANNOTATED))
    assert findings == []


def test_empty_artifact_has_no_findings():
    assert checks.check(_artifact("")) == []


def test_headings_with_no_messages_have_no_findings():
    text = "# Title\n\n## Signup form\n\n## Password field\n"
    assert checks.check(_artifact(text)) == []


def test_stray_screen_prose_is_ignored_when_the_document_also_has_annotated_blocks():
    """Bare-message fallback is a whole-document mode, not a per-block one
    (see checks.py's _parse_messages docstring): a document that already
    has an annotated 'Message:' block elsewhere does not sweep up
    unrelated descriptive prose as a message of its own. Without this,
    the prose below (no instruction verb in it) would misfire
    NNG-EM-CONSTRUCTIVE."""
    text = """## Signup form

Some descriptive screen prose that is not a message block at all.

Message: Please enter a valid email address.
Container: inline
Signal: same weight as the label text, icon
Fires: on-blur
Input on resubmission: preserved
Suggested fix: none
"""
    assert checks.check(_artifact(text)) == []


# --------------------------------------------------------------------------
# NNG-EM-CONSTRUCTIVE
# --------------------------------------------------------------------------

def test_constructive_clean_when_instruction_present():
    findings = checks.check(_artifact(CLEAN_ANNOTATED))
    assert "NNG-EM-CONSTRUCTIVE" not in _criteria(findings)


def test_constructive_violation_severity_3_when_no_suggested_fix():
    """docs/reference/severity-scale.md's own Microcopy domain anchor for
    severity 3 is this exact message: "Something went wrong. Try again."
    with no indication of what to change."""
    text = """## Checkout, payment failure

Message: Something went wrong. Try again.
Placement: top of the checkout page
Container: modal
Signal: bold, bold
Fires: on-submit
Predictable mistake: no
Input on resubmission: preserved
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    finding = _one(findings, "NNG-EM-CONSTRUCTIVE")
    assert finding.severity == 3
    assert finding.lane == "scripted"
    assert finding.confidence == "high"
    assert "Checkout, payment failure" in finding.location
    assert finding.evidence == "Something went wrong. Try again."


def test_constructive_violation_severity_2_when_fix_described_elsewhere():
    text = """## Checkout, payment failure

Message: Something went wrong.
Placement: top of the checkout page
Container: modal
Signal: bold, bold
Fires: on-submit
Predictable mistake: no
Input on resubmission: preserved
Suggested fix: described, contact support with the order number
"""
    findings = checks.check(_artifact(text))
    finding = _one(findings, "NNG-EM-CONSTRUCTIVE")
    assert finding.severity == 2


# --------------------------------------------------------------------------
# NNG-EM-NEUTRAL-TONE
# --------------------------------------------------------------------------

def test_neutral_tone_clean_with_no_blame_phrase():
    findings = checks.check(_artifact(CLEAN_ANNOTATED))
    assert "NNG-EM-NEUTRAL-TONE" not in _criteria(findings)


def test_neutral_tone_violation_severity_2_ordinary_case():
    text = """## Signup form, email field

Message: You did not enter a valid email address.
Placement: directly below the email input field
Container: inline
Signal: same weight as the label text, icon
Fires: on-blur
Predictable mistake: yes
Input on resubmission: preserved
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    finding = _one(findings, "NNG-EM-NEUTRAL-TONE")
    assert finding.severity == 2


def test_neutral_tone_violation_severity_3_with_repetition_marker():
    """NNG-EM.md's own severity-3 anchor for this criterion."""
    text = """## Login, password field

Message: You keep entering the wrong password.
Placement: directly below the password input field
Container: inline
Signal: same weight as the label text, icon
Fires: on-submit
Predictable mistake: no
Input on resubmission: not-applicable
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    finding = _one(findings, "NNG-EM-NEUTRAL-TONE")
    assert finding.severity == 3


# --------------------------------------------------------------------------
# NNG-EM-PLAIN-LANGUAGE
# --------------------------------------------------------------------------

def test_plain_language_clean_with_no_jargon():
    findings = checks.check(_artifact(CLEAN_ANNOTATED))
    assert "NNG-EM-PLAIN-LANGUAGE" not in _criteria(findings)


def test_plain_language_violation_severity_2_when_plain_sentence_carries_a_code():
    text = """## Checkout, payment failure

Message: Please correct the highlighted fields. [ERR_502]
Placement: top of the checkout page
Container: inline
Signal: same weight as the label text, icon
Fires: on-submit
Predictable mistake: no
Input on resubmission: preserved
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    finding = _one(findings, "NNG-EM-PLAIN-LANGUAGE")
    assert finding.severity == 2


def test_plain_language_ignores_a_jargon_term_inside_an_ordinary_word():
    """JARGON_TERMS matches whole words only. Without that, null inside
    annulled (and the same shape for every other short term on the list)
    is a false positive on a scripted criterion."""
    text = """## Billing, subscription

Message: Your subscription was annulled before the renewal date. Contact support to restore it.
Placement: in a banner above the billing summary
Container: inline
Signal: bold text, icon
Fires: on-load-before-input
Predictable mistake: no
Input on resubmission: not-applicable
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    assert "NNG-EM-PLAIN-LANGUAGE" not in _criteria(findings)


def test_plain_language_still_flags_a_jargon_term_as_a_whole_word():
    text = """## Checkout, payment failure

Message: Please correct the highlighted field. The backend rejected this request.
Placement: top of the checkout page
Container: inline
Signal: same weight as the label text, icon
Fires: on-submit
Predictable mistake: no
Input on resubmission: preserved
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    assert "NNG-EM-PLAIN-LANGUAGE" in _criteria(findings)


def test_plain_language_violation_severity_3_when_message_is_only_a_code():
    text = """## Checkout, payment failure

Message: Status code: 500
Placement: top of the checkout page
Container: modal
Signal: bold, bold
Fires: on-submit
Predictable mistake: no
Input on resubmission: preserved
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    finding = _one(findings, "NNG-EM-PLAIN-LANGUAGE")
    assert finding.severity == 3


# --------------------------------------------------------------------------
# NNG-EM-NOT-COLOR-ONLY
# --------------------------------------------------------------------------

def test_not_color_only_clean_when_non_color_cue_present():
    findings = checks.check(_artifact(CLEAN_ANNOTATED))
    assert "NNG-EM-NOT-COLOR-ONLY" not in _criteria(findings)


def test_not_color_only_violation_severity_2_when_container_persists():
    text = """## Signup form, email field

Message: Please enter a valid email address.
Placement: directly below the email input field
Container: inline
Signal: red outline, none
Fires: on-blur
Predictable mistake: yes
Input on resubmission: preserved
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    finding = _one(findings, "NNG-EM-NOT-COLOR-ONLY")
    assert finding.severity == 2
    assert "Signal field" in finding.location


def test_not_color_only_violation_severity_3_when_container_is_toast():
    text = """## Signup form, email field

Message: Please enter a valid email address.
Placement: top-right of the screen
Container: toast
Signal: red highlight, none
Fires: on-blur
Predictable mistake: yes
Input on resubmission: preserved
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    finding = _one(findings, "NNG-EM-NOT-COLOR-ONLY")
    assert finding.severity == 3


# --------------------------------------------------------------------------
# NNG-EM-PRESERVE-INPUT
# --------------------------------------------------------------------------

def test_preserve_input_clean_when_preserved():
    findings = checks.check(_artifact(CLEAN_ANNOTATED))
    assert "NNG-EM-PRESERVE-INPUT" not in _criteria(findings)


def test_preserve_input_not_applicable_is_never_flagged():
    text = """## Login, password field

Message: Choose a password with at least eight characters.
Placement: directly below the password input field
Container: inline
Signal: same weight as the label text, icon
Fires: on-blur
Predictable mistake: no
Input on resubmission: not-applicable
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    assert "NNG-EM-PRESERVE-INPUT" not in _criteria(findings)


def test_preserve_input_violation_severity_2_in_a_small_section():
    text = """## Contact form, submission failure

Message: Please try again in a moment.
Placement: top of the form
Container: inline
Signal: same weight as the label text, icon
Fires: on-submit
Predictable mistake: no
Input on resubmission: cleared
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    finding = _one(findings, "NNG-EM-PRESERVE-INPUT")
    assert finding.severity == 2
    assert "Input on resubmission field" in finding.location


def test_preserve_input_violation_severity_3_in_a_larger_section():
    """Three or more message blocks under the same heading is this file's
    deterministic proxy for "a longer, multi-section form" (NNG-EM.md's
    own severity-3 anchor)."""
    text = """## Registration, multi-field form

Message: Choose a display name.
Placement: below the display name field
Container: inline
Signal: same weight as the label text, icon
Fires: on-blur
Predictable mistake: no
Input on resubmission: cleared
Suggested fix: none

Message: Please enter a valid email address.
Placement: below the email field
Container: inline
Signal: same weight as the label text, icon
Fires: on-blur
Predictable mistake: yes
Input on resubmission: cleared
Suggested fix: none

Message: Choose a password with at least eight characters.
Placement: below the password field
Container: inline
Signal: same weight as the label text, icon
Fires: on-blur
Predictable mistake: no
Input on resubmission: cleared
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    preserve_findings = [f for f in findings if f.criterion == "NNG-EM-PRESERVE-INPUT"]
    assert len(preserve_findings) == 3
    assert all(f.severity == 3 for f in preserve_findings)


# --------------------------------------------------------------------------
# NNG-EM-TIMING
# --------------------------------------------------------------------------

def test_timing_clean_when_fires_on_blur():
    findings = checks.check(_artifact(CLEAN_ANNOTATED))
    assert "NNG-EM-TIMING" not in _criteria(findings)


def test_timing_violation_severity_2_when_informational():
    """NNG-EM.md's own severity-2 anchor: a strength meter that updates on
    every keystroke but is not itself an error."""
    text = """## Signup form, password field

Message: Weak. Add a number or a symbol for a stronger password.
Placement: directly below the password input field
Container: inline
Signal: same weight as the label text, icon
Fires: mid-keystroke
Predictable mistake: no
Input on resubmission: not-applicable
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    finding = _one(findings, "NNG-EM-TIMING")
    assert finding.severity == 2


def test_timing_violation_severity_3_when_error_toned():
    """NNG-EM.md's own severity-3 anchor: an email-format error appearing
    before the reader could possibly have finished typing."""
    text = """## Signup form, email field

Message: Please enter a valid email address.
Placement: directly below the email input field
Container: inline
Signal: same weight as the label text, icon
Fires: mid-keystroke
Predictable mistake: yes
Input on resubmission: preserved
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    finding = _one(findings, "NNG-EM-TIMING")
    assert finding.severity == 3


def test_timing_violation_on_load_before_input():
    text = """## Signup form, email field

Message: This field is required.
Placement: directly below the email input field
Container: inline
Signal: same weight as the label text, icon
Fires: on-load-before-input
Predictable mistake: no
Input on resubmission: not-applicable
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    assert "NNG-EM-TIMING" in _criteria(findings)


# --------------------------------------------------------------------------
# Multiple criteria firing on one message; malformed / incomplete blocks
# --------------------------------------------------------------------------

def test_multiple_criteria_can_fire_on_one_message():
    text = """## Login, password field

Message: You keep entering the wrong password. [ERR_401]
Placement: directly below the password input field
Container: toast
Signal: red highlight, none
Fires: mid-keystroke
Predictable mistake: no
Input on resubmission: cleared
Suggested fix: none
"""
    findings = checks.check(_artifact(text))
    criteria = set(_criteria(findings))
    assert {
        "NNG-EM-NEUTRAL-TONE",
        "NNG-EM-PLAIN-LANGUAGE",
        "NNG-EM-NOT-COLOR-ONLY",
        "NNG-EM-PRESERVE-INPUT",
        "NNG-EM-TIMING",
    } <= criteria


def test_incomplete_annotation_block_does_not_crash_and_skips_missing_fields():
    """A block missing Signal, Fires, and Input on resubmission must not
    raise; the field-dependent checks that need those fields simply find
    nothing to flag."""
    text = """## Signup form, email field

Message: Something went wrong. Try again.
Container: inline
"""
    findings = checks.check(_artifact(text))
    criteria = _criteria(findings)
    assert "NNG-EM-NOT-COLOR-ONLY" not in criteria
    assert "NNG-EM-PRESERVE-INPUT" not in criteria
    assert "NNG-EM-TIMING" not in criteria
    assert "NNG-EM-CONSTRUCTIVE" in criteria


# --------------------------------------------------------------------------
# Bare-message fallback (SKILL.md's "bare-string-list artifact" case): no
# screen annotation at all, so only the three message-text-only checks can
# fire.
# --------------------------------------------------------------------------

BARE_LIST = """# Error messages for review

- You did not enter a valid email address.
- Please choose a display name.
- Status code: 500
"""


def test_bare_bullet_list_runs_text_only_checks():
    findings = checks.check(_artifact(BARE_LIST))
    criteria = set(_criteria(findings))
    assert "NNG-EM-NEUTRAL-TONE" in criteria
    assert "NNG-EM-PLAIN-LANGUAGE" in criteria
    assert "NNG-EM-NOT-COLOR-ONLY" not in criteria
    assert "NNG-EM-PRESERVE-INPUT" not in criteria
    assert "NNG-EM-TIMING" not in criteria


def test_bare_paragraph_list_runs_text_only_checks():
    text = """# Error messages for review

You did not enter a valid email address.

Status code: 500
"""
    findings = checks.check(_artifact(text))
    criteria = set(_criteria(findings))
    assert "NNG-EM-NEUTRAL-TONE" in criteria
    assert "NNG-EM-PLAIN-LANGUAGE" in criteria


# --------------------------------------------------------------------------
# Location addressing
# --------------------------------------------------------------------------

def test_location_resets_per_section_and_names_the_heading():
    findings = checks.check(_artifact(f"""## Screen A

Message: You did not enter a valid email address.
Container: inline

## Screen B

Message: You did not enter a valid email address.
Container: inline
"""))
    locations = sorted(f.location for f in findings if f.criterion == "NNG-EM-NEUTRAL-TONE")
    assert locations == ["Screen A, message 1", "Screen B, message 1"]


# --------------------------------------------------------------------------
# IMPLEMENTED_CRITERIA
# --------------------------------------------------------------------------

def test_implemented_criteria_matches_the_six_scripted_criteria():
    assert checks.IMPLEMENTED_CRITERIA == {
        "NNG-EM-CONSTRUCTIVE",
        "NNG-EM-NEUTRAL-TONE",
        "NNG-EM-NOT-COLOR-ONLY",
        "NNG-EM-PLAIN-LANGUAGE",
        "NNG-EM-PRESERVE-INPUT",
        "NNG-EM-TIMING",
    }


# --------------------------------------------------------------------------
# Determinism: same artifact in, same findings out, twice.
# --------------------------------------------------------------------------

def test_check_function_is_deterministic_across_two_calls():
    artifact = _artifact(CLEAN_ANNOTATED + "\n" + BARE_LIST)
    first = checks.check(artifact)
    second = checks.check(artifact)
    assert first == second


def test_check_function_is_deterministic_across_two_fresh_artifacts():
    text = """## Checkout, payment failure

Message: You keep entering the wrong password. [ERR_401]
Container: toast
Signal: red highlight, none
Fires: mid-keystroke
Input on resubmission: cleared
Suggested fix: none
"""
    first = checks.check(_artifact(text))
    second = checks.check(_artifact(text))
    assert first == second


def test_full_cli_run_is_deterministic_across_two_runs(tmp_path, monkeypatch):
    """A full run_scripted_lane round trip, mirroring skills/_shared/tests/
    test_runner.py::test_same_artifact_twice_produces_identical_findings_
    and_summary: findings[] and summary must match byte for byte across
    two runs of the same artifact; run.timestamp is the one field the
    determinism claim excludes (docs/internal/skill-template.md, "What
    determinism does and does not cover")."""
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "doc.md"
    target.write_text(CLEAN_ANNOTATED.replace("Please enter a valid", "You did not enter a valid"), encoding="utf-8", newline="\n")

    def run_once():
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_scripted_lane(
                skill_name="critique-microcopy",
                skill_version="0.1.0",
                rubrics=["NNG"],
                check_fn=checks.check,
                argv=[str(target)],
                now=FIXED_NOW,
            )
        return json.loads(buf.getvalue())

    first = run_once()
    second = run_once()

    assert first["findings"] == second["findings"]
    assert first["summary"] == second["summary"]
    assert first["findings"] != []
