# 0028 - Post-calibration verdict: critique-accessibility 0.1.1 clears AC-6 on re-measurement, and what that does not prove

## TL;DR
- **Decision:** on run set `cal1-2026-08-01`, `critique-accessibility` 0.1.1 **passes S-05 AC-6 substantively on both pinned tiers**, literally rather than by dominance argument: higher location-level recall *and* higher location-level precision than the frozen `baseline-generic` prompt. Location recall 0.988 against 0.376 on haiku and 0.965 against 0.776 on sonnet; location precision 0.875 against 0.258 and 0.672 against 0.293. The core release blocker [0026](0026-location-level-re-examination-of-baseline-gates.md) escalated is **discharged on evidence, not waived**.
- **Verdicts elsewhere:** unmoved. No baseline `.v2.json` parity envelope exists, `bench/baseline/` is untouched, and every baseline figure in the repository is the same committed number it was on 2026-07-31. The five other skills were not re-measured, no number of theirs changed, and the [0022](0022-consistency-floor-overall-lane-min-core.md) consistency floor keeps its value of 0.309 because `critique-clarity` set it and `critique-clarity` was not re-measured. All three stretch SHIPs stand on exactly the arguments [0026](0026-location-level-re-examination-of-baseline-gates.md) recorded.
- **Why it is believable:** the win survives the harshest match this repository can express (exact truth node only: 0.988 and 0.965, unchanged to three decimals), the skill's judged-lane *detection* rate is flat across the two versions (36 of 40 opportunities to 35 of 40), and the scripted lane, which supplies 13 of the 17 planted defects per pass, is byte-reproducible from committed code with no model in the loop.
- **What it does not prove:** the comparison spans two run sets, the cal1 run set has no provenance document, and the corpus is unusually friendly to the exact fix that was made. All three are recorded below and published in `bench/results/README.md`.
- **Status:** Accepted (2026-08-01).

- **Status:** Accepted
- **Date:** 2026-08-01
- **Deciders:** Jonathan Prisant, post-calibration judge pass (Claude)

## Builds on

- [0026 - Location-level re-examination of the baseline gates](0026-location-level-re-examination-of-baseline-gates.md), which produced the AC-6 failure this ADR answers, defined the substantive reading of the gate that is applied here unchanged, and defined the cut-B probe reused below. This ADR **amends 0026's escalated open item and one row of its twelve-cell table**; it does not disturb any other ruling in it.
- [0027 - critique-accessibility 0.1.1: the one permitted calibration is a location-emission fix](0027-accessibility-location-emission-calibration.md), which made the change and explicitly declined to claim a score for it. This ADR supplies the score.
- [0022 - Consistency floor: 0.309, overall lane](0022-consistency-floor-overall-lane-min-core.md), whose floor and whose published judged-lane diagnostic are both re-read against the new numbers and both found unmoved in what they gate.
- [0015 - Location tolerance keyed on artifact type](0015-location-tolerance-per-artifact-type.md) and [0023 - v0.1.0 measurement basis](0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md), applied unchanged. No tolerance rule, model pin, or k was altered to produce any number here.

## Context and problem statement

[0026](0026-location-level-re-examination-of-baseline-gates.md) recorded a core skill losing its baseline comparison on both tiers and both metrics, called that a release blocker under S-05 AC-6, and escalated the halt-or-iterate-or-ship choice rather than making it. The iterate branch was taken once, under a policy fixed before the diagnosis was read: one iteration, from a permitted lever list, with an ADR. [0027](0027-accessibility-location-emission-calibration.md) is that ADR and it deliberately claimed no new score, on the grounds that claiming one without measuring it is the failure mode this library exists to avoid.

This ADR is the measurement. The question it settles is narrow: **does 0.1.1 clear AC-6, and does anything else move.**

It is written as a judgement on a result that arrived looking too good. The pre-calibration figures were location recall 0.176 and 0.306; the post-calibration figures are 0.988 and 0.965. A jump of that size is the shape both a real fix to a total-failure mode and a rigged benchmark would have, and the second possibility was tested before the first was accepted.

## Decision drivers

