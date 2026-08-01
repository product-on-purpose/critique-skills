---
id: S-08
title: Documentation and release packaging
type: spec
status: committed
created: 2026-07-31
updated: 2026-08-01
linked-effort: S-08
linked-plan: ../implementation/IMPL-B-skills-to-rc.md
linked-strategy-brief: "01-strategy-brief.md (local planning archive, not committed)"
linked-release: ../plan_v0.1.0.md
source-count: 3
ac-count: 7
audience: agent
---

# Spec: Documentation and release packaging

## Task Summary

- Status: fulfilled
- AC: [x] AC-1 [x] AC-2 [x] AC-3 [x] AC-4 [x] AC-5 [x] AC-6 [x] AC-7
- AC evidence:
  - AC-1: docs/internal/execution/P4-report.md (S08-AC1, Pass with a caveat: the two named
    cold-read weak spots were fixed and confirmed at their cited locations, not re-verified by an
    independent fresh-context 90-second read, since no subagent tool was available to that pass).
  - AC-2: docs/internal/execution/P4-report.md (S08-AC2, Pass)
  - AC-3: docs/internal/execution/P4-report.md (S08-AC3, Pass)
  - AC-4: docs/internal/execution/P4-report.md (S08-AC4, Pass)
  - AC-5: docs/internal/execution/P4-report.md (S08-AC5, Pass)
  - AC-6: docs/internal/execution/P5-report.md, Remediation addendum (2026-08-01): version guard
    passed (`GITHUB_REF_NAME=v0.1.0 node scripts/check-release-versions.mjs`) as part of the full
    deterministic suite run recorded there, independent of the packaging pass's self-report.
  - AC-7: `_local/initial-plan/marketplace-listing-pr.md` and `_local/initial-plan/rc-handover.md`
    both exist (handover written 2026-08-01 by the orchestrating session at run close). Note:
    both live in gitignored `_local/` by design (local working documents for the human publish
    steps); the repository intentionally does not track them.
- Open questions: 0
- Last-updated: 2026-08-01

## Purpose

Produce the human-facing view layer and the release packaging exactly as `03-documentation-plan.md` defines, plus the RC handover artifacts the autonomy model requires [S1][S5].

## Scope

README, QUICKSTART, the `docs/` tree from the documentation plan, generated tables and their generators, CHANGELOG/RELEASE-NOTES preparation, version consistency, the marketplace listing PR text, and `rc-handover.md`.

## Non-Goals

Docs site. Essays. Contributor guide beyond the methodology's checklist. Anything the human performs at publish time (tagging, pushing, PR opening).

## Users / Actors

Strangers landing on the README (90-second comprehension target); Claude Code users following QUICKSTART; Jonathan consuming the handover; the marketplace registry maintainer role.

## Requirements

README MUST open with the generated results table, then the accountable-critique claim in three paragraphs, install instructions, generated skill-catalog table, the thinking-versus-critique boundary tests, and family links; every claim traceable to a repo artifact; no survey claim [S1][S5].

QUICKSTART MUST be a single no-branch path: install from marketplace, critique one bundled example artifact, read the envelope, record one disposition [S1].

The `docs/` tree MUST match the documentation plan's table exactly (explanation/methodology.md arrives via S-02; reference pages for contract, severity, criterion IDs; how-to for gate-in-ci and dispositions; bench/README.md) with G7-style frontmatter on every page [S1].

Generators MUST produce: README results table (from `bench/results/results.json`), README catalog table (from `library.json`), `INDEX.md`; each with a `--check` drift mode wired into CI [S1][S4].

CHANGELOG MUST have its `[Unreleased]` promoted to a dated 0.1.0 section; RELEASE-NOTES MUST carry a curated, distinct 0.1.0 entry; every version-bearing manifest MUST read 0.1.0 [S2].

Marketplace listing PR text MUST be drafted (registry entry JSON with placeholder SHA, description, registry CHANGELOG row) and saved to `_local/initial-plan/marketplace-listing-pr.md` for human use; nothing is opened against `agent-plugins` [S2][S5].

`rc-handover.md` MUST follow the release plan's RC definition item 5: shipped versus gated-out, in-run decisions with ADR links, unflattering numbers first, recommended review order [S5].

## Acceptance Criteria

- AC-1: A cold-read agent given only README answers correctly: what the library claims, how claims are evidenced, what the six skills cover, and where the boundary with thinking-framework-skills lies. [S1][model-inference: cold-read verification method]
- AC-2: QUICKSTART executes end to end in a fresh environment (verified by an agent following it literally, no improvisation). [S1]
- AC-3: Every `docs/**` page (excluding internal) carries `title`, `description`, `audience`, `level` frontmatter. [S1]
- AC-4: All three generators exist; hand-editing any generated region then running `--check` fails. [S1][S4]
- AC-5: Zero em or en dashes across every authored file in the repo (scripted sweep, wired as a CI grep in the drift job). [S5]
- AC-6: Version 0.1.0 consistent across `library.json`, `.claude-plugin/plugin.json`, CHANGELOG section, RELEASE-NOTES entry, and all SKILL.md frontmatter. [S2]
- AC-7: `rc-handover.md` and `marketplace-listing-pr.md` exist and conform to their content requirements. [S5]

## Behavior / Examples

Given the stretch skill critique-argument fails its gate, then README's catalog shows only shipped skills, `bench/results/` still publishes its numbers, RELEASE-NOTES mentions the hold honestly, and the handover explains the verdict: the honest-failure path is a first-class documented flow. [S5]

## Non-Functional Requirements

House style everywhere (no em/en dashes, reference IDs always paired with a handle). README renders correctly on GitHub's markdown (tables, no HTML dependencies). [S5]

## Revisions

None (draft).

## Sources & Evidence

- S1: `_local/initial-plan/03-documentation-plan.md`. Class A.
- S2: `agent-plugins/CONTRIBUTING.md` survey (listing entry shape, L4 hygiene); family release conventions from `agent-skills-toolkit` survey. Class A.
- S4: `_local/initial-plan/04-ci-plan.md` (drift job). Class A.
- S5: `00-README.md` decisions log; `05-release-plan.md` (RC definition, gate i). Class A.

## Open Questions

N/A - documentation decisions are settled in the documentation plan.
