"""Tests for this skill's scripts/checks.py scripted lane: the 18 FORMS
criteria in SKILL.md's checks.scripted.

what-it-is:   the unit suite for critique-forms' scripted lane
what-it-does: exercises every check function against small in-memory
              HTML fixtures: a violation is detected at the severity
              references/FORMS.md states, a clean fixture produces no
              finding for that criterion, every "never flag" statement
              in the operational test holds, and the whole lane is
              deterministic across two runs
why:          the template requires pytest coverage of every scripted
              check (docs/internal/skill-template.md, "scripts/tests/")
used-by:      `python -m pytest`, and `scripts/skill-selftest.py`'s own
              pytest check when it validates this directory

`critique-forms` ships `scripts/tests/test_checks.py`-shaped collisions
across skills, so this module is named `test_checks_forms.py` and loads
`checks.py` under the module name `forms_checks_under_test`, the same
technique `critique-accessibility`'s own suite uses and the same reason
`scripts/checks.py`'s own bootstrap puts the repository root on
`sys.path` unconditionally.
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
    spec = importlib.util.spec_from_file_location("forms_checks_under_test", _CHECKS_PATH)
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


def _control_purpose(html, control_id):
    """The purpose `checks._purpose` infers for the control with this id,
    resolved through the same pipeline `checks.check` uses (parse, build
    labels, collect forms), so these tests exercise the real code path
    rather than calling `_purpose` with a hand-built Node."""
    tree = checks._parse_html(html)
    labels = checks.Labels(tree)
    for form in checks._collect_forms(tree):
        for c in form.controls:
            if c.attrs.get("id") == control_id:
                return checks._purpose(c, labels, form)
    raise AssertionError(f"no control with id={control_id!r} found in fixture")


def _opts(n, start=1):
    return "".join(f'<option value="{i}">{i}</option>' for i in range(start, start + n))


def _run_lane(html, tmp_path, monkeypatch, capsys):
    """Runs the full scripted-lane CLI (run_scripted_lane) over `html`
    written to a real file, so the contract validator sees the actual
    envelope, and returns the parsed JSON stdout."""
    target = tmp_path / "fixture.html"
    target.write_text(html, encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)
    run_scripted_lane(
        skill_name="critique-forms",
        skill_version="0.1.0",
        rubrics=["FORMS"],
        check_fn=checks.check,
        argv=[str(target)],
        now=FIXED_NOW,
    )
    return json.loads(capsys.readouterr().out)


# ---------------------------------------------------------------------------
# A comprehensive clean form: every criterion's happy path in one
# document, like the accessibility suite's CLEAN_PAGE.
# ---------------------------------------------------------------------------

CLEAN_FORM = """<!DOCTYPE html>
<html lang="en">
<head>
<title>Create your account</title>
<style>
input, textarea, select { font-size: 16px; }
</style>
</head>
<body>
<form>
<label for="full-name">Full name (required)</label>
<input id="full-name" name="name" type="text" autocomplete="name" autocorrect="off" spellcheck="false" required>

<label for="email">Email address (required)</label>
<input id="email" name="email" type="email" autocomplete="email" required>

<label for="phone">Phone number (required)</label>
<input id="phone" name="phone" type="tel" autocomplete="tel" required aria-describedby="phone-hint">
<p id="phone-hint">We will only use this to contact you about delivery.</p>

<label for="password">Create a password (required)</label>
<input id="password" name="password" type="password" autocomplete="new-password" minlength="12" required>

<label for="verification-code">Verification code (required)</label>
<input id="verification-code" name="code" type="text" inputmode="numeric" maxlength="6" autocomplete="one-time-code" required>

<label for="street">Street address (required)</label>
<input id="street" name="street" type="text" autocomplete="street-address" autocorrect="off" spellcheck="false" required>

<label for="city">City (required)</label>
<input id="city" name="city" type="text" autocomplete="address-level2" size="20" required>

<label for="postcode">Postal code (required)</label>
<input id="postcode" name="postcode" type="text" autocomplete="postal-code" size="10" required>

<label for="country">Country (optional)</label>
<select id="country" name="country" autocomplete="country">
<option value="">Choose a country</option>
<option value="us">United States</option>
<option value="ca">Canada</option>
<option value="gb">United Kingdom</option>
<option value="au">Australia</option>
<option value="de">Germany</option>
<option value="fr">France</option>
</select>

<label for="date-day">Day (required)</label>
<input id="date-day" name="day" type="text" inputmode="numeric" maxlength="2" required>
<label for="date-month">Month (required)</label>
<input id="date-month" name="month" type="text" inputmode="numeric" maxlength="2" required>
<label for="date-year">Year (required)</label>
<input id="date-year" name="year" type="text" inputmode="numeric" maxlength="4" required>

