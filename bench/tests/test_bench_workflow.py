"""Tests for .github/workflows/bench.yml: that a dispatch can actually reach a model.

This file exists because of a defect nothing else could see. `bench.yml` passed `--skills`, `--k`,
`--tiers` and `--dry-run`, and no `--out-dir`. `run_bench.py` defaults `--out-dir` to
`bench/results/runs`, which holds the committed measurement evidence, and the immutability guard
added in v0.1.4 refuses any directory that already holds envelopes. So a live dispatch exited 1
before its first model call.

Nothing caught it. `bench.yml` never runs on push or pull request by design, so CI never executed
the path. Both halves were correct in isolation: the guard is right to refuse that directory, and
the harness is right to default somewhere obvious. Only the combination was wrong, and the only
dispatch on record was a `--dry-run`, which returns before the guard and passed in 19 seconds.

The suite even held the knowledge already, in a comment in `test_run_bench.py`: "A fresh --out-dir,
because the default is the committed evidence directory and the immutability guard would
(correctly) refuse it." Nothing checked the workflow against it.

These are text assertions rather than a YAML parse on purpose: `pyyaml` is not a dependency of this
repository and adding one to assert a command line would cost more than it buys.
"""

from __future__ import annotations

import re
from pathlib import Path

import bench.run_bench as run_bench
from bench.run_bench import DEFAULT_OUT_DIR, _check_out_dir_is_not_committed_evidence

WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "bench.yml"


def _workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _harness_command() -> str:
    """The single `run:` line that invokes run_bench.py."""
    for line in _workflow_text().splitlines():
        if "run_bench.py" in line and line.strip().startswith("run:"):
            return line
    raise AssertionError("bench.yml has no `run:` line invoking run_bench.py")


# ---------------------------------------------------------------------------
# Why an --out-dir is mandatory, asserted against the harness rather than assumed
# ---------------------------------------------------------------------------


def test_the_harness_default_out_dir_would_be_refused_today() -> None:
    """The premise of every assertion below.

    If this ever stops holding, the harness default has moved and this file's reasoning needs
    revisiting rather than its assertions quietly passing for the wrong reason.
    """
    assert DEFAULT_OUT_DIR.name == "runs"
    refusal = _check_out_dir_is_not_committed_evidence(DEFAULT_OUT_DIR)
    assert refusal is not None, (
        f"{DEFAULT_OUT_DIR} no longer holds envelopes, so the harness default is no longer "
        "destructive and this test file's premise has changed"
    )
    assert "immutable measurement evidence" in refusal


# ---------------------------------------------------------------------------
# What the workflow must therefore do
# ---------------------------------------------------------------------------


def test_a_dispatch_passes_an_explicit_out_dir() -> None:
    """Without this, a live dispatch dies at the immutability guard before any model call."""
    assert "--out-dir" in _harness_command()


def test_the_workflow_exposes_an_out_dir_input() -> None:
    """A caller re-running one cell needs to name the directory; blank falls back to a fresh one."""
    text = _workflow_text()
    assert re.search(r"^\s{6}out_dir:\s*$", text, re.MULTILINE), "bench.yml declares no out_dir input"


def test_the_fallback_out_dir_is_unique_per_dispatch() -> None:
    """Two dispatches must not collide: the second would hit the guard against the first's output."""
    text = _workflow_text()
    assert "github.run_id" in text
    assert "runs-dispatch-" in text


def test_the_out_dir_stays_under_bench_results() -> None:
    """The publish step stages `bench/results` and nothing else, so envelopes written outside it
    would run to completion and then be silently discarded."""
    text = _workflow_text()
    assert "bench/results/runs-dispatch-" in text
    assert "git add bench/results" in text


def test_the_fallback_is_not_a_committed_run_set() -> None:
    """`runs` and `runs-cal1` are the two committed run sets; a dispatch must target neither."""
    command_and_env = _workflow_text()
    for committed in ("bench/results/runs'", "bench/results/runs\"", "bench/results/runs-cal1"):
        assert committed not in command_and_env, f"bench.yml would write into committed evidence: {committed}"


# ---------------------------------------------------------------------------
# The guard ordering that made this invisible
# ---------------------------------------------------------------------------


def test_results_are_published_even_when_the_run_partly_failed() -> None:
    """A partial failure is the case where publishing matters most, and it was the one case that
    published nothing.

    Measured 2026-08-17: a 40-cell dispatch produced 37 valid envelopes over 72 minutes of paid
    model time, three cells failed, the bench step exited non-zero, and this step was skipped as a
    consequence. Every one of those envelopes was discarded with the runner. A results branch is
    reviewed as a diff before anything is merged, so publishing a partial set costs nothing and
    losing it costs the whole run.
    """
    text = _workflow_text()
    publish = text.index("Publish results as a branch diff")
    condition = text[publish : publish + 400]
    assert "!cancelled()" in condition or "always()" in condition, (
        "the publish step is still conditioned only on dry_run, so a failed bench step discards "
        "every envelope the run paid for"
    )


def test_dry_run_still_needs_no_fresh_directory() -> None:
    """A dry run writes nothing, so it returns before the guard. That ordering is correct, and it
    is also why the one dispatch on record passed while the live path was broken. Asserted so a
    future reordering does not make dry runs need ceremony they have no reason to need."""
    source = Path(run_bench.__file__).read_text(encoding="utf-8")
    dry_run_return = source.index("if args.dry_run:")
    guard_call = source.index("out_dir_check = _check_out_dir_is_not_committed_evidence")
    assert dry_run_return < guard_call
