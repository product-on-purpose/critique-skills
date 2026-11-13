---
name: critique-revision-loop
description: "Runs the revision loop over one artifact: critique it with a critique-<domain> skill, record the person's accept, reject, or defer decisions, then either stop or pause with a revision brief of the accepted findings; on a second invocation with the revised artifact, re-critique it and compare the two runs. Stops when no finding at severity 3 or above remains, or after the third iteration. Never edits the artifact. Use when the user wants to iterate a document, interface, or piece of writing to convergence against a rubric, asks to re-review a revised draft against an earlier critique, or wants a revision brief to act on."
metadata:
  version: 0.1.0
  tier: convergent
  status: active
  agent-targets:
    - claude
# S5 checks every entry against the skills on disk. These seven are alternatives, not a sequence:
# a run critiques with exactly one of them, chosen for the artifact, and re-critiques with the same
# one. The order of the loop itself is in the body.
steps:
  - skill: critique-accessibility
  - skill: critique-argument
  - skill: critique-clarity
  - skill: critique-docs
  - skill: critique-forms
  - skill: critique-microcopy
  - skill: critique-usability
---

# critique-revision-loop

The revision loop, as an invokable workflow. It runs the five steps of
[ADR 0040 (the revision loop pauses with a revision brief)](../docs/internal/decisions/0040-revision-loop-pauses-with-a-revision-brief.md)
and stops by the bound in [methodology section 10](../docs/explanation/methodology.md).

**The loop takes two invocations.** The first critiques the artifact and, unless the loop stops,
pauses with a revision brief. A person, or a tool the person runs on their own authority, revises the
artifact. The second invocation hands the revised artifact back and the loop resumes. No step of this
workflow writes to the artifact. What a person builds on top of the brief is theirs, not the
library's: see [what the revision loop does and does not do](../docs/explanation/revision-loop-boundary.md).

`<plugin>` below is the directory the plugin is installed in. Run every command from the same
working directory, because relative paths are read from there: `run.artifact`, a log's
`envelope.path`, and the default brief location. Every command prints one JSON object.
Exit code 0 means the step ran, including a decision to stop. Exit code 3 means an input is not
contract-valid or two inputs disagree. Exit code 4 is a usage error.

## Steps

### First invocation

1. **Critique.** Run the one `critique-<domain>` skill that fits the artifact, listed in `steps:`
   above. It delegates to `critique-critic` and returns a contract-valid run envelope. Save it, for
   example as `memo.envelope.json`. Hands on: the envelope.
2. **Record dispositions.** The person decides accept, reject, or defer on each finding and records
   it in a disposition log ([how to record dispositions](../docs/how-to/dispositions.md)). On the
   first iteration the log may omit `iteration`, which means 1. Each finding gets at most one
   decision; a log that decides one finding twice is refused. Hands on: the log, for example
   `memo.dispositions.json`.
3. **Stop-check, and 4. pause with a brief.** One command does both:

   ```
   python3 <plugin>/skills/_shared/revision_loop.py brief --envelope memo.envelope.json --dispositions memo.dispositions.json
   ```

   The JSON's `decision` is one of four values:

   | Decision | Meaning | Brief written? |
   |---|---|---|
   | `stop-converged` | No finding at severity 3 or above remains. | No |
   | `stop-bound-reached` | Findings at severity 3 or above remain, and this was iteration 3. Disposition the rest as they stand; there is no fourth iteration. | No |
   | `stop-nothing-accepted` | Findings at severity 3 or above remain, and the person accepted none of the findings. There is nothing to revise. | No |
   | `continue` | Findings at severity 3 or above remain, and this was iteration 1 or 2. | Yes |

   On `continue`, the brief is written to `<artifact-stem>.revision-brief.json` beside the artifact,
   or to `--out`. It holds one item per accepted finding, `{finding_id, criterion, location, fix}`,
   copied from the envelope, and it validates as a contract 1.1.0 revision brief. The same envelope
   and log always produce the same bytes. The step refuses an `--out` that names the artifact, the
   envelope, or the log. A later iteration's brief replaces an earlier one at the default path, and
   its `iteration` field says which pass wrote it. When a later call stops the loop, it writes
   nothing and deletes nothing: if an earlier brief is still at that path, the JSON names it as
   `stale_brief`, so nothing acts on it by mistake. Hands on: the brief, to the person. **The loop
   pauses here.**

   `stop-check` alone answers the stop question without writing anything:
   `python3 <plugin>/skills/_shared/revision_loop.py stop-check --envelope memo.envelope.json --dispositions memo.dispositions.json`.

### Second invocation

5. **Resume, re-critique, and compare.** After the person revises the artifact:

   ```
   python3 <plugin>/skills/_shared/revision_loop.py resume --artifact memo.md --dispositions memo.dispositions.json
   ```

   The person passes the prior iteration's disposition log by path (N4 decision D2). The prior
   envelope is the log's `envelope.path`, or `--envelope` when the log does not record one. If both
   are given and name different files, the step fails and names both, rather than guessing. It also
   fails when the loop already stopped, when the prior pass accepted nothing, or when the artifact
   is byte-identical to the one the prior run critiqued. It does not require the revised artifact
   to keep its name, so its JSON reports `prior_artifact` beside `artifact` for the person to
   check. It also names the skill to run and the `iteration` the new disposition log must carry.

   Then run the same skill on the revised artifact, save its envelope, and compare the two runs:

   ```
   python3 <plugin>/skills/_shared/revision_loop.py compare --previous memo.envelope.json --current memo.v2.envelope.json
   ```

   Both envelopes must come from the same skill, record the same `run.artifact` path, and be
   different runs. The comparison reports, per criterion and per severity, the count in each run
   and the change.
   It never claims that a finding in one run is "the same" finding as one in the other, because a
   finding id is unique only within its own envelope. Then return to step 2 with the new envelope,
   writing the log with the `iteration` that `resume` reported.

## Exit criteria

The loop is complete when the stop-check returns any `stop-` decision. The loop never runs more
than three iterations. Whatever remains at the bound is dispositioned like any other finding, not
carried into a fourth round.

## What is checked, and where

Every step except the two critiques is deterministic and runs on committed fixtures with no model
call. `evals/critique-<domain>.revision-loop.eval.json` holds one eval set per chain edge in
`agents/_chain-permitted.yaml`, and `skills/_shared/tests/test_revision_loop_evals.py` executes
every case in the `unit-python` CI job.