<button type="submit">Create account</button>
</form>
</body>
</html>
"""


def test_clean_form_has_no_findings():
    findings = checks.check(_artifact(CLEAN_FORM))
    assert findings == []


def test_empty_artifact_has_no_findings():
    findings = checks.check(_artifact(""))
    assert findings == []


# ---------------------------------------------------------------------------
# FORMS-ACTION-LABEL
# ---------------------------------------------------------------------------


def test_action_label_specific_button_is_not_flagged():
    html = '<form><button type="submit">Create account</button></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ACTION-LABEL")
    assert findings == []


def test_action_label_generic_submit_is_flagged_severity_2():
    html = '<form><button type="submit">Submit</button></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ACTION-LABEL")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_action_label_ignores_case_and_punctuation():
    html = '<form><button type="submit"> SUBMIT! </button></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ACTION-LABEL")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_action_label_never_flags_continue():
    html = '<form><button type="submit">Continue</button></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ACTION-LABEL")
    assert findings == []


def test_action_label_never_flags_a_word_that_adds_to_a_generic_word():
    html = '<form><button type="submit">Send message</button></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ACTION-LABEL")
    assert findings == []


def test_action_label_never_flags_a_form_with_no_submit_button():
    html = '<form><label for="n1">Name</label><input id="n1"><button type="reset">Reset</button></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ACTION-LABEL")
    assert findings == []


# ---------------------------------------------------------------------------
# FORMS-ADDRESS-FORMAT
# ---------------------------------------------------------------------------


def test_address_format_combined_address_line_is_not_flagged():
    html = (
        '<form>'
        '<label for="st1">Street address</label><input id="st1" name="street">'
        '<label for="rg1">State</label><input id="rg1" name="region" required>'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ADDRESS-FORMAT")
    assert findings == []


def test_address_format_required_house_number_with_street_is_severity_3():
    html = (
        '<form>'
        '<label for="hn1">House number</label><input id="hn1" name="house" required>'
        '<label for="st2">Street address</label><input id="st2" name="street">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ADDRESS-FORMAT")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_address_format_optional_house_number_with_street_is_severity_2():
    html = (
        '<form>'
        '<label for="hn2">House number</label><input id="hn2" name="house">'
        '<label for="st3">Street address</label><input id="st3" name="street">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ADDRESS-FORMAT")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_address_format_house_number_without_street_is_not_flagged():
    html = '<form><label for="hn3">House number</label><input id="hn3" name="house" required></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ADDRESS-FORMAT")
    assert findings == []


def test_address_format_required_county_is_severity_2():
    html = '<form><label for="co2">County</label><input id="co2" name="county" required></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ADDRESS-FORMAT")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_address_format_optional_county_is_not_flagged():
    html = '<form><label for="co3">County</label><input id="co3" name="county"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ADDRESS-FORMAT")
    assert findings == []


def test_address_format_required_region_is_never_flagged():
    html = '<form><label for="rg2">State</label><input id="rg2" name="region" required></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-ADDRESS-FORMAT")
    assert findings == []


# ---------------------------------------------------------------------------
# FORMS-AUTOCOMPLETE
# ---------------------------------------------------------------------------


def test_autocomplete_valid_token_is_not_flagged():
    html = '<form><label for="ac1">Email address</label><input id="ac1" type="email" autocomplete="email"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCOMPLETE")
    assert findings == []


def test_autocomplete_missing_attribute_is_severity_2():
    html = '<form><label for="ac2">Email address</label><input id="ac2" type="email"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCOMPLETE")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_autocomplete_value_on_is_severity_2():
    html = '<form><label for="ac3">Email address</label><input id="ac3" type="email" autocomplete="on"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCOMPLETE")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_autocomplete_invalid_token_is_severity_3():
    html = '<form><label for="ac4">Email address</label><input id="ac4" type="email" autocomplete="email-address"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCOMPLETE")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_autocomplete_off_on_credential_field_is_severity_3():
    html = '<form><label for="un1">Username</label><input id="un1" type="text" name="username" autocomplete="off"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCOMPLETE")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_autocomplete_off_on_email_field_is_severity_2():
    html = '<form><label for="ac5">Email address</label><input id="ac5" type="email" autocomplete="off"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCOMPLETE")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_autocomplete_never_flags_one_time_code_even_when_off():
    html = '<form><label for="otp1">Verification code</label><input id="otp1" type="text" autocomplete="off"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCOMPLETE")
    assert findings == []


def test_autocomplete_never_flags_an_untracked_purpose():
    html = '<form><label for="q1">Search</label><input id="q1" type="search"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCOMPLETE")
    assert findings == []


def test_autocomplete_form_level_off_cascades_to_a_field_with_no_own_token():
    html = '<form autocomplete="off"><label for="sa1">Street address</label><input id="sa1" name="address"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCOMPLETE")
    assert len(findings) == 1
    assert findings[0].severity == 3


# ---------------------------------------------------------------------------
# FORMS-AUTOCORRECT
# ---------------------------------------------------------------------------


def test_autocorrect_clean_name_field_is_not_flagged():
    html = '<form><label for="fn1">First name</label><input id="fn1" type="text" autocorrect="off" spellcheck="false"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCORRECT")
    assert findings == []


def test_autocorrect_single_unprotected_field_is_severity_2():
    html = '<form><label for="em1">Email</label><input id="em1" name="email"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCORRECT")
    assert len(findings) == 1
    assert findings[0].severity == 2
    assert "autocorrection and spellchecking stay on" in findings[0].violation
    assert "auto-capitalization stays on" in findings[0].violation


def test_autocorrect_two_unprotected_fields_escalate_to_severity_3():
    html = (
        '<form>'
        '<label for="fn2">First name</label><input id="fn2" name="firstname">'
        '<label for="un2">Username</label><input id="un2" name="username">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCORRECT")
    assert len(findings) == 2
    assert all(f.severity == 3 for f in findings)


def test_autocorrect_caps_only_branch_is_severity_2():
    html = '<form><label for="em2">Email</label><input id="em2" name="email" autocorrect="off"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCORRECT")
    assert len(findings) == 1
    assert findings[0].severity == 2
    assert "auto-capitalization stays on" in findings[0].violation
    assert "autocorrection and spellchecking stay on" not in findings[0].violation


def test_autocorrect_never_flags_a_field_whose_type_is_not_text():
    html = '<form><label for="em3">Email</label><input id="em3" type="email"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCORRECT")
    assert findings == []


def test_autocorrect_never_flags_a_textarea():
    html = '<form><label for="addr1">Address</label><textarea id="addr1" autocomplete="street-address"></textarea></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCORRECT")
    assert findings == []


def test_autocorrect_name_field_is_exempt_from_the_capitalization_branch():
    html = '<form><label for="fn3">First name</label><input id="fn3" name="firstname" autocorrect="off"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCORRECT")
    assert findings == []


# ---------------------------------------------------------------------------
# FORMS-CONFIRM-PASSWORD
# ---------------------------------------------------------------------------


def test_confirm_password_a_lone_password_field_is_not_flagged():
    html = '<form><label for="pw1">Password</label><input id="pw1" type="password"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-CONFIRM-PASSWORD")
    assert findings == []


def test_confirm_password_current_then_new_is_never_flagged():
    html = (
        '<form>'
        '<label for="pw2">Current password</label><input id="pw2" type="password" autocomplete="current-password">'
        '<label for="pw3">New password</label><input id="pw3" type="password" autocomplete="new-password">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-CONFIRM-PASSWORD")
    assert findings == []


def test_confirm_password_confirm_cue_is_flagged_severity_2():
    html = (
        '<form>'
        '<label for="pw4">Password</label><input id="pw4" type="password">'
        '<label for="pw5">Confirm password</label><input id="pw5" type="password">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-CONFIRM-PASSWORD")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_confirm_password_both_tokens_new_password_is_flagged_severity_2():
    html = (
        '<form>'
        '<label for="pw6">Create password</label><input id="pw6" type="password" autocomplete="new-password">'
        '<label for="pw7">Create password</label><input id="pw7" type="password" autocomplete="new-password">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-CONFIRM-PASSWORD")
    assert len(findings) == 1
    assert findings[0].severity == 2


# ---------------------------------------------------------------------------
# FORMS-DATE-SELECTS
# ---------------------------------------------------------------------------


def test_date_selects_fewer_than_three_selects_is_not_flagged():
    html = (
        '<form>'
        f'<label for="d1">Day</label><select id="d1" name="day">{_opts(2)}</select>'
        f'<label for="m1">Month</label><select id="m1" name="month">{_opts(2)}</select>'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-DATE-SELECTS")
    assert findings == []


def test_date_selects_appointment_with_few_year_options_is_not_flagged():
    html = (
        '<form>'
        f'<label for="d2">Day</label><select id="d2" name="day">{_opts(2)}</select>'
        f'<label for="m2">Month</label><select id="m2" name="month">{_opts(2)}</select>'
        f'<label for="y2">Year</label><select id="y2" name="year">{_opts(5)}</select>'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-DATE-SELECTS")
    assert findings == []


def test_date_selects_birth_trio_with_few_year_options_is_severity_2():
    html = (
        '<form>'
        f'<label for="d3">Day of birth</label><select id="d3" name="day">{_opts(2)}</select>'
        f'<label for="m3">Month</label><select id="m3" name="month">{_opts(2)}</select>'
        f'<label for="y3">Year</label><select id="y3" name="year">{_opts(10)}</select>'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-DATE-SELECTS")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_date_selects_non_birth_trio_with_many_year_options_is_severity_3():
    html = (
        '<form>'
        f'<label for="d4">Day</label><select id="d4" name="day">{_opts(2)}</select>'
        f'<label for="m4">Month</label><select id="m4" name="month">{_opts(2)}</select>'
        f'<label for="y4">Year</label><select id="y4" name="year">{_opts(40)}</select>'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-DATE-SELECTS")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_date_selects_birth_detected_via_fieldset_legend():
    html = (
        '<form><fieldset><legend>Date of birth</legend>'
        f'<label for="d5">Day</label><select id="d5" name="day">{_opts(2)}</select>'
        f'<label for="m5">Month</label><select id="m5" name="month">{_opts(2)}</select>'
        f'<label for="y5">Year</label><select id="y5" name="year">{_opts(5)}</select>'
        '</fieldset></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-DATE-SELECTS")
    assert len(findings) == 1
    assert findings[0].severity == 2


# ---------------------------------------------------------------------------
# FORMS-FIELD-WIDTH
# ---------------------------------------------------------------------------


def test_field_width_normal_email_width_is_not_flagged():
    html = '<form><label for="em4">Email</label><input id="em4" type="email" name="email" size="25"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FIELD-WIDTH")
    assert findings == []


def test_field_width_narrow_phone_is_severity_3():
    html = '<form><label for="ph1">Phone</label><input id="ph1" type="tel" size="5"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FIELD-WIDTH")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_field_width_narrow_but_maxlength_shows_whole_value_is_never_flagged():
    html = '<form><label for="ph2">Phone</label><input id="ph2" type="tel" size="5" maxlength="5"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FIELD-WIDTH")
    assert findings == []


def test_field_width_wide_postal_code_is_severity_2():
    html = '<form><label for="pc1">Postal code</label><input id="pc1" name="postcode" size="30"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FIELD-WIDTH")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_field_width_wide_day_is_severity_2():
    html = '<form><label for="day1">Day</label><input id="day1" name="day" size="10"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FIELD-WIDTH")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_field_width_never_flags_an_untracked_purpose():
    html = '<form><label for="nm1">Full name</label><input id="nm1" autocomplete="name" size="200"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FIELD-WIDTH")
    assert findings == []


def test_field_width_css_ch_unit_narrow_phone_is_severity_3():
    html = (
        '<style>.narrowphone { width: 8ch; }</style>'
        '<form><label for="ph3">Phone</label><input id="ph3" type="tel" class="narrowphone"></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FIELD-WIDTH")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_field_width_never_reads_a_px_declared_width():
    html = '<form><label for="ph4">Phone</label><input id="ph4" type="tel" style="width: 40px;"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FIELD-WIDTH")
    assert findings == []


# ---------------------------------------------------------------------------
# FORMS-FORMAT-TOLERANCE
# ---------------------------------------------------------------------------


def test_format_tolerance_permissive_phone_pattern_is_not_flagged():
    html = '<form><label for="ph5">Phone</label><input id="ph5" type="tel" pattern=".*"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FORMAT-TOLERANCE")
    assert findings == []


def test_format_tolerance_phone_pattern_rejecting_valid_formats_is_severity_3():
    html = '<form><label for="ph6">Phone</label><input id="ph6" type="tel" pattern="[0-9]+"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FORMAT-TOLERANCE")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_format_tolerance_name_pattern_rejecting_valid_names_is_severity_3():
    html = '<form><label for="nm2">Full name</label><input id="nm2" autocomplete="name" pattern="[A-Za-z]+"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FORMAT-TOLERANCE")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_format_tolerance_postal_code_with_country_choice_rejecting_letters_is_severity_3():
    html = (
        '<form>'
        '<label for="pc2">Postal code</label><input id="pc2" name="postcode" pattern="[0-9]+">'
        '<label for="co4">Country</label><select id="co4" name="country">'
        '<option value="us">United States</option><option value="gb">United Kingdom</option></select>'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FORMAT-TOLERANCE")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_format_tolerance_never_judges_postal_code_pattern_without_a_country_choice():
    html = '<form><label for="pc3">Postal code</label><input id="pc3" name="postcode" pattern="[0-9]+"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FORMAT-TOLERANCE")
    assert findings == []


def test_format_tolerance_email_maxlength_below_254_is_severity_2():
    html = '<form><label for="em5">Email</label><input id="em5" type="email" maxlength="50"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FORMAT-TOLERANCE")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_format_tolerance_email_maxlength_254_is_not_flagged():
    html = '<form><label for="em6">Email</label><input id="em6" type="email" maxlength="254"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FORMAT-TOLERANCE")
    assert findings == []


def test_format_tolerance_uncompilable_pattern_is_not_judged():
    html = '<form><label for="ph7">Phone</label><input id="ph7" type="tel" pattern="(unclosed"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FORMAT-TOLERANCE")
    assert findings == []


def test_format_tolerance_v_mode_rejected_pattern_is_not_judged():
    """The name pattern ends its character class with an unescaped hyphen
    immediately before the closing bracket, which the browser's v-flag
    syntax rejects. A pattern the browser cannot compile rejects nothing
    and references/FORMS.md says such a pattern is not judged, so this
    field must produce no finding even though the pattern would reject
    several of FORMS-FORMAT-TOLERANCE's own name samples if it compiled."""
    html = '<form><label for="nm3">Full name</label><input id="nm3" autocomplete="name" pattern="[A-Za-z\' -]+"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-FORMAT-TOLERANCE")
    assert findings == []


