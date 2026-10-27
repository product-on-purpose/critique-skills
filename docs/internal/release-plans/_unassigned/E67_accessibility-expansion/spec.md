---
id: E67
title: "Accessibility expansion: add the WCAG 2.2 Level AA criteria checkable from static markup"
type: spec
status: committed
created: 2026-10-26
updated: 2026-10-27
linked-effort: docs/internal/backlog/enhancements.md
linked-plan: null
linked-release: null
ac-count: 10
source-count: 23
requires-human-review: true
spec-dependencies: ["E73"]
target-release: v0.3.0
---

# Spec: accessibility expansion

Ruled by the maintainer on 2026-10-27 (the nine decisions below) and built the same day. The build
covers requirements 1 through 5, 7 and 8, D1 through D9, and AC-1 through AC-10. Requirement 6, the
version move, waits for the shared paid re-measure. E73's spec gives the reason under "Versions": the
site shows only cells measured at a skill's active version, so a move without new results would blank
the skill's published figures.

## Task Summary

**Status:** built 2026-10-27; the version move and the paid re-measure stay open, pending the
maintainer's go
**Last updated:** 2026-10-27 by Claude, build
**Linked plan:** not yet planned
**Open questions:** 0 (all nine were decided 2026-10-27; see Open Questions / Decisions)
**Revisions:** 2 (2026-10-27: moved from the local draft; D1's Option D, presented in the walk, added
to its options list; Scope, Non-Goals, Requirement 6, "What changes in each file", "Measurement and
sequencing", AC-5, AC-9 and "What I do not know" rewritten to the ruling; AC checklist updated to the
build. 2026-10-27, adversarial-review fixes: a third base defect, the promo-code error span's
missing live region, found and fixed, moving the live-vs-frozen diff from three attributes to four;
Requirement 7 and AC-3 reworded to name the coverage guard's own literals that did change; a new
"Build notes" section; D9's free local check recorded as run, not planned)

### Acceptance Criteria Fulfillment

- [x] **AC-1** - `SKILL.md`'s combined `checks.scripted` and `checks.judged` lists hold exactly 27
  WCAG IDs, the current 22 plus the five this spec names
- [x] **AC-2** - Each new criterion's row in `references/WCAG.md` carries all seven required columns,
  with zero quotation marks in Operationalization
- [x] **AC-3** - `test_wcag_scope_accessibility.py` passes with no edit to its own level-A/AA constant
  sets; its `UNCHECKED_HEADING` string and `len(registry) == 27` literal change along with
  `SKILL.md` and `WCAG.md`
- [x] **AC-4** - Every criterion kept scripted gets a `checks.py` function and a passing test case;
  every criterion kept judged gets neither
- [x] **AC-5** - D1's Option D is built: the shared form fixed, `accessibility-005` added, and
  today's four artifacts frozen so the committed run sets still score
- [x] **AC-6** - Each new scripted criterion's threshold is restated in `severity-anchors.md`,
  "Thresholds the scripted lane applies"
- [x] **AC-7** - The `critique-forms` overlap on WCAG-1.3.5 and WCAG-2.5.8 is recorded in
  `WCAG.md`, and `enhancements.md`'s E67 entry's "one such overlap, unrecorded" sentence is updated
- [x] **AC-8** - Every scope-claim citation moves from "22 of the 55" to "27 of the 55"
- [x] **AC-9** - `golden-06` covers the five new criteria, `golden-01` and `golden-05` carry their
  WCAG-1.3.5 findings, and each location resolves under `bench.metrics.resolve_html`
- [x] **AC-10** - The shared E73-and-E67 paid dispatch is drafted with exact envelope counts and
  marked as needing the maintainer's own go before it runs

## Purpose

`critique-accessibility` checks 22 of WCAG 2.2's 55 Level A and AA success criteria. The maintainer
ruled on 2026-09-25 to expand it, naming five criteria that are checkable from static markup and
declared CSS and are not yet implemented: 1.3.4 Orientation, 1.3.5 Identify Input Purpose, 2.4.7
Focus Visible, 2.5.8 Target Size (Minimum), and 4.1.3 Status Messages [S1]. That ruling fixed *which*
criteria and *that* two of them come first. It left open *how* each one is checked, whether its lane
is scripted or judged, how the corpus grows to exercise it, and how the deliberate overlap with
`critique-forms` gets written down. This spec frames those nine open decisions so the maintainer can
rule them in one pass, the way E73's spec framed six decisions about the merge step before anyone
built it [S16].

## Scope

- `skills/critique-accessibility/SKILL.md`: the `checks.scripted` and `checks.judged` frontmatter
  lists, the description, and the scope paragraph.
- `skills/critique-accessibility/references/WCAG.md`: five rows move from "The 33 criteria this
  skill does not check" into the registry table, each filled in per the template's seven-column
  format; the overlap with `critique-forms` is recorded for the two criteria that border it.
- `skills/critique-accessibility/scripts/checks.py`: one function per criterion D2 through D6 keeps
  scripted, plus its test case in `scripts/tests/test_checks_accessibility.py`.
- `skills/critique-accessibility/references/severity-anchors.md`: a new bullet per scripted
  criterion's threshold, in "Thresholds the scripted lane applies".
- `bench/generator/domains/accessibility.py` and `bench/corpus/accessibility/`: D1's Option D. The
  shared form builder gives the email and phone fields `autocomplete` tokens, the status card
  `role="status"`, and the promo-code error span `aria-live="polite"`, and a new
  `accessibility-005` carries the five plants.
- `bench/corpus/_frozen/v1/accessibility/`: a frozen copy of today's `accessibility-001` to `004`
  artifacts and manifests, so the committed run sets still score. `bench/generator/verify.py`
  leaves it out of regeneration, and a test guards its integrity.
- `skills/critique-accessibility/examples/`: a new `golden-06` covering the five new criteria, and the
  WCAG-1.3.5 findings `golden-01` and `golden-05` now carry.
- `skills/critique-forms/references/FORMS.md`: the two overlapping rows' "once E67 adds it" becomes
  present tense.
- `README.md`, `skills/critique-accessibility/README.md`, `docs/reference/criterion-ids.md`: the
  scope-claim citations and the overlap-registry sentence.
- `library.json`, `SKILL.md`'s `metadata.version`, and `checks.py`'s `skill_version=` argument: one
  version move to 0.2.0, shared with E73's own version move, per E73's ruled D4 [S16]. It is not in
  this build; it lands with the shared paid re-measure (Requirement 6).
- The shared paid dispatch this spec and E73 both feed, drafted here with envelope counts.

## Non-Goals

- **No criterion is added beyond the five this spec names**, unless D8 rules otherwise. The four
  criteria this skill already declares out of reach (2.1.2, 2.2.1, 2.5.1, 2.5.7) stay out of reach;
  nothing here revisits that boundary.
- **No version moves in this build.** Requirement 6's move to 0.2.0 waits for the shared paid
  re-measure, so the skill keeps 0.1.1 until then.
- **No paid model call happens here or from this spec.** The envelope counts under AC-10 are a plan,
  not a run; `python bench/run_bench.py` is never invoked without `--dry-run` from this work.
- **No change to `skills/_shared/merge.py` or to the merge-step fix.** That is E73's build, which
  this spec treats as a binding prerequisite, not as something to re-litigate.
- **No change to `critique-forms`'s own criteria, thresholds, or lane assignments.** `FORMS-AUTOCOMPLETE`
  and `FORMS-TOUCH-TARGET` already name this expansion in their own rows [S12]; this spec records the
  mirror image in `critique-accessibility`'s registry, nothing more. The one edit there is tense: both
  rows said the WCAG criterion arrives "once E67 adds it", and now it has.

## Requirements

These restate what the maintainer has already ruled. None of them is open; each cites where the
ruling lives.

1. **The expansion adds exactly these five criteria, at minimum:** WCAG-1.3.4 (Orientation),
   WCAG-1.3.5 (Identify Input Purpose), WCAG-2.4.7 (Focus Visible), WCAG-2.5.8 (Target Size
   (Minimum)), and WCAG-4.1.3 (Status Messages). All five are confirmed Level AA against the W3C
   Recommendation's own text, read 2026-10-26 (verified; see Sources S21). [S1]
2. **WCAG-1.3.5 and WCAG-2.5.8 are built first**, because both border `critique-forms`'s existing
   criteria (`FORMS-AUTOCOMPLETE` and `FORMS-TOUCH-TARGET`). [S1]
3. **Each new ID is the upstream WCAG number, adopted verbatim**, per `criterion-ids.md`'s
   permanence rule 3 ("adopt upstream IDs where they exist"). No criterion is split into more than
   one ID: WCAG-2.5.8's several named exceptions (Spacing, Equivalent, Inline, User Agent Control,
   Essential) stay inside one `WCAG-2.5.8` finding, per permanence rule 4 ("one criterion, one ID").
   This is a closed question, not an open one: the grammar leaves no room for a different choice.
   (Verified.) [S13]
