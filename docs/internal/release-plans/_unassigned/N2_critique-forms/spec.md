---
id: N2
title: "critique-forms, a form-usability critique skill"
type: spec
status: draft
created: 2026-09-25
updated: 2026-09-25
linked-effort: docs/internal/backlog/new-components.md
linked-plan: null
linked-release: null
ac-count: 13
source-count: 17
requires-human-review: true
spec-dependencies: [S-04, S-05]
target-release: v0.2.0
---

# Spec: critique-forms, a form-usability critique skill

## Task Summary

**Status:** draft
**Last updated:** 2026-09-26 00:45 (UTC) by plab-spec
**Linked plan:** not yet planned
**Open questions:** 0 (see Open Questions section)
**Revisions:** 2 (see Revisions section)

### Acceptance Criteria Fulfillment

- [ ] **AC-1** - `checks` and `references/` declare exactly the 24 ruled IDs, each in its ruled lane
- [ ] **AC-2** - Every criterion row cites its registry sources by handle and grade, all resolving in the bibliography
- [ ] **AC-3** - No criterion's operational test flags ground another skill owns
- [ ] **AC-4** - The two overlap rows each name the accessibility criterion they overlap and why forms differs
- [ ] **AC-5** - A merged envelope with scripted and judged `FORMS` findings validates with `run.rubrics` `["FORMS"]`
- [ ] **AC-6** - Two scripted-lane runs over the full forms corpus produce identical output
- [ ] **AC-7** - The corpus seeds all 18 scripted and at least 3 judged criteria across at least 3 artifacts, 1 clean
- [ ] **AC-8** - Hand-scored k=3 joint-routing results on both tiers cover the three contested pairs
- [ ] **AC-9** - Every `ci.yml` job passes on the change that registers the skill
- [ ] **AC-10** - A committed real-forms report classifies the scripted lane's findings on at least 10 forms
- [ ] **AC-11** - The README scoreboard shows forms and baseline at k=5 on both tiers from one run set
- [ ] **AC-12** - A recorded ship or hold verdict cites the figures against the baseline and the consistency floor
- [ ] **AC-13** - No scripted criterion firing 3+ times on real forms has more false alarms than correct findings

### Currently In Progress

None.

---

## Purpose

`critique-forms` critiques HTML forms for form usability: how well a form's fields, input types,
labels and actions let a person complete it, especially on a phone [S1, S2]. It is the one new skill in
v0.2.0 [S9]. Its criteria are the 24 rows the maintainer ruled on 2026-09-25, synthesized from 75
sources in the `FORMS` namespace [S2, S3, S4]. This spec turns that ruling into the conditions the
built skill must meet. The registry and bibliography remain its research record.

## Scope

### In Scope

- The skill directory `skills/critique-forms/`, built to the skill template [S6], implementing the
  24 criteria in Requirements 1.
- Static HTML forms as the artifact: markup and declared CSS, through the shipped `html` artifact
  type and its resolver, reused as is [S1, S2].
- A new bench corpus module for the forms domain [S2].
- Joint-routing cases and description boundary clauses with the three skills whose ground forms
  borders: `critique-accessibility`, `critique-usability` and `critique-microcopy` [S2, S6].
- A scripted-lane check against real production forms, before any paid run [S2].
- k=5 measurement on both pinned tiers and a ship or hold verdict [S7, S9].

## Non-Goals

- **Checkout-specific criteria.** Card fields, coupons, guest checkout and address lookup belong to
  N5 (critique-checkout), which has 38 seeded findings and needs its own research pass [S2].
- **Criteria the registry left out.** `FORMS-GROUPING` (deferred until a measured study is found),
  the thin or single-sourced rules deferred to a v1.1 review, and the practices the sources contest:
  disabling submit until valid, confirm-email and validation timing [S2].
- **Live pages.** No criterion depends on script execution, rendered layout the artifact does not
  declare, or interaction [S2].
