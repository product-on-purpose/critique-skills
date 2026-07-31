# 0020 - critique-usability: Nielsen's severity ratings operationalize as severity anchors, not criterion IDs

## TL;DR
- **Decision:** `critique-usability` declares two `rubric_sources`, but only one of them produces criteria. `NNG-HEURISTICS` supplies all 20 criterion IDs. `NNG-SEVERITY` (Nielsen's severity ratings) contributes **zero** criterion IDs and is operationalized in `references/severity-anchors.md` instead: the fixed severities the scripted lane emits, the rules for rating a defect from a static artifact, and the explicit dropping of Nielsen's fourth weighing factor, market impact. The skill therefore ships **no** `references/NNG-SEVERITY.md`.
- **Why:** severity is not a thing an artifact can violate. It is applied after a heuristic finding already exists, to say how bad that finding is. Minting `NNG-SEV-*` IDs would invent artifact-checkable criteria the source does not supply, which is exactly what [methodology](../../explanation/methodology.md) section 9 forbids, and would push the registry past the population [S-05 (skills slate)](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) AC-2 asks for.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, build-run P2 `critique-usability` pipeline (Claude)

## Context and problem statement

[S-05 (skills slate)](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)'s slate table gives this skill two rubric sources, both paraphrased: Nielsen's 10 usability heuristics, and Nielsen's severity ratings. Its AC-2 gives the registry population as exactly the 10 heuristics with sub-criteria as needed. Those two statements pull in different directions the moment a pipeline tries to write one `references/<source-id>.md` per source, which the [skill template](../skill-template.md)'s directory shape asks for, because the template's file format for such a file is a criterion table and the severity source has no criteria to put in one.

The question is not cosmetic. Three things follow from the answer:

1. Whether `run.rubrics` and the criterion registry carry a second population of IDs that findings can cite.
2. Whether the bench corpus module has to seed defects for that population, since the template requires an injector and a recipe per scripted criterion and at least three judged ones.
3. Whether the skill's recall and precision numbers at P3 are computed over 20 criteria or over some larger set whose extra members no artifact can actually violate.

The registry-drafting pass that preceded this one raised the question explicitly and declined to settle it, leaving a recommendation for confirmation. This ADR settles it.

## Decision drivers

- **The methodology's own gate.** Section 2, Part 2 admits a source that is specific enough to generate discrete criteria. Severity ratings generate a scale, not criteria. Section 9 states the converse rule this skill is bound by: a criterion that cannot cite a source does not exist here. Manufacturing a criterion so that a source has something to cite runs the same rule backwards.
- **The shared scale is already this source, adopted once, centrally.** [`docs/reference/severity-scale.md`](../../reference/severity-scale.md) is frozen and is explicitly adapted from this source (methodology section 6 says so and links it). A per-skill re-encoding of the same scale as criteria would create a second, competing statement of a thing the family deliberately states once.
- **AC-2's wording.** Exactly the 10 heuristics with sub-criteria as needed names one population. `NNG-SEV-*` IDs would make the registry the-heuristics-plus-something-else, which is not what the acceptance criterion asks for and would make the AC-2 check ambiguous at review time.
- **The self-test's own structure.** `scripts/skill-selftest.py`'s paraphrase check requires every file in `references/` other than `severity-anchors.md` to contain a criterion table with an Operationalization column (`references-criterion-table-missing`). It exempts exactly one filename, and that filename is the one designated for severity calibration. The tooling already encodes the shape this decision picks.
- **Provenance must stay honest.** Dropping the source from `rubric_sources` altogether would be the tidier file layout and the wrong provenance record: the skill genuinely operationalizes this source, and methodology section 11 requires every source a skill operationalizes to be declared with its `operationalization` policy.

## Considered options

1. **Mint `NNG-SEV-0` through `NNG-SEV-4` as criteria.** Rejected: a finding cannot cite severity-3-ness as the thing an artifact violates, and `finding.severity` already carries the value. This would put the same information in two contract fields, one of which is typed and gated on.
2. **Mint criteria for the rating *process* (for example, ratings are averaged across evaluators).** Rejected: those are claims about the evaluation method, not about the artifact, so they fail the methodology's Part 1 artifact-dependency gate outright. Every finding must locate itself in the artifact; a process criterion cannot.
3. **Drop `NNG-SEVERITY` from `rubric_sources` and cite it only in prose.** Rejected: it understates provenance for material the skill does operationalize, and it contradicts the slate table, which names two sources for this skill.
4. **Keep the source in `rubric_sources` with zero criterion IDs, operationalized in `references/severity-anchors.md` (chosen).** The provenance record is complete and the criterion registry stays exactly the heuristic population AC-2 names.
5. **Chosen option plus a placeholder `references/NNG-SEVERITY.md` carrying an empty criterion table**, so the one-file-per-source shape holds literally. Rejected: an empty table exists only to satisfy a check, and the same content would then live in two files, which the template warns against for severity material specifically.

## Decision outcome

Option 4, with option 5 considered and refused.

- `SKILL.md` declares `NNG-SEVERITY` in `rubric_sources` with `operationalization: paraphrased`, citing ISBN and chapter for the book form and the canonical NN/g URL for the living reference, per S-05's Non-Functional Requirements. The citation says in-line where the source is operationalized.
- The skill ships two files in `references/`: `NNG-HEURISTICS.md` (the 20-criterion table) and `severity-anchors.md`. There is no `references/NNG-SEVERITY.md`. This is a deliberate, documented departure from the template's one-file-per-rubric-source directory shape, available only to a source that yields no criteria, and it is the shape the self-test already enforces.
- `references/severity-anchors.md` carries the operationalization: the source citation, what this skill takes from the source and what it drops, how to rate a design defect from a static artifact, and the fixed severities the scripted lane emits per criterion.
- **Market impact is not weighed.** The source weighs four factors; `docs/reference/severity-scale.md` weighs three (impact, frequency, persistence). The omitted fourth, the effect on the product's market reception, is not applied by this skill, because this skill's artifact claim is static UI specs and mockups (S-05 AC-8) and a static artifact carries no evidence of how a shipped product is received. Applying it would be the critic's speculation wearing a severity number.
- **Averaging across evaluators is not implemented.** The source recommends it for reliability; this family gets the same property from measured k-run consistency (methodology section 8) and from the acceptance-rate signal, so no skill implements per-run averaging.

## Consequences

**Positive:** the criterion registry means one thing, and every ID in it names something an artifact can actually violate. AC-2 checks cleanly at 20 criteria across 10 heuristics. The bench corpus module has no untestable criteria to seed, so P3 recall is computed over a population where recall is defined for every member. Provenance stays complete: a reader of `SKILL.md` sees both sources and can find where each one landed.

**Negative:** the directory no longer maps one references file per rubric source, so a reader who expects `references/NNG-SEVERITY.md` finds nothing and has to follow the pointer in the citation and in `severity-anchors.md`. This is the cost of the exception and the reason it is written down here. A future source with the same property (calibration, not criteria) should point at this ADR rather than re-litigate it.

**Neutral:** `run.rubrics` records the namespace `NNG` either way, since the namespace derives from criterion IDs and `NNG-SEVERITY` produces none. Nothing downstream can tell from `rubrics` alone that a second source informed the run, which is already true of every skill whose sources share a namespace.

## Implementation sites

- `skills/critique-usability/SKILL.md`: `rubric_sources[1]`, and the absence of `NNG-SEVERITY` from `checks`.
- `skills/critique-usability/references/severity-anchors.md`: the source citation, the dropped factor, the static-artifact rating rules, and the scripted lane's fixed severities.
- `skills/critique-usability/references/NNG-HEURISTICS.md`: the "Severity" section pointing at the anchors file.
- Deleted in this pass: the draft `skills/critique-usability/references/NNG-SEVERITY.md`, whose content moved to `severity-anchors.md`.