4. **The paid re-measure needs its own approval**, separate from this spec and separate from any
   ruling this spec's decisions produce. Drafting the dispatch (AC-10) is not running it. [S1]
5. **One dispatch measures all seven skills, after E73's build and this spec's build both land.**
   E73's spec fixed the order: "E73's ruling, E73's build, E67's build, then one dispatch for all
   seven skills" [S16]. This spec does not reopen that order; it sizes the dispatch D1 produces.
6. **`critique-accessibility` moves its version once, to 0.2.0**, carrying both E73's merge-step fix
   and this expansion, per E73's ruled D4. Three places move together: `metadata.version` in
   `SKILL.md`, the `library.json` entry (currently `0.1.1`, line 11), and `checks.py`'s
   `skill_version="0.1.1"` argument. This build does not move them. The move lands with the shared
   paid re-measure, for the reason E73's spec gives under "Versions". [S16, S20]
7. **The coverage guard's criteria sets stay self-updating; its own string and count literals do
   not.** `test_wcag_scope_accessibility.py`'s `WCAG22_LEVEL_A` and `WCAG22_LEVEL_AA` constant sets,
   which name all 55 Level A and AA criteria, need no edit as the registry grows: the
   disjoint-and-complete assertion reads the registry and the unchecked table from the live files
   rather than from a count anyone has to update by hand [S17]. The test's own `UNCHECKED_HEADING`
   string and its `len(registry) == 27` literal are not self-updating in that sense, and this
   build's row-moves between the two tables do change both.
8. **The corpus question is this spec's to frame, not the backlog's to answer.** The 2026-09-25
   ruling named it explicitly as open: "a measurement-design question to settle in the spec, not
   here" [S1]. D1 frames it.

## What changes in each file

