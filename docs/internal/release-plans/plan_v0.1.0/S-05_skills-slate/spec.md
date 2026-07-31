---
id: S-05
title: "Skills slate: 3 core + 3 stretch"
type: spec
status: draft
created: 2026-07-31
updated: 2026-07-31
linked-effort: S-05
linked-plan: ../implementation/IMPL-B-skills-to-rc.md
linked-strategy-brief: "01-strategy-brief.md (local planning archive, not committed)"
linked-release: ../plan_v0.1.0.md
source-count: 3
ac-count: 8
audience: agent
---

# Spec: Skills slate: 3 core + 3 stretch

## Task Summary

- Status: draft
- AC: [ ] AC-1 [ ] AC-2 [ ] AC-3 [ ] AC-4 [ ] AC-5 [ ] AC-6 [ ] AC-7 [ ] AC-8
- Open questions: 2
- Last-updated: 2026-07-31

## Purpose

Define the six skills of v0.1.0: their rubric sources, ID namespaces, lane expectations, artifact claims, and the gate that decides core versus stretch shipping [S5].

## Scope

Domain content per skill, instantiated through the S-04 template. Core skills are committed; stretch skills are built identically and gated on P3 results.

## Non-Goals

Any seventh domain. BYOR mode (v0.2). Cross-skill composition recipes (v0.3).

## Users / Actors

P2 pipeline teams (one per skill); P3 measurement agents; end users critiquing documents, pages, UI specs, docs, error messages, and arguments.

## Requirements

Slate definition [S1][S2][S5]. Every skill uses the S-04 template; table columns are the domain deltas:

| Skill | Status | Rubric sources (operationalization) | ID namespace(s) | Artifact claim (v0.1) | Expected lane balance |
|---|---|---|---|---|---|
| critique-clarity | core | US Federal Plain Language Guidelines (open-standard); Williams, Style: Lessons in Clarity and Grace (paraphrased) | `PLAIN-*`, `WILLIAMS-*` | Markdown/plain-text prose documents | Scripted-heavy (readability grade, passive ratio, sentence-length distribution, nominalization density) plus judged (audience fit, cohesion) |
| critique-accessibility | core | WCAG 2.2 AA (open-standard, upstream IDs) | `WCAG-<n.n.n>` | HTML pages and fragments; markdown where mappable | Scripted-heavy (contrast, alt text, heading structure, link text, lang attributes) plus judged (meaningful-sequence, purpose-of-controls subset) |
| critique-usability | core | Nielsen 10 heuristics (paraphrased); Nielsen severity ratings (paraphrased) | `NNG-H1..H10` | HTML/markdown UI specs and page mockups; NOT live applications (narrow claim per release plan R2) | Judged-heavy; scripted assists (label presence, control naming consistency, orphan states) |
| critique-docs | stretch | Diataxis (open-standard) | `DIATAXIS-*` | Technical documentation pages/trees in markdown | Mixed (mode-mixing signals, heading depth, orphan detection scripted; mode fit judged) |
| critique-microcopy | stretch | NN/g error-message guidelines (paraphrased) | `NNG-EM*` | Error messages, empty states, microcopy strings (list or annotated screens as text) | Mixed (constructive-tone lexical checks scripted; helpfulness judged) |
| critique-argument | stretch | Toulmin model (paraphrased) | `TOULMIN-*` | Argumentative prose: essays, proposals, position docs | Judged-heavy; scripted assists (claim-marker detection, hedging density) |

Each skill's references/ MUST enumerate every criterion with: permanent ID, paraphrased operationalization, the operational test a finding must satisfy, severity anchor examples at levels 2 and 3 minimum, and lane assignment with rationale [S1].

Each skill MUST contribute its bench domain module (S-04 requirement) seeding at minimum: all scripted-lane criteria and >=3 judged-lane criteria, across >=3 artifacts of which >=1 is clean [S3-spec].

Core skills ship regardless of first-pass numbers but their numbers publish as measured; iterate within P3 only if a core skill fails to beat baseline (that is a release blocker for core) [S5]. Stretch skills ship only if they beat baseline AND meet the R1 consistency floor; otherwise they are excluded from `library.json` components, retained in-tree under a documented `status: incubating`, with numbers published in `bench/results/` and the hold recorded [S5]. [model-inference: incubating in-tree retention rather than deletion]

## Acceptance Criteria

- AC-1: Six skill directories exist, each passing the S-04 self-test runner. [S5]
- AC-2: Criterion registries: clarity >=12 criteria, accessibility >=15 (the machine-checkable AA subset plus judged subset), usability exactly the 10 heuristics with sub-criteria as needed, docs >=8, microcopy >=8, argument >=6 (claim, grounds, warrant, backing, qualifier, rebuttal). [S1][model-inference on counts]
- AC-3: Every criterion ID resolves to exactly one operationalization; no ID appears in two skills except upstream WCAG IDs, which appear only in critique-accessibility. [S1]
- AC-4: Each skill's scripted lane runs deterministically on the full corpus (two runs, identical output). [S1]
- AC-5: P3 produces per-skill envelopes covering the full corpus for its domain: recall, precision, k=5 consistency, baseline comparison on the two pinned tiers. [S1]
- AC-6: All three core skills beat the frozen baseline prompt on seeded recall at equal-or-better precision on at least one pinned tier, or the release halts with a handover diagnosis. [S1][S5]
- AC-7: Each stretch skill has a recorded ship/hold verdict citing its numbers against the R1 floor. [S5]
- AC-8: critique-usability's SKILL.md and README entry state the narrow artifact claim explicitly. [S5]

## Behavior / Examples

Given "can you give me feedback on this error message?" the trigger evals require critique-microcopy to fire and critique-argument to stay silent; given "review my PRD's argument", critique-argument fires. Cross-skill trigger confusion cases MUST appear in each skill's eval set (>=3 cross-domain negatives). [model-inference]

## Non-Functional Requirements

Paraphrase policy D6 enforced by the S-04 self-test. Book-sourced rubrics (Williams, Toulmin, Nielsen) cite ISBN and page/chapter ranges in `rubric_sources` [S1].

## Revisions

None (draft).

## Sources & Evidence

- S1: methodology draft (gate table, provenance, criterion rules). Class A.
- S2: strategy doc sec 3.3 (source map, scriptable-share estimates). Class A.
- S5: decisions log D3, D6; release plan R1, R2. Class A.

## Open Questions

- OQ-1: Whether WILLIAMS-* criteria fold into PLAIN-* to keep clarity's registry single-sourced. Pipeline decides with ADR; default is two namespaces, one skill.
- OQ-2: Microcopy artifact format (bare string list vs annotated context). Pipeline decides during P2; the corpus module must match the choice.
