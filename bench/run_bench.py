"""CLI: the bench.yml workflow_dispatch entry point (S-07 CI-pipeline spec).

Runs the scripted and judged lanes for the given skills, k repeat count, and model tiers, and emits
run envelopes plus a results table (bench/README.md "Metrics", "Baseline comparison (next stage)").
The judged-lane runner itself is S-03 (bench-harness) and S-06 (critic subagent) scope; library.json
currently declares no skills, so every dispatch of this workflow today has nothing to run.

Live runs (the default) require ANTHROPIC_API_KEY. --dry-run validates inputs and the skill filter
without calling any model and without the secret (S-07 AC-3: "dry-run mode works without the
secret"). A live run with the secret present but no skills declared also does nothing, honestly,
rather than failing on a harness that has not shipped yet.

Usage:
    python bench/run_bench.py [--skills all] [--k 5] [--tiers ""] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBRARY_JSON = ROOT / "library.json"


def declared_skills() -> list[str]:
    """Skill names from library.json's components.skills, whatever shape each entry takes
    (a bare name, or an object carrying one). Returns [] if library.json is missing, unreadable,
    or declares none yet, which is this repo's actual state as of S-07."""
    try:
        data = json.loads(LIBRARY_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"bench: cannot read {LIBRARY_JSON}: {exc}", file=sys.stderr)
        return []
    skills = data.get("components", {}).get("skills", [])
    return [s.get("name", s) if isinstance(s, dict) else s for s in skills]


def resolve_filter(skills: list[str], raw_filter: str) -> list[str]:
    """`raw_filter` is "all" (or blank) for every declared skill, else a comma-separated allowlist."""
    if raw_filter in ("", "all"):
        return skills
    wanted = {s.strip() for s in raw_filter.split(",") if s.strip()}
    return [s for s in skills if s in wanted]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python bench/run_bench.py",
        description="Run the bench harness for one or more skills (bench.yml dispatch entry point).",
    )
    parser.add_argument("--skills", default="all", help='Comma-separated skill names, or "all" (default).')
    parser.add_argument("--k", type=int, default=5, help="Repeat count per skill per artifact (default 5).")
    parser.add_argument(
        "--tiers", default="", help="Comma-separated model tier list (blank = the two pinned tiers)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and wiring without calling any model; no secret required.",
    )
    args = parser.parse_args(argv)

    if args.k < 1:
        print("bench: --k must be at least 1", file=sys.stderr)
        return 2

    all_skills = declared_skills()
    selected = resolve_filter(all_skills, args.skills)

    print(f"bench: skills filter '{args.skills}' -> {len(selected)} of {len(all_skills)} declared skill(s)")
    print(f"bench: k={args.k}, tiers='{args.tiers or '(default pinned tiers)'}', dry_run={args.dry_run}")

    if not args.dry_run and not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "bench: ANTHROPIC_API_KEY is required for a live run (S-07 CI-pipeline spec, AC-3); "
            "set the secret, or pass --dry-run to validate wiring without it.",
            file=sys.stderr,
        )
        return 1

    if not selected:
        print("bench: no skills to run yet (library.json declares none); nothing to do.")
        return 0

    # Reachable once library.json declares a skill: the judged-lane runner (S-03/S-06) is not built
    # yet, so a real dispatch with a real skill selected is a signal this placeholder needs replacing,
    # not something to rubber-stamp as a silent pass.
    print(
        "bench: the judged-lane harness (S-03 bench-harness, S-06 critic subagent) is not built yet; "
        "this dispatch validated inputs and wiring only.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
