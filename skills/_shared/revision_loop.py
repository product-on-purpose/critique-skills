"""The revision loop's deterministic steps: stop-check, brief, resume, and compare.

N4 (the revision-loop chain) runs ADR 0040's five steps: critique, record dispositions, stop or
pause with a revision brief, and, on resume with a revised artifact, re-critique and compare. Two
of those steps call a model, and each is already a `critique-<domain>` skill run. Everything else
is bookkeeping over contract documents, and it lives here, so it can be tested on committed
fixtures with no model call (N4 decision D9).

No function here writes to the artifact under critique. The library never revises it: the person,
or a tool the person runs on their own authority, does (ADR 0040).

Usage, from anywhere, with the plugin's root on disk:

    python3 <plugin>/skills/_shared/revision_loop.py stop-check --envelope E [--iteration N]
    python3 <plugin>/skills/_shared/revision_loop.py brief --envelope E --dispositions D [--out P]
    python3 <plugin>/skills/_shared/revision_loop.py resume --artifact A --dispositions D [--envelope E]
    python3 <plugin>/skills/_shared/revision_loop.py compare --previous E1 --current E2

Every subcommand prints one JSON object on stdout. Exit codes: 0 when the step succeeded (a stop
decision is a success, and the JSON says which stop), 3 when an input is not a contract-valid
document or the inputs disagree with each other, and 4 for a usage error such as an unreadable file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in (None, ""):
    # Run as a script path: put the repository root on sys.path so `contract` imports resolve.
    _here = Path(__file__).resolve()
    for _candidate in _here.parents:
        if (_candidate / "library.json").is_file():
            if str(_candidate) not in sys.path:
                sys.path.insert(0, str(_candidate))
            break

from contract.validate import validate_document  # noqa: E402

# Methodology section 10: the loop runs at most three iterations. The contract deliberately sets no
# maximum on `iteration` (N4 decision D4), so this constant is the only place the bound lives.
ITERATION_BOUND = 3

SEVERITY_KEYS: tuple[str, ...] = ("0", "1", "2", "3", "4")

CONTINUE = "continue"
STOP_CONVERGED = "stop-converged"
STOP_BOUND = "stop-bound-reached"
STOP_NOTHING_ACCEPTED = "stop-nothing-accepted"

BRIEF_SUFFIX = ".revision-brief.json"

# $defs/envelopeRef's property order in the contract schema. The brief writes its envelope reference
# in this order, whatever order the disposition log used, so its bytes depend on content alone.
ENVELOPE_REF_KEYS: tuple[str, ...] = (
    "skill",
    "skill_version",
    "artifact",
    "artifact_sha256",
    "timestamp",
    "path",
    "envelope_sha256",
)

EXIT_OK = 0
EXIT_INVALID = 3
EXIT_USAGE = 4


class LoopError(Exception):
    """An input is not contract-valid, or two inputs disagree. Exit code 3."""


class UsageError(Exception):
    """A file cannot be read or parsed, or an argument is wrong. Exit code 4."""


# --------------------------------------------------------------------------
# Loading and validating inputs
# --------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise UsageError(f"cannot read '{path}': {exc}") from exc
    except UnicodeDecodeError as exc:
        raise UsageError(f"'{path}' is not UTF-8 text: {exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise UsageError(f"'{path}' is not valid JSON: {exc}") from exc


def _require_valid(doc: Any, *, what: str, path: Path | None = None, **kwargs: Any) -> None:
    result = validate_document(doc, **kwargs)
    if not result.ok:
        where = f" '{path}'" if path is not None else ""
        details = "; ".join(str(issue) for issue in result.errors)
        raise LoopError(f"{what}{where} is not contract-valid: {details}")


def load_envelope(path: Path) -> dict[str, Any]:
    doc = _load_json(path)
    if not isinstance(doc, dict) or "run" not in doc:
        raise LoopError(f"'{path}' is not a run envelope (it has no 'run' object)")
    _require_valid(doc, what="envelope", path=path)
    return doc


def load_disposition_log(path: Path, *, envelope: Mapping[str, Any] | None = None) -> dict[str, Any]:
    doc = _load_json(path)
    if not isinstance(doc, dict) or "dispositions" not in doc:
        raise LoopError(f"'{path}' is not a disposition log (it has no 'dispositions' list)")
    _require_valid(doc, what="disposition log", path=path, referenced_envelope=envelope)
    check_one_decision_per_finding(doc)
    return doc


def check_one_decision_per_finding(log: Mapping[str, Any]) -> None:
    """A finding decided twice in one log is ambiguous, and the contract does not forbid it, so
    the loop does: an accept followed by a reject must not silently become an accept."""
    seen: set[str] = set()
    for entry in log["dispositions"]:
        finding_id = entry["finding_id"]
        if finding_id in seen:
            raise LoopError(
                f"the disposition log decides finding '{finding_id}' more than once; keep one "
                "decision per finding"
            )
        seen.add(finding_id)


def _envelope_key(envelope: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    run = envelope["run"]
    return run["skill"], run["artifact_sha256"], run["timestamp"]


def _reference_key(log: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    ref = log["envelope"]
    return ref["skill"], ref["artifact_sha256"], ref["timestamp"]


def check_log_references_envelope(log: Mapping[str, Any], envelope: Mapping[str, Any]) -> None:
    """The log's envelope reference must name this envelope by its composite key: skill, artifact
    hash, and timestamp. Finding IDs are unique only within a run, so a log applied to the wrong
    envelope would select the wrong findings without any other error."""
    if _reference_key(log) != _envelope_key(envelope):
        skill, sha, ts = _reference_key(log)
        raise LoopError(
            "the disposition log references a different run: it names "
            f"skill '{skill}', artifact_sha256 '{sha[:12]}...', timestamp '{ts}', "
            "and the envelope does not match all three"
        )


def log_iteration(log: Mapping[str, Any]) -> int:
    """A log with no `iteration` field is the first pass: contract 1.0.0 logs predate the field."""
    return int(log.get("iteration", 1))


# --------------------------------------------------------------------------
# Step 3: the stop-check
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class StopCheck:
    decision: str
    iteration: int
    severity_3_or_4: int

    def as_json(self) -> dict[str, Any]:
        return {
            "step": "stop-check",
            "decision": self.decision,
            "iteration": self.iteration,
            "iteration_bound": ITERATION_BOUND,
            "severity_3_or_4": self.severity_3_or_4,
        }


def stop_check(envelope: Mapping[str, Any], iteration: int) -> StopCheck:
    """Stop when no finding at severity 3 or above remains, or when this is the third iteration,
    whichever comes first (ADR 0040, methodology section 10).

    Reads `summary.by_severity`, which counts every finding the run produced. Severity 3 and 4 are
    never suppressed (validator rule 3), so the emitted and the recorded counts agree here.
    Convergence is tested first: a third iteration that reaches zero has converged, not hit the
    bound.
    """
    if iteration < 1:
        raise UsageError(f"--iteration must be 1 or greater, got {iteration}")
    by_severity = envelope["summary"]["by_severity"]
    remaining = int(by_severity["3"]) + int(by_severity["4"])
    if remaining == 0:
        decision = STOP_CONVERGED
    elif iteration >= ITERATION_BOUND:
        decision = STOP_BOUND
    else:
        decision = CONTINUE
    return StopCheck(decision=decision, iteration=iteration, severity_3_or_4=remaining)


# --------------------------------------------------------------------------
# Step 4: the revision brief
# --------------------------------------------------------------------------


def build_brief(envelope: Mapping[str, Any], log: Mapping[str, Any]) -> dict[str, Any]:
    """Project an envelope and its disposition log into a revision brief (contract 1.1.0).

    One item per accepted finding, in the order the log records the decisions, carrying the
    finding's id, criterion, location, and fix copied verbatim from the envelope. The envelope
    reference is the log's own, so the brief binds to exactly the run the person dispositioned.
    No model call, no clock, no randomness: the same two inputs always give the same brief.
    """
    check_log_references_envelope(log, envelope)
    check_one_decision_per_finding(log)
    findings = {f["id"]: f for f in envelope["findings"]}
    items: list[dict[str, Any]] = []
    for entry in log["dispositions"]:
        if entry["disposition"] != "accept":
            continue
        finding_id = entry["finding_id"]
        finding = findings.get(finding_id)
        if finding is None:
            raise LoopError(f"accepted finding '{finding_id}' is not in the envelope")
        items.append(
            {
                "finding_id": finding_id,
                "criterion": finding["criterion"],
                "location": finding["location"],
                "fix": finding["fix"],
            }
        )
    ref = log["envelope"]
    envelope_ref = {key: ref[key] for key in ENVELOPE_REF_KEYS if key in ref}
    return {"envelope": envelope_ref, "iteration": log_iteration(log), "items": items}


def serialize_brief(brief: Mapping[str, Any]) -> str:
    """The brief's on-disk bytes: two-space indent, keys in contract order, one trailing newline."""
    return json.dumps(brief, indent=2, ensure_ascii=False) + "\n"


