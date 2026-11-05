---
id: E54
title: "Ship one documented cross-library composition workflow"
type: spec
status: committed
created: 2026-10-27
updated: 2026-11-03
linked-effort: docs/internal/backlog/enhancements.md
linked-plan: null
linked-release: v0.3.0
ac-count: 7
source-count: 24
requires-human-review: true
spec-dependencies: [N4]
target-release: v0.3.0
---

# Spec: cross-library composition workflow (E54)

Ruled by the maintainer on 2026-10-30 (the six decisions below), and not built yet. It is built after [N4 (the revision-loop chain)](../N4_revision-loop-chain/spec.md), because D4 has the recipe produce a revision brief with N4's brief writer. The body below is the draft the maintainer ruled on, so a note that was true on 2026-10-27 can be out of date: where it calls N4 an unruled draft, N4 was ruled on 2026-10-30. Its one model call is a paid run, and the maintainer deferred that go until N4 is built.

## Task Summary

**Status:** ruled 2026-10-30, not built
**Last updated:** 2026-11-03 by Claude, promoted from a local draft after the 2026-10-30 walk
**Linked plan:** not yet planned
**Open questions:** 0 (all six were decided 2026-10-30; see Open Questions / Decisions)
**Revisions:** 0

### Acceptance Criteria Fulfillment

- [ ] **AC-1** - The recipe names one sibling library, one concrete output artifact of that sibling, and one critique-skills skill whose published "Artifact claim" already covers that artifact type
- [ ] **AC-2** - The recipe is reachable from README.md's "The family" section and from `examples/recipes/`, both added in the same change
- [ ] **AC-3** - The recipe runs at least one critique-skills run against a real, sibling-produced file, with that file's provenance (repo, skill, version) stated
- [ ] **AC-4** - Any model-calling step in the recipe is dispatched only after the maintainer's own, separate, recorded approval
- [ ] **AC-5** - The recipe does not write, revise, or modify the sibling's output on this library's own authority; it stops at a critique envelope or, if chosen, a documented revision brief with a named human actor
- [ ] **AC-6** - The recipe states plainly that it is a same-org demonstration and does not satisfy the v1.0 external-consumer criterion
- [ ] **AC-7** - Whatever evidence the recipe commits is dated, states the CLI/model version it was produced under, and is covered by a stated drift check

## Purpose

`README.md` asserts that this library is "the judging end of the family value chain," composing
with `thinking-framework-skills` and `pm-skills` along "one value chain: think with one, make with
another, judge the result with this one" [S6]. No recipe in `examples/` demonstrates that chain
across a repository boundary; all three existing cross-cutting recipes, `gate-in-ci.md`,
`revision-loop.md`, and `critic-delegation.md`, stay inside this one repository [S10, S11, S12].
`ROADMAP.md`'s own v0.3.0 item calls the gap exactly: "One documented workflow where a sibling
library's output is critiqued by this one, as the concrete proof of the family's think-make-judge
value chain rather than an assertion about it" [S1]. The backlog entry frames the same gap as "the
difference between an asserted positioning claim and a demonstrated one" [S3]. This spec frames the
decisions that choice requires: which sibling and which of its outputs, which skill reviews it, what
"runs end to end" has to mean, where the recipe lives, whether it loops back into the sibling, and
how it is kept from going stale.

## Scope

- Choosing one sibling library, one concrete output of that sibling, and one `critique-<domain>`
  skill to review it (D1).
- Deciding what "runs end to end" means for this one recipe, and whether any step calls a model
  (D2).
- Deciding where the recipe is documented (D3).
- Deciding whether the recipe stops at a critique or produces a revision brief that something,
  or someone, could act on (D4).
- Deciding how the recipe is kept from drifting out of date (D5).
- Deciding what evidence satisfies the ROADMAP's own "proof, not an assertion" bar (D6).

## Non-Goals

- **No build.** This is a draft for a decision walk, not code or a written recipe. Nothing here is
  implemented.
- **No N4 (the revision-loop chain) work.** N4 itself is still an unruled draft with nine open
  decisions of its own [S9]; this spec does not resolve any of them, and D4 below treats N4's
  eventual chain as a possible but not required destination for E54's output.
- **No change to the auto-fix exclusion.** `ROADMAP.md`'s "Deliberately not doing" section stands
  unchanged: "Nothing here rewrites an artifact on its own authority" [S2]. Every option this spec
  considers keeps that boundary.