- **A gate discharged by argument is not discharged.** [0026](0026-location-level-re-examination-of-baseline-gates.md) refused to reinterpret AC-6 to make a failure disappear. The same discipline forbids accepting a pass without checking that the numbers mean what they appear to mean.
- **The pre-committed lever list is the whole basis of the iteration's legitimacy.** The list was fixed before the diagnosis was read: scripted-check bug fixes, location-emission wording, severity-anchor wording, four-pass protocol emphasis, and measurement-parity fixes; deleting or weakening criteria, editing the corpus, and changing scoring to favour the skill forbidden outright. A pass obtained by a forbidden lever is worse than a recorded failure, so compliance had to be verified from the diff rather than taken from the ADR that describes it.
- **The failure has to stay visible after it is fixed.** A calibration that overwrites the row it fixed converts a results page into an advertisement. Both versions had to end up in the published tables, side by side.
- **What the result does not establish matters as much as what it does.** The corpus is generated, it is unusually id-rich, and the fix's first-choice anchor is an id. That is a family resemblance between how a defect is anchored and how the skill was told to cite it, which is exactly the risk `bench/results/README.md` already names in the abstract. Here it is concrete, and it belongs in the record whichever way the verdict goes.

## The numbers

Read from [`bench/results/results.json`](../../../bench/results/results.json), which now holds both run sets, distinguished by `skill_version`. Baseline figures are the frozen, unmodified 2026-07-31 ones.

| Cut | Tier | 0.1.0 (p3) | 0.1.1 (cal1) | baseline-generic (frozen) |
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

AC-6 asks for higher recall at equal-or-better precision on at least one pinned tier. It is met literally on both tiers and at both cuts, with the precision half won outright rather than merely tied, so no dominance argument is offered or needed. The criterion-level pass remains worth nothing on its own for the reason [0026](0026-location-level-re-examination-of-baseline-gates.md) established, and the location-level pass carries the verdict.

**Consistency and the R1 floor.** 0.625 and 0.808 against the [0022](0022-consistency-floor-overall-lane-min-core.md) floor of 0.309, cleared by wider margins than 0.1.0 cleared it. The floor's **value** does not move: it is `min(core-skill overall consistency)`, it was set by `critique-clarity` on haiku, and `critique-clarity` was not re-measured. Accessibility was never the cell that set it. No stretch skill's condition 2 changes. The judged-only cut that [0022](0022-consistency-floor-overall-lane-min-core.md) publishes as a non-gating diagnostic does move, 0.090 to 0.286 and 0.449 to 0.736, retiring what was the worst number in the run set; the lowest judged-only core cell is now `critique-clarity` on haiku at 0.150.

## Verification performed before accepting the result

Every check below writes nothing and changes no committed code. The two probes reproduce figures already published in [0026](0026-location-level-re-examination-of-baseline-gates.md) and [0022](0022-consistency-floor-overall-lane-min-core.md) for the 0.1.0 condition, which is what makes them trustworthy for the 0.1.1 condition.

**1. The permitted-lever list was honoured.** `python -m bench.generator verify --corpus bench/corpus` reports 53 files byte-identical and `leak-check` passes; `git status` shows no modification anywhere under `bench/corpus/`, `bench/metrics/`, `bench/baseline/`, `contract/`, or `bench/results/runs/`. The skill diff is confined to `_loc` and two new helpers in `checks.py` (location string composition only, no detection predicate and no threshold), the WCAG-1.4.4 descriptor wording, a "Naming a location" section and passes 1 and 2 of `SKILL.md`, a pointer in `references/WCAG.md`, the five golden examples' location strings, and version bumps. **No criterion was added, removed, re-scoped, or moved between lanes.**

**2. The committed p3 results reproduce byte-identically.** Scoring the steering-excluded p3 grid with the committed CLI reproduces all 24 pre-calibration entries exactly, field for field. This was checked because a merged `results.json` is only trustworthy if the half that was supposed to be untouched is provably untouched.

**3. The win is not a tolerance artifact.** Re-run under [0026](0026-location-level-re-examination-of-baseline-gates.md)'s cut B, which credits a claim only when it resolves to the truth node itself, with no ancestor and no descendant credit, and which is strictly harsher than any tolerance this repository defines:

| Tier | Condition | Recall A (committed) | Recall B (exact node) | Precision A | Precision B |
|---|---|---|---|---|---|
| haiku | baseline-generic | 0.376 | 0.212 | 0.258 | 0.145 |
| haiku | critique-accessibility 0.1.0 | 0.176 | 0.176 | 0.158 | 0.158 |
| haiku | critique-accessibility 0.1.1 | **0.988** | **0.988** | **0.875** | **0.875** |
| sonnet | baseline-generic | 0.776 | 0.588 | 0.293 | 0.222 |
| sonnet | critique-accessibility 0.1.0 | 0.306 | 0.224 | 0.202 | 0.147 |
| sonnet | critique-accessibility 0.1.1 | **0.965** | **0.965** | **0.672** | **0.672** |

Every baseline and 0.1.0 figure here matches the corresponding figure in [0026](0026-location-level-re-examination-of-baseline-gates.md) exactly. 0.1.1 is **unchanged to three decimals** between the two cuts: every one of its matches is an exact-node match, so it takes nothing at all from the ancestor window that [0026](0026-location-level-re-examination-of-baseline-gates.md) flagged as flattering high-volume emitters. The objection that ADR raised against the *baseline's* numbers cannot be raised against these.

**4. Detection did not improve, which is the point and also the answer to the sharpest objection.** On `accessibility-003`, whose four planted defects are all judged-lane criteria, the planted criteria were emitted at all (location ignored entirely) in **36 of 40** opportunities under 0.1.0 and **35 of 40** under 0.1.1. The skill did not start finding more; it started saying where. That is precisely the mechanism [0027](0027-accessibility-location-emission-calibration.md) predicted, and it is corroborated by the unresolvable-claim collapse, 71 of 95 to 3 of 96 and 65 of 129 to 0 of 122.

This check exists because of a real objection to [0027](0027-accessibility-location-emission-calibration.md)'s protocol-emphasis lever: `SKILL.md`'s new Pass 2 text names five judged criteria to sweep hardest, and **four of those five are exactly the four judged criteria this corpus plants defects under**, while none of the four unnamed judged criteria carries a planted defect. That is a fit to the test set. It is inside the permitted lever list ("four-pass protocol emphasis") and no corpus file was touched, so it is not a policy breach, but it is the kind of thing that should be found by a reviewer rather than discovered later. The flat detection rate is what stops it mattering: the emphasis bought no measurable detection, so removing it would not move the numbers AC-6 is decided on. It is published in `bench/results/README.md` and in `verdicts.md` regardless.

**5. The skill got quieter, not louder.** Claims fell from 129 to 122 on sonnet and clean-artifact findings per run fell from 1.800 to 1.200 and from 1.000 to 0.600. A skill gaming a location metric by spraying anchors would show the opposite on every one of those figures.

**6. The scripted lane is reproducible with no model in the loop.** Running committed `scripts/checks.py` locally over the committed corpus reproduces, byte for byte, every scripted finding in **39 of the 40** cal1 envelopes. The scripted lane supplies 13 of the 17 planted defects per pass, so the dominant contributor to these figures requires no trust in any harness at all. The one exception is recorded below.

## Decision outcome

**`critique-accessibility` 0.1.1 passes S-05 AC-6 substantively, on both pinned tiers.** The blocker [0026](0026-location-level-re-examination-of-baseline-gates.md) escalated is discharged. `library.json` `components.skills` membership is unchanged; only the component's version moved, which [0027](0027-accessibility-location-emission-calibration.md) records.

**No other verdict moves.** No baseline parity envelope was produced, so no baseline cell in any domain changed and no comparison involving the other five skills was recomputed against a different comparator. `critique-clarity` and `critique-usability` stand as [0026](0026-location-level-re-examination-of-baseline-gates.md) left them, including usability's pass on haiku only and the published caveat that its qualifying tier is the tier where the comparator collapsed. All three stretch skills stand, `critique-docs` still on precision dominance at equal recall.