| Component | File | Change | Depends on |
|---|---|---|---|
| Registry | `skills/critique-accessibility/SKILL.md`, frontmatter `checks:` | 5 IDs added, filed by D2-D6's lanes | D2, D3, D4, D5, D6 |
| Scope paragraph | `SKILL.md`, body | "22 of the 55" to "27 of the 55" | Requirement 1 |
| Registry table | `references/WCAG.md` | 5 rows move from "does not check" into the table | D2-D6, D7 |
| Unchecked table | `references/WCAG.md`, "The 33 criteria..." | Heading becomes "The 28 criteria...", 5 rows removed | D8 |
| Overlap note | `references/WCAG.md` | New sentence per D7's choice, on the two bordering rows | D7 |
| Scripted checks | `scripts/checks.py` | One function per criterion D2-D6 keep scripted | D2, D3, D4, D5, D6 |
| Script tests | `scripts/tests/test_checks_accessibility.py` | One case per new scripted criterion | D2, D3, D4, D5, D6 |
| Thresholds | `references/severity-anchors.md`, "Thresholds..." | One bullet per new scripted criterion | D2, D3, D4, D5, D6 |
| Corpus | `bench/generator/domains/accessibility.py`, `bench/corpus/accessibility/` | Shared form and status card fixed; five injectors; `accessibility-005` | D1 |
| Frozen corpus | `bench/corpus/_frozen/v1/accessibility/`, `bench/generator/verify.py` | Today's four artifacts and manifests, kept for the committed run sets | D1 |
| Goldens | `skills/critique-accessibility/examples/` | `golden-06` added; WCAG-1.3.5 findings added to `golden-01` and `golden-05` | AC-9 |
| Scope citations | `README.md`:161, `skills/critique-accessibility/README.md`:7 | "22" to "27" | Requirement 1 |
| Overlap registry | `docs/internal/backlog/enhancements.md` | "one such overlap, unrecorded" sentence (E67 entry's "Why" bullet) updated | D7 |
| Forms overlap tense | `skills/critique-forms/references/FORMS.md` | "once E67 adds it" to present tense, in two rows | D7 |
| Version | `library.json`:11, `SKILL.md` `metadata.version`, `checks.py`'s `skill_version=` | `0.1.1` to `0.2.0`, not in this build | Requirement 6 (shared with E73; lands with the re-measure) |

## Measurement and sequencing with E73

**The existing corpus.** Before this build, `bench/README.md`'s corpus design table counted 27 scored
artifacts across seven skills: 4 each for clarity, accessibility, usability, docs, microcopy and forms, and 3 for
argument [S10]. At k=5 on two pinned tiers, that is 270 skill envelopes; E73's own spec adds a
baseline re-run inside the same dispatch, for 270 more, 540 total [S16].

**What D1's Option D adds to that figure.** One new artifact raises the total by 2 tiers x 5 reps x 2
(a skill envelope and a baseline envelope) = 20 envelopes. The frozen copy adds none:
`bench/run_bench.py` reads each domain's directory without descending into subfolders, so no frozen
artifact is ever dispatched. [S10, S16]

| Corpus | Artifacts | Skill envelopes | Baseline envelopes | Grand total |
|---|---|---|---|---|
| Before this build | 27 | 270 | 270 | 540 |
| After this build (D1, Option D) | 28 | 280 | 280 | 560 |

**Why the existing four were edited and also kept.** Each of the four existing artifacts carried two
real WCAG-1.3.5 failures: email and phone fields with no `autocomplete` token, from one shared
builder. The clean `accessibility-004` was among them. The bench counts a correct but unplanted
finding against precision [S10], so leaving them would have charged the new scripted check eight
false positives per pass over the four, two of them on the clean artifact. The same builder's status
card sits beside a "Refresh status" button with no live-region role, which a model judging
WCAG-4.1.3 could flag on every artifact. An adversarial review after the first pass found a third
instance of the same WCAG-4.1.3 shape: the builder's promo-code error span sits beside
`aria-invalid="true"` with no live region either, on every live artifact including the clean
`accessibility-004`, which is exactly the pattern WCAG-4.1.3's severity-2 anchor names. The build
fixes all three in the builder, so each of the four artifacts changes by those four attributes and
nothing else: both `autocomplete` tokens, the status card's `role="status"`, and the promo-code
error span's `aria-live="polite"`. Editing an artifact changes its `artifact_sha256`, and scoring
joins an envelope to its manifest by that hash, silently skipping an envelope it cannot match [S23].
The frozen copy keeps today's bytes and manifests, so every committed run set still scores and still
reproduces `results.json` and `variance.json`.

**What a replay cannot do here.** E73's own D5 ran a free replay over committed envelopes before
paying for a dispatch, because the merge-step fix could be sized from historical data with no model
call [S16]. The five criteria this spec adds have no historical envelopes: no model has ever been
asked to judge WCAG-1.3.4, 1.3.5, 2.4.7, 2.5.8, or 4.1.3 against any artifact in this corpus, so there
is nothing to replay. A replay can still size E73's own change on the other 22 criteria before the
shared dispatch runs; it cannot preview how a model performs on the five new ones. D9 frames this.

**The shared paid dispatch, drafted (AC-10).** One dispatch measures all seven skills after E73's build
and this one: 28 corpus artifacts, k=5, on the two pinned tiers, with E73's baseline re-run inside it,
for 280 skill envelopes and 280 baseline envelopes, 560 in total [S16]. D9's free local check has
run, as D9 ruled, ahead of this dispatch's approval: `checks.py` against every live accessibility
artifact. On each of the five, the scripted lane's findings equal exactly the planted scripted defects, with
WCAG-1.3.5 firing once, on `accessibility-005`'s `#email`
(`bench/tests/test_accessibility_scripted_precision.py` now holds this as a standing regression
guard). The same `checks.py` run against the four frozen copies, which keep the pre-fix bytes on
purpose, draws two WCAG-1.3.5 findings each, on the shared builder's old email and phone fields with
no `autocomplete` token, the base defect the corpus fix removed from every live artifact. **The
dispatch needs the maintainer's own explicit go before `bench/run_bench.py` runs without
`--dry-run`.** Until it runs, envelopes produced from `main` carry the new criteria under the skill's
old version number, so no other dispatch should run first.

## Build notes

- **WCAG-2.4.7's plant uses an inline style, not a `:focus` rule.** D5's maintainer follow-up asked
  for "an `outline: none` rule on `:focus`"; `accessibility-005`'s plant instead sets
  `style="outline:none"` directly on a standalone link (technique F78), which the Operational
  test covers: it reads the stylesheet and inline styles alike. `checks.py`'s CSS engine matches
  no pseudo-class selector at all, so a scripted test could never see a `:focus` rule either way, and
  the judged lane reads declared styles, inline or in a stylesheet, the same way.
- **The build fixed a third base defect beyond D1's Option D: the promo-code error span's missing
  live region.** An adversarial review, after the first build pass, found that span sitting beside
  `aria-invalid="true"` with no live region on every live artifact, including the clean
  `accessibility-004`, which is exactly the pattern WCAG-4.1.3's severity-2 anchor names (see "Why
  the existing four were edited and also kept"). The shared builder now gives that span
  `aria-live="polite"` unconditionally, the same way it already fixed the autocomplete and
  `role="status"` gaps, so the four live artifacts differ from their frozen counterparts by exactly
  four attribute additions, not three.

## Acceptance Criteria

AC-1: `SKILL.md`'s combined `checks.scripted` and `checks.judged` lists hold exactly 27 WCAG IDs:
today's 22 plus WCAG-1.3.4, WCAG-1.3.5, WCAG-2.4.7, WCAG-2.5.8, and WCAG-4.1.3, each filed into the
lane D2 through D6 selects. [S3]

AC-2: Each new criterion's row in `references/WCAG.md` carries all seven columns docs/internal/
skill-template.md's "Criterion tables" section requires (ID, Operationalization, Operational test,
Severity 2 anchor, Severity 3 anchor, Lane, Lane rationale), with zero quotation marks in the
Operationalization column. [S4, S14]

AC-3: `scripts/tests/test_wcag_scope_accessibility.py` passes after the build, with no edit to its
own `WCAG22_LEVEL_A` or `WCAG22_LEVEL_AA` constant sets. `SKILL.md`'s frontmatter and `WCAG.md`'s
unchecked-criteria table change, and so do two of the test's own literals that name a count rather
than deriving one, its `UNCHECKED_HEADING` string and its `len(registry) == 27` assertion; the
disjoint-and-complete assertion still holds over all 55 criteria. [S17]

AC-4: Every criterion D2 through D6 keep scripted gets a `scripts/checks.py` function, entered in
`IMPLEMENTED_CRITERIA`, and a passing case in `scripts/tests/test_checks_accessibility.py`; every
criterion kept judged gets neither, and is swept instead in `SKILL.md`'s protocol pass 2. [S5, S7]

AC-5: D1's Option D is built. The shared form builder gives the email and phone fields `autocomplete`
tokens, the status card `role="status"`, and the promo-code error span `aria-live="polite"` (a third
WCAG-4.1.3 base defect an adversarial review found after the first pass), and those four attributes
are the only change to `accessibility-001` through `004`. A new `accessibility-005` carries one
planted instance of each of
the five criteria, consistent with "At most one planted defect per criterion per section, or per
top-level `<section>` in HTML." Today's four artifacts and manifests are kept under
`bench/corpus/_frozen/v1/accessibility/`, and the documented variance command still reproduces the
committed `variance.json` from the committed run sets. [S9, S10, S23]

AC-6: Each new scripted criterion's threshold is restated in `references/severity-anchors.md`,
"Thresholds the scripted lane applies," in the style already used for WCAG-1.4.10 and WCAG-1.4.12.
[S19]

AC-7: The overlap between WCAG-1.3.5 and `FORMS-AUTOCOMPLETE`, and between WCAG-2.5.8 and
`FORMS-TOUCH-TARGET`, is recorded in `references/WCAG.md` per D7's choice, and
`docs/internal/backlog/enhancements.md`'s E67 entry's sentence "The library already carries one such
overlap, unrecorded" is updated to name these two as now recorded, alongside the existing WCAG-3.3.2
/ NNG-H6-LABELED pair. [S1, S11, S12]

AC-8: Every scope-claim citation ("22 of the 55") moves to "27 of the 55": `SKILL.md`'s description
and scope paragraph, `README.md`:161, `skills/critique-accessibility/README.md`:7, and
`references/WCAG.md`'s "Scope" heading paragraph. [S18]

AC-9: A new `golden-06` covers the five new criteria. `golden-01` and `golden-05`, whose artifacts
have email or phone fields with no `autocomplete` token, carry the WCAG-1.3.5 findings `checks.py` now
emits on them. Each location resolves under `bench.metrics.resolve_html`, following the precedent ADR
0027 set when it regenerated all five goldens for the 0.1.1 location-emission fix. [S15]

AC-10: The shared E73-and-E67 paid dispatch is drafted with the exact envelope counts the
"Measurement and sequencing" table above gives for D1's chosen option, and is marked, in whatever
document carries it forward, as needing the maintainer's own explicit go before `bench/run_bench.py`
runs without `--dry-run`. [S1, S16]

## Sources & Evidence