- **No edit to a sibling repository.** This task's own instructions bar editing any file outside
  this repository, and D3's recommendation keeps the recipe inside this repository for the same
  reason the backlog entry's own Target field never names a sibling repo path [S3].
- **No pursuit of the v1.0 external-consumer criterion.** The backlog entry says outright that this
  item "does not count toward the v1.0 external-consumer criterion" [S3]; that is E56's separate,
  unscheduled item [S1, "After" / v1.0.0 section].
- **No ruling on which third-party consumer the library eventually targets.** Out of scope; that is
  E56.

## Requirements

Restating what the evidence already fixes. None of this is reopened by this spec.

1. **The exit-gate condition's own wording sets the bar.** `ROADMAP.md`'s v0.3.0 exit gate: "One
   workflow that composes this library with a sibling library is documented and runs end to end"
   [S1, line 118]. The backlog entry's own "Done" bar: "one recipe demonstrating it" [S3, line 1201].
2. **This is a same-org demonstration, not an external-consumer proof.** The backlog entry states
   this outright: "This is a same-org demonstration and does not count toward the v1.0
   external-consumer criterion" [S3, line 1201].
3. **The auto-fix exclusion binds any option this spec considers.** `ROADMAP.md`: "Skills report
   findings; a human disposes them. Nothing here rewrites an artifact on its own authority, and that
   will not change as the catalog grows" [S2, line 168]. A composition workflow may critique or hand
   back a revision brief; it may not have this library rewrite the sibling's artifact itself.
4. **No sibling depends on this library technically, and the reverse is also true today.**
   `README.md`: "None depend on each other technically. They compose along one value chain" [S6,
   line 274]. A composition workflow must not introduce a runtime or build-time dependency from one
   plugin's code onto another's; it stays a documented, person-run sequence.
5. **`--gate` hardening is already built and exercised.** E53 is closed: every shipped skill reaches
   exit 0 and exit 2 from committed content, and the consumer-facing how-to and recipe both exist
   [S4-adjacent; docs/internal/backlog/enhancements.md E53 entry, lines 1176-1195]. Whichever option
   D2 and D3 choose can reuse this; E54 does not have to build gate infrastructure from zero.
6. **The revision brief's format is already fixed, if a composition chooses to use it.** ADR 0040
   rules that the brief holds "one entry per accepted finding: the finding, its location, its fix
   and its criterion" [S8, line 125], documented outside the versioned contract specifically "until a
   second consumer exists. It joins the contract when E54 (cross-library composition) consumes it"
   [S8, line 11-12]. N4's own spec repeats the same boundary: "The brief stays outside the versioned
   contract until E54 consumes it; moving it in is E54's decision, not this one" [S9, lines 84-85].

## Acceptance Criteria

AC-1: The recipe names exactly one sibling library, one concrete output artifact of that sibling
(a real file format or a real committed sample, not a hypothetical), and one `critique-<domain>`
skill whose own, already-published "Artifact claim" section names that artifact type without a new
SKILL.md edit. [S3, S6, D1]

AC-2: `README.md` gains a line in "The family" section pointing at the new recipe, and
`examples/recipes/` gains the recipe itself (or, per D3's resolution, a `docs/how-to/` page the
recipe links to), both added in the same change. [S6, S13; D3]

