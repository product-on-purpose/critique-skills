# 0041 - The merge step runs the scripted lane itself, and assigns lane from the declaration

## TL;DR
- **Decision:** `skills/_shared/merge.py` runs the skill's own `scripts/checks.py` itself and takes
  the scripted lane only from that output. A model finding's lane comes from `SKILL.md`'s
  `checks.scripted` / `checks.judged` declaration, never from the finding's own `lane` field. A
  finding on a scripted criterion is dropped, with the count reported on standard error. A finding
  on a criterion in neither list fails the merge, naming it, unless it is marked
  `rubric_source: byor`, which is filed `judged` whatever its namespace. A judged finding with no
  stated confidence defaults to `medium`, not `high`.
- **This is D1 through D3.** D4 through D6 are this decision's consequences: every skill's version
  moves once, together with E67's version move, in the release that carries both; the moved skills
  are measured by a free replay first and then one paid dispatch; five of the six E35 validator
  findings ride the same version move, and one (R1) waits for its own change.
- **The version moves and the paid re-measure (AC-9) are still to come.** Neither is built by this
  ADR, and both need the maintainer's own, separate approval before they happen.
- **Ruled:** by the maintainer on 2026-10-23. Built 2026-10-26.
- **Status:** Accepted (2026-10-26). Records the E73 ruling and build; the backlog entry and the
  spec track what AC-9 and the version moves still need.

- **Status:** Accepted
- **Date:** ruled 2026-10-23, built and recorded 2026-10-26
- **Deciders:** Jonathan Prisant (the ruling). Drafted by Claude from the E73 backlog entry, the
  reproduced defect, `skills/_shared/merge.py` as it stood on `main` at `5ed5a6a`, and ADR 0037's
  check 6.

## Builds on

