# 0037 - Ship verdict for critique-forms 0.1.0: the measured case, and what it rests on

## TL;DR
- **Verdict:** SHIP, ruled by the maintainer on 2026-10-06. On run set `bench-2026-10-03`,
  `critique-forms` 0.1.0 meets the N2 spec's AC-12 (a recorded ship or hold verdict) literally on
  both pinned tiers. The judged-lane weakness below is published beside the pass.
- **The test:** higher seeded recall than the frozen `baseline-generic` prompt, at equal or better
  precision, on at least one pinned tier. The skill must also clear the consistency gate in force
  when the paid run was approved. Following [ADR 0026](0026-location-level-re-examination-of-baseline-gates.md),
  the comparison is read at location level, because the baseline's criterion-level figures are
  zero by construction.
- **The numbers:** on haiku, recall is 0.933 and precision 0.458, against the baseline's 0.438
  and 0.287. On sonnet, recall is 0.905 and precision 0.317, against 0.819 and 0.303.
  Consistency is 0.691 and 0.651, against the 0.309 floor.
- **What carries the result:** the scripted lane. `checks.py` alone finds 18 of the 21 seeded
  defects, with no model involved. The judged lane names 4 of its 15 seeded instances on each
  tier, and all four are one criterion.
- **Where it is weakest:** sonnet precision is a near-tie at the committed tolerance. Forms wins it
  in 3 of 5 repetitions. Under ADR 0026's exact-node cut, forms wins it in all 5.
- **Where the figures live:** every figure here is read from the run folder PR 69 committed. They
  join the top-level `results.json` in the change that moves the skill to `active`. See
  "Publication: two steps".

- **Status:** Accepted (2026-10-06)
- **Date:** drafted 2026-10-05, ruled 2026-10-06
- **Deciders:** Jonathan Prisant (the ruling: SHIP). Drafted by Claude from run `37091134037`'s 80
  envelopes.

## Builds on

- The [N2 (critique-forms) spec](../release-plans/_unassigned/N2_critique-forms/spec.md):
  Requirements 12 (both arms in one run set), Requirements 13 (the consistency gate), and AC-12.
- [0022 - Consistency floor: 0.309, overall lane](0022-consistency-floor-overall-lane-min-core.md),
  the gate applied here unchanged.
- [0026 - Location-level re-examination of the baseline gates](0026-location-level-re-examination-of-baseline-gates.md),
  which defines the location-level reading of "beats the baseline" and the exact-node probe.
- [0028 - Post-calibration verdict for critique-accessibility](0028-post-calibration-verdict-accessibility-clears-ac-6.md),
  whose verification checks this ADR repeats.
- [0036 - Experimental status until the ship verdict](0036-experimental-status-until-ship-verdict.md),
  which says what a ship or a hold ruling changes.

## Context

`critique-forms` reviews how easy an HTML form is to complete, against 24 FORMS criteria. Eighteen
criteria are checked by `scripts/checks.py` and six by the model. PR 60 (`11c4a65`) built it and
registered it `experimental`.

The maintainer approved one paid k=5 dispatch on 2026-10-02. GitHub's record of run `37091134037`
shows a `workflow_dispatch` from the `jprisant` account at 02:49 UTC on 2026-10-03, which is the
evening of 2026-10-02 in Pacific time. The run used commit `c442ba8`. It measured the skill and the frozen baseline on
`claude-haiku-4-5-20251001` and `claude-sonnet-5`, five runs per artifact, in one run set. That
satisfies Requirements 12. It also removes the caveat ADR 0028 had to carry, where the skill and
the baseline came from different run sets.

The forms corpus has four artifacts. Three are seeded with 21 defects in total: 18 under scripted
criteria and 3 under judged criteria (FORMS-FIELD-NECESSITY, FORMS-LABEL-POSITION and
FORMS-TOUCH-TARGET). The fourth, `forms-004`, is clean. At k=5 that gives 105 seeded instances per
tier: 90 scripted and 15 judged.

**The consistency gate.** Requirements 13 sets the gate as the rule in force on the approval day.
That is ADR 0022's 0.309 on the overall lane, unless E26 (a per-lane consistency threshold) had
replaced it. E26 has not landed as of 2026-10-05, so the gate is 0.309 whichever day counts.

## The numbers

Every figure in this table is read from
[`bench/results/runs-dispatch-37091134037/results.json`](../../../bench/results/runs-dispatch-37091134037/results.json),
which PR 69 copied byte for byte from result commit `c51eed8`. Overall lane throughout.