# ---------------------------------------------------------------------------
# FORMS-INPUT-FONT-SIZE
# ---------------------------------------------------------------------------


def test_input_font_size_no_declared_css_is_not_flagged():
    html = '<form><label for="f1">Name</label><input id="f1" type="text"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-FONT-SIZE")
    assert findings == []


def test_input_font_size_16px_is_not_flagged():
    html = '<form><label for="f2">Name</label><input id="f2" type="text" style="font-size: 16px;"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-FONT-SIZE")
    assert findings == []


def test_input_font_size_14px_is_severity_2():
    html = '<form><label for="f3">Name</label><input id="f3" type="text" style="font-size: 14px;"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-FONT-SIZE")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_input_font_size_10px_is_severity_3():
    html = '<form><label for="f4">Name</label><input id="f4" type="text" style="font-size: 10px;"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-FONT-SIZE")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_input_font_size_exactly_12px_boundary_is_severity_2():
    html = '<form><label for="f5">Name</label><input id="f5" type="text" style="font-size: 12px;"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-FONT-SIZE")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_input_font_size_just_below_12px_is_severity_3():
    # Pins the severity-3 line itself: 10px alone would still pass if the line moved to 11.
    html = '<form><label for="f5b">Name</label><input id="f5b" type="text" style="font-size: 11.5px;"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-FONT-SIZE")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_input_font_size_just_below_16px_is_severity_2():
    html = '<form><label for="f5c">Name</label><input id="f5c" type="text" style="font-size: 15.5px;"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-FONT-SIZE")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_input_font_size_em_unit_below_12px_equivalent_is_severity_3():
    html = '<form><label for="f6">Name</label><input id="f6" type="text" style="font-size: 0.5em;"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-FONT-SIZE")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_input_font_size_pt_unit_at_12px_equivalent_is_severity_2():
    html = '<form><label for="f7">Name</label><input id="f7" type="text" style="font-size: 9pt;"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-FONT-SIZE")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_input_font_size_never_reads_an_unsupported_unit():
    html = '<form><label for="f8">Name</label><input id="f8" type="text" style="font-size: 1.2vw;"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-FONT-SIZE")
    assert findings == []


