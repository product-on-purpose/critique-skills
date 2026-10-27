"""Assemble one contract-valid run envelope from a critique's scripted and judged findings.

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

E73 (2026-10-26) removed a second kind of trust this module used to extend to the model: it no
longer accepts the model's own copy of the scripted lane, or the model's own claim about which lane
a finding belongs to. This module now runs the skill's own `scripts/checks.py` `check(artifact)`
itself, in-process, exactly as `skills/_shared/runner.py`'s `_run` does, and that is the entire
scripted lane. A model finding's lane comes from the skill's own `SKILL.md` declaration
(`checks.scripted` / `checks.judged`), never from a `lane` field the model wrote: a finding on a
scripted criterion is dropped (the script already covers it, and the drop is reported on standard
error), and a finding on an undeclared criterion is rejected unless it is marked
`rubric_source: byor`. See `docs/internal/decisions/0041-merge-runs-the-scripted-lane-itself.md`.

Everything derivable is derived rather than asked for: the artifact hash is computed from the file,
`rubrics` from the namespaces the findings actually cite, and the skill version from its SKILL.md.
Each one is a field a critic could otherwise transcribe wrongly.

Usage:
    python skills/_shared/merge.py --skill critique-clarity --artifact path/to/file.md < findings.json

`findings.json` is either {"findings": [...]} or a bare [...], and holds the judged lane only: the
scripted lane comes from running `checks.py` on `--artifact`, not from this file. Prints one envelope
to stdout, and prints nothing at all if it would not validate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
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

from contract.validate import MissingDependencyError, validate_document  # noqa: E402
from skills._shared.artifact import Artifact  # noqa: E402
from skills._shared.envelope import assemble_envelope  # noqa: E402
from skills._shared.findings import RawFinding  # noqa: E402

# Built with chr() so this file carries none of the punctuation it exists to strip, matching
# contract/validate.py's and bench/baseline/postprocess.py's own convention.
_DASHES = {chr(0x2014): " - ", chr(0x2013): " - "}
_WHITESPACE_RE = re.compile(r"\s+")

# contract/critique-contract.schema.json: $defs/locationText, and $defs/finding's own properties.
_PROSE_FIELD_MAX_LENGTH = {"location": 400, "evidence": 2000, "violation": 1000, "fix": 1000}

# The skill version is `metadata.version` (Standard sec 3.7; the toolkit's U16 makes a top-level
# `version` an error from Standard 0.14). A top-level one is the pre-0.14 placement, reported as
# that rather than as a missing field, so an author following an old template learns where it went.
_TOP_LEVEL_VERSION_RE = re.compile(r"^version:")
_NESTED_KEY_RE = re.compile(r"^(\s+)version:\s*(\S+)\s*$")


def read_skill_version(skill_md_text: str) -> str:
    """Return `metadata.version` from a SKILL.md's frontmatter, or raise ValueError.

    Reads the frontmatter block only, so a body line that happens to start with `version:` is never
    mistaken for the declaration, and reads only direct children of `metadata:`. Raises with a
    distinct message for a missing block, a top-level `version`, and an absent `metadata.version`.
    Shared with `bench/run_bench.py`, which once defaulted a missing version to "0.1.0" and so
    would have recorded every moved skill under the wrong `skill_version` without an error.
    """
    lines = skill_md_text.lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md has no '---' delimited frontmatter block")
    close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if close is None:
        raise ValueError("SKILL.md frontmatter has no closing '---' delimiter")
    frontmatter = lines[1:close]
    if any(_TOP_LEVEL_VERSION_RE.match(line) for line in frontmatter):
        raise ValueError(
            "SKILL.md declares version at the top level of its frontmatter; Standard sec 3.7 places it "
            "under metadata (toolkit check U16, an error from Standard 0.14), as metadata.version"
        )
    in_metadata = False
    child_indent: str | None = None
    for line in frontmatter:
        if not line.strip():
            continue
        if not line[0].isspace():
            in_metadata = line.rstrip() == "metadata:"
            child_indent = None
            continue
        if not in_metadata:
            continue
        indent = line[: len(line) - len(line.lstrip())]
        if child_indent is None:
            child_indent = indent
        match = _NESTED_KEY_RE.match(line)
        if match and match.group(1) == child_indent:
            return match.group(2).strip("\"'")
    raise ValueError("SKILL.md frontmatter declares no metadata.version")


_skill_selftest_module_cache: dict[str, Any] = {}


def _skill_selftest_parse_frontmatter(repo_root: Path):
    """Load `scripts/skill-selftest.py` as a module and return its `parse_frontmatter` function.

    Cached per resolved path, since the module defines nothing that depends on call-time state and
    reloading it on every `read_lane_manifest` call would cost a file read and a parse for nothing.
    """
    path = repo_root / "scripts" / "skill-selftest.py"
    key = str(path.resolve()) if path.exists() else str(path)
    module = _skill_selftest_module_cache.get(key)
    if module is None:
        if not path.is_file():
            raise MergeError(f"{path} does not exist")
        module_name = "_critique_skills_skill_selftest"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise MergeError(f"could not load {path} as a module")
        module = importlib.util.module_from_spec(spec)
        # Registered before exec_module for the same reason `_load_check_fn` registers a skill's
        # checks.py: this file's `@dataclass(frozen=True)` resolves its own module by this name.
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        _skill_selftest_module_cache[key] = module
    return module.parse_frontmatter


def read_lane_manifest(
    skill_md_text: str, *, repo_root: Path = ROOT
) -> tuple[frozenset[str], frozenset[str]]:
    """Return `(scripted, judged)` criterion ID sets from a SKILL.md's `checks.scripted` and
    `checks.judged` frontmatter declaration (docs/internal/skill-template.md, "Lane manifest").

    This is what requirement 3 means by "a model finding's lane comes from the declaration": this
    function is the declaration, and a finding's own `lane` field never overrides it.

    Delegates to `scripts/skill-selftest.py`'s own `parse_frontmatter`, the parser that gates every
    SKILL.md in CI (`scripts/tests/test_skills_conformance.py`), rather than a second, hand-rolled
    reader of the same block. The hand-rolled reader this replaced disagreed with that parser on
    three inputs every SKILL.md author could plausibly write: a quoted ID kept its quotes (so
    `"A-ONE"` never matched the bare `A-ONE` a finding cites), a list item with a trailing inline
    comment was dropped outright, and a `checks:` sibling key other than `scripted`/`judged` (a
    `notes:` block, say) leaked its items into whichever lane preceded it. All seven shipped
    `SKILL.md` files and the template fixture happened to avoid every one of those shapes, so the
    disagreement was latent. Importing the real parser means a future change to it changes this
    function too, instead of leaving two readers to drift apart unnoticed.
    """
    parse_frontmatter = _skill_selftest_parse_frontmatter(repo_root)
    try:
        frontmatter = parse_frontmatter(skill_md_text.lstrip("﻿"))
    except Exception as exc:
        raise ValueError(f"SKILL.md: {exc}") from exc

    checks = frontmatter.get("checks") if isinstance(frontmatter, dict) else None
    if not isinstance(checks, dict):
        raise ValueError("SKILL.md frontmatter declares no checks.scripted or checks.judged manifest")

    def _ids(key: str) -> list[str]:
        value = checks.get(key)
        if value in (None, []):
            return []
        if not isinstance(value, list):
            raise ValueError(f"SKILL.md frontmatter's checks.{key} is not a list")
        return [str(item) for item in value]

    scripted, judged = _ids("scripted"), _ids("judged")
    if not scripted and not judged:
        raise ValueError("SKILL.md frontmatter declares no checks.scripted or checks.judged manifest")
    return frozenset(scripted), frozenset(judged)


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


def _to_raw_judged(finding: Mapping[str, Any], *, index: int) -> RawFinding:
    """Build a RawFinding for one kept model finding. Lane is always "judged": a finding only
    reaches here because its criterion is in `checks.judged`, or it carries
    `rubric_source: byor` (D2 option A) - never because its criterion is in `checks.scripted`,
    which is dropped before this function is called (D1 option A). Confidence defaults to
    "medium" when the model states none (D3 option A); a stated value, including "high", is left
    alone, because it is the model's own claim, not a scripted fact.
    """
    missing = [k for k in ("criterion", "severity", "location", "evidence", "violation", "fix") if k not in finding]
    if missing:
        raise MergeError(f"finding {index}: missing required field(s) {', '.join(missing)}")

    confidence = finding.get("confidence")
    confidence = str(confidence) if confidence else "medium"

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
        lane="judged",
        confidence=confidence,
        instances=tuple(finding.get("instances") or ()),
        rubric_source=finding.get("rubric_source"),
        selector=finding.get("selector"),
    )


def _route_model_findings(
    findings: Sequence[Mapping[str, Any]],
    *,
    scripted_ids: frozenset[str],
    judged_ids: frozenset[str],
) -> tuple[list[RawFinding], dict[str, int]]:
    """Requirements 3-6 (D1, D2, D3): file each model finding under the lane its criterion is
    declared in, never the lane the model wrote in its own `lane` field.

    Returns the kept, judged-lane findings and a `{criterion: dropped_count}` map, which is D1's
    "report the count on standard error" (requirement 4); the caller decides how to report it.
    Raises MergeError naming every undeclared, non-BYOR criterion at once (D2 option A, requirement
    5), rather than failing on the first one, so one merge run reports every bad ID it saw.
    """
    kept: list[RawFinding] = []
    dropped: dict[str, int] = {}
    undeclared: list[str] = []

    for index, finding in enumerate(findings):
        if not isinstance(finding, Mapping):
            raise MergeError(f"finding {index}: expected an object, got {type(finding).__name__}")
        criterion = finding.get("criterion")
        if criterion is None:
            raise MergeError(f"finding {index}: missing required field(s) criterion")
        criterion = str(criterion)

        if criterion in scripted_ids:
            # D1 option A: the scripted lane is check()'s output and only that. A model's copy of
            # a scripted criterion - whatever it claims about severity, location or its own lane -
            # is dropped, not merged in, which is also what makes the old pass 4 (requirement 8)
            # give the same envelope as the new one: its script-finding copies all land here.
            dropped[criterion] = dropped.get(criterion, 0) + 1
            continue

        if criterion in judged_ids or finding.get("rubric_source") == "byor":
            # D2 option A: a BYOR finding is judged whatever its namespace; a declared judged
            # criterion is judged because that is what the declaration says.
            kept.append(_to_raw_judged(finding, index=index))
            continue

        undeclared.append(criterion)

    if undeclared:
        named = ", ".join(sorted(set(undeclared)))
        raise MergeError(
            "finding criterion(s) are not declared in SKILL.md's checks.scripted or checks.judged, "
            f"and not marked rubric_source: byor: {named}"
        )

    return kept, dropped


def _load_check_fn(skill: str, *, repo_root: Path):
    """Load the skill's own `scripts/checks.py` as a module and return its `check` function.

    A unique module name per skill keeps two skills loaded in the same process (as the parametrized
    tests do) from overwriting each other in `sys.modules`. The module is registered in
    `sys.modules` before `exec_module` runs, which several `checks.py` files need: a dataclass
    defined under `from __future__ import annotations` resolves its own module by that name.
    """
    checks_path = repo_root / "skills" / skill / "scripts" / "checks.py"
    if not checks_path.is_file():
        raise MergeError(f"{checks_path} does not exist; is --skill spelled correctly?")
    module_name = f"_critique_skills_checks__{skill.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, checks_path)
    if spec is None or spec.loader is None:
        raise MergeError(f"could not load {checks_path} as a module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    check_fn = getattr(module, "check", None)
    if check_fn is None:
        raise MergeError(f"{checks_path} defines no check(artifact) function")
    return check_fn


def run_script_checks(skill: str, artifact: Artifact, *, repo_root: Path = ROOT) -> list[RawFinding]:
    """Requirement 1: run the skill's own scripted lane in-process, the way
    `skills/_shared/runner.py`'s `_run` does, rather than trusting a model's copy of it.

    Returns the raw, unranked, unbounded findings `check()` emits. Requirement 2: every one enters
    the merged pool as `scripted`, exactly as emitted - that is `RawFinding`'s own default, and no
    `check()` function sets `lane` to anything else, so nothing further is needed here to make that
    true. Running `checks.py` as a subprocess would not do: its own output is already bounded
    (`skills/_shared/runner.py`'s `_run` calls `rank_and_bound` before printing), so a finding below
    severity 3 beyond the fifth would already be lost before this module could merge it with the
    judged lane and bound the combined pool.
    """
    check_fn = _load_check_fn(skill, repo_root=repo_root)
    return list(check_fn(artifact))


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


def _read_artifact_bytes(artifact: Path) -> tuple[bytes, str]:
    """Read `artifact` once, and decode it once. The same `raw` bytes are what `run.artifact_sha256`
    hashes and what `check()` reads as `artifact.text` (requirement 7): there is exactly one read of
    the `--artifact` file, so a findings file has no way to make the two disagree about which bytes
    were critiqued. `utf-8-sig` matches `skills/_shared/artifact.py`'s own decoding convention.
    """
    try:
        raw = artifact.read_bytes()
    except OSError as exc:
        raise MergeError(f"{artifact}: {exc}") from exc
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise MergeError(f"{artifact} is not valid UTF-8: {exc}") from exc
    return raw, text


def _skill_md_text(skill: str, *, repo_root: Path) -> str:
    skill_md = repo_root / "skills" / skill / "SKILL.md"
    if not skill_md.is_file():
        raise MergeError(f"{skill_md} does not exist; is --skill spelled correctly?")
    return skill_md.read_text(encoding="utf-8")


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
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one contract-valid envelope from the skill's own scripted lane plus `findings`, the
    judged lane a model wrote, doing every deterministic step for the caller: running `checks.py`,
    routing each model finding to the lane its criterion declares (D1-D3), prose normalisation,
    ranking, bounding, id assignment, the histogram over everything found, the suppressed count,
    and the gate.

    `diagnostics`, when passed a dict, is filled with `dropped_scripted_criteria` (a
    `{criterion: count}` map) and `dropped_count`: D1's "report the count on standard error",
    reported as data so a caller (`main`, below, or a test) decides how to say it.
    """
    if not artifact.is_file():
        raise MergeError(f"{artifact} does not exist")

    raw_bytes, text = _read_artifact_bytes(artifact)
    digest = hashlib.sha256(raw_bytes).hexdigest()
    artifact_path = artifact_label or _relative_label(artifact)
    artifact_obj = Artifact(path=artifact_path, text=text, sha256=digest, disk_path=artifact.resolve())

    skill_md_text = _skill_md_text(skill, repo_root=repo_root)
    try:
        skill_version = read_skill_version(skill_md_text)
    except ValueError as exc:
        raise MergeError(f"{skill} SKILL.md: {exc}") from exc
    try:
        scripted_ids, judged_ids = read_lane_manifest(skill_md_text, repo_root=repo_root)
    except ValueError as exc:
        raise MergeError(f"{skill} SKILL.md: {exc}") from exc

    script_raw = run_script_checks(skill, artifact_obj, repo_root=repo_root)
    model_raw, dropped = _route_model_findings(findings, scripted_ids=scripted_ids, judged_ids=judged_ids)

    if diagnostics is not None:
        diagnostics["dropped_scripted_criteria"] = dict(sorted(dropped.items()))
        diagnostics["dropped_count"] = sum(dropped.values())

    raw_findings = list(script_raw) + model_raw

    return assemble_envelope(
        skill=skill,
        skill_version=skill_version,
        artifact_path=artifact_path,
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
        help="JSON file of judged-lane findings. Omit to read them from stdin instead.",
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

        diagnostics: dict[str, Any] = {}
        envelope = assemble(
            skill=args.skill,
            artifact=args.artifact,
            findings=_read_findings(raw),
            model=args.model,
            timestamp=args.timestamp,
            severity_3_threshold=args.severity_3_threshold,
            artifact_label=args.artifact_label,
            diagnostics=diagnostics,
        )
    except MergeError as exc:
        print(f"merge: {exc}", file=sys.stderr)
        return 1
    except MissingDependencyError as exc:
        # Same guard skills/_shared/runner.py's run_scripted_lane uses: a missing jsonschema is a
        # fresh-install state, not a bug, and the point of running checks.py in-process (requirement
        # 1) is defeated if that state now reaches the caller as a traceback instead.
        print(str(exc), file=sys.stderr)
        return 1

    if diagnostics.get("dropped_count"):
        # D1's "report the count on standard error" (requirement 4): every model finding on a
        # scripted criterion was dropped, not merged in, and this is the only trace of that left.
        criteria = ", ".join(
            f"{criterion} x{count}" for criterion, count in diagnostics["dropped_scripted_criteria"].items()
        )
        print(
            f"merge: dropped {diagnostics['dropped_count']} model finding(s) on scripted "
            f"criterion(s), because the scripted lane is checks.py's output and only that: {criteria}",
            file=sys.stderr,
        )

    # Never print something that does not validate: a downstream reader cannot tell a broken
    # envelope from a real one. runner.py holds the same line for the scripted lane.
    try:
        result = validate_document(envelope)
    except MissingDependencyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
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
