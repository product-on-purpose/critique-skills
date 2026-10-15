"""Evidence-quotes-not-characterizes check (E24).

docs/reference/critique-contract.md states the `evidence` field contract: "evidence must be a
quotation taken from the artifact or a measurement of it, never a characterization of it. 'The
contrast seems low' is schema-valid prose and contract-breaking evidence; a contrast ratio
computed from the artifact's actual colors is not." Nothing enforced that property before this
module. This module is both an importable classifier and a CLI report over committed envelopes.

Library usage:

    from contract.evidence import classify_evidence

    verdict = classify_evidence("4.5:1", artifact_text)
    if not verdict.ok:
        print(verdict.reason)

CLI usage (report only, never a pass or fail gate):

    python -m contract.evidence report <directory-of-envelopes>

Scope, per the ruling recorded in docs/internal/backlog/enhancements.md E24: this module is wired
into a pass/fail test only over authored fixtures (every golden fixture and every
examples/<domain>/envelope.json whose run.artifact resolves to a file). Committed benchmark
envelopes under bench/results/runs*/ are measured model output, not an authored claim, so a
characterizing finding there is reported by the CLI below and never fails a build.

Design, in three tiers tried in order; the first match wins:

1. Whole-segment quotation: after splitting the evidence on ellipsis markers ("..." or the
   Unicode ellipsis), a whole segment that exactly equals a verbatim, word-boundary-aligned span
   of the artifact passes regardless of length, provided it carries at least two letters or
   digits. A segment that is the ENTIRE evidence contributes no characterizing language by
   definition, so no length floor is needed: "Error" and "<h4>" both pass this way.
2. Quoted-span and labeled-value quotation: a segment that is not a whole-string match may still
   be the genuine one in a short structured line such as `control labeled "Save"` or
   `heading: Escalation`, where the writer's own label ("control labeled", "heading:") is not
   artifact text but the quoted or colon-valued remainder is. Text set off by matching quote
   characters, or following a short `Label:` or `attr=` prefix, passes at a 3-non-space-character
   floor: short enough for a one-word label like "Save" or "toast", long enough that a stray
   punctuation mark cannot satisfy it on its own.
3. Long embedded quotation: for prose with no quote marks and no label at all, such as a sentence
   that embeds a list item or a heading's exact words without setting them off, the longest
   contiguous run the segment shares with the artifact must reach 12 non-space characters. 12 is
   chosen specifically to clear "contrast" (8 letters), the one word from the contract's own
   characterization example ("The contrast seems low") that plausibly recurs verbatim in an
   accessibility artifact; a single common word must never be enough to pass, but two words or one
   longer one should be.

Measurement is checked independently (a characterization can never satisfy it, since every pattern
requires a digit): a contrast or other ratio, a percentage, a pixel or similar unit size, a decimal
in parentheses, or a count pairing a number with a counted noun from a closed list. It is
deliberately narrow, per the backlog ruling, rather than "any digit present somewhere."

A finding passes if it is a quotation OR a measurement; otherwise it is a characterization.

This module imports only the standard library, so it carries none of contract/validate.py's lazy
jsonschema-import concern; it has no third-party dependency to defer.
"""

from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parent.parent

# Tier thresholds (non-space characters), justified above in the module docstring.
WHOLE_SEGMENT_MIN_ALNUM = 2
QUOTED_OR_LABELED_MIN_CHARS = 3
LONG_SUBSTRING_MIN_CHARS = 12

ELLIPSIS_RE = re.compile(r"\.\.\.|…")
QUOTED_SPAN_RE = re.compile(r'"([^"\n]{1,300})"' + r"|'([^'\n]{1,300})'")
LABEL_PREFIX_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 ()/_-]{0,40}:\s+(?=\S)")
ATTR_PREFIX_RE = re.compile(r"^[a-zA-Z][a-zA-Z-]{0,30}=(?=\S)")

CURLY_QUOTES = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
}

WRAPPING_QUOTE_PAIRS = {'"': '"', "'": "'"}

