"""Tests for contract/evidence.py, the E24 evidence-quotes-not-characterizes check.

Three groups: unit tests pinning the classifier's three quotation tiers and its measurement
patterns on synthetic strings; an enforcement test that runs the real classifier over every
authored fixture in scope (skills/**/examples/golden-*.json and every resolving
examples/<domain>/envelope.json), against a maintainer-reviewed allowlist of genuine breaches; and
a smoke test for the report CLI over one small committed bench run folder.
"""

from __future__ import annotations

import pytest

from contract.evidence import (
    REPO_ROOT,
    classify_evidence,
    iter_enforced_fixture_findings,
    main as evidence_main,
    report_bench_envelopes,
)

CURLY_LEFT_DOUBLE = chr(0x201C)
CURLY_RIGHT_DOUBLE = chr(0x201D)


# --------------------------------------------------------------------------
# Passing quotations
# --------------------------------------------------------------------------


def test_exact_quotation_passes():
    verdict = classify_evidence(
        "The system routes new tickets to the queue.",
        "Before the change, nothing moved. The system routes new tickets to the queue. "
        "Nothing else happens.",
    )
    assert verdict.verdict == "quotation"


def test_whitespace_varied_quotation_passes():
    """Evidence wraps the quote across what would be two lines; the artifact has it on one.
    Both are collapsed to single spaces before comparison, so the difference does not matter."""
    verdict = classify_evidence(
        "Reach the Riverbend\n   Water Utility service desk",
        "Reach the Riverbend Water Utility service desk using the form below.",
    )
    assert verdict.verdict == "quotation"


def test_ellipsis_split_quotation_passes():
    """An elided middle, written with ASCII ellipsis, is tried as two independent segments; the
    first segment alone is long enough and verbatim, so the whole evidence passes."""
    verdict = classify_evidence(
        "Reach the Riverbend Water ... service desk using the form below",
        "Reach the Riverbend Water Utility service desk using the form below, or browse updates.",
    )
    assert verdict.verdict == "quotation"


def test_unicode_ellipsis_split_quotation_passes():
    verdict = classify_evidence(
        f"Reach the Riverbend Water {chr(0x2026)} service desk using the form below",
        "Reach the Riverbend Water Utility service desk using the form below, or browse updates.",
    )
    assert verdict.verdict == "quotation"


def test_curly_quotes_in_evidence_match_straight_quotes_in_artifact():
    verdict = classify_evidence(
        f"{CURLY_LEFT_DOUBLE}Save{CURLY_RIGHT_DOUBLE}",
        'The commit button reads "Save" in the corner.',
    )
    assert verdict.verdict == "quotation"


def test_curly_quotes_in_artifact_match_straight_quotes_in_evidence():
    verdict = classify_evidence(
        "Save",
        f"The commit button reads {CURLY_LEFT_DOUBLE}Save{CURLY_RIGHT_DOUBLE} in the corner.",
    )
    assert verdict.verdict == "quotation"


def test_short_quoted_label_value_passes():
    """A short structured line such as 'control labeled "Save"' is not itself artifact text, but
    the quoted value is; the writer's own label does not need to match anything."""
    verdict = classify_evidence(
        'control labeled "Save"',
        "<button type=\"submit\">Save</button>",
    )
    assert verdict.verdict == "quotation"


def test_bare_short_word_quotation_passes_as_whole_segment():
    """A whole evidence value this short contributes no characterizing language of its own, so no
    length floor applies to a full match."""
    verdict = classify_evidence("Error", 'The error text reads only "Error" and nothing else.')
    assert verdict.verdict == "quotation"


# --------------------------------------------------------------------------
# Passing measurements
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "evidence",
    [
        "text color #8a8a8a on background #f5f5f5, contrast ratio 2.9:1",
        "37 words in the paragraph",
        "3 of 5 images carry no alt text",
        "font size is 12px here",
        "82 percent of users agreed",
        "6 of 10 sentences (0.60) carry at least one hedging term",
        "table with 3 rows and 3 columns, no th present",
        "2 focusable element(s) precede the first heading",
    ],
)
def test_measurement_patterns_pass(evidence):
    verdict = classify_evidence(evidence, "an artifact sharing no text with the evidence at all")
    assert verdict.verdict == "measurement", f"expected a measurement verdict for {evidence!r}"


# --------------------------------------------------------------------------
# Failing characterizations
# --------------------------------------------------------------------------


def test_contract_canonical_characterization_example_fails():
    """docs/reference/critique-contract.md's own example of contract-breaking evidence."""
    verdict = classify_evidence(
        "The contrast seems low",
        "An unrelated artifact describing a checkout flow with no overlapping wording.",
    )
    assert verdict.verdict == "characterization"


