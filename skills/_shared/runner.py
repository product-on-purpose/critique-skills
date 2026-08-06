"""The shared scripted-lane CLI every skill's `scripts/checks.py` calls
into. Owns argument parsing, artifact loading, envelope assembly,
contract validation, and `--gate` exit codes, so a skill's checks.py is
never more than: import this, write one check function, call
`run_scripted_lane`.

See docs/internal/skill-template.md, "Wiring scripts/checks.py", for the
full worked example a pipeline agent copies.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Callable, Sequence

from skills._shared.artifact import Artifact, ArtifactError, load_artifact
from skills._shared.envelope import assemble_envelope
from skills._shared.findings import RawFinding
from skills._shared.gate import MissingDependencyError, gate_exit_code, validate_document

CheckFn = Callable[[Artifact], Sequence[RawFinding]]


def build_parser(skill_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="checks.py",
        description=(
            f"{skill_name} scripted-lane checks: one artifact in, one "
            "contract-valid run envelope out, on stdout."
        ),
    )
    parser.add_argument("artifact", help="Path to the artifact to check.")
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Exit with critique-contract gate codes (0/1/2/3/4) instead of 0/1.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=None,
        help="Severity-3 threshold for --gate. Defaults to 0.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root the artifact path is relativized against. "
            "Defaults to the current working directory; override only "
            "when checks.py is not being run from the repository root."
        ),
    )
    return parser


def run_scripted_lane(
    *,
    skill_name: str,
    skill_version: str,
    rubrics: Sequence[str],
    check_fn: CheckFn,
    argv: Sequence[str] | None = None,
    now: Callable[[], datetime] | None = None,
) -> int:
    """The entire body of a skill's `scripts/checks.py` `main()`.

    `check_fn` receives the loaded `Artifact` and returns the
    `RawFinding`s its scripted checks detected, in any order; everything
    after that (id assignment, ranking, bounding, the run record, the
    summary, printing, and the `--gate` exit code) is identical across
    every skill and lives here.

    `now` exists only so tests can pin the timestamp; a real invocation
    always uses the wall clock. Because `run.timestamp` is a real
    instant by contract, it is the one field the "same artifact, same
    output bytes" determinism claim does not cover; see
    docs/internal/skill-template.md, "What determinism does and does not
    cover".

    Returns the process exit code; callers pass this straight to
    `sys.exit`.
    """
    parser = build_parser(skill_name)
    args = parser.parse_args(argv)

    try:
        artifact = load_artifact(args.artifact, repo_root=args.repo_root)
    except ArtifactError as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return 4 if args.gate else 1

    try:
        return _run(
            skill_name=skill_name,
            skill_version=skill_version,
            rubrics=rubrics,
            check_fn=check_fn,
            artifact=artifact,
            args=args,
            now=now,
        )
    except MissingDependencyError as exc:
        # The scripted lane is step 2 of every skill's protocol, so this is the first command an
        # agent runs after a fresh install. Report the remedy, not an import traceback.
        print(str(exc), file=sys.stderr)
        return 4 if args.gate else 1


def _run(
    *,
    skill_name: str,
    skill_version: str,
    rubrics: Sequence[str],
    check_fn: CheckFn,
    artifact: Artifact,
    args: argparse.Namespace,
    now: Callable[[], datetime] | None = None,
) -> int:
    """The part of `run_scripted_lane` that can need the contract validator."""

    raw_findings = list(check_fn(artifact))

    timestamp = (now or _utc_now)().strftime("%Y-%m-%dT%H:%M:%SZ")
    threshold = args.threshold if args.threshold is not None else 0

    envelope = assemble_envelope(
        skill=skill_name,
        skill_version=skill_version,
        artifact_path=artifact.path,
        artifact_sha256=artifact.sha256,
        model="none",  # no judged lane ran; "none" is the contract's own convention for this case
        timestamp=timestamp,
        rubrics=rubrics,
        raw_findings=raw_findings,
        severity_3_threshold=threshold,
    )

    result = validate_document(envelope)
    if not result.ok:
        # A scripted lane that produces an invalid envelope is a bug in
        # the skill's check function, not a usage error; still exit
        # non-gate-clean so CI catches it rather than shipping a broken
        # envelope silently.
        for issue in result.errors:
            print(f"internal error: checks.py produced an invalid envelope: {issue}", file=sys.stderr)
        return 3 if args.gate else 1

    print(json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True))

    if not args.gate:
        return 0
    return gate_exit_code(envelope["summary"], threshold=args.threshold)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
