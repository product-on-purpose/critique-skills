---
id: S-04
title: Skill template pattern
type: spec
status: committed
created: 2026-07-31
updated: 2026-08-01
linked-effort: S-04
linked-plan: ../implementation/IMPL-B-skills-to-rc.md
linked-strategy-brief: "01-strategy-brief.md (local planning archive, not committed)"
linked-release: ../plan_v0.1.0.md
source-count: 4
ac-count: 7
audience: agent
---

# Spec: Skill template pattern

## Task Summary

- Status: committed
- AC: [ ] AC-1 [ ] AC-2 [ ] AC-3 [ ] AC-4 [ ] AC-5 [x] AC-6 [ ] AC-7
- AC evidence:
  - AC-1: the template guide (`docs/internal/skill-template.md`) and self-test runner shipped in P2
    (docs/internal/execution/P2-report.md phase summary, commit `1095663`), but no report records a
    per-criterion verdict for AC-1 itself. Not evidenced; left unchecked.
  - AC-2: docs/internal/execution/P2-report.md's S05-AC1 row confirms the self-test runner passes
    on all six built skills, but AC-2's own text (the runner failing correctly on each of five
    named bad-input modes) was never separately verified in any report. Not evidenced; left
    unchecked.
  - AC-3: no report records a per-criterion verdict for the template-conformance CI check. Not
    evidenced; left unchecked.
  - AC-4: no report records a per-criterion verdict for the shared gate/check library requirement.
    Not evidenced; left unchecked.
  - AC-5: no report records a per-criterion verdict for golden/anti-example correctness. Not
    evidenced; left unchecked.
  - AC-6: docs/internal/execution/P2-report.md (S04-AC6, PASS: all six skills score 1.00 on the
    family U5 description scorer, threshold 0.70).
  - AC-7: no report records a per-criterion verdict for the paraphrase-policy self-test detection.
    Not evidenced; left unchecked.
- Open questions: 1
- Last-updated: 2026-08-01

## Purpose

Define the single pattern all six skills instantiate, so the P2 fan-out produces six structurally identical, contract-conformant skills that differ only in domain content. The template is the anti-drift mechanism for parallel skill construction [S5].

## Scope

The canonical skill directory shape, SKILL.md structure, frontmatter contract, scripts interface, evals and examples requirements, and the self-test each skill must pass before leaving its pipeline.

## Non-Goals

Domain content (S-05). The critic subagent (S-06). agentskills.io spec re-derivation; the template conforms to the family's existing skill conventions [S3].

## Users / Actors

Six P2 skill-pipeline agent teams (template consumers); the family gate; end-user agents triggering skills.

## Requirements

Directory shape, fixed [S1][S2][S3]:

```
skills/critique-<domain>/
  SKILL.md
  references/<source-id>.md        (one per rubric source: criterion table with IDs, anchors, operationalizations)
  references/severity-anchors.md   (domain anchor examples, extends docs/reference/severity-scale.md)
  scripts/checks.py                (scripted lane; CLI: artifact path in, contract findings JSON out)
  scripts/tests/                   (pytest for every scripted check)
  evals/triggers.eval.json         (>=20 {query, should_trigger} cases)
  examples/                        (>=3 golden runs, >=1 anti-example)
```

SKILL.md frontmatter MUST declare: `name` (`critique-<domain>`, matching directory, prefix rule D1), `description` (pushy trigger surface naming artifact types and everyday phrasings: review, feedback, second opinion, red-line, quality check; never relying on the name) [S2][S3], `version`, `license`, `rubric_sources` (citation, url, accessed, `operationalization: paraphrased | open-standard | byor`) [S1], and `checks` (`scripted: []`, `judged: []` listing criterion IDs by lane) [S1].

SKILL.md body MUST instruct the four-pass protocol in fixed order (inventory, criterion sweep in ID order, severity assignment as separate pass, rank and bound), reference the contract schema for output, state the bounded-output rule, and instruct clean-context execution via the critic subagent where available [S1].

`scripts/checks.py` MUST be deterministic (same artifact, same output bytes), emit contract-valid findings with `lane: scripted` and `confidence: high`, and exit with gate-mode codes when passed `--gate` [S1][S2].

Every skill MUST ship a domain generator module for the bench (S-03 plugin API) covering at least its scripted-lane criteria plus at least three judged-lane criteria [model-inference: minimum seeding coverage to make recall meaningful].

The template MUST include a self-test runner: schema validation of example envelopes, pytest pass, trigger-eval well-formedness, description-quality heuristics (the family's U5 scorer), and lane-manifest consistency (every `checks.scripted` ID implemented in checks.py; no criterion in both lanes).

## Acceptance Criteria

- AC-1: A template instantiation guide exists (`docs/internal/skill-template.md` or equivalent) from which a pipeline agent can build a skill without reading another skill's source. [S5]
- AC-2: The self-test runner exists and fails correctly on each of: missing lane declaration, criterion in both lanes, undeclared scripted check, schema-invalid example, under-20 trigger evals. [model-inference]
- AC-3: Frontmatter contract is machine-checked: a template-conformance script validates all six skills uniformly in CI. [S3]
- AC-4: `scripts/checks.py --gate` implements S-02 exit-code semantics identically across skills (shared library, not six copies). [S1]
- AC-5: Golden examples each contain artifact, expected envelope, and a prose note on why the findings are correct; the anti-example documents a query that must NOT trigger the skill. [S3]
- AC-6: Trigger descriptions score >= 0.7 on the family U5 description-quality rubric. [S3]
- AC-7: The template forbids and the self-test detects reproduced rubric source text beyond short anchor quotes in references (paraphrase policy D6). [S1][S5]

## Behavior / Examples

Given the toy domain from S-03's generator docs, when the template guide is followed end to end, then the resulting toy skill passes the self-test runner; this worked example is committed as the template's own golden example. [model-inference]

## Non-Functional Requirements

A skill directory loads progressively: SKILL.md under 500 lines; references loaded only when the skill runs; scripts never loaded into context, only executed [S2].

## Revisions

None (draft).

## Sources & Evidence

- S1: methodology draft (protocol, lanes, contract, provenance, IP policy). Class A.
- S2: strategy doc sec 3.3-3.5 (frontmatter provenance, pushy descriptions, progressive disclosure). Class A.
- S3: `agent-skills-toolkit` survey 2026-07-31 (golden/anti examples, >=20 trigger evals, U5 scorer, skill conventions). Class A.
- S5: `00-README.md` decisions log D1, D6; `01-strategy-brief.md` approach A rationale. Class A.

## Open Questions

- OQ-1: Whether the shared gate/check library lives in `skills/_shared/` or a top-level `lib/`; family convention check during P1 decides (askit uses `scripts/lib/`).
