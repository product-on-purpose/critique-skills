# Stretch-skill ship/hold verdicts

Run set `p3-2026-07-31`, measured 2026-07-31 on `claude-haiku-4-5-20251001` and `claude-sonnet-5`
at k=5. Every number below is read from [`results.json`](results.json) except the judged-lane
column, which is a derived cut (see [Judged-lane figures](#judged-lane-figures) for the recipe).

This file discharges [S-05 (skills slate)](../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)
AC-7: each stretch skill carries a recorded verdict citing its numbers against the
[R1 (consistency floor value)](../../docs/internal/release-plans/plan_v0.1.0/plan_v0.1.0.md) floor.

## The gate

A stretch skill ships only if **both** conditions hold ([S-05](../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md), "Requirements"):

1. **Baseline win.** Higher seeded-defect recall than the frozen `baseline-generic` prompt at
   equal-or-better precision, on at least one pinned tier.
2. **Consistency floor.** Consistency at or above **0.309**, the minimum core-skill overall-lane
   consistency, per [ADR 0022 (consistency floor: 0.309, overall lane)](../../docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md).

A skill failing either condition is excluded from `library.json` components and retained in-tree as
`status: incubating`, with its numbers published here regardless.

**Read condition 1 with the caveat in [What "beats baseline" is worth here](#what-beats-baseline-is-worth-here) before quoting it.**
The baseline scores exactly 0.000 recall and 0.000 precision in every domain on both tiers, and it
could not have scored anything else. Condition 1 is satisfied by any nonzero recall.

## Summary

| Skill | Baseline win | Consistency vs floor 0.309 | Verdict |
|---|---|---|---|
| critique-docs | Yes, both tiers | 0.842 haiku, 1.000 sonnet | **SHIP** |
| critique-microcopy | Yes, both tiers | 0.768 haiku, 0.853 sonnet | **SHIP** |
| critique-argument | Yes, both tiers | 0.371 haiku, 0.737 sonnet | **SHIP** (thin on haiku, +0.062) |

All three ship. All three go into `library.json` components; none is retained as incubating.

## critique-docs: SHIP

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
baseline on a criterion-agnostic location-only match, or adjudicating baseline findings by hand. Both
change the frozen comparison and require a new run set.

## Judged-lane figures

The judged-lane column is a derived cut, not a committed number: `results.json` carries one
consistency, recall, and precision per (skill, skill_version, model, domain) group, computed over all
findings, and its schema fixes `additionalProperties: false` with no lane dimension. The judged figures
here are produced by filtering each envelope's `findings[]` to `lane: "judged"` and calling the same
unmodified `bench.metrics.score` primitives (`score_artifact`, `score_consistency`). The recipe is in
[`README.md`](README.md). See [ADR 0022](../../docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md)
for why the gate uses the overall cut and publishes the judged cut beside it.
