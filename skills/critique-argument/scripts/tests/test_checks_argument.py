"""Tests for critique-argument's scripts/checks.py scripted lane:
TOULMIN-CLAIM-MARKER, TOULMIN-HEDGE-DENSITY.

what-it-is:   the unit suite for this skill's scripted lane
what-it-does: exercises each TOULMIN-* scripted check against small
              in-memory artifacts, including the fire/no-fire boundary
              for each of references/TOULMIN.md's own thresholds, and
              checks determinism both at the check() level and through
              the shared run_scripted_lane CLI
why:          docs/internal/skill-template.md requires pytest coverage
              of every scripted check
used-by:      `python -m pytest`, and `scripts/skill-selftest.py`'s own
              pytest check when it validates this directory

The module basename carries the skill's domain (`_argument`) on purpose:
two skills shipping `scripts/tests/test_checks.py` collide at pytest
collection time and abort the whole repository run. See
`scripts/skill-selftest.py`'s `check_test_module_names`.

`critique-argument` (like every real `skills/critique-<domain>/`
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
    spec = importlib.util.spec_from_file_location("argument_checks_under_test", _CHECKS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checks = _load_checks_module()

FIXED_NOW = lambda: datetime(2026, 7, 31, 9, 0, 0, tzinfo=timezone.utc)  # noqa: E731


def _artifact(text: str) -> Artifact:
    return Artifact(path="fixture.md", text=text, sha256="0" * 64, disk_path=Path("fixture.md"))


def _criteria(findings):
    return sorted(f.criterion for f in findings)


# ---------------------------------------------------------------------------
# TOULMIN-CLAIM-MARKER
# ---------------------------------------------------------------------------

CLEAN_TEXT = """# Field crew staffing proposal

We recommend adding a third crew to the evening shift. The current two crews cover the service
window, but the fourth quarter's call volume regularly exceeds what two crews can close before the
window ends. Therefore, a third crew keeps the average close time inside policy through the winter
peak.
"""


def test_clean_artifact_has_no_findings():
    findings = checks.check(_artifact(CLEAN_TEXT))
    assert findings == []


def test_claim_marker_missing_is_flagged_severity_2_under_300_words():
    text = (
        "The field crew reviews the meter log before the shift ends. Crews that finish early "
        "return the vehicle to the depot and record the mileage on the shared log."
    )
    findings = checks.check(_artifact(text))
    marker_findings = [f for f in findings if f.criterion == "TOULMIN-CLAIM-MARKER"]
    assert len(marker_findings) == 1
    finding = marker_findings[0]
    assert finding.severity == 2
    assert finding.lane == "scripted"
    assert finding.confidence == "high"
    assert "0 conclusion-marker phrases found" in finding.evidence


def _n_word_paragraph(n: int) -> str:
    """`n` whitespace-separated tokens, no claim marker and no hedge term
    among them, so this isolates cleanly to TOULMIN-CLAIM-MARKER's own
    word-count threshold. No heading, so the document also exercises the
    "no H1" location fallback."""
    return " ".join(["widget"] * n) + "."


def test_claim_marker_word_boundary_299_words_is_severity_2():
    findings = checks.check(_artifact(_n_word_paragraph(299)))
    assert _criteria(findings) == ["TOULMIN-CLAIM-MARKER"]
    assert findings[0].severity == 2


def test_claim_marker_word_boundary_300_words_is_severity_3():
    """references/TOULMIN.md: "Severity 2 when the artifact is under 300
    words, severity 3 at 300 words or more" - the boundary is inclusive
    on the 300 side."""
    findings = checks.check(_artifact(_n_word_paragraph(300)))
    assert _criteria(findings) == ["TOULMIN-CLAIM-MARKER"]
    assert findings[0].severity == 3


def test_claim_marker_present_in_heading_only_still_satisfies_the_criterion():
    """A marker phrase in a heading is exactly where a reader scanning
    for the conclusion looks first, so it counts."""
    text = "# We recommend a phased rollout\n\nThe pilot covered one region for one quarter.\n"
    findings = checks.check(_artifact(text))
    assert "TOULMIN-CLAIM-MARKER" not in _criteria(findings)


def test_claim_marker_word_count_ignores_markdown_structural_tokens():
    """references/TOULMIN.md states the threshold in words, and a '#' or
    a list bullet is not one. This artifact carries 299 words (one
    heading word plus 298 in twenty bullets) and must stay severity 2. A
    plain \\S+ count over the raw source sees 320 tokens and would report
    severity 3 on punctuation alone."""
    words = ["widget"] * 298
    bullets = "\n".join(f"- {' '.join(words[i * 15:(i + 1) * 15])}" for i in range(20))
    text = f"# Note\n\n{bullets}\n"
    assert len(text.split()) == 320, "fixture must exceed 300 raw whitespace tokens"
    findings = checks.check(_artifact(text))
    marker_findings = [f for f in findings if f.criterion == "TOULMIN-CLAIM-MARKER"]
    assert len(marker_findings) == 1
    assert marker_findings[0].severity == 2
    assert "across 299 words" in marker_findings[0].evidence


def test_claim_marker_lexicon_uses_word_boundaries_not_substrings():
    """"enthusiastic" must not match "thus", and "argues" alone must not
    match "this paper argues" or "i argue that". This document has none
    of the real marker phrases and must still fire."""
    text = (
        "The team is enthusiastic about the pilot. A reviewer argues informally that the "
        "numbers look promising, without ever stating a recommendation."
    )
    findings = checks.check(_artifact(text))
    assert "TOULMIN-CLAIM-MARKER" in _criteria(findings)


# ---------------------------------------------------------------------------
# TOULMIN-HEDGE-DENSITY
# ---------------------------------------------------------------------------


def _hedge_ratio_text(total: int, hedged: int) -> str:
    """An H1 carrying a conclusion marker (so TOULMIN-CLAIM-MARKER never
    fires here) followed by `total` short sentences in one paragraph,
    `hedged` of which carry the hedge term "may" and the rest of which
    carry no lexicon term at all."""
    sentences = []
    for i in range(total):
        if i < hedged:
            sentences.append(f"The team may adjust item {i}.")
        else:
            sentences.append(f"The team adjusts item {i}.")
    body = " ".join(sentences)
    return f"# We recommend a schedule change\n\n{body}\n"


def test_hedge_density_ratio_at_or_below_035_produces_no_finding():
    findings = checks.check(_artifact(_hedge_ratio_text(total=20, hedged=7)))  # 0.35 exactly
    assert findings == []


def test_hedge_density_ratio_just_above_035_is_severity_2():
    findings = checks.check(_artifact(_hedge_ratio_text(total=20, hedged=8)))  # 0.40
    assert _criteria(findings) == ["TOULMIN-HEDGE-DENSITY"]
    finding = findings[0]
    assert finding.severity == 2
    assert "8 of 20 sentences" in finding.evidence


def test_hedge_density_ratio_at_050_is_still_severity_2():
    """references/TOULMIN.md: "Severity 2 while the ratio stays at or
    below 0.50, severity 3 above it"."""
    findings = checks.check(_artifact(_hedge_ratio_text(total=20, hedged=10)))  # 0.50 exactly
    assert _criteria(findings) == ["TOULMIN-HEDGE-DENSITY"]
    assert findings[0].severity == 2