- **[S1]** The E67 ruling, change description and corpus-design note -
  `docs/internal/backlog/enhancements.md`, section "E67" - class A
- **[S2]** The E68 ruling, closed 2026-10-15 (scope-narrowing precedent this expansion mirrors in
  reverse) - `docs/internal/backlog/enhancements.md`, section "E68" - class A
- **[S3]** The skill's frontmatter `checks:` lists and scope paragraph -
  `skills/critique-accessibility/SKILL.md` - class A
- **[S4]** The registry, its Scope section, and "The 33 criteria this skill does not check" -
  `skills/critique-accessibility/references/WCAG.md` - class A
- **[S5]** The scripted lane's CSS-engine scope, including that a `:focus` or other pseudo-class
  selector is never matched - `skills/critique-accessibility/scripts/checks.py`, module docstring,
  - class A
- **[S6]** The declared-width/height machinery already used for WCAG-1.4.10 and WCAG-1.4.12 -
  `skills/critique-accessibility/scripts/checks.py` - class A
- **[S7]** `IMPLEMENTED_CRITERIA` and the `skill_version` argument -
  `skills/critique-accessibility/scripts/checks.py` - class A
- **[S8]** The bench injectors (13 scripted-lane and 4 judged-lane before this build, 14 and 8 after),
  and the recipe comment stating the >=3-judged-criteria floor -
  `bench/generator/domains/accessibility.py` - class A
- **[S9]** Planted-defect counts per artifact (7, 6, 4 and 0 before this build; `accessibility-005`
  adds 5) -
  `bench/corpus/accessibility/accessibility-00{1,2,3,4}.manifest.json` - class A
- **[S10]** The corpus design table (27 artifacts before this build, 28 after, 7 skills), the
  conservative precision rule, and the per-section planted-defect
  invariant - `bench/README.md`, "Corpus design" and "Invariants" - class A
- **[S11]** The deliberate overlap, stated from the forms side - `skills/critique-forms/SKILL.md`,
  lines 142-145 - class A
- **[S12]** The two overlapping rows, each already naming "once E67 adds it" -
  `skills/critique-forms/references/FORMS.md`, lines 192 (`FORMS-AUTOCOMPLETE`) and 212
  (`FORMS-TOUCH-TARGET`) - class A
- **[S13]** The criterion-ID grammar, permanence rules, and namespace registry -
  `docs/reference/criterion-ids.md` - class A
- **[S14]** "Scripted lane discipline" and "Criterion tables" -
  `docs/internal/skill-template.md`, lines 463-520 - class A
- **[S15]** The version-move and golden-regeneration precedent -
  [ADR 0027 (accessibility location-emission calibration)](../../../decisions/0027-accessibility-location-emission-calibration.md) -
  class A
- **[S16]** E73's ruled spec: the build order, D4's version move, and the dispatch-cost math -
  [E73's spec](../E73_merge-runs-scripted-lane/spec.md) - class A (ruled 2026-10-23, built in PR 105
  under ADR 0041; its version moves and re-measure are not built)
- **[S17]** The self-updating coverage guard -
  `skills/critique-accessibility/scripts/tests/test_wcag_scope_accessibility.py` - class A
- **[S18]** The "22 of the 55" scope-claim citations outside the skill's own files -
  `README.md`:161, `skills/critique-accessibility/README.md`:7 - class A
- **[S19]** "Thresholds the scripted lane applies" -
  `skills/critique-accessibility/references/severity-anchors.md`, lines 54-93 - class A
- **[S20]** The skill's `library.json` version entry - `library.json`:11 - class A
- **[S21]** W3C WCAG 2.2 (Recommendation), fetched 2026-10-26: normative text and Level AA
  confirmed for all five criteria (1.3.4, 1.3.5, 2.4.7, 2.5.8, 4.1.3) -
  https://www.w3.org/TR/WCAG22/ - class A
- **[S22]** The WCAG 2.2 Understanding pages for the five criteria, fetched 2026-10-26: sufficient
  and failure techniques, exceptions, and static-detectability notes -
  https://www.w3.org/WAI/WCAG22/Understanding/{orientation, identify-input-purpose, focus-visible,
  target-size-minimum, status-messages}.html - class A
- **[S23]** The join of an envelope to its manifest on `artifact_sha256`, the silent skip of an
  envelope no manifest matches, and the artifact read from `repo_root / manifest["artifact"]` -
  `bench/metrics/__main__.py` (`build_results`, `_read_artifact_text`) and `bench/variance.py` -
  class A

## Open Questions / Decisions

| ID | Title | Resolution | Status | Updated |
|----|-------|------------|--------|---------|
| D1 | Corpus design: new artifacts or edit the existing four | Option D (walk-presented): fix the shared form, add 005, freeze the old four | Decided | 2026-10-27 |
| D2 | Lane and test for WCAG-1.3.5 (Identify Input Purpose) | Option A: scripted, closed purpose list as FORMS-AUTOCOMPLETE | Decided | 2026-10-27 |
| D3 | Lane and test for WCAG-2.5.8 (Target Size (Minimum)) | Option B: judged | Decided | 2026-10-27 |
| D4 | Lane and test for WCAG-1.3.4 (Orientation) | Option B: judged | Decided | 2026-10-27 |
| D5 | Lane and test for WCAG-2.4.7 (Focus Visible) | Option A: judged | Decided | 2026-10-27 |
| D6 | Lane and test for WCAG-4.1.3 (Status Messages) | Option A: judged | Decided | 2026-10-27 |
| D7 | How the critique-forms overlap gets recorded | Option A: overlap sentence on both new rows | Decided | 2026-10-27 |
| D8 | Whether more than the five ruled criteria are added now | Option A: exactly the five | Decided | 2026-10-27 |
| D9 | How the shared paid dispatch is sequenced given no replay is possible for the five | Option B: free local checks.py run before the dispatch | Decided | 2026-10-27 |

### D1: Corpus design: new artifacts or edit the existing four (Decided)

**Summary.** Decide whether the five new criteria get planted into new corpus artifacts or into
edited versions of `accessibility-001` through `004`.

**Context.** The 2026-09-25 ruling flagged this as open, not as its own decision: editing the
existing four changes their `artifact_sha256`, which the cal1 recalibration avoided because that
pass changed only the skill, never the corpus [S1]. `bench/README.md`'s invariant allows at most one
planted defect per criterion per section, and the existing recipes already carry multiple plants
across several sections (accessibility-001 holds 7) [S9, S10], so a new artifact built the same way
could hold all five new plants without crowding. Under E73's ruled sequencing, the baseline is
re-run for all seven skills in one shared dispatch regardless of this choice, so the "forces a
re-run" framing in the original backlog entry is weaker than it was when written: the real cost this
decision controls is how many artifacts that already-planned re-run covers, sized in "Measurement and
sequencing" above.

**Desired outcome.** The five new criteria get at least one planted instance each, the existing
22-criterion comparison (0.1.0 to 0.1.1, recorded in `results.json`) stays reproducible against the
corpus bytes it was measured on, and the added measurement cost is stated in envelopes, not left
implicit.

**Options / approaches.**

* **Option A:** Add one new artifact (`accessibility-005`) carrying all five new plants across its
  sections, and leave `accessibility-001` through `004` byte-identical to today. Cost: +20 envelopes
  (560 total for the shared dispatch).
