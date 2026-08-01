# 0026 - Location-level re-examination of the baseline gates: three stretch SHIPs stand, one core skill fails AC-6 on the merits

## TL;DR
- **Decision:** for run set `p3-2026-07-31`, the **location-level** cut (`recall_location`, `precision_location` in [`bench/results/results.json`](../../../bench/results/results.json), results version 1.1.0) is the reading of "beats the frozen baseline" that the [S-05 (skills slate)](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) AC-6 and AC-7 gates are judged on substantively. The criterion-level cut those criteria are literally written against is retained as the primary per-skill metric and as the formal pass condition, but it cannot fail, so it cannot gate. A skill clears the substantive reading by meeting AC-6 literally (higher recall at equal-or-better precision) or by stated dominance (no worse on either metric, strictly better on one).
- **Verdicts:** all three stretch skills are **re-affirmed SHIP** under AC-7; `critique-docs` ships on a precision-dominance argument at *equal* recall, not on the recall win originally recorded. `critique-clarity` and `critique-usability` **pass** AC-6 substantively. **`critique-accessibility` fails AC-6 substantively on both tiers and on both metrics** (location recall 0.176 against the baseline's 0.376 on haiku, 0.306 against 0.776 on sonnet; location precision 0.158 against 0.258 and 0.202 against 0.293). That is a core-skill release blocker whose remedy AC-6 itself names; this ADR records the failure and hands the halt-or-iterate choice to the release owner rather than making it.
- **Why:** the criterion-level baseline is pinned at exactly 0.000 recall and 0.000 precision by construction, so the condition "beats baseline" was satisfied by any nonzero number and discriminated nothing. A gate that cannot fail is not a gate, and a verdict resting on it is not a verdict. The location-level cut is computed from the same 460 committed envelopes under the same tolerance rules, so re-reading the gates cost no new measurement and changed no evidence.
- **Status:** Accepted (2026-07-31). **Amended 2026-08-01: the escalated core failure is discharged,
  and one of this ADR's twelve gated cells no longer reads as recorded here.** See
  [0028 - Post-calibration verdict: critique-accessibility 0.1.1 clears AC-6 on re-measurement](0028-post-calibration-verdict-accessibility-clears-ac-6.md).
  The `critique-accessibility` rows in the twelve-cell table below are the 0.1.0 measurement and stay
  correct as such; they are no longer the current state of that skill. Every other ruling here,
  including all three stretch re-affirmations and `critique-usability`'s single-tier pass, stands
  unmodified and unaffected.

- **Status:** Accepted, amended by [0028](0028-post-calibration-verdict-accessibility-clears-ac-6.md)
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, P3 verdict-review pass (Claude)

## Builds on

- [0022 - Consistency floor for stretch gating: 0.309, overall lane](0022-consistency-floor-overall-lane-min-core.md), which set condition 2 of the stretch gate. This ADR **amends how 0022's floor is applied, not the floor itself**: 0022 settled the consistency half and explicitly left "the baseline-win half is assessed separately in `verdicts.md`". That half is what is re-examined here. The floor stays 0.309, on the overall lane, from `critique-clarity` on haiku, unmodified, and every consistency figure in the run set is untouched by the rescore.
- [0015 - Location tolerance keyed on artifact type](0015-location-tolerance-per-artifact-type.md), whose per-artifact-type tolerance is applied unchanged by the location-level match. Nothing about the tolerance rules was altered to produce these numbers.
- [0023 - v0.1.0 measurement basis](0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md), which fixes the run set, the two pinned tiers, and k=5 that every number below is read from.

## Context and problem statement

[`bench/results/verdicts.md`](../../../bench/results/verdicts.md), as first written, shipped all three stretch skills against a two-part gate whose first condition was "higher seeded-defect recall than the frozen `baseline-generic` prompt at equal-or-better precision, on at least one pinned tier". The same file then said, in its own words, that this condition "is satisfied by any skill that scores above zero" and "discriminates nothing among the three stretch skills", because `bench/baseline/postprocess.py` stamps every baseline finding with the fixed criterion `BASELINE-GENERIC`, no manifest plants a defect under that criterion, and `bench/metrics/match.py` required criterion equality. The baseline's recall and precision were arithmetic, not measurement.

The 2026-07-31 rescore removed that obstacle without disturbing the evidence. `match_claims_to_defects` gained an `ignore_criterion` mode, `score_artifact_location` was added beside `score_artifact`, and `results.json` (results version 1.1.0) now carries `recall_location` and `precision_location` for every entry, skill and baseline alike, computed from the same 460 committed envelopes, under the same per-artifact-type tolerance, with no new runs and no envelope modified. Every field that existed before the rescore is byte-identical.

That produces the first comparison in this run set that a skill could have lost. Three of them did lose something. The question this ADR settles is what the recorded verdicts should be once the gates are read against a comparison that can fail.

The twelve gated cells, location-level, from `results.json`:

| Skill | Tier | Recall (loc) | Baseline (loc) | Precision (loc) | Baseline (loc) | Substantive reading |
|---|---|---|---|---|---|---|
| critique-clarity (core) | haiku | 0.780 | 0.540 | 0.419 | 0.329 | pass, dominates |
| critique-clarity (core) | sonnet | 0.890 | 0.880 | 0.434 | 0.335 | pass, dominates |
| critique-accessibility (core) | haiku | **0.176** | **0.376** | **0.158** | **0.258** | **fail** |
| critique-accessibility (core) | sonnet | **0.306** | **0.776** | **0.202** | **0.293** | **fail** |
| critique-usability (core) | haiku | 0.800 | 0.000 | 0.231 | 0.000 | pass, dominates |
| critique-usability (core) | sonnet | 0.857 | 0.829 | 0.169 | 0.181 | no pass on this tier |
| critique-docs (stretch) | haiku | 0.933 | 0.933 | 0.875 | 0.275 | tie on recall, dominates overall |
| critique-docs (stretch) | sonnet | 1.000 | 1.000 | 1.000 | 0.238 | tie on recall, dominates overall |
| critique-microcopy (stretch) | haiku | 0.920 | 0.813 | 0.831 | 0.581 | pass, both metrics |
| critique-microcopy (stretch) | sonnet | 0.960 | 0.840 | 0.911 | 0.481 | pass, both metrics |
| critique-argument (stretch) | haiku | 0.825 | 0.525 | 0.579 | 0.189 | pass, both metrics |
| critique-argument (stretch) | sonnet | 0.775 | 0.725 | 0.470 | 0.228 | pass, both metrics |

## Decision drivers

- **A gate that cannot fail is not a gate.** The criterion-level baseline scores 0.000 in six domains on two tiers, in every cell, by construction. Continuing to record "beats baseline, both tiers" as the reason three skills ship, when the comparator was pinned at zero by a string-equality rule, would be publishing a conclusion the evidence cannot carry. The library's whole claim is that it publishes its own performance rather than asserting it.
- **The location-level cut is the fair comparison and costs nothing to apply.** Same envelopes, same corpus, same tolerance, criterion equality dropped from the predicate on both sides. It answers the one question the criterion-level metric cannot ask of a rubric-less prompt: did either condition point at the right place at all.
- **The criterion-level cut is still the primary per-skill metric and is not demoted.** Naming a defect under the criterion the rubric assigns it is what a rubric-cited critique library sells. Location-level scoring is deliberately blind to whether the finding says anything true about the place it names; it credits a claim for landing near a planted defect while describing something else entirely. It is the right instrument for a cross-condition comparison and the wrong one for a per-skill quality claim, which is why both cuts are committed side by side rather than one replacing the other.
- **AC-6 and AC-7 are frozen text and this ADR does not edit them.** Read literally, both are written against the methodology's recall and precision, which are criterion-level, and every cell passes them as written. Recording a formal pass and a substantive failure in the same breath is uncomfortable and it is the honest state of the evidence. The alternative, quietly reinterpreting a frozen acceptance criterion so its verdict changes, is worse.
- **The core failure has a remedy already specified, and it is not a measurement decision.** [S-05](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)'s Requirements section makes a core skill failing to beat baseline "a release blocker for core", and AC-6 names the alternatives: iterate within P3, or halt with a handover diagnosis. Choosing between iterating, halting, and shipping with the failure published as measured is a release decision for the owner. De-listing a core skill from `library.json` on the strength of a re-scored metric would also contradict S-05's own rule that core skills ship regardless of first-pass numbers with those numbers published.
- **The verdict has to survive an attempt to break it.** The strongest available objection to the accessibility failure is that [0015](0015-location-tolerance-per-artifact-type.md)'s `html` tolerance credits a claim resolving to an ancestor of the truth node at distance 1 or 2, which flatters a high-volume emitter naming container elements. That objection was tested, not waved away, and it does not survive: see the probe below.
- **Nothing here should require trusting the judge.** Every gating number is in a committed `results.json` and reproducible with the committed CLI. The one set of figures that is not, the ancestor-window probe, ships with the exact script that produced it.

## The ancestor-window probe (adversarial re-check, diagnostic only)

Not a published metric and not a gate input. It exists to test whether the two `html` domains' location-level results are an artifact of the tolerance window. Cut B replaces `bench/metrics/resolve_html.is_hit` with a predicate that credits a claim **only** when it resolves to the truth node itself, no ancestor and no descendant credit, which is strictly harsher than any tolerance this repository defines. Same envelopes, same everything else, run against the documented 460-run grid:

| Domain | Tier | Condition | Recall A (committed) | Recall B (exact node) | Precision A | Precision B |
|---|---|---|---|---|---|---|
| accessibility | haiku | baseline-generic | 0.376 | 0.212 | 0.258 | 0.145 |
| accessibility | haiku | critique-accessibility | 0.176 | 0.176 | 0.158 | 0.158 |
| accessibility | sonnet | baseline-generic | 0.776 | 0.588 | 0.293 | 0.222 |
| accessibility | sonnet | critique-accessibility | 0.306 | 0.224 | 0.202 | 0.147 |
| usability | haiku | baseline-generic | 0.000 | 0.000 | 0.000 | 0.000 |
| usability | haiku | critique-usability | 0.800 | 0.486 | 0.231 | 0.140 |
| usability | sonnet | baseline-generic | 0.829 | 0.514 | 0.181 | 0.113 |
| usability | sonnet | critique-usability | 0.857 | 0.686 | 0.169 | 0.135 |

What it shows:

- **The objection is real.** The window supplies 14 of the baseline's 32 accessibility matches on haiku and 16 of its 66 on sonnet, against 0 of 15 and 7 of 26 for the skill. `critique-accessibility` gets almost no credit from tolerance: when it resolves at all, it resolves precisely. Its problem is that it resolves rarely, 71 of 95 haiku claims and 65 of 129 sonnet claims being unresolvable.
- **The objection does not rescue the verdict.** Under the harshest cut available the baseline still out-recalls the skill on both tiers, 0.212 against 0.176 and 0.588 against 0.224. The skill takes the precision half on haiku under cut B (0.158 against 0.145) but AC-6 asks for higher recall at equal-or-better precision, and recall is the half it loses under every cut. There is no reading of this run set in which `critique-accessibility` beats the baseline.
- **It changes the reading of one usability cell in the skill's favour.** `critique-usability`'s only substantive shortfall, sonnet precision 0.169 against 0.181, reverses under cut B (0.135 against 0.113) together with recall (0.686 against 0.514). Its published sonnet precision deficit is an ancestor-window effect, not a quality deficit. This does not change the verdict, which already passed on haiku, but it does mean the sonnet cell should not be quoted as evidence against the skill.

Reproduce it by monkeypatching `resolve_html.is_hit` to `any(c == truth_idx for c in resolved.candidates)` and calling `bench.metrics.__main__.build_results` over the documented steering-excluded grid, once before the patch and once after. It writes nothing.

## Considered options

1. **Judge both gates on the location-level cut, re-affirm the three stretch SHIPs, record the core failure and escalate it (chosen).**
2. **Leave the verdicts on the criterion-level reading and publish the location-level numbers as context.** Rejected. That is what the state before this ADR amounted to, and it means the recorded reason three skills ship is a comparison against zero. It also leaves `critique-docs`'s file saying it beats the baseline on recall when it exactly ties on the only cut where recall could be lost.
3. **Flip `critique-docs` to HOLD for failing the recall clause at location level.** Rejected, and it was the closest call in this ADR. Its recall does not exceed the baseline's on either tier; it equals it, 28 of 30 and 30 of 30 on both sides. But it reaches that recall with 32 and 30 claims against the baseline's 102 and 126 (precision 0.875 and 1.000 against 0.275 and 0.238), emits 0.000 findings per run on the clean artifact against 5.000 and 6.200, and is the most repeatable cell in the slate at 0.842 and 1.000 consistency. It is no worse on any like-for-like measure and better by factors of three to four on several. Holding the quietest, most precise, most repeatable skill in the library for tying a comparator that sprays would be a gate punishing the behaviour it exists to encourage. The dominance argument is stated explicitly in `verdicts.md` and in the summary table so nobody has to infer it, and the recall tie is stated with it.
4. **Flip `critique-usability` to a core failure for losing sonnet precision.** Rejected. AC-6 asks for a pass on at least one pinned tier and haiku is an unambiguous dominance (0.800 against 0.000 recall, 0.231 against 0.000 precision). The probe above also shows the sonnet precision deficit is a tolerance artifact that reverses under a stricter match. The caveat that its qualifying tier is the tier where the comparator collapsed is published rather than resolved.
5. **De-list `critique-accessibility` from `library.json` components, mirroring the stretch-skill remedy.** Rejected as outside this pass's authority and contrary to S-05, which says core skills ship regardless of first-pass numbers with the numbers published, and which routes a core baseline failure to a release halt with a handover diagnosis rather than to component surgery. The failure is recorded, the diagnosis is written, the decision is escalated.
6. **Re-run the accessibility domain before ruling.** Rejected for this pass. The envelopes are immutable evidence and a re-run would not be comparable to the frozen run set; more to the point, the failure is not marginal (0.306 against 0.776 on sonnet is the largest gap in the run set) and it survives an adversarial re-cut, so no plausible sampling story closes it.

## Decision outcome

Option 1.

**Stretch, AC-7.** All three re-affirmed SHIP. `library.json` `components.skills` is unchanged, `plugin.json` was not regenerated, and the release gate was re-run as a check rather than because a manifest changed. `critique-microcopy` and `critique-argument` clear condition 1 literally at location level on both tiers. `critique-docs` clears it by stated dominance at equal recall, and its entry in `verdicts.md` now says so in those words. Condition 2 is unchanged for all three under [0022](0022-consistency-floor-overall-lane-min-core.md)'s 0.309 floor.

**Core, AC-6.** `critique-clarity` passes substantively on both tiers. `critique-usability` passes substantively on haiku, with its comparator's collapse on that tier published beside it. **`critique-accessibility` does not pass on either tier under any cut of this run set.** AC-6 reads a formal pass for it against the frozen criterion-level definition; that formal pass is recorded as worthless in the same place the failure is recorded, because the comparison behind it could not have failed.

**What is escalated, not decided here:** whether v0.1.0 halts, iterates `critique-accessibility` within P3, or ships with this published as measured. The evidence for that choice is complete and is in [`bench/results/README.md`](../../../bench/results/README.md); the choice is the release owner's.

**Scope.** Everything above is tied to run set `p3-2026-07-31`, its two model IDs, its corpus, and k=5. Re-measuring re-opens all of it.

## Consequences

**Positive:** the release gates are now judged on a comparison that a skill could lose, and one did. The recorded reasons the six skills ship are reasons rather than arithmetic. The single most consequential number in the release, `critique-accessibility` at 0.306 location recall against the baseline's 0.776, is on the results page in the first screen rather than buried, and the calibration lever for it (location emission and the reserved selector form of [0012](0012-location-grammar-freetext-plus-reserved-selector.md), not detection) is named. `critique-docs`'s public claim shrinks to what its numbers support.

**Negative:** the repository now carries a criterion that formally passes and substantively fails for the same skill, which is confusing to read and impossible to fix without unfreezing the spec. It also ships a release-blocking finding without resolving it, which leaves v0.1.0 in an explicitly undecided state at the last gate rather than at an early one. And the substantive standard applied here (literal AC-6, or stated Pareto dominance) is a judgement rule invented in this ADR rather than one pre-committed in the methodology, which is exactly the kind of after-the-fact rule-making the frozen-thresholds discipline exists to prevent. It is defensible only because the rule was written down before the numbers were applied to it and because it is strictly harder to clear than the criterion it replaces.

**Neutral:** the ancestor-window probe extends the labelled-derived-numbers exception that [0022](0022-consistency-floor-overall-lane-min-core.md) opened for judged-lane figures. It is confined to this ADR, kept out of the published results tables except as a one-line pointer, and shipped with its recipe.

## Open items handed to the orchestrator

- **The AC-6 halt-or-iterate decision for `critique-accessibility`.** ~~Blocking for v0.1.0. The three options are named in S-05 itself; the diagnosis is written; nothing else in the run set is waiting on it.~~ **Closed 2026-08-01.** The iterate branch was taken once, under the pre-committed lever list in [0027](0027-accessibility-location-emission-calibration.md), and the re-measurement recorded in [0028](0028-post-calibration-verdict-accessibility-clears-ac-6.md) clears the gate on both tiers and on both metrics. The diagnosis written above is what the fix was built from, and it held: the failure was location emission, not detection.
- **The `html` ancestor window flatters volume.** Quantified above for the first time. If location-level metrics survive into v0.2 as a gating cut, the window needs either an asymmetric rule (credit the truth node and descendants, not ancestors) or a published companion figure, because as it stands a skill can lose a precision comparison to a noisier condition purely on container-level credit, which is what happened to `critique-usability` on sonnet.
- **Methodology section 8 still defines recall and precision criterion-level only**, and now understates what the bench computes. It is frozen for this run; the update is flagged, not made. Same treatment as [0022](0022-consistency-floor-overall-lane-min-core.md)'s flag about the 0.7 placeholder, and the two should be resolved in one pass.
- **`bench/results/verdicts.md` is now a layered document**, original criterion-level entries plus a dated re-examination. It reads correctly and it will not survive a second amendment cleanly. Whoever writes the v0.2 verdicts should rewrite rather than layer again.

## Implementation sites

- [`bench/results/verdicts.md`](../../../bench/results/verdicts.md): carries the dated "Location-level re-examination (2026-07-31)" section, the amended summary table, and an in-place correction of the pre-rescore claim that a criterion-agnostic match "requires a new run set".
- [`bench/results/README.md`](../../../bench/results/README.md): unflattering-first lead, the AC-6 core-gate section, the AC-7 stretch-gate section, and a new limitation recording the ancestor-window effect.
- [`bench/results/results.json`](../../../bench/results/results.json): source of every gating number here, results version 1.1.0, unmodified by this ADR.
- `library.json` and `plugin.json`: **not changed.** No verdict flipped, and the core failure is escalated rather than actioned.
- [`docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md`](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) AC-6 and AC-7: frozen, not edited. The conflict between their criterion-level wording and the substantive reading applied here is recorded above, not resolved by editing them.
