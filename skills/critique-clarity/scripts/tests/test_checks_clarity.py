"""Tests for critique-clarity's scripts/checks.py scripted lane: the 15
PLAIN-* and WILLIAMS-* criteria declared in checks.scripted.

what-it-is:   the unit suite for this skill's scripted lane
what-it-does: exercises each scripted criterion against small in-memory
              artifacts, including the fire/no-fire boundary for every
              criterion whose severity has two tiers, and checks
              determinism both at the check() level and through the
              shared run_scripted_lane CLI
why:          docs/internal/skill-template.md requires pytest coverage
              of every scripted check
used-by:      `python -m pytest`, and `scripts/skill-selftest.py`'s own
              pytest check when it validates this directory

The module basename carries the skill's domain (`_clarity`) on purpose:
two skills shipping `scripts/tests/test_checks.py` collide at pytest
collection time and abort the whole repository run. See
`scripts/skill-selftest.py`'s `check_test_module_names`.

`critique-clarity` (like every real `skills/critique-<domain>/`
directory) has a hyphen in its own directory name, so `checks.py` cannot
be reached with a normal `import` statement. It is loaded here by file
path via `importlib.util`, the same technique the template fixture's own
test module and critique-argument's own test module use.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from skills._shared.artifact import Artifact

_CHECKS_PATH = Path(__file__).resolve().parents[1] / "checks.py"


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())


def _load_checks_module():
    spec = importlib.util.spec_from_file_location("clarity_checks_under_test", _CHECKS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checks = _load_checks_module()


def _artifact(text: str) -> Artifact:
    return Artifact(path="fixture.md", text=text, sha256="0" * 64, disk_path=Path("fixture.md"))


def _of(findings, criterion):
    return [f for f in findings if f.criterion == criterion]


def _criteria(findings):
    return sorted(f.criterion for f in findings)


# ---------------------------------------------------------------------------
# Clean baseline and empty/degenerate artifacts
# ---------------------------------------------------------------------------

CLEAN_TEXT = """# Field operations notice

## Service window

The crew checks the meter log every morning. You may return the vehicle to the depot after your shift ends.

## Maintenance schedule