def test_hedge_density_ratio_above_050_is_severity_3():
    findings = checks.check(_artifact(_hedge_ratio_text(total=20, hedged=11)))  # 0.55
    assert _criteria(findings) == ["TOULMIN-HEDGE-DENSITY"]
    assert findings[0].severity == 3


def test_hedge_density_counts_sentences_not_word_occurrences():
    """A single sentence stacking several hedge words is one hedged
    sentence, not several; the criterion is a sentence-level ratio."""
    text = (
        "# We recommend caution\n\n"
        "It might perhaps possibly be somewhat premature to expand. The pilot ran for one "
        "full quarter across two regions. The results were consistent across both regions. "
        "The team closed every ticket inside the service window."
    )
    findings = checks.check(_artifact(text))
    hedge_findings = [f for f in findings if f.criterion == "TOULMIN-HEDGE-DENSITY"]
    assert hedge_findings == []  # 1 of 4 sentences hedged, ratio 0.25, below threshold


def test_headings_are_excluded_from_hedge_sentence_count():
    """A heading carrying hedge language must not be counted as a
    sentence: a document with only a heading and no paragraph has
    nothing to measure a ratio over."""
    text = "# This might possibly work\n"
    findings = checks.check(_artifact(text))
    assert "TOULMIN-HEDGE-DENSITY" not in _criteria(findings)


def test_hedge_lexicon_uses_word_boundaries_not_substrings():
    """"maybe" is not the lexicon term "may" and must not match it."""
    text = _hedge_ratio_text(total=20, hedged=0).replace(
        "The team adjusts item 0.", "Maybe the team adjusts item 0."
    )
    findings = checks.check(_artifact(text))
    assert findings == []


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
# Location
# ---------------------------------------------------------------------------


def test_location_names_the_h1_heading_when_present():
    text = "# Staffing proposal\n\n" + _n_word_paragraph(50)
    findings = checks.check(_artifact(text))
    assert findings, "expected a TOULMIN-CLAIM-MARKER finding to inspect"
    assert findings[0].location == 'the whole document, under its "Staffing proposal" heading'


def test_location_falls_back_to_line_1_without_any_h1():
    text = "## Subsection only\n\n" + _n_word_paragraph(50)
    findings = checks.check(_artifact(text))
    assert findings, "expected a TOULMIN-CLAIM-MARKER finding to inspect"
    assert findings[0].location == "the whole document, starting at line 1"


# ---------------------------------------------------------------------------
# Both criteria together
# ---------------------------------------------------------------------------


def test_multiple_defects_in_one_artifact_are_all_reported():
    sentences = []
    for i in range(20):
        if i < 11:  # ratio 0.55, severity 3
            sentences.append(f"The team may adjust item {i}.")
        else:
            sentences.append(f"The team adjusts item {i}.")
    text = "# Untitled note\n\n" + " ".join(sentences)
    findings = checks.check(_artifact(text))
    assert _criteria(findings) == ["TOULMIN-CLAIM-MARKER", "TOULMIN-HEDGE-DENSITY"]


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_check_is_deterministic_across_repeated_calls():
    """S-04 spec: checks.py MUST be deterministic, same artifact, same
    output. RawFinding is a frozen dataclass, so list equality compares
    every field."""
    artifact = _artifact(_hedge_ratio_text(total=20, hedged=11))
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
    target.write_text(_hedge_ratio_text(total=20, hedged=11), encoding="utf-8", newline="\n")
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
    assert first["run"]["skill"] == "critique-argument"
    assert first["run"]["rubrics"] == ["TOULMIN"]


def test_gate_exits_two_for_a_severity_3_hedge_finding_at_default_threshold(tmp_path, monkeypatch):
    target = tmp_path / "doc.md"
    target.write_text(_hedge_ratio_text(total=20, hedged=11), encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    code = checks.main([str(target), "--gate"])

    assert code == 2


def test_gate_exits_zero_for_a_clean_artifact(tmp_path, monkeypatch):
    target = tmp_path / "doc.md"
    target.write_text(CLEAN_TEXT, encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)

    code = checks.main([str(target), "--gate"])

    assert code == 0