def default_brief_path(envelope: Mapping[str, Any]) -> Path:
    """`<artifact-stem>.revision-brief.json` beside the artifact (N4 decision D3), resolved against
    the working directory, which is where `run.artifact` was recorded relative to."""
    artifact = Path(envelope["run"]["artifact"])
    return artifact.with_name(artifact.stem + BRIEF_SUFFIX)


def pause(
    envelope: Mapping[str, Any], log: Mapping[str, Any]
) -> tuple[StopCheck | None, dict[str, Any] | None]:
    """Steps 3 and 4 together: run the stop-check at the log's iteration, and build the brief only
    when the loop continues and the person accepted at least one finding.

    Returns `(check, brief)`. When the check stops the loop, the brief is None. When the check says
    continue but nothing was accepted, the decision becomes `stop-nothing-accepted`: an empty brief
    would ask the person to revise nothing, and the contract rejects one.
    """
    check_log_references_envelope(log, envelope)
    check = stop_check(envelope, log_iteration(log))
    if check.decision != CONTINUE:
        return check, None
    brief = build_brief(envelope, log)
    if not brief["items"]:
        return StopCheck(STOP_NOTHING_ACCEPTED, check.iteration, check.severity_3_or_4), None
    _require_valid(brief, what="revision brief", referenced_envelope=dict(envelope))
    return check, brief


