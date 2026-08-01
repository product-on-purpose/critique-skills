# Stretch-skill ship/hold verdicts

Run set `p3-2026-07-31`, measured 2026-07-31 on `claude-haiku-4-5-20251001` and `claude-sonnet-5`
at k=5. Every number below is read from [`results.json`](results.json) except the judged-lane
column, which is a derived cut (see [Judged-lane figures](#judged-lane-figures) for the recipe).

This file discharges [S-05 (skills slate)](../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)
AC-7: each stretch skill carries a recorded verdict citing its numbers against the
[R1 (consistency floor value)](../../docs/internal/release-plans/plan_v0.1.0/plan_v0.1.0.md) floor.

> **Re-examined 2026-07-31 against location-level metrics.** The sections below the summary are the
> original criterion-level record, written before `results.json` carried `recall_location` and
> `precision_location`. They are kept unedited except where they stated something the rescore has
> since falsified, which is marked in place. The current verdicts, and the reasoning that now
> supports them, are in
> [Location-level re-examination (2026-07-31)](#location-level-re-examination-2026-07-31).
> **All three verdicts are re-affirmed as SHIP. One of them ships on a different argument than the
> one originally recorded.**

## The gate

A stretch skill ships only if **both** conditions hold ([S-05](../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md), "Requirements"):

1. **Baseline win.** Higher seeded-defect recall than the frozen `baseline-generic` prompt at
   equal-or-better precision, on at least one pinned tier.
2. **Consistency floor.** Consistency at or above **0.309**, the minimum core-skill overall-lane
   consistency, per [ADR 0022 (consistency floor: 0.309, overall lane)](../../docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md).

A skill failing either condition is excluded from `library.json` components and retained in-tree as
`status: incubating`, with its numbers published here regardless.

**Read condition 1 with the caveat in [What "beats baseline" is worth here](#what-beats-baseline-is-worth-here) before quoting it.**
At criterion level the baseline scores exactly 0.000 recall and 0.000 precision in every domain on both
tiers, and it could not have scored anything else. Condition 1, read that way, is satisfied by any
nonzero recall. It has since been re-read against the location-level metrics, where the baseline is not
pinned at zero and one stretch skill's recall win disappears entirely:
[Location-level re-examination (2026-07-31)](#location-level-re-examination-2026-07-31).

## Summary

| Skill | Baseline win (criterion) | Baseline win (location) | Consistency vs floor 0.309 | Verdict |
|---|---|---|---|---|
| critique-docs | Yes, both tiers | **Recall ties exactly, both tiers.** Wins on precision by 3.2x and 4.2x | 0.842 haiku, 1.000 sonnet | **SHIP**, on precision dominance at equal recall |
| critique-microcopy | Yes, both tiers | Yes, both tiers, both metrics | 0.768 haiku, 0.853 sonnet | **SHIP** |
| critique-argument | Yes, both tiers | Yes, both tiers, both metrics | 0.371 haiku, 0.737 sonnet | **SHIP** (thin on haiku, +0.062) |

All three ship. All three go into `library.json` components; none is retained as incubating. No
verdict flipped in the location-level re-examination, so `library.json` and the generated
`plugin.json` are unchanged by it.

**The core slate is a different story and it is not this file's to settle.** The same rescore shows
`critique-accessibility`, a **core** skill, reading below the frozen baseline at location level on
both tiers and on both metrics. That is a substantive failure of
[S-05](../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) AC-6, whose own
remedy is a release halt with a handover diagnosis, and it is recorded in
[ADR 0026 (location-level re-examination of the baseline gates)](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
and in [`README.md`](README.md#core-skills-s-05-ac-6), not here. A reader who takes "all three
stretch skills ship" from this file and stops has read the good half of the rescore.

## Location-level re-examination (2026-07-31)

Judged by the P3 verdict-review pass on the day of the rescore, on the same run set, from the same 460
committed envelopes. **No new runs, no envelope touched, no skill changed.** Only the metric the gate
is read against changed, and only by addition: `results.json` (results version 1.1.0) now carries
`recall_location` and `precision_location` beside the criterion-level pair, computed by
`bench/metrics/score.py`'s `score_artifact_location` under the identical per-artifact-type tolerance,
with criterion equality dropped from the match predicate.

**Why the verdicts needed re-examining at all.** Condition 1 of the gate, as originally applied, was
worthless: the baseline scored 0.000 recall and 0.000 precision in every domain on both tiers because
every baseline finding carries the fixed criterion `BASELINE-GENERIC` and no manifest plants a defect
under it. Any nonzero recall cleared it. The location-level cut is the first comparison in this run set
that could have gone against a skill, so it is the first one worth calling a gate. Applying it is not
optional politeness: a verdict that rests on a comparison that could not have failed is not a verdict.

**How condition 1 is read here.** The written rule is "higher seeded-defect recall than the frozen
`baseline-generic` prompt at equal-or-better precision, on at least one pinned tier". At location level
that is read literally, and where it is not literally met, the skill ships only on an explicitly stated
dominance argument: no worse than the baseline on either metric and strictly better on at least one.
Nothing else counts. Condition 2, the [ADR 0022](../../docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md)
consistency floor of 0.309, is unchanged and unaffected: consistency was never scored through the
criterion-versus-baseline comparison, it is a within-skill run-to-run measure, and the rescore did not
alter a single consistency figure.

Location-level figures, all six stretch cells, read from [`results.json`](results.json):

| Skill | Tier | Recall (loc) | Baseline recall (loc) | Precision (loc) | Baseline precision (loc) | Condition 1 |
|---|---|---|---|---|---|---|
| critique-docs | haiku | 0.933 (28/30) | 0.933 (28/30) | 0.875 (28/32) | 0.275 (28/102) | **tie on recall**, +0.600 precision |
| critique-docs | sonnet | 1.000 (30/30) | 1.000 (30/30) | 1.000 (30/30) | 0.238 (30/126) | **tie on recall**, +0.762 precision |
| critique-microcopy | haiku | 0.920 (69/75) | 0.813 (61/75) | 0.831 (69/83) | 0.581 (61/105) | met, both metrics |
| critique-microcopy | sonnet | 0.960 (72/75) | 0.840 (63/75) | 0.911 (72/79) | 0.481 (63/131) | met, both metrics |
| critique-argument | haiku | 0.825 (33/40) | 0.525 (21/40) | 0.579 (33/57) | 0.189 (21/111) | met, both metrics |
| critique-argument | sonnet | 0.775 (31/40) | 0.725 (29/40) | 0.470 (31/66) | 0.228 (29/127) | met, both metrics |

### critique-docs: SHIP re-affirmed, on a different argument

**The original argument does not survive.** "Beats baseline on recall, both tiers" was true only at
criterion level. At location level `critique-docs` and the generic prompt find **exactly the same
planted defects**: 28 of 30 on haiku, both sides; 30 of 30 on sonnet, both sides. Not "close to".
Identical, on both tiers. Every defect this skill finds, an unrubricked prompt also points at. The
recall half of condition 1 is therefore **not met on either tier**, and any sentence claiming this skill
finds defects the baseline misses is false on this evidence.

**What it does have is dominance on the other half, and it is not marginal.** At equal recall it emits
32 claims against the baseline's 102 on haiku (precision 0.875 against 0.275) and 30 against 126 on
sonnet (1.000 against 0.238). It emits 0.000 findings per run on the clean artifact against the
baseline's 5.000 and 6.200. Its consistency is 0.842 and 1.000 against 0.479 and 0.537. On every
like-for-like measure other than recall it is better, on some by a factor of four, and on none of them
worse. That is a Pareto-dominance argument, it is stated here rather than implied, and it is what this
verdict now rests on: **`critique-docs` ships because it finds the same defects the baseline finds
while saying almost nothing else, not because it finds more.**

**Condition 2 unchanged:** 0.842 (+0.533) and 1.000 (+0.691) against the 0.309 floor, the largest
margins in the slate.

**Verdict: SHIP.** A hold here would be perverse: this is the most precise, most repeatable, quietest
cell in the run set, and it would be held for tying a comparator that the same rescore shows to be a
high-volume emitter. But the claim the skill is allowed to make in public shrinks accordingly. It is a
precision result, not a detection result.

**What would flip it:** a recall figure that fell below the baseline's rather than tying it, or a
precision advantage that narrowed to nothing. Both are far away. The corpus caveat in the original
section below still applies and is the more serious limit on what this row can support: 6 distinct
planted defect types across 3 artifacts, not 30 independent trials.

### critique-microcopy: SHIP re-affirmed, strengthened

Strict dominance at location level on both tiers, on both metrics: recall 0.920 against 0.813 (haiku)
and 0.960 against 0.840 (sonnet), precision 0.831 against 0.581 and 0.911 against 0.481. Condition 1 is
met literally, no dominance argument needed. Condition 2 met at 0.768 and 0.853.

The location-level cut **improves** this skill's own numbers as well (recall 0.840 to 0.920 on haiku,
0.920 to 0.960 on sonnet), which means a handful of its findings landed on the right string under the
wrong criterion ID. That is a real, if small, rubric-labeling gap and it belongs on the record: 6 of 75
on haiku, 3 of 75 on sonnet.

**Verdict: SHIP.** This is the only stretch skill whose baseline win means at location level what the
original file said it meant at criterion level. **What would flip it:** nothing in this run set.

### critique-argument: SHIP re-affirmed, margin still the thinnest in the slate

Strict dominance at location level on both tiers: recall 0.825 against 0.525 (haiku) and 0.775 against
0.725 (sonnet), precision 0.579 against 0.189 and 0.470 against 0.228. Condition 1 is met literally.

**The sonnet recall margin is +0.050, which is two defect instances out of forty**, and it should be
read the way the original section below reads the consistency margin: not a distinguishable result. The
haiku cell carries this verdict (+0.300 recall, +0.390 precision), not the sonnet one.

Condition 2 is unchanged and remains the binding constraint: 0.371 on haiku, +0.062 over the floor,
still the thinnest margin anywhere in the slate, still inside plausible k=5 sampling noise. The
observation in the original section below, that this skill is less consistent on haiku than the generic
baseline prompt (0.371 against 0.600), also stands unchanged, and its "not like-for-like" defence still
holds: consistency is scored on `(criterion, location)` pairs for both conditions, so the skill is still
being asked to agree with itself on a strictly harder predicate than the single-criterion baseline is.
The location-level rescore does not touch consistency and does not soften that row.

**Verdict: SHIP.** **What would flip it:** unchanged from the original entry, a re-run in which haiku
consistency lands below 0.309. Location level moved nothing here.

### What this re-examination did not change

- **No skill's status changed**, so `library.json` `components.skills` is untouched, `plugin.json` was
  not regenerated, and the release gate was not re-run for a manifest change. It was re-run as a check
  and reports the same result as before.
- **The consistency floor of 0.309 stands**, unmodified, source cell unmodified. Location-level
  scoring changes recall and precision only.
- **The criterion-level numbers stand**, in `results.json` and in the sections below. They are the
  primary metric for a skill, because they measure whether the rubric was operationalized rather than
  whether something was noticed nearby, and the rescore added a column rather than replacing one.

## critique-docs: SHIP

*(Original criterion-level entry, 2026-07-31, superseded in part by
[the re-examination above](#critique-docs-ship-re-affirmed-on-a-different-argument). Its "Condition 1,
baseline win" paragraph is the claim the location-level cut falsified.)*

Domain `docs`, artifact type `markdown-tree`, 4 artifacts (3 seeded, 1 clean), 6 planted defects per
pass, 20 scored runs per tier.

| Metric | haiku | sonnet | Baseline haiku | Baseline sonnet |
|---|---|---|---|---|
| Recall | 0.933 (28/30) | 1.000 (30/30) | 0.000 (0/30) | 0.000 (0/30) |
| Precision | 0.875 (28/32) | 1.000 (30/30) | 0.000 (0/102) | 0.000 (0/126) |
| Consistency (overall) | 0.842 | 1.000 | 0.479 | 0.537 |
| Consistency (exact locations) | 0.675 | 0.933 | 0.389 | 0.535 |
| Consistency (judged lane only) | 0.775 | 1.000 | n/a | n/a |
| Clean-artifact findings per run | 0.000 | 0.000 | 5.000 | 6.200 |
| Unresolvable locations | 3 of 32 claims | 0 of 30 | 20 of 102 | 14 of 126 |

**Condition 1, baseline win:** met on both tiers. Recall 0.933 and 1.000 against 0.000, precision
0.875 and 1.000 against 0.000.

**Condition 2, consistency floor:** met on both tiers. 0.842 (+0.533) and 1.000 (+0.691).

**Verdict: SHIP.** The strongest cell in the slate. On sonnet it is perfect on every scored metric:
every planted defect found, no unplanted claims, identical findings across all five runs, nothing
emitted on the clean artifact. Judged-lane-only recall is 0.433 haiku and 0.500 sonnet, meaning
roughly half of this skill's recall comes from its deterministic scripted lane, which is exactly the
mixed lane balance [S-05](../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)
specifies for the Diataxis domain.

**Read the perfect sonnet row sceptically.** 30 of 30 on a 6-defect, 3-artifact seeded corpus is 6
distinct defect types, not 30 independent trials: the same 6 defects were found in all 5 runs. It is
a real result about repeatability and a weak result about breadth. The corpus is the limiting factor,
not the skill.

**What would flip this:** nothing in this run set. A regression below 0.309 consistency or a
precision drop below the baseline would, but both are far away.

## critique-microcopy: SHIP

Domain `microcopy`, artifact type `markdown-prose`, 4 artifacts (3 seeded, 1 clean), 15 planted
defects per pass, 20 scored runs per tier.

| Metric | haiku | sonnet | Baseline haiku | Baseline sonnet |
|---|---|---|---|---|
| Recall | 0.840 (63/75) | 0.920 (69/75) | 0.000 (0/75) | 0.000 (0/75) |
| Precision | 0.759 (63/83) | 0.873 (69/79) | 0.000 (0/105) | 0.000 (0/131) |
| Consistency (overall) | 0.768 | 0.853 | 0.521 | 0.610 |
| Consistency (exact locations) | 0.768 | 0.853 | 0.311 | 0.659 |
| Consistency (judged lane only) | 0.623 | 0.846 | n/a | n/a |
| Clean-artifact findings per run | 0.000 | 0.200 | 5.200 | 6.000 |
| Unresolvable locations | 0 of 83 claims | 0 of 79 | 18 of 105 | 14 of 131 |

**Condition 1, baseline win:** met on both tiers. Recall 0.840 and 0.920 against 0.000, precision
0.759 and 0.873 against 0.000.

**Condition 2, consistency floor:** met on both tiers. 0.768 (+0.459) and 0.853 (+0.544).

**Verdict: SHIP.** Second-strongest in the slate and the most robust to the corpus caveat above,
since it is scored against 15 planted defects rather than 6. Its overall and exact-location
consistency are identical on both tiers (0.768 and 0.853), meaning it phrases locations the same way
every run: zero unresolvable locations across 162 claims on the two tiers combined. That is the
cleanest location behavior of any skill in the slate.

**Unflattering detail:** judged-lane consistency on haiku is 0.623 against 0.768 overall, so about a
fifth of its apparent repeatability on the cheap tier is scripted-lane determinism rather than stable
judgment. Judged-lane recall is 0.373 haiku and 0.453 sonnet.

**What would flip this:** nothing in this run set.

## critique-argument: SHIP, with the thinnest margin in the slate

Domain `argument`, artifact type `markdown-prose`, 3 artifacts (2 seeded, 1 clean), 8 planted defects
per pass, 15 scored runs per tier.

| Metric | haiku | sonnet | Baseline haiku | Baseline sonnet |
|---|---|---|---|---|
| Recall | 0.775 (31/40) | 0.775 (31/40) | 0.000 (0/40) | 0.000 (0/40) |
| Precision | 0.544 (31/57) | 0.470 (31/66) | 0.000 (0/111) | 0.000 (0/127) |
| Consistency (overall) | **0.371** | 0.737 | 0.600 | 0.718 |
| Consistency (exact locations) | 0.286 | 0.463 | 0.363 | 0.538 |
| Consistency (judged lane only) | 0.320 | 0.724 | n/a | n/a |
| Clean-artifact findings per run | 1.200 | 2.600 | 7.000 | 7.600 |
| Unresolvable locations | 0 of 57 claims | 0 of 66 | 2 of 111 | 1 of 127 |

**Condition 1, baseline win:** met on both tiers. Recall 0.775 on both against 0.000, precision 0.544
and 0.470 against 0.000.

**Condition 2, consistency floor:** met on both tiers, but haiku clears by **+0.062** (0.371 against
0.309), the thinnest margin anywhere in the slate. Sonnet clears by +0.428.

**Verdict: SHIP.** Both gate conditions are met on both tiers, so the verdict is not in doubt under
the rule as written. Three things belong on the record beside it.

**First, the haiku margin is inside plausible sampling noise.** k=5 gives 10 pairwise comparisons per
artifact across 2 seeded artifacts plus 1 clean one. A margin of 0.062 on that sample is not a
distinguishable result from "at the floor", and a re-run could land either side of it. The verdict
holds, the margin should not be quoted as a quality claim.

**Second, this skill is less consistent on haiku than the generic baseline prompt is.** 0.371 against
the baseline's 0.600. That comparison is not like-for-like, because every baseline finding carries the
single criterion `BASELINE-GENERIC`, so two baseline findings agree whenever their locations agree,
while two skill findings must agree on criterion *and* location. The skill is being scored on a
strictly harder predicate. It is still the one row in this file where a skill number is worse than the
baseline number in the same cell, and it is not hidden.

**Third, precision falls as the tier gets stronger.** 0.544 on haiku, 0.470 on sonnet, with
clean-artifact findings rising from 1.200 to 2.600 per run. Recall is flat at 0.775 across both tiers.
The stronger model is not finding more planted defects; it is making more unplanted claims. That
pattern is worth a look before v0.2, not a hold in v0.1.0.

**What would flip this:** a re-run in which haiku consistency lands below 0.309. That is the single
result in this file that a different set of five runs could plausibly change.

## What "beats baseline" is worth here

Every row above shows the frozen baseline at recall 0.000 and precision 0.000, in every domain, on
both tiers. That is not an empirical finding about the generic prompt. It is a structural property of
how the bench matches claims to defects.

`bench/metrics/match.py` matches a claim to a planted defect only when the claim's `criterion` string
equals the defect's `criterion` string and the locations resolve to a hit. `bench/baseline/postprocess.py`
assigns every baseline finding the fixed criterion `BASELINE-GENERIC`, because the baseline has no
rubric to cite. No manifest anywhere in the corpus plants a defect under that criterion. **The
baseline's recall and precision are therefore pinned at exactly 0.000 by construction, and no baseline
response, however good, could score otherwise.**

What follows:

- Condition 1 of the gate ("beats baseline on recall at equal-or-better precision") is satisfied by any
  skill that scores above zero. It discriminates nothing among the three stretch skills.
- The verdicts above therefore rest, in practice, on the absolute numbers and on the consistency floor,
  not on the baseline comparison.
- The baseline comparison is not worthless. It is informative on the metrics that do not depend on
  criterion matching: clean-artifact false-positive rate (the baseline emits 5.0 to 7.6 findings per run
  on artifacts with no planted defects, against 0.000 to 2.600 for the three stretch skills) and
  unresolvable locations (up to 107 of 137 baseline claims in one cell could not be resolved to a
  location at all). Those comparisons are like-for-like and they are the ones worth quoting.

This is recorded as a measurement-instrument limitation, not fixed. Fixing it means either scoring the
baseline on a criterion-agnostic location-only match, or adjudicating baseline findings by hand.

**Correction, 2026-07-31 (same day, after the rescore).** The sentence that stood here claimed both
fixes "change the frozen comparison and require a new run set". That was wrong about the first one. A
criterion-agnostic location-only match needs no new runs at all: it is a different predicate applied to
the same committed envelopes, and it has now been computed and committed as `recall_location` and
`precision_location` in [`results.json`](results.json). What it did require was a results-schema minor
bump, because the entry object sets `additionalProperties: false`. The rest of this section stands: the
criterion-level zeros are arithmetic, not measurement, and the clean-artifact and unresolvable-location
comparisons remain the like-for-like ones on the criterion-level cut. See
[Location-level re-examination (2026-07-31)](#location-level-re-examination-2026-07-31) for what the
fair comparison did to these verdicts, and
[ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md) for
what it did to the core gate.

## Judged-lane figures

The judged-lane column is a derived cut, not a committed number: `results.json` carries one
consistency, recall, and precision per (skill, skill_version, model, domain) group, computed over all
findings, and its schema fixes `additionalProperties: false` with no lane dimension. The judged figures
here are produced by filtering each envelope's `findings[]` to `lane: "judged"` and calling the same
unmodified `bench.metrics.score` primitives (`score_artifact`, `score_consistency`). The recipe is in
[`README.md`](README.md). See [ADR 0022](../../docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md)
for why the gate uses the overall cut and publishes the judged cut beside it.