**Both versions are published side by side.** `results.json` gained the two 0.1.1 entries and changed nothing else: the diff removes exactly two lines, `run_set` and `generated_at`. Finding this out required fixing a real defect in `bench/report.py`, which keyed each `(domain, model)` comparison cell by skill name alone and therefore **silently dropped** one of two entries for the same skill at different versions. Left unfixed, publishing the calibration would have deleted the 0.1.0 failure row from the table that recorded it, with no error and no warning. It now keys on `(skill, skill_version)` and renders a version column.

## What this does not establish

Three limits, all published in `bench/results/README.md` rather than kept here.

- **The comparison spans two run sets.** 0.1.1 is measured on `cal1-2026-08-01`; the baseline it beats is measured on `p3-2026-07-31`. Corpus bytes, model IDs and k are identical and the baseline condition is frozen by construction, so this is the intended comparison rather than a substitution. It is still not one simultaneous run set, and the sonnet baseline cell at 0.776 is the figure a re-run could most plausibly move. The haiku margin (0.988 against 0.376) is far too large for that to matter; the sonnet margin (0.965 against 0.776) is large but not immune.
- **The cal1 run set has no provenance document.** `bench/results/README.md` records that the 462 p3 envelopes came from a documented multi-agent workflow rather than from `bench/run_bench.py`, and that **the two mechanisms are not byte-equivalent**. No equivalent record exists for cal1, and `measurement-manifest.json`'s `calibration.cal1` block names corpus, models, k and staging but not the production mechanism. Six of the 40 cal1 envelopes carry round-number `run.timestamp` values, four of them exactly `00:00:00Z`, so those timestamps are not a record of when anything ran. A reader therefore cannot currently confirm that 0.1.0 and 0.1.1 were measured under the same harness. Checks 4 and 6 above bound the exposure and do not close it. **Writing the cal1 provenance record is an open item and it is the weakest link in this verdict.**
- **The corpus is unusually friendly to the specific fix.** 0.1.1's first-choice anchor is the element's own `id`, and every artifact in this generated corpus carries ids on the elements its defects are planted on. The double-quoted CSS-path fallback, which is what id-poor real markup would exercise, is barely reached. How much of the 0.176-to-0.988 gain survives on markup without ids is **not measured by this run set**. This is the generated-corpus limitation the results page already states in the abstract, in its sharpest concrete form.

One smaller defect found while verifying, affecting no scored figure: in `bench/results/runs-cal1/critique-accessibility/accessibility-001/haiku-r5.json` the WCAG-1.3.1 scripted finding's `fix` reads `Change this heading to <h3>` where committed `checks.py` emits `<h5>`. Criterion, severity, location, evidence and violation match exactly. A scripted-lane finding in a committed envelope is supposed to be bit-for-bit what the script produced and this one is not. Separately, `<h3>` is the substantively correct fix for an h2-to-h4 skip, so `checks.py`'s `<h5>` wording looks like a latent defect of its own. Neither is fixed here: the envelopes are immutable evidence, and `checks.py` is out of scope for a judging pass.

## Considered options

1. **Accept the pass, publish both versions side by side, and publish the three limits (chosen).**
2. **Accept the pass and replace the 0.1.0 rows.** Rejected. It is the single change that would most improve how the library looks and it would destroy the most valuable thing on the results page, which is a recorded failure with a correct diagnosis attached and a fix that vindicated it. The `report.py` collision would have done this silently if it had not been found.
3. **Reject the pass as unmeasured because the cal1 harness is undocumented.** Rejected, and it was the closest call. The provenance gap is real and is recorded as the weakest link. Against rejection: the scripted lane supplies most of the result and is reproducible from committed code with no harness at all; the judged lane's detection rate is flat, which is not the signature of a harness change; and the alternative to accepting is refusing a measured result on a documentation gap while the failing result it replaces came from a mechanism documented only slightly better. The right remedy is to write the provenance record, not to discard the measurement.
4. **Reject the pass because the Pass 2 emphasis list is corpus-shaped.** Rejected on the evidence rather than on the policy. The lever is permitted and the corpus was untouched, but that alone would not settle it, because a permitted lever aimed at the test set is still aimed at the test set. What settles it is that the emphasis produced no measurable detection change (36 of 40 to 35 of 40), so the numbers deciding AC-6 do not depend on it. The finding is published rather than argued away.
5. **Re-run the frozen baseline on cal1 for a single-run-set comparison.** Rejected. The baseline is frozen precisely so it cannot be re-rolled after seeing a skill's numbers, `bench/README.md` makes re-running it invalidate every published comparison, and the bounding-parity check that could have compelled a re-postprocess came back true. Re-running a frozen comparator to improve a comparison is the exact move the freeze exists to prevent.

