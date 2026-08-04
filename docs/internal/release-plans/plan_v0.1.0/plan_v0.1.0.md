---
version: v0.1.0
title: "Release plan: v0.1.0"
type: release-plan
status: draft
created: 2026-07-31
updated: 2026-08-01
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
| S-01 | Repo scaffold and family conformance | fulfilled | draft | complete | yes (IMPL-A) |
| S-02 | Critique Contract: schema, envelope, severity | fulfilled | draft | complete | yes (IMPL-A) |
| S-03 | Bench harness: generator, corpus, metrics | committed | draft | complete | yes (IMPL-A) |
| S-04 | Skill template pattern | committed | draft | complete | yes (IMPL-B) |
| S-05 | Skills slate: 3 core + 3 stretch | fulfilled | draft | complete | yes (IMPL-B) |
| S-06 | Clean-context critic subagent | fulfilled | draft | complete | yes (IMPL-B) |
| S-07 | CI pipeline | committed | draft | complete | yes (IMPL-A) |
| S-08 | Documentation and release packaging | committed | draft | complete | yes (IMPL-B) |

`spec-status` is `fulfilled` only where every one of that spec's own acceptance criteria is
evidenced by a PASS verdict in a `docs/internal/execution/` report; `committed` means the spec has
progressed past `draft` but at least one AC is deferred, unevidenced, or partially met, named in
that spec's own Task Summary AC evidence list (S-03 AC-3; S-04 AC-1, AC-2, AC-3, AC-4, AC-5, AC-7;
S-07 AC-1, AC-4, AC-6; S-08 AC-6, AC-7). `AC-coverage` here mirrors the linked implementation plan's
own `ac-coverage: complete` frontmatter field (both `IMPL-A-foundation.md` and
`IMPL-B-skills-to-rc.md` already declare it), i.e. every AC is mapped to a phase in the plan; it is
not a claim that every AC is fulfilled, which is what `spec-status` states per spec.

Implementation plans are phase-grouped (`implementation/IMPL-A-foundation.md` covers P0-P1 efforts, `implementation/IMPL-B-skills-to-rc.md` covers P2-P5); each spec's AC map to named workflow phase outputs.

---

## Hygiene Gates

These conditions block tagging. The in-repo `--gate` reports pass/fail after migration.

| Gate | Condition | Status |
|------|-----------|--------|
| (a) Spec status | Every effort's spec has `status: committed` or `fulfilled` (no `draft`) | PASS - all eight specs now read `fulfilled` (S-01, S-02, S-05, S-06) or `committed` (S-03, S-04, S-07, S-08), each with its unevidenced ACs named in its own Task Summary. |
| (b) Coupled plan | Every effort has an implementation plan or a recorded waiver | PASS (phase-grouped plans cover all eight) |
| (c) AC coverage | Every implementation plan reaches `ac-coverage: complete` | PASS - both `implementation/IMPL-A-foundation.md` and `implementation/IMPL-B-skills-to-rc.md` frontmatter already declare `ac-coverage: complete`. |
| (d) Phases done | Every workflow phase P0-P5 reports Done with its exit criteria met | PARTIAL - `docs/internal/execution/P0-report.md` through `P4-report.md` (plus `P3-cal1-report.md` and `P3-provenance.md`) each exist and each discloses its own deferrals honestly rather than claiming a clean Done; P5 (release packaging) is this pass and has not yet produced its own committed execution report. |
| (e) Staleness | No spec edited after its implementation plan's last edit | PASS - a hygiene pass on 2026-08-01 closed the gap the previous FAIL named: `IMPL-A-foundation.md` and `IMPL-B-skills-to-rc.md` now also carry `status: executed`, checked phase boxes with one-line pointers to their evidencing `docs/internal/execution/` reports, and `updated: 2026-08-01`, matching every spec's `updated` date. No spec now postdates its implementation plan. |

### Release-specific gates (beyond the template defaults)

