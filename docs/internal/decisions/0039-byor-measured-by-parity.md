# 0039 - BYOR is measured by parity, on one flagship skill's own judged criteria

## TL;DR
- **Decision:** BYOR (bring your own rubric) is measured, not exempted. One flagship skill's own
  judged criteria are rewritten as a user-supplied rubric. The skill runs that rubric in BYOR mode on
  its existing corpus, and both paths are scored on the same criteria. The gap between them is
  published.
- **The flagship is `critique-microcopy`.** Its corpus seeds all 8 of its judged criteria, so a
  parity run tests the whole rewritten rubric.
- **The published claim carries a fixed caveat.** The path was measured on the flagship's own
  rubric, and a user's rubric is unmeasured.
- **The measured-only rule is unchanged.**
- **Ruled:** by the maintainer, on the method and the claim on 2026-10-23 and on the flagship on
  2026-10-24.
- **Status:** Accepted (2026-10-24). Closes E10.

- **Status:** Accepted
- **Date:** ruled 2026-10-23 and 2026-10-24, recorded 2026-10-25
- **Deciders:** Jonathan Prisant (the ruling). Drafted by Claude from the committed corpus manifests,
  each skill's `SKILL.md`, and `bench/results/results.json`.

## Builds on

- [Methodology section 3 (Bring Your Own Rubric)](../../explanation/methodology.md), status
  Provisional, which makes BYOR a mode of an existing skill rather than a skill of its own.