* **Option B:** Add two new artifacts, splitting the five plants so no single artifact's section
  count grows past what existing recipes use, and so one of the two can also serve as a second clean
  check against false positives on the new scripted criteria. Cost: +40 envelopes (580 total).
* **Option C:** Edit `accessibility-001` through `004` to add the five plants among them, adding no
  new file. Their hashes change, and the frozen `results.json` rows for 0.1.0 and 0.1.1 stop being
  reproducible from the current corpus, though they remain valid as a historical record of what was
  measured when. Cost: +0 envelopes beyond what E73 already plans (540 total).
* **Option D (added in the 2026-10-27 walk, after a pre-walk check):** Fix the shared form builder
  so the email and phone fields carry `autocomplete` tokens, add `accessibility-005` with the five
  plants, and keep a frozen copy of today's four artifacts and manifests that the committed run sets
  still score against. The check found two WCAG-1.3.5 failures in each existing artifact, which
  Options A and B would leave as permanent false positives. Cost: 560 envelopes, plus the frozen copy.

**Recommendation.** Option A, medium confidence. It adds the least new measurement cost of the two
corpus-growing options while keeping the existing 22-criterion comparison reproducible against
today's artifact bytes, which Option C gives up for no stated gain now that the shared-dispatch
sequencing already absorbs the baseline re-run either way. Option B's second clean artifact is a real
benefit (catching false positives on the new scripted checks for free) but is not required to meet
the ruling's floor, and `accessibility-004` already exercises the existing 22 checks against a clean
artifact; whether the new scripted checks also need their own dedicated clean artifact is worth the
maintainer's direct judgment rather than a default.

---

> **Maintainer decision:** Decided 2026-10-27 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option D, presented in the walk and absent from this draft's options list: fix the shared form builder so the email and phone fields carry `autocomplete` tokens, add `accessibility-005` with the five plants, and keep a frozen copy of today's `accessibility-001` to `004` artifacts and manifests that the committed run sets still score against
> * **Reasoning:** The maintainer answered "d1 D". A pre-walk check found that all four existing artifacts carry `<input id="email" type="email">` and `<input id="phone" type="tel">` with no `autocomplete`, from one builder (`bench/generator/domains/accessibility.py` lines 389 and 396), so a scripted WCAG-1.3.5 check would flag both on every artifact, including the clean `004`, and `bench/README.md` counts an unplanted correct finding against precision. Option A's byte-identical premise therefore fails, and Option C's hash change would make the committed accessibility envelopes unscorable (`bench/variance.py` skips an envelope whose hash matches no manifest), so D fixes the corpus and keeps the old bytes for the old evidence.
> * **Follow-up:** Size the frozen-copy work before the build: scoring and `bench.variance --committed` must read the frozen copy for every committed run set holding accessibility envelopes (p3-2026-07-31, cal1-2026-08-01 and bench-2026-10-15), and `bench/tests/test_variance.py`'s end-to-end test (which scores `runs-cal1`) must keep passing. Reword AC-5 and the Measurement table for Option D (560 envelopes) when this spec moves to `docs/internal/release-plans/_unassigned/E67_accessibility-expansion/spec.md`.
> * **Decided by / date:** jprisant / 2026-10-27

### D2: Lane and test for WCAG-1.3.5 (Identify Input Purpose) (Decided)

**Summary.** Decide whether WCAG-1.3.5 is scripted or judged, and what its operational test checks.

**Context.** The W3C Understanding page states the test directly: a field whose purpose is in WCAG's
Input Purposes list (name, email, phone, address, and similar) must carry an `autocomplete` token
from a closed, well-defined vocabulary; `type` alone does not satisfy it, and browser autofill
heuristics do not either (verified, fetched 2026-10-26) [S22]. `critique-forms`'s own
`FORMS-AUTOCOMPLETE` already tests the same attribute, scripted, with the stated rationale "purpose
comes from the cue vocabulary, and validity is a lookup against a closed vocabulary under a fixed
token grammar" [S12]. The open part is scope: the Understanding page excludes fields that do not
collect information "about the user" (its own example: a transaction amount), and deciding that for
an arbitrary field is a judgment call the forms criterion sidesteps by naming a fixed, closed list of
purposes it checks (name, email, phone, username, password, address, city, region, country, birth
date) rather than trying to infer purpose generally [S12, S22].

**Desired outcome.** The test is deterministic wherever the `autocomplete` value or its absence is
the thing being judged, and it does not try to infer an unmarked field's purpose from its label text,
which would be a judgment call.

**Options / approaches.**

