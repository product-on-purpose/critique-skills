# P3 provenance record

- Phase: P3 (bench measurement, results, ship/hold verdicts, and the floor, model-pin, and
  tier-backfill decisions)
- Branch: `build/v0.1.0`
- Date recorded: 2026-07-31
- Recorder: P3 provenance-record subagent (facts supplied by the orchestrating session that ran
  the measurement; not independently re-verified against external logs, since none exist in this
  repository)

## Purpose

[P3-report.md](P3-report.md)'s self-audit found that nothing committed to this repository explains
how the 462 envelope files under `bench/results/runs/` were actually produced: `bench/run_bench.py`
was, and remains, a stub that returns exit 1 for any live, non-dry-run dispatch with a real skill
selected, and no other committed code path calls a live model or `agents/critique-critic.md`
programmatically. That report named this the "Provenance gap" deviation and carried it into "Open
items for P4" as the first item: either build the harness and re-run the grid, or add an explicit,
prominent statement describing how the committed envelopes were actually produced.

This document is that statement. It is backward-looking: it records the mechanism that produced the
v0.1.0 measurement grid, as supplied by the orchestrating session that ran it, so a reader is not
left to infer the mechanism from the absence of harness code the way the P3 self-audit had to.

## What produced the grid

The v0.1.0 measurement grid was produced 2026-07-31 to 2026-08-01 by a Claude Code multi-agent
workflow, run ID `wf_217bbe66-cb0`. It was not produced by `bench/run_bench.py`. That script was a
stub at measurement time, and the P3 self-audit confirmed it remains one: it prints "the judged-lane
harness... is not built yet" and exits 1 whenever a real skill is selected outside `--dry-run`, and
no P3 commit touched it.

## Mechanism

One fresh clean-context subagent per run. 460 measurement runs total: 23 corpus artifacts times 2
model tiers times k=5 times 2 conditions (skill condition, baseline condition), plus 2 steering-test
runs (the `bench/results/runs/steering/clarity-001/` envelopes already described in
[P3-report.md](P3-report.md) and pinned outside the scored grid by
[ADR 0023 (v0.1.0 measurement basis: two pinned tiers, k=5)](../decisions/0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md)).

- **Skill-condition runners** operated under the `agents/critique-critic.md` definition: executed
  the skill's `scripts/checks.py` for the scripted lane, performed the judged lane per the four-pass
  protocol, merged the two lanes' findings, and bounded the result.
- **Baseline-condition runners** applied the frozen `bench/baseline/prompt.txt` and converted the
  raw model output into an envelope via the committed postprocess rule
  (`bench/baseline/postprocess.py`).

## Model routing

Tier aliases (`haiku`, `sonnet`) resolved to the pinned model IDs `claude-haiku-4-5-20251001` and
`claude-sonnet-5`, the same pair [ADR 0023](../decisions/0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md)
declares as the measurement basis. Each runner was told its assigned model ID directly and recorded
it verbatim in the envelope's `run.model` field; the alias-to-ID mapping was not left to runner
inference.

## Ground-truth isolation

Runners read artifacts only from a manifest-free staging copy, `bench/results/staging/`, deleted
after measurement completed. Runner prompts explicitly prohibited reading `bench/corpus/` manifests,
the corpus generator code, or the output of other runs. `bench/results/measurement-manifest.json`
already records the staging path and the per-artifact hashes proving the staged copies were
byte-identical to the corpus; it does not record the isolation instructions given to runners, which
is why that fact is recorded here instead.

## Interruption and resume

The first execution hit a session usage limit at 384 of 464 agents. The workflow resumed from its
own journal on 2026-08-01, re-running only the missing agents; the envelopes already written by the
first pass were left on disk untouched. Coverage after resume: 460 of 460 scored runs, zero gaps,
matching `bench/results/README.md`'s "Coverage gaps: 0" line and
[P3-report.md](P3-report.md)'s S05-AC5 verdict.

The 464 figure is stated here exactly as supplied by the orchestrating session. It is two more than
the 462 total envelopes this document otherwise describes (460 scored plus 2 steering). This
document does not resolve that two-agent difference; it is noted here rather than silently
reconciled.

## Limitation: not independently reproducible from the repository alone

This mechanism is documented, here and now, but it is not independently reproducible from the
repository alone. There is no committed harness invocation log, no committed code path that calls a
live model or `agents/critique-critic.md` programmatically, and no way for a reader who has only this
git history to re-run the exact orchestration that produced these 462 files.

`bench/run_bench.py`, committed in this phase, is the reproduction path for re-measurement going
forward, not a record of how the committed grid was produced. Its numbers may differ from the
agentic mechanism's: the two are not byte-equivalent, and nothing in this record or in
`bench/run_bench.py` guarantees they converge. A future run through `bench/run_bench.py` should be
treated as a new measurement, comparable to the P3 grid in shape but not assumed identical to it in
value, and given its own run-set identifier per the rule [ADR 0023](../decisions/0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md)
already sets for any change to the measurement basis.

## What this document is and is not

This is a provenance record, not a re-verification. Every fact in it was supplied by the
orchestrating session that ran the P3 measurement and is presented here as authoritative on that
session's own account; it was not checked against API billing records, execution logs, or any other
external evidence, because none of those exist in this repository. It closes the "how was this
produced" question that [P3-report.md](P3-report.md)'s audit left open. It does not, and cannot,
convert that answer into independently verifiable evidence the way a committed harness invocation
and its logs would.

## Cross-references

- [P3-report.md](P3-report.md): the self-audit that found the provenance gap this document closes
  ("Provenance gap" deviation; first "Open items for P4" bullet).
- [ADR 0023 (v0.1.0 measurement basis: two pinned tiers, k=5)](../decisions/0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md):
  the declared measurement basis (model IDs, k, corpus hash) this mechanism executed against.
- [`bench/results/measurement-manifest.json`](../../../bench/results/measurement-manifest.json): the
  machine-readable staging and hash record referenced under "Ground-truth isolation" above.
- [`bench/results/README.md`](../../../bench/results/README.md): carries a short cross-reference to
  this document in its provenance section.
- [S06-AC2 (critic subagent: envelope validates, no prose wrapper)](../release-plans/plan_v0.1.0/S-06_critic-subagent/spec.md):
  the acceptance criterion whose "validated in P3 by actual invocation" language this document's
  mechanism is meant to substantiate.
