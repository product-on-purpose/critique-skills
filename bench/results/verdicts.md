# Ship and hold verdicts

This file records the current ship or hold verdict for every skill in the library, with the
figures each verdict rests on and a link to the decision record that explains the reasoning. It
reads [`results.json`](results.json), run sets `p3-2026-07-31`, `cal1-2026-08-01` and
`bench-2026-10-03`. It is current as of 2026-10-15. The layered record this file replaced, with its
original 2026-07-31 reasoning and its dated amendments, is recoverable from git at commit
`a852b52`. Some of that original reasoning exists nowhere else, so this pointer is required rather
than decorative.

- Machine-readable numbers: [`results.json`](results.json)
- Narrative and the unflattering numbers first: [`README.md`](README.md)
- Full generated tables, every skill and baseline row: [`../README.md`](../README.md)

## The gate

A skill ships when it beats the frozen `baseline-generic` prompt and clears a consistency floor.
Three gates apply, because the library grew past its first release.

**Core skills ship on [S-05 (skills slate)](../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)
AC-6.** A core skill ships regardless of its first-pass numbers, and those numbers publish as
measured. AC-6 asks for higher recall than the frozen baseline at equal-or-better precision, on at
least one pinned tier. If no tier passes, the release halts for a handover diagnosis, or the
library iterates once and re-measures.

**Stretch and later skills ship on AC-7's two-condition rule.** A stretch skill ships only if it
beats the baseline under the same rule AC-6 states, and clears the consistency floor below; a
skill that fails either condition is excluded from `library.json` components and kept in the tree
with `status: experimental`, per [ADR 0036 (experimental status until the ship verdict)](../../docs/internal/decisions/0036-experimental-status-until-ship-verdict.md).
`critique-forms` followed the same two-condition shape under its own spec's AC-12, which names the
same baseline test and points the consistency half at the floor in force on its approval day; see
its own section below.

<a id="location-level-re-examination-2026-07-31"></a>

