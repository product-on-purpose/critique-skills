---
id: IMPL-A
title: "Foundation: scaffold, contract, bench core, CI"
type: implementation-plan
status: draft
created: 2026-07-31
updated: 2026-07-31
linked-spec: covers ../S-01_repo-scaffold/spec.md, ../S-02_critique-contract/spec.md, ../S-03_bench-harness/spec.md, ../S-07_ci-pipeline/spec.md
linked-release: ../plan_v0.1.0.md
phase-count: 4
ac-coverage: complete
audience: agent
---

# Implementation Plan A: Foundation (workflow phases P0-P1)

> Deviation note: this plan is phase-grouped across four specs rather than per-effort, because the four efforts share one serial dependency chain and one agent team. At P0 migration, it may be split per-effort if the in-repo machinery needs it; the Completion Status table already partitions by spec.

## Task Summary

- Status: draft
- Phases: [ ] A1 [ ] A2 [ ] A3 [ ] A4
- Last-updated: 2026-07-31

## Completion Status

| Phase | Goal | Fulfills AC | Owner (subagent, model) | Status |
|-------|------|-------------|------------------------|--------|
| A1 | Conformant scaffold on build branch | S-01 AC-1..AC-5, AC-7 | scaffold-builder (sonnet) + gate-verifier (haiku) | Not started |
| A2 | Plan-suite migration into repo | S-01 AC-6 | migrator (haiku) | Not started |
| A3 | Contract frozen: schema, validator, severity, methodology promoted | S-02 AC-1..AC-8 | contract-designer (opus), validator-impl (sonnet), adversarial-reviewer (opus) | Not started |
| A4 | Bench core + CI live | S-03 AC-1..AC-8; S-07 AC-1..AC-5 (AC-6 measured at P5) | bench-architect (opus), harness-impl (sonnet x2), ci-impl (sonnet), reviewers (sonnet/haiku) | Not started |

## Phase A1: Conformant scaffold

**Goal.** S-01's skeleton, gate-green, on `build/v0.1.0`.

**Steps.**
1. Create branch `build/v0.1.0` from `main`.
2. Inspect `pm-skills` and `thinking-framework-skills` for the family gate wiring (S-01 OQ-1); adopt the family answer; draft ADR.
3. Read the pinned Standard version from `agent-skills-toolkit/library.json`'s own `standard` usage; author `library.json` per S-01 requirements; generate `.claude-plugin/plugin.json`.
4. Author LICENSE (Apache-2.0), extend `.gitignore`, starters for AGENTS.md, README, CHANGELOG (`[Unreleased]`), RELEASE-NOTES, Diataxis docs tree.
5. Author ADRs D1-D10 (MADR, TL;DR each) into `docs/internal/decisions/`.
6. Run the gate; iterate to zero errors.

**Verification.** Gate exit 0 at Universal; plugin.json regeneration diff-free; ADR count = 10 + wiring ADR.

**Decision gate.** If the family has no settled gate-wiring answer, default to pinned dependency and record the ADR as provisional; do not block.

**Output artifacts.** Scaffold commit on `build/v0.1.0` tagged in message as `P0 scaffold`.

## Phase A2: Plan-suite migration

**Goal.** S-01 AC-6: specs and release plan live in-repo.

**Steps.** Copy `_local/initial-plan/specs/S-*` folders to `docs/internal/release-plans/plan_v0.1.0/`; transform `05-release-plan.md` into `plan_v0.1.0/plan_v0.1.0.md`; rewrite relative links; leave `_local/` untouched; commit.

**Verification.** Link checker over migrated tree; folder count = 8.

**Decision gate.** None.

**Output artifacts.** Migration commit.

## Phase A3: Contract frozen

**Goal.** Every S-02 AC; downstream interfaces stable from here on.

**Steps.**
1. contract-designer drafts `contract/critique-contract.schema.json` (finding, envelope, disposition log, criterion regex, contract_version) resolving S-02 OQ-1/OQ-2 and S-06 OQ-1 with ADRs.
2. validator-impl builds `contract/validate.py` (library + CLI + `--gate` exit codes) with the malformed-variant test suite (S-02 AC-2).
3. Promote methodology to `docs/explanation/methodology.md`: em-dash sweep, status labels kept, schema examples synced to the shipped schema.
4. Author `docs/reference/severity-scale.md` (anchors x6 domains), `criterion-ids.md`, `critique-contract.md` (by-reference commentary).
5. adversarial-reviewer attacks the schema per S-02 AC-8; close or ADR each hole.

**Verification.** S-02 AC-1..AC-7 checks scripted where possible; AC-8 report committed.

**Decision gate.** Any change to finding/envelope required fields after this phase is a build-run stop condition (halt and write handover), not a quiet edit.

**Output artifacts.** Contract commit `P1 contract`; frozen-interface notice in the run journal.

## Phase A4: Bench core and CI

**Goal.** S-03 harness core plus S-07 workflows, both verified.

**Steps.**
1. bench-architect designs the domain-plugin API and location-tolerance rules (S-03 OQ-1); ADR.
2. harness-impl builds generator core, manifest schema, metrics module with the five named unit-test scenarios, baseline runner with frozen prompt text, `results.json` schema and table generator.
3. ci-impl writes `ci.yml`, `bench.yml`, `release.yml` plus the npm/python script surface; documents every command in AGENTS.md.
4. Verifiers: corpus determinism double-run; planted per-category CI failures on a scratch branch (S-07 AC-1); logic-free workflow audit (S-07 AC-2); leak check (S-03 AC-8).

**Verification.** All S-03 and S-07 AC except runtime (AC-6, deferred to P5) green by command output.

**Decision gate.** If deterministic generation proves infeasible for any planned artifact type, narrow the artifact type (record in ADR) rather than weaken determinism.

**Output artifacts.** Commits `P1 bench-core`, `P1 ci`; foundation phase report.