# Rule categories: a contrast or other ratio, a percentage, a pixel-like size, a decimal fraction
# in parentheses (e.g. "6 of 10 sentences (0.60)"), and a count pairing a number with a counted
# noun drawn from a closed list. Narrow and pattern-based on purpose: a bare digit is not enough,
# since a location reference such as "paragraph 1" must never read as a measurement.
_COUNT_NOUNS = (
    r"word|words|character|characters|item|items|row|rows|column|columns|sentence|sentences|"
    r"paragraph|paragraphs|link|links|image|images|control|controls|element|elements|"
    r"element\(s\)|phrase|phrases|instance|instances|occurrence|occurrences|pixel|pixels|px"
)
MEASUREMENT_PATTERNS = (
    re.compile(r"\d+(\.\d+)?\s*:\s*\d+(\.\d+)?"),  # ratio, e.g. "4.5:1", "2.38:1"
    re.compile(r"\d+(\.\d+)?\s*%|\d+(\.\d+)?\s*percent\b", re.IGNORECASE),  # percentage
    re.compile(r"\d+(\.\d+)?\s*(px|em|rem|pt)\b", re.IGNORECASE),  # size
    re.compile(r"\(\s*\d*\.\d+\s*\)"),  # decimal fraction in parens, e.g. "(0.60)"
    re.compile(r"\bgrade\s+\d+(\.\d+)?\b|\d+(\.\d+)?\s*reading\s+ease\b", re.IGNORECASE),
    re.compile(
        r"\b\d+(\.\d+)?\b(?:\s+[A-Za-z()/_-]+){0,3}?\s+(?:" + _COUNT_NOUNS + r")\b",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class EvidenceVerdict:
    """The classifier's result: which of the contract's two allowed shapes the evidence took,
    or that it took neither, plus one line explaining why."""

    verdict: str  # "quotation", "measurement", or "characterization"
    reason: str

    @property
    def ok(self) -> bool:
        return self.verdict != "characterization"


# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------


def _normalize_quotes(text: str) -> str:
    for curly, straight in CURLY_QUOTES.items():
        text = text.replace(curly, straight)
    return text


def normalize(text: str) -> str:
    """Decode HTML entities, unify curly and straight quotes, and collapse whitespace.

    Applied identically to the evidence string and the artifact text, so a difference in
    formatting alone never decides the verdict. The artifact's raw source is normalized this way
    too rather than having its tags stripped: every HTML fixture examined quotes raw source
    (a tag, an attribute, or a text node), never a separately rendered text. Entity decoding is
    cheap and correct either way, so it stays even though no fixture currently needs it.
    """
    text = html.unescape(text)
    text = _normalize_quotes(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _non_space_len(text: str) -> int:
    return len(text) - text.count(" ")


def _alnum_count(text: str) -> int:
    return sum(1 for ch in text if ch.isalnum())


def _strip_wrapping_quotes(text: str) -> str:
    """Strip one fully-wrapping pair of matching quote characters, e.g. a whole evidence value
    written as '"...the quoted sentence..."' (methodology's convention for a full-sentence
    quotation, seen in skills/critique-usability's goldens)."""
    if len(text) >= 2 and text[0] in WRAPPING_QUOTE_PAIRS and text[-1] == WRAPPING_QUOTE_PAIRS[text[0]]:
        inner = text[1:-1].strip()
        if inner:
            return inner
    return text


# --------------------------------------------------------------------------
# Quotation: boundary-aware substring search
# --------------------------------------------------------------------------


def _is_word_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _boundary_ok(haystack: str, start: int, end: int, needle: str) -> bool:
    """True when a match of `needle` at haystack[start:end] is not merely a slice out of the
    middle of a longer word on either side, so a short fragment cannot pass by matching inside an
    unrelated, longer identifier."""
    if needle and _is_word_char(needle[0]) and start > 0 and _is_word_char(haystack[start - 1]):
        return False
    if needle and _is_word_char(needle[-1]) and end < len(haystack) and _is_word_char(haystack[end]):
        return False
    return True


def _contains_at_boundary(needle: str, haystack: str) -> bool:
    if not needle:
        return False
    start = 0
    while True:
        index = haystack.find(needle, start)
        if index == -1:
            return False
        if _boundary_ok(haystack, index, index + len(needle), needle):
            return True
        start = index + 1


def _longest_common_run(a: str, b: str) -> str:
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    match = matcher.find_longest_match(0, len(a), 0, len(b))
    return b[match.b : match.b + match.size]


def _extract_quoted_spans(text: str) -> list[str]:
    spans = []
    for match in QUOTED_SPAN_RE.finditer(text):
        span = match.group(1) if match.group(1) is not None else match.group(2)
        if span is not None:
            spans.append(span.strip())
    return spans


def _label_stripped(text: str) -> str | None:
    match = LABEL_PREFIX_RE.match(text)
    if match:
        return text[match.end() :].strip()
    match = ATTR_PREFIX_RE.match(text)
    if match:
        return text[match.end() :].strip()
    return None


def _segment_quotation_reason(segment: str, artifact_norm: str) -> str | None:
    """Try the three tiers in order for one ellipsis-split segment of the evidence. Returns a
    one-line reason on the first tier that passes, or None."""
    whole = _strip_wrapping_quotes(segment).strip()
    if whole and _alnum_count(whole) >= WHOLE_SEGMENT_MIN_ALNUM and _contains_at_boundary(whole, artifact_norm):
        return "the whole evidence segment appears verbatim in the artifact"

    for span in _extract_quoted_spans(segment):
        if _non_space_len(span) >= QUOTED_OR_LABELED_MIN_CHARS and _contains_at_boundary(span, artifact_norm):
            return f"the quoted span {span!r} appears verbatim in the artifact"

    labeled = _label_stripped(whole)
    if (
        labeled
        and _non_space_len(labeled) >= QUOTED_OR_LABELED_MIN_CHARS
        and _contains_at_boundary(labeled, artifact_norm)
    ):
        return f"the value {labeled!r} after the evidence's own label appears verbatim in the artifact"

    run = _longest_common_run(whole, artifact_norm)
    if _non_space_len(run) >= LONG_SUBSTRING_MIN_CHARS:
        start = artifact_norm.find(run)
        if start != -1 and _boundary_ok(artifact_norm, start, start + len(run), run):
            return f"shares a {_non_space_len(run)}-character verbatim run with the artifact: {run!r}"

    return None


def _quotation_reason(evidence_norm: str, artifact_norm: str) -> str | None:
    unwrapped = _strip_wrapping_quotes(evidence_norm)
    segments = [s.strip() for s in ELLIPSIS_RE.split(unwrapped) if s.strip()]
    if not segments:
        segments = [unwrapped]
    for segment in segments:
        reason = _segment_quotation_reason(segment, artifact_norm)
        if reason is not None:
            return reason
    return None


# --------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------


def _measurement_reason(evidence_norm: str) -> str | None:
    for pattern in MEASUREMENT_PATTERNS:
        match = pattern.search(evidence_norm)
        if match:
            return f"states a computed figure matching {match.group(0)!r}"
    return None


# --------------------------------------------------------------------------
# Public classifier
# --------------------------------------------------------------------------


def classify_evidence(evidence: str, artifact_text: str) -> EvidenceVerdict:
    """Classify one finding's `evidence` string against the artifact's full text.

    Returns a quotation verdict first, then a measurement verdict, then characterization.
    `artifact_text` is the artifact's own raw text (source, not a rendering); see `normalize`.
    """
    evidence_norm = normalize(evidence)
    artifact_norm = normalize(artifact_text)

    reason = _quotation_reason(evidence_norm, artifact_norm)
    if reason is not None:
        return EvidenceVerdict(verdict="quotation", reason=reason)

    reason = _measurement_reason(evidence_norm)
    if reason is not None:
        return EvidenceVerdict(verdict="measurement", reason=reason)

    return EvidenceVerdict(
        verdict="characterization",
        reason="no verbatim quotation fragment and no measurement pattern was found",
    )


# --------------------------------------------------------------------------
# Walking envelopes: findings and their evidence, including instances
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceSite:
    """One `evidence` string inside one envelope: where it lives (for a report line or an
    allowlist entry) and what it says."""

    path: str  # dotted path within the envelope, e.g. "findings[3].instances[0].evidence"
    finding_id: str
    lane: str
    evidence: str


def iter_evidence_sites(envelope: dict[str, Any]) -> Iterator[EvidenceSite]:
    """Every `evidence` string in an envelope's `findings`, including each entry of a finding's
    optional `instances` list (contract/critique-contract.schema.json #/$defs/instance)."""
    findings = envelope.get("findings")
    if not isinstance(findings, list):
        return
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            continue
        finding_id = finding.get("id") if isinstance(finding.get("id"), str) else f"[{index}]"
        lane = finding.get("lane") if isinstance(finding.get("lane"), str) else "unknown"
        evidence = finding.get("evidence")
        if isinstance(evidence, str):
            yield EvidenceSite(
                path=f"findings[{index}].evidence", finding_id=finding_id, lane=lane, evidence=evidence
            )
        instances = finding.get("instances")
        if isinstance(instances, list):
            for inst_index, instance in enumerate(instances):
                if not isinstance(instance, dict):
                    continue
                inst_evidence = instance.get("evidence")
                if isinstance(inst_evidence, str):
                    yield EvidenceSite(
                        path=f"findings[{index}].instances[{inst_index}].evidence",
                        finding_id=finding_id,
                        lane=lane,
                        evidence=inst_evidence,
                    )


# --------------------------------------------------------------------------
# Authored fixtures: golden examples and examples/<domain>/envelope.json
# --------------------------------------------------------------------------


def find_golden_fixtures(repo_root: Path = REPO_ROOT) -> list[Path]:
    """Every `skills/**/examples/golden-*.json` fixture, including skills/_template-fixture, per
    the E24 scope ruling: these are authored by this project, so a characterizing evidence string
    here is a defect, not a measured property of a model."""
    return sorted((repo_root / "skills").glob("**/examples/golden-*.json"))


def find_example_envelopes(repo_root: Path = REPO_ROOT) -> list[Path]:
    """Every `examples/<domain>/envelope.json` whose `run.artifact` resolves to a real file.

    One illustrative envelope lives directly under `examples/`, not `skills/`; see
    docs/explanation and the top-level examples/README.md. A path that does not resolve is
    skipped rather than failed: this walker is read-only evidence discovery, not a second artifact
    existence check, and a non-resolving path is out of E24's enforced scope by the ruling's own
    wording.
    """
    paths = []
    for candidate in sorted((repo_root / "examples").glob("*/envelope.json")):
        try:
            doc = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        artifact = doc.get("run", {}).get("artifact") if isinstance(doc.get("run"), dict) else None
        if isinstance(artifact, str) and (repo_root / artifact).is_file():
            paths.append(candidate)
    return paths


def _load_golden_envelope(path: Path) -> tuple[dict[str, Any], str] | None:
    """Return (expected_envelope, artifact-relative-path) for a golden fixture, or None if it is
    not shaped like one (kind != "golden")."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("kind") != "golden":
        return None
    envelope = doc.get("expected_envelope")
    artifact = doc.get("artifact")
    if not isinstance(envelope, dict) or not isinstance(artifact, str):
        return None
    return envelope, artifact


@dataclass(frozen=True)
class FixtureFinding:
    """One evidence site inside one authored fixture file, resolved against its artifact."""

    fixture_path: str  # repo-relative, forward slashes
    finding_id: str
    lane: str
    envelope_path: str  # dotted path within the fixture's envelope
    evidence: str
    artifact_text: str


def iter_enforced_fixture_findings(repo_root: Path = REPO_ROOT) -> Iterator[FixtureFinding]:
    """Every evidence site in every enforced authored fixture, with its artifact text already
    read, ready to classify. Raises if a fixture or its artifact cannot be read: a broken fixture
    under enforcement is a defect, not something to skip silently."""
    seen_fixtures: set[Path] = set()
    for fixture_path in find_golden_fixtures(repo_root) + find_example_envelopes(repo_root):
        if fixture_path in seen_fixtures:
            continue
        seen_fixtures.add(fixture_path)
        doc = json.loads(fixture_path.read_text(encoding="utf-8"))
        if fixture_path.name.startswith("golden-"):
            loaded = _load_golden_envelope(fixture_path)
            if loaded is None:
                continue
            envelope, artifact_rel = loaded
        else:
            envelope = doc
            run = doc.get("run")
            artifact_rel = run.get("artifact") if isinstance(run, dict) else None
            if not isinstance(artifact_rel, str):
                continue
        artifact_path = repo_root / artifact_rel
        artifact_text = artifact_path.read_text(encoding="utf-8")
        rel_fixture = fixture_path.relative_to(repo_root).as_posix()
        for site in iter_evidence_sites(envelope):
            yield FixtureFinding(
                fixture_path=rel_fixture,
                finding_id=site.finding_id,
                lane=site.lane,
                envelope_path=site.path,
                evidence=site.evidence,
                artifact_text=artifact_text,
            )


# --------------------------------------------------------------------------
# Benchmark envelopes: reported, never failing (bench/results/runs*/)
# --------------------------------------------------------------------------


def find_bench_envelope_files(runs_dir: Path) -> list[Path]:
    """Every envelope `*.json` under a bench run-set directory, excluding non-envelope files the
    same way contract/validate_envelopes.py does."""
    if not runs_dir.is_dir():
        return []
    return sorted(
        p
        for p in runs_dir.rglob("*.json")
        if p.is_file() and p.name != "results.json" and not p.name.endswith(".schema.json")
    )


@dataclass
class LaneTally:
    quotation: int = 0
    measurement: int = 0
    characterization: int = 0

    @property
    def total(self) -> int:
        return self.quotation + self.measurement + self.characterization


def report_bench_envelopes(runs_dir: Path, repo_root: Path = REPO_ROOT) -> dict[str, LaneTally]:
    """Classify every finding's evidence in every envelope under `runs_dir`, tallied by lane.

    Bench envelopes record `run.artifact` as a corpus path under bench/corpus/; resolved relative
    to `repo_root` per the E24 scope ruling. A finding whose artifact file cannot be resolved or
    read is skipped: this is a report, not a gate, so a missing corpus file reduces the sample
    rather than raising.
    """
    tallies: dict[str, LaneTally] = {}
    for envelope_path in find_bench_envelope_files(runs_dir):
        try:
            doc = json.loads(envelope_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(doc, dict):
            continue
        run = doc.get("run")
        artifact_rel = run.get("artifact") if isinstance(run, dict) else None
        if not isinstance(artifact_rel, str):
            continue
        artifact_path = repo_root / artifact_rel
        try:
            artifact_text = artifact_path.read_text(encoding="utf-8")
        except OSError:
            continue
        for site in iter_evidence_sites(doc):
            tally = tallies.setdefault(site.lane, LaneTally())
            verdict = classify_evidence(site.evidence, artifact_text)
            if verdict.verdict == "quotation":
                tally.quotation += 1
            elif verdict.verdict == "measurement":
                tally.measurement += 1
            else:
                tally.characterization += 1
    return tallies


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _print_report(runs_dir: Path, repo_root: Path) -> int:
    tallies = report_bench_envelopes(runs_dir, repo_root)
    if not tallies:
        print(f"evidence report: no findings with evidence found under {runs_dir}")
        return 0
    print(f"evidence report: {runs_dir}")
    grand = LaneTally()
    for lane in sorted(tallies):
        tally = tallies[lane]
        grand.quotation += tally.quotation
        grand.measurement += tally.measurement
        grand.characterization += tally.characterization
        pass_count = tally.quotation + tally.measurement
        rate = pass_count / tally.total if tally.total else 0.0
        print(
            f"  lane={lane:<10} total={tally.total:<5} quotation={tally.quotation:<5} "
            f"measurement={tally.measurement:<5} characterization={tally.characterization:<5} "
            f"pass_rate={rate:.3f}"
        )
    pass_count = grand.quotation + grand.measurement
    rate = pass_count / grand.total if grand.total else 0.0
    print(
        f"  {'TOTAL':<15} total={grand.total:<5} quotation={grand.quotation:<5} "
        f"measurement={grand.measurement:<5} characterization={grand.characterization:<5} "
        f"pass_rate={rate:.3f}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m contract.evidence",
        description=(
            "Report, by lane, how many findings' evidence is a quotation, a measurement, or a "
            "characterization. Never a pass or fail gate: see the module docstring for scope."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    report_parser = subparsers.add_parser(
        "report", help="Report evidence verdicts for every envelope under a directory."
    )
    report_parser.add_argument(
        "runs_dir", help="A bench run-set directory, e.g. bench/results/runs."
    )
    args = parser.parse_args(argv)

    if args.command == "report":
        return _print_report(Path(args.runs_dir), REPO_ROOT)
    return 1  # pragma: no cover - argparse's `required=True` makes this unreachable


if __name__ == "__main__":
    sys.exit(main())
