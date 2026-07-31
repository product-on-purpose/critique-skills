---
id: S-07
title: CI pipeline
type: spec
status: draft
created: 2026-07-31
updated: 2026-07-31
linked-effort: S-07
linked-plan: ../implementation/IMPL-A-foundation.md
linked-strategy-brief: "01-strategy-brief.md (local planning archive, not committed)"
linked-release: ../plan_v0.1.0.md
source-count: 3
ac-count: 6
audience: agent
---

# Spec: CI pipeline

## Task Summary

- Status: draft
- AC: [ ] AC-1 [ ] AC-2 [ ] AC-3 [ ] AC-4 [ ] AC-5 [ ] AC-6
- Open questions: 0
- Last-updated: 2026-07-31

## Purpose

Implement `04-ci-plan.md` as workflows plus the scripts they call, honoring the family rule that CI contains no logic and every failure reproduces locally [S3][S4].

## Scope

`.github/workflows/ci.yml`, `bench.yml`, `release.yml`; the npm/python script surface they call; local developer commands documented in `AGENTS.md`.

## Non-Goals

CodeQL (v0.2). Docs-site build job (no site in v0.1). Per-PR model-dependent benchmarking (explicitly excluded by design) [S4].

## Users / Actors

GitHub Actions; build-run agents running the same commands locally; Jonathan at release time.

## Requirements

`ci.yml` MUST run, on push and PR, exactly the seven jobs from the CI plan (conformance, unit-python, unit-node, schema, corpus, drift, audit), each a single documented command, matrix Node 22.12.0 and 24, Python 3.12 [S4][S3].

`bench.yml` MUST be `workflow_dispatch` only, require the API-key secret, accept skill/k/tier inputs, and write results as a branch diff, never a direct push [S4].

`release.yml` MUST trigger on `v*` tags, re-run the deterministic suite, enforce tag-equals-manifests version consistency, and publish a GitHub Release from the `RELEASE-NOTES.md` section [S3][S4].

Every command MUST be runnable locally with identical results and be listed in `AGENTS.md` under a "checks" section [S3].

All version-bearing files MUST be enumerated in one place consumed by both the release workflow and the version-bump script. [model-inference: single enumeration prevents the version-drift class of release failure]

## Acceptance Criteria

- AC-1: `ci.yml` exists with the seven jobs; a deliberate failure planted in each category (one at a time, in a test branch during P4 verification) fails its job and reproduces locally with the same command. [S4]
- AC-2: Workflows contain no conditional validation logic (grep-auditable: no inline `if` beyond job orchestration, no shell pipelines that compute verdicts). [S3]
- AC-3: `bench.yml` refuses to run without dispatch inputs and secret; dry-run mode works without the secret. [S4]
- AC-4: `release.yml` on a test tag in a scratch clone correctly blocks when `library.json` disagrees with the tag. [S3]
- AC-5: `AGENTS.md` lists every CI command; drift job fails if a workflow command is absent from `AGENTS.md`. [S3][model-inference]
- AC-6: Total `ci.yml` runtime under 4 minutes on GitHub-hosted runners (measured once in P5 verification). [S4]

## Behavior / Examples

Given a PR that edits a committed results table by hand, when CI runs, then the drift job fails because regenerating from `results.json` produces a diff, enforcing the generated-tables rule [S5-doc-plan].

## Non-Functional Requirements

No secrets in per-commit jobs. Workflows pin action versions by SHA. [model-inference: supply-chain hygiene consistent with family posture]

## Revisions

None (draft).

## Sources & Evidence

- S3: `agent-skills-toolkit` survey (CI design rules, release workflow pattern, Node baseline). Class A.
- S4: `_local/initial-plan/04-ci-plan.md`. Class A.
- S5-doc-plan: `03-documentation-plan.md` (generated tables seam). Class A.

## Open Questions

N/A - the gate-wiring question lives in S-01 OQ-1.
