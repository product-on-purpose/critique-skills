# P3-cal1: accessibility calibration report

- Phase: P3-cal1 (the one pre-committed calibration iteration for `critique-accessibility`, taken
  under S-05 AC-6's iterate-or-halt-or-ship remedy for a core-skill release blocker)
- Branch: `build/v0.1.0`
- Date: 2026-08-01
- Author: P3-cal1 reporting pass (Claude)

## Purpose

This is the closing record of a single calibration episode: one core skill lost its baseline
comparison, was diagnosed, was changed inside a pre-committed lever list, was re-measured, and
either cleared the gate or did not. It exists so a reader does not have to reconstruct the episode
from three ADRs and a results file. It asserts nothing that
[0026](../decisions/0026-location-level-re-examination-of-baseline-gates.md),
[0027](../decisions/0027-accessibility-location-emission-calibration.md), and
[0028](../decisions/0028-post-calibration-verdict-accessibility-clears-ac-6.md) do not already
establish; it summarizes and cross-references them.

## 1. The failure that triggered calibration

The location-level re-examination of the S-05 AC-6 gate ([0026](../decisions/0026-location-level-re-examination-of-baseline-gates.md))
found `critique-accessibility` failing substantively on both pinned tiers and both metrics, the
only one of the three core skills to do so:

| Tier | Recall (location) | Baseline (location) | Precision (location) | Baseline (location) |
|---|---|---|---|---|
| haiku | 0.176 (15/85) | 0.376 (32/85) | 0.158 (15/95) | 0.258 (32/124) |
| sonnet | 0.306 (26/85) | 0.776 (66/85) | 0.202 (26/129) | 0.293 (66/225) |

The sonnet cell is the headline number: 0.306 recall against a baseline of 0.776, a 47-point gap,
on a skill whose detection was not in question. AC-6 names three remedies for a core-skill gate
failure: iterate once inside P3, halt with a handover diagnosis, or ship with the failure
published. [0026](../decisions/0026-location-level-re-examination-of-baseline-gates.md) recorded
the failure and escalated the choice rather than making it. The iterate branch was taken, under a
policy fixed before the diagnosis was read (see section 7).

## 2. Diagnosis

The diagnosis pass ran before any edit and ranked candidate mechanisms by how many of the 85
sonnet defect instances each explains ([0027](../decisions/0027-accessibility-location-emission-calibration.md)):

| Mechanism | Instances | Verdict |
|---|---|---|
| Scripted-lane location emission (`_loc` discards the element id) | 50 | dominant cause |
| Judged-lane location emission (class or prose instead of an id) | 8 | real, secondary |
| Greedy-assignment loss into the ancestor window | 5 | scoring artifact, self-correcting |
| Judged-lane true detection failure | 1 | negligible |
| Output bounding suppressing sub-threshold findings | 1 | ruled out quantitatively |
| Scripted-check detection bugs | 0 | none exist |

Two findings shaped everything that followed:

- **Detection was already correct.** A deterministic local run of `skills/critique-accessibility/scripts/checks.py`
  over the four corpus artifacts emits 7 findings on `accessibility-001` (7 planted defects), 6 on
  `accessibility-002` (6 planted), 0 on `accessibility-003` (4 planted defects, all judged-lane
  criteria, correctly out of the scripted lane's scope), and 0 on the clean `accessibility-004`.
  That is 13 of 13 scripted-lane-targeted defects named under the correct criterion, with zero
  false positives.
- **The defect was one helper naming a place, not a script finding a defect.** `_loc(node,
  descriptor)` at `skills/critique-accessibility/scripts/checks.py:673` returned `f"line {node.line},
  {descriptor}"` and never read `node.attrs['id']`, so a location string built from it named no
  node `bench/metrics/resolve_html.resolve` recognizes. 55 of 65 pooled sonnet scripted-lane claims
  (84.6 percent) and 54 of 65 haiku claims (83.1 percent) were unresolvable as a result. Only `#html`
  and `#body` resolved, by coincidence: those two planted element ids happen to equal the tag names
  the descriptor printed. Of the 50 sonnet scripted-target misses this mechanism explains, 29 carry
  the truth element id verbatim inside the finding's own `evidence` field; the information was in
  the envelope, in the wrong field. The model was not the problem at any point: all 65 scripted
  findings survived into the envelope, and the location string was byte-identical to `checks.py`
  output in 98.5 percent of sonnet findings and 89.2 percent of haiku findings.

Output bounding was ruled out quantitatively rather than assumed: across all 40 accessibility
envelopes, `suppressed_count` totaled 1 on sonnet and 0 on haiku, against `critique-clarity`
suppressing 42 findings on a corpus that plants more defects per artifact. Recall in this run set
tracked location resolvability, not bounding pressure.

## 3. Levers applied

The pre-committed permitted-lever list was: scripted-check bug fixes, location-emission wording,
severity-anchor wording, four-pass protocol emphasis, and measurement-parity fixes, with deleting
or weakening criteria, editing the corpus, and changing scoring to favor the skill forbidden
outright. Three levers were pulled, all inside that list:

1. **Scripted-check fix, location emission.** `_loc` now composes `<anchor>, <descriptor>, line
   <n>`, backed by two new helpers: `_element_anchor(node)` returns `#<id>` when the id matches the
   resolver's bare-token grammar, otherwise a double-quoted bounded CSS path built from tag names,
   the child combinator, and `:nth-of-type`. The line number moved to the end of the string as a
   documented human convenience, never the anchor. No detection predicate and no threshold changed.
2. **Location-emission wording, judged lane.** `SKILL.md` gained a "Naming a location" section
   stating the same anchor preference order for hand-written findings, and `references/WCAG.md`
   gained a three-line pointer to it.
3. **Four-pass protocol emphasis.** Pass 1 (Inventory) now records each element's `id` while
   mapping; Pass 2 (Criterion sweep) requires each judged criterion to be swept by element id, with
   the five criteria that most often went shallow named explicitly.

Two permitted levers were deliberately not pulled, and the reasons are recorded because a lever
left on the table is as much a compliance fact as one pulled:

- **Severity-anchor wording.** Not needed: only 1 finding across 40 envelopes was ever suppressed,
  so there was no under-rating pattern to correct, and rewriting anchors with no evidence of
  mis-rating would have been inflation dressed as calibration.
- **Measurement-parity fixes.** The baseline postprocess parity check came back true, so nothing
  under `bench/baseline/` was touched and no `.v2.json` parity envelope was produced.

No criterion was added, removed, re-scoped, or moved between lanes. No file under `bench/corpus/`,
`bench/metrics/`, `bench/baseline/`, `contract/`, or `bench/results/runs/` was modified. Five golden
examples were regenerated or hand-corrected to demonstrate the new rule rather than the old habit
(`golden-01` through `golden-04` from the current `checks.py`, byte-identical except for location
strings and `skill_version`; `golden-05` hand-corrected and verified to resolve). Skill version
moved to 0.1.1.

## 4. Re-measurement design

Run set `cal1-2026-08-01`, recorded in `bench/results/measurement-manifest.json` under
`calibration.cal1`:

- **40 fresh envelopes**, clean context per run: 4 accessibility corpus artifacts times 2 pinned
  model tiers times k=5, under `bench/results/runs-cal1/critique-accessibility/`.
- **Same corpus, byte-identical.** `python -m bench.generator verify --corpus bench/corpus`
  reported 53 files byte-identical; the four staged artifacts' sha256 values in the manifest match
  the corpus originals, and `git status` showed no modification under `bench/corpus/`.
- **Same two pinned model IDs** as the frozen p3 grid: `claude-haiku-4-5-20251001` and
  `claude-sonnet-5` (alias `haiku` / `sonnet`), per [0023](../decisions/0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md).
- **Same k=5**, both tiers, no cell below floor.
- **Skill version 0.1.1** on every envelope; the p3 grid's 0.1.0 envelopes were left untouched.
- **The p3 grid reproduces byte-identically.** Scoring the steering-excluded p3 grid with the
  committed CLI reproduces all 24 pre-calibration `results.json` entries exactly, field for field,
  confirming the half of the merged results file that was not supposed to change did not change.

The re-measurement's own provenance (the mechanism that produced the 40 cal1 envelopes, and six
envelopes' round-number timestamps) is not fully documented in this repository yet.
[0028](../decisions/0028-post-calibration-verdict-accessibility-clears-ac-6.md) names this the
weakest link in the verdict below and hands writing a `cal1` provenance record, to the standard of
[P3-provenance.md](P3-provenance.md), to the orchestrator as an open item. That gap is disclosed
here rather than closed by this report.

## 5. Pre-vs-post numbers

All figures from `bench/results/results.json`, distinguished by `skill_version`. Baseline figures
are the frozen, unmodified 2026-07-31 ones; no `.v2.json` parity envelopes exist anywhere in the
repository, and `bench/baseline/` was not touched.

| Cut | Tier | 0.1.0 (p3, pre) | 0.1.1 (cal1, post) | Baseline (frozen) |
|---|---|---|---|---|
| Recall (location) | haiku | 0.176 (15/85) | **0.988 (84/85)** | 0.376 (32/85) |
| Recall (location) | sonnet | 0.306 (26/85) | **0.965 (82/85)** | 0.776 (66/85) |
| Precision (location) | haiku | 0.158 (15/95) | **0.875 (84/96)** | 0.258 (32/124) |
| Precision (location) | sonnet | 0.202 (26/129) | **0.672 (82/122)** | 0.293 (66/225) |
| Recall (criterion) | haiku | 0.176 (15/85) | **0.976 (83/85)** | 0.000, by construction |
| Recall (criterion) | sonnet | 0.235 (20/85) | **0.965 (82/85)** | 0.000, by construction |
| Precision (criterion) | haiku | 0.158 (15/95) | **0.865 (83/96)** | 0.000, by construction |
| Precision (criterion) | sonnet | 0.155 (20/129) | **0.672 (82/122)** | 0.000, by construction |
| Consistency (overall) | haiku | 0.362 | **0.625** | 0.175 |
| Consistency (overall) | sonnet | 0.605 | **0.808** | 0.653 |
| Consistency (judged only, derived) | haiku | 0.090 | **0.286** | n/a |
| Consistency (judged only, derived) | sonnet | 0.449 | **0.736** | n/a |
| Clean-artifact findings per run | haiku | 1.000 | **0.600** | 5.000 |
| Clean-artifact findings per run | sonnet | 1.800 | **1.200** | 8.200 |
| Unresolvable claims | haiku | 71 of 95 | **3 of 96** | 66 of 124 |
| Unresolvable claims | sonnet | 65 of 129 | **0 of 122** | 8 of 225 |

The criterion-level pass remains worth nothing on its own: the baseline is pinned at 0.000 by
construction on that cut, so any nonzero skill score would have cleared it. The location-level cut
carries the verdict, and it moved from a 47-point sonnet recall deficit to the skill leading the
baseline on both metrics, both tiers.

**Robustness check.** Re-scored under [0026](../decisions/0026-location-level-re-examination-of-baseline-gates.md)'s
cut B, which credits a claim only when it resolves to the truth node itself, with no ancestor and
no descendant credit, and which is strictly harsher than any tolerance this repository defines,
0.1.1 reads 0.988 (haiku) and 0.965 (sonnet) recall, unchanged to three decimals from the committed
cut. Every 0.1.1 match is an exact-node match, so the win takes nothing from the ancestor window
[0026](../decisions/0026-location-level-re-examination-of-baseline-gates.md) flagged as flattering
high-volume emitters. The baseline, by contrast, falls to 0.212 (haiku) and 0.588 (sonnet) under
the same cut.

**Detection was flat, which is the point.** On `accessibility-003`, whose four planted defects are
all judged-lane criteria, the planted criteria were emitted at all (location ignored entirely) in
36 of 40 opportunities under 0.1.0 and 35 of 40 under 0.1.1. The skill did not start finding more
defects; it started saying where they were.

## 6. Final verdict

`critique-accessibility` 0.1.1 **passes S-05 AC-6 substantively, on both pinned tiers, literally
rather than by dominance argument**: higher location-level recall and higher location-level
precision than the frozen baseline on both haiku and sonnet
([0028](../decisions/0028-post-calibration-verdict-accessibility-clears-ac-6.md)). The core-skill
release blocker [0026](../decisions/0026-location-level-re-examination-of-baseline-gates.md)
escalated is discharged on evidence, not waived. The R1 consistency floor set in
[0022](../decisions/0022-consistency-floor-overall-lane-min-core.md) (0.309, overall lane) is
cleared on both tiers by a wider margin than 0.1.0 cleared it (0.625 and 0.808 against 0.362 and
0.605); the floor's own value does not move, since `critique-clarity` set it and `critique-clarity`
was not re-measured.

**No other verdict moved.** No baseline parity envelope was produced, so no baseline cell in any
domain changed and no comparison involving the other five skills was recomputed against a different
comparator. `critique-clarity` and `critique-usability` stand exactly as
[0026](../decisions/0026-location-level-re-examination-of-baseline-gates.md) left them. All three
stretch skills (`critique-docs`, `critique-microcopy`, `critique-argument`) stand as re-affirmed by
[0026](../decisions/0026-location-level-re-examination-of-baseline-gates.md); none was re-measured
and none of their numbers changed.

**What this does not establish**, published in full in `bench/results/README.md` and
[0028](../decisions/0028-post-calibration-verdict-accessibility-clears-ac-6.md):

- The comparison spans two run sets (`p3-2026-07-31` for the baseline, `cal1-2026-08-01` for
  0.1.1), not one simultaneous measurement. Corpus bytes, model IDs, and k are identical, so this
  is the intended comparison rather than a substitution, but the sonnet baseline cell is the figure
  a re-run could most plausibly move.
- The `cal1` run set has no provenance document yet (see section 4).
- The corpus is unusually friendly to the specific fix: every artifact carries ids on the elements
  its defects are planted on, so the id-anchor path is exercised far more than the CSS-path
  fallback that id-poor real markup would reach. How much of the gain survives on markup without
  ids is not measured by this run set.

## 7. Policy statement

The calibration policy was fixed before the diagnosis was read, not adjusted afterward to fit what
the diagnosis found: **one iteration, from a pre-committed permitted-lever list, with an ADR.** The
permitted levers were scripted-check bug fixes, location-emission wording, severity-anchor wording,
four-pass protocol emphasis, and measurement-parity fixes. Deleting or weakening criteria, editing
the corpus to make defects easier, and changing scoring to favor the skill were forbidden outright,
whether or not the iteration succeeded.

This was that iteration. It is spent. A second pass at `critique-accessibility`, for this or any
other gap, is a release-owner decision for a future build run, not something this build run's
policy authorizes on its own. Two of the permitted levers (severity-anchor wording,
measurement-parity fixes) were left unpulled because the diagnosis found no evidence they were
needed, not because the policy budget ran out first.

## Cross-references

- [0026 - Location-level re-examination of the baseline gates](../decisions/0026-location-level-re-examination-of-baseline-gates.md):
  the location-level rescore that surfaced the failure this report opens with, and the source of
  the twelve-cell gated table, the cut-B probe, and the escalated halt-or-iterate-or-ship choice.
- [0027 - critique-accessibility 0.1.1: the one permitted calibration is a location-emission fix](../decisions/0027-accessibility-location-emission-calibration.md):
  the diagnosis and the change, deliberately claiming no score.
- [0028 - Post-calibration verdict: critique-accessibility 0.1.1 clears AC-6 on re-measurement](../decisions/0028-post-calibration-verdict-accessibility-clears-ac-6.md):
  the measurement, the six verification checks run against it before it was accepted, and the three
  published limits.
- [`bench/results/results.json`](../../../bench/results/results.json): the 26 entries (24
  pre-calibration, byte-identical, plus 2 for 0.1.1) every number in section 5 is read from.
- [`bench/results/measurement-manifest.json`](../../../bench/results/measurement-manifest.json):
  the `calibration.cal1` block recording corpus hashes, staging path, models, and k for the
  re-measurement design in section 4.
- [`bench/results/verdicts.md`](../../../bench/results/verdicts.md): the dated "Post-calibration
  verdict (cal1, 2026-08-01)" section.
- [P3-report.md](P3-report.md) and [P3-provenance.md](P3-provenance.md): the phase self-audit and
  provenance record this report follows in form, for the p3-2026-07-31 grid that `cal1-2026-08-01`
  extends.