## Consequences

**Positive:** the one core-skill release blocker in v0.1.0 is closed by measurement. The library now has a complete worked example of its own claimed method: publish an unflattering result, diagnose it, fix the diagnosed cause under a pre-committed constraint, re-measure, and publish both numbers. That example is worth more than the score. A silent row-dropping defect in the results reporter was found and fixed before it could delete a published failure.

**Negative:** the strongest result in the run set is also the one whose production mechanism is least documented, which is an uncomfortable pairing and the honest state of the evidence. `results.json` now holds two run sets in a format with one `run_set` field, which works only because the calibration happened to change a version number and would not work for two run sets of the same version. And `verdicts.md` is now a three-layer document, one layer past the point [0026](0026-location-level-re-examination-of-baseline-gates.md) predicted it would stop reading cleanly.

**Neutral:** the generated tables changed shape, gaining a version column in all three. Every number in them still comes from `results.json` and `--check` reports no drift.

## Open items handed to the orchestrator

- **Write the cal1 provenance record**, to the standard of `docs/internal/execution/P3-provenance.md`, naming the mechanism that produced the 40 envelopes and explaining the six round-number timestamps. This is the weakest link in the verdict above and the cheapest to close.
- **Measure the id-poor case before v0.2.** One accessibility artifact whose defect-bearing elements carry no `id` would tell the library how much of this gain is the CSS-path fallback and how much is the id shortcut. It is a corpus addition, which is why it was not done in this pass.
- **`results.schema.json` needs a per-entry `run_set`**, alongside the lane dimension [0022](0022-consistency-floor-overall-lane-min-core.md) already flagged. Resolve both in one v0.2 pass.
- **`verdicts.md` needs the rewrite [0026](0026-location-level-re-examination-of-baseline-gates.md) called for**, now overdue by one layer. It was not done here because rewriting the stretch verdicts while ruling on a core skill would mix two unrelated changes in one pass.
- **`checks.py`'s WCAG-1.3.1 fix wording appears to name the wrong heading level** (`<h5>` for an h2-to-h4 skip). A one-line defect, out of scope for a judging pass, and it would change golden examples and one committed envelope's expected content.
- **Methodology section 8 still defines recall and precision criterion-level only**, unchanged from [0026](0026-location-level-re-examination-of-baseline-gates.md)'s flag and still frozen.

## Implementation sites

- [`bench/results/results.json`](../../../bench/results/results.json): 26 entries, the 24 pre-calibration entries byte-identical and two 0.1.1 entries added; only `run_set` and `generated_at` changed.
- [`bench/results/README.md`](../../../bench/results/README.md): lead, unflattering numbers 1 to 5, the AC-6 section and its new post-calibration subsection, provenance, limitations, reproduction, and known issues.
- [`bench/results/verdicts.md`](../../../bench/results/verdicts.md): the dated "Post-calibration verdict (cal1, 2026-08-01)" section, the amended banner, and the amended summary paragraph about the core slate.
- `bench/report.py`: `_by_domain_model` re-keyed on `(skill, skill_version)`, `_find_baseline` added, and a version column in all three generated tables.
- `bench/README.md`: the generated results block, regenerated; `--check` reports no drift.
- [`0026`](0026-location-level-re-examination-of-baseline-gates.md) and [`0027`](0027-accessibility-location-emission-calibration.md): status amendments and the closure note on 0026's escalated open item.
- `bench/corpus/`, `bench/metrics/`, `bench/baseline/`, `contract/`, `bench/results/runs/`: **not changed.**