- [0031 - The fidelity gate's acceptance band](0031-fidelity-gate-acceptance-band.md), whose variance
  method is the natural source for a parity pass band.
- [0038 - Consistency threshold v2](0038-consistency-threshold-v2-per-tier-floors.md), which records
  that the current harness reads differently from the v0.1.0 figures.
- [E10 (rule how BYOR is measured)](../backlog/enhancements.md), which this ADR closes, and
  [E45 (build BYOR on one flagship skill)](../backlog/enhancements.md), which builds under it.

## Context and problem statement

ROADMAP's "Deliberately not doing" list rules out any skill that cannot be measured: "A skill that
cannot be measured against ground truth does not ship, regardless of how well-written its rubric is."

BYOR's criteria arrive at run time, from the user. The benchmark corpus is keyed by criterion ID, and
each seeded defect in a manifest names the criterion it breaks. A criterion that does not exist until
run time cannot have a seeded defect in advance. E10 asked whether BYOR is measured some other way,
or is exempt, and why. The v0.3.0 exit gate requires that ruling to be recorded, and it requires E45
to be measured under it.

Three facts bound the answer.

- **BYOR is a mode of a skill.** The skill applies the user's rubric under the same contract,
  severity scale and evidence rules. It marks every such finding `rubric_source: byor`, and the
  contract requires that mark on any criterion in the `BYOR-` namespace.
- **A BYOR criterion can only be judged.** The contract's lane enum is `scripted` and `judged`, and
  no script exists for a criterion that arrives at run time.
- **The invocation surface does not exist yet.** E45 records what it needs: a rubric-intake format,
  an extended critic contract, and one skill whose `SKILL.md` and checks path accept a user rubric.

## Decision drivers

- **The library is accountable for the path, not for the user's rubric.** Intake, operationalization,
  citation, location, severity and the envelope are the library's work. The quality of a rubric a user
  writes belongs to the user.
- **BYOR needs a published figure that can fail.** That is what the measured-only rule asks of
  anything that ships.
- **Keep the measured-only rule whole.** Exempting a mode would need the rule's wording amended.
- **Reuse the committed corpus and scorer.** A parity run needs no new generator domain.
- **The flagship's corpus must test the criteria being rewritten.** A rewritten criterion with no
  seeded defect is measured by nothing.

## Considered options

Three decisions, ruled in one walk.

**How BYOR is measured.**

1. **Parity (chosen).** The flagship's own judged criteria are rewritten as a BYOR file and scored
   against the native path on the same corpus. The new code is a map from each `BYOR-` ID to the
   native ID it rewrites, applied before scoring, plus one paid run.
2. **Exempt BYOR as a mode, and amend the rule to say so.** Rejected. It changes a published rule
   and gives BYOR no figure at all.
3. **A probe rubric.** A committed synthetic rubric, such as a fictional house style guide, with its
   own seeded corpus from a new generator domain. Not taken. It costs a generator domain and a corpus,
   and it cannot compare the BYOR path with the native one. It stays the fallback if a rubric that
   reads more like a real style guide is wanted.
4. **A kit for users to measure their own rubrics.** Deferred. [E57 (standalone
   benchmark)](../backlog/enhancements.md) would package it, at v0.4.0 or later, and it measures
   nothing until a user runs it.

**Which flagship.** The figures below rescore each skill's committed `p3-2026-07-31` judged-lane
findings against only the seeded defects on its judged criteria, with the committed scorer. The
published judged-lane recall cannot be reused for this, because its denominator counts scripted
defects too.

| Skill | Judged criteria | Seeded defects on judged criteria | Judged recall, haiku / sonnet | Judged precision, haiku / sonnet |
|---|---|---|---|---|
| `critique-microcopy` | 8 of 14 | 8 | 28/40 / 34/40 | 28/48 / 34/44 |
| `critique-docs` | 6 of 9 | 3 | 13/15 / 15/15 | 13/17 / 15/15 |
| `critique-clarity` | 8 of 23 | 5 | 13/25 / 23/25 | 13/118 / 23/141 |
| `critique-usability` | 17 of 20 | 4 | 10/20 / 15/20 | 10/99 / 15/153 |

Each recall denominator is the number of seeded defects on judged criteria times k=5.

1. **`critique-microcopy` (chosen).** Its corpus seeds each of its 8 judged criteria once. Its native
   judged lane sits below ceiling on both tiers, so a gap in either direction can show.
2. **`critique-docs`.** It was the first recommendation, for the highest published judged precision.
   Rejected. Its corpus has 6 seeded defects, and only 3 of them sit on judged criteria, so a parity
   run would leave half of a rewritten rubric untested.
3. **`critique-clarity`.** Writing style guides are the most common house rubric. Rejected. Only 8 of
   its 23 criteria are judged, and its native judged precision is 0.11 on haiku and 0.16 on sonnet,
   so matching it would prove little.
4. **`critique-usability`.** Rejected for the same reason: its native judged precision is 0.10 on
   both tiers.

**What the published claim may say.**

1. **Publish the parity gap with a fixed caveat (chosen).** This matches how the README already pairs
   each figure with its limit.
2. **Publish no figure, only a statement that the path passed parity.** Rejected. It hides the
   number the rule asks for.
3. **Publish the figure without a caveat, like any other skill cell.** Rejected. A bundled rubric is
   unusually well operationalized, so a parity figure is a best case, and an uncaveated figure would
   read as a promise about every rubric.

## Decision outcome

**The measurement.** E45 builds BYOR on `critique-microcopy`. Its parity run works as follows.

- **The rubric.** Microcopy's 8 judged criteria are rewritten as a BYOR rubric. Each one is stated as
  a user would write it, without the skill's reference text, so the run does not simply replay the
  native path.
- **The run.** Both paths run on the microcopy corpus, in one run set, at k=5 on both pinned tiers.
  The native path is re-run rather than read from the published figures, because ADR 0038 records
  that the current harness reads differently from them.
- **The scoring.** Both paths are scored on the 8 judged criteria only. Each `BYOR-` ID is mapped to
  the native ID it rewrites before scoring. A test maps every corpus criterion and fails on an
  unmapped one, because a wrong map would credit or miss defects silently.

**The pass band.** No document sets a parity threshold today. ADR 0031's variance bands are
whole-skill bands, and `bench/variance.py` compares the overall lane only. E45's spec sets the band
and states its source.

**The claim.** The published parity figure always carries this caveat beside it, in the README and on
the site: "Measured on `critique-microcopy`'s own rubric, rewritten as a user-supplied one. A user's
own rubric is unmeasured."

**The paid run.** The parity run is a paid dispatch. It needs its own approval when E45's spec drafts
it.

## Consequences

**Positive:** BYOR ships with a published figure that can fail, and the measured-only rule keeps its
wording. The run reuses the committed corpus and scorer. Because the criteria and the artifacts stay
fixed, any gap between the two paths is the cost of supplying criteria at run time.

**Negative:**

- **Parity is a best case.** A bundled rubric is better operationalized than most rubrics a user
  brings. The caveat states this limit. It does not remove it.
- **The sample is small.** Microcopy's 8 judged-criterion defects sit 1, 6, 1 and 0 across its four
  artifacts, so one artifact, `microcopy-002`, carries most of the signal.
- **The rewrite could leak the native rubric.** A BYOR file that copies the native operational tests
  word for word would measure little beyond the native path. E45's spec states the rewrite rule.
- **Microcopy may not be the rubric most users bring.** If the users in view mostly bring
  documentation style guides, this choice should be revisited.

**Neutral:** no code changes, and no shipped skill's status or verdict changes.

## What this ADR does not decide

- The parity pass band, which E45's spec sets.
- The rubric-intake format and the extended critic contract, which are E45's build.
- Whether to add judged-defect recipes to the microcopy corpus, which E45's spec decides.
- Whether the merge step checks a BYOR finding's ID against the user's rubric, which stays with E45.
- Approval of the paid parity run.
