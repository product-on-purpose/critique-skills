"""Assemble one contract-valid run envelope from a critique's merged findings.

WHY THIS EXISTS. `skills/_shared/envelope.py` has carried the deterministic assembly logic from the
start, and `assemble_envelope`'s own docstring names its intended callers as "skills/_shared/
runner.py, or a judged-lane critic merging both lanes". The scripted lane could reach it, because
`runner.py` is a CLI. The critic could not: the critic is prose plus `Read` and `Bash`, and this was
a Python function with no entry point. So the critic ranked, bounded, histogrammed and gated in its
head, every run, from instructions.

It did not do it reliably. Measured 2026-08-09 on the pinned haiku tier, 2 of 7 benchmark cells
produced a contract-valid envelope, and the two recurring failures were both the critic mis-stating
its own measurement rather than critiquing badly:

  * `summary.by_severity: histogram total 9 does not equal len(findings) (9) plus
    suppressed_count (2)`. The histogram is over everything found; `findings` is the bounded subset.
  * `findings[4].confidence: 'high' was expected` on a `scripted` finding, which the contract pins
    because a deterministic check either fired or it did not (methodology section 5).

Both are arithmetic and recall, not judgment. This module turns them into a subprocess the critic
already has the tools to run, so the four passes of the protocol stay the critic's work and the
bookkeeping stops being.

Everything derivable is derived rather than asked for: the artifact hash is computed from the file,
`rubrics` from the namespaces the findings actually cite, and the skill version from its SKILL.md.
Each one is a field a critic could otherwise transcribe wrongly.

Usage:
    python skills/_shared/merge.py --skill critique-clarity --artifact path/to/file.md < findings.json

`findings.json` is either {"findings": [...]} or a bare [...]. Prints one envelope to stdout, and
prints nothing at all if it would not validate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


ROOT = _find_repo_root(Path(__file__).resolve())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contract.validate import validate_document  # noqa: E402
from skills._shared.envelope import assemble_envelope  # noqa: E402
from skills._shared.findings import RawFinding  # noqa: E402

# Built with chr() so this file carries none of the punctuation it exists to strip, matching
# contract/validate.py's and bench/baseline/postprocess.py's own convention.
_DASHES = {chr(0x2014): " - ", chr(0x2013): " - "}
_WHITESPACE_RE = re.compile(r"\s+")

# contract/critique-contract.schema.json: $defs/locationText, and $defs/finding's own properties.
_PROSE_FIELD_MAX_LENGTH = {"location": 400, "evidence": 2000, "violation": 1000, "fix": 1000}

_VERSION_RE = re.compile(r"^version:\s*(\S+)\s*$", re.MULTILINE)


class MergeError(RuntimeError):
    """Raised when the input cannot be turned into an envelope at all."""


def _sanitize_prose(text: str, *, max_length: int) -> str:
    """The contract's prose rules: no em dash, no en dash, no whitespace runs, no leading or
    trailing whitespace, no more than the schema's maximum.

    Same rule `bench/baseline/postprocess.py` applies to the baseline lane, for the reason it
    states there: the model was never told the house style, and a truncated but contract-valid
    envelope is better than a faithful but invalid one. This cannot change which criterion was
    cited, at what severity, or where.
    """
    for bad, replacement in _DASHES.items():
        text = text.replace(bad, replacement)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    if len(text) > max_length:
        text = text[:max_length].rstrip()
    return text


def _to_raw(finding: Mapping[str, Any], *, index: int) -> RawFinding:
    missing = [k for k in ("criterion", "severity", "location", "evidence", "violation", "fix") if k not in finding]
    if missing:
        raise MergeError(f"finding {index}: missing required field(s) {', '.join(missing)}")

    lane = str(finding.get("lane", "scripted"))
    confidence = str(finding.get("confidence", "high"))
    if lane == "scripted" and confidence != "high":
        # Not a judgment call. A scripted finding came from a deterministic check, so "high" is
        # simply true, and the contract pins it on those grounds (methodology section 5: scripted
        # findings "are always high confidence or they are bugs"). A model claiming otherwise is
        # stating something false about its own lane, not expressing a real doubt.
        confidence = "high"

    try:
        severity = int(finding["severity"])
    except (TypeError, ValueError) as exc:
        raise MergeError(f"finding {index}: severity {finding['severity']!r} is not an integer") from exc

    return RawFinding(
        criterion=str(finding["criterion"]),
        severity=severity,
        location=_sanitize_prose(str(finding["location"]), max_length=_PROSE_FIELD_MAX_LENGTH["location"]),
        evidence=_sanitize_prose(str(finding["evidence"]), max_length=_PROSE_FIELD_MAX_LENGTH["evidence"]),
        violation=_sanitize_prose(str(finding["violation"]), max_length=_PROSE_FIELD_MAX_LENGTH["violation"]),
        fix=_sanitize_prose(str(finding["fix"]), max_length=_PROSE_FIELD_MAX_LENGTH["fix"]),
        lane=lane,
        confidence=confidence,
        instances=tuple(finding.get("instances") or ()),
        rubric_source=finding.get("rubric_source"),
        selector=finding.get("selector"),
    )


_CRITERION_RE = re.compile(r"^    - (\S+)\s*$", re.MULTILINE)


def _rubrics_for(raw_findings: Sequence[RawFinding], *, skill: str, repo_root: Path) -> list[str]:
    """The namespace of each cited criterion, which is the text before its first hyphen
    (contract/critique-contract.schema.json, $defs/rubricNamespace). Derived rather than asked for,
    because run.rubrics must cover every namespace the findings draw on or the validator's
    rubrics-cover-findings rule fails the whole envelope.

    A clean artifact cites nothing, and an empty rubrics list is not a valid envelope, so a run
    with no findings falls back to the namespaces the skill itself declares. That is the honest
    answer to "which rubrics did this run apply": all of them, and none was breached.
    """
    cited = sorted({raw.criterion.split("-", 1)[0] for raw in raw_findings})
    if cited:
        return cited
    skill_md = repo_root / "skills" / skill / "SKILL.md"
    declared = _CRITERION_RE.findall(skill_md.read_text(encoding="utf-8")) if skill_md.is_file() else []
    return sorted({c.split("-", 1)[0] for c in declared})


def _relative_label(artifact: Path) -> str:
    """What to record as `run.artifact`.

    The contract requires a relative path: `$defs`'s pattern rejects a leading separator and a
    drive letter, so an absolute path invalidates the whole envelope. Callers hand this module
    whatever path they happen to have, usually absolute, so the relativisation happens here rather
    than being one more thing for a critic to get right. Relative to the working directory when the
    artifact is underneath it, which is the ordinary case, and the bare filename otherwise.
    """
    resolved = artifact.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return resolved.name


def _skill_version(skill: str, *, repo_root: Path) -> str:
    skill_md = repo_root / "skills" / skill / "SKILL.md"
    if not skill_md.is_file():
        raise MergeError(f"{skill_md} does not exist; is --skill spelled correctly?")
    match = _VERSION_RE.search(skill_md.read_text(encoding="utf-8"))
    if not match:
        raise MergeError(f"{skill_md} declares no version: in its frontmatter")
    return match.group(1)


def assemble(
    *,
    skill: str,
    artifact: Path,
    findings: Sequence[Mapping[str, Any]],
    repo_root: Path = ROOT,
    model: str = "none",
    timestamp: str | None = None,
    severity_3_threshold: int = 0,
    artifact_label: str | None = None,
) -> dict[str, Any]:
    """Build one contract-valid envelope from `findings`, doing every deterministic step for the
    caller: prose normalisation, ranking, bounding, id assignment, the histogram over everything
    found, the suppressed count, and the gate.
    """
    if not artifact.is_file():
        raise MergeError(f"{artifact} does not exist")

    raw_findings = [_to_raw(f, index=i) for i, f in enumerate(findings)]
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

    return assemble_envelope(
        skill=skill,
        skill_version=_skill_version(skill, repo_root=repo_root),
        artifact_path=artifact_label or _relative_label(artifact),
        artifact_sha256=digest,
        model=model,
        timestamp=timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        rubrics=_rubrics_for(raw_findings, skill=skill, repo_root=repo_root),
        raw_findings=raw_findings,
        severity_3_threshold=severity_3_threshold,
    )


def _read_findings(text: str) -> list[Mapping[str, Any]]:
    """Accept {"findings": [...]} or a bare [...]. Models emit both, and rejecting either would
    cost a whole run over a formatting choice that carries no meaning."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MergeError(f"stdin is not valid JSON: {exc}") from exc
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("findings"), list):
        return payload["findings"]
    raise MergeError('expected {"findings": [...]} or a bare [...]')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        # Named after however it was actually invoked, which is usually a skill's own
        # scripts/merge.py shim. A fixed prog string sent a real session chasing
        # skills/_shared/merge.py, a path that does not resolve from where it was standing, at the
        # exact moment the usage message was supposed to be helping it recover.
        prog=f"python3 {Path(sys.argv[0]).name}" if sys.argv and sys.argv[0] else "merge.py",
        description="Assemble one contract-valid run envelope from merged critique findings.",
    )
    parser.add_argument("--skill", required=True, help="Skill name, e.g. critique-clarity.")
    parser.add_argument("--artifact", required=True, type=Path, help="Path to the critiqued artifact.")
    parser.add_argument(
        "--findings",
        default=None,
        type=Path,
        help="JSON file of findings. Omit to read them from stdin instead.",
    )
    parser.add_argument(
        "--artifact-label",
        default=None,
        help="What to record as run.artifact, if it differs from the path on disk.",
    )
    parser.add_argument("--model", default="none", help='Model id to record (default "none").')
    parser.add_argument("--timestamp", default=None, help="UTC timestamp to record (default: now).")
    parser.add_argument("--severity-3-threshold", type=int, default=0, dest="severity_3_threshold")
    args = parser.parse_args(argv)

    try:
        if args.findings is not None:
            if not args.findings.is_file():
                print(f"merge: --findings {args.findings} does not exist", file=sys.stderr)
                return 1
            raw = args.findings.read_text(encoding="utf-8")
        else:
            raw = sys.stdin.read()
            if not raw.strip():
                # The observed failure: invoked with nothing on stdin, which is easy to do when the
                # command also has to `cd` to reach this script. Say what to do rather than let a
                # JSON parser error stand, because the run that hit this abandoned the tool instead
                # of correcting the call.
                print(
                    "merge: no findings on stdin. Either pipe them in "
                    "(cat findings.json | merge.py ...) or pass --findings <file>, "
                    "which avoids stdin entirely and is easier when the command has to cd first.",
                    file=sys.stderr,
                )
                return 1

        envelope = assemble(
            skill=args.skill,
            artifact=args.artifact,
            findings=_read_findings(raw),
            model=args.model,
            timestamp=args.timestamp,
            severity_3_threshold=args.severity_3_threshold,
            artifact_label=args.artifact_label,
        )
    except MergeError as exc:
        print(f"merge: {exc}", file=sys.stderr)
        return 1

    # Never print something that does not validate: a downstream reader cannot tell a broken
    # envelope from a real one. runner.py holds the same line for the scripted lane.
    result = validate_document(envelope)
    if not result.ok:
        print("merge: the assembled envelope is not contract-valid:", file=sys.stderr)
        for error in result.errors[:5]:
            print(f"  {error}", file=sys.stderr)
        return 1

    json.dump(envelope, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