* **Option A:** Scripted, with the same closed-vocabulary, fixed-field-purpose approach
  `FORMS-AUTOCOMPLETE` already uses: check only fields the script can name a purpose for (by `type`,
  `name`, or `id` pattern matching a closed list drawn from WCAG's Input Purposes), flag a missing or
  invalid `autocomplete` token, and stay silent on any field outside that closed list rather than
  guessing.
* **Option B:** Judged, on the premise that deciding whether any given field "collects information
  about the user" is itself a comprehension call the general case needs, even though the specific
  test (token presence and validity) is mechanical once a field is in scope.
* **Option C:** Scripted, but broader than Option A: infer purpose from label text and placeholder
  wording as well as `type`/`name`/`id`, to catch more fields. This re-introduces the comprehension
  call Option A avoids and risks the same false-positive pattern WCAG-2.4.6 and WCAG-3.1.2 were moved
  to judged for in the draft pass [S4].

**Recommendation.** Option A, high confidence. `critique-forms` already runs this exact pattern in
this repository as a scripted check against the same attribute, and the scoping problem the
Understanding page raises is solved the same way forms solved it: by naming a closed list of
field purposes rather than inferring purpose generally. Reusing that precedent costs nothing new to
validate.

---

> **Maintainer decision:** Decided 2026-10-27 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A
> * **Reasoning:** The maintainer answered "d2 a". It reuses the scripted, closed-list pattern `FORMS-AUTOCOMPLETE` already runs; it is sound only because D1's Option D fixes the shared form, since a judged lane would flag the same two real failures on some runs instead of all.
> * **Follow-up:** Build a `checks.py` function, an `IMPLEMENTED_CRITERIA` entry, a test case and a `severity-anchors.md` threshold bullet (AC-4, AC-6). WCAG-1.3.5 is the only scripted criterion among the five, so it is the one D9's local check covers.
> * **Decided by / date:** jprisant / 2026-10-27

### D3: Lane and test for WCAG-2.5.8 (Target Size (Minimum)) (Decided)

**Summary.** Decide whether WCAG-2.5.8 is scripted or judged, and what its operational test checks.

**Context.** The criterion's floor is mechanical: a pointer target at least 24 by 24 CSS pixels,
unless one of five named exceptions applies (Spacing, Equivalent, Inline, User Agent Control,
Essential) (verified, fetched 2026-10-26) [S21, S22]. `checks.py` already resolves declared `width`,
`height`, and similar box properties for other checks (WCAG-1.4.10, WCAG-1.4.12), so computing a
declared target size against the 24px floor reuses existing machinery rather than building new
[S6]. The Understanding page states that the Equivalent and Essential exceptions cannot be decided
from CSS alone ("flag for manual review") [S22], which is the same declared-CSS-is-partial problem
`critique-forms`'s `FORMS-TOUCH-TARGET` already faces at its own, larger threshold, and that
criterion is judged in this repository today, with the stated rationale "Rendered size depends on
styling, inheritance and layout that the artifact may only partly declare." [S12].

**Desired outcome.** The 24px floor is tested without the scripted lane silently asserting an
exception does not apply when it has no way to know, and without duplicating `FORMS-TOUCH-TARGET`'s
own judgment call under a different name.

**Options / approaches.**

* **Option A:** Scripted. Reuse the declared-width/height resolution `checks.py` already has, flag
  any tappable control under 24px in either dimension with no CSS basis to apply an exception, and
  stay silent where the CSS gives no basis for an estimate, mirroring `FORMS-TOUCH-TARGET`'s own
  silence rule. The Spacing, Equivalent, User Agent Control, and Essential exceptions are not
  evaluated, which risks flagging a target that would in fact pass under one of them.
* **Option B:** Judged, for the same reason `FORMS-TOUCH-TARGET` is judged: declared CSS only
  partly determines rendered size, and at least two of the five exceptions explicitly need manual
  review per the primary source.
* **Option C:** Scripted, narrowed to skip any case where an exception plausibly applies (inline
  text links, elements inside a visually dense group) rather than evaluating the exceptions
  directly, accepting lower recall in exchange for fewer false positives than Option A.

**Recommendation.** Option B, medium confidence. The forms precedent is the closest comparison
available in this repository and it chose judged for the same underlying problem (declared CSS is a
partial signal for rendered size) at a different, larger threshold; the primary source's own
instruction to flag two of the five exceptions "for manual review" points the same way. Confidence
is medium rather than high because the base 24px-floor test by itself, ignoring every exception, is
more mechanical than `FORMS-TOUCH-TARGET`'s 44px test, and Option A's existing-machinery reuse is a
real, lower-effort path the maintainer may weigh differently.

---

> **Maintainer decision:** Decided 2026-10-27 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option B
> * **Reasoning:** The maintainer answered "d3 b". Two of the five exceptions cannot be decided from CSS, and `FORMS-TOUCH-TARGET` is judged in this repository for the same partial-CSS reason.
> * **Follow-up:** File WCAG-2.5.8 under `checks.judged` with a judged Lane rationale in `WCAG.md` (AC-1, AC-2), and plant one undersized target in `accessibility-005` (D1).
> * **Decided by / date:** jprisant / 2026-10-27

### D4: Lane and test for WCAG-1.3.4 (Orientation) (Decided)

**Summary.** Decide whether WCAG-1.3.4 is scripted or judged, and what its operational test checks.

**Context.** The criterion fails when content locks its view to one display orientation; the
Understanding page's sufficient and failure techniques point at CSS orientation media queries that
hide or disable content, or a rotation transform tied to one, and name an "essential" exception for
content that genuinely needs a fixed orientation, such as a check-deposit capture or a piano
keyboard app (verified, fetched 2026-10-26) [S22]. Deciding whether that exception applies is
explicitly a two-part judgment in the primary source: whether removing the restriction would change
the content's function, *and* whether the same function is achievable another way [S22]. `checks.py`
already reads `@media` block text as a coarse presence signal for two other criteria (WCAG-1.4.10,
WCAG-1.4.12), rather than resolving a second cascade [S5], which is a plausible pattern to extend
here, but it was built for "is there a responsive override," not for "does this orientation lock
have a legitimate exception."

**Desired outcome.** An orientation lock that is a genuine usability defect gets flagged, and a
legitimate essential-use case (which the primary source gives real examples of) does not get a false
positive from a lane that cannot ask whether the exception applies.

**Options / approaches.**

* **Option A:** Scripted. Flag any `@media (orientation: portrait)` or `(orientation: landscape)`
  block whose declarations hide content (`display: none`, `visibility: hidden`) or apply a rotation
  transform to a root-level element, using the existing coarse-presence-signal pattern. The essential
  exception is never evaluated, so every match is reported as a violation.
* **Option B:** Judged. The model reads the orientation-locking CSS the scripted lane's own output
  (from pass 2) surfaces, and judges whether the lock is a defect or falls under the essential
  exception, following the same "when in doubt, judged" rule that moved WCAG-2.4.6 and WCAG-3.1.2 in
  the draft pass [S4].
* **Option C:** Judged, with the scripted lane emitting the orientation-media-query pattern as
  context for pass 2 (not as a finding of its own), so the model's judgment call is informed by a
  mechanical signal rather than a fresh text read. This is architecturally close to Option B, since
  the protocol already has the model read `checks.py`'s output during its judged sweep [S3]; it adds
  no new mechanism.

**Recommendation.** Option B, high confidence. The essential exception is stated in the primary
source as a two-part comprehension judgment with named real-world cases on both sides, which is
exactly the category of call the skill's own "when in doubt, judged" rule reserves for the judged
lane, and it already has two precedents (WCAG-2.4.6, WCAG-3.1.2) inside this same registry.

---

> **Maintainer decision:** Decided 2026-10-27 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option B
> * **Reasoning:** The maintainer answered "d4 b". The essential exception is a two-part reading call in the W3C text, which the skill's when-in-doubt-judged rule reserves for the judged lane.
> * **Follow-up:** File WCAG-1.3.4 under `checks.judged` (AC-1, AC-2), and plant an orientation lock in `accessibility-005`, since no existing artifact has an orientation query (D1).
> * **Decided by / date:** jprisant / 2026-10-27

### D5: Lane and test for WCAG-2.4.7 (Focus Visible) (Decided)

**Summary.** Decide whether WCAG-2.4.7 is scripted or judged, and what its operational test checks.

**Context.** The dominant failure pattern is a `:focus` rule that removes the outline with no visible
replacement (verified, fetched 2026-10-26, technique F78) [S22]. `checks.py`'s own docstring states
that its CSS engine does not match any pseudo-class selector at all: "a pseudo-class... is not
matched against any element; the declaration it carries is simply never applied" (verified) [S5]. A
scripted test for this criterion therefore cannot reuse the file's existing cascade-resolution
machinery as-is; it would need a new, narrower text-level read of `:focus` and `:focus-visible` rule
bodies, in the same spirit as the existing coarse-presence-signal checks for `@media` blocks [S5].
The primary source itself states that "visible" is not defined numerically in the criterion (no
minimum contrast or size; that is a different, AAA-level criterion, 2.4.13), so a replacement style's
adequacy cannot be confirmed by a fixed rule even if the removal itself can be detected [S22].

**Desired outcome.** An outline removed with nothing replacing it gets flagged, without the scripted
lane claiming to verify that a replacement style is genuinely visible, which the standard itself
leaves undefined.

**Options / approaches.**

* **Option A:** Judged. Given that the CSS engine does not parse pseudo-classes today, and that
  "visible" has no fixed definition to test against, the model reads the stylesheet text during its
  judged sweep and judges whether a keyboard-focus indicator exists and is visible.
* **Option B:** Scripted, narrow. Extend the CSS engine with a bounded, text-level read of `:focus`
  and `:focus-visible` rule bodies only (not a general pseudo-class cascade), flag a rule that sets
  `outline: none` / `0` / `none` with no other visually-distinguishing declaration in the same rule,
  and accept false positives where a visible replacement is declared in a different rule the check
  does not cross-reference. This limitation would be documented in `references/WCAG.md`, the way
  `FORMS-TOUCH-TARGET`'s own declared-CSS limits are documented today.
* **Option C:** Scripted, broader. Build genuine `:focus`/`:focus-visible` cascade resolution into
  `checks.py`'s CSS engine, matching the same specificity and inheritance rules it already applies
  to other properties, so a replacement declared anywhere in the cascade is correctly credited. This
  is the most capable option and the largest engineering lift, extending a subsystem the module's own
  docstring describes as deliberately excluding pseudo-classes.

**Recommendation.** Option A, medium confidence. The combination of "the engine does not parse
pseudo-classes today" and "the standard leaves 'visible' undefined" makes a scripted test either
narrow enough to carry a documented, non-trivial false-positive rate (Option B) or expensive enough
to look like a different kind of change than this expansion's other four criteria (Option C).
Confidence is medium, not high, because Option B's narrow text-level read is a real middle path that
reuses the repository's own "coarse presence signal" precedent and may be cheaper to build and worth
the trade than this recommendation assumes; it is the one criterion among the five where the
engineering cost of each option, not just the judgment question, should weigh on the choice.

---

> **Maintainer decision:** Decided 2026-10-27 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A
> * **Reasoning:** The maintainer answered "d5 a". The `checks.py` CSS engine matches no pseudo-class selector, and WCAG gives no numeric definition of visible, so the model judges it from the stylesheet.
> * **Follow-up:** File WCAG-2.4.7 under `checks.judged` (AC-1, AC-2), and plant an `outline: none` rule on `:focus` in `accessibility-005`, since no existing artifact has a `:focus` rule (D1).
> * **Decided by / date:** jprisant / 2026-10-27

### D6: Lane and test for WCAG-4.1.3 (Status Messages) (Decided)

**Summary.** Decide whether WCAG-4.1.3 is scripted or judged, and what its operational test checks.

**Context.** The sufficient pattern is mechanical once a status region is identified: `role="status"`,
`role="alert"`, `role="log"`, or an `aria-live` attribute (verified, fetched 2026-10-26) [S22]. The
hard part is identifying a status region in the first place from static markup, since a live page's
dynamic update is exactly what a static artifact cannot show. The only static signal available short
of a live-region attribute is content or class-name wording that suggests a status area ("saved",
"items", "error", a toast-styled container), and the Understanding page's own fetched summary flags
that route as inference, calling it something to "treat as review prompts," not a confident mechanical
test [S22]. Misuse is also a named failure mode (`role="alert"` on non-error content, or on content
with no text) [S22], which is itself a content-reading judgment about what the message means.

**Desired outcome.** A status region that updates without any live-region exposure gets noticed, and
the lane that notices it does not claim a keyword match for "looks like a status message" is a fixed,
reliable pattern, which the primary source's own framing does not support.

**Options / approaches.**

* **Option A:** Judged. The model reads the artifact for anything that functions as, or is styled or
  labeled as, a feedback or status area, and judges both whether it needs live-region exposure and
  whether an exposure that is present (`role="alert"` on a success message, for instance) is a
  misuse. This matches the comprehension-call pattern WCAG-3.3.1 and WCAG-1.4.1 already use in this
  registry: reading markup for what it says, not matching a fixed pattern [S4].
* **Option B:** Scripted, keyword-based. Flag an element whose class name or id matches a closed list
  of status-suggestive tokens (`status`, `alert`, `toast`, `notification`, `error-summary`,
  `success-message`) and carries no `role` or `aria-live` attribute. This is the route the
  Understanding fetch itself called unreliable inference; it also risks false positives on static
  text that merely discusses errors or statuses without being a live-updating region.
* **Option C:** Scripted, misuse-only. Flag only the narrower, more mechanical half of the criterion:
  `role="alert"` or `aria-live="assertive"` present on an element with no text content, or
  `aria-live="off"` explicitly set on an element whose class name suggests a status region. This
  leaves the harder "is this a status region at all" question entirely to the judged lane for every
  other case, in effect running alongside Option A rather than instead of it, since a criterion sits
  in exactly one lane; the scripted half would need its own ID under permanence rule 4, which
  conflicts with Requirement 3's "one criterion, one ID."

**Recommendation.** Option A, high confidence. The primary source's own treatment of the
hard case (identifying a status region at all) explicitly reads as a judgment call rather than a
fixed pattern, which is the same signal that moved WCAG-2.4.6 and WCAG-3.1.2 to judged in the draft
pass. Option C's structural conflict with the one-ID rule (Requirement 3) rules it out as stated;
it would need redesigning as "judged, with scripted-lane output as one more input to the sweep,"
which is just Option A under a different description.

---

> **Maintainer decision:** Decided 2026-10-27 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A
> * **Reasoning:** The maintainer answered "d6 a". Identifying a status region in static markup is a reading call, and Option C's scripted misuse half would need a second ID for one criterion.
> * **Follow-up:** File WCAG-4.1.3 under `checks.judged` (AC-1, AC-2), plant one status region in `accessibility-005`, and check the dispatch results for clean-artifact findings on `004`'s "Refresh status" button and its inline error span, which have no live region.
> * **Decided by / date:** jprisant / 2026-10-27

### D7: How the critique-forms overlap gets recorded (Decided)

**Summary.** Decide how `references/WCAG.md` records the deliberate overlap between WCAG-1.3.5 and
`FORMS-AUTOCOMPLETE`, and between WCAG-2.5.8 and `FORMS-TOUCH-TARGET`.

**Context.** `FORMS.md` already states the forms-side half of both overlaps, naming the different
grading rationale each time: `FORMS-AUTOCOMPLETE` grades the attribute "by what happens to autofill"
rather than conformance, and `FORMS-TOUCH-TARGET` tests "the larger size mobile-usability guidance
recommends" against a 44px target, not WCAG's 24px conformance floor; both rows already say "once
E67 adds it" (verified) [S12]. `docs/internal/backlog/enhancements.md`'s E67 entry (its "Why" bullet)
separately notes one existing, unrecorded overlap in the library (WCAG-3.3.2 and NNG-H6-LABELED,
both testing label presence) and says plainly "these are recorded" about the two E67 will add [S1],
committing this spec to writing the other half down, not merely leaving `FORMS.md`'s half-statement
standing alone.

**Desired outcome.** A reader who finds a WCAG-1.3.5 or WCAG-2.5.8 finding, or a `FORMS-AUTOCOMPLETE`
or `FORMS-TOUCH-TARGET` finding, learns from either skill's own reference file that the other skill
tests the same underlying attribute on different terms, without having to discover the pairing by
reading both skills' source side by side.

**Options / approaches.**

* **Option A:** Add a matching "Overlap" sentence to each of the two new rows in `WCAG.md`, mirroring
  `FORMS.md`'s existing language and naming the different rationale (conformance floor versus
  usability recommendation; presence and validity versus effect on autofill), and update
  `criterion-ids.md`'s "one such overlap, unrecorded" sentence to say two more are now recorded.