We inspect the pump weekly. The technician replaces worn parts before they fail.
"""


def test_clean_artifact_has_no_findings():
    assert checks.check(_artifact(CLEAN_TEXT)) == []


def test_empty_artifact_has_no_findings():
    assert checks.check(_artifact("")) == []


def test_whitespace_only_artifact_has_no_findings():
    assert checks.check(_artifact("   \n\n   \n")) == []


# ---------------------------------------------------------------------------
# PLAIN-ACTIVE
# ---------------------------------------------------------------------------


def test_active_passive_construction_is_flagged_severity_2():
    text = (
        "# T\n\n## S\n\nThe meter log is reviewed before the shift ends. "
        "The vehicle is returned to the depot by the crew.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-ACTIVE")
    assert len(findings) == 2
    assert all(f.severity == 2 for f in findings)
    assert all(f.lane == "scripted" and f.confidence == "high" for f in findings)
    assert findings[0].evidence == "The meter log is reviewed before the shift ends."


def test_active_paragraph_that_is_mostly_passive_is_severity_3():
    text = (
        "# T\n\n## S\n\nThe log is reviewed by the crew. The report is filed by the crew. "
        "The ticket is closed by the crew. The vehicle is returned by the crew.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-ACTIVE")
    assert len(findings) == 4
    assert all(f.severity == 3 for f in findings)


# ---------------------------------------------------------------------------
# PLAIN-CONCISE
# ---------------------------------------------------------------------------


def test_concise_single_wordy_phrase_is_severity_2():
    text = "# T\n\n## S\n\nIn order to finish the setup, the crew starts early each day.\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-CONCISE")
    assert len(findings) == 1
    assert findings[0].severity == 2
    assert "In order to finish the setup" in findings[0].evidence


def test_concise_three_or_more_wordy_phrases_in_one_paragraph_is_severity_3():
    text = (
        "# T\n\n## S\n\nIn order to finish early, due to the fact that volume is low, the crew "
        "leaves at this point in time given a number of open tickets.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-CONCISE")
    assert len(findings) == 1
    assert findings[0].severity == 3


# ---------------------------------------------------------------------------
# PLAIN-DOUBLE-NEGATIVE
# ---------------------------------------------------------------------------


def test_double_negative_two_markers_is_severity_2():
    text = "# T\n\n## S\n\nThe form is not valid without a signature.\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-DOUBLE-NEGATIVE")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_double_negative_three_or_more_markers_is_severity_3():
    text = "# T\n\n## S\n\nThe applicant is not eligible without a valid form and cannot appeal.\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-DOUBLE-NEGATIVE")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_double_negative_single_marker_is_not_flagged():
    text = "# T\n\n## S\n\nThe form is not valid today.\n"
    assert _of(checks.check(_artifact(text)), "PLAIN-DOUBLE-NEGATIVE") == []


# ---------------------------------------------------------------------------
# PLAIN-HEADINGS
# ---------------------------------------------------------------------------


def test_headings_non_specific_label_is_flagged_severity_2():
    text = "# T\n\n## Other\n\nA short note about one minor topic.\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-HEADINGS")
    assert len(findings) == 1
    assert findings[0].severity == 2
    assert findings[0].location == "the Other heading"


def test_headings_long_section_with_no_subheading_is_severity_2():
    paragraph = " ".join(["word"] * 140) + "."
    long_section = "\n\n".join([paragraph] * 3)  # 420 words across three in-threshold paragraphs
    text = f"# T\n\n## Detail Notes\n\n{long_section}\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-HEADINGS")
    length_findings = [f for f in findings if "words follow this heading" in f.evidence]
    assert len(length_findings) == 1
    assert length_findings[0].severity == 2


def test_headings_very_long_section_with_no_subheading_is_severity_3():
    paragraph = " ".join(["word"] * 140) + "."
    long_section = "\n\n".join([paragraph] * 6)  # 840 words across six in-threshold paragraphs
    text = f"# T\n\n## Detail Notes\n\n{long_section}\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-HEADINGS")
    length_findings = [f for f in findings if "words follow this heading" in f.evidence]
    assert len(length_findings) == 1
    assert length_findings[0].severity == 3


def test_headings_does_not_double_report_a_single_over_long_paragraph():
    """PLAIN-PARAGRAPH's threshold and PLAIN-HEADINGS' must not collide: one
    over-long paragraph is one defect, reported once, under the criterion
    that is actually about paragraph length."""
    paragraph = " ".join(["word"] * 200) + "."
    text = f"# T\n\n## Detail Notes\n\n{paragraph}\n"
    findings = checks.check(_artifact(text))
    assert _of(findings, "PLAIN-PARAGRAPH") != []
    assert _of(findings, "PLAIN-HEADINGS") == []


def test_headings_specific_label_is_not_flagged():
    text = "# T\n\n## Submission deadlines\n\nA short note about one minor topic.\n"
    assert _of(checks.check(_artifact(text)), "PLAIN-HEADINGS") == []


# ---------------------------------------------------------------------------
# PLAIN-JARGON
# ---------------------------------------------------------------------------


def test_jargon_term_with_no_definition_is_severity_2():
    text = "# T\n\n## S\n\nPursuant to the policy, the crew must file the report by Friday.\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-JARGON")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_jargon_term_defined_nearby_is_not_flagged():
    text = (
        "# T\n\n## S\n\nPursuant to the policy, meaning the rule that applies here, "
        "the crew must file the report.\n"
    )
    assert _of(checks.check(_artifact(text)), "PLAIN-JARGON") == []


def test_jargon_three_or_more_undefined_terms_in_one_paragraph_is_severity_3():
    text = (
        "# T\n\n## S\n\nPursuant to the policy, the crew must file the report. "
        "Notwithstanding that requirement, the crew must also sign it. "
        "The aforementioned crew must submit it by Friday.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-JARGON")
    assert len(findings) == 3
    assert all(f.severity == 3 for f in findings)


# ---------------------------------------------------------------------------
# PLAIN-LISTS
# ---------------------------------------------------------------------------


def test_lists_three_inline_items_is_severity_2():
    text = "# T\n\n## S\n\nThe crew reviews the log, files the report, and closes the ticket.\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-LISTS")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_lists_five_inline_items_is_severity_3():
    text = (
        "# T\n\n## S\n\nThe crew reviews the log, files the report, updates the roster, "
        "signs the form, and closes the ticket.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-LISTS")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_lists_two_items_are_not_flagged():
    text = "# T\n\n## S\n\nThe crew reviews the log and files the report.\n"
    assert _of(checks.check(_artifact(text)), "PLAIN-LISTS") == []


# ---------------------------------------------------------------------------
# PLAIN-MUST
# ---------------------------------------------------------------------------


def test_must_shall_with_no_mixing_is_severity_2():
    text = "# T\n\n## S\n\nThe crew shall file the report by noon each day without exception.\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-MUST")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_must_single_shall_in_an_otherwise_must_consistent_document_is_severity_2():
    """references/PLAIN.md's own severity 2 anchor: one shall in a document
    that otherwise uses must, with the obligation still clear from
    context. This stays a 2, not a 3."""
    text = "# T\n\n## S\n\nThe crew shall file the report. The crew must also sign it.\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-MUST")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_must_alternating_registers_across_several_requirements_is_severity_3():
    """The severity 3 anchor: several separate requirements stated in
    different registers, so the reader cannot tell which are mandatory."""
    text = (
        "# T\n\n## S\n\nThe crew shall file the report. The crew is required to sign it. "
        "The crew must archive it.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-MUST")
    assert len(findings) == 2
    assert all(f.severity == 3 for f in findings)


def test_must_two_shalls_with_no_must_or_should_anywhere_stays_severity_2():
    """Two non-must requirements alone are consistent with each other; it is
    the alternation with must or should that makes a reader unable to tell
    which requirements bind."""
    text = "# T\n\n## S\n\nThe crew shall file the report. The crew shall sign it.\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-MUST")
    assert len(findings) == 2
    assert all(f.severity == 2 for f in findings)


def test_must_alone_is_not_flagged():
    text = "# T\n\n## S\n\nThe crew must file the report by noon each day.\n"
    assert _of(checks.check(_artifact(text)), "PLAIN-MUST") == []


# ---------------------------------------------------------------------------
# PLAIN-NOMINALIZATION
# ---------------------------------------------------------------------------


def test_nominalization_isolated_instance_is_severity_2():
    text = (
        "# T\n\n## S\n\nThe committee made a determination about the proposal. "
        "The staff filed the report on time. The crew closed the ticket quickly.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-NOMINALIZATION")
    assert len(findings) == 1
    assert findings[0].severity == 2
    assert "determination" in findings[0].violation


def test_nominalization_in_every_sentence_of_a_paragraph_is_severity_3():
    text = (
        "# T\n\n## S\n\nThe committee made a determination about the proposal. "
        "The team gave an evaluation of the report. The staff took an assessment of the risk.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-NOMINALIZATION")
    assert len(findings) == 3
    assert all(f.severity == 3 for f in findings)


# ---------------------------------------------------------------------------
# PLAIN-PARAGRAPH
# ---------------------------------------------------------------------------


def test_paragraph_topic_mismatch_is_severity_3():
    text = (
        "# T\n\n## S\n\nThe scheduling window opens Monday. Eligibility depends on tenure. "
        "Benefits vary by region. Approval requires manager sign off.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-PARAGRAPH")
    assert len(findings) == 1
    assert findings[0].severity == 3
    assert findings[0].evidence == "The scheduling window opens Monday."


def test_paragraph_over_length_threshold_with_matching_topic_is_severity_2():
    long_para = " ".join(["The team reviews items carefully today."] * 40)
    text = f"# T\n\n## S\n\n{long_para}\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-PARAGRAPH")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_paragraph_short_and_on_topic_is_not_flagged():
    text = "# T\n\n## S\n\nThe crew reviews the log. The crew files the report.\n"
    assert _of(checks.check(_artifact(text)), "PLAIN-PARAGRAPH") == []


# ---------------------------------------------------------------------------
# PLAIN-PRONOUNS
# ---------------------------------------------------------------------------


def test_pronouns_isolated_institutional_substitute_is_severity_2():
    text = (
        "# T\n\n## S\n\nThe applicant must submit the form. You may then wait for a decision. "
        "We will notify you by mail.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-PRONOUNS")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_pronouns_every_sentence_routed_through_substitutes_is_severity_3():
    text = (
        "# T\n\n## S\n\nThe applicant must submit the form. The applicant must sign the form. "
        "The applicant must date the form. This office will then review the applicant submission.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-PRONOUNS")
    assert len(findings) == 4
    assert all(f.severity == 3 for f in findings)


# ---------------------------------------------------------------------------
# PLAIN-SENTENCE-LENGTH
# ---------------------------------------------------------------------------


def test_sentence_length_over_30_words_is_severity_2():
    sentence = " ".join(["token"] * 33) + " truly done."
    text = f"# T\n\n## S\n\n{sentence}\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-SENTENCE-LENGTH")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_sentence_length_50_words_or_more_is_severity_3():
    sentence = " ".join(["token"] * 55) + "."
    text = f"# T\n\n## S\n\n{sentence}\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-SENTENCE-LENGTH")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_sentence_length_four_or_more_clause_markers_is_severity_3_even_when_short():
    text = (
        "# T\n\n## S\n\nThe rule, which applies broadly, that we adopted, because staff wanted "
        "it, when needed, applies.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-SENTENCE-LENGTH")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_sentence_length_short_plain_sentence_is_not_flagged():
    text = "# T\n\n## S\n\nThe crew reviews the log every morning.\n"
    assert _of(checks.check(_artifact(text)), "PLAIN-SENTENCE-LENGTH") == []


# ---------------------------------------------------------------------------
# PLAIN-SUBJECT-VERB-OBJECT
# ---------------------------------------------------------------------------


def test_subject_verb_object_single_long_aside_is_severity_2():
    text = "# T\n\n## S\n\nThe report, submitted well after the posted deadline last night, needs review.\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-SUBJECT-VERB-OBJECT")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_subject_verb_object_two_asides_is_severity_3():
    text = (
        "# T\n\n## S\n\nThe policy, which was updated after a long internal review process that "
        "took several months to complete, because leadership wanted more clarity, applies to "
        "every regional office starting next quarter.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-SUBJECT-VERB-OBJECT")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_subject_verb_object_a_genuine_parallel_list_is_not_misread_as_an_interruption():
    """A well-formed Oxford-comma list of verb phrases has the same comma
    shape as a subject-verb interruption; PLAIN-LISTS' own >= 3 item
    series is excluded from this check for exactly that reason."""
    text = "# T\n\n## S\n\nThe crew reviews the log, files the report, updates the roster, and closes the ticket.\n"
    assert _of(checks.check(_artifact(text)), "PLAIN-SUBJECT-VERB-OBJECT") == []


def test_subject_verb_object_short_sentence_with_one_small_aside_is_not_flagged():
    text = "# T\n\n## S\n\nThe crew, as usual, reviews the log.\n"
    assert _of(checks.check(_artifact(text)), "PLAIN-SUBJECT-VERB-OBJECT") == []


# ---------------------------------------------------------------------------
# PLAIN-TRANSITIONS
# ---------------------------------------------------------------------------


def test_transitions_isolated_missing_transition_is_severity_2():
    text = (
        "# T\n\n## S\n\nThe crew opens the gate at dawn.\n\n"
        "The crew checks the meter reading closely.\n\n"
        "Therefore, the crew records the value.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-TRANSITIONS")
    assert len(findings) == 1
    assert findings[0].severity == 2
    assert findings[0].location == "S, paragraph 2"


def test_transitions_four_consecutive_paragraphs_missing_it_is_severity_3():
    text = (
        "# T\n\n## S\n\nThe crew starts the shift and reviews the log first.\n\n"
        "The crew files the report next in the queue.\n\n"
        "The crew closes the ticket after that step.\n\n"
        "The crew logs the mileage at the end.\n\n"
        "The crew leaves the depot last of all.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-TRANSITIONS")
    assert len(findings) == 4
    assert all(f.severity == 3 for f in findings)


def test_transitions_first_paragraph_after_a_heading_is_exempt():
    text = "# T\n\n## S\n\nThe crew opens the gate at dawn without a transition word.\n"
    assert _of(checks.check(_artifact(text)), "PLAIN-TRANSITIONS") == []


# ---------------------------------------------------------------------------
# WILLIAMS-PARALLELISM
# ---------------------------------------------------------------------------


def test_parallelism_mismatched_three_item_series_is_severity_2():
    text = "# T\n\n## S\n\nThe manual covers filing the report, to review the log, and inspection.\n"
    findings = _of(checks.check(_artifact(text)), "WILLIAMS-PARALLELISM")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_parallelism_mismatched_four_item_series_is_severity_3():
    text = (
        "# T\n\n## S\n\nThe manual covers filing the report, to review the log, "
        "inspection duties, and closing the ticket.\n"
    )
    findings = _of(checks.check(_artifact(text)), "WILLIAMS-PARALLELISM")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_parallelism_matching_gerund_series_is_not_flagged():
    text = "# T\n\n## S\n\nThe manual covers filing the report, reviewing the log, and closing the ticket.\n"
    assert _of(checks.check(_artifact(text)), "WILLIAMS-PARALLELISM") == []


def test_parallelism_bare_two_item_and_with_no_comma_is_not_flagged():
    """No comma at all means _split_series_items cannot separate the
    coordinated item from the sentence's own leading subject and verb, so
    this shape is deliberately left unclaimed rather than misclassified."""
    text = "# T\n\n## S\n\nThe manual covers filing the report and reviewing the log before the deadline.\n"
    assert _of(checks.check(_artifact(text)), "WILLIAMS-PARALLELISM") == []


# ---------------------------------------------------------------------------
# WILLIAMS-SHAPE
# ---------------------------------------------------------------------------


def test_shape_forty_plus_word_sentence_with_asides_is_severity_2():
    sentence = (
        "The newly updated regional operations policy, which the full executive committee "
        "carefully approved after several months of internal review, because staff members "
        "across the office wanted much clearer day to day guidance, now applies to every "
        "regional office starting next quarter across the network offices."
    )
    text = f"# T\n\n## S\n\n{sentence}\n"
    findings = _of(checks.check(_artifact(text)), "WILLIAMS-SHAPE")
    assert len(findings) == 1
    assert findings[0].severity == 2


def test_shape_sixty_plus_word_sentence_is_severity_3():
    sentence = (
        "The updated regional operations policy, which the full executive committee carefully "
        "thoroughly rigorously approved after several extremely detailed lengthy months of "
        "internal review across every single department, because staff members across every "
        "regional office wanted much clearer day to day operational guidance following the "
        "recent major reorganization, now applies to every regional office starting next "
        "quarter across the entire company network without exception for legacy contracts."
    )
    text = f"# T\n\n## S\n\n{sentence}\n"
    findings = _of(checks.check(_artifact(text)), "WILLIAMS-SHAPE")
    assert len(findings) == 1
    assert findings[0].severity == 3


def test_shape_short_sentence_is_not_flagged():
    text = "# T\n\n## S\n\nThe crew closes the ticket after the shift ends.\n"
    assert _of(checks.check(_artifact(text)), "WILLIAMS-SHAPE") == []


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------


def test_location_includes_the_nearest_heading():
    text = "# T\n\n## Service window\n\nThe form is not valid without a signature.\n"
    findings = _of(checks.check(_artifact(text)), "PLAIN-DOUBLE-NEGATIVE")
    assert findings[0].location == "Service window, paragraph 1"


def test_location_falls_back_to_paragraph_number_with_no_heading():
    text = "The form is not valid without a signature."
    findings = _of(checks.check(_artifact(text)), "PLAIN-DOUBLE-NEGATIVE")
    assert findings[0].location == "paragraph 1"


def test_location_paragraph_number_is_counted_within_its_heading():
    """A location naming a heading numbers its paragraph within that
    heading, not across the document. bench/metrics' markdown-prose
    resolver reads it that way, so a whole-document number printed beside a
    heading name resolves to the wrong paragraph or to none at all."""
    text = (
        "# T\n\n## First section\n\nAlpha one. Alpha two.\n\n"
        "However, alpha three.\n\n## Second section\n\nBeta one.\n\n"
        "Therefore, the form is not valid without a signature.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-DOUBLE-NEGATIVE")
    assert len(findings) == 1
    # Document paragraph 4, but the second paragraph under its own heading.
    assert findings[0].location == "Second section, paragraph 2"


def test_location_resolves_onto_the_right_paragraph_under_the_metrics_resolver():
    """End-to-end guard against the numbering convention drifting again:
    the library's own location resolver must land every emitted location on
    the paragraph the finding is actually about."""
    locate = pytest.importorskip("bench.metrics.locate")
    text = (
        "# T\n\n## First section\n\nAlpha one. Alpha two.\n\n"
        "However, alpha three.\n\n## Second section\n\nBeta one.\n\n"
        "Therefore, the form is not valid without a signature.\n"
    )
    findings = _of(checks.check(_artifact(text)), "PLAIN-DOUBLE-NEGATIVE")
    parsed = locate.parse_artifact("markdown-prose", text)
    resolved = locate.resolve_location(parsed, "markdown-prose", findings[0].location)
    assert resolved.paragraph_exact == 4  # the whole-document index of that same paragraph


# ---------------------------------------------------------------------------
# Multiple defects together
# ---------------------------------------------------------------------------


def test_multiple_defects_in_one_artifact_are_all_reported():
    text = (
        "# T\n\n## S\n\nThe form is not valid without a signature. "
        "Pursuant to the policy, the crew shall file it by Friday.\n"
    )
    findings = checks.check(_artifact(text))
    assert _criteria(findings) == ["PLAIN-DOUBLE-NEGATIVE", "PLAIN-JARGON", "PLAIN-MUST"]


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_check_is_deterministic_across_repeated_calls():
    """S-04 spec: checks.py MUST be deterministic, same artifact, same
    output. RawFinding is a frozen dataclass, so list equality compares
    every field."""
    text = (
        "# T\n\n## S\n\nThe log is reviewed by the crew. The report is filed by the crew. "
        "The ticket is closed by the crew. The vehicle is returned by the crew.\n"
    )
    artifact = _artifact(text)
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
    target.write_text(CLEAN_TEXT.replace("You may return", "The vehicle is returned"), encoding="utf-8", newline="\n")
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
    assert first["run"]["skill"] == "critique-clarity"
    assert first["run"]["rubrics"] == ["PLAIN", "WILLIAMS"]


# ---------------------------------------------------------------------------
# Gate exit codes
# ---------------------------------------------------------------------------


def test_gate_exits_zero_for_a_clean_artifact(tmp_path, monkeypatch):
    target = tmp_path / "doc.md"
    target.write_text(CLEAN_TEXT, encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    code = checks.main([str(target), "--gate"])

    assert code == 0


def test_gate_exits_two_for_a_severity_3_finding_at_default_threshold(tmp_path, monkeypatch):
    target = tmp_path / "doc.md"
    target.write_text(
        "# T\n\n## S\n\nThe applicant is not eligible without a valid form and cannot appeal.\n",
        encoding="utf-8",
        newline="\n",
    )
    monkeypatch.chdir(tmp_path)

    code = checks.main([str(target), "--gate"])

    assert code == 2