| Cut | Tier | critique-forms 0.1.0 | baseline-generic (frozen) |
|---|---|---|---|
| Recall (location) | haiku | **0.933 (98/105)** | 0.438 (46/105) |
| Recall (location) | sonnet | **0.905 (95/105)** | 0.819 (86/105) |
| Precision (location) | haiku | **0.458 (98/214)** | 0.287 (46/160) |
| Precision (location) | sonnet | **0.317 (95/300)** | 0.303 (86/284) |
| Recall (criterion) | haiku | 0.895 (94/105) | 0.000, by construction |
| Recall (criterion) | sonnet | 0.790 (83/105) | 0.000, by construction |
| Precision (criterion) | haiku | 0.439 (94/214) | 0.000, by construction |
| Precision (criterion) | sonnet | 0.277 (83/300) | 0.000, by construction |
| Consistency (overall) | haiku | 0.691 | 0.324 |
| Consistency (overall) | sonnet | 0.651 | 0.718 |
| Consistency (judged lane) | haiku | 0.317 | not applicable |
| Consistency (judged lane) | sonnet | 0.507 | not applicable |
| Clean-form findings per run | haiku | 3.6 (18/5) | 6.4 (32/5) |
| Clean-form findings per run | sonnet | 9.8 (49/5) | 13.0 (65/5) |
| Unresolvable claims | haiku | 0 of 214 | 44 of 160 |
| Unresolvable claims | sonnet | 0 of 300 | 18 of 284 |

**AC-12, the baseline half.** It is met literally on both tiers. Haiku is decisive: recall more
than doubles, and precision rises by 0.171. Sonnet is thin: 9 more instances found out of 105,
and precision higher by 0.014.

**AC-12, the consistency half.** 0.691 and 0.651 clear 0.309 by 0.382 and 0.342. Requirements 13
says in advance that this is weak evidence for this skill. Eighteen of 24 criteria are scripted
and repeat exactly, so the skill clears a pooled floor almost by construction. The judged-lane
figures, 0.317 and 0.507, are published beside the gate and do not gate.

**One unflattering figure.** On sonnet, the baseline is more consistent than forms, 0.718 against
0.651. The baseline is not gated on consistency, so this changes no verdict. It is stated here so
a reader does not find it first.

## Verification performed before proposing the verdict

Every check below writes nothing to the repository. Checks 3 to 6 produce derived figures that no
`results.json` carries. They are labelled as derived, as ADR 0022 and ADR 0026 did for theirs,
and "Reproducing the derived figures" gives the recipe.

**1. The run set's results reproduce field for field.** `build_results` in `bench/metrics/__main__.py`,
run over the 80 envelopes and the committed corpus, reproduces all 12 entries exactly.
`bench/corpus/`, `bench/metrics/` and `bench/baseline/` are unchanged between `c442ba8` and `main`.
`bench/baseline/` is unchanged since v0.1.6. Since v0.1.6, `bench/metrics/` changed only by PR 44's
lane split, whose code states its overall pass is byte-for-byte the older computation.

**2. The win is not a tolerance artifact.** ADR 0026's cut B credits a claim only when it resolves
to the seeded element itself, with no ancestor or descendant credit:

| Tier | Condition | Recall A (committed) | Recall B (exact node) | Precision A | Precision B |
|---|---|---|---|---|---|
| haiku | baseline-generic | 0.438 | 0.114 (12/105) | 0.287 | 0.075 (12/160) |
| haiku | critique-forms | 0.933 | **0.933** | 0.458 | **0.458** |
| sonnet | baseline-generic | 0.819 | 0.333 (35/105) | 0.303 | 0.123 (35/284) |
| sonnet | critique-forms | 0.905 | **0.905** | 0.317 | **0.317** |

Forms is unchanged to three decimals on both tiers, so every one of its matches lands on the
seeded element. Most of the baseline's matches come from the tolerance window. The sonnet
precision near-tie is therefore the window flattering a high-volume emitter. ADR 0026 found the
same effect for `critique-usability` on sonnet.

**3. The sonnet precision half holds in the pool, not in every repetition.** Each repetition pools
the four artifacts once:

| Tier | Forms wins recall | Forms wins precision (A) | Forms wins precision (B) |
|---|---|---|---|
| haiku | 5 of 5 | 5 of 5 | 5 of 5 |
| sonnet | 5 of 5 | 3 of 5 | 5 of 5 |

Sonnet loses precision in repetition 3 (19 of 71 against 18 of 58) and repetition 5 (20 of 65
against 19 of 57). Both are near-ties of the size the pooled figure shows.

**4. The scripted lane carries the result; the judged lane barely registers.** This splits recall
by the lane of each seeded defect's criterion:

| Seeded under | Tier | Forms, criterion | Forms, location | Baseline, location | Baseline, cut B |
|---|---|---|---|---|---|
| scripted (90) | haiku | 90 | 90 | 37 | 8 |
| scripted (90) | sonnet | 79 | 88 | 72 | 25 |
| judged (15) | haiku | 4 | 8 | 9 | 4 |
| judged (15) | sonnet | 4 | 7 | 14 | 10 |

All four judged matches are FORMS-TOUCH-TARGET. FORMS-FIELD-NECESSITY and FORMS-LABEL-POSITION are
never named under their own criterion in 20 runs. On sonnet, the generic prompt points at the
three judged defects more often than forms does, under both cuts.

**5. The script alone beats the baseline.** `checks.py` run once over the four artifacts scores
criterion-level recall 18 of 21 (0.857) and precision 18 of 32 (0.562), with no claim on the clean
form. That stricter cut is above the baseline's location-level figures on both tiers. It is a
counterfactual, not the shipped skill, which adds a judged lane with false alarms of its own.

**6. The envelopes are not always faithful to the script.** Each envelope's scripted-lane claims
were compared with `checks.py`'s output for the same artifact:

- Sonnet dropped 11 script claims in 6 of 20 runs, all on `forms-002` and `forms-003`. That is
  exactly the gap between 79 and 90 in check 4.
- Haiku labeled 10 judged-criterion findings "scripted" in 3 of 20 runs, all on the clean form.
  The criteria were FORMS-ACTION-HIERARCHY, FORMS-FIELD-NECESSITY and FORMS-TOUCH-TARGET.
- Haiku HTML-escaped the angle brackets in five location strings in one run (`forms-002`, r3).
  The element id still leads each string, so scoring is unaffected.

The defect's fingerprint is visible in the committed figures. A faithful scripted lane repeats
exactly, but its consistency reads 0.816 on haiku and 0.928 on sonnet. On the clean form, haiku's
scripted lane holds 10 claims where the script emits none.

The overall lane ignores lane labels, so haiku's mislabels move no gating figure. Sonnet's drops
do, and their effect was computed by adding the 11 claims back to the sonnet envelopes. Location
recall rises from 0.905 to 0.924 (97/105), and location precision falls from 0.317 to 0.312
(97/311). The sonnet pass holds either way. Criterion recall rises from 0.790 to 0.895, which
equals haiku's. The drops therefore explain the whole criterion-level gap between the two tiers.

The cause is inferred, not reproduced. `skills/_shared/merge.py` line 143 defaults a finding with
no `lane` to `"scripted"`. The assembler also takes the model's list of script findings rather
than running `checks.py` itself. Every skill that uses the shared assembler is exposed.
[E73 (make the merge step run the scripted lane itself)](../backlog/enhancements.md) records the
fix.

## Ruling

**SHIP**, ruled by the maintainer on 2026-10-06 on the analysis in this ADR. AC-12's baseline test
is met literally on both pinned tiers, decisively on haiku. The result survives the harshest match
the repository can express. It reproduces from the envelopes. The consistency floor is cleared on
both tiers.