* **Option B:** Leave the overlap recorded only on the forms side, where it already is, and treat
  `FORMS.md`'s existing sentence as sufficient since a reader of either skill's output can look up
  the other skill's registry.
* **Option C:** Record it on both sides, as in Option A, and also add a standing cross-skill overlap
  registry document cataloguing every deliberate overlap in the library (the existing WCAG-3.3.2 /
  NNG-H6-LABELED pair plus these two), rather than a footnote on each affected row.

**Recommendation.** Option A, high confidence. It is what `docs/internal/backlog/enhancements.md`'s
E67 entry already commits this spec to doing ("these are recorded"), and it matches the existing
one-sentence-per-row pattern `FORMS.md` already uses rather than introducing a new document for three
total pairs. Option C is a
reasonable future step if a fourth overlap appears, but building a registry file for three rows is
more structure than the current evidence asks for.

---

> **Maintainer decision:** Decided 2026-10-27 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A
> * **Reasoning:** The maintainer answered "d7 a". It matches the one-sentence-per-row pattern `FORMS.md` already uses and keeps the commitment the E67 backlog entry makes. The sentence Option A names is in `docs/internal/backlog/enhancements.md` (line 1547), not in `criterion-ids.md`.
> * **Follow-up:** Add the overlap sentence to the WCAG-1.3.5 and WCAG-2.5.8 rows in `WCAG.md`, and update `enhancements.md`'s "one such overlap, unrecorded" sentence (AC-7).
> * **Decided by / date:** jprisant / 2026-10-27