- **E67 (accessibility expansion) and E68 (narrowing accessibility's scope claim).** Both are
  separate efforts, even though forms' two overlap rows point at criteria E67 adds [S10].
- **Editing the published criterion-ID reference before the skill ships.**
  `docs/reference/criterion-ids.md` gains its `FORMS` row at ship, not before [S4].
- **Changing any existing corpus artifact.** Forms adds a domain; it does not alter another
  domain's artifacts, which the `corpus` CI job verifies byte for byte [S14].

## Users / Actors

| Actor | Role | Interaction |
|-------|------|-------------|
| End user | Author or reviewer of a form | Asks for a critique of an HTML form; reads the findings |
| Build agent | Author of the skill | Builds it through `askit-build-skill` in fallback mode, following the template [S11, S6] |
| `critique-critic` subagent | Clean-context critic | Runs the judged lane the skill delegates to [S6] |
| Bench harness | Measurement | Runs forms and the baseline at k=5 on both pinned tiers [S12] |
| Maintainer | Approver | Approves each paid dispatch, rules the open questions, commits the spec |

## Requirements

### Criterion set

1. `critique-forms` implements exactly these 24 criteria in the `FORMS` namespace, 18 scripted and
   6 judged, as ruled on 2026-09-25 [S2]. The Flags column is a summary of each ruled criterion. The
   operational test, severity anchors and lane rationale for each are written in the skill's
   `references/` criterion table, in the template's seven-column format [S6], not here.

   | # | ID | Lane | Flags |
   |---|---|---|---|
   | 1 | `FORMS-INPUT-TYPE` | scripted | An email, telephone, URL or search field whose `type` does not match its purpose |
   | 2 | `FORMS-NUMERIC-INPUTMODE` | scripted | A digit string that is not a quantity using `type="number"`, or plain text without `inputmode="numeric"` |
   | 3 | `FORMS-AUTOCOMPLETE` | scripted | A personal, contact, address or credential field with no `autocomplete` token, a token outside the WHATWG vocabulary, or `autocomplete="off"` on data that is not one-time |
   | 4 | `FORMS-AUTOCORRECT` | scripted | A name, email, username or address field left with autocorrect, auto-capitalization or spellcheck on |
   | 5 | `FORMS-PLACEHOLDER-INSTRUCTION` | scripted | A labelled field whose format instruction or example exists only in its placeholder |
   | 6 | `FORMS-REQUIRED-OPTIONAL` | scripted | Required and optional fields mixed with the difference not visible in label text: nothing marked, a symbol with no legend, or a marker only in a placeholder |
   | 7 | `FORMS-SPLIT-ENTITY` | scripted | One entity split across several inputs (phone number, one-time code, name). Dates excluded |
   | 8 | `FORMS-FIELD-WIDTH` | scripted | A field of predictable length whose width in markup is far from its expected input |
   | 9 | `FORMS-FORMAT-TOLERANCE` | scripted | A restriction that rejects valid or harmless input |
   | 10 | `FORMS-PASSWORD-RULES` | scripted | A new-password field forcing composition through `pattern`, `minlength` below 8, or any `maxlength` |
   | 11 | `FORMS-CONFIRM-PASSWORD` | scripted | A second "confirm password" field |
   | 12 | `FORMS-ACTION-LABEL` | scripted | A primary submit labelled with a generic word from a fixed set. "Continue" excluded |
   | 13 | `FORMS-RESET-BUTTON` | scripted | A reset or clear-all control in the form |
   | 14 | `FORMS-INPUT-FONT-SIZE` | scripted | A text input below 16px where the artifact's own CSS sets the size |
   | 15 | `FORMS-OPTION-CONTROL` | scripted | A single-choice `select` with fewer than five options |
   | 16 | `FORMS-DATE-SELECTS` | scripted | A memorable date entered through three `select` dropdowns |
   | 17 | `FORMS-PHONE-REASON` | scripted | A required phone field with no adjacent or `aria-describedby` text saying why |
   | 18 | `FORMS-ADDRESS-FORMAT` | scripted | House number and street forced into separate inputs, or a county-style field delivery does not need |
   | 19 | `FORMS-FIELD-NECESSITY` | judged | Fields the task does not need now, information asked twice, or questions that could be deferred |
   | 20 | `FORMS-SINGLE-COLUMN` | judged | Fields side by side so completion order is ambiguous. Severity capped at 2 (mixed evidence) |
   | 21 | `FORMS-LABEL-POSITION` | judged | Labels beside fields on a mobile or short form, or mixed label alignment |
   | 22 | `FORMS-ACTION-HIERARCHY` | judged | A secondary action as prominent as the primary, or actions away from or above the fields |
   | 23 | `FORMS-SELECTION-DEPENDENT` | judged | Every branch's conditional fields exposed at once, or revealed far from their trigger |
   | 24 | `FORMS-TOUCH-TARGET` | judged | Tappable controls too small or too close together for a finger |

2. Scripted criteria decide from markup and declared CSS alone. `FORMS-INPUT-FONT-SIZE` and
   `FORMS-FIELD-WIDTH` report nothing when the artifact does not carry the relevant CSS or
   attribute [S2].
3. Most scripted criteria first work out what a field is for, lexically, from its label, `name`,
   `id` or `autocomplete` token. That is deterministic but heuristic. The generated corpus uses
   vocabulary the heuristic recognizes, so the benchmark alone measures it favourably, and its miss
   and false-alarm rates on real forms are unmeasured [S2].
4. Each scripted finding locates one control. The resolver locates by an element's `id`, tag, class
   or ordinal noun, so every control the corpus generates carries an `id` [S2].

### Namespace and attribution

5. The namespace is `FORMS`, a synthesized rubric admitted under ADR 0035's four conditions [S4].
   `rubric_sources` in `SKILL.md` lists every publisher the rubric draws on, and each criterion's
   row names the sources that state it, graded by strength of evidence, by the handles the
   bibliography uses [S4, S3]. `checks.py`
   passes `["FORMS"]` as its rubric list [S4].
6. No figure the registry lists as untraceable to a primary source is cited as measured, anywhere in
   the skill [S2].

### Scope boundaries

7. Forms does not test ground another shipped skill owns [S2]:
   - label presence (`WCAG-3.3.2`, `NNG-H6-LABELED`);
   - error text and the error summary (`WCAG-3.3.1`, `NNG-H9-IDENTIFY`, the `NNG-EM` set);
   - recovery after an error (`NNG-H9-RECOVER`, `NNG-EM-PRESERVE-INPUT`);
   - when validation fires (`NNG-EM-TIMING`);
   - preventing a wrong entry by constraint (`NNG-H5-PREVENT`, `NNG-EM-PREVENT`). Forms tests only
     the opposite failure, rejecting input that is valid or harmless;
   - consistent naming of one action across a flow (`NNG-H4-CONTROL-NAMING`). Forms tests only
     whether a submit label is specific;
   - a radio or checkbox group's `fieldset` and `legend` (`WCAG-1.3.1`);
   - colour as the only signal (`WCAG-1.4.1`).
8. Two overlaps with `critique-accessibility` are deliberate and recorded [S2, S10].
   `FORMS-AUTOCOMPLETE` tests the attribute WCAG 1.3.5 (Identify Input Purpose) covers.
   `FORMS-TOUCH-TARGET` tests the property WCAG 2.5.8 (Target Size (Minimum)) covers, at larger
   mobile-usability sizes than its 24 by 24 CSS pixel minimum. E67 adds both WCAG criteria to
   accessibility. In each pair, accessibility cites conformance and forms cites the autofill and
   mobile-usability evidence. Each skill's description points to the other for the other angle
   [S2]. Forms grades its autocomplete finding by what happens to autofill, which accessibility's
   pass-or-fail conformance finding cannot: a personal field with no token is severity 2, because
   the browser falls back to guessing and may still fill it; a token outside the standard's
   vocabulary, or `autocomplete="off"` on address or credential data, is severity 3, because
   autofill is certainly broken [S3, S17].
9. Forms borders three siblings. Each pair (forms with accessibility, usability and microcopy) needs
   a boundary clause in both skills' descriptions and contested cases in the joint-routing fixture
   [S2, S6, S13].

### Build, measurement and shipping

10. The skill is built through `askit-build-skill` in fallback mode, per E11 (build through askit),
    and conformance is judged by this repository's pinned gate. Each point of friction with the
    askit procedure is filed to the toolkit's backlog [S11].
11. Before any paid run, the scripted lane is checked against real production forms, because
    Requirement 3 leaves its real-world error rate unmeasured [S2]. The number of forms (at least 10)
    is a judgment [model-inference]. Copies of third-party forms are kept locally and never
    committed, the same rule the research record follows [S3]. The check is a gate, ruled before
    any result exists: a scripted criterion whose false alarms outnumber its correct findings on
    the real forms is fixed or moved to the judged lane before the paid run, and a criterion that
    fires fewer than three times across the set is reported as inconclusive rather than failed
    [S15].
12. Forms and the frozen baseline are measured at k=5 on both pinned tiers, through the shipped
    harness, in one run set [S9, S12]. ADR 0031 found that the shipped harness's sonnet figures do
    not reproduce the committed p3 figures. Measuring both arms in one run set keeps the comparison
    inside one harness [model-inference, drawn from S12].
13. A skill that does not beat the baseline does not ship [S7]. The consistency gate is the rule
    in force on the day the maintainer approves the paid k=5 dispatch: ADR 0022's floor of 0.309
    on the overall lane cut [S8], or E26's per-lane threshold if E26 has replaced it by then [S16].
    Forms' judged-lane consistency is published beside it and does not gate, as ADR 0022 does for
    the judged cut [S16, S8]. Clearing the floor is weak evidence for this skill: 18 of its 24
    criteria are scripted and repeat exactly, so it clears a pooled floor almost by construction,
    and the floor was set on a different run set and harness from the one forms is measured
    through. A pass is not evidence that the judged lane is steady. The comparison that can fail
    forms is AC-12's, against the baseline inside one run set [S16, S12].
14. Every paid dispatch needs the maintainer's go-ahead before it runs [S2].

## Acceptance Criteria

AC-1: `SKILL.md`'s `checks.scripted` and `checks.judged`, and the rows of the skill's `references/`
criterion tables, declare exactly the 24 IDs in Requirements 1, each in the lane shown there. [S2, S5]

AC-2: Every criterion row in `references/` cites the sources the registry lists for it, by
bibliography handle and with the registry's evidence grade, and every handle resolves to a row of the
committed bibliography. [S2, S3, S4]

AC-3: No criterion's operational test in `references/` flags ground listed in Requirements 7. [S2]

AC-4: The `FORMS-AUTOCOMPLETE` and `FORMS-TOUCH-TARGET` rows each name the accessibility criterion
they overlap (WCAG 1.3.5 and 2.5.8 respectively) and state the different reason forms tests it. [S2, S10]

AC-5: An envelope produced through the skill's merge step validates against the contract with
`run.rubrics` equal to `["FORMS"]`. [S4]
  Given: a critique-forms run whose scripted lane emits at least one `FORMS-*` finding and whose
  judged lane emits at least one `FORMS-*` finding
  When: `scripts/merge.py` combines them and the envelope goes through the contract validator
  Then: validation passes and `run.rubrics` is `["FORMS"]`

AC-6: Two runs of the scripted lane over the full forms corpus produce identical output. [S5]

AC-7: The forms corpus module seeds every scripted criterion and at least three judged criteria,
across at least three artifacts, at least one of them clean. [S5, S2]

AC-8: Hand-scored joint-routing results at k=3 on both pinned tiers are committed, covering contested
cases between `critique-forms` and each of `critique-accessibility`, `critique-usability` and
`critique-microcopy`. [S6, S13]

AC-9: Every job in `.github/workflows/ci.yml` passes on the pull request that registers
`critique-forms` in `library.json`. [S6, S14]

AC-10: Before any paid dispatch, a committed report records the scripted lane's findings on at least
10 real production forms, each finding classified as correct or a false alarm, with the misses found
by hand review listed per criterion. [S2, model-inference]
  Given: 10 or more live sign-up, contact, profile or address forms, saved locally with URL, access
  date and sha256
  When: the scripted lane runs on each and a reviewer classifies every finding and hand-checks for
  misses
  Then: the report lists, per criterion, correct findings, false alarms and misses, and records each
  form by URL and hash with no copy of the form committed

AC-11: The README scoreboard shows `critique-forms` and baseline figures at k=5 on both pinned
tiers, from one run set produced by the shipped harness. [S9, S12]

AC-12: A recorded ship or hold verdict cites `critique-forms`' measured figures against the baseline
(seeded recall at equal or better precision, on at least one pinned tier) and against the
consistency gate in force on the day the paid dispatch was approved. On a hold, the skill stays
in the tree marked `incubating`, with its numbers published. [S7, S5, S8, S16]

AC-13: Before any paid dispatch, no scripted criterion that fired three or more times across the
real-forms set has more false alarms than correct findings on it. [S15, S2]

## Behavior / Examples

### Example 1: a scripted finding and its overlap (AC-1, AC-4)

A sign-up form has `<input id="email" name="email" type="text">`. The scripted lane reports
`FORMS-INPUT-TYPE` located at `#email`: the field's purpose, inferred from its `name`, is email, and
`type="text"` does not invoke the email keyboard. The same field has no `autocomplete` token, so
`FORMS-AUTOCOMPLETE` fires too, citing the autofill completion evidence. Once E67 lands,
`critique-accessibility` reports the missing token as a WCAG 1.3.5 conformance failure. The two
findings name the same attribute for different reasons, which is the recorded overlap.

A valid `autocomplete` value is not always one word. The HTML standard's grammar allows an
optional `section-` group, an optional `shipping` or `billing` token, a contact type such as
`work` or `mobile` before a telephone or email field, the field name itself, and an optional
trailing `webauthn` [S3]. So `section-blue shipping street-address` and `work tel` are both
valid, and `FORMS-AUTOCOMPLETE` judges a value against that grammar, not against a flat list of
field names. A flat-list check would flag valid values and fail the real-forms gate (AC-13).

### Example 2: ground forms leaves alone (AC-3)

A form has an input with no label, a required field whose error message says only "Invalid", and a
submit button labelled "Submit". Forms reports `FORMS-ACTION-LABEL` on the button. It reports nothing
about the missing label (`WCAG-3.3.2` and `NNG-H6-LABELED` own it) or the error text (the `NNG-EM`
set owns it).

### Example 3: where a row's sources go (AC-2)

The template says the Operationalization column cites its source by `rubric_sources.id`, and the
shipped skills do, for example "(NNG-HEURISTICS, heuristic 1)" [S6]. ADR 0035 moves `FORMS`
attribution to the row at source level [S4], so a forms row cites article-level handles instead,
for example `FORMS-INPUT-TYPE` citing `baymard-mobile-touch-keyboards` (LS) and
`webdev-signin-form` (OG), while `rubric_sources` lists the publishers behind those handles. The
self-test checks neither granularity: it validates each `rubric_sources` entry's fields and the
Operationalization column's quotation marks, not the citations themselves (checked 2026-09-25), so
AC-2 is verified by review or by a script over the rows and the bibliography.

### Example 4: a routing contest (AC-8)

"Can you review the usability of this sign-up form?" is contested between `critique-forms`
and `critique-usability`. Each description's boundary clause names the other, and the joint-routing
fixture records the expected winner and the sibling it is contested with.

## Non-Functional Requirements

| Category | Requirement | Source |
|----------|-------------|--------|
| Copyright | Every Operationalization cell is paraphrase with zero quotation marks, and no quoted span anywhere in `references/` exceeds the self-test's threshold | [S6] |
| Copyright | No copy of a research source or a real-world form is committed; only the bibliography and URLs with hashes | [S3] |
| Cost | Every paid k=5 dispatch is approved by the maintainer before it runs | [S2] |
| Reproducibility | Every live bench run passes `--model` explicitly and writes to a fresh `--out-dir` | [S14] |

## Revisions

| Date | Author | Type | Description |
|------|--------|------|-------------|
| 2026-09-25 | Claude (plab-spec) | added | Initial draft from the ruled criterion registry, revision 2 |
| 2026-09-25 | Claude (plab-spec) | added | D1 (real-forms threshold) ruled Option A: Requirements 11 extended, AC-13 added |
| 2026-09-25 | Claude (plab-spec) | clarified | D2 (consistency gate) and D3 (keep `FORMS-AUTOCOMPLETE`) ruled Option A: Requirements 13 rewritten from the D2 ruling and AC-12 names the gate in force on the dispatch approval day; Requirements 8 gains the D3 severity grading; Example 1 gains the autofill grammar note |

## Sources & Evidence

- **[S1]** N2 (critique-forms) backlog entry, including its "Done looks like" bar (the same as
  N1's) - `docs/internal/backlog/new-components.md`, section "N2 - critique-forms" - class A
- **[S2]** Criterion registry, revision 2, all decisions ruled 2026-09-25 -
  `docs/internal/release-plans/_unassigned/N2_critique-forms/criterion-registry-draft.md` - class A
- **[S3]** Bibliography, 75 sources with URL or ISBN, access date and sha256 -
  `docs/internal/release-plans/_unassigned/N2_critique-forms/sources.md` - class A
- **[S4]** ADR 0035, a namespace may name a synthesized rubric -
  `docs/internal/decisions/0035-synthesized-rubric-namespace.md` - class A
- **[S5]** S-05 (skills slate) spec, the precedent for criterion-registry, determinism, corpus and
  ship-or-hold criteria - `docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md` - class A
- **[S6]** Skill template, including its criterion-table format and end-to-end build checklist -
  `docs/internal/skill-template.md` - class A
- **[S7]** Methodology, "A skill that does not beat the baseline does not ship" -
  `docs/explanation/methodology.md` - class A
- **[S8]** ADR 0022, consistency floor 0.309 on the overall lane cut -
  `docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md` - class A
- **[S9]** v0.2.0 shape ruling and its exit-gate clause for `critique-forms` -
  `docs/internal/release-plans/v0.2.0-shape-options.md` - class A
- **[S10]** E67 (accessibility expansion), ruled 2026-09-25 - `docs/internal/backlog/enhancements.md`,
  section "E67" - class A
- **[S11]** E11 (askit-* authoring and CodeQL), ruled 2026-09-15 -
  `docs/internal/backlog/enhancements.md`, section "E11" - class A
- **[S12]** ADR 0030 (bench harness through the Claude Code CLI, amended) and ADR 0031 (fidelity
  gate acceptance band, sonnet result) -
  `docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md`,
  `docs/internal/decisions/0031-fidelity-gate-acceptance-band.md` - class A
- **[S13]** Eval fixtures, including joint-routing case kinds and hand-scoring - `evals/README.md` -
  class A
- **[S14]** Agent navigation entrypoint, CI job table and bench run rules - `AGENTS.md` - class A
- **[S15]** Maintainer ruling on D1 (real-forms threshold), 2026-09-25 - this spec, Open Questions,
  D1 - class A
- **[S16]** Maintainer ruling on D2 (consistency gate for a v0.2.0 skill), 2026-09-25 - this spec,
  Open Questions, D2 - class A
- **[S17]** Maintainer ruling on D3 (keep `FORMS-AUTOCOMPLETE`, graded by effect on autofill),
  2026-09-25 - this spec, Open Questions, D3 - class A

### Unverified Claims

- "The number of forms (at least 10) is a judgment" - appears in Requirements 11 and AC-10
- "Measuring both arms in one run set keeps the comparison inside one harness" - appears in
  Requirements 12

### Gaps

- The research notes' guideline paraphrases were never checked against their sources (only quotes
  and figures were). A seeded 10% sample was checked for this spec; see Fidelity check. The other
  90% remain unchecked.
- Baymard's five-option threshold (`FORMS-OPTION-CONTROL`) comes from checkout research; no
  non-checkout study was found [S2].

### Fidelity check

Run 2026-09-25, for this spec. **What was checked:** the research notes' `guideline` paraphrases
against the saved source copies they came from. **What was not:** the registry's own evidence
prose [S2], which paraphrases those notes a second time.

- **Population:** the 408 of 470 note lines whose source the registry's evidence section cites
  (54 handles, plus the two books cited by page).
- **Sample:** 41 lines (10%), drawn at random with seed 20260925, so the draw can be repeated.
- **Method:** a separate checker located each line's quoted passage in the saved copy (web pages
  as saved, books and PDFs through their text conversions), read the surrounding passage, and
  judged meaning, strength and scope.
