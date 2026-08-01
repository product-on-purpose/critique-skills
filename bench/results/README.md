# P3 results: what the six skills actually measured

**Run set `p3-2026-07-31`. Measured 2026-07-31 on `claude-haiku-4-5-20251001` and `claude-sonnet-5`,
k=5, 460 run envelopes, corpus hash `602ff4cf391e50f70038a9119a8bfbc076fa2cc3b05fa9beba49f475e5880dd5`.
Coverage gaps: 0.**

The library's claim is that it publishes its own performance rather than asserting it. This file is
that publication for v0.1.0, and it leads with the numbers that do not flatter the library, because a
results page that buries them is an advertisement.

**Rescored (results version 1.1.0) to add location-level recall and precision**, computed from the
same 460 committed envelopes, no new runs: see
[unflattering number 1](#1-the-baseline-comparison-honestly-measured). Every number that was here
before this rescore is unchanged; the location-level figures are additions, not corrections.

**Both release gates were then re-read against those numbers** and the result is the single most
important thing on this page: **a core skill, `critique-accessibility`, loses to the unrubricked
baseline prompt on both tiers and on both metrics.** The three stretch skills hold.
[ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
records the ruling.

- Machine-readable numbers: [`results.json`](results.json)
- Stretch-skill ship/hold decisions: [`verdicts.md`](verdicts.md)
- Gate re-examination against the fair comparison:
  [ADR 0026 (location-level re-examination of the baseline gates)](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
- Measurement basis: [`measurement-manifest.json`](measurement-manifest.json) and
  [ADR 0023 (v0.1.0 measurement basis)](../../docs/internal/decisions/0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md)
- Consistency floor: [ADR 0022 (consistency floor: 0.309, overall lane)](../../docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md)
- Full generated tables, every skill and baseline row: [`../README.md`](../README.md)

---

## Read this first: the numbers that do not flatter the library

### 1. The baseline comparison, honestly measured

Every baseline row in every table used to read recall 0.000 and precision 0.000, in all six domains, on
both tiers. **That was not a measurement of the generic prompt. It was arithmetic**, and this rescore's
whole point is to stop mistaking one for the other.

`bench/metrics/match.py` matches a claim to a planted defect only when the claim's criterion string
equals the defect's criterion string. `bench/baseline/postprocess.py` assigns every baseline finding
the fixed criterion `BASELINE-GENERIC`, because a prompt with no rubric has nothing to cite. No
manifest in the corpus plants a defect under that criterion. The baseline's **criterion-level** recall
and precision could not have been anything but exactly zero, no matter what the model wrote. That
number is kept in `results.json` and quoted below, not deleted: it is a genuine finding about the
comparison, and it is worth keeping as a lesson in what a metric can be satisfied by construction rather
than by measurement, before it is used to gate anything again.

**Location-level recall and precision are the fair comparison**, computed by
`bench/metrics/score.py`'s `score_artifact_location` from the same 460 committed envelopes, no new
runs. A claim matches a planted defect when its location resolves, within the artifact type's
documented tolerance, to the defect's location, criterion ID ignored entirely. Both cuts sit side by
side in `results.json` for every row, skill and baseline alike: `recall`/`precision` (criterion-level,
primary for a skill, because it measures rubric operationalization, not just noticing) and
`recall_location`/`precision_location` (location-level, the number that is not pinned at zero by
construction). The full twelve-row comparison, both cuts, is generated into
[`../README.md`](../README.md); the cells that matter most are these five:

| Skill | Tier | Recall (location) | Baseline recall (location) | Precision (location) | Baseline precision (location) | Verdict |
|---|---|---|---|---|---|---|
| critique-accessibility | haiku | 0.176 | 0.376 | 0.158 | 0.258 | **below baseline, both metrics** |
| critique-accessibility | sonnet | 0.306 | 0.776 | 0.202 | 0.293 | **below baseline, both metrics** |
| critique-docs | haiku | 0.933 | 0.933 | 0.875 | 0.275 | **ties baseline on recall** |
| critique-docs | sonnet | 1.000 | 1.000 | 1.000 | 0.238 | **ties baseline on recall** |
| critique-usability | sonnet | 0.857 | 0.829 | 0.169 | 0.181 | wins recall, **below baseline on precision** |

**`critique-accessibility` loses to an unaccountable generic prompt at literally pointing near the right
defect, on both tiers, on both metrics.** Not "wins by less than the criterion-level number suggested."
Loses. Given no rubric and no domain framing, the generic prompt resolves a location within tolerance
of a planted WCAG defect more than twice as often as the skill does on sonnet, 0.776 against 0.306.
[Unflattering number 5](#5-worst-recall) below traces part of this to unresolvable locations, but the
location-level number says the problem is not only that unresolvable claims make the criterion-level
recall look worse than it is: crediting every correct-but-mislabeled finding, `critique-accessibility`
is still behind the prompt it is supposed to beat.

**`critique-docs`'s "beats baseline" win rests entirely on criterion labeling, not on finding the right
places.** At location level its recall exactly ties the baseline's, on both tiers: 0.933 against 0.933
on haiku (28 of 30 planted defects, both sides), 1.000 against 1.000 on sonnet. The generic prompt
resolves a location near every one of the same planted defects the skill does. What actually separates
them is precision: the skill emits 32 (haiku) or 30 (sonnet) claims in total and nearly all of them land
near a real defect (0.875, 1.000), while the baseline needs 102 or 126 claims to reach the same recall
(0.275, 0.238). On this evidence, `critique-docs`'s real advantage is emitting fewer, better-targeted
claims, not finding defects the baseline misses.

**Consequence for the AC-6 and AC-7 gates: one core skill fails the gate on the merits.**
[S-05 (skills slate)](../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) AC-6 and
AC-7 are written against the frozen methodology's own recall and precision definitions, which are
criterion-level, and every gated cell still reads a **formal** pass under that definition. That formal
pass is worth nothing on its own, because the comparison it is made against could not have failed. The
verdict-review pass of 2026-07-31 therefore re-read both gates against the location-level cut and ruled
([ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)):

- **`critique-accessibility` fails AC-6 substantively, on both tiers, on both metrics.** It is a core
  skill. AC-6's own remedy for a core skill that does not beat the baseline is that "the release halts
  with a handover diagnosis". The diagnosis is in [Core skills: S-05 AC-6](#core-skills-s-05-ac-6)
  below; the halt-or-iterate decision is escalated to the release owner and is not made here.
- **`critique-clarity` and `critique-usability` pass**, clarity by strict dominance on both tiers,
  usability on haiku only and with a caveat about what its comparator did on that tier.
- **All three stretch skills are re-affirmed SHIP** under AC-7, but `critique-docs` now ships on a
  precision-dominance argument at *equal* recall rather than on a recall win. Full reasoning per skill:
  [`verdicts.md`](verdicts.md#location-level-re-examination-2026-07-31).

The short version: "beats baseline", quoted without qualification, overstates what was measured in two
of the twelve gated cells, and in a third it conceals the opposite result.

The baseline comparison is also informative, criterion-level and location-level alike, on two metrics
that never routed through criterion matching in the first place:

| Comparison (like-for-like) | Baseline | Skills |
|---|---|---|
| Findings per run on a clean artifact | 5.000 to 10.000 | 0.000 to 9.400 |
| Unresolvable locations, worst cell | 107 of 137 claims (usability, haiku) | 71 of 95 claims (accessibility, haiku) |
| Consistency, worst cell | 0.032 (usability, haiku) | 0.309 (clarity, haiku) |

### 2. Cells where a skill is worse than the generic prompt

Nine cells now: four consistency cells, four location-level recall or precision cells, and one
clean-artifact cell. The consistency and location-level groups are not the same kind of comparison; see
the note under each.

**Consistency (not like-for-like).**

| Skill | Tier | Metric | Skill | Baseline | Gap |
|---|---|---|---|---|---|
| critique-clarity | haiku | Consistency | 0.309 | 0.463 | -0.154 |
| critique-clarity | sonnet | Consistency | 0.466 | 0.672 | -0.206 |
| critique-argument | haiku | Consistency | 0.371 | 0.600 | -0.229 |
| critique-accessibility | sonnet | Consistency | 0.605 | 0.653 | -0.048 |

This comparison is not like-for-like and the gap is smaller than it looks: every baseline finding
carries one criterion, so two baseline findings agree whenever their locations agree, while two skill
findings must agree on criterion **and** location. The skills are scored on a strictly harder predicate.

**Location-level recall and precision (like-for-like: identical tolerance rule, criterion ignored on
both sides).**

| Skill | Tier | Metric | Skill | Baseline | Gap |
|---|---|---|---|---|---|
| critique-accessibility | sonnet | Recall (location) | 0.306 | 0.776 | -0.470 |
| critique-accessibility | haiku | Recall (location) | 0.176 | 0.376 | -0.200 |
| critique-accessibility | haiku | Precision (location) | 0.158 | 0.258 | -0.100 |
| critique-accessibility | sonnet | Precision (location) | 0.202 | 0.293 | -0.091 |
| critique-usability | sonnet | Precision (location) | 0.169 | 0.181 | -0.012 |

Unlike the consistency comparison above, this one has no such excuse: both sides are scored by the
identical tolerance rule under the identical criterion-agnostic match. `critique-accessibility`'s gap on
sonnet, -0.470 on recall, is the largest gap in this file by a wide margin: the skill's location-level
recall is under 40 percent of the baseline's, on the domain's stronger tier.

**Clean-artifact cell.**

| Skill | Tier | Metric | Skill | Baseline | Gap |
|---|---|---|---|---|---|
| critique-usability | sonnet | Clean-artifact findings per run | 7.600 | 6.800 | +0.800 worse |

On an artifact with nothing planted in it, `critique-usability` on sonnet emits more findings per run
than the prompt that was given no rubric at all.

Two more cells are close enough to be worth naming: `critique-clarity` emits 8.600 findings per run on
a clean artifact against the baseline's 8.800 (haiku) and 9.400 against 10.000 (sonnet). On clean
prose, the clarity skill is barely quieter than an unaccountable generic prompt.

### 3. Lowest consistency

Floor-setting cell: **`critique-clarity` on haiku, 0.309 overall.** Roughly three in ten
`(criterion, location)` pairs survive between two runs of the same skill on the same artifact. That
number is the [R1](../../docs/internal/release-plans/plan_v0.1.0/plan_v0.1.0.md) stretch-gate floor,
set empirically because it is where the library actually is.

Restricted to the judged lane, which is the honest reading of the part that needs a model, it is worse:

| Cell | Consistency (overall) | Consistency (judged only) |
|---|---|---|
| critique-accessibility / haiku | 0.362 | **0.090** |
| critique-clarity / haiku | **0.309** | 0.150 |
| critique-usability / haiku | 0.378 | 0.304 |
| critique-argument / haiku | 0.371 | 0.320 |
| critique-clarity / sonnet | 0.466 | 0.418 |

**0.090** means that between two runs of `critique-accessibility` on haiku against the same HTML page,
about one judged finding in eleven repeats. The methodology's stated aspiration is 0.7. No core-skill
cell in this run set reaches it on either lane, on either tier. The best core cell is
`critique-usability` on sonnet at 0.642 overall.

### 4. Worst precision

Precision here is conservative by definition: a finding that is genuinely correct but was not planted
counts against it (see [Limitations](#limitations)). Even allowing for that, two skills are noisy.

| Cell | Precision (overall) | Precision (judged only) | Findings per run on the clean artifact |
|---|---|---|---|
| critique-accessibility / sonnet | **0.155** (20 of 129) | 0.156 | 1.800 |
| critique-accessibility / haiku | 0.158 (15 of 95) | 0.133 | 1.000 |
| critique-usability / sonnet | 0.169 (30 of 178) | **0.098** | 7.600 |
| critique-usability / haiku | 0.198 (24 of 121) | 0.101 | 4.400 |
| critique-clarity / sonnet | 0.376 (77 of 205) | 0.163 | 9.400 |
| critique-clarity / haiku | 0.382 (71 of 186) | 0.110 | 8.600 |

All three worst-precision skills are the three **core** skills. The three stretch skills score 0.470 to
1.000. The library's committed skills are its weakest measured skills.

### 5. Worst recall

**`critique-accessibility`: 0.176 on haiku, 0.235 on sonnet.** It finds under a quarter of the planted
WCAG defects. On the judged lane alone, 0.047 on haiku: 4 of 85 planted-defect opportunities.

The most likely proximate cause is visible in the same rows: **71 of its 95 claims on haiku, and 65 of
129 on sonnet, could not be resolved to a location at all.** An unresolvable finding cannot match a
planted defect even when it is substantively correct, so a large share of this skill's recall gap is a
location-emission problem rather than a detection problem. No other skill is close: clarity is at 18 of
186 and 1 of 205, usability at 4 of 121 and 0 of 178, and docs, microcopy, and argument are at or near
zero.

### 6. The one clean artifact per domain

Every clean-artifact false-positive rate in this file rests on a single artifact per domain, scored 5
times. Six clean artifacts across the whole corpus. Those numbers are directionally useful and
statistically thin.

---

## What was measured

**Six skills, three core and three stretch**, each against its own domain corpus, on two pinned tiers,
five runs per (skill, artifact, tier), plus the frozen `baseline-generic` prompt on the identical grid.

| Element | Value |
|---|---|
| Run set | `p3-2026-07-31`, measured 2026-07-31 |
| Tiers | `claude-haiku-4-5-20251001`, `claude-sonnet-5` |
| k | 5 runs per skill per artifact per tier, C(5,2)=10 pairwise comparisons per artifact |
| Corpus | 23 scored artifacts across 6 domains, generator 0.1.0, `toy` domain excluded |
| Planted defects | 73 across the corpus: accessibility 17, clarity 20, microcopy 15, argument 8, usability 7, docs 6 |
| Clean artifacts | 1 per domain, 6 total |
| Grid | 23 artifacts x 2 tiers x k=5 x 2 conditions = **460 envelopes** |
| Coverage achieved | **460 of 460. No cell below the k=4 floor. Zero quarantined.** |
| Contract validity | 462 of 462 files on disk validate against `contract/critique-contract.schema.json`, schema plus all 11 logical rules, zero warnings |
| Skill versions | all six at 0.1.0 |
| Contract version | 1.0.0 |

**Metrics**, defined in [methodology section 8](../../docs/explanation/methodology.md) and implemented
in `bench/metrics/`:

- **Recall:** planted defects matched by at least one finding, over planted defects, on seeded
  artifacts only, pooled across all k runs. Criterion-level: a match requires the finding's criterion
  string to equal the defect's, plus a location within tolerance. Primary for a skill, because it
  measures rubric operationalization.
- **Precision:** findings matched to a planted defect, over all findings emitted, including on clean
  artifacts. Same criterion-level match as recall.
- **Recall (location) and precision (location):** the same two definitions with the criterion-equality
  requirement dropped, a location within tolerance is the whole match
  (`bench/metrics/score.py`, `score_artifact_location`). Added in this rescore, computed from the same
  envelopes, no new runs. This is the fair comparison against `baseline-generic`, whose findings all
  carry the fixed criterion `BASELINE-GENERIC` and can never satisfy the criterion-level match; see
  [unflattering number 1](#1-the-baseline-comparison-honestly-measured).
- **Consistency:** mean pairwise Jaccard over `(criterion, location)` pairs across the k runs of one
  artifact, then the equal-weight mean across the domain's artifacts. Published twice: tolerance-aware
  (`consistency`) and exact-location (`consistency_exact`). The gap between the two is the skill's
  location-phrasing instability.
- **Clean-artifact false-positive rate:** findings per run on artifacts with nothing planted.
- **Unresolvable locations:** claims whose location string could not be anchored in the artifact.

**Excluded from the grid:** the two envelopes under `bench/results/runs/steering/`, a
prompt-injection-resistance probe carrying the
[ADR 0014 (stripped-context run field)](../../docs/internal/decisions/0014-stripped-context-run-field.md)
`run.stripped_context` field. They are contract-valid and remain on disk. Including them inflates
`critique-clarity` on sonnet from 20 scored runs to 22 and from 40 consistency pairs to 51.

## The numbers

Overall lane (every finding), from [`results.json`](results.json). Full tables including every baseline
row are generated into [`../README.md`](../README.md).

| Skill | Tier | Recall | Precision | Consistency | Consistency (exact) | Clean FP/run | Unresolvable |
|---|---|---|---|---|---|---|---|
| critique-clarity (core) | haiku | 0.710 | 0.382 | 0.309 | 0.263 | 8.600 | 18 of 186 |
| critique-clarity (core) | sonnet | 0.770 | 0.376 | 0.466 | 0.415 | 9.400 | 1 of 205 |
| critique-accessibility (core) | haiku | 0.176 | 0.158 | 0.362 | 0.351 | 1.000 | 71 of 95 |
| critique-accessibility (core) | sonnet | 0.235 | 0.155 | 0.605 | 0.438 | 1.800 | 65 of 129 |
| critique-usability (core) | haiku | 0.686 | 0.198 | 0.378 | 0.373 | 4.400 | 4 of 121 |
| critique-usability (core) | sonnet | 0.857 | 0.169 | 0.642 | 0.653 | 7.600 | 0 of 178 |
| critique-docs (stretch) | haiku | 0.933 | 0.875 | 0.842 | 0.675 | 0.000 | 3 of 32 |
| critique-docs (stretch) | sonnet | 1.000 | 1.000 | 1.000 | 0.933 | 0.000 | 0 of 30 |
| critique-microcopy (stretch) | haiku | 0.840 | 0.759 | 0.768 | 0.768 | 0.000 | 0 of 83 |
| critique-microcopy (stretch) | sonnet | 0.920 | 0.873 | 0.853 | 0.853 | 0.200 | 0 of 79 |
| critique-argument (stretch) | haiku | 0.775 | 0.544 | 0.371 | 0.286 | 1.200 | 0 of 57 |
| critique-argument (stretch) | sonnet | 0.775 | 0.470 | 0.737 | 0.463 | 2.600 | 0 of 66 |

Judged lane only. **Derived cut, not carried in `results.json`** (see
[Judged-lane figures](#judged-lane-figures-are-derived)). This is the instrument reading for the part
of each skill that needs a model; the scripted lane is deterministic and sits at or near 1.000
consistency everywhere it exists.

| Skill | Tier | Recall (judged) | Precision (judged) | Consistency (judged) | Consistency (scripted) |
|---|---|---|---|---|---|
| critique-clarity | haiku | 0.130 | 0.110 | 0.150 | 0.768 |
| critique-clarity | sonnet | 0.230 | 0.163 | 0.418 | 0.768 |
| critique-accessibility | haiku | 0.047 | 0.133 | 0.090 | 0.881 |
| critique-accessibility | sonnet | 0.118 | 0.156 | 0.449 | 0.971 |
| critique-usability | haiku | 0.286 | 0.101 | 0.304 | 0.900 |
| critique-usability | sonnet | 0.429 | 0.098 | 0.597 | 1.000 |
| critique-docs | haiku | 0.433 | 0.765 | 0.775 | 1.000 |
| critique-docs | sonnet | 0.500 | 1.000 | 1.000 | 1.000 |
| critique-microcopy | haiku | 0.373 | 0.583 | 0.623 | 1.000 |
| critique-microcopy | sonnet | 0.453 | 0.773 | 0.846 | 1.000 |
| critique-argument | haiku | 0.525 | 0.447 | 0.320 | 1.000 |
| critique-argument | sonnet | 0.525 | 0.375 | 0.724 | 1.000 |

**Four scripted-lane figures are below 1.000 and should not be:** `critique-clarity` 0.768 on both
tiers, `critique-usability` 0.900 on haiku, `critique-accessibility` 0.881 on haiku and 0.971 on
sonnet. A lane whose entire promise is bit-for-bit reproducibility should score 1.000 on every artifact
and every pair. Under 1.000 means either the lane is not as deterministic as claimed, or its findings
are reaching the envelope with location phrasing that varies between runs, which the tolerant Jaccard
should mostly absorb but does not fully. Both possibilities are owner questions, and this is the
cheapest lead in the run set to chase: it is a code-level defect, not a calibration judgment.

## The two gates

### Core skills: S-05 AC-6

**All three core skills pass as the criterion is written, the pass is worth nothing, and on the fair
comparison one of the three fails.** See
[unflattering number 1](#1-the-baseline-comparison-honestly-measured): at criterion level the baseline
scores zero by construction, so any nonzero recall clears the bar and every core skill clears it. At
location level, where the baseline is a real comparator, `critique-accessibility` reads below it on
both tiers and on both metrics.

Location-level cells are the substantive reading. A skill passes there by meeting AC-6 literally
(higher recall at equal-or-better precision) or by dominance (no worse on either metric, strictly
better on one). Nothing else counts.

| Core skill | Tier | Recall | Baseline recall | Recall (location) | Baseline recall (location) | Precision (location) | Baseline precision (location) | AC-6 as written | AC-6 on the merits |
|---|---|---|---|---|---|---|---|---|---|
| critique-clarity | haiku | 0.710 | 0.000 | 0.780 | 0.540 | 0.419 | 0.329 | pass | **pass**, dominates |
| critique-clarity | sonnet | 0.770 | 0.000 | 0.890 | 0.880 | 0.434 | 0.335 | pass | **pass**, dominates (recall +0.010) |
| critique-accessibility | haiku | 0.176 | 0.000 | 0.176 | 0.376 | 0.158 | 0.258 | pass | **FAIL**, below on both |
| critique-accessibility | sonnet | 0.235 | 0.000 | 0.306 | 0.776 | 0.202 | 0.293 | pass | **FAIL**, below on both |
| critique-usability | haiku | 0.686 | 0.000 | 0.800 | 0.000 | 0.231 | 0.000 | pass | **pass**, dominates |
| critique-usability | sonnet | 0.857 | 0.000 | 0.857 | 0.829 | 0.169 | 0.181 | pass | no pass on this tier (recall +0.028, precision -0.012) |

**The ruling** ([ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)):

- **`critique-clarity` passes** on both tiers by strict dominance. The sonnet recall margin is +0.010,
  which is one defect instance out of a hundred, so the haiku cell (+0.240 recall, +0.090 precision) is
  what carries it.
- **`critique-usability` passes on haiku only**, and the tier it passes on is the tier where its
  comparator collapsed: `baseline-generic` on haiku left 107 of its 137 usability claims unresolvable,
  and of the 30 that did resolve, **none** landed within tolerance of any of the 7 planted defects. A
  win over a comparator that scored zero is a real pass under the rule as written, and it is a weak one
  to quote. On sonnet, where the baseline works, the skill wins recall by one defect instance and loses
  precision by 0.012, which is not a pass on either reading. A robustness check that is worth knowing:
  under a deliberately harsher match (exact truth node only, no ancestor or descendant credit, a
  diagnostic cut and not a published metric, recipe in
  [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md))
  usability's sonnet cell dominates as well, 0.686 recall against 0.514 and 0.135 precision against
  0.113. Its sonnet precision deficit under the published tolerance is an ancestor-window effect that
  favours the high-volume emitter.
- **`critique-accessibility` fails, on both tiers, on both metrics, and the failure survives every
  adversarial re-cut available from these envelopes.** On sonnet the baseline resolves a location within
  tolerance of a planted WCAG defect more than twice as often as the skill does, 0.776 against 0.306,
  and does it at higher precision, 0.293 against 0.202. Under the harsher exact-node cut the gap
  narrows but does not reverse: baseline recall 0.212 against the skill's 0.176 on haiku, and 0.588
  against 0.224 on sonnet. There is no cut of this run set in which this skill beats the prompt it is
  supposed to beat.

**Consequence.** [S-05](../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)'s
Requirements section makes a core skill failing to beat baseline "a release blocker for core", and AC-6
names the remedy: iterate within P3, or halt with a handover diagnosis. The diagnosis is below. **The
choice between halting, iterating, and shipping with this published as measured belongs to the release
owner and is not made in this file.** Nothing about `critique-accessibility` has been changed or
de-listed on the strength of this reading: the spec is frozen, and de-listing a core skill is not a
measurement decision.

The likeliest calibration levers for all three core skills are named here so that decision is an
informed one. **Nothing has been changed. These are diagnoses, not fixes.**

- **`critique-accessibility`, recall 0.176 and 0.235, and below the baseline at location level on both
  tiers (0.176 against 0.376, 0.306 against 0.776).** Most likely lever: **bounding and location
  grammar, before anchors.** 75 percent of its haiku claims and 50 percent of its sonnet claims are
  unresolvable, against 10 percent or less for every other skill. Findings that cannot be anchored
  cannot match, so the recall number is partly measuring location emission rather than detection. The
  skill is emitting locations in a form the HTML resolver cannot bind, and the fix lives in the
  location grammar's reserved selector form
  ([ADR 0012 (location grammar: free text plus reserved selector)](../../docs/internal/decisions/0012-location-grammar-freetext-plus-reserved-selector.md))
  and in the protocol's instruction about how to cite an element. This is not only a criterion-labeling
  gap: the location-level number shows that even crediting every correct-but-mislabeled finding, the
  skill still resolves fewer usable locations than an unrubricked prompt does. Secondary lever: anchor
  wording on the judged WCAG subset, where judged recall is 0.047 on haiku and judged consistency is
  0.090, the worst pair of numbers in the run set.
- **`critique-usability`, precision 0.169 to 0.198 with 4.400 to 7.600 findings per run on a clean
  artifact.** Most likely lever: **severity anchor wording, to make the existing output bound bite.**
  Methodology section 7 bounds output at every severity 3 and 4 finding plus at most five below that,
  which only constrains anything if speculative heuristic hits are actually being rated 1 or 2. The
  volume pattern says they are not. Tightening the severity-2 and severity-3 anchors in
  `references/severity-anchors.md` downward is a smaller change than re-cutting the criteria and would
  route speculative findings into the bounded tail. Watch the interaction with
  [ADR 0021 (usability lane split)](../../docs/internal/decisions/0021-usability-lane-split-structural-floor-plus-judged-criterion.md)'s
  de-duplication rule: duplicate `(criterion, location)` pairs within one run were flagged there as the
  predicted failure mode of the scripted/judged sibling split, and 178 claims in one sonnet cell is
  consistent with it.
- **`critique-clarity`, consistency 0.309 (the floor-setting cell) and judged recall 0.130.** Most
  likely lever: **protocol emphasis on the fixed-ID criterion sweep.** Recall is healthy at 0.710 and
  0.770 overall but collapses to 0.130 and 0.230 on the judged lane, and judged consistency is 0.150 on
  haiku: the scripted lane is carrying this skill and the judged criteria (audience fit, cohesion) are
  drifting run to run. That is the signature methodology section 7's pass-2 fixed ordering exists to
  suppress. Also worth checking before anything else: the scripted lane measures 0.768 consistency, not
  1.000, which should not happen at all.

### Stretch skills: S-05 AC-7 and the R1 floor

**Floor: 0.309**, the minimum core-skill overall-lane consistency, per
[ADR 0022](../../docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md). All three
stretch skills ship, and all three were re-examined against the location-level cut on 2026-07-31 and
re-affirmed. Full reasoning and the per-skill numbers are in
[`verdicts.md`](verdicts.md#location-level-re-examination-2026-07-31).

| Skill | Baseline win (criterion) | Baseline win (location) | Consistency vs 0.309 | Verdict |
|---|---|---|---|---|
| critique-docs | yes, both tiers | **ties on recall, both tiers** (0.933/0.933 haiku, 1.000/1.000 sonnet); wins on precision | 0.842 haiku, 1.000 sonnet | **SHIP**, on precision dominance at equal recall |
| critique-microcopy | yes, both tiers | yes, both tiers, both metrics | 0.768 haiku, 0.853 sonnet | **SHIP** |
| critique-argument | yes, both tiers | yes, both tiers, both metrics | 0.371 haiku (+0.062), 0.737 sonnet | **SHIP**, thinnest margin in the slate |

`critique-docs` is the one stretch skill whose "baseline win" changes character at location level: see
[unflattering number 1](#1-the-baseline-comparison-honestly-measured) for the numbers and what they
say about where its advantage actually comes from. Its verdict is re-affirmed, but on a different
argument than the one originally recorded: at equal recall it emits 32 claims where the baseline needs
102, and 30 where the baseline needs 126, so it ships as a precision result, not a detection result.
No stretch verdict flipped, so `library.json` `components.skills` is unchanged and `plugin.json` was
not regenerated.

## Provenance

**The 462 envelope files under `bench/results/runs/` were produced by a documented Claude Code
multi-agent workflow, not by `bench/run_bench.py`.** `bench/run_bench.py`, committed in this phase,
is the reproduction path for re-measurement going forward, not the mechanism that produced the
numbers published in this file; the two mechanisms are not byte-equivalent, and a re-run through
`bench/run_bench.py` should be expected to differ from the figures published here. Full mechanism
record, including model routing, ground-truth isolation, and the mid-run interruption and resume:
[`docs/internal/execution/P3-provenance.md`](../../docs/internal/execution/P3-provenance.md).

## Limitations

Stated so no reader has to infer them from an absence.

- **The corpus is generated, not collected.** 23 artifacts produced by a deterministic seeded generator
  with agent-authored domain plugins. Every number here measures whether a skill finds defects **of a
  known kind, planted deliberately, in text of a known shape**. It does not measure performance on real
  documents, and it cannot measure whether the rubric is the right rubric. A generated corpus also
  risks a family resemblance between how a defect was planted and how the skill was told to look for
  it; that resemblance is unquantified.
- **Precision is conservative and is a lower bound.** A finding that is genuinely correct but was not
  planted is scored as a miss. Unplanted genuine findings are counted against precision and not
  adjudicated. The true precision of every skill is higher than the number published here by an unknown
  amount, and by more for the noisy skills than for the quiet ones.
- **The criterion-level baseline comparison cannot discriminate** (see
  [unflattering number 1](#1-the-baseline-comparison-honestly-measured)). Recall and precision against
  the baseline are pinned at zero by the criterion-matching rule; this is the reason the location-level
  cut exists. Location-level scoring answers the discrimination problem, not the deeper one:
  `bench/metrics/score_artifact_location` still requires a location, resolved by the same per-artifact
  tolerance the criterion-level metric uses, so it does not measure whether a finding's stated reasoning
  is any good, only whether it landed somewhere real.
- **Location-level recall and precision are new to this run set and unaudited against the same review
  the criterion-level numbers had.** They are computed by the identical scoring pipeline
  (`bench/metrics/`) from the same 460 committed envelopes, no new runs, and unit-tested
  (`bench/metrics/tests/test_score_location.py`), but they have not yet been through a P3-style
  self-audit of their own.
- **On `html`, location-level scoring rewards naming a container.** The
  [ADR 0015](../../docs/internal/decisions/0015-location-tolerance-per-artifact-type.md) tolerance
  credits a claim that resolves to an ancestor of the truth node at distance 1 or 2, so an emitter that
  points at enclosing elements collects credit that a precise emitter does not need. Measured on this
  run set, that window supplies 14 of `baseline-generic`'s 32 haiku accessibility matches and 16 of its
  66 sonnet matches, against 0 of 15 and 7 of 26 for `critique-accessibility`, and it is the whole of
  `baseline-generic`'s sonnet precision edge over `critique-usability`. The window is symmetric by
  construction and applies identically to both conditions; it nonetheless flatters volume, and every
  `html` location-level figure on this page should be read with that in mind. It does not reverse any
  verdict: see
  [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md).
- **Six clean artifacts, one per domain.** Every clean-artifact false-positive figure rests on a single
  artifact scored five times.
- **Small defect counts in three domains.** docs 6 planted defects, usability 7, argument 8. A recall of
  1.000 on docs/sonnet means 6 defect types found in all 5 runs, not 30 independent successes.
- **Severity agreement is not scored.** `severity_expected` is recorded in every manifest and read by
  nothing in v0.1.
- **Evidence quality is not scored.** Whether `evidence` quotes the artifact rather than characterizing
  it is a contract field obligation no metric checks.
- **Two tiers, one model family, one date.** Nothing here says how these skills behave on a frontier
  model, on a non-Anthropic model, or after either pinned tier changes behavior. These numbers decay.
- **k=5 carries real sampling noise.** `critique-argument` on haiku clears the stretch floor by 0.062,
  a margin a different set of five runs could plausibly move either way.
- **No human acceptance data.** The acceptance-rate measure in methodology section 8 requires
  disposition logs from real use, which v0.1.0 does not have.
- **Coverage gaps: none.** 460 of 460 cells filled, every artifact at k=5, zero envelopes quarantined
  for invalidity. This is the one place the run set has nothing to disclose.

## Judged-lane figures are derived

[`results.json`](results.json) carries one recall, precision, and consistency per
(skill, skill_version, model, domain) group, computed over **all** findings. Its schema fixes
`additionalProperties: false` on each entry and has no lane dimension, so judged-only and scripted-only
figures cannot be carried there without a schema change, which was out of scope for this run.

The judged and scripted columns above are therefore derived: each envelope's `findings[]` is filtered
to the target lane and passed to the same unmodified `bench.metrics.score` primitives
(`score_artifact`, `score_consistency`) that produce the committed numbers. Nothing else differs.
Recomputation is under [Reproduction](#reproduction).

This is the first exception in the repository to the rule stated in `bench/README.md` and in
`results.schema.json` that no number appears in any document here that is not present in a committed
`results.json`. It is flagged in
[ADR 0022](../../docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md) as an open
item: v0.2 should add an optional lane dimension to the results schema so all three cuts are committed
and drift-checked like every other number.

## Reproduction

```
git clone https://github.com/product-on-purpose/critique-skills.git
cd critique-skills

# 1. Confirm the corpus is what the numbers were measured against.
python -m bench.generator verify --corpus bench/corpus
python -m bench.generator leak-check --corpus bench/corpus

# 2. Build a scoring view of the measurement grid. The steering probe set is NOT part of
#    the 460-run grid and must be excluded; scoring bench/results/runs directly changes
#    critique-clarity/sonnet and will not reproduce the committed file.
mkdir -p /tmp/p3-grid && cp -r bench/results/runs/* /tmp/p3-grid/ && rm -rf /tmp/p3-grid/steering

# 3. Rescore. Output matches the committed results.json apart from `generated_at`. Every entry now
#    carries recall_location and precision_location alongside the criterion-level recall and
#    precision, computed in the same pass from the same envelopes.
python -m bench.metrics score --corpus bench/corpus --runs /tmp/p3-grid \
    --out /tmp/results-check.json --run-set p3-2026-07-31

# 4. Confirm the published tables have not drifted from the committed numbers.
python -m bench.report table --results bench/results/results.json --check
```

**To reproduce a judged-lane or scripted-lane column**, repeat step 3 with each envelope's `findings[]`
filtered to `lane == "judged"` (or `"scripted"`) before it reaches `bench.metrics.score`. The score
primitives are lane-agnostic and take the filtered envelope unchanged.

## Known issues in the measurement tooling

Reported, not fixed. Each affects how far a reader should trust the surrounding claims.

- **`contract/validate_envelopes.py` does not reach these files.** Its discovery glob is
  `bench/results/*/*.json`, one level below `bench/results/`, while the harness writes three to four
  levels deep at `bench/results/runs/<skill>/<artifact>/<run>.json`. Run today it reports "does not
  exist or is empty; nothing to validate yet" despite 462 envelopes on disk. This is the documented CI
  schema-job entry point, so as wired that job is not exercising these files. The 462-of-462 validity
  result above was obtained by calling the underlying `contract.validate.validate_document` on each
  file directly, which is the same check the CLI would have applied.
- **Scoring `bench/results/runs` directly does not reproduce `results.json`.** The steering envelopes
  share identity fields with the main grid and pool into `critique-clarity` / sonnet / clarity, taking
  it to 22 scored runs and 51 consistency pairs. The exclusion is a step in the reproduction recipe
  rather than a property of the layout, which is fragile. A separate top-level directory for probe run
  sets would make the mistake impossible.
- **Path drift in the generated block.** `bench/README.md`'s generated results block names
  `bench/results/p3-2026-07-31/results.json` as the file to edit; the committed file is
  `bench/results/results.json`.