AC-3: The recipe runs at least one real critique-skills invocation against a file the sibling
library actually produced (an existing committed sample, or a fresh run of the sibling's own skill),
not an authored stand-in for the sibling's half of the pairing; the recipe states which repository,
which skill, and which skill version produced that file. [S3; D2]

AC-4: No step this spec's recipe adds calls a model, paid or otherwise metered, without the
maintainer's own explicit, separately recorded approval before dispatch; a step that needs one names
the cost in the same terms N4's own D9 used (envelope count, not a dollar guess), rather than
assuming the approval. [S9, D9 pattern; D2]

AC-5: The recipe's last step is either a critique run envelope or, if D4 chooses to go further, a
revision brief in ADR 0040's documented format; no step in the recipe has critique-skills write to,
or modify, the sibling's output file. [S2, S8; D4]

AC-6: The recipe's own text states that it is a same-org demonstration and does not satisfy the
v1.0 external-consumer criterion, in words a reader does not have to infer from context. [S3, line
1201]

AC-7: Any envelope or sample file this recipe commits as evidence carries the date it was produced
and the CLI or model version it ran under, and is covered by whichever drift check D5 selects, so a
later contributor can tell live evidence from a stale or invented example. [S10, S11, S12 house
style; D5]

## Sources & Evidence

- **[S1]** `ROADMAP.md`, "Next: v0.3.0" section, read in full 2026-10-27: the "Cross-library
  composition" bullet (line 109) and its matching exit-gate condition (line 118); also "Deliberately
  not doing" (lines 163-171) and the v1.0.0 and "After" sections (lines 128-161) - class A
- **[S2]** `ROADMAP.md`, line 168, the Auto-fix bullet under "Deliberately not doing" - class A
- **[S3]** `docs/internal/backlog/enhancements.md`, "## E54 - Ship one documented cross-library
  composition workflow", lines 1198-1208, read in full 2026-10-27 - class A
- **[S4]** `docs/internal/backlog/enhancements.md`, E52's resolution note, lines 1160-1195 (E52's
  ruling and the closed E53 entry immediately following it) - class A
- **[S5]** `docs/internal/backlog/README.md`, line 129, the ranked-backlog table row for E54 ("M",
  "v0.3.0") - class A
- **[S6]** `README.md` (this repo), read in relevant sections 2026-10-27: "Where this stops" (line
  251, the Two-Part Gate test naming `thinking-framework-skills`), "The family" (lines 265-276, the
  four-bullet sibling list and "None depend on each other technically"), and the closing "About the
  maintainer" paragraph (line 348, "the judging end of the family value chain") - class A
- **[S7]** `docs/explanation/architecture.md`, grepped for "sibling", "compose", "think-make-judge",
  `pm-skills`, `thinking-framework`: the only hit is line 78, "Seven sibling skills," which refers to
  this plugin's own seven `critique-<domain>` skills, not a cross-library relationship - class A
  (verified absence, not inferred)
- **[S8]** `docs/internal/decisions/0040-revision-loop-pauses-with-a-revision-brief.md`, read in
  full 2026-10-26 (prior session) and re-cited here: lines 11-12, 125, 153, 162 - class A
