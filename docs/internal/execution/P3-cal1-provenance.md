# P3-cal1 provenance record

- Phase: P3-cal1 (the one pre-committed calibration iteration for `critique-accessibility`)
- Run set: `cal1-2026-08-01`, envelopes under `bench/results/runs-cal1/`
- Date recorded: 2026-08-05, in the v0.1.x verification pass, four days after the runs
- Recorder: a later session, working from committed artifacts plus one fact carried in the
  orchestrating session's own notes. **This record was not written by the session that ran the
  measurement**, which is the material difference between it and
  [P3-provenance.md](P3-provenance.md), and the reason for the "Not established" section below.

## Purpose

[P3-cal1-report.md](P3-cal1-report.md) section 4 and
[`bench/results/README.md`](../../../bench/results/README.md)'s Provenance section both state that
the 40 cal1 envelopes have no provenance record, and
[ADR 0028](../decisions/0028-post-calibration-verdict-accessibility-clears-ac-6.md) names that the
weakest link in its verdict. All three hand writing this record to a later session as an open item.

This is that record, written to the extent the evidence supports and no further. Where a fact could
not be established it is listed as not established rather than inferred, because a provenance record
that guesses is worse than one that is honest about its own gaps: the guess would be indistinguishable
from measurement to every later reader.

## What is established, from committed artifacts alone

Every figure below was recomputed from the 40 committed envelopes on 2026-08-05, not copied from a
prior document.

| Property | Value | How it was established |
|---|---|---|
| Envelope count | 40 | file count under `bench/results/runs-cal1/` |
| Skill | `critique-accessibility`, all 40 | `run.skill` |
| Skill version | `0.1.1`, all 40 | `run.skill_version` |
| Model tiers | `claude-haiku-4-5-20251001` (20), `claude-sonnet-5` (20) | `run.model` |
| Grid shape | 4 artifacts x 2 tiers x k=5 | `run.artifact` x `run.model`, 10 envelopes per artifact |
| Findings by lane | 130 scripted, 86 judged | `findings[].lane` |
| Corpus | accessibility domain only, 4 artifacts, byte-identical to `bench/corpus/` | `measurement-manifest.json` `calibration.cal1.verification` |
| Staging | `bench/results/staging-cal1/`, since deleted | `calibration.cal1.staging_dir` |

The grid shape, model pins, k, and skill version therefore match what
[ADR 0023](../decisions/0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md) declares as the
measurement basis, and match `calibration.cal1` in
[`measurement-manifest.json`](../../../bench/results/measurement-manifest.json). Nothing in the
committed evidence contradicts the report's account of what was measured.

## Mechanism, supplied rather than verified

The orchestrating session recorded that the calibration iteration ran as a Claude Code multi-agent
workflow, run ID `wf_b9052469-f8a`: a snapshot commit of the P4 integrity work, an opus diagnosis
pass, permitted-lever calibration bumping the skill to 0.1.1, then 40 fresh re-measurement runs and
a final verdict.

**That workflow ID is the only mechanism fact in this record, it comes from the orchestrating
session's notes rather than from anything in this repository, and it has not been independently
verified here.** It is recorded because a later reader tracing this run set should know the identifier
exists; it is not evidence of how any individual envelope was produced. P3-provenance.md carries the
same caveat for the p3 grid ("facts supplied by the orchestrating session that ran the measurement;
not independently re-verified against external logs, since none exist in this repository"), and the
same limitation applies here more strongly, because this record was written four days later by a
session that was not present.

What this does bound: the cal1 mechanism was the same class of mechanism as the p3 grid (Claude Code
workflow subagents), not `bench/run_bench.py`, which per P3-report.md's self-audit was still a stub
at p3 time and which `bench/results/README.md` already states is not byte-equivalent to the workflow
path.

## Anomalies in the committed envelopes

Three, measured on 2026-08-05. The first was known and is corrected here; the second and third are
recorded for the first time.

**1. Round-number timestamps (known, and the prior count was low).**
`bench/results/README.md` states "six of the 40 cal1 envelopes also carry round-number
`run.timestamp` values, four of them exactly `00:00:00Z`." Recounted: **four** envelopes carry
exactly `2026-07-31T00:00:00Z`, which matches, but **nine** envelopes carry a timestamp whose minute
and second are both round (`:00:00Z` or `:30:00Z`), across six distinct values. The prior figure of
six undercounts by three. Either way the conclusion is unchanged and unchanged in force: those
timestamps are not a record of when the runs happened.

**2. Ten envelopes predate the recorded calibration date (new).**
`calibration.cal1.date` is `2026-08-01`. Ten of the 40 envelopes carry a `run.timestamp` on
`2026-07-31`, ranging from `2026-07-31T00:00:00Z` to `2026-07-31T20:30:00Z`. The full range across
all 40 is `2026-07-31T00:00:00Z` to `2026-08-01T06:28:16Z`. This is consistent with anomaly 1 rather
than separate from it: if a timestamp is not a record of when a run happened, it can land on the
wrong day. It is recorded separately because a reader checking dates would otherwise find a
contradiction between the manifest and the envelopes with nothing explaining it.

**3. One envelope records the staging path rather than the corpus path (new).**
`bench/results/runs-cal1/critique-accessibility/accessibility-004/haiku-r1.json` records
`run.artifact` as `bench/results/staging-cal1/accessibility/accessibility-004.html`. The other 39
record a `bench/corpus/accessibility/*.html` path. The same envelope is also the only one whose
timestamp carries sub-second precision (`2026-08-01T06:06:19.078068Z`); the other 39 are
second-resolution. Both differences point the same way: this envelope was written by a different
code path, or at a different moment in the run, than its 39 siblings.

This does not change what was measured. The manifest records that the staged copies are
byte-identical to their corpus originals, and `accessibility-004` still has its full complement of
ten envelopes (five per tier), so no cell is missing or duplicated. It is a provenance
inconsistency, not a measurement one, and it is exactly the kind of detail a provenance record
exists to surface.

## Not established

Recorded plainly so no later reader mistakes this document for a complete account:

- **Which process wrote each envelope.** No per-run log, transcript, or harness output is committed
  for the cal1 run set. The workflow ID above is a session-supplied identifier, not a committed
  artifact, and nothing in this repository resolves it.
- **Why the timestamps are unreliable.** The mechanism that produced round-number and
  previous-day timestamps is not known. It is visible in the data and unexplained.
- **Why one envelope differs in artifact path and timestamp precision.** Recorded above as a fact;
  the cause is not established.
- **Whether the p3 and cal1 runs used an identical runner.** Both are believed to be Claude Code
  workflow subagents, but "the same class of mechanism" is not "the same mechanism," and nothing
  committed settles it. `bench/results/README.md` already bounds the damage from this two ways: the
  scripted lane supplies 13 of the 17 planted defects per pass and is byte-reproducible from
  committed code with no model at all, and the judged lane's detection rate is flat between the two
  skill versions, which is not the shape a harness change would typically produce. Neither argument
  closes the gap, and this record does not close it either.

## What would close it

A re-measurement through a committed harness, with its output committed alongside a log that names
the harness, its version, and the wall-clock window. That is the same thing
[`bench/results/README.md`](../../../bench/results/README.md) already says a live `bench.yml`
dispatch would establish going forward, and it is why that dispatch is carried as a v0.1.x item
rather than treated as optional polish.
