---
id: S-02
title: "Critique Contract: schema, envelope, severity"
type: spec
status: draft
created: 2026-07-31
updated: 2026-07-31
linked-effort: S-02
linked-plan: ../implementation/IMPL-A-foundation.md
linked-strategy-brief: "01-strategy-brief.md (local planning archive, not committed)"
linked-release: ../plan_v0.1.0.md
source-count: 3
ac-count: 8
audience: agent
---

# Spec: Critique Contract: schema, envelope, severity

## Task Summary

- Status: draft
- AC: [ ] AC-1 [ ] AC-2 [ ] AC-3 [ ] AC-4 [ ] AC-5 [ ] AC-6 [ ] AC-7 [ ] AC-8
- Open questions: 2
- Last-updated: 2026-07-31

## Purpose

Freeze the machine-parseable interfaces every other effort depends on: the finding schema, the run envelope, the disposition log, the severity scale, and the criterion ID grammar. This is the single most interface-critical effort in the release; every skill, the bench, the critic subagent, and gate mode consume it [S1].

## Scope

`contract/critique-contract.schema.json` (JSON Schema draft 2020-12), a Python validator callable as a library and CLI, `docs/reference/severity-scale.md` with per-domain anchor stubs, and the criterion ID registry conventions. Promotion of the methodology draft into `docs/explanation/methodology.md` (with em-dash sweep and status labels retained) belongs to this effort because the contract and constitution must not drift apart [S1][S5].

## Non-Goals

Per-skill criterion tables (S-05). Aggregation rules for instance explosion (methodology open question; v0.2). Contract versioning machinery beyond a `contract_version` field.

## Users / Actors

Skill scripts (emit findings), the critic subagent (emits envelopes), bench harness (consumes envelopes and manifests), CI (validates envelopes), downstream consumers scripting against gate mode.

## Requirements

The finding object MUST carry exactly these required fields: `id`, `criterion`, `lane` (`scripted` | `judged`), `severity` (integer 0-4), `location`, `evidence`, `violation`, `fix`, `confidence` (`high` | `medium` | `low`); optional fields: `instances` (array of locations for recurring findings), `rubric_source` (`bundled` | `byor`) [S1]. Field contracts from the methodology apply verbatim: location navigable unaided, evidence quoted or measured (never characterized), violation names the breached criterion part, fix actionable, scripted-lane confidence always `high` [S1].

The run envelope MUST carry `run` (`skill`, `skill_version`, `contract_version`, `artifact`, `artifact_sha256`, `model`, `timestamp`, `rubrics`), `findings[]`, and `summary` (`by_severity` map, `suppressed_count`, `gate` verdict) [S1]. Bounded output per the methodology: all severity 3-4 findings plus at most five below, `suppressed_count` records the rest [S1].

The disposition log MUST be schema-defined: entries of `finding_id`, `disposition` (`accept` | `reject` | `defer`), optional `note`, with envelope reference. [model-inference: the methodology mandates disposition logging but leaves its format open; a schema-defined format is required for acceptance-rate telemetry]

Criterion IDs MUST follow `<SOURCE>-<CRITERION>`, uppercase, permanent, upstream IDs adopted where they exist (WCAG success criterion numbers), one criterion one ID [S1].

Severity MUST use the single 0-4 scale with impact/frequency/persistence weighing, and `docs/reference/severity-scale.md` MUST provide per-domain anchor examples for each launch domain [S1].

Gate mode MUST be specified as exit-code semantics computable from `summary` alone: exit 0 clean, exit 1 any severity 4, exit 2 severity-3 count above a configurable threshold (default 0) [S1][S2]. [model-inference: specific exit-code assignments]

The validator MUST reject an envelope containing any em or en dash in string fields. [model-inference: house style enforced at the contract boundary, cheapest single enforcement point]

## Acceptance Criteria

- AC-1: `contract/critique-contract.schema.json` is valid JSON Schema draft 2020-12 and encodes every required finding and envelope field above; `python -m contract.validate <file>` exits nonzero on any violation. [S1]
- AC-2: The methodology's example finding and example envelope (adapted to the schema) validate; nine deliberately malformed finding variants (one per required field) each fail with a field-naming error message. [S1]
- AC-3: The disposition log schema exists in the same schema file and a sample log validates. [model-inference]
- AC-4: `docs/reference/severity-scale.md` exists with the 0-4 table and at least two anchor examples per launch domain (usability, accessibility, clarity, docs, microcopy, argument). [S1]
- AC-5: Criterion ID grammar is specified in `docs/reference/criterion-ids.md` with a regex the validator enforces on `finding.criterion`. [S1]
- AC-6: Gate-mode exit codes are implemented in the validator CLI (`--gate` flag) and documented; a severity-4 envelope produces exit 1. [S2]
- AC-7: `docs/explanation/methodology.md` exists, content-equivalent to the `_local` draft, zero em or en dashes, Status labels retained, and its schema examples match the shipped schema exactly. [S1][S5]
- AC-8: An adversarial review agent attempting to construct a finding that is schema-valid but violates a methodology field contract documents its findings; any hole found is closed or ADR-recorded as accepted. [model-inference: adversarial verification per build-run design]

## Behavior / Examples

Given the methodology's WCAG contrast example finding, when validated, then it passes; when its `evidence` is replaced with "the contrast seems low" the schema still passes but the reviewer lane flags it, demonstrating the documented boundary between schema-checkable and review-checkable contract rules. [S1]

## Non-Functional Requirements

Validator: Python 3.12 stdlib plus `jsonschema` only; runs offline; under 1 second per envelope. Schema file is the single source of truth; the reference doc embeds by reference, never copies. [S5]

## Revisions

None (draft).

## Sources & Evidence

- S1: `_local/initial-discovery/2026-07-27_claude-opus_methodology.md` (finding schema, envelope, severity, IDs, bounding, disposition mandate). Class A.
- S2: `_local/initial-discovery/2026-07-27_claude-fable-max_critique-skills-strategy.md` sec 3.5 (gate mode, exit codes concept). Class A.
- S5: `00-README.md` decisions log; `03-documentation-plan.md` (dual representation). Class A.

## Open Questions

- OQ-1: Location grammar for non-linear artifacts (methodology open question). v0.1 answer: free-text location plus optional structured `selector` field reserved but unvalidated. Confirm at RC.
- OQ-2: Whether `contract_version` starts at `1.0.0` independent of plugin version. Recommendation: yes, contract versions independently. ADR at P1.
