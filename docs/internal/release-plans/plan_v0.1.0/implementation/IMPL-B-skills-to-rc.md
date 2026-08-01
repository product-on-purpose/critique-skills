---
id: IMPL-B
title: "Skills to RC: template, slate, critic, measurement, docs, release prep"
type: implementation-plan
status: executed
created: 2026-07-31
updated: 2026-08-01
linked-spec: covers ../S-04_skill-template/spec.md, ../S-05_skills-slate/spec.md, ../S-06_critic-subagent/spec.md, ../S-08_docs-and-packaging/spec.md
linked-release: ../plan_v0.1.0.md
phase-count: 5
ac-coverage: complete
audience: agent
---

# Implementation Plan B: Skills to RC (workflow phases P2-P5)

## Task Summary

- Status: executed
- Phases: [x] B1 [x] B2 [x] B3 [x] B4 [x] B5
- Phase evidence:
  - B1: docs/internal/execution/P2-report.md (phase summary, commit `1095663`, "P2 template") for the
    guide and toy skill's construction; the per-criterion S-04 AC-1..AC-7 verdicts P2-report.md itself
    never recorded (flagged by docs/internal/execution/P5-report.md) were verified fresh in this
    hygiene pass and are now recorded in `../S-04_skill-template/spec.md`'s own Task Summary (6 of 7
    ACs PASS; AC-3 FAIL, named there).
  - B2: docs/internal/execution/P2-report.md (S05-AC1..AC4, AC8, S06-AC1/AC4/AC5 all PASS).
  - B3: docs/internal/execution/P3-report.md (S05-AC5..AC7, S06-AC2 (PASS narrowly, provenance gap
    noted), S06-AC3 all PASS); docs/internal/execution/P3-cal1-report.md and P3-provenance.md for the
    later accessibility calibration and provenance record.
  - B4: docs/internal/execution/P4-report.md (S08-AC1..AC5, each with its own named section).
  - B5: docs/internal/execution/P5-report.md, with two open items that report itself names and this
    pass did not close (out of this pass's scope): S07-AC6 (CI runtime never measured) and S08-AC7
    (`rc-handover.md` does not exist).
- Last-updated: 2026-08-01

## Completion Status

| Phase | Goal | Fulfills AC | Owner (subagent, model) | Status |
|-------|------|-------------|------------------------|--------|
| B1 | Template + toy skill proven | S-04 AC-1..AC-7 | template-author (sonnet), toy-builder (sonnet), reviewer (opus) | Executed - docs/internal/execution/P2-report.md; per-criterion S-04 verdicts recorded in this pass, see spec |
| B2 | Six skills built in parallel | S-05 AC-1..AC-4, AC-8; S-06 AC-1, AC-4, AC-5 | 6 pipelines: rubric-researcher (sonnet), operationalizer (opus for judged-heavy domains, sonnet otherwise), checks-impl (sonnet), evals-author (sonnet), corpus-contributor (sonnet), skill-adversary (opus) | Executed - docs/internal/execution/P2-report.md |
| B3 | Measurement and gating | S-05 AC-5..AC-7; S-06 AC-2, AC-3 | run-orchestrator (sonnet), k5-runners (haiku/sonnet per pinned tier), metrics-verifier (haiku), calibration-judge (opus) | Executed - docs/internal/execution/P3-report.md, P3-cal1-report.md |
| B4 | Docs and generated views | S-08 AC-1..AC-5 | docs-author (sonnet), cold-reader (haiku), quickstart-executor (haiku), sweep-verifier (haiku) | Executed - docs/internal/execution/P4-report.md |
| B5 | Release prep and RC handover | S-08 AC-6, AC-7; S-07 AC-6; release-plan checklist and gates | release-packager (sonnet), completeness-critic (opus), external validators (plugin-dev:plugin-validator, plugin-dev:skill-reviewer) | Executed, two open items - docs/internal/execution/P5-report.md; S07-AC6 unmeasured, S08-AC7 `rc-handover.md` missing |

## Phase B1: Template + toy skill

**Goal.** S-04 complete; the pattern proven end to end before six teams copy it.

**Steps.** Author the template guide and self-test runner; build the toy skill from S-03's toy domain by following the guide literally; opus review of the guide against methodology and Standard; fix, re-run.

**Verification.** Toy skill passes self-test; each S-04 AC-2 failure mode demonstrably fails; U5 description score >= 0.7 on the toy.

**Decision gate.** Template ambiguities found by the toy build are fixed in the template, never worked around in the toy.

**Output artifacts.** Commit `P2 template`; template guide; toy skill (kept as fixture, not registered in `library.json`).

## Phase B2: Six-skill fan-out

**Goal.** Six structurally identical skills, self-test green, corpus modules contributed.

**Steps (per pipeline, x6, parallel, no cross-pipeline barrier).**
1. rubric-researcher: enumerate criteria from the S-05 sources; draft ID registry with citations.
2. operationalizer: paraphrased operationalizations, operational tests, severity anchors (levels 2-3 minimum), lane assignment with rationale; resolve pipeline-local OQs (S-05 OQ-1/OQ-2) with ADRs.
3. checks-impl: `scripts/checks.py` on the shared library, pytest suite, determinism double-run.
4. evals-author: >=20 trigger cases including >=3 cross-domain negatives; golden x3 and anti x1 examples with expected envelopes.
5. corpus-contributor: domain generator module (scripted criteria + >=3 judged, >=3 artifacts incl. 1 clean).
6. skill-adversary: attack operationalizations (vague criteria, untestable anchors, lane misassignments, paraphrase violations); pipeline fixes before exit.
Also in this phase: critic subagent authored (S-06 AC-1, AC-4) and delegation stanzas added to all SKILL.md files (AC-5).

**Verification.** Per pipeline: self-test green, determinism verified, adversary report closed. Slate-wide: S-05 AC-3 ID-uniqueness sweep.

**Decision gate.** A pipeline stuck after one tier-up retry halts its skill only: core-skill halt = run halt; stretch halt = documented hold, run continues.

**Output artifacts.** Commits `P2 <skill>` x6, `P2 critic-agent`; six adversary reports.

## Phase B3: Measurement and gating

**Goal.** Every number the release publishes, produced honestly.

**Steps.**
1. run-orchestrator regenerates the corpus from seeds, verifies integrity, freezes a measurement manifest (skill versions, model IDs, corpus hash).
2. k5-runners execute per skill x artifact x tier: scripted lane once (deterministic), judged lane k=5 through `critique-critic` (fulfills S-06 AC-2/AC-3 verification in passing); baseline prompt runs on identical inputs.
3. metrics-verifier computes recall, precision, consistency; cross-checks a 10 percent sample by hand-recomputation.
4. calibration-judge: sets the R1 floor (min core consistency), drafts stretch ship/hold verdicts, drafts the results narrative flagging every unflattering number.

**Verification.** S-05 AC-5 envelope completeness; AC-6 baseline wins for core (else halt with diagnosis); AC-7 verdicts recorded; results.json validates; tables regenerate diff-free.

**Decision gate.** Core skill failing baseline: one calibration iteration (prompt/anchor fixes, no criterion deletions), re-measure once; second failure halts the run.

**Output artifacts.** Commit `P3 results`; `bench/results/` envelopes; R1 ADR; verdict records.

## Phase B4: Docs and generated views

**Goal.** S-08's view layer, verified by cold readers.

**Steps.** docs-author builds README (results table first), QUICKSTART, how-tos, reference pages, frontmatter everywhere; generators wired; cold-reader answers the S-08 AC-1 questionnaire from README alone; quickstart-executor follows QUICKSTART literally in a fresh environment; sweep-verifier runs the em-dash and claim-traceability sweeps.

**Verification.** S-08 AC-1..AC-5 green; failed cold-read answers loop back to docs-author once, then escalate to opus rewrite.

**Decision gate.** None beyond the retry rule.

**Output artifacts.** Commit `P4 docs`.

## Phase B5: Release prep and handover

**Goal.** RC per the release plan's definition; run ends.

**Steps.** Version stamp 0.1.0 everywhere; CHANGELOG promotion; RELEASE-NOTES curation; full deterministic suite + gate + tier report; CI runtime measurement (S-07 AC-6); marketplace listing PR text; external validators (plugin-validator, skill-reviewer) run as independent checks; completeness-critic audits against every spec AC and release-plan gate; author `rc-handover.md`; final commit; stop.

**Verification.** Release-plan gates (b), (f), deterministic (i) green by command; checklist all checked except the two human rows; handover complete per RC definition item 5.

**Decision gate.** Completeness-critic findings either fixed or listed in the handover as open items; the run never ships around a red gate silently.

**Output artifacts.** Commit `P5 rc`; `rc-handover.md`; `marketplace-listing-pr.md`.