# --------------------------------------------------------------------------
# Step 5a: resume
# --------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise UsageError(f"cannot read '{path}': {exc}") from exc


def resume(
    artifact: Path, log_path: Path, envelope_path: Path | None = None
) -> dict[str, Any]:
    """Locate the prior run from what the person hands over (N4 decision D2): the revised artifact
    and the prior iteration's disposition log, plus the prior envelope when the log does not name
    its path.

    The prior envelope is the log's `envelope.path` or `--envelope`. If both are given and name
    different files, that is a conflict, reported by name, never resolved by guessing. If neither
    is given, there is nothing to resume against. The located envelope must match the log's
    composite key, the loop must not already have stopped, and the artifact must have changed.
    """
    log = load_disposition_log(log_path)
    candidates: dict[str, Path] = {}
    ref_path = log["envelope"].get("path")
    if ref_path is not None:
        candidates["the log's envelope.path"] = Path(ref_path)
    if envelope_path is not None:
        candidates["--envelope"] = envelope_path
    if not candidates:
        raise UsageError(
            "the disposition log does not record its envelope's path; pass --envelope with the "
            "prior iteration's envelope"
        )
    resolved = {name: p.resolve() for name, p in candidates.items()}
    if len(set(resolved.values())) > 1:
        listing = ", ".join(f"{name} = '{candidates[name]}'" for name in candidates)
        raise LoopError(f"conflicting prior envelopes: {listing}; pass exactly one")
    prior_path = next(iter(candidates.values()))
    if not prior_path.is_file():
        raise UsageError(
            f"prior envelope '{prior_path}' not found. A relative envelope.path is read from the "
            "current directory, as run.artifact is, so run resume from the directory the first "
            "invocation ran in, or pass --envelope"
        )
    envelope = load_envelope(prior_path)
    check_log_references_envelope(log, envelope)
    expected_sha = log["envelope"].get("envelope_sha256")
    if expected_sha is not None and _sha256_file(prior_path) != expected_sha:
        raise LoopError(
            f"'{prior_path}' does not match the envelope_sha256 the disposition log records"
        )
    _require_valid(log, what="disposition log", path=log_path, referenced_envelope=envelope)

    prior_iteration = log_iteration(log)
    check = stop_check(envelope, prior_iteration)
    if check.decision == STOP_CONVERGED:
        raise LoopError(
            f"the loop already converged at iteration {prior_iteration}: the prior envelope has "
            "no finding at severity 3 or above"
        )
    if check.decision == STOP_BOUND:
        raise LoopError(
            f"the loop already reached its bound of {ITERATION_BOUND} iterations; disposition the "
            "remaining findings as they stand rather than starting a fourth"
        )
    if not any(entry["disposition"] == "accept" for entry in log["dispositions"]):
        raise LoopError(
            f"iteration {prior_iteration} accepted no finding, so the loop stopped there with "
            "nothing to revise"
        )
    if _sha256_file(artifact) == envelope["run"]["artifact_sha256"]:
        raise LoopError(
            f"'{artifact}' is byte-identical to the artifact iteration {prior_iteration} "
            "critiqued; revise it before resuming"
        )
    return {
        "step": "resume",
        "skill": envelope["run"]["skill"],
        "artifact": artifact.as_posix(),
        "prior_artifact": envelope["run"]["artifact"],
        "prior_envelope": prior_path.as_posix(),
        "prior_iteration": prior_iteration,
        "iteration": prior_iteration + 1,
    }