- **Result: 41 of 41 within tolerance (38 exact, 3 mildly strengthened).** Every quote was found
  at its locator. The checker judged the three strengthenings faithful; they are listed here so the
  reader can judge them too. A `webdev-signin-form` line drops
  the source's "probably" from its advice to put labels above inputs. A Wroblewski line turns
  the book's observation that list boxes are rarely used into advice to avoid them. A second
  Wroblewski line adds disabling the button as an example of preventing a duplicate submission.
- **Registry impact: none.** The first line is one of two official-guidance sources behind
  `FORMS-LABEL-POSITION`, which the registry lists without quoting or grading up the hedge. The
  list-box rule is among the criteria the registry defers. Duplicate-submission prevention is not
  a criterion.

## Open Questions

| ID | Title | Resolution | Status | Updated |
|----|-------|------------|--------|---------|
| D1 | Real-forms threshold | Option A, with a three-firing minimum | Decided | 2026-09-25 |
| D2 | Consistency gate for a v0.2.0 skill | Option A, gate fixed on the dispatch approval day | Decided | 2026-09-25 |
| D3 | Keep `FORMS-AUTOCOMPLETE` | Option A, severity graded by effect on autofill | Decided | 2026-09-25 |

### D1: Real-forms threshold (Decided)

**Summary.** What result from the real-forms report (AC-10) blocks the paid dispatch?