def test_characterization_fails_even_when_artifact_contains_one_shared_word():
    """A single shared word (here, 'contrast', 8 letters) must never be enough on its own: the
    long-quote tier requires 12 non-space characters precisely so this stays a characterization."""
    verdict = classify_evidence(
        "The contrast seems low",
        "This design brief discusses contrast and spacing choices at length, among other topics.",
    )
    assert verdict.verdict == "characterization"


def test_vague_opinion_with_no_digits_fails():
    verdict = classify_evidence("This feels confusing to read", "Some unrelated artifact text.")
    assert verdict.verdict == "characterization"


def test_bare_number_with_no_unit_or_quote_fails():
    """A number alone, with no counted noun and no ratio or size unit, is a location reference
    (e.g. 'paragraph 1'), not a measurement; it must not pass on the digit alone."""
    verdict = classify_evidence("paragraph 1 feels off", "Some unrelated artifact text.")
    assert verdict.verdict == "characterization"


# --------------------------------------------------------------------------
# Enforcement over every authored fixture in scope
# --------------------------------------------------------------------------

# Genuine contract breaches found by running this classifier over every enforced fixture,
# reviewed by hand and kept here rather than fixed in place because another agent owns fixture
# file edits concurrently (see the E24 backlog entry for the ruling). Each key is
# (fixture path relative to the repo root, finding id); the value is why it breaches the
# contract. Empty on first landing: every evidence string in every enforced fixture classified as
# a quotation or a measurement, so there is nothing to list. If a fixture edit later introduces a
# real breach, add it here with one line naming the reason, never by weakening the classifier.
ALLOWLISTED_BREACHES: dict[tuple[str, str], str] = {}


def test_evidence_quotes_not_characterizes_over_enforced_fixtures():
    findings = list(iter_enforced_fixture_findings())
    # A path or discovery bug could make this vacuously pass by finding nothing; guard against it.
    assert len(findings) >= 50, (
        f"expected a non-trivial number of enforced findings, found {len(findings)}; "
        "check fixture discovery in contract/evidence.py"
    )

    unexpected = []
    for finding in findings:
        key = (finding.fixture_path, finding.finding_id)
        if key in ALLOWLISTED_BREACHES:
            continue
        verdict = classify_evidence(finding.evidence, finding.artifact_text)
        if not verdict.ok:
            unexpected.append((finding, verdict))

    assert not unexpected, "\n".join(
        f"{f.fixture_path} {f.finding_id} ({f.envelope_path}): {v.reason}: evidence={f.evidence!r}"
        for f, v in unexpected
    )


def test_allowlist_entries_still_exist_and_still_fail():
    """Guards the allowlist from rotting: an entry must still resolve to at least one real
    evidence site in a real fixture, and that evidence must still fail the classifier. If a
    fixture is later fixed, the entry must be deleted here, not left stale."""
    if not ALLOWLISTED_BREACHES:
        return
    findings = list(iter_enforced_fixture_findings())
    for (fixture_path, finding_id), reason in ALLOWLISTED_BREACHES.items():
        matches = [
            f for f in findings if f.fixture_path == fixture_path and f.finding_id == finding_id
        ]
        assert matches, f"allowlist entry {fixture_path} {finding_id} ({reason}) no longer exists"
        verdicts = [classify_evidence(f.evidence, f.artifact_text) for f in matches]
        assert any(not v.ok for v in verdicts), (
            f"allowlist entry {fixture_path} {finding_id} ({reason}) now passes; remove it"
        )


# --------------------------------------------------------------------------
# Report CLI smoke test
# --------------------------------------------------------------------------


def test_report_cli_runs_over_a_small_run_folder(capsys):
    """The report CLI runs over one small committed bench run folder and prints counts. No rate
    is asserted here: bench envelopes are reported, never gated (see the module docstring)."""
    run_dir = REPO_ROOT / "bench" / "results" / "runs" / "critique-argument"
    assert run_dir.is_dir(), f"expected the committed run folder {run_dir} to exist"

    exit_code = evidence_main(["report", str(run_dir)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "lane=" in output
    assert "TOTAL" in output


def test_report_bench_envelopes_tallies_by_lane():
    run_dir = REPO_ROOT / "bench" / "results" / "runs" / "critique-argument"
    tallies = report_bench_envelopes(run_dir)
    assert tallies, "expected at least one lane tally from a non-empty run folder"
    total_findings = sum(t.total for t in tallies.values())
    assert total_findings > 0
