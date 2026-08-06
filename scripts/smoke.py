#!/usr/bin/env python3
# what-it-is:   the does-it-actually-run check
# what-it-does: runs every skill's scripted lane on a real artifact from a bare checkout and asserts
#               the result matches what a user in that environment should get
# why:          every other CI job installs dependencies first, so nothing was testing what
#               /plugin install actually delivers; a fresh install crashed for exactly that reason
# used-by:      .github/workflows/ci.yml (the "smoke" job), and by hand: python scripts/smoke.py
"""Does this plugin run for someone who just installed it?

Every other check in this repository answers a different question. The
conformance gate asks whether the repository follows the family Standard. The
unit suites ask whether the code is correct. Both run after dependencies are
installed, in a working tree the author already has set up.

None of them asks the question a user asks first: *I ran `/plugin install`,
does it work?* That gap is not hypothetical. `contract/validate.py` imported
`jsonschema` at module load, `/plugin install` does not run `pip`, and the
result was a raw traceback on step 2 of every skill's protocol. 784 tests
passed and the gate was clean while that was true.

This script closes the gap by running each skill the way an agent does, and
asserting the outcome that environment is supposed to produce:

  --expect ready     dependencies present: every skill exits 0 and emits a
                     contract-shaped run envelope on stdout.
  --expect no-deps   dependencies absent: every skill exits non-zero, names
                     the exact install command, and prints no traceback.

Both are real user states, so both are asserted. Running only the first would
have missed the defect this script exists because of.

Stdlib only, on purpose: it has to run in the environment where the third-party
dependency is missing, so it cannot depend on one itself.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# One real artifact per skill, taken from that skill's own committed golden example so the smoke
# check exercises a case the skill is known to handle rather than a synthetic stub.
CASES: list[tuple[str, str]] = [
    ("critique-accessibility", "skills/critique-accessibility/examples/artifacts/golden-01.html"),
    ("critique-argument", "skills/critique-argument/examples/argument-golden-01-warrant-gap.md"),
    ("critique-clarity", "skills/critique-clarity/examples/clarity-golden-01-passive-and-nominalization.md"),
    ("critique-docs", "skills/critique-docs/examples/docs-golden-01-heading-and-nav.md"),
    ("critique-microcopy", "skills/critique-microcopy/examples/microcopy-golden-01-signup-checkout.md"),
    ("critique-usability", "skills/critique-usability/examples/artifacts/golden-01-settings.html"),
]

INSTALL_COMMAND = 'pip install "jsonschema>=4.20,<5"'
TRACEBACK_MARKER = "Traceback (most recent call last)"


def run_skill(skill: str, artifact: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, f"skills/{skill}/scripts/checks.py", artifact],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


def check_ready(skill: str, proc: subprocess.CompletedProcess[str]) -> list[str]:
    """With dependencies installed, a skill must produce a usable envelope."""
    problems = []
    if proc.returncode != 0:
        problems.append(f"exit {proc.returncode}, expected 0: {(proc.stderr or '').strip()[:200]}")
        return problems
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        problems.append(f"stdout is not JSON ({exc}); first 200 chars: {proc.stdout[:200]!r}")
        return problems
    # Shape only. contract/validate.py owns real validation; this asserts the script produced the
    # kind of thing a caller can act on, which is the user-facing claim being smoke-tested.
    for key in ("run", "findings", "summary"):
        if key not in envelope:
            problems.append(f"envelope has no {key!r} key")
    run = envelope.get("run") or {}
    if run.get("skill") != skill:
        problems.append(f"run.skill is {run.get('skill')!r}, expected {skill!r}")
    if not isinstance(envelope.get("findings"), list):
        problems.append("findings is not a list")
    return problems


def check_no_deps(skill: str, proc: subprocess.CompletedProcess[str]) -> list[str]:
    """Without dependencies, a skill must fail in a way the reader can act on."""
    combined = (proc.stdout or "") + (proc.stderr or "")
    problems = []
    if proc.returncode == 0:
        problems.append("exited 0 with the dependency missing; it cannot have validated anything")
    if INSTALL_COMMAND not in combined:
        problems.append(f"never named the remedy ({INSTALL_COMMAND}); output: {combined.strip()[:200]!r}")
    if TRACEBACK_MARKER in combined:
        problems.append("printed a traceback; a traceback is not an actionable error")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="smoke.py",
        description="Run every skill's scripted lane and assert the outcome for this environment.",
    )
    parser.add_argument(
        "--expect",
        choices=("ready", "no-deps"),
        default="ready",
        help="ready: dependencies installed, expect valid envelopes. "
        "no-deps: dependencies absent, expect an actionable error and no traceback.",
    )
    args = parser.parse_args(argv)
    checker = check_ready if args.expect == "ready" else check_no_deps

    print(f"smoke: {len(CASES)} skill(s), expecting '{args.expect}'\n")
    failures = 0
    for skill, artifact in CASES:
        if not (REPO_ROOT / artifact).is_file():
            print(f"  FAIL  {skill}: artifact missing: {artifact}")
            failures += 1
            continue
        problems = checker(skill, run_skill(skill, artifact))
        if problems:
            failures += 1
            print(f"  FAIL  {skill}")
            for p in problems:
                print(f"          {p}")
        else:
            print(f"  ok    {skill}")

    print()
    if failures:
        print(f"smoke: {failures} of {len(CASES)} skill(s) failed in the '{args.expect}' environment")
        return 1
    print(f"smoke: all {len(CASES)} skill(s) behaved correctly in the '{args.expect}' environment")
    return 0


if __name__ == "__main__":
    sys.exit(main())