**Context.** AC-10 makes the check happen and publishes it, but sets no bar. Without one, a scripted
criterion that misfires on most real forms could still go to measurement, where the generated
corpus will flatter it (Requirements 3).

**Desired outcome.** A rule, set before the report exists, saying what a scripted criterion must
show on real forms to go to the paid run unchanged.

**Options / approaches.**

* **Option A:** per criterion, if false alarms outnumber correct findings, fix its operational test or
  move it to the judged lane before dispatch. Simple and pre-registered, but noisy on criteria that
  fire rarely.
* **Option B:** no gate; publish the figures beside the benchmark numbers as a caveat. Cheapest, but
  ships a known-noisy criterion.

**Recommendation.** Option A, with criteria that fire fewer than three times across the set reported
as inconclusive rather than gated.

---

> **Maintainer decision:** Option A
>
> * **Status:** Decided
> * **Choice:** Option A. A criterion that fires fewer than three times across the set is reported
>   as inconclusive rather than failed.
> * **Reasoning:** Agreed with the recommendation.
> * **Decided by / date:** Jonathan Prisant, 2026-09-25

### D2: Consistency gate for a v0.2.0 skill (Decided)

**Summary.** Does ADR 0022's 0.309 overall-lane floor gate `critique-forms`?

**Context.** ADR 0022 set the floor for v0.1.0 stretch skills. E26 (consistency threshold v2) may
replace it with a per-lane threshold, and nothing yet says which gate applies to a skill added in
v0.2.0.

