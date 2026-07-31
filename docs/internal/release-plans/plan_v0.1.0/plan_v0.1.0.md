---
version: v0.1.0
title: "Release plan: v0.1.0"
type: release-plan
status: draft
created: 2026-07-31
updated: 2026-07-31
target-date: null
includes: [S-01, S-02, S-03, S-04, S-05, S-06, S-07, S-08]
spec-count: 8
plan-count: 2
checklist-complete: false
audience: both
---

# Release Plan: v0.1.0

> **Location note.** This plan now lives in-repo at `docs/internal/release-plans/plan_v0.1.0/`, with per-effort subfolders (`S-NN_<slug>/spec.md`) and phase-grouped implementation plans under `implementation/`. `/jp-release-plan --update` and `--gate` operate on this in-repo copy. `_local/initial-plan/` holds the historical original from before the P0 migration; it is not updated further and is not committed. Aggregation below is hand-seeded once for planning; the in-repo copy is regenerated, never hand-edited.

## Theme

Prove accountable critique: three measured skills, a finding contract, and a seeded benchmark, shipped as a Bronze-conformant marketplace plugin.

## Context

First release of the third product-on-purpose library. Built by a fully autonomous agent workflow to a release candidate on branch `build/v0.1.0`; Jonathan reviews the RC and personally performs every publish action (merge, tag, push, marketplace re-pin). Decisions D1-D10 in `00-README.md` are settled inputs to this plan.

---

## Aggregation

| id | title | spec-status | plan-status | AC-coverage | has-plan? |
|----|-------|-------------|-------------|-------------|-----------|
| S-01 | Repo scaffold and family conformance | draft | draft | pending | yes (IMPL-A) |
| S-02 | Critique Contract: schema, envelope, severity | draft | draft | pending | yes (IMPL-A) |
| S-03 | Bench harness: generator, corpus, metrics | draft | draft | pending | yes (IMPL-A) |
| S-04 | Skill template pattern | draft | draft | pending | yes (IMPL-B) |
| S-05 | Skills slate: 3 core + 3 stretch | draft | draft | pending | yes (IMPL-B) |
| S-06 | Clean-context critic subagent | draft | draft | pending | yes (IMPL-B) |
| S-07 | CI pipeline | draft | draft | pending | yes (IMPL-A) |
| S-08 | Documentation and release packaging | draft | draft | pending | yes (IMPL-B) |

Implementation plans are phase-grouped (`implementation/IMPL-A-foundation.md` covers P0-P1 efforts, `implementation/IMPL-B-skills-to-rc.md` covers P2-P5); each spec's AC map to named workflow phase outputs.

---

## Hygiene Gates

These conditions block tagging. The in-repo `--gate` reports pass/fail after migration.

| Gate | Condition | Status |
|------|-----------|--------|
| (a) Spec status | Every effort's spec has `status: committed` or `fulfilled` (no `draft`) | FAIL (all drafts; specs commit at Jonathan's plan-suite review) |
| (b) Coupled plan | Every effort has an implementation plan or a recorded waiver | PASS (phase-grouped plans cover all eight) |
| (c) AC coverage | Every implementation plan reaches `ac-coverage: complete` | pending |
| (d) Phases done | Every workflow phase P0-P5 reports Done with its exit criteria met | pending |
| (e) Staleness | No spec edited after its implementation plan's last edit | pending |

### Release-specific gates (beyond the template defaults)

| Gate | Condition | Status |
|------|-----------|--------|
| (f) Conformance | Family Standard gate: 0 errors at Universal tier, pinned Standard version | pending |
| (g) Measurement | Every shipped skill has committed envelopes for seeded recall, precision, k=5 consistency, and a baseline win on two pinned model tiers | pending |
| (h) Stretch gating | Each stretch skill has an explicit ship/hold verdict recorded with its numbers | pending |
| (i) Honesty sweep | README claims trace to repo artifacts; no survey claim; no em/en dashes; results tables generated not hand-edited | pending |

---

## Doc-Update Checklist

Every box checked before the tag. Publish actions marked (human) are Jonathan's alone.

| Doc | Update | Done |
|-----|--------|------|
| `CHANGELOG.md` | Promote [Unreleased] to v0.1.0 dated section | [ ] |
| `RELEASE-NOTES.md` | Curated v0.1.0 highlights (distinct from CHANGELOG) | [ ] |
| `README.md` | Generated results table current; catalog table matches `library.json` | [ ] |
| `AGENTS.md` | Reflects final component list | [ ] |
| `library.json` | `version: 0.1.0`; components each carry name, path, version, tier, status | [ ] |
| `.claude-plugin/plugin.json` | `version: 0.1.0`; generated, drift-free | [ ] |
| `skills/*/SKILL.md` | Per-skill `version` frontmatter set | [ ] |
| `docs/internal/decisions/` | ADRs for D1-D10 plus any in-run decisions, each with TL;DR | [ ] |
| `bench/results/` | Envelopes committed for every number cited anywhere | [ ] |
| Git tag `v0.1.0` | Annotated tag after all above (human) | [ ] |
| `agent-plugins` registry | Listing PR: entry with SHA pin on the tag, `strict: true`, registry CHANGELOG row (human merge) | [ ] |

---

## RC Definition (what "fully autonomous to RC" delivers)

The run halts and hands over when ALL of the following hold on `build/v0.1.0`:

1. Gates (b), (f), and the deterministic half of (i) are green by command output.
2. Gate (g) evidence exists for all six skills; gate (h) verdicts are drafted for the three stretch skills.
3. All checklist rows except the two human rows are checked.
4. Version 0.1.0 is consistent across every manifest.
5. A handover report exists at `_local/initial-plan/rc-handover.md`: what shipped, what was gated out, every in-run decision with its ADR link, the unflattering numbers called out first, and a recommended review order.

Anything the run could not honestly complete appears in the handover report as an open item, never silently skipped.

## Open Questions / Decisions

| ID | Title | Resolution | Status | Updated |
|----|-------|------------|--------|---------|
| R1 | Consistency floor value for stretch gating | Set empirically from P3 core-skill data; the floor is the lowest core-skill consistency, minus nothing | Open | 2026-07-31 |
| R2 | Usability artifact-type claim | Recommend narrow claim (HTML/markdown UI specs) in v0.1.0, widen later | Open | 2026-07-31 |
| R3 | Baseline model tiers to pin | Recommend claude-haiku-4-5 and claude-sonnet-5 (exact IDs pinned at P3 run time) | Open | 2026-07-31 |

### R1: Consistency floor value (Open)

**Summary.** The 0.7 Jaccard target is a placeholder; the stretch-skill gate needs a real number.

**Context.** No empirical data exists until P3. A pre-committed arbitrary floor would either block everything or gate nothing.

**Desired outcome.** A floor that is defensible in public ("stretch skills ship only if they are at least as consistent as the core skills we measured first").

**Recommendation.** Floor = min(core-skill consistency scores) measured in P3. Simple, honest, self-calibrating. Decided in-run, recorded as an ADR.

> **Maintainer decision:** _(pending; delegated to the run per D8 unless Jonathan overrides at plan review)_

---

## Notes

Publish boundary: the autonomous run never pushes, tags, or opens PRs. Everything outward-facing is staged as local artifacts (branch, drafted PR text) for human action.
