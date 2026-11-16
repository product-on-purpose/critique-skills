---
id: E83
title: "Best-in-class worked examples for every skill"
type: plan
status: ruled
created: 2026-11-15
updated: 2026-11-15
linked-effort: docs/internal/backlog/enhancements.md
linked-release: null
requires-human-review: true
---

# Plan: best-in-class worked examples for every skill (E83)

It proposes what each skill's worked example should become, in what order, and at what cost. The
maintainer ruled its eight decisions on 2026-11-15 and accepted every recommendation; the rulings
are recorded at the top of the decisions section. No paid run in it starts without a separate go.

## The goal

A worked example exists so a reader can decide whether to trust a skill before pointing it at their
own work. The best example answers that question with evidence the reader can check, on an artifact
that looks like their own, and is honest about every part it did not run.

## Where the examples stand today

Every skill has one folder under `examples/<domain>/`, holding an artifact, an envelope, a
disposition log, and a README walkthrough. The inventory below was taken on 2026-11-15 from the
files themselves.

| Skill | Artifact | Findings (scripted / judged) | Highest severity |
|---|---|---|---|
| `critique-accessibility` | 31-line HTML dashboard | 6 / 0 | 3 |
| `critique-argument` | 25-line memo | 2 / 1 | 3 |
| `critique-clarity` | 9-line task list | 3 / 1 | 3 |
| `critique-docs` | 20-line how-to page | 1 / 1 | 3 |
| `critique-forms` | 78-line signup form | 8 / 1 | 3 |
| `critique-microcopy` | 32-line set of error strings | 8 / 2 | 3 |
| `critique-usability` | 24-line settings spec | 1 / 2 | 3 |

What that table hides:

- **No judged finding comes from a live run.** Every artifact is a copy of a golden test fixture,
  and every envelope is that fixture's `expected_envelope`, with `run.model` set to `illustrative`.
  Only the scripted lane can be reproduced, by running its printed command. The judged lane, which
  is where a reader most needs evidence, is curated.
- **The artifacts are small and synthetic.** They run from 9 to 78 lines, and each was written to
  seed specific defects. None is a document anyone would actually ship.
- **The range is narrow.** No example shows a severity-4 finding, and no example shows a clean
  result, although six skills have a clean golden fixture.
- **The dispositions are authored, and nothing says by whom.** Each README calls them one
  reviewer's plausible call, but the log itself has no field naming who decided.