**Desired outcome.** The gate is named before forms is measured, so the verdict cannot be fitted to
the result.

**Options / approaches.**

* **Option A:** apply 0.309 overall unless E26 lands first, in which case apply E26's threshold.
* **Option B:** wait for E26. Cleaner, but it blocks forms on an item with no scheduled slot.

**Recommendation.** Option A. It is the only floor with a published method today, and it falls back
to E26 without reopening this spec.

---

> **Maintainer decision:** Option A
>
> * **Status:** Decided
> * **Choice:** Option A. The gate is whichever rule is in force on the day the maintainer
>   approves the paid k=5 dispatch: 0.309 on the overall lane cut, or E26's threshold if it has
>   landed. Forms' judged-lane consistency is published beside it and does not gate.
> * **Reasoning:** Agreed with the recommendation, sharpened on review. A 75% scripted skill
>   clears a pooled floor almost by construction, and the floor comes from a different run set
>   and harness, so a pass must not be read as evidence the judged lane is steady. AC-12's
>   baseline comparison is the test that can fail forms. The only judged-lane floor on record,
>   0.090, is one ADR 0022 itself calls no gate, so the judged figure is published, not gated.
> * **Decided by / date:** Jonathan Prisant, 2026-09-25

### D3: Keep `FORMS-AUTOCOMPLETE` (Decided)

**Summary.** Keep `FORMS-AUTOCOMPLETE` as a deliberate overlap, or leave `autocomplete` to
`critique-accessibility` alone?

**Context.** The registry keeps it by ruling (decision 4), and the last session parked a possible
reversal as reversible at spec time [S2]. Once this spec is committed, dropping it is a spec revision.

**Desired outcome.** A settled criterion list before the build starts.

**Options / approaches.**

* **Option A:** keep it. The conversion evidence is forms' own, and the overlap is recorded on both
  sides.
* **Option B:** drop it, leaving 23 criteria (17 scripted). This removes a double finding on one
  attribute, but loses the only criterion carrying autofill conversion evidence.

**Recommendation.** Option A, as already ruled.

---

> **Maintainer decision:** Option A
>
> * **Status:** Decided
> * **Choice:** Option A. Keep the criterion, with severity graded by its effect on autofill:
>   a missing token is severity 2, a token outside the standard or `off` on address or
>   credential data is severity 3.
> * **Reasoning:** Agreed with the recommendation. The grading is what forms adds that
>   accessibility's pass-or-fail conformance finding cannot, which makes the overlap two
>   findings rather than one found twice.
> * **Decided by / date:** Jonathan Prisant, 2026-09-25
