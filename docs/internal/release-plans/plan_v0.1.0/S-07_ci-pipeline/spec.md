---
id: S-07
title: CI pipeline
type: spec
status: committed
created: 2026-07-31
updated: 2026-08-01
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

- Status: committed
- AC: [x] AC-1 [x] AC-2 [x] AC-3 [x] AC-4 [x] AC-5 [x] AC-6
- AC evidence:
  - AC-1: **MET 2026-09-14.** Both halves of the criterion were run. Local: a deliberate failure
    planted in each category, one at a time, reproduced a failure with that job's own command, with
    the tree asserted clean between cases. Live: each plant was pushed as its own commit to
    `verify/s07-ac1-planted-failures` and run on GitHub-hosted infrastructure through PR 42, and in
    every case the job the plant was aimed at went red. **8 of 8 categories, plus a green control.**

      | category | commit | run | plant |
      |---|---|---|---|
      | conformance | `79171b1` | [34873969976](https://github.com/product-on-purpose/critique-skills/actions/runs/34873969976) | README envelope figure 541 to 999 |
      | drift | `36a7b7f` | [34874249231](https://github.com/product-on-purpose/critique-skills/actions/runs/34874249231) | hand-written row appended to generated `INDEX.md` |
      | schema | `70c6108` | [34874340934](https://github.com/product-on-purpose/critique-skills/actions/runs/34874340934) | `run.skill` removed from one committed envelope |
      | corpus | `9892f6c` | [34873984315](https://github.com/product-on-purpose/critique-skills/actions/runs/34873984315) | prose appended to a locked corpus artifact |
      | unit-node | `e88df3f` | [34874425180](https://github.com/product-on-purpose/critique-skills/actions/runs/34874425180) | a README door label renamed |
      | unit-python | `92de2e7` | [34873991315](https://github.com/product-on-purpose/critique-skills/actions/runs/34873991315) | `SKILL.md` frontmatter name no longer matches its directory |
      | smoke | `90cd04c` | [34874510947](https://github.com/product-on-purpose/critique-skills/actions/runs/34874510947) | `critique-clarity`'s scripted lane raises on import |
      | build-site | `2405610` | [34874591367](https://github.com/product-on-purpose/critique-skills/actions/runs/34874591367) | a baseline route the site does not build |
      | CONTROL | `d2d0891` | [34874008925](https://github.com/product-on-purpose/critique-skills/actions/runs/34874008925) | tree restored: **15 jobs, 0 failures** |

    Three things the exercise established beyond the criterion itself. **`ci-ok` failed in all eight
    red runs and passed in the green one**, which is the first live evidence that ADR 0033's
    aggregate gate actually gates rather than merely reporting. **The control run is what makes the
    eight reds mean anything**: without it they are equally consistent with a branch that was simply
    broken. And **matrix `fail-fast` defaults to true**, so a failing leg cancels its sibling and a
    run shows `schema (Node 24)` red with `schema (Node 22.12.0)` neither red nor green; the
    category still fails, which is what this criterion asks, but a reader should not read a
    cancelled sibling as a pass.

    **`audit` is the one category not planted, deliberately.** Making `npm audit --audit-level=high`
    fail requires introducing a genuinely vulnerable dependency into a public repository, which is
    not a thing to do for a test. That leaves one of nine categories evidenced by inspection only,
    and saying so is more useful than a table that implies otherwise.
  - AC-2: docs/internal/execution/P1-report.md (S07-AC2, FAIL: `release.yml` computed a verdict
    inline via shell/`awk`). Fixed in P2 (docs/internal/execution/P2-report.md phase summary,
    commit `9ef369d`) and independently reconfirmed this pass: `release.yml` now calls
    `scripts/extract-release-notes.mjs`, no inline `awk`.
  - AC-3: docs/internal/execution/P1-report.md (S07-AC3, PASS)
  - AC-4: **MET 2026-09-15.** Run
    [34932832402](https://github.com/product-on-purpose/critique-skills/actions/runs/34932832402).
    Tag `v9.9.9` was pushed while every version-bearing manifest read `0.1.6`, and `release.yml`
    behaved exactly as the criterion requires:

      | step | outcome |
      |---|---|
      | Guard, tag must equal every version-bearing manifest | **failure** |
      | Extract this version's RELEASE-NOTES section | skipped |
      | Create GitHub release | skipped |

    The guard named all three manifests individually rather than failing on the first
    (`error: package.json version "0.1.6" does not match tag "9.9.9"`, and the same for
    `library.json` and `.claude-plugin/plugin.json`) and exited with
    `version guard failed: tag/version mismatch; aborting before publishing a release`. **No release
    was created**: `gh release view v9.9.9` returns "release not found" and the release list still
    ends at `v0.1.6`. The tag was deleted from the remote immediately afterwards.

    **On "in a scratch clone".** The criterion's wording was read for a while as requiring a scratch
    *repository*, which this token cannot clean up afterwards. That reading was wrong and the
    correction is worth keeping: a pushed tag triggers a workflow whose first step is
    `actions/checkout`, so **GitHub makes the scratch clone**, on a clean runner, from the tag. The
    intent behind the wording was never "use a different repository", it was "do not test in the
    working tree the thing was authored in", which is the same reason P4's local replay was judged
    insufficient for AC-1. A runner checkout satisfies that more completely than a hand-made clone,
    and it exercises this repository's own workflow rather than a copy of it.

    **What this added over what already existed**, stated honestly because it was nearly skipped:
    the guard already had six unit tests including this exact scenario, and `release.yml` had
    already run successfully on five real tags. What none of that covered was the **negative path**
    on real infrastructure: that a non-zero exit from the guard step actually halts the job before
    the publish step. The guard had never once been observed blocking anything. That is the same
    shape as three defects this repository has already found in itself, the `ci-ok` job that would
    have passed green without `if: always()`, Gold checks G1 and G3 passing vacuously, and the
    Standard's section 7.1 requirement having no check module at all. A guard whose negative path
    has never fired is not yet a guard.

    Superseded reading, kept for the record: **PARTIALLY MET 2026-09-14, left unchecked on a strict
    reading.**
    What was done: a scratch clone was made outside this tree, and `scripts/check-release-versions.mjs`
    was exercised in it against five tags. A matching tag exits 0; `v9.9.9`, `v0.1.5` and a
    non-semver string each exit 1. **The criterion's exact scenario was then run**: `library.json`
    forced to `0.9.9` while `package.json` and `.claude-plugin/plugin.json` stayed at `0.1.6`, tag
    `v0.1.6`. The guard exits 1, names `library.json` specifically, and reports the other two as
    passing. `.github/workflows/release.yml` carries no `continue-on-error`, so a non-zero step
    fails the job.

    What is still missing, and why it stays unchecked: the criterion says `release.yml` **on a test
    tag**, and `release.yml` is tag-triggered, so the honest version of this test needs a pushed tag
    against a real Actions runner. Doing that in this repository would leave a stray tag and a
    deliberately red release run in a public history; the recorded preference is a scratch GitHub
    repository instead. That was not done because the available `gh` token carries `repo` but not
    `delete_repo`, so a scratch repository could be created and then not cleaned up. Tracked as E15.
  - AC-5: docs/internal/execution/P1-report.md (S07-AC5, PASS)
  - AC-6: **MET 2026-09-14.** Measured on GitHub-hosted runners across the three most recent `main`
    runs of `ci.yml`: **31, 41 and 67 seconds**, against a target of under 4 minutes. The criterion
    named P5 as the measurement point and no P5 report was ever written, which is why this sat
    unchecked long after it was satisfiable; the measurement itself was never the hard part.
- Open questions: 0
- Last-updated: 2026-09-15

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