- **[S9]** [N4's spec](../N4_revision-loop-chain/spec.md), read in full as a draft: Non-Goals lines 84-85, Requirement 3 lines 124-126, D9's measurement
  framing (model-call sizing in envelope counts, not dollars) - class B when cited (then an uncommitted
  draft; ADR 0040 at [S8] is the class A record of the same E54-trigger boundary)
- **[S10]** `examples/recipes/gate-in-ci.md`, read in full - class A
- **[S11]** `examples/recipes/revision-loop.md`, read in full - class A
- **[S12]** `examples/recipes/critic-delegation.md`, read in part (header and "What clean-context
  critique means") - class A
- **[S13]** `examples/recipes/README.md`, read in full: the inventory table (three recipes, all
  inside this repository) and the "Honesty labeling, restated for this folder" paragraph - class A
- **[S14]** `docs/how-to/gate-in-ci.md`, read in part: "Before you gate anything" and the exit-code
  table; its own example envelope path is literally `critique/prd-envelope.json` - class A
- **[S15]** `skills/critique-clarity/SKILL.md`, "Artifact claim" paragraph (lines 54-59): "markdown
  or plain-text prose documents: memos, **PRDs**, proposals, policy explanations, and similar
  continuous prose" - class A
- **[S16]** `skills/critique-argument/SKILL.md`, frontmatter `description` and "Artifact claim"
  section: "argumentative prose: essays, proposals, position papers, recommendation memos, strategy
  documents, op-eds... Markdown or plain text" - class A
- **[S17]** `skills/critique-usability/SKILL.md`, "Artifact claim" (lines 50-56): "HTML or markdown
  UI specs, wireframe write-ups, and page mockups. It does not critique live running applications" -
  class A (read to rule usability out as a candidate reviewer for either sibling output considered
  below)
- **[S18]** `skills/critique-docs/SKILL.md`, frontmatter and body: scoped to Diataxis-mode markdown
  documentation trees specifically, not general prose or specification documents - class A
- **[S19]** `thinking-framework-skills/README.md` (sibling repo), read in part: "What this is,"
  "Relationship to `pm-skills`," and the badge block (version 0.13.0, tier advanced/Gold, 63
  frameworks; its `library.json` says 0.18.6 and 67 skills, so the README badge is stale) - class A
- **[S20]** `thinking-framework-skills/library.json`, read directly: `components` object with 67
  skills, 9 workflows, 3 subagents, 10 commands; no mention of `critique-skills` anywhere in the file
  - class A
- **[S21]** `thinking-framework-skills/skills/think-argument-mapping/SKILL.md`, read in full: "Output
  Format" ("The deliverable is the structured map with flagged weak links, not prose") and the
  Quality Checklist's closing item ("The output is the argument-map artifact, not prose") - class A
- **[S22]** `thinking-framework-skills/skills/think-argument-mapping/references/EXAMPLE.md`, read in
  part: a worked argument map laid out as headed sections, bullet lists, and a table, confirming the
  non-prose structure [S21] states - class A
- **[S23]** `pm-skills/README.md` and `pm-skills/.claude-plugin/plugin.json` (sibling repo): version
  2.34.0, 68 skills including `deliver-prd`; `pm-skills/skills/deliver-prd/SKILL.md` (version 3.1.0,
  updated 2026-10-16, "Creates a comprehensive Product Requirements Document"); and
  `pm-skills/library/skill-output-samples/deliver-prd/` holding four committed PRD samples in
  Markdown with `artifact: prd` frontmatter, one read in part
  (`sample_deliver-prd_storevine_sms-optin.md`) - class A
- **[S24]** Verification that neither sibling names this library back: `grep -rin "critique"` over
  `thinking-framework-skills/README.md` and `AGENTS.md`, and over `pm-skills/README.md` and
  `AGENTS.md`, returns no reference to `critique-skills`; the only "critique" hits are unrelated
  in-library uses (`think-boundary-critique`, a PM sprint's "speed critique" exercise) - class A
  (verified absence, run 2026-10-27)

**Also considered and set aside, not cited as a numbered source for a decision below:**
`writing-style-catalog`, the fourth library README.md's "family" section names [S6], is a composable
style-instruction catalog with no artifact of its own to critique (confirmed from its own README's
tagline, "composable catalog of writing instructions," read in part 2026-10-27); it is not carried
into D1 as a candidate for that reason. `product-lifecycle-templates`, which has its own
`library.json` and ships PRD/user-story/backlog template bundles, is not named in this repository's
README "family" section at all; it is noted under "What I do not know" below rather than folded into
D1, since this spec's evidence for it is thinner than for the two siblings README.md actually names.

## Open Questions / Decisions

| ID | Title | Resolution | Status | Updated |
|----|-------|------------|--------|---------|
| D1 | Which sibling, which output, and which critique skill reviews it | Option A | Decided | 2026-10-30 |
| D2 | What "runs end to end" means, and whether a model call is involved | Option A | Decided | 2026-10-30 |
| D3 | Where the recipe is documented | Option A | Decided | 2026-10-30 |
| D4 | Whether the workflow feeds back into the sibling, or stops at critique | Option B, after N4 | Decided | 2026-10-30 |
| D5 | How the recipe is kept from going stale | Option A | Decided | 2026-10-30 |
| D6 | What evidence counts as the "proof" ROADMAP promises | Option A | Decided | 2026-10-30 |

### D1: Which sibling, which output, and which critique skill reviews it (Decided)

**Summary.** Decide the one concrete pairing: a named sibling library, a named concrete output of
that sibling, and the one `critique-<domain>` skill that reviews it.

**Context.** `README.md`'s own "family" section names `thinking-framework-skills` and `pm-skills` as
the two siblings with technical outputs [S6]; the backlog entry's own evidence line names the same
two as candidates [S3, "thinking-framework-skills or pm-skills"]. Neither sibling's own README or
`AGENTS.md` currently names `critique-skills` back, confirmed by a direct grep returning zero hits
[S24]; whichever pairing is chosen is this library's unilateral choice, not a coordinated one.
`thinking-framework-skills`'s `think-argument-mapping` skill produces an "argument map," which its
own SKILL.md states twice is "not prose" [S21], while `critique-argument`'s own Artifact claim
requires "argumentative prose... Markdown or plain text" [S16]: a real, untested mismatch in form,
even though the two skills share a Toulmin-adjacent subject (argument structure). `pm-skills`'s
`deliver-prd` skill produces a Markdown PRD (`artifact: prd` in its sample frontmatter, four such
samples already committed) [S23], and `critique-clarity`'s own Artifact claim names "PRDs" by the
same word, among its listed in-scope document types [S15].

**Desired outcome.** A pairing where the reviewing skill's own published Artifact claim already
covers the sibling's output type in its own words, with no new SKILL.md edit needed to make the
claim true, and where a real (not invented) sample of the sibling's output already exists to use as
input.

**Options / approaches.**

* **Option A:** `pm-skills`'s `deliver-prd` output (a Markdown PRD) reviewed by `critique-clarity`.
  Both ends cite the same word independently: `critique-clarity`'s Artifact claim names "PRDs"
  verbatim [S15], and `pm-skills` already ships four committed PRD samples today [S23], so no new
  fixture has to be authored on the sibling's side.
* **Option B:** `thinking-framework-skills`'s `think-argument-mapping` output (an argument map)
  reviewed by `critique-argument`. The most thematically obvious pairing (argument structure on both
  sides), but it carries a real, unverified risk: the map's own skill states its output is
  structured, not prose [S21], while `critique-argument`'s scripted checks (`TOULMIN-CLAIM-MARKER`,
  `TOULMIN-HEDGE-DENSITY`) are built to read continuous prose for linguistic markers like hedge
  density, a measure that may not mean the same thing against a bulleted, tabled map. Untried.
* **Option C:** `pm-skills`'s `deliver-prd` output reviewed by `critique-argument` instead of
  `critique-clarity`, on the reasoning that a PRD argues for a solution. Weaker textual support than
  Option A: `critique-argument`'s own Artifact claim never uses the word "PRD" anywhere in its text
  [S16], where `critique-clarity`'s does [S15].

**Recommendation.** Option A, high confidence. It is the only pairing where both the sibling's
output type and the reviewing skill's own scope are independently, explicitly named in each side's
published text, and it needs no newly authored fixture, since real PRD samples already exist in
`pm-skills` today.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: a `pm-skills` `deliver-prd` PRD, reviewed by `critique-clarity`
> * **Reasoning:** The maintainer answered "d1 a". Both sides' published text names PRDs, and real samples exist.
> * **Follow-up:** Build in E54's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E54_cross-library-composition/spec.md`.
> * **Decided by / date:** jprisant / 2026-10-30

### D2: What "runs end to end" means, and whether a model call is involved (Decided)

**Summary.** Decide whether the recipe is a fully authored walkthrough, one with a real model call
somewhere, or a CI job, and whether any paid or metered model call is involved.

**Context.** `ROADMAP.md`'s exit-gate wording is "documented and runs end to end" [S1, line 118];
the backlog's own bar is "one recipe demonstrating it" [S3]. This library's three existing
cross-cutting recipes already set a house style: cheap, deterministic parts (exit codes, schema
validation) are actually run and reproduced, while expensive or illustrative parts are authored and
labeled as such [S10, S11, S12, S13]. A related decision in N4's own draft (D9) reached the same
split for a comparable question and recommended deterministic coverage now, with any live
model-calling smoke test needing the maintainer's own separate go-ahead before dispatch [S9].

**Desired outcome.** A recipe that earns the word "runs" rather than merely asserting it, at a cost
the maintainer can see and approve before anything is dispatched.

**Options / approaches.**

* **Option A:** A documented recipe in the existing house style: a real, already-committed sibling
  output file as input (no new model call needed to produce it, since `pm-skills` already ships PRD
  samples [S23] under Option A of D1), and one real critique-skills model call against that real
  file, with the resulting envelope committed as evidence. Exactly one model call, needing the
  maintainer's explicit go before it is dispatched.
* **Option B:** A fully authored recipe with no model call at all: a hand-written, illustrative
  critique envelope in the same "curated illustration" style parts of `revision-loop.md` already use
  [S11]. Buildable immediately with no approval needed, but produces no new evidence; the one claim
  this item exists to prove, that this specific pairing actually works, stays unverified.
* **Option C:** A CI job wiring this library's already-built `--gate` mode [Requirement 5] to a
  sibling's real or sample output, so a build literally passes or fails on a critique-skills verdict.
  The most literal reading of "runs end to end," but it needs either a workflow file committed in a
  repository this task may not edit, or a faked consumer repo inside this one [S10 already does the
  latter for a non-sibling case], and it still needs at least one real model call to produce the
  gated envelope in the first place.

**Recommendation.** Option A, medium confidence. It matches the house style every existing recipe
already uses, costs exactly one model call rather than a new CI surface in either repository, and
gives the ROADMAP's "proof, not an assertion" claim one real, reproducible data point; the
maintainer's go-ahead for that one call is a precondition this spec does not assume.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: one real `critique-clarity` run against one committed `pm-skills` PRD, envelope committed and dated
> * **Reasoning:** The maintainer answered "d2 a" in round 2, after the step-by-step comparison. D6 Option A needs a real envelope, which only this option produces.
> * **Follow-up:** Build in E54's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E54_cross-library-composition/spec.md`. The one model call needs the maintainer's separate go before it runs.
> * **Decided by / date:** jprisant / 2026-10-30

### D3: Where the recipe is documented (Decided)

**Summary.** Decide whether the recipe lives in `examples/recipes/`, a `docs/how-to/` page, the
sibling repository, or more than one of these.

**Context.** The backlog entry's own Target field names only paths inside this repository:
`ROADMAP.md`, `README.md`, `examples/recipes` [S3, line 1200]; it names no sibling-repo path.
`examples/recipes/README.md` already documents the pattern a fourth recipe would extend, including
its "Honesty labeling" convention [S13]. `docs/how-to/gate-in-ci.md` is the kind of procedural
reference a recipe cites, not the worked illustration itself [S14].

**Desired outcome.** A location that matches how this repository already organizes "cross-cutting,
how the pieces connect" content, discoverable from the README's own "family" section, with no
coordinated change required in a repository this project does not control for this one item.

**Options / approaches.**

* **Option A:** `examples/recipes/` in this repository only, as a fourth recipe beside
  `gate-in-ci.md`, `revision-loop.md`, and `critic-delegation.md`, linked from `README.md`'s "The
  family" section. Matches the backlog's own stated Target field exactly [S3] and needs no change
  outside this repository.
* **Option B:** A `docs/how-to/` page instead of, or in addition to, a recipe. This repository's
  existing how-to pages are procedural references a recipe cites [S14], not illustrative
  walkthroughs on their own; a how-to page alone would likely fall short of the backlog's "one
  recipe demonstrating it" bar [S3].
* **Option C:** Something also committed in the sibling repository (`pm-skills`, under D1's Option
  A), so the pairing is discoverable from both sides, closing the gap that neither sibling currently
  names this library back [S24]. Matches that gap directly, but it means a coordinated change in a
  repository outside this task's own edit boundary, on a release cycle this item does not control.

**Recommendation.** Option A, high confidence. It is exactly what the backlog entry's own Target
field already names, it reuses an established folder and house style, and it needs no coordinated
change in a repository this task's own instructions already bar editing.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: a fourth recipe in `examples/recipes/`, linked from the README's "The family" section
> * **Reasoning:** The maintainer answered "d3 a". It needs no change outside this repository.
> * **Follow-up:** Build in E54's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E54_cross-library-composition/spec.md`.
> * **Decided by / date:** jprisant / 2026-10-30

### D4: Whether the workflow feeds back into the sibling, or stops at critique (Decided)

**Summary.** Decide whether the recipe ends at a critique envelope, ends one step further at a
documented revision brief, or goes all the way to a revised sibling artifact and a re-critique.

**Context.** The auto-fix exclusion stands regardless of which option is chosen: "a human disposes
them... nothing here rewrites an artifact on its own authority" [S2]. ADR 0040 named this exact
decision as the trigger for moving the revision brief into the versioned contract: the brief "is
documented outside the versioned contract... until a second consumer exists. It joins the contract
when E54 (cross-library composition) consumes it" [S8, lines 11-12, 153]. N4, which would build the
actual invokable revision-loop chain this library could resume against, is itself still an unruled
draft with nine open decisions of its own [S9]; nothing about E54 requires waiting for N4 to be
built first if the composition stops short of a live resume.

**Desired outcome.** A choice that demonstrates the "think-make-judge" value chain credibly without
depending on machinery (N4's chain) that does not exist yet, and without crossing the auto-fix
boundary.

**Options / approaches.**

* **Option A:** Stop at critique. The recipe ends with a critique-skills envelope (optionally, a
  disposition log) against the sibling's output; nothing is handed back to the sibling, and no
  revision brief is produced. Simplest, needs nothing from N4 or ADR 0040's brief format, and keeps
  the auto-fix boundary visibly uncrossed.
* **Option B:** Produce a revision brief in ADR 0040's documented format, and stop there with no
  live resume. Gives ADR 0040's own named trigger, "when E54 consumes it" [S8, line 153], something
  concrete to point to, without needing N4's still-unbuilt chain to exist, and without pm-skills
  being asked to do anything it was not built to accept.
* **Option C:** A full loop: critique, brief, a person revises the sibling's artifact (for example,
  re-running `deliver-prd` with the brief's findings folded into a new prompt), then a re-critique.
  The most complete demonstration of the value chain, but it depends either on N4's chain existing
  (it does not yet [S9]) or on every step being driven by hand, and on treating `pm-skills` as
  willing to accept a revision brief it was never designed to read.

**Recommendation.** Option B, medium confidence. It gives ADR 0040's own stated trigger something
real to point to without waiting on N4's nine still-open decisions, it stays inside the auto-fix
boundary because a person, not this library, would act on the brief, and it is a smaller build than
Option C's full loop.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option B, sequenced after N4: E54 writes a revision brief with N4's brief writer, and the brief joins the contract in the same 1.1.0 bump as N4's `iteration` field
> * **Reasoning:** The maintainer answered "d4 b" in round 2, having initially leaned to B. ADR 0040 says the brief joins the contract when E54 consumes it; building N4 first means the writer exists and the contract changes once.
> * **Follow-up:** Build in E54's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E54_cross-library-composition/spec.md`, ordered after N4's build. The brief schema and its validator coverage join contract 1.1.0 with N4's `iteration` field, so N4's implementation should leave room for it.
> * **Decided by / date:** jprisant / 2026-10-30

### D5: How the recipe is kept from going stale (Decided)

**Summary.** Decide what keeps the recipe's committed evidence trustworthy as both repositories keep
shipping new versions, rather than freezing as a snapshot nobody checks again.

**Context.** `examples/recipes/README.md`'s own "Honesty labeling" convention already distinguishes
real, reproducible commands from authored illustration in every existing recipe [S13]. Elsewhere in
this repository, dated, versioned evidence is the normal pattern for anything claimed as "real" (the
bench harness's `harness-provenance.txt`, the dispatch run-set convention E63 and E73 formalized).
`pm-skills`'s own `deliver-prd` skill has moved from version 2.2.0 (the committed sample's
`skill_version`) to 3.1.0 in the time between that sample's creation and this draft [S23], which is
direct, dated evidence that a sibling's output shape does change under a recipe's feet.

**Desired outcome.** A low-cost way for a later reader, or CI, to tell a still-valid recipe from one
that has quietly gone stale, without inventing new infrastructure this item's own Size (M) estimate
does not obviously budget for.

**Options / approaches.**

* **Option A:** A dated, committed example envelope (the real output of D2 Option A's one model
  call), stating the date and the CLI or model version it ran under, in the same provenance style
  `bench.yml`'s own `harness-provenance.txt` already uses elsewhere in this project.
* **Option B:** An automated check in the existing `schema` CI job (`npm run validate:envelopes`)
  that re-validates the committed envelope against the current contract schema on every push,
  catching contract-version drift with no new model call and no new CI job to register.
* **Option C:** A dated example with no automated check at all, matching how the three existing
  recipes are kept today (none of them has its own dedicated regression test). Cheapest, but carries
  the same silent-drift risk this project's own `CHANGELOG.md` records happening to published figures
  elsewhere.

**Recommendation.** Option A combined with Option B, medium confidence. A dated envelope answers "is
this evidence or an invented example" on its own; folding its schema check into the already-existing
`schema` job costs no new job registration while catching the one kind of drift, a contract-version
bump, most likely to silently break a multi-year-old recipe.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: a dated envelope recording the CLI and model version it ran under
> * **Reasoning:** The maintainer answered "d5 a", choosing Option A alone rather than the recommended A with B, so no new schema-job check is added.
> * **Follow-up:** Build in E54's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E54_cross-library-composition/spec.md`.
> * **Decided by / date:** jprisant / 2026-10-30

### D6: What evidence counts as the "proof" ROADMAP promises (Decided)

**Summary.** Decide what standard of evidence actually satisfies the ROADMAP's own claim that this
item is "the concrete proof... rather than an assertion," as opposed to a narrated example that
merely relocates the same assertion.

**Context.** `ROADMAP.md`'s own words set the bar: "the concrete proof of the family's
think-make-judge value chain rather than an assertion about it" [S1, line 109]. The backlog entry
frames the risk the same way: "the difference between an asserted positioning claim and a
demonstrated one" [S3, line 1202]. A recipe that is entirely authored, with no live run anywhere,
would answer the letter of "documented" while leaving the one genuinely new claim, that this
specific sibling output actually passes through this specific skill, unverified.

**Desired outcome.** A standard that a skeptical reader, not just the recipe's own author, would
agree closes the gap the backlog entry names, at a cost proportionate to this item's Size M estimate
[S5].

**Options / approaches.**

* **Option A:** One real, dated critique-skills envelope against one real sibling output file,
  reproducible by a reader who runs the stated commands themselves, the same bar the three existing
  recipes already hold their own reproducible parts to [S13]. Satisfies "demonstrated" because a
  reader can re-run it and get the same result, not merely read a claim.
* **Option B:** A narrated walkthrough with an authored (not live) envelope, in the same "curated
  illustration" style `revision-loop.md` already uses for parts of its own content [S11]. Cheaper and
  matches existing house style, but the one new claim this item exists to prove would still be
  unverified if that is the only new content added.
* **Option C:** A standing, repeatable mechanism, for example a script that re-runs the pairing
  against a fresh sibling sample on demand, rather than a one-time artifact. The strongest ongoing
  proof, but it is infrastructure this item's Size M backlog estimate [S5] does not obviously budget
  for, and no existing recipe in this repository is kept live this way.

**Recommendation.** Option A, high confidence. The backlog entry's own stated gap is between "an asserted positioning claim and a
demonstrated one" [S3, line 1202]; Option B would only partially close that gap, since the one claim
that is actually new here would stay unverified, and Option C's ongoing mechanism is more than this
item's own size estimate anticipates. One real, reproducible run is the cheapest thing that actually
closes the gap instead of relocating it.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: one real, dated envelope a reader can reproduce with the stated commands
> * **Reasoning:** The maintainer answered "d6 a". "Reproduce" means re-running the commands: the judged lane is not deterministic, so a re-run will not return identical findings.
> * **Follow-up:** Build in E54's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E54_cross-library-composition/spec.md`; the recipe states that a re-run's judged findings will differ.
> * **Decided by / date:** jprisant / 2026-10-30

## What I do not know

- Whether `product-lifecycle-templates`, a fourth plugin in this
  organization with its own `library.json` and a "delivery-docs" bundle family
  that produces PRDs, user stories, and release notes from templates rather than agent skills,
  belongs in "the family" at all. `README.md`'s own "family" section does not name it [S6], and I did
  not read enough of it to say whether that is a deliberate exclusion or a README that has not caught
  up; I read only its top-level README in part.
- Whether `critique-clarity`'s full criterion registry (whatever reference file holds its judged and
  scripted checks, which I did not open) has ever been tested against a `pm-skills`-shaped PRD's
  actual section structure; I confirmed only that the skill's own Artifact claim names "PRDs" by
  word, not that every criterion reads cleanly against one.
- The exact dollar or token cost of D2 Option A's one model call; consistent with N4's own D9 gap
  [S9], I counted the call, not its price, and did not look up current per-token rates.
- Whether `pm-skills`'s own release or contribution process has any stated policy about being named,
  linked, or cited from another project's README or recipe; I did not read `pm-skills/CONTRIBUTING.md`
  or any governance document there.
- Whether `scripts/gen-readme-catalog.mjs` or `scripts/check-site.mjs` (this repository's own
  README- and site-generators) would need a change to carry a new "family" section line or a new
  recipe-inventory row; I did not read either generator.
- Whether a `docs/internal/release-plans/` document for the v0.3.0 exit gate, beyond `ROADMAP.md`
  itself, states acceptance language for E54 more specific than the ROADMAP bullet and the backlog
  entry I read in full; I did not find or read such a document.