- [E73 (merge step runs the scripted lane itself)](../backlog/enhancements.md), which this ADR
  records the ruling and build for, and
  [E73's spec](../release-plans/_unassigned/E73_merge-runs-scripted-lane/spec.md), which this ADR
  does not restate.
- [0027 - Accessibility location-emission calibration](0027-accessibility-location-emission-calibration.md),
  the precedent for moving a skill's version over a change that is mostly in `checks.py` or its
  assembly path rather than its rubric.
- [0037 - Critique-forms ship verdict](0037-critique-forms-ship-verdict.md), check 6, whose hand
  arithmetic first sized what a corrected merge step would have scored.
- [E67 (accessibility expansion)](../backlog/enhancements.md) and [E45 (BYOR on one flagship
  skill)](../backlog/enhancements.md), which this decision sequences against without building
  either.

## Context and problem statement

The scripted lane is the part of every verdict that needs no trust in a model: it is meant to be
reproducible from committed code alone. Before this change, the envelope's scripted lane was
whatever the model copied into its findings file. `skills/_shared/merge.py`'s `_to_raw`
(`main` at `5ed5a6a`, lines 138-169) defaulted a finding's lane to `"scripted"` when the finding
omitted it, and otherwise trusted whatever the model wrote.

Two measured symptoms follow from that one trust. In the `critique-forms` paid dispatch
`37091134037`, Sonnet dropped 11 scripted-lane claims in 6 of 20 runs, and Haiku labeled 10
judged-criterion findings `scripted` in 3 of 20 (ADR 0037, check 6). The second is the worse
failure: a mislabeled judgment was not only filed in the wrong lane, `_to_raw` then forced its
confidence to `high`, because a scripted finding must be high confidence
(methodology section 5). The envelope asserted a certainty no one held. The defect was reproduced
on `main` at `5ed5a6a` with no model call, using `skills/critique-forms/examples/artifacts/golden-02.html`:
a findings file with one script finding removed and two judged findings mislabeled (one
`"scripted"` at `"medium"`, one with no `lane` at all) produced an envelope in which the removed
finding vanished uncounted and both relabeled findings were recorded `scripted`, at `high`
confidence.

Every skill uses the same assembler, so every skill carried the same exposure. Three further
questions had no stated answer: what to do with a model's copy of a scripted criterion the script
did not itself emit, what to do with a criterion declared in neither `checks.scripted` nor
`checks.judged`, and what confidence a judged finding gets when it states none.

## Decision drivers

- **The scripted lane must be exactly `checks.py`'s own output.** Anything else breaks the
  reproducible-from-committed-code claim the lane exists to make.
- **No criterion sits in both lanes.** `scripts/skill-selftest.py` already enforces this for the
  declarations themselves (`lane-overlap`); the merge step's handling of a model's lane claim must
  not quietly reopen it.
- **An envelope never records more certainty than anyone expressed.** A scripted finding's `high`
  confidence is a fact about a deterministic check; forcing a judged finding to the same value
  states something false about a judgment call.
- **BYOR needs a path forward that an invented or mistyped ID cannot exploit.** E45 will bring
  user-supplied criteria that exist in no skill's declaration; the merge step's handling of an
  undeclared criterion has to leave room for that without accepting anything else silently.
- **Keep the fix to the merge step.** No `checks.py`, no contract field, and no bounding or ranking
  rule changes; the defect is in trust, not in what either lane measures.

## Considered options

Three decisions, ruled in one walk on 2026-10-23.

**D1. A model finding on a scripted criterion the script did not emit.**

1. **Drop the finding, and report the count on standard error, by criterion (chosen).** The
   envelope's scripted lane is then exactly the script's.
2. **Keep it, filed as `judged`.** Rejected: this is the `lane-overlap` rule, reopened at the merge
   step instead of at declaration time.
3. **Fail the merge.** Rejected: one stray finding would cost a whole run.

**D2. A model finding on a criterion in neither list.**

1. **File a finding marked `rubric_source: byor` as `judged`, whatever its namespace; reject the
   merge for any other undeclared ID, naming it (chosen).** Keying on `rubric_source` rather than a
   `BYOR-` prefix follows the contract, which lets a user rubric name its own namespace.
2. **File every undeclared finding as `judged`.** Rejected: measured on dispatch `31988100372`
   (2026-08-17), 4 of 19 Haiku `critique-clarity` envelopes named an undeclared, namespace-swapped
   ID such as `WILLIAMS-AUDIENCE`; this option would pass a typo through silently.
3. **Drop every undeclared finding, BYOR included, until E45 designs its own path.** Rejected: it
   would cost E45 a redesign for a path that already has an answer.

**D3. The default confidence of a judged finding that states none.**

1. **Default to `medium` (chosen).** The honest reading of "no confidence stated"; few findings
   reach it, because every `SKILL.md` already asks the model to state confidence.
2. **Keep `high`.** Rejected: the scripted default, which overstates a judgment once lane no
   longer comes from the model's own claim.
3. **Fail the merge.** Rejected: costs a whole run over one missing field.

The maintainer accepted the recommended option on each, answering "Ok" to all three.

## Decision outcome

**The scripted lane runs in-process.** `skills/_shared/merge.py`'s `run_script_checks` (line 326)
loads the skill's own `scripts/checks.py` as a module and calls its `check(artifact)`, the way
`skills/_shared/runner.py`'s `_run` already does for the standalone scripted-lane CLI. Every
finding it returns enters the pool as `scripted`, exactly as emitted; running `checks.py` as a
subprocess would not do, because its own output is already bounded, and a finding below severity 3
beyond the fifth would be lost before the merge could weigh it against the judged lane.

**A model finding's lane comes from the declaration, read once per run.** `read_lane_manifest`
(line 133) parses `checks.scripted` and `checks.judged` from the skill's `SKILL.md` frontmatter, in
the style `read_skill_version` already used for `metadata.version`: the frontmatter block only, and
only `checks:`'s own direct children, so a body line is never mistaken for the declaration.
`_route_model_findings` (line 252) then applies D1 through D3 to every finding in the model's
findings file:

- a criterion in `checks.scripted` is dropped; the dropped count, by criterion, is reported on
  standard error by the CLI (`main`, line 479) whenever it is non-zero;
- a criterion in `checks.judged`, or any criterion marked `rubric_source: byor`, is kept, filed
  `judged`, at its stated confidence or `medium` if it states none;
- any other criterion fails the merge outright, naming every such ID in one message rather than
  stopping at the first.

**Backward compatible with the old pass 4.** A findings file that still carries copies of the
script's own findings, as every `SKILL.md` asked for before this build, produces the same envelope
as one carrying the judged findings alone: every copy's criterion is in `checks.scripted`, so D1
drops it regardless of what else it claims.

**Pass 4 now says this.** Every registered skill's `SKILL.md`, `agents/critique-critic.md`'s
assembly step, and `docs/internal/skill-template.md`'s pass-4 template tell the model to write its
judged-lane findings only, and say that merge runs the scripted lane itself. Pass 2 still runs
`checks.py`, because seeing its output helps the inventory and keeps the model from duplicating it.

**Tests.** `skills/_shared/tests/test_merge_lanes.py`, parametrized over every skill
`library.json` registers, covers AC-1 through AC-7 with no model call, including a shared test that
every finding `check()` returns is listed in the merged envelope or counted in
`summary.suppressed_count`.

## Consequences

**Positive:** a scripted finding in any envelope is now provably `checks.py`'s own output, and a
judged finding's lane and confidence are the model's claim, not a claim the merge step laundered on
its behalf. The old pass 4's script-finding copies become harmless rather than load-bearing, so the
seven `SKILL.md` files, the critic and the template can say the same, simpler thing.

**Negative, and tracked separately (D4-D6):**

- **Every skill's envelope can now differ from before, even though no rubric changed.** A dropped
  script finding reappears, and a mislabeled judgment changes lane and confidence. D4 ruled that
  this moves every skill's version, and the critic's, by one patch release, in the release that
  carries E67 (accessibility expansion): `critique-accessibility` is already at 0.1.1 from ADR 0027
  and is expected to move again for E67's new criteria, and moving twice in one release was ruled
  out. **Not done here.** This ADR changes no
  `metadata.version`, no `library.json` entry, and no `checks.py` `skill_version=` argument.
  `scripts/gen-site.mjs` shows each skill only its active version's cells, and
  `bench/results/results.json` carries no post-move cells for six of the seven skills yet, so
  moving a version before that dispatch runs would blank those skills' published figures rather
  than show a result.
- **The moved skills need a re-measure.** `ROADMAP.md`'s rule ("Each skill is re-measured through
  the current harness when a release changes it") applies to all seven once D4's move lands. D5
  ruled a free replay over committed envelopes first, to size the change and give the paid run an
  expected result to check against, then one paid dispatch shared with E67's own re-measure.
  **Neither is built here.** AC-9 in E73's spec tracks both, and the paid dispatch needs the
  maintainer's own explicit go when it is drafted, same as any paid run.
- **Five of the six E35 validator findings ride this build; one does not.** D6 ruled that R2
  (critique-clarity's scope list), R3 (critique-microcopy's frontmatter order), R4 and V1 (the
  shared docs' citation path) and V2 (the critic's "pinned" wording) are wording or ordering fixes
  with no effect on what a skill reports, so they are **fixed in this build**:
  `docs/internal/execution/E35-validator-run.md` records each disposition. R1 (critique-docs's
  description naming no sibling skill) changes triggering, not reporting, and waits for a change
  measured by the trigger evals, not by the bench; it is **not fixed here**.

**Neutral:** no change to any `checks.py`, to the contract (the `lane` enum stays `scripted` and
`judged`), to bounding or ranking in `skills/_shared/envelope.py`, or to the bench harness or its
metrics, which read envelopes and keep reading the same shape.

## What this ADR does not decide

- The exact release the version moves land in, beyond "together with E67's own move"; that is
  E67's and the release plan's call once E67 is built.
- The paid re-measure dispatch itself, its run set name, or its approval; AC-9 in E73's spec tracks
  it, and it needs its own go when drafted.
- R1's fix (critique-docs's description) or the trigger-eval run that measures it.
- Whether merge should also check a BYOR finding's criterion ID against the rubric the user
  supplied at run time; D2's recommendation leaves that with E45 (BYOR on one flagship skill).