# ---------------------------------------------------------------------------
# FORMS-INPUT-TYPE
# ---------------------------------------------------------------------------


def test_input_type_correct_types_are_not_flagged():
    html = (
        '<form>'
        '<label for="em7">Email</label><input id="em7" type="email">'
        '<label for="ph8">Phone</label><input id="ph8" type="tel">'
        '<label for="ur1">Website</label><input id="ur1" type="url">'
        '<label for="se1">Search</label><input id="se1" type="search">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-TYPE")
    assert findings == []


def test_input_type_single_mismatch_is_severity_2():
    html = '<form><label for="em8">Email</label><input id="em8" type="text"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-TYPE")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_input_type_two_mismatches_escalate_to_severity_3():
    html = (
        '<form>'
        '<label for="em9">Email</label><input id="em9" type="text">'
        '<label for="ph9">Phone</label><input id="ph9" type="text">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-TYPE")
    assert len(findings) == 2
    assert all(f.severity == 3 for f in findings)


def test_input_type_number_type_on_a_phone_field_is_flagged():
    html = '<form><label for="ph10">Phone</label><input id="ph10" type="number"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-INPUT-TYPE")
    assert len(findings) == 1
    assert findings[0].severity == 2


# ---------------------------------------------------------------------------
# FORMS-NUMERIC-INPUTMODE
# ---------------------------------------------------------------------------


def test_numeric_inputmode_clean_one_time_code_is_not_flagged():
    html = '<form><label for="otp2">Verification code</label><input id="otp2" type="text" inputmode="numeric"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-NUMERIC-INPUTMODE")
    assert findings == []


def test_numeric_inputmode_number_type_on_one_time_code_is_severity_3():
    html = '<form><label for="otp3">One-time code</label><input id="otp3" type="number"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-NUMERIC-INPUTMODE")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_numeric_inputmode_missing_inputmode_on_account_number_is_severity_2():
    html = '<form><label for="acct1">Account number</label><input id="acct1" type="text"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-NUMERIC-INPUTMODE")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_numeric_inputmode_never_flags_a_quantity():
    html = '<form><label for="qty1">Quantity</label><input id="qty1" type="text"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-NUMERIC-INPUTMODE")
    assert findings == []


def test_numeric_inputmode_never_flags_a_phone_number():
    html = '<form><label for="ph11">Phone</label><input id="ph11" type="number"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-NUMERIC-INPUTMODE")
    assert findings == []


# ---------------------------------------------------------------------------
# FORMS-OPTION-CONTROL
# ---------------------------------------------------------------------------


def test_option_control_five_options_is_not_flagged():
    html = (
        '<form><select id="sel1">'
        '<option value="a">A</option><option value="b">B</option><option value="c">C</option>'
        '<option value="d">D</option><option value="e">E</option>'
        '</select></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-OPTION-CONTROL")
    assert findings == []


def test_option_control_one_real_option_is_not_flagged():
    html = '<form><select id="sel2"><option value="">Choose</option><option value="a">Only</option></select></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-OPTION-CONTROL")
    assert findings == []


def test_option_control_zero_real_options_is_not_flagged():
    html = '<form><select id="sel3"><option value="">Choose</option></select></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-OPTION-CONTROL")
    assert findings == []


def test_option_control_three_options_is_severity_2():
    html = (
        '<form><select id="sel4">'
        '<option value="a">A</option><option value="b">B</option><option value="c">C</option>'
        '</select></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-OPTION-CONTROL")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_option_control_two_selects_in_range_escalate_to_severity_3():
    html = (
        '<form>'
        '<select id="sel5"><option value="a">A</option><option value="b">B</option></select>'
        '<select id="sel6"><option value="a">A</option><option value="b">B</option><option value="c">C</option></select>'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-OPTION-CONTROL")
    assert len(findings) == 2
    assert all(f.severity == 3 for f in findings)


def test_option_control_never_flags_a_multiple_select():
    html = (
        '<form><select id="sel7" multiple>'
        '<option value="a">A</option><option value="b">B</option><option value="c">C</option>'
        '</select></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-OPTION-CONTROL")
    assert findings == []


def test_option_control_excludes_the_empty_placeholder_from_the_count():
    html = (
        '<form><select id="sel8">'
        '<option value="">Please select</option>'
        '<option value="a">A</option><option value="b">B</option><option value="c">C</option>'
        '</select></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-OPTION-CONTROL")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_option_control_excludes_a_disabled_option_from_the_count():
    html = (
        '<form><select id="sel9">'
        '<option value="a">A</option><option value="b">B</option><option value="c" disabled>C</option>'
        '</select></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-OPTION-CONTROL")
    assert len(findings) == 1
    assert findings[0].severity == 2


# ---------------------------------------------------------------------------
# FORMS-PASSWORD-RULES
# ---------------------------------------------------------------------------


def test_password_rules_clean_new_password_is_not_flagged():
    html = (
        '<form><label for="npw1">Create a password</label>'
        '<input id="npw1" type="password" autocomplete="new-password" minlength="10"></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PASSWORD-RULES")
    assert findings == []


def test_password_rules_short_minlength_is_severity_2():
    html = (
        '<form><label for="npw2">Create a password</label>'
        '<input id="npw2" type="password" autocomplete="new-password" minlength="6"></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PASSWORD-RULES")
    assert len(findings) == 1
    assert findings[0].severity == 2
    assert "the minimum length is only 6" in findings[0].violation


def test_password_rules_pattern_is_severity_3():
    html = (
        '<form><label for="npw3">Create a password</label>'
        '<input id="npw3" type="password" autocomplete="new-password" pattern="(?=.*[A-Z]).+"></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PASSWORD-RULES")
    assert len(findings) == 1
    assert findings[0].severity == 3
    assert "a pattern forces a composition rule" in findings[0].violation


def test_password_rules_maxlength_is_severity_3():
    html = (
        '<form><label for="npw4">Create a password</label>'
        '<input id="npw4" type="password" autocomplete="new-password" maxlength="20"></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PASSWORD-RULES")
    assert len(findings) == 1
    assert findings[0].severity == 3
    assert "a maximum length of 20 cuts long passwords short" in findings[0].violation


def test_password_rules_never_flags_a_confirmation_field():
    html = (
        '<form>'
        '<label for="npw5">Create a password</label><input id="npw5" type="password" autocomplete="new-password">'
        '<label for="npw6">Confirm password</label>'
        '<input id="npw6" type="password" autocomplete="new-password" pattern="(?=.*[A-Z]).+">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PASSWORD-RULES")
    assert findings == []


def test_password_rules_combined_branches_report_one_finding_at_the_worst_severity():
    html = (
        '<form><label for="npw7">Create a password</label>'
        '<input id="npw7" type="password" autocomplete="new-password" pattern="(?=.*[A-Z]).+" minlength="6"></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PASSWORD-RULES")
    assert len(findings) == 1
    assert findings[0].severity == 3
    assert "a pattern forces a composition rule" in findings[0].violation
    assert "the minimum length is only 6" in findings[0].violation


# ---------------------------------------------------------------------------
# FORMS-PHONE-REASON
# ---------------------------------------------------------------------------


def test_phone_reason_reason_in_label_is_not_flagged():
    html = (
        '<form><label for="ph12">Phone number (so we can contact you about delivery)</label>'
        '<input id="ph12" type="tel" required></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PHONE-REASON")
    assert findings == []


def test_phone_reason_unexplained_with_no_email_in_form_is_severity_2():
    html = '<form><label for="ph13">Phone</label><input id="ph13" type="tel" required></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PHONE-REASON")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_phone_reason_unexplained_with_email_also_in_form_is_severity_3():
    html = (
        '<form>'
        '<label for="em10">Email</label><input id="em10" type="email">'
        '<label for="ph14">Phone</label><input id="ph14" type="tel" required>'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PHONE-REASON")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_phone_reason_never_flags_an_optional_phone_field():
    html = '<form><label for="ph15">Phone</label><input id="ph15" type="tel"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PHONE-REASON")
    assert findings == []


def test_phone_reason_reason_via_aria_describedby_is_not_flagged():
    html = (
        '<form><label for="ph16">Phone</label>'
        '<input id="ph16" type="tel" required aria-describedby="ph16-hint">'
        '<p id="ph16-hint">We will call you about delivery.</p>'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PHONE-REASON")
    assert findings == []


def test_phone_reason_reason_via_own_group_text_is_not_flagged():
    html = (
        '<form><div>'
        '<label for="ph17">Phone</label> <input id="ph17" type="tel" required> '
        '<span>used to confirm your order</span>'
        '</div></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PHONE-REASON")
    assert findings == []


def test_phone_reason_own_group_text_ignored_when_parent_holds_another_control():
    html = (
        '<form><div>'
        '<label for="ph18">Phone</label> <input id="ph18" type="tel" required> '
        '<label for="em11">Email</label> <input id="em11" type="email"> '
        '<span>used to contact you</span>'
        '</div></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PHONE-REASON")
    assert len(findings) == 1
    assert findings[0].severity == 3


# ---------------------------------------------------------------------------
# FORMS-PLACEHOLDER-INSTRUCTION
# ---------------------------------------------------------------------------


def test_placeholder_instruction_benign_placeholder_is_not_flagged():
    html = '<form><label for="nm4">Nickname</label><input id="nm4" type="text" placeholder="Enter your nickname"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PLACEHOLDER-INSTRUCTION")
    assert findings == []


def test_placeholder_instruction_rule_only_in_placeholder_is_severity_3():
    html = '<form><label for="pw8">Password</label><input id="pw8" type="password" placeholder="Must be at least 8 characters"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PLACEHOLDER-INSTRUCTION")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_placeholder_instruction_example_only_in_placeholder_is_severity_2():
    html = '<form><label for="em17">Email</label><input id="em17" type="email" placeholder="e.g. jane@example.com"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PLACEHOLDER-INSTRUCTION")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_placeholder_instruction_never_flags_when_guidance_duplicates_the_rule():
    html = (
        '<form><label for="pw9">Password (at least 8 characters)</label>'
        '<input id="pw9" type="password" placeholder="Must be at least 8 characters"></form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PLACEHOLDER-INSTRUCTION")
    assert findings == []


def test_placeholder_instruction_never_flags_an_unlabeled_field():
    html = '<form><input id="pw10" type="password" placeholder="Must be at least 8 characters"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PLACEHOLDER-INSTRUCTION")
    assert findings == []


def test_placeholder_instruction_never_flags_a_field_with_no_placeholder():
    html = '<form><label for="nm5">Nickname</label><input id="nm5" type="text"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-PLACEHOLDER-INSTRUCTION")
    assert findings == []


# ---------------------------------------------------------------------------
# FORMS-REQUIRED-OPTIONAL
# ---------------------------------------------------------------------------


def test_required_optional_all_fields_marked_in_words_is_not_flagged():
    html = (
        '<form>'
        '<label for="ro1">Full name (required)</label><input id="ro1" type="text" required>'
        '<label for="ro2">Company (optional)</label><input id="ro2" type="text">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-REQUIRED-OPTIONAL")
    assert findings == []


def test_required_optional_asterisk_unexplained_is_severity_2():
    html = (
        '<form>'
        '<label for="a1">Name *</label><input id="a1" type="text" required>'
        '<label for="a2">Company (optional)</label><input id="a2" type="text">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-REQUIRED-OPTIONAL")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_required_optional_never_flags_an_explained_asterisk():
    html = (
        '<form>'
        '<p>Fields marked with * are required.</p>'
        '<label for="a3">Name *</label><input id="a3" type="text" required>'
        '<label for="a4">Company (optional)</label><input id="a4" type="text">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-REQUIRED-OPTIONAL")
    assert findings == []


def test_required_optional_placeholder_only_marker_is_severity_2():
    html = (
        '<form>'
        '<label for="b1">Name</label><input id="b1" type="text" required placeholder="Required">'
        '<label for="b2">Company (optional)</label><input id="b2" type="text">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-REQUIRED-OPTIONAL")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_required_optional_two_placeholder_only_markers_are_two_separate_findings():
    html = (
        '<form>'
        '<label for="c1">Name</label><input id="c1" type="text" required placeholder="Required">'
        '<label for="c2">Email</label><input id="c2" type="text" required placeholder="Required">'
        '<label for="c3">Company (optional)</label><input id="c3" type="text">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-REQUIRED-OPTIONAL")
    assert len(findings) == 2
    assert all(f.severity == 2 for f in findings)
    assert all(not f.instances for f in findings)


# ---------------------------------------------------------------------------
# FORMS-RESET-BUTTON
# ---------------------------------------------------------------------------


def test_reset_button_no_reset_control_is_not_flagged():
    html = '<form><label for="nm6">Name</label><input id="nm6" type="text"><button type="submit">Create account</button></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-RESET-BUTTON")
    assert findings == []


def test_reset_button_far_from_submit_is_severity_2():
    html = (
        '<form>'
        '<div><button type="submit">Create account</button></div>'
        '<div><button type="reset">Reset</button></div>'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-RESET-BUTTON")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_reset_button_adjacent_to_submit_via_type_reset_is_severity_3():
    html = '<form><button type="submit">Create account</button><button type="reset">Reset</button></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-RESET-BUTTON")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_reset_button_adjacent_to_submit_via_clear_all_label_is_severity_3():
    html = '<form><button type="submit">Send</button><button type="button">Clear all</button></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-RESET-BUTTON")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_reset_button_never_flags_an_icon_button_named_clear_only_by_aria_label():
    html = (
        '<form>'
        '<label for="sq1">Search</label><input id="sq1" type="search">'
        '<button type="button" aria-label="Clear">X</button>'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-RESET-BUTTON")
    assert findings == []


# ---------------------------------------------------------------------------
# FORMS-SPLIT-ENTITY
# ---------------------------------------------------------------------------


def test_split_entity_two_single_char_fields_is_not_flagged():
    html = (
        '<form>'
        '<label for="s1">Code 1</label><input id="s1" type="text" maxlength="1">'
        '<label for="s2">Code 2</label><input id="s2" type="text" maxlength="1">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-SPLIT-ENTITY")
    assert findings == []


def test_split_entity_three_single_char_fields_is_severity_2():
    html = (
        '<form>'
        '<label for="s3">Code 1</label><input id="s3" type="text" maxlength="1">'
        '<label for="s4">Code 2</label><input id="s4" type="text" maxlength="1">'
        '<label for="s5">Code 3</label><input id="s5" type="text" maxlength="1">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-SPLIT-ENTITY")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_split_entity_phone_part_tokens_is_severity_2():
    html = (
        '<form>'
        '<label for="pa1">Area code</label><input id="pa1" type="text" autocomplete="tel-area-code">'
        '<label for="pa2">Local number</label><input id="pa2" type="text" autocomplete="tel-local-prefix">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-SPLIT-ENTITY")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_split_entity_phone_purpose_with_short_maxlength_is_severity_2():
    html = (
        '<form>'
        '<label for="pb1">Phone</label><input id="pb1" type="text" maxlength="4">'
        '<label for="pb2">Phone</label><input id="pb2" type="text" maxlength="4">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-SPLIT-ENTITY")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_split_entity_never_flags_two_full_length_phone_fields():
    html = (
        '<form>'
        '<label for="hp1">Home phone</label><input id="hp1" type="tel">'
        '<label for="hp2">Mobile phone</label><input id="hp2" type="tel">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-SPLIT-ENTITY")
    assert findings == []


def test_split_entity_given_and_family_name_split_is_severity_2():
    html = (
        '<form>'
        '<label for="n1">First name</label><input id="n1" type="text">'
        '<label for="n2">Last name</label><input id="n2" type="text">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-SPLIT-ENTITY")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_split_entity_never_flags_two_given_names_only():
    html = (
        '<form>'
        '<label for="n3">First name</label><input id="n3" type="text">'
        '<label for="n4">Middle name</label><input id="n4" type="text">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-SPLIT-ENTITY")
    assert findings == []


def test_split_entity_never_flags_day_month_year_fields():
    html = (
        '<form>'
        '<label for="d6">Day</label><input id="d6" type="text" maxlength="2">'
        '<label for="d7">Month</label><input id="d7" type="text" maxlength="2">'
        '<label for="d8">Year</label><input id="d8" type="text" maxlength="4">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-SPLIT-ENTITY")
    assert findings == []


def test_split_entity_two_runs_escalate_to_severity_3():
    html = (
        '<form>'
        '<label for="r1">Code 1</label><input id="r1" type="text" maxlength="1">'
        '<label for="r2">Code 2</label><input id="r2" type="text" maxlength="1">'
        '<label for="r3">Code 3</label><input id="r3" type="text" maxlength="1">'
        '<label for="r4">Area code</label><input id="r4" type="text" autocomplete="tel-area-code">'
        '<label for="r5">Local number</label><input id="r5" type="text" autocomplete="tel-local-prefix">'
        '</form>'
    )
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-SPLIT-ENTITY")
    assert len(findings) == 2
    assert all(f.severity == 3 for f in findings)


# ---------------------------------------------------------------------------
# Purpose heuristic: references/FORMS.md, "How a field's purpose is read"
# ---------------------------------------------------------------------------


def test_purpose_bare_name_label_reads_as_name():
    html = '<form><label for="p1">Name</label><input id="p1"></form>'
    assert _control_purpose(html, "p1") == "name"


def test_purpose_company_name_does_not_read_as_name():
    html = '<form><label for="p2">Company name</label><input id="p2"></form>'
    assert _control_purpose(html, "p2") is None


def test_purpose_joined_cue_firstname_reads_as_name():
    html = '<form><input id="p3" name="firstname"></form>'
    assert _control_purpose(html, "p3") == "name"


def test_purpose_joined_cue_phonenumber_reads_as_phone():
    html = '<form><input id="p4" name="phonenumber"></form>'
    assert _control_purpose(html, "p4") == "phone"


def test_purpose_label_marker_word_is_ignored_phone_required():
    html = '<form><label for="p5">Phone (required)</label><input id="p5"></form>'
    assert _control_purpose(html, "p5") == "phone"


def test_purpose_user_name_reads_as_username_not_name():
    html = '<form><label for="p6">User name</label><input id="p6"></form>'
    assert _control_purpose(html, "p6") == "username"


def test_purpose_textarea_state_your_reason_has_no_purpose():
    html = '<form><label for="p7">State your reason</label><textarea id="p7"></textarea></form>'
    assert _control_purpose(html, "p7") is None


def test_purpose_textarea_with_street_address_token_has_a_purpose():
    html = '<form><label for="p8">Address</label><textarea id="p8" autocomplete="street-address"></textarea></form>'
    assert _control_purpose(html, "p8") == "street address"


def test_purpose_password_followed_by_confirm_is_new_password():
    html = (
        '<form>'
        '<label for="p9">Password</label><input id="p9" type="password">'
        '<label for="p10">Confirm password</label><input id="p10" type="password">'
        '</form>'
    )
    assert _control_purpose(html, "p9") == "new password"


def test_purpose_lone_password_is_current_password():
    html = '<form><label for="p11">Password</label><input id="p11" type="password"></form>'
    assert _control_purpose(html, "p11") == "current password"


def test_purpose_autocomplete_token_outranks_the_name_attribute():
    html = '<form><input id="p12" name="username" autocomplete="email"></form>'
    assert _control_purpose(html, "p12") == "email"


# ---------------------------------------------------------------------------
# checks._v_mode_rejects: the browser's v-flag character-class syntax
# ---------------------------------------------------------------------------


def test_v_mode_rejects_digit_range_is_judged():
    assert checks._v_mode_rejects("[0-9]+") is False


def test_v_mode_rejects_letter_range_is_judged():
    assert checks._v_mode_rejects("[A-Za-z]+") is False


def test_v_mode_rejects_word_class_with_bare_trailing_hyphen_is_rejected():
    assert checks._v_mode_rejects(r"[\w-]+") is True


def test_v_mode_rejects_letter_range_with_trailing_hyphen_is_rejected():
    assert checks._v_mode_rejects("[A-Za-z-]+") is True


def test_v_mode_rejects_escaped_hyphen_is_judged():
    assert checks._v_mode_rejects("[a-z\\-]+") is False


# ---------------------------------------------------------------------------
# Instance shape: through run_scripted_lane, so the contract validator
# sees the envelope's actual `instances` arrays.
# ---------------------------------------------------------------------------


def test_required_optional_no_marking_four_fields_is_one_finding_with_three_instances(tmp_path, monkeypatch, capsys):
    html = (
        '<form>'
        '<label for="f1">First name</label><input id="f1" type="text">'
        '<label for="f2">Last name</label><input id="f2" type="text" required>'
        '<label for="f3">Email</label><input id="f3" type="text">'
        '<label for="f4">Phone</label><input id="f4" type="text" required>'
        '</form>'
    )
    envelope = _run_lane(html, tmp_path, monkeypatch, capsys)
    matches = [f for f in envelope["findings"] if f["criterion"] == "FORMS-REQUIRED-OPTIONAL"]
    assert len(matches) == 1
    assert matches[0]["severity"] == 3
    assert len(matches[0]["instances"]) == 3


def test_required_optional_one_required_one_optional_is_two_findings_with_no_instances(tmp_path, monkeypatch, capsys):
    html = (
        '<form>'
        '<label for="g1">Name</label><input id="g1" type="text" required>'
        '<label for="g2">Company</label><input id="g2" type="text">'
        '</form>'
    )
    envelope = _run_lane(html, tmp_path, monkeypatch, capsys)
    matches = [f for f in envelope["findings"] if f["criterion"] == "FORMS-REQUIRED-OPTIONAL"]
    assert len(matches) == 2
    assert all(f["severity"] == 3 for f in matches)
    assert all("instances" not in f for f in matches)


def test_input_font_size_one_stylesheet_rule_over_three_inputs_is_one_finding_with_two_instances(tmp_path, monkeypatch, capsys):
    html = (
        '<style>input { font-size: 14px; }</style>'
        '<form>'
        '<label for="i1">First name</label><input id="i1" type="text">'
        '<label for="i2">Last name</label><input id="i2" type="text">'
        '<label for="i3">Email</label><input id="i3" type="email">'
        '</form>'
    )
    envelope = _run_lane(html, tmp_path, monkeypatch, capsys)
    matches = [f for f in envelope["findings"] if f["criterion"] == "FORMS-INPUT-FONT-SIZE"]
    assert len(matches) == 1
    assert matches[0]["severity"] == 2
    assert len(matches[0]["instances"]) == 2


# ---------------------------------------------------------------------------
# Determinism: same artifact, same output bytes, across two runs.
# ---------------------------------------------------------------------------

SEEDED_FORM = """<!DOCTYPE html>
<html lang="en">
<body>
<form>
<label for="sf-name">Name</label>
<input id="sf-name" name="name">
<label for="sf-house">House number</label>
<input id="sf-house" name="house_number" required>
<label for="sf-street">Street address</label>
<input id="sf-street" name="street">
<label for="sf-email">Email</label>
<input id="sf-email" type="text" name="email">
<label for="sf-phone">Phone</label>
<input id="sf-phone" type="number" required>
<label for="sf-pw">Password</label>
<input id="sf-pw" type="password" autocomplete="new-password" minlength="4">
<label for="sf-pw2">Confirm password</label>
<input id="sf-pw2" type="password" autocomplete="new-password">
<label for="sf-otp">Verification code</label>
<input id="sf-otp" type="number">
<button type="submit">Submit</button>
<button type="reset">Reset</button>
</form>
</body>
</html>
"""


def test_direct_check_call_is_deterministic_across_two_runs():
    first = checks.check(_artifact(SEEDED_FORM))
    second = checks.check(_artifact(SEEDED_FORM))
    assert first == second
    assert len(first) > 10  # a real cross-criterion mix, not an accidental empty match


def test_run_scripted_lane_is_deterministic_across_two_runs(tmp_path, monkeypatch, capsys):
    target = tmp_path / "seeded.html"
    target.write_text(SEEDED_FORM, encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    def run_once():
        run_scripted_lane(
            skill_name="critique-forms",
            skill_version="0.1.0",
            rubrics=["FORMS"],
            check_fn=checks.check,
            argv=[str(target)],
            now=FIXED_NOW,
        )
        return capsys.readouterr().out

    first = run_once()
    second = run_once()
    assert first == second
    assert json.loads(first)["run"]["skill"] == "critique-forms"


# ---------------------------------------------------------------------------
# Contract prose rules: scripted lane, high confidence, a bounded and
# navigable location, and no en or em dash in any prose field.
# ---------------------------------------------------------------------------


def test_every_finding_from_a_many_defect_form_meets_the_contract_prose_rules():
    findings = checks.check(_artifact(SEEDED_FORM))
    assert findings
    for finding in findings:
        assert finding.lane == "scripted"
        assert finding.confidence == "high"
        assert len(finding.location) <= 400
        for field in (finding.location, finding.evidence, finding.violation, finding.fix):
            assert "\u2013" not in field
            assert "\u2014" not in field


def test_an_en_dash_in_an_autocomplete_value_still_produces_dash_free_prose():
    value = "ema\u2013il"
    html = f'<form><label for="dash1">Email</label><input id="dash1" type="email" autocomplete="{value}"></form>'
    findings = _by_criterion(checks.check(_artifact(html)), "FORMS-AUTOCOMPLETE")
    assert len(findings) == 1
    assert findings[0].severity == 3
    assert "\u2013" not in findings[0].violation
    assert "\u2014" not in findings[0].violation
    assert "ema-il" in findings[0].violation
