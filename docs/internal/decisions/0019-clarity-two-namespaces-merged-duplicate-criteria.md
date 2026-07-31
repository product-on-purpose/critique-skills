# 0019 - Clarity registry: two namespaces retained, duplicate criterion pairs merged

## TL;DR
- **Decision:** critique-clarity keeps two criterion namespaces, PLAIN and WILLIAMS, rather than folding
  WILLIAMS-* entirely into PLAIN-* (S-05, skills-slate spec, OQ-1). Within that, the two criterion pairs
  that tested the literal same construction across both sources merge into one ID each:
  PLAIN-NOMINALIZATION absorbs Williams ch. 3's treatment of actions, and PLAIN-CONCISE absorbs Williams
  ch. 9's treatment of concision. WILLIAMS-NOMINALIZATION and WILLIAMS-CONCISION are never published.
- **Why:** six of Williams' eight candidate criteria have no PLAIN equivalent and would be misattributed
  to an open-standard source if renamed into its namespace; the two that do duplicate a PLAIN test would
  let one passage double-cite the same flaw under two IDs if both shipped separately.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** critique-clarity pipeline, operationalization stage

## Context and problem statement

S-05 (skills-slate spec) OQ-1 leaves open whether WILLIAMS-* criteria fold into PLAIN-* so
critique-clarity's registry stays single-sourced, defaulting to two namespaces if the pipeline does not
decide otherwise. `docs/reference/criterion-ids.md`'s namespace registry restates the same open
question. A prior research pass in this pipeline (recorded in `references/PLAIN.md` and
`references/WILLIAMS.md`'s draft "Overlap flags for S-05 OQ-1" sections) surveyed all 17 PLAIN and all 8
WILLIAMS candidate criteria against each other and found only two pairs close enough to be the same
checkable claim: nominalization (PLAIN's hidden-verb guidance versus Williams ch. 3, "Actions") and
concision (PLAIN's word-trimming guidance versus Williams ch. 9, "Concision"). The remaining six WILLIAMS
candidates (character-as-subject, cohesion, coherence, stress, sentence shape, parallelism) were found
related to, but not the same test as, various PLAIN criteria. This ADR is the pipeline's resolution,
required before `SKILL.md`'s `checks` manifest and `rubric_sources` block can be written.

## Decision drivers

- `docs/reference/criterion-ids.md` rule 4, "one criterion, one ID": a rubric item that bundles two
  independently checkable things is split before it ships. The inverse applies structurally too: two
  sources independently converging on the identical checkable claim should not ship as two IDs a single
  finding could cite twice for what a reader experiences as one flaw.
- Provenance integrity: WILLIAMS is a paraphrased, copyrighted source ([ADR 0006](
  0006-copyright-paraphrase-policy.md)); PLAIN is an open standard. Renaming Williams-only concepts
  (cohesion, coherence, stress, character-as-subject, sentence shape, parallelism) into the PLAIN-*
  namespace would misattribute their citation to a source that does not actually state them, which is
  the opposite of what the paraphrase policy's citation discipline exists to preserve.
- S-05 AC-2 sets clarity's minimum at 12 criteria; either resolution clears that floor by a wide margin,
  so criterion count was not a deciding factor.
- S-05 AC-3: no criterion ID appears in two skills except upstream WCAG IDs. This ADR does not touch
  that rule; it concerns two sources within one skill, not cross-skill reuse.

## Considered options

1. **Fold all WILLIAMS-* into PLAIN-*, one namespace.** Rejected. Six of the eight WILLIAMS candidates
   have no PLAIN equivalent at all; inventing PLAIN-* IDs for concepts PLAIN's own text never states
   would misattribute Williams' original contribution to an open-standard source, and OQ-1's
   "single-sourced registry" motivation does not actually require one namespace, only non-duplication.
2. **Keep two namespaces, ship all candidate IDs as-is, including both duplicate pairs.** Rejected. A
   passage that both nominalizes a verb and pads word count would double-cite under two IDs for what a
   reader experiences as one flaw each time, inflating finding counts and confusing severity and
   frequency weighing for no operational benefit.
3. **Keep two namespaces; merge only the two genuinely duplicate pairs into one ID each (chosen).**
   Preserves the six genuinely distinct WILLIAMS concepts under their own namespace and citation, while
   collapsing the two pairs where both sources test the literal same construction into one ID citing
   both.

## Decision outcome

Option 3. PLAIN-NOMINALIZATION and PLAIN-CONCISE each cite both sources in their Operationalization
text and carry the merged criterion under the PLAIN namespace. The open-standard source was chosen to
hold both merged IDs, rather than splitting one to PLAIN and one to WILLIAMS, so the merge rule reads
consistently across the registry: a reader checking "did this criterion merge" only ever has to look in
one place (`PLAIN.md`) rather than two. WILLIAMS-NOMINALIZATION and WILLIAMS-CONCISION are not
published as IDs; the six-criterion WILLIAMS registry (`references/WILLIAMS.md`) and the
seventeen-criterion PLAIN registry (`references/PLAIN.md`, two of whose rows are jointly sourced) are
this decision's implementation.

Final count: 17 PLAIN-owned criteria (2 jointly cited with WILLIAMS) plus 6 WILLIAMS-owned criteria,
23 total, against S-05 AC-2's 12-criterion floor for clarity.

## Consequences

**Positive:** the registry stays honest about provenance, since the six criteria that are genuinely
Williams' own contribution keep the WILLIAMS-* namespace and citation rather than being folded into an
open-standard namespace that never stated them. No finding can double-cite the same nominalization or
concision flaw under two IDs. 23 criteria comfortably clears the AC-2 floor.

**Negative:** a reader comparing this skill's shipped ID count against S-05's spec table, which
estimates "8" WILLIAMS criteria, needs this ADR to understand why only 6 ship as WILLIAMS-* IDs; both
`references/PLAIN.md` and `references/WILLIAMS.md` cross-reference this ADR directly so that reader does
not have to find it independently.

**Neutral:** this decision does not change lane assignment, severity anchors, or the S-04 template's
required file shape; it is a namespace and ID-count decision only, resolved before `SKILL.md`'s
`rubric_sources` and `checks` manifest were written so both could be written once, correctly.

## Implementation sites

- `skills/critique-clarity/references/PLAIN.md` - the 17-row registry, two rows jointly citing WILLIAMS.
- `skills/critique-clarity/references/WILLIAMS.md` - the 6-row registry, with a resolution note
  explaining the two IDs that do not appear.
- `skills/critique-clarity/SKILL.md` - `rubric_sources` (two entries, PLAIN and WILLIAMS) and the
  `checks.scripted` / `checks.judged` manifest, drawing criterion IDs from both files above.
- `docs/reference/criterion-ids.md`'s namespace-registry note, rewritten from "may still merge" to the
  resolution above with a link back to this ADR. The note was initially left unedited as out of
  pipeline scope; that left the one shared, cross-skill file a reader would consult still describing
  OQ-1 as open, with no path to the decision, so the note now records the outcome. The registry table
  itself is unchanged, since it already listed both namespaces.