- **Some text has gone stale.** Three READMEs (argument, docs, usability) print scripted output
  stamped `skill_version` 0.1.0 against envelopes stamped 0.1.1. The usability envelope points
  `run.artifact` at its example copy, while the other six point at the golden fixture.
  (`examples/recipes/README.md`'s "five folders" was fixed in PR 139.)
- **Only one example links to measured evidence.** `critique-forms` cites the bench runs that
  converged on its judged finding; the other six do not.

## What the first live run taught

E54's recipe, `examples/recipes/cross-library-composition.md` (PR 139), committed the first live,
dated envelope in the examples tree: one `critique-clarity` run on a 91-line `pm-skills` PRD on
2026-11-15. Its method is the one this plan generalizes. Its result is a warning about what a
flagship run on a realistic document will show.

- **Realistic structure exposed a parser defect.** 8 of the 29 findings shown read markdown tables
  as prose, six of them at severity 3. The goldens and the bench corpus hold no tables, so nothing
  had tested this. This is E82 (tables read as prose).
- **The judged lane was invisible.** The run found 68 scripted and 5 judged findings. The output
  bound keeps five findings below severity 3, scripted findings filled every slot, and no judged
  finding appears in the envelope. This is the reverse case of E80 (should the output bound rank by
  lane).

So a flagship run today, on a realistic and longer artifact, would likely repeat both effects: a
wall of scripted findings, some of them false, and none of the judged findings that make a skill
worth more than a linter. The plan below adds a free pre-screen step and makes the paid step wait
on E82 and E80.

## What "best in class" means here

Each criterion below is checkable. An example meets the bar when it meets all eight.

1. **Live.** The envelope is the output of one real skill run, not a curated copy, and it says so.
   It shows at least one judged finding, or says why none survived the output bound.
2. **Dated and pinned.** It records the date, the Claude Code CLI version, and the model it ran
   under, as the E54 envelope's provenance file does.
3. **Realistic artifact.** The artifact is the kind of document the skill's Artifact claim names,
   at a realistic length, and its source is stated.
4. **Both lanes shown.** The walkthrough shows at least one scripted and one judged finding, and
   says which command reproduces which.
5. **Honest about variance.** It says that a re-run's judged findings will differ in wording and
   may differ in which fire, and it links the skill's measured consistency figure.
6. **Linked to measurement.** It links the skill's benchmark result for the tier it ran on.
7. **Dispositions with a named actor.** Each disposition says who made it, or is labeled as
   illustration in the log itself, not only in the README.
8. **Guarded against drift.** A test fails when the envelope no longer validates against the
   current contract, or when the artifact's bytes no longer match `artifact_sha256`.

## The proposed shape: keep the walkthrough, add a flagship

Each skill would carry two examples, because they answer different questions.

- **The walkthrough (kept, corrected).** The current folder stays. It is the right teaching tool:
  small, every finding explained, and its scripted half reproducible bit for bit. Phase 1 fixes its
  stale text and adds the missing labels, and nothing else changes.
- **The flagship (new).** One live run on a realistic artifact, at
  `examples/<domain>/flagship/`. It is the trust tool: what the skill actually says about a real
  document, unedited, with its provenance.

A clean-result example and a severity-4 example would follow the same flagship rules where a skill
can produce them honestly (decision D5 below).

## Phases

| Phase | What it does | Model calls | Depends on |
|---|---|---|---|
| 1. Correct what exists | Fix the stale `skill_version` outputs and the usability `run.artifact` path; label every disposition log as illustration inside the log | 0 | Nothing |
| 2. Guard what exists | A test that validates every `examples/**/envelope.json` against the contract and checks each `artifact_sha256`, extending the existing example-hash test | 0 | Phase 1 |
| 3. Choose the flagship artifacts | One realistic artifact per skill, with its source and licence recorded (D2) | 0 | D2 |
| 3b. Pre-screen them, free | Run each skill's scripted lane on its candidate artifact and read every finding for parser misfires such as E82's tables. The purpose is to find defects before paying, not to pick flattering inputs: a misfire becomes a backlog item, not a reason to swap the artifact | 0 | Phase 3 |
| 4. Run the flagships | One live run per skill, one attempt each, with E54's runner and provenance file | 7 on one tier, 14 on both (D6) | D1, D6, E82 and E80 resolved or ruled, and a separate paid go |
| 5. Write the flagship walkthroughs | Per skill: the artifact, the envelope unedited, the findings explained, a named-actor disposition log, links to the skill's bench result | 0 | Phase 4 |
| 6. Surface them | Link each flagship from the skill's README and its docs-site page; the site already routes every `.md` under `examples/` | 0 | Phase 5 |

Phases 1 and 2 are free and could ship as one small PR before any decision is made. **Done
2026-11-15.** Phase 1 found a fourth defect the inventory missed: every artifact copy checked out
with CRLF on Windows, so no README's hash claim held there. Phase 2's guard is
`scripts/tests/test_worked_examples.py`. Phases 3 and 3b ran on 2026-11-16, free, for six skills;
see [the pre-screen record](phase-3-prescreen.md). It filed E84 to E86 and widened E82's evidence.

## Decisions for the maintainer

**Ruled by the maintainer on 2026-11-15, every recommendation accepted:**

| Decision | Ruling |
|---|---|
| D1 (live or curated findings) | A: live, one attempt, committed unedited |
| D2 (where the artifacts come from) | Sibling-library outputs where a sibling produces the artifact type, licensed public documents for the rest |
| D3 (flagships beside or instead of walkthroughs) | A: beside them |
| D4 (who dispositions the findings) | A: the maintainer, for real, named in the log |
| D5 (clean and severity-4 flagships) | B: one flagship per skill first, the others as a follow-up |
| D6 (one tier or both) | A: Sonnet only, 7 runs |
| D7 (flagships and specimens) | A: kept separate |
| D8 (wait for E82 and E80) | A: the paid runs wait until both are resolved or ruled |

Phases 1 and 2 were done the same day. Phase 4, the paid runs, still needs a separate go after E82 (tables
read as prose) and E80 (output-bound ranking). The options as drafted follow.

**D1. Should flagship judged findings come from a live run, or stay curated?** Option A: live, one
attempt, committed unedited, whatever it says. Option B: curated from goldens, as today. Option C:
live, but the best of several attempts. Recommendation: A, high confidence. B leaves the trust
question unanswered, and C selects the evidence, which is the defect the honesty labels exist to
prevent.

**D2. Where do the flagship artifacts come from?** Option A: sibling-library outputs, as E54 did
(PRDs from `pm-skills`, argument-adjacent output from `thinking-framework-skills`). Option B:
public real-world documents under a licence that allows copying. Option C: newly authored realistic
documents with no seeded defects. Recommendation: A where a sibling produces the artifact type, and
B for the rest, medium confidence. Not every skill has a sibling source: forms, accessibility and
microcopy need HTML or UI text that no sibling produces today.

**D3. Do flagships replace the walkthroughs or sit beside them?** Option A: beside them. Option B:
replace them. Recommendation: A, high confidence. The walkthrough's reproducible scripted half and
its explained findings are a teaching asset a single live run does not replace.

**D4. Who dispositions the flagship findings?** Option A: the maintainer, for real, with the log
naming them. Option B: authored illustration, labeled inside the log. Recommendation: A, medium
confidence, because a real decision on a real run is the one part of the loop no example shows yet.
It costs the maintainer one reading session per skill.

**D8. Do the flagship runs wait for E82 and E80?** Option A: yes, both resolved or ruled first.
Option B: run now and let the flagships document the defects, as E54 does. Recommendation: A,
medium confidence. One example that shows a defect is honest evidence; seven that each show a wall
of scripted findings and no judged ones would make the examples page an argument against the
library, and the money would buy little that E54 has not already shown.

**D5. Should there be clean-result and severity-4 flagships?** Option A: yes, where the skill's
golden set shows it can produce one. Option B: no, one flagship per skill only. Recommendation: B
first, then A as a follow-up, medium confidence. A clean live run is cheap and useful, but a live
severity-4 needs an artifact with a severe defect, which reintroduces seeding.

**D6. One tier or both?** Option A: Sonnet only, 7 runs. Option B: Sonnet and Haiku, 14 runs.
Recommendation: A, medium confidence. The examples answer "what does the skill say", and the bench
already answers "how does it vary by tier". Haiku's acceptance bands are 2.3 times wider, so a single
Haiku run is the weaker illustration.

**D7. How do flagships relate to the interactive specimens?** The specimen format was ruled on
2026-11-04 (Option A), with text specimens for docs, clarity and argument next, and the
payment-details prototype is unpublished. Option A: keep them separate: a specimen teaches the
rubric, a flagship evidences the skill. Option B: make each flagship the input to a specimen.
Recommendation: A, medium confidence. Coupling them would block the flagships on specimen work
that has its own open phases.

## Cost

Phase 4 is the only paid step. Counted in runs, as N4's D9 counted: 7 single-attempt skill runs on
Sonnet, or 14 with Haiku. E54's one Sonnet run on a 91-line PRD took about seven minutes and is the
per-run reference; longer artifacts cost proportionally more. No phase calls a model outside Phase 4.

## What I do not know

- Whether public real-world documents exist under a licence that permits copying them into an
  Apache-2.0 repository for every artifact type, especially accessible-markup and form HTML.
- How a live judged run behaves on artifacts several times longer than the goldens. The bench corpus
  tops out near the golden sizes, so the skills' measured figures may not transfer.
- Whether the maintainer wants examples to show a skill's weaknesses as well as its strengths. A
  live, unedited run will sometimes show a false positive, which is honest and may be unwelcome on a
  front page.