The skill moves to `active` as ADR 0036 decision 3 sets out. E72 (the site's rubric attribution),
the precondition, was fixed first in PR 71.

## What this does not establish

- **That the skill's judgment beats a general model's.** Only 3 of 21 seeded defects are judged.
  Forms names two of them under their criterion in no run at all. On sonnet, the generic prompt
  finds them more often. The verdict says the skill as a whole beats a generic prompt. It says
  nothing in favour of the judged lane.
- **That the judged lane is quiet.** On sonnet, every one of the 9.8 clean-form findings per run
  comes from the judged lane. It is fewer than the baseline's 13.0, and it is still high.
- **That the result holds on real forms.** The corpus is generated, small, and id-rich: every
  seeded defect is anchored on an element id. The real-forms report (AC-10) measured the scripted
  lane's false alarms on real forms. It did not measure recall.
- **How large the sonnet margin is beyond noise.** ADR 0031 (the fidelity gate's acceptance band)
  measured no band for forms. Check 3 is the only spread this run set offers.

## Considered options

1. **SHIP on this evidence, with the judged-lane weakness published (chosen).** The stated
   test is met, and ADR 0028 established publishing a weakness beside a pass.
2. **HOLD until the judged lane improves.** This is the closest call. It reads AC-12 as a test of
   the skill's judgment, which the spec does not say. Requirements 13 already warned that the
   consistency gate would not test the judged lane either. A hold on these numbers would add a
   test after the result is known.
3. **SHIP, but claim the haiku tier only.** Rejected. AC-12 needs one tier, and both pass
   literally. Publishing the sonnet thinness serves a reader better than omitting the tier.
4. **Fix the assembler, then re-measure before ruling.** Rejected. It needs a new paid
   dispatch, and check 6 shows the defect cannot change either tier's outcome.

## Publication: two steps

`bench/README.md` states that no number appears in a document unless a committed `results.json`
carries it. E63 (dispatch run sets in `results.json`) records how the repository has handled a
dispatch run before. Three dispatch folders sit on `main` as committed evidence, quoted in prose,
with no `results.json` entry (PRs 38 and 50). That precedent splits publication into two steps.

1. **Commit the run folder to `main` as evidence. Done in PR 69.** That is
   `bench/results/runs-dispatch-37091134037/`: 80 envelopes, the run's own `results.json`, and 40
   baseline `.json.raw.txt` files, as all three earlier dispatch folders kept theirs. It is the
   committed `results.json` this ADR cites. It changed no published table and nothing on the site.
2. **Add the run set's entries to `bench/results/results.json`, in the change that acts on the
   ruling.** This step meets AC-11, and ADR 0036 decision 4 requires it on a hold as well as a
   ship. Three facts bear on it:
   - **The forms entries cannot collide.** E63's concern is a dispatch entry sharing `(skill,
     skill_version, model, domain)` with a p3 entry. No committed entry is in the `forms` domain,
     so all 12 forms entries are new keys.
   - **It puts forms on the site.** `loadResults` in `scripts/gen-site.mjs` renders every
     overall-lane entry on the receipts page and does not read `status`. ADR 0036's table of
     status readers does not list it. Taking this step before a ship ruling shows forms' figures
     on the site while the skill is `experimental`.
   - **The variance command still verifies.** `bench/variance.py --committed` checks only the
     cells its `--runs` folders produce. Run against a scratch `results.json` holding the forms
     entries, the `AGENTS.md` command verified 104 of 104 cell-metrics and wrote an identical
     `variance.json`. Forms gets no band until its folder is added to that command.

## Consequences

**On the SHIP ruling, which was made:** fix E72, then set `critique-forms` to `active` in
`library.json` and re-run every generator that reads `status`. Add the FORMS row to
`docs/reference/criterion-ids.md`. This ADR was accepted on the ruling itself. ADR 0036's status
line still reads "Proposed, accepted when PR 60 (the `critique-forms` build) merges". PR 60 merged
at 01:28 UTC on 2026-10-03, so update that line in the activation change.

**Had the ruling been HOLD:** the status would have stayed `experimental`. The figures would still
have published in the full grid, and the hold would have been recorded in `RELEASE-NOTES.md`, as
ADR 0036 decision 4 requires.

**Either way:** `bench/results/verdicts.md` is titled for the v0.1.0 stretch skills, and ADR 0026
said it would not survive another layer. Where readers find this verdict is decided at the
publication step, not here.

## Open items

- **E73 (make the merge step run the scripted lane itself),** filed in PR 67: run `checks.py`
  inside the merge step and assign lanes from `SKILL.md`'s `checks.scripted` list.
- **A judged-lane corpus addition.** Three judged seeds cannot measure a judged lane. More judged
  seeds, on an artifact without element ids, would test both weaknesses named above.
- **`golden-05`** (PR 60 question 10b), built from this run's judged findings.
- **ADR 0036's reader table** should gain `loadResults`, whichever way E63 is ruled.

## Reproducing the derived figures

Every check reads the committed `bench/results/runs-dispatch-37091134037/`. From the repository
root:

- **Check 1:** call `bench.metrics.__main__.build_results` on that directory and `bench/corpus`,
  with the run set and timestamp from the extracted `results.json`, and compare entries.
- **Check 2:** monkeypatch `bench.metrics.resolve_html.is_hit` to accept only a candidate equal to
  `_resolve_truth_node(doc, truth)`, then score every forms envelope with `score_artifact_location`.
- **Checks 3 and 4:** group the same per-envelope scores by repetition (the `-rN` file suffix), or
  by whether each defect's criterion is in `SKILL.md`'s `checks.judged` list.
- **Checks 5 and 6:** run `python skills/critique-forms/scripts/checks.py <artifact>` and compare
  its findings' `(criterion, location)` claims with each envelope's `lane: "scripted"` claims.
  For the restored figures, append each missing script finding to a copy of the sonnet envelope
  and score the copy with `score_artifact_location` and `score_artifact`.

## Implementation sites

- This ADR changes no file. The run folder landed in PR 69, and E72's fix in PR 71.
- The activation change carries out the ruling: `critique-forms` to `active` in `library.json`,
  the 12 entries into `bench/results/results.json`, the FORMS row in
  `docs/reference/criterion-ids.md`, every generator that reads `status` re-run, and ADR 0036's
  status line and reader table.
