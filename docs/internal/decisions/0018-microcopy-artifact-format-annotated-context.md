# 0018 - Microcopy artifact format: annotated context, encoded as markdown-prose

## TL;DR
- **Decision:** `critique-microcopy`'s v0.1 artifact format is annotated context, not a bare string
  list. An artifact is one or more screens, each a markdown heading naming the screen or state, and
  under each heading one labeled block per message carrying the message text plus eight fixed context
  fields (placement, container, signal, timing, predictable-mistake, input-preservation, suggested-fix
  shape). The artifact's `bench` `artifact_type` is the existing `markdown-prose` value; no new type
  is added. All 14 criteria in `references/NNG-EM.md` ship for v0.1; none are cut.
- **Why:** a bare string list leaves only 6 of the 14 candidate criteria checkable at all, under
  AC-2's floor of 8 on this skill's own merits. Annotated context unlocks all 14 while reusing an
  artifact type and location-tolerance rule that already exist, so the decision costs no manifest
  schema change; [ADR 0015 (location tolerance: per artifact type)](0015-location-tolerance-per-artifact-type.md)
  already anticipated this exact question and pre-committed a usable rule either way.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, build-run P2 critique-microcopy pipeline, operationalize stage
  (Claude)

## Context and problem statement

[S-05 (skills slate)](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) OQ-2 leaves
`critique-microcopy`'s artifact format open between a bare string list and annotated context, to be
decided during P2 with the corpus module built to match. The prior pipeline stage's draft registry
(`skills/critique-microcopy/references/NNG-EM.md`) surfaced the fact that forces the decision: of the
14 candidate criteria drawn from the NN/g error-message guidelines, only 6, `PLAIN-LANGUAGE`,
`SPECIFIC`, `CONSTRUCTIVE`, `NEUTRAL-TONE`, `EXPLAIN`, `GRACE`, are evaluable from the message string
alone. The other 8 need placement, styling, container, timing, or behavior context a bare string
cannot carry. AC-2 sets this skill's floor at 8 criteria; a bare-string-list format cannot clear that
floor on its own criteria, only by importing criteria from elsewhere, which no other requirement
authorizes.

## Decision drivers

- AC-2 requires at least 8 criteria for `critique-microcopy`. Bare text alone supports 6.
- S-05's own artifact-claim column for this skill already reads "error messages, empty states,
  microcopy strings (list or annotated screens as text)", so annotated context is within the
  originally scoped claim, not an expansion invented at this stage.
