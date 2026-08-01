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
- AC: [x] AC-1 [x] AC-2 [ ] AC-3 [x] AC-4 [x] AC-5 [x] AC-6 [x] AC-7
- AC evidence:
  - AC-1: PASS. `docs/internal/skill-template.md` (803 lines) covers directory shape, SKILL.md
    frontmatter (format, required fields, description scoring, two worked examples), SKILL.md body
    structure and delegation, scripted-lane discipline and what determinism does and does not cover,
    `references/` file formats, a full worked `scripts/checks.py` wiring example plus the shared
    `skills/_shared` API surface, `evals/` and `examples/` formats, the corpus-module obligation, what
    the self-test does and does not check, and a 13-step "Building a skill end to end" walkthrough
    that references only `skills/_template-fixture/critique-toy/`, never another domain skill's
    source. Re-ran `python scripts/skill-selftest.py skills/<name>` fresh against all six shipped
    skills this pass: all six print `skill-selftest: 0 errors, 0 warning(s). PASS`, consistent with
    having been built from this guide alone.
  - AC-2: PASS. `scripts/tests/test_skill_selftest.py` names and exercises exactly AC-2's five
    failure modes, each with its own test asserting the distinct rule name:
    `test_missing_lane_declaration_fails_distinctly`, `test_criterion_in_both_lanes_fails_distinctly`,
    `test_undeclared_scripted_check_fails_distinctly`, `test_schema_invalid_example_fails_distinctly`,
    `test_under_20_trigger_evals_fails_distinctly`. Ran `python -m pytest
    scripts/tests/test_skill_selftest.py -k "..."` naming all five: 5 passed. Independently
    reproduced one mode outside pytest: truncated a copy of the toy fixture's
    `evals/triggers.eval.json` to 5 cases and ran `python scripts/skill-selftest.py` directly against
    it, which printed `[trigger-evals-too-few] ...: 5 case(s), need at least 20` distinctly.
  - AC-3: FAIL, verified. AC-3's text requires the template-conformance script to validate all six
    skills "uniformly in CI." Nothing does: `.github/workflows/ci.yml`'s only Python job runs
    `python -m pytest`, and `scripts/tests/test_skill_selftest.py`'s own cases run
    `scripts/skill-selftest.py` only against the synthetic `skills/_template-fixture/critique-toy`
    fixture and broken `tmp_path` copies, never against a real `skills/critique-*` directory; grepped
    `.github/workflows/`, `package.json`, and every `*.py`/`*.mjs`/`*.js` file in the repo for
    `skill-selftest`, finding only the script itself, its own test module, and skills' own
    `checks.py` docstring comments that name it in passing. The only place all six real skills were
    ever swept with this script is a one-time manual audit command recorded in
    `docs/internal/execution/P2-report.md`'s S05-AC1 row, which is not CI. Re-ran that sweep by hand
    this pass (`for d in skills/critique-*/; do python scripts/skill-selftest.py "$d"; done`): all six
    still pass cleanly, so the validator itself is sound, but AC-3's specific "in CI" claim is not
    met. Left unchecked; closing this needs a CI job (or a pytest case) that globs
    `skills/critique-*` and runs `skill-selftest.py` against each.
  - AC-4: PASS. `skills/_shared/gate.py`'s own module docstring: "the load-bearing file for S-04
    AC-4," re-exporting `gate_exit_code`/`validate_document` from `contract/validate.py` rather than
    reimplementing them. Grepped all six skills' `scripts/checks.py`: every one imports
    `run_scripted_lane` from `skills._shared.runner` (which itself resolves to
    `skills._shared.gate.gate_exit_code`) with an identical `main()` shape; none reimplements gate
    logic locally. Ran `--gate` directly against two skills with severity-3 findings present and the
    default threshold 0 (`critique-accessibility` on `bench/corpus/accessibility/accessibility-001.html`,
    `critique-usability` on `examples/artifacts/golden-01-settings.html`): both exit 2, matching S-02
    semantics. `pytest contract/tests/test_gate.py`: 14 passed.
  - AC-5: PASS. `scripts/skill-selftest.py`'s golden/anti-example checks
    (`EXAMPLES_MIN_GOLDEN=3`, `EXAMPLES_MIN_ANTI=1`, `GOLDEN_NOTE_MIN_LENGTH=40`) are exercised
    distinctly by `test_too_few_golden_examples_fails` and `test_missing_anti_example_fails`, both
    passing. Spot-checked `skills/critique-accessibility/examples/golden-02.json` and `anti-01.json`
    directly: the golden carries `artifact`, `expected_envelope`, and a `note` explaining why each
    finding is correct; the anti-example carries a `query` plus a `note` explaining why it must not
    trigger the skill. All six real skills pass `skill-selftest.py` fresh (re-run above), which
    enforces this shape for every skill, not only accessibility.
  - AC-6: PASS. docs/internal/execution/P2-report.md (S04-AC6, PASS: all six skills score 1.00 on the
    family U5 description scorer, threshold 0.70).
  - AC-7: PASS. `test_over_long_quote_in_references_fails` and `test_quoted_operationalization_cell_fails`
    (both in `scripts/tests/test_skill_selftest.py`) independently exercise the paraphrase-policy
    detector (`MAX_ANCHOR_QUOTE_WORDS=25`, D6): a references quote over 25 words and a quoted
    Operationalization-column cell each fail distinctly. Ran `python -m pytest
    scripts/tests/test_skill_selftest.py -k "over_long_quote_in_references_fails or
    quoted_operationalization_cell_fails"`: 2 passed.
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
