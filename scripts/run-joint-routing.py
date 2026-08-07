#!/usr/bin/env python3
# what-it-is:   the scorer for evals/joint-routing.eval.json
# what-it-does: puts each fixture query to a pinned model with all six skill descriptions loaded,
#               records which skill it selects, and scores the answers against the fixture
# why:          six sibling skills in one namespace collide on triggering, and nothing else in this
#               repository measures whether the right one is actually selected
# used-by:      run by hand; not wired into CI, because it costs money and calls a live model
"""Score the joint-routing eval by asking a real model, with the real descriptions loaded.

Routing is a model decision over descriptions in context. This script makes
that decision observable: it loads this repository as a plugin with
``claude --plugin-dir``, so all six skill descriptions are in context exactly
as they would be for a user, then puts one query at a time and records which
skill comes back.

**Forced choice, on purpose.** An earlier prompt offered "or answer AMBIGUOUS
if no single skill is clearly right" and the model took that option for a case
it answers correctly without it. Real routing has no AMBIGUOUS option: a user
says something and a skill fires or does not. Offering the escape hatch
measures the model's willingness to hedge, not its routing. So the prompt asks
which skill it *would invoke*, and the ambiguous fixture cases are scored as
correct if the answer is any of their ``acceptable`` set, since under forced
choice every one of those is defensible.

**What this does not measure.** Whether the model would recognize an ambiguous
request and ask for clarification rather than guessing. That is a real and
separate question, it needs the AMBIGUOUS option to be offered, and it is not
answered here.

The model is pinned with --model and recorded in the output. A routing result
that does not say which model produced it is not reproducible.

Usage:
    python scripts/run-joint-routing.py --model sonnet
    python scripts/run-joint-routing.py --model haiku --out results-haiku.json
"""

from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "evals" / "joint-routing.eval.json"

SYSTEM = "Answer with bare data only. No preamble, no commentary, no insights, no markdown."

PROMPT = """A user says: "{query}"

Which ONE of the available critique-skills skills would you invoke? Reply with only the skill name."""


def ask(query: str, model: str, timeout: int) -> tuple[str | None, str]:
    """Return (parsed skill name or None, raw answer)."""
    proc = subprocess.run(
        [
            "claude",
            "--plugin-dir", str(REPO_ROOT),
            "--model", model,
            "--append-system-prompt", SYSTEM,
            "-p", PROMPT.format(query=query),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    raw = (proc.stdout or "").strip()
    # The model may answer "critique-clarity" or "critique-skills:critique-clarity"; normalize.
    for token in raw.replace(":", " ").replace(",", " ").split():
        cleaned = token.strip("`*.\"'").lower()
        if cleaned.startswith("critique-") and cleaned != "critique-skills":
            return cleaned, raw
    return None, raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run-joint-routing.py")
    parser.add_argument("--model", required=True, help="Model alias or full name, pinned and recorded.")
    parser.add_argument("--out", default=None, help="Where to write results (default: alongside the fixture).")
    parser.add_argument("--timeout", type=int, default=240, help="Per-query timeout in seconds.")
    parser.add_argument(
        "--k",
        type=int,
        default=3,
        help="Repeats per query. Routing is stochastic: the same query has returned different "
        "skills across runs, so k=1 is an anecdote. The modal answer is scored.",
    )
    args = parser.parse_args(argv)
    if args.k < 1:
        parser.error("--k must be 1 or greater")

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = fixture["cases"]
    out_path = Path(args.out) if args.out else REPO_ROOT / "evals" / f"joint-routing.results-{args.model}.json"

    results = []
    print(f"joint-routing: {len(cases)} case(s), model={args.model}\n", flush=True)
    for i, case in enumerate(cases, 1):
        query, kind = case["query"], case["kind"]
        expected = case.get("expected")
        acceptable = set(case.get("acceptable") or ([expected] if expected else []))
        trials: list[str | None] = []
        for _ in range(args.k):
            try:
                answer, raw = ask(query, args.model, args.timeout)
            except subprocess.TimeoutExpired:
                answer, raw = None, "<timeout>"
            trials.append(answer)
            if args.k > 1:
                time.sleep(1)

        counts = collections.Counter(t for t in trials if t)
        modal = counts.most_common(1)[0][0] if counts else None
        # Unanimity is reported separately from correctness: a query that lands on an acceptable
        # skill only sometimes is a weaker result than one that lands there every time, and the
        # score alone would hide the difference.
        unanimous = len(counts) == 1 and len(trials) == args.k
        correct = modal in acceptable if modal else False

        mark = "ok  " if correct else "MISS"
        if modal is None:
            mark = "ERR "
        spread = "" if unanimous else f"  (split: {dict(counts)})"
        print(f"  {mark} [{i:2d}/{len(cases)}] {kind:9s} -> {modal or '<none>'}{spread}", flush=True)
        if not correct and modal:
            print(f"         expected {sorted(acceptable)}", flush=True)

        results.append(
            {
                "query": query,
                "kind": kind,
                "expected": expected,
                "acceptable": sorted(acceptable),
                "answer": modal,
                "trials": trials,
                "unanimous": unanimous,
                "correct": correct,
            }
        )
        # Written every iteration so a timeout or interrupt does not lose the run.
        out_path.write_text(
            json.dumps(
                {
                    "eval": "joint-routing",
                    "fixture_version": fixture["version"],
                    "model": args.model,
                    "k": args.k,
                    "prompt_mode": "forced-choice",
                    "note": (
                        "Forced choice: no AMBIGUOUS option is offered, because real routing has none. "
                        "Ambiguous fixture cases are scored correct if the answer is any of their "
                        "acceptable set. Whether the model would ask for clarification instead of "
                        "guessing is a separate question this run does not measure. Each query is run k times and the MODAL answer is scored, because routing is stochastic; unanimity is reported per case so a shaky win is distinguishable from a solid one."
                    ),
                    "cases_run": len(results),
                    "cases_total": len(cases),
                    "results": results,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        time.sleep(1)

    by_kind: dict[str, list[bool]] = {}
    for r in results:
        by_kind.setdefault(r["kind"], []).append(r["correct"])
    total_ok = sum(r["correct"] for r in results)

    print(f"\njoint-routing ({args.model}): {total_ok}/{len(results)} correct")
    for kind in sorted(by_kind):
        hits = by_kind[kind]
        print(f"  {kind:9s} {sum(hits)}/{len(hits)}")
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