- `bench/generator/manifest.schema.json`'s `artifact_type` is a closed set of four values
  (`markdown-prose`, `markdown-tree`, `html`, `string-list`); adding a fifth is its own manifest minor
  version and requires its own location-tolerance rule first (`bench/generator/README.md`, "Checklist
  for a new domain module", step 1). Reusing an existing type avoids that cost entirely.
- ADR 0015 already named this decision by number and pre-committed to having a rule ready for either
  outcome: "S-05 OQ-2 is pre-answered: whichever microcopy format the pipeline picks, a rule already
  exists for it." Picking `markdown-prose` collects on that commitment; inventing a fifth type would
  not.
- A downstream corpus-module stage and a downstream `scripts/checks.py` stage both need one
  unambiguous grammar to build against, not a range of options left for each to interpret separately.

## Considered options

1. **Bare string list, `string-list` artifact type.** Rejected: only 6 of 14 criteria are checkable,
   under the AC-2 floor of 8, and `string-list`'s location-tolerance rule is exact-index-or-key with
   zero tolerance, the least generous of the four, which does not offset the coverage loss.
2. **Annotated context as a new, fifth artifact type** (something like `microcopy-screen`). Rejected:
   requires its own `manifest.schema.json` minor version and its own location-tolerance rule under
   ADR 0015's own terms, a disproportionate cost for a stretch skill when an existing type already
   fits.
3. **Annotated context encoded as `markdown-prose` (chosen).** Reuses an existing artifact type and
   its already-defined tolerance rule (paragraph index within plus or minus 1, or heading path,
   `bench/README.md`, "Location tolerance"). A message and its context fields become a small labeled
   block under a heading naming the screen or control, addressable by that block's heading path and
   paragraph index exactly as `critique-clarity` and the toy fixture already are.
4. **Ship the bare string list now, defer annotated context to v0.2.** Rejected: 8 of 14 criteria
   would sit unimplemented at launch for a stretch skill that must still clear the R1 consistency
   floor to ship at all ([S-05 spec](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) AC-7).
   Option 3 costs nothing extra over option 1, so under-powering the skill has no offsetting benefit.

## Decision outcome

Option 3.

**Artifact type:** `markdown-prose`, the existing `bench/generator/manifest.schema.json` enum value.
No manifest schema change.

**Grammar.** An artifact is one or more screens. Each screen is a `##` heading naming the screen or
state (for example, "Signup form, email field" or "Checkout, payment failure"). Under each heading,
one labeled block per message on that screen:

- `Message`: the exact user-facing string.
- `Placement`: where the message sits relative to the control it concerns, free text.
- `Container`: `inline`, `toast`, or `modal`.
- `Signal`: the message's visual-weight description, plus a non-color-cue token drawn from `none`,
  `icon`, `text-label`, `shape-change`, `bold`, `underline`.
- `Fires`: when the message appears, drawn from `on-blur`, `on-submit`, `after-field-complete`,
  `mid-keystroke`, `on-load-before-input`, `on-focus`.
- `Predictable mistake`: `yes` or `no`, whether the underlying error is a common, foreseeable one.
- `Input on resubmission`: `preserved`, `cleared`, or `not-applicable`.
- `Suggested fix`: `none`, `described`, or `selectable`, plus a one-line note on what it recommends.

`Message` is the only field that is literally the artifact's own user-facing content; every other
field is reviewer-supplied screen context, the textual stand-in for what a screenshot or a live
render would otherwise show. This matches the S-05 artifact-claim phrase "annotated screens as text"
directly: the format is a screen described in text, not a live application and not an image.

Every one of the 14 criteria in `references/NNG-EM.md` now has a concrete field, or the `Message`
text itself, to evaluate against. The six scripted-lane criteria each check one field's controlled
vocabulary or the `Message` text against a fixed lexicon; see that file's Lane column for which field
backs which criterion.

**Location addressing.** Each message block addresses through `markdown-prose`'s existing anchors,
heading path and paragraph index, reusing ADR 0015's tolerance rule with no change: a message block
is one or more paragraphs under its screen heading.

**Criterion count.** All 14 candidate criteria from the prior stage's draft registry ship for v0.1.
None are cut, deferred, or reworded into a text-only form, because this format resolves the coverage
gap that would otherwise have forced a cut.

**Controlled-vocabulary tokens are v0.1 defaults**, first specified here, not measured against the
corpus yet. A downstream corpus-module or `scripts/checks.py` author who finds a real message needing
a token this list does not have extends the set additively, never repurposes an existing token's
meaning, and records the addition in `references/NNG-EM.md`.

## Consequences

**Positive:** all 14 criteria ship, clearing AC-2's floor by 6 rather than falling 2 short. No
`manifest.schema.json` change, no new location-tolerance rule to design and defend, and no new corpus
invariant beyond what `markdown-prose` domains (`critique-clarity`, the toy fixture) already prove
out. The eight controlled-vocabulary fields give the scripted lane genuinely deterministic checks
(fixed-token lookups) rather than forcing every context-dependent criterion into the judged lane by
default.

**Negative:** the annotation fields are metadata a real production screen does not literally render as
text next to the message; a reviewer supplies them, so the corpus module and any live-application
adapter must construct them rather than scrape them from a rendered page. This is a genuine narrowing
of what "artifact" means for this skill: `critique-microcopy` critiques a described screen, never a
live application or a screenshot image, which the skill's `SKILL.md` states as its own narrow claim.
The eight-field grammar is invented for this ADR, not sourced from NN/g, and its coverage of what a
reviewer needs to state is this pass's best judgment, not a validated schema; the first corpus-module
and `checks.py` authors to build against it are the ones who will find its gaps.

**Neutral:** `string-list`'s zero-tolerance rule and `markdown-prose`'s generous plus-or-minus-1 rule
now diverge for the same underlying content (a list of messages), a cost this decision accepts because
markdown-prose's greater location generosity was not the deciding factor, coverage was.

## Implementation sites

- `skills/critique-microcopy/references/NNG-EM.md`: the finished 14-row criterion table, this ADR's
  grammar restated in the "Artifact format" section, and lane assignments that cite the specific field
  each scripted check reads.
- `skills/critique-microcopy/SKILL.md`: the narrow artifact claim in the purpose paragraph, and the
  `checks` lane manifest.
- Not yet created, owed to a downstream pipeline stage: `skills/critique-microcopy/scripts/checks.py`
  (must parse the grammar above), `bench/generator/domains/microcopy.py` (must compose artifacts in
  this grammar, per the skill parameters' own note that "the corpus module must match" this decision),
  and `skills/critique-microcopy/examples/*.json` (goldens written in this grammar).