# --------------------------------------------------------------------------
# Step 5b: compare
# --------------------------------------------------------------------------


def _criterion_counts(envelope: Mapping[str, Any]) -> Counter[str]:
    return Counter(f["criterion"] for f in envelope["findings"])


def compare(previous: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    """Per-criterion and per-severity count deltas between two runs of one skill (N4 decision D5).

    It never pairs individual findings: a finding id is unique only within its own envelope, and a
    location is prose written against one version of the artifact, so neither identifies "the same"
    finding across a revision. Criterion counts are of emitted findings; severity counts are
    `summary.by_severity`, which also counts findings the output bound suppressed.
    """
    prev_skill = previous["run"]["skill"]
    curr_skill = current["run"]["skill"]
    if prev_skill != curr_skill:
        raise LoopError(
            f"the two envelopes come from different skills ('{prev_skill}' and '{curr_skill}'); "
            "a comparison across rubrics means nothing"
        )
    prev_artifact = previous["run"]["artifact"]
    curr_artifact = current["run"]["artifact"]
    if prev_artifact != curr_artifact:
        raise LoopError(
            f"the two envelopes critique different artifacts ('{prev_artifact}' and "
            f"'{curr_artifact}'); compare runs of one artifact across a revision"
        )
    if previous["run"]["timestamp"] == current["run"]["timestamp"]:
        raise LoopError("the two envelopes are the same run (same timestamp); nothing to compare")
    prev_counts = _criterion_counts(previous)
    curr_counts = _criterion_counts(current)
    by_criterion = {
        criterion: {
            "previous": prev_counts.get(criterion, 0),
            "current": curr_counts.get(criterion, 0),
            "delta": curr_counts.get(criterion, 0) - prev_counts.get(criterion, 0),
        }
        for criterion in sorted(set(prev_counts) | set(curr_counts))
    }
    prev_sev = previous["summary"]["by_severity"]
    curr_sev = current["summary"]["by_severity"]
    by_severity = {
        key: {
            "previous": int(prev_sev[key]),
            "current": int(curr_sev[key]),
            "delta": int(curr_sev[key]) - int(prev_sev[key]),
        }
        for key in SEVERITY_KEYS
    }
    return {
        "step": "compare",
        "skill": curr_skill,
        "previous": {
            "artifact_sha256": previous["run"]["artifact_sha256"],
            "timestamp": previous["run"]["timestamp"],
        },
        "current": {
            "artifact_sha256": current["run"]["artifact_sha256"],
            "timestamp": current["run"]["timestamp"],
        },
        "by_criterion": by_criterion,
        "by_severity": by_severity,
    }


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # pragma: no cover - exercised through main()
        raise UsageError(message)


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog="revision_loop.py",
        description="The revision loop's deterministic steps. Never writes to the artifact.",
    )
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_ArgumentParser)

    p = sub.add_parser("stop-check", help="decide whether the loop continues")
    p.add_argument("--envelope", required=True, type=Path)
    p.add_argument(
        "--iteration",
        type=int,
        default=None,
        help="the iteration this envelope belongs to; read from --dispositions when omitted, else 1",
    )
    p.add_argument("--dispositions", type=Path, default=None)

    p = sub.add_parser("brief", help="stop-check, then write the revision brief when continuing")
    p.add_argument("--envelope", required=True, type=Path)
    p.add_argument("--dispositions", required=True, type=Path)
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="where to write the brief; default <artifact-stem>.revision-brief.json beside the artifact",
    )

    p = sub.add_parser("resume", help="locate the prior run for a revised artifact")
    p.add_argument("--artifact", required=True, type=Path)
    p.add_argument("--dispositions", required=True, type=Path)
    p.add_argument("--envelope", type=Path, default=None)

    p = sub.add_parser("compare", help="count deltas between two runs of one skill")
    p.add_argument("--previous", required=True, type=Path)
    p.add_argument("--current", required=True, type=Path)
    return parser