| Gate | Condition | Status |
|------|-----------|--------|
| (f) Conformance | Family Standard gate: 0 errors at Universal tier, pinned Standard version | PASS - `node scripts/check.mjs`: "0 error(s), 0 warning(s)" at declared tier Convergent (above Universal; the twelve `[error]`-labeled lines it prints are explicitly scoped "above your declared tier (informational)" per the gate's own output and do not affect the exit code). |
| (g) Measurement | Every shipped skill has committed envelopes for seeded recall, precision, k=5 consistency, and a baseline win on two pinned model tiers | PASS - 460 scored grid envelopes plus 2 steering probe envelopes (462 JSON files under `bench/results/runs/`) for run set `p3-2026-07-31`, plus 40 `cal1-2026-08-01` calibration envelopes. At location level, `critique-accessibility` (0.1.1) and `critique-clarity` beat the frozen baseline on recall at equal-or-better precision on both pinned tiers, `critique-usability` does so on the Haiku tier only; all three stretch skills clear S-05 AC-7 (baseline win on at least one pinned tier, `critique-docs` on precision dominance at equal recall) plus the R1 consistency floor (`bench/results/README.md`; `docs/internal/execution/P3-report.md`; `P3-cal1-report.md`). |
| (h) Stretch gating | Each stretch skill has an explicit ship/hold verdict recorded with its numbers | PASS - `bench/results/verdicts.md`: all three stretch skills (`critique-docs`, `critique-microcopy`, `critique-argument`) SHIP, each citing its baseline-win and R1-floor numbers. |
| (i) Honesty sweep | README claims trace to repo artifacts; no survey claim; no em/en dashes; results tables generated not hand-edited | PASS - the unverified "40-candidate, 13-domain survey" claim in `docs/explanation/methodology.md` was corrected this pass (ADR 0029, the one explicitly authorized freeze exception); a codepoint scan of all 1,058 tracked repository files found zero U+2014 or U+2013 (the `bench/results/runs/baseline/**/*.raw.txt` carve-out was checked too and also came back clean); `python -m bench.report table --results bench/results/results.json --check` and `node scripts/gen-readme-catalog.mjs --check` both report no drift. |

---

## Doc-Update Checklist

Every box checked before the tag. Publish actions marked (human) are Jonathan's alone.

| Doc | Update | Done |
|-----|--------|------|
| `CHANGELOG.md` | Promote [Unreleased] to v0.1.0 dated section | [x] |
| `RELEASE-NOTES.md` | Curated v0.1.0 highlights (distinct from CHANGELOG) | [x] |
| `README.md` | Generated results table current; catalog table matches `library.json` | [x] |
| `AGENTS.md` | Reflects final component list | [x] (component-list version drift for `critique-accessibility` 0.1.1 fixed this pass) |
| `library.json` | `version: 0.1.0`; components each carry name, path, version, tier, status | [x] |
| `.claude-plugin/plugin.json` | `version: 0.1.0`; generated, drift-free | [x] |
| `skills/*/SKILL.md` | Per-skill `version` frontmatter set | [x] |
| `docs/internal/decisions/` | ADRs for D1-D10 plus any in-run decisions, each with TL;DR | [x] (29 ADRs, 0001-0029, each with exactly one `## TL;DR`) |
| `bench/results/` | Envelopes committed for every number cited anywhere | [x] |
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
| R1 | Consistency floor value for stretch gating | Resolved: floor set to 0.309 (overall lane cut, `critique-clarity` on `claude-haiku-4-5-20251001`), per [ADR 0022 (consistency floor: overall lane, min core)](../../decisions/0022-consistency-floor-overall-lane-min-core.md) | Resolved | 2026-08-03 |
| R2 | Usability artifact-type claim | Resolved: narrow claim shipped as recommended (HTML/markdown UI specs, wireframe write-ups, page mockups; not live running applications), stated in `skills/critique-usability/SKILL.md`'s "Artifact claim" section and in `README.md`'s skill-catalog note, evidenced by S-05 AC-8 | Resolved | 2026-08-03 |
| R3 | Baseline model tiers to pin | Resolved: pinned to `claude-haiku-4-5-20251001` and `claude-sonnet-5`, formalized in [ADR 0023 (v0.1.0 measurement basis: two pinned tiers and k=5)](../../decisions/0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md) and applied throughout `bench/results/` | Resolved | 2026-08-03 |

### R1: Consistency floor value (Resolved)

**Summary.** The 0.7 Jaccard target is a placeholder; the stretch-skill gate needs a real number.

**Context.** No empirical data exists until P3. A pre-committed arbitrary floor would either block everything or gate nothing.

**Desired outcome.** A floor that is defensible in public ("stretch skills ship only if they are at least as consistent as the core skills we measured first").

**Recommendation.** Floor = min(core-skill consistency scores) measured in P3. Simple, honest, self-calibrating. Decided in-run, recorded as an ADR.

> **Maintainer decision:** Accepted as recommended. Floor set to **0.309** (overall lane cut, `critique-clarity` on `claude-haiku-4-5-20251001`), recorded in [ADR 0022 (consistency floor: overall lane, min core)](../../decisions/0022-consistency-floor-overall-lane-min-core.md).

---

## Notes

Publish boundary: the autonomous run never pushes, tags, or opens PRs. Everything outward-facing is staged as local artifacts (branch, drafted PR text) for human action.