### D8: Whether more than the five ruled criteria are added now (Decided)

**Summary.** Decide whether this expansion stops at the five named criteria or also pulls in one or
more of the six criteria `WCAG.md` already marks "partly checkable, not implemented."

**Context.** The 2026-09-25 ruling's own wording is "adding at least" the five it names [S1], which
leaves room to go further without re-opening the ruling itself. `WCAG.md`'s unchecked table already
flags six criteria as partly checkable from static markup: 1.4.2 (Audio Control), 1.4.5 (Images of
Text), 2.1.1 (Keyboard), 2.2.2 (Pause, Stop, Hide), 3.3.3 (Error Suggestion), and 3.3.8 (Accessible
Authentication (Minimum)) [S4]. Each of those is only partly checkable, meaning a static check would
cover part of the criterion and leave the rest unaddressed, which is a different, weaker claim than
the five criteria this spec covers, each of which `WCAG.md` already marks fully "checkable, not
implemented" [S4]. The backlog's own size estimate for E67 ("five criteria, their injectors and
tests") and E73's dispatch-cost math (which assumes this corpus's shape) are both scoped to five, not
eleven [S1, S16].

**Desired outcome.** The expansion's size matches what was actually sized and estimated, and any
later decision to reach into the partly-checkable six happens as its own scoped choice rather than as
scope added mid-build to this one.

**Options / approaches.**

* **Option A:** Exactly the five ruled criteria, nothing more. The "at least" in the ruling is
  satisfied at five, and nothing in the evidence suggests the maintainer intended more at this pass.
* **Option B:** The five ruled criteria plus one or more of the six partly-checkable criteria, built
  now in the same version move, accepting that each of those six would need its own scope statement
  explaining which part of the criterion is checked and which is not (the same "partly" framing
  `WCAG.md` already gives them).
* **Option C:** The five ruled criteria now; name the six partly-checkable criteria as a specific,
  sized follow-on in `WCAG.md`'s scope table, so a future expansion has a concrete target already
  written down rather than a bare mention in a backlog row.

**Recommendation.** Option A, high confidence, with Option C's footnoting as a cheap addition worth
doing regardless of which option is chosen. The ruling, the backlog's size estimate, and E73's cost
math all point at five; going further now would mean sizing and measuring a different, larger change
than any of those three documents estimated.

---

> **Maintainer decision:** Decided 2026-10-27 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A
> * **Reasoning:** The maintainer answered "d8 a". The ruling, the backlog estimate and the dispatch counts are all sized for five criteria.
> * **Follow-up:** None needed for scope. The recommendation's optional addition, naming the six partly checkable criteria in `WCAG.md` as a sized follow-on, can ride the build if wanted.
> * **Decided by / date:** jprisant / 2026-10-27

### D9: How the shared paid dispatch is sequenced given no replay is possible for the five (Decided)

**Summary.** Decide what, if anything, runs before the shared E73-and-E67 paid dispatch, given that
E73's own free-replay technique cannot preview how a model performs on five criteria it has never
been asked to judge.

**Context.** E73's ruled D5 inserted a free replay before its own paid dispatch, computed from
committed envelopes with no model call, specifically to "size the change and catch surprises" before
spending money [S16]. That technique works because E73's change (the merge step) acts on envelopes
that already exist. The five criteria this spec adds have no committed envelopes to replay: no prior
run, on any tier, has ever judged WCAG-1.3.4, 1.3.5, 2.4.7, 2.5.8, or 4.1.3 against this corpus. A
replay can therefore still size E73's own fix on the other 22 criteria, exactly as E73's D5 planned,
but it gives zero visibility into whether a model can actually find the five new defects D1's chosen
corpus plants, before the one paid dispatch that is supposed to measure both changes at once runs.

**Desired outcome.** The maintainer's single approval for the paid dispatch is made with a realistic
sense of what it will and will not have validated in advance, and a genuine problem with one of the
five new criteria's detectability is caught before it is buried inside a seven-skill, two-tier result
set.

**Options / approaches.**

* **Option A:** Run E73's replay as already planned, covering the other 22 criteria, and go straight
  to the one shared paid dispatch for all seven skills with no separate look at the five new
  criteria first. If a new criterion's scripted check is broken or its judged framing confuses the
  model, that surfaces only after the dispatch runs.
* **Option B:** Before the shared dispatch, run `scripts/checks.py` locally against D1's new or
  edited corpus artifacts for every scripted criterion among the five (no model call), to confirm
  each one fires exactly where planted and nowhere else, the same deterministic check E73's own
  "defect, reproduced" section ran for its own fix [S16]. This catches a scripted-lane bug before
  payment, though it says nothing about the judged criteria.
* **Option C:** A small, separately-approved paid run against `critique-accessibility` alone, k=5 on
  one tier, before the full seven-skill shared dispatch, to check that the new criteria are at least
  detectable before committing to the larger, more expensive run.

**Recommendation.** Option B, high confidence, as a floor that costs nothing and should happen
regardless of what else is decided; Option C is a reasonable addition if the maintainer wants
model-level confidence before the full dispatch, at the cost of a second approval and a second
payment instead of one. Option A alone leaves every scripted check for the five new criteria
unverified until the one expensive run has already happened.

---

> **Maintainer decision:** Decided 2026-10-27 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option B
> * **Reasoning:** The maintainer answered "d9 b". It costs nothing, and the walk's own pre-check, a manual version of it, found the WCAG-1.3.5 collision before any spend.
> * **Follow-up:** Before the shared dispatch, run `checks.py` against the new and frozen corpus and confirm the WCAG-1.3.5 check fires only where planted; record the result in the AC-10 dispatch draft, which still needs the maintainer's own go.
> * **Decided by / date:** jprisant / 2026-10-27

## What I do not know

- Whether the pinned models can find the four judged criteria at all. No committed envelope has ever
  been judged against them, so the shared dispatch is their first measurement.
- Whether a judged sweep flags WCAG-2.5.8 on the shared page's nav links or icon control, on the
  clean `accessibility-004`. A later review found and fixed a third base defect of the same
  WCAG-4.1.3 shape, on the promo-code error span (see "Build notes"), so that question is settled;
  WCAG-2.5.8's nav-link and icon-control sizing is the one this build could not rule out from static
  markup.
- The dollar cost of the shared paid dispatch at 560 envelopes. Translating envelopes to a dollar
  figure needs per-token pricing that neither this spec nor E73's states.
