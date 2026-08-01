"""CLI: validate every run envelope committed under bench/results/ against the critique contract.

This is the CI "schema" job's entry point (S-07 CI-pipeline spec): every run envelope under
bench/results/ must be a contract-valid document, reusing the same validator contract/validate.py's
own CLI wraps. See contract/README.md for what "contract-valid" means.

Per bench/README.md "Layout", the harness writes envelopes three to four levels below
bench/results/, not one:

    results/
      runs/<skill>/<artifact>/<run>.json           a skill's own condition
      runs/baseline/<domain>/<artifact>/<run>.json  the frozen baseline condition
      runs/<...>/<run>.json.raw.txt                 the baseline lane's raw model text, a
                                                     companion file, never a document to validate
      results.json                                  the computed numbers: a different, non-envelope
                                                      schema
      results.schema.json                           the schema *for* results.json, not a document
                                                      to validate

so discovery walks the whole tree under bench/results/runs/, not bench/results/ itself:
bench/results/ also holds measurement-manifest.json, results.json, and results.schema.json, none
of them envelopes, and a glob scoped no narrower than bench/results/ would misclassify
measurement-manifest.json as a failed envelope (it has none of run/findings/summary). Within
runs/, any `*.raw.txt` companion (the baseline lane's raw model text, not JSON at all) is excluded
explicitly, so a future glob change cannot silently start matching it
(docs/internal/execution/P3-report.md, "Known validator wiring gap", names the original
one-level-too-shallow glob as the reason 462 committed envelopes were invisible to this command).

bench/results/runs/ does not exist until a benchmark has actually been run (bench/run_bench.py,
the bench.yml dispatch entry point). Until then this command succeeds vacuously: there is nothing
to be wrong about a set of files with zero members.

Usage:
    python -m contract.validate_envelopes [--strict]

Exits 0 when every discovered file is contract-valid (or none exist yet). Exits 1 when any file
fails validation or is not readable JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from contract.validate import load_document, validate_document

RESULTS_DIR = Path(__file__).resolve().parent.parent / "bench" / "results"
RUNS_DIR = RESULTS_DIR / "runs"


def find_envelope_files(runs_root: Path) -> list[Path]:
    """Every envelope `*.json` file anywhere under `runs_root` (bench/results/runs/), sorted for
    deterministic output, excluding a stray `results.json` or `*.schema.json` should one ever
    land inside this subtree, and any `*.raw.txt` companion (which this glob would never match as
    `*.json` in the first place, but is excluded explicitly so a future glob change cannot
    silently start matching it). Empty list if `runs_root` does not exist, which is the normal
    state before any bench run has landed.
    """
    if not runs_root.is_dir():
        return []
    return sorted(
        p
        for p in runs_root.rglob("*.json")
        if p.is_file()
        and p.name != "results.json"
        and not p.name.endswith(".schema.json")
        and not p.name.endswith(".raw.txt")
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m contract.validate_envelopes",
        description="Validate every JSON file under bench/results/ against the critique contract.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote validator warnings (output bounding, producer-declared threshold) to errors.",
    )
    args = parser.parse_args(argv)

    files = find_envelope_files(RUNS_DIR)
    if not files:
        print(
            f"validate-envelopes: {RUNS_DIR} does not exist or is empty; "
            "nothing to validate yet (no bench run has landed)."
        )
        return 0

    failed = 0
    for path in files:
        try:
            doc = load_document(path)
        except OSError as exc:
            print(f"FAIL {path}: cannot read: {exc}", file=sys.stderr)
            failed += 1
            continue
        except json.JSONDecodeError as exc:
            print(f"FAIL {path}: not valid JSON: {exc}", file=sys.stderr)
            failed += 1
            continue

        result = validate_document(doc)
        if args.strict:
            result = result.with_strict()

        if not result.ok:
            for issue in result.errors:
                print(f"FAIL {path}: {issue}", file=sys.stderr)
            failed += 1
        else:
            for issue in result.warnings:
                print(f"warning {path}: {issue}", file=sys.stderr)
            print(f"ok   {path}")

    if failed:
        print(
            f"validate-envelopes: {failed} of {len(files)} file(s) failed contract validation.",
            file=sys.stderr,
        )
        return 1

    print(f"validate-envelopes: {len(files)} file(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