**Both rules are read at location level, not at criterion level.** `bench/metrics/match.py`
matches a claim to a planted defect only when the claim's criterion string equals the defect's.
`bench/baseline/postprocess.py` stamps every baseline finding with the fixed criterion
`BASELINE-GENERIC`, and no corpus manifest plants a defect under that criterion. The baseline's
criterion-level recall and precision are therefore pinned at exactly 0.000 in every domain, on both
tiers, by construction. A gate read against that comparison cannot fail, so it is not a gate. The
location-level cut drops the criterion-equality requirement and credits a claim when its location
resolves, within the artifact type's documented tolerance, to the planted defect's location.
[ADR 0026 (location-level re-examination of the baseline gates)](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
made this cut the substantive reading for both gates, on the same 460 envelopes already committed,
with no new runs. A skill passes a tier under this reading by meeting the rule literally (higher
recall at equal-or-better precision) or by stated dominance (no worse on either metric, strictly
better on one).

**The consistency floor is set per tier, on the overall lane.** [ADR 0038 (consistency threshold
v2)](../../docs/internal/decisions/0038-consistency-threshold-v2-per-tier-floors.md) replaced the
single floor [ADR 0022 (consistency floor: 0.309, overall lane)](../../docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md)
set. The floor is now **0.450 on the sonnet tier**, the lowest current-harness overall-lane
consistency among the three core skills. On the **haiku tier it stays 0.309**, ADR 0022's figure
from run set `p3-2026-07-31`, until all three core skills have current-harness haiku data. The
scripted lane's expected consistency is 1.000, reported and not gated; a reading below 1.000 is a
known transport defect, not a calibration target. The judged lane publishes per cell as a
diagnostic, with no threshold.

Every verdict recorded below applied the single 0.309 floor, because that was the rule in force
when each skill shipped. Every shipped skill also clears both of ADR 0038's per-tier floors. ADR
0038 carries the per-skill margin table, and it reads each sonnet margin from the current harness,
so the sonnet floor's source figures are not in `results.json`.

## Summary

| Skill and version | Gate | Verdict | Deciding figures (location-level, vs baseline) | Consistency vs 0.309 (haiku / sonnet) | Source |
|---|---|---|---|---|---|
| `critique-clarity` 0.1.0 | AC-6 | Passes substantively, both tiers | Haiku: recall 0.780 vs 0.540, precision 0.419 vs 0.329. Sonnet: recall 0.890 vs 0.880, precision 0.434 vs 0.335 | 0.309 (sets the floor) / 0.466 | [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md) |
| `critique-accessibility` 0.1.1 | AC-6 | Passes substantively, both tiers, literally | Haiku: recall 0.988 vs 0.376, precision 0.875 vs 0.258. Sonnet: recall 0.965 vs 0.776, precision 0.672 vs 0.293 | 0.625 / 0.808 | [ADR 0028](../../docs/internal/decisions/0028-post-calibration-verdict-accessibility-clears-ac-6.md) |
| `critique-usability` 0.1.0 | AC-6 | Passes on haiku only; ships qualified through haiku | Haiku: recall 0.800 vs 0.000, precision 0.231 vs 0.000. Sonnet: recall 0.857 vs 0.829, precision 0.169 vs 0.181 (no pass) | 0.378 / 0.642 | [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md) |
| `critique-docs` 0.1.0 | AC-7 | SHIP, on precision dominance at equal recall | Haiku: recall ties 0.933 vs 0.933, precision 0.875 vs 0.275. Sonnet: recall ties 1.000 vs 1.000, precision 1.000 vs 0.238 | 0.842 / 1.000 | [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md) |
| `critique-microcopy` 0.1.0 | AC-7 | SHIP, both tiers, both metrics | Haiku: recall 0.920 vs 0.813, precision 0.831 vs 0.581. Sonnet: recall 0.960 vs 0.840, precision 0.911 vs 0.481 | 0.768 / 0.853 | [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md) |
| `critique-argument` 0.1.0 | AC-7 | SHIP, thinnest consistency margin in the slate | Haiku: recall 0.825 vs 0.525, precision 0.579 vs 0.189. Sonnet: recall 0.775 vs 0.725, precision 0.470 vs 0.228 | 0.371 (+0.062) / 0.737 | [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md) |
| `critique-forms` 0.1.0 | N2 AC-12 | SHIP, decisive on haiku, near-tie on sonnet | Haiku: recall 0.933 vs 0.438, precision 0.458 vs 0.287. Sonnet: recall 0.905 vs 0.819, precision 0.317 vs 0.303 | 0.691 / 0.651 | [ADR 0037](../../docs/internal/decisions/0037-critique-forms-ship-verdict.md) |

All seven skills ship. `library.json` `components.skills` lists all seven as `active`.
`critique-accessibility` ships at 0.1.1; its 0.1.0 predecessor failed AC-6 substantively on both
tiers and both metrics and is superseded, not installable. No verdict in this file moves anything
recorded in the ADRs it cites; it restates each ADR's ruling with the ADR's own figures.

## critique-clarity 0.1.0

**Verdict: passes AC-6 substantively, on both tiers, literally.** Location-level recall and
precision both beat the frozen baseline on haiku (0.780 against 0.540 recall, 0.419 against 0.329
precision) and on sonnet (0.890 against 0.880 recall, 0.434 against 0.335 precision). Figures from
`results.json`, `lane: "overall"`, run set `p3-2026-07-31`.

**Weakest point.** The sonnet recall margin is +0.010, one defect instance out of a hundred. The
haiku cell, with a +0.240 recall margin and a +0.090 precision margin, is what carries the verdict;
the sonnet pass is real but thin. `critique-clarity` also sets both consistency floors: 0.309 on
haiku, from [ADR 0022](../../docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md),
and 0.450 on sonnet, from its current-harness re-measurement, per
[ADR 0038](../../docs/internal/decisions/0038-consistency-threshold-v2-per-tier-floors.md). A skill
exactly as consistent as clarity passes either floor with no margin at all.

**What would flip it.** A haiku dominance margin this wide is far from reversing. The sonnet cell
is the one a different set of five runs could plausibly move, since its own margin is already
inside the range a single defect instance can shift.

**Dated caveats.** Two harness re-measurements exist outside `results.json` and feed no published
number. On haiku, run `31988100372` (2026-08-17) landed inside its fidelity-gate band on
`recall_location` and outside it on `precision_location`, by less than the band's own width, which
[ADR 0031 (the fidelity gate's acceptance band)](../../docs/internal/decisions/0031-fidelity-gate-acceptance-band.md)
reads as triggering investigation rather than failure. On sonnet, run `34917562578` (2026-09-15)
missed its band on `precision_location` by more than the band's width, which ADR 0031 records as "a
failure by the gate's own rule". ADR 0031 traces most of that move to the judged lane no longer
emitting an `instances` field, and it states plainly: "None of it is the skill finding fewer
defects." Both location recall and criterion-level recall in the re-run are above the committed
figures. Neither re-run changes this verdict or feeds a
published number.

**History:** [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
for the location-level ruling; [`bench/results/README.md`, "Core skills: S-05 AC-6"](README.md)
for the same ruling in narrative form; [ADR 0031](../../docs/internal/decisions/0031-fidelity-gate-acceptance-band.md)
for both dated harness re-measurements.

<a id="post-calibration-verdict-cal1-2026-08-01"></a>

## critique-accessibility 0.1.1

**Verdict: passes AC-6 substantively, on both tiers, literally rather than by dominance.** Location
recall is 0.988 against the baseline's 0.376 on haiku and 0.965 against 0.776 on sonnet; location
precision is 0.875 against 0.258 and 0.672 against 0.293. Both the recall half and the precision
half are won outright on both tiers, so no dominance argument is needed. Figures from
`results.json`, `lane: "overall"`, run set `cal1-2026-08-01`.

0.1.1 is a fix, not a rewrite. 0.1.0 failed AC-6 substantively on both tiers and both metrics
(haiku recall 0.176 against the baseline's 0.376; sonnet recall 0.306 against 0.776), the largest
gap in the run set. [ADR 0027 (accessibility location-emission calibration)](../../docs/internal/decisions/0027-accessibility-location-emission-calibration.md)
diagnosed the failure as a location-emission defect, not a detection defect: `checks.py` found 13
of 13 scripted-lane-targeted planted defects locally with no false positives, but named most of
them with a line number the location resolver cannot bind. [ADR 0028 (post-calibration verdict)](../../docs/internal/decisions/0028-post-calibration-verdict-accessibility-clears-ac-6.md)
is the re-measurement that supplies the 0.1.1 score above, after the fix. Judged-lane detection is
flat across the two versions (36 of 40 opportunities under 0.1.0, 35 of 40 under 0.1.1), which is
the evidence that the gain is a reporting fix and not an improvement in what the skill notices.
0.1.0 is superseded and is not installable; its row stays in `results.json` and in the generated
tables beside 0.1.1's, unreplaced, because overwriting a recorded failure once it is fixed is how a
results page becomes an advertisement.

**Weakest point.** ADR 0028 names three limits on its own result. The comparison spans two run
sets, `p3-2026-07-31` for the baseline and `cal1-2026-08-01` for 0.1.1, though both share the same
corpus bytes and model IDs and the baseline is frozen by construction. The `cal1-2026-08-01` run
set has no provenance document naming the mechanism that produced its 40 envelopes, which ADR 0028
calls "the weakest link in this verdict". And the corpus is unusually id-rich: every seeded defect
sits on an element carrying its own `id`, which is exactly the anchor the 0.1.1 fix prefers, so how
much of the gain survives on markup without ids is not measured by this run set.

**What would flip it.** Measuring an id-poor accessibility artifact, which ADR 0028 names as an
open item and which this run set does not contain.

**Dated caveat.** Run `38673834829` (2026-10-14, sonnet) re-measured this cell through the current
harness: `recall_location` landed inside its fidelity-gate band, and `precision_location` landed
outside it, below the band, by 0.017 against a band 0.062 wide.
[ADR 0031](../../docs/internal/decisions/0031-fidelity-gate-acceptance-band.md) reads a single miss
smaller than the band's width as triggering investigation, not failure. It traces the miss to the
critic writing more judged findings, not to the skill finding fewer defects. The re-run changes no
verdict and feeds no published number.

**History:** [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
for the 0.1.0 failure, [ADR 0027](../../docs/internal/decisions/0027-accessibility-location-emission-calibration.md)
for the fix, [ADR 0028](../../docs/internal/decisions/0028-post-calibration-verdict-accessibility-clears-ac-6.md)
for the 0.1.1 measurement and its checks, and [`bench/results/README.md`, "Core skills: S-05 AC-6"](README.md)
for the narrative form of both.

## critique-usability 0.1.0

**Verdict: passes AC-6 on haiku only; ships qualified through haiku.** On haiku, location recall is
0.800 against the baseline's 0.000 and location precision is 0.231 against 0.000, a literal pass
against a comparator that resolved nothing. On sonnet, the skill wins recall by 0.028 (0.857
against 0.829) and loses precision by 0.012 (0.169 against 0.181), which is a pass on neither
reading named in [The gate](#the-gate). Figures from `results.json`, `lane: "overall"`, run set
`p3-2026-07-31`.

**Weakest point.** The tier that passes is the tier where the comparator collapsed: `baseline-generic`
on haiku left 107 of its 137 usability claims unresolvable, and of the 30 that did resolve, none
landed within tolerance of any of the 7 planted defects. [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
records that the skill "passes substantively on haiku, with its comparator's collapse on that tier
published beside it." Under a deliberately
harsher match (exact truth node only, a diagnostic cut, not a published metric) ADR 0026 also found
the sonnet cell would dominate, 0.686 recall against 0.514 and 0.135 precision against 0.113, which
means the sonnet precision deficit under the published tolerance is an ancestor-window effect that
favors the high-volume baseline rather than a quality deficit in the skill. That diagnostic finding
does not change the recorded verdict, which rests on the published tolerance.

**What would flip it.** A haiku re-run in which the baseline stops collapsing, or a sonnet re-run
in which the skill's precision clears the baseline's. The 2026-09-15 re-measurement, below, tested
the second possibility and did not find it.

**Dated caveat.** Run `34917728793` (2026-09-15) re-ran both arms of the sonnet cell through the
shipped harness at k=5. Read two separate facts from it. First, against its own fidelity-gate band,
both gated figures land inside: `recall_location` 0.800 against a band of [0.771, 0.943], and
`precision_location` 0.169 against [0.153, 0.183]
([ADR 0031](../../docs/internal/decisions/0031-fidelity-gate-acceptance-band.md)). Second, within
that same re-run, the skill still trails the re-run baseline on both location metrics: recall 0.800
against the baseline's 0.857, precision 0.169 against 0.194. Both gaps are smaller than the spread
either arm shows across its own five repetitions, so the re-run confirms that the sonnet cell does
not qualify. Neither fact changes this verdict or feeds a published number.
[ROADMAP.md](../../ROADMAP.md)'s "Known limitations" section states the consequence plainly: the
skill "ships qualified through Haiku, not unconditionally."

**History:** [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
for the ruling and the ancestor-window diagnostic; [`bench/results/README.md`, "Core skills: S-05
AC-6"](README.md) for the narrative form; [ADR 0031](../../docs/internal/decisions/0031-fidelity-gate-acceptance-band.md)
for the 2026-09-15 re-measurement.

## critique-docs 0.1.0

**Verdict: SHIP, on precision dominance at equal recall.** At location level, `critique-docs` and
the frozen baseline find exactly the same planted defects on both tiers: 28 of 30 on haiku, both
sides, and 30 of 30 on sonnet, both sides. The recall half of the gate is therefore tied, not won.
What separates the two conditions is precision: at that equal recall the skill emits 32 claims on
haiku where the baseline needs 102 (0.875 against 0.275), and 30 claims on sonnet where the
baseline needs 126 (1.000 against 0.238). Figures from `results.json`, `lane: "overall"`, run set
`p3-2026-07-31`. The claim this skill can make in public is a precision claim: it ships because it
finds the same defects the baseline finds while saying almost nothing else, not because it finds
more.

**Weakest point.** The corpus behind this row is 6 distinct planted defect types across 3 seeded
artifacts, not 30 independent trials; the sonnet row's 30 of 30 is the same 6 defects found
identically across all 5 runs. The judged lane supplies roughly half this skill's own recall
(0.433 on haiku, 0.500 on sonnet, per the per-lane table in [`bench/README.md`](../README.md)), so
the scripted lane is not the whole story.

**What would flip it.** A recall figure that fell below the baseline's rather than tying it, or a
precision advantage that narrowed to nothing. Neither is close in this run set.

**Dated caveat.** Run `38673837025` (2026-10-14, sonnet) re-measured this cell through the current
harness. `recall_location` landed inside its band, exactly at 1.000. `precision_location` landed
outside a band of zero width, because `critique-docs` on sonnet scored 1.000 in every one of its
five committed repetitions, which ADR 0031 had already called "maximally discriminating and
useless as a gate, because a single malformed envelope fails it". The one stray claim behind this
miss is one judged finding, in 20 envelopes, that matched no planted defect; ADR 0031 records it as
a miss and states plainly that it "is not read as evidence about fidelity."

**History:** [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
for the location-level ruling and the recall-tie finding; [`bench/results/README.md`, "The baseline
comparison, honestly measured"](README.md) for the narrative form; [ADR 0031](../../docs/internal/decisions/0031-fidelity-gate-acceptance-band.md)
for the 2026-10-14 re-measurement.

## critique-microcopy 0.1.0

**Verdict: SHIP, both tiers, both metrics, by strict dominance.** Location recall is 0.920 against
the baseline's 0.813 on haiku and 0.960 against 0.840 on sonnet; location precision is 0.831
against 0.581 and 0.911 against 0.481. The gate is met literally, with no dominance argument
needed. Figures from `results.json`, `lane: "overall"`, run set `p3-2026-07-31`.

**Weakest point.** The location-level cut improves this skill's own criterion-level numbers (recall
0.840 to 0.920 on haiku, 0.920 to 0.960 on sonnet), showing that a handful of its findings land on
the right string under the wrong criterion ID. That is a real, small rubric-labeling gap: 6 of 75
planted defect instances on haiku and 3 of 75 on sonnet.

**What would flip it.** Nothing in this run set.

**Dated caveat.** Run `38683363024` (2026-10-14, sonnet) re-measured this cell through the current
harness. Both gated figures land inside their fidelity-gate bands:
`recall_location` 0.960 against [0.933, 0.987], and `precision_location` 0.900 against [0.887,
0.935]. The frozen baseline moved further than the skill did in the same run, and
[ADR 0031](../../docs/internal/decisions/0031-fidelity-gate-acceptance-band.md) records the
consequence worth naming: the baseline's `recall_location` rose to 0.987 (74 of 75), so the skill's
own 72 of 75 now trails the in-run baseline. ADR 0031 states this as "the baseline rose; the skill
did not fall," and it changes no published number and no verdict.

**History:** [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
for the location-level ruling; [`bench/results/README.md`, "The baseline comparison, honestly
measured"](README.md) for the narrative form; [ADR 0031](../../docs/internal/decisions/0031-fidelity-gate-acceptance-band.md)
for the 2026-10-14 re-measurement.

## critique-argument 0.1.0

**Verdict: SHIP, both tiers, both metrics; the thinnest consistency margin in the slate.** Location
recall is 0.825 against the baseline's 0.525 on haiku and 0.775 against 0.725 on sonnet; location
precision is 0.579 against 0.189 and 0.470 against 0.228. The gate is met literally on both tiers.
Figures from `results.json`, `lane: "overall"`, run set `p3-2026-07-31`.

**Weakest point.** Haiku consistency is 0.371, clearing the 0.309 floor by only +0.062, the
thinnest margin anywhere in the slate; a k=5 sample at that margin is not distinguishable from
sitting at the floor. This skill is also less consistent on haiku than the unrubricked baseline
prompt, 0.371 against 0.600, though [`bench/results/README.md`, section 2](README.md) notes that
comparison is not like-for-like: a baseline finding carries one fixed criterion, so two baseline
findings agree whenever their locations agree, while two skill findings must agree on criterion
and location, a strictly harder predicate. Separately, at criterion level, precision falls as the
tier strengthens (0.544 on haiku to 0.470 on sonnet) while recall stays flat at 0.775. Over the same
step, clean-artifact findings per run rise from 1.200 to 2.600. The stronger model makes more
unplanted claims rather than finding more planted defects.

**What would flip it.** A re-run in which haiku consistency lands below 0.309. That is the single
figure in this run set that a different set of five runs could plausibly move.

**Dated caveat.** Run `38678419907` (2026-10-14, sonnet) re-measured this cell through the current
harness. `recall_location` landed inside its band, on the upper bound. `precision_location` landed
outside it, above the band, by 0.032 against a band 0.066 wide, which
[ADR 0031](../../docs/internal/decisions/0031-fidelity-gate-acceptance-band.md) reads as triggering
investigation, not failure, since the miss is less than half the band's width. No figure in this
re-run shows the skill finding fewer defects.

**History:** [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
for the location-level ruling and the margin finding; [`bench/results/README.md`, section 2](README.md)
for the baseline consistency comparison and its caveat; [ADR 0031](../../docs/internal/decisions/0031-fidelity-gate-acceptance-band.md)
for the 2026-10-14 re-measurement.

## critique-forms 0.1.0

**Verdict: SHIP, decisive on haiku, a near-tie on sonnet.** The [N2 (critique-forms) spec](../../docs/internal/release-plans/_unassigned/N2_critique-forms/spec.md)'s
AC-12 names the same baseline test as AC-6 and AC-7 and points its consistency half at the floor in
force on the approval day, which [ADR 0037 (the critique-forms ship verdict)](../../docs/internal/decisions/0037-critique-forms-ship-verdict.md)
records as the single 0.309 floor, unchanged by [E26 (calibrate a per-lane consistency threshold)](../../docs/internal/backlog/enhancements.md)
at the time. On haiku, location recall is 0.933 against the baseline's 0.438 and location precision
is 0.458 against 0.287: a decisive pass. On sonnet, recall is 0.905 against 0.819 and precision is
0.317 against 0.303, a near-tie: the skill wins precision in 3 of 5 repetitions at the committed
tolerance and in all 5 under the stricter exact-node cut [ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
defines. AC-12 needs one qualifying tier and haiku clears it with no overlap. Figures from
`results.json`, `lane: "overall"`, run set `bench-2026-10-03`.

**Weakest point.** The scripted lane carries nearly all of this result: `checks.py` alone finds 18
of 21 seeded defects with no model involved, while the judged lane names only 4 of its 15 seeded
instances on each tier, all four under one criterion. On sonnet the baseline is more consistent
than the skill, 0.718 against 0.651; the baseline is not gated on consistency, so this changes no
verdict, but ADR 0037 publishes it rather than letting a reader find it first. The sonnet precision
margin is measured, in [`variance.json`](variance.json), to lie inside repetition noise: forms'
band is [0.288, 0.346] and the baseline's is [0.280, 0.322], and the two overlap.

**What would flip it.** A haiku result that fell to the baseline's level, since haiku is the only
tier carrying the verdict without qualification. Nothing in this run set is close to that.

**History:** [ADR 0037](../../docs/internal/decisions/0037-critique-forms-ship-verdict.md) for the
full ruling, its six verification checks, and what it does not establish; [ADR 0036](../../docs/internal/decisions/0036-experimental-status-until-ship-verdict.md)
for why the skill was registered `experimental` until this verdict and moved to `active` after it.

## What "beats baseline" is worth here

Every baseline row in the criterion-level cut reads recall 0.000 and precision 0.000, in every
domain, on both tiers. That is not an empirical finding about the generic prompt; it is a
structural property of how the bench matches claims to defects.

`bench/metrics/match.py` matches a claim to a planted defect only when the claim's criterion string
equals the defect's and the locations resolve to a hit. `bench/baseline/postprocess.py` assigns
every baseline finding the fixed criterion `BASELINE-GENERIC`, because the baseline has no rubric
to cite. No manifest anywhere in the corpus plants a defect under that criterion. The baseline's
criterion-level recall and precision are pinned at exactly 0.000 by construction, and no baseline
response, however good, could score otherwise.

The criterion-level comparison therefore discriminates nothing among skills: any nonzero recall
clears it. The location-level comparison, read in [The gate](#the-gate), is the fair one, because
it is the first comparison in this run set a skill could actually have lost, and
[ADR 0026](../../docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md)
is the record of what changed when the gates were re-read against it.

The criterion-level comparison is still informative on two measures that never depended on
criterion matching: the clean-artifact false-positive rate (the baseline emits 5.000 to 13.000
findings per run on artifacts with nothing planted, against 0.000 to 9.800 for the seven skills)
and the count of unresolvable locations (up to 107 of 137 baseline claims in one cell could not be
resolved to a location at all). Those two comparisons are like-for-like at criterion level, and the
full per-cell figures are generated into [`../README.md`](../README.md).

## Judged-lane figures

Since `results.json` reached results version 1.2.0, the file carries a `judged` and a `scripted`
entry per cell beside the `overall` entry every verdict above is read from. The recipe this section
once described, filtering an `overall` cell's findings by lane and rescoring them by hand, is
obsolete: the three lanes are now each a committed, machine-checked number, and
[`bench/README.md`](../README.md)'s per-lane table prints `recall`, `precision`, `consistency` and
`severity agreement` for the judged and scripted lanes of every skill, run set by run set.

[ADR 0038 (consistency threshold v2)](../../docs/internal/decisions/0038-consistency-threshold-v2-per-tier-floors.md)
states how each lane is treated now: the scripted lane has an expected consistency of 1.000,
reported and not gated until [E73 (make the merge step run the scripted lane itself)](../../docs/internal/backlog/enhancements.md)
closes the transport defect that keeps some scripted-lane cells below it; the judged lane publishes
per cell as a diagnostic, with no threshold; and the gating floor is computed on the overall lane
only, per tier, as [The gate](#the-gate) states above.
