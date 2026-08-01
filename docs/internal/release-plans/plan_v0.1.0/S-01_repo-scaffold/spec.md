---
id: S-01
title: Repo scaffold and family conformance
type: spec
status: fulfilled
created: 2026-07-31
updated: 2026-08-01
linked-effort: S-01
linked-plan: ../implementation/IMPL-A-foundation.md
linked-strategy-brief: "01-strategy-brief.md (local planning archive, not committed)"
linked-release: ../plan_v0.1.0.md
source-count: 4
ac-count: 7
audience: agent
---

# Spec: Repo scaffold and family conformance

## Task Summary

- Status: fulfilled
- AC: [x] AC-1 [x] AC-2 [x] AC-3 [x] AC-4 [x] AC-5 [x] AC-6 [x] AC-7
- AC evidence:
  - AC-1: docs/internal/execution/P0-report.md (S01-AC1, PASS)
  - AC-2: docs/internal/execution/P0-report.md (S01-AC2, PASS)
  - AC-3: docs/internal/execution/P0-report.md (S01-AC3, PASS)
  - AC-4: docs/internal/execution/P0-report.md (S01-AC4, PASS)
  - AC-5: docs/internal/execution/P0-report.md (S01-AC5, PASS)
  - AC-6: docs/internal/execution/P0-report.md (S01-AC6, PASS)
  - AC-7: docs/internal/execution/P0-report.md (S01-AC7, PASS)
- Open questions: 1
- Last-updated: 2026-08-01

## Purpose

Turn the near-empty `critique-skills` repo into a Standard-conformant plugin skeleton that passes the family gate with zero errors before any product content lands, so every later phase builds on verified ground [S3].

## Scope

Repo root files, manifests, branch setup, planning-artifact migration, and decision records. No skills, no bench content, no docs beyond starters.

## Non-Goals

Silver-tier conformance (roadmap v0.3) [S5]. Docs site. Marketplace listing execution (human action, release plan). Any content the seed template does not require.

## Users / Actors

Build-run subagents (primary consumers of the scaffold); the family conformance gate; Jonathan at RC review.

## Requirements

The repo MUST carry a root `library.json` with the five Universal-required fields (`name`, `version`, `description`, `standard`, `tier`) and, although optional at Universal, MUST also declare `prefix: "critique-"` and a `components` inventory, per decision D1/D10 [S5][S3]. `name` is `critique-skills`, `version` is `0.1.0`, `tier` is `universal`, `standard` pins the current family Standard version read from `agent-skills-toolkit` at scaffold time [S3].

`.claude-plugin/plugin.json` MUST exist with `name`, `version`, `description`, `license` and MUST be generated from `library.json`, never hand-authored, following the family dual-representation rule [S3][S4].

The repo MUST include: Apache-2.0 `LICENSE` [S5], the existing `.gitignore` extended to the family convention (`_local/`, `_LOCAL/`, plus toolchain noise), `AGENTS.md`, `README.md` starter, `CHANGELOG.md` with an `[Unreleased]` section (Keep a Changelog), `RELEASE-NOTES.md` starter, and the Diataxis docs tree with `docs/internal/decisions/` [S3].

All work MUST happen on branch `build/v0.1.0` with commits at phase boundaries; nothing is pushed [S5].

The plan suite in `_local/initial-plan/specs/` MUST migrate to `docs/internal/release-plans/plan_v0.1.0/` per-effort folders, and `05-release-plan.md` content to `plan_v0.1.0/plan_v0.1.0.md`, updating relative links [S5]. The `_local/` originals remain untouched as the historical record. [model-inference: migration keeps the release-plan machinery usable in-repo]

ADRs MUST be recorded in MADR format with `## TL;DR` for decisions D1 through D10 from `00-README.md` [S3][S5].

The P0 exit command MUST be the family gate reporting zero errors at Universal tier; the gate-wiring mechanism follows whatever `pm-skills` or `thinking-framework-skills` currently uses (inspect first, copy the family answer, ADR the choice) [S1].

## Acceptance Criteria

- AC-1: `node`-runnable family conformance gate exits 0 with zero `error`-severity findings at Universal tier on the scaffolded repo. [S3]
- AC-2: `library.json` validates with `name: critique-skills`, `version: 0.1.0`, `tier: universal`, pinned `standard`, `prefix: "critique-"`, and a `components` array (empty allowed at P0). [S3][S5]
- AC-3: `.claude-plugin/plugin.json` exists, agrees with `library.json` on name/version/description, and regenerating it produces no diff. [S3]
- AC-4: Branch `build/v0.1.0` exists; `git log` on it shows the scaffold commit; `main` is untouched. [S5]
- AC-5: Ten ADR files exist under `docs/internal/decisions/`, one per D1-D10, each with a TL;DR section. [S5]
- AC-6: `docs/internal/release-plans/plan_v0.1.0/` contains the migrated plan document and eight `S-NN_<slug>/spec.md` folders with intact links. [S5]
- AC-7: The gate-wiring choice (vendored, dependency, or wrapper) is recorded as an ADR citing the sibling repo inspected. [S1]

## Behavior / Examples

Given a fresh checkout of `build/v0.1.0`, when a subagent runs the documented check command from `AGENTS.md`, then the gate passes and the command matches the one CI runs (no CI-only logic) [S3].

## Non-Functional Requirements

Scaffold must not introduce any dependency requiring credentials. Windows-first development environment: all scripts must run under both Git Bash and PowerShell. [model-inference from the owner's environment]

## Revisions

None (draft).

## Sources & Evidence

- S1: `_local/initial-plan/04-ci-plan.md` (gate-wiring open question). Class A (session artifact).
- S3: `agent-skills-toolkit/STANDARD.md` survey, 2026-07-31 (manifest schema, checks, dual representation, MADR/TL;DR). Class A.
- S4: `agent-plugins/CONTRIBUTING.md` survey, 2026-07-31 (L1 plugin.json requirements). Class A.
- S5: `00-README.md` decisions log D1-D10, session 2026-07-31. Class A.

## Open Questions

- OQ-1: Whether the family currently prefers vendored checks or a toolkit dependency (resolved by inspection during P0, AC-7).