def _run(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "stop-check":
        envelope = load_envelope(args.envelope)
        iteration = args.iteration
        if args.dispositions is not None:
            log = load_disposition_log(args.dispositions, envelope=envelope)
            check_log_references_envelope(log, envelope)
            logged = log_iteration(log)
            if iteration is not None and iteration != logged:
                raise LoopError(
                    f"--iteration {iteration} disagrees with the disposition log's iteration {logged}"
                )
            iteration = logged
        return stop_check(envelope, iteration if iteration is not None else 1).as_json()

    if args.command == "brief":
        envelope = load_envelope(args.envelope)
        log = load_disposition_log(args.dispositions, envelope=envelope)
        check, brief = pause(envelope, log)
        result = check.as_json()
        result["step"] = "brief"
        out = args.out if args.out is not None else default_brief_path(envelope)
        if brief is None:
            result["brief"] = None
            if out.is_file():
                # Not deleted: removing a file the person may still want is not this step's call.
                result["stale_brief"] = out.as_posix()
            return result
        protected = {
            "the artifact": Path(envelope["run"]["artifact"]),
            "the envelope": args.envelope,
            "the disposition log": args.dispositions,
        }
        for name, path in protected.items():
            if out.resolve() == path.resolve():
                raise UsageError(f"refusing to write the brief over {name} ('{path}')")
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(serialize_brief(brief), encoding="utf-8", newline="\n")
        except OSError as exc:
            raise UsageError(f"cannot write '{out}': {exc}") from exc
        result["brief"] = out.as_posix()
        result["items"] = len(brief["items"])
        return result

    if args.command == "resume":
        return resume(args.artifact, args.dispositions, args.envelope)

    if args.command == "compare":
        return compare(load_envelope(args.previous), load_envelope(args.current))

    raise UsageError(f"unknown command '{args.command}'")  # pragma: no cover


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _build_parser().parse_args(argv)
        result = _run(args)
    except UsageError as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except LoopError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INVALID
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
