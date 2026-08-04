# P7 report: closure verification of the P6 pre-merge audit

**Pass:** P7, closure check on the fixes applied against P6's (pre-merge completeness critique's)
findings, run before a human merges `build/v0.1.0`, tags `v0.1.0`, and pushes.
**Date:** 2026-08-04.
**Branch:** `build/v0.1.0` (verified with `git branch --show-current`).
**Head at review time:** `d08b25b` ("P7 pre-tag: INDEX filter, node test spine, public roadmap,
release hygiene"), the fix commit this report verifies. Working tree clean before and after
(`git status --short`).
**Scope of writes:** this file only, plus one commit. No source file, generated file, or FROZEN
file was edited by this pass. A scratch verification (deliberately breaking a copy of
`scripts/lib/gen-index-filter.mjs` outside the repository, in the scratchpad directory, to confirm
its tests can fail) was run entirely outside this checkout and left no trace here.

## Summary

**All 3 hostile-reader points and all 8 must-know-before-tagging items from
[P6](P6-report.md) are closed, verified against primary sources rather than taken on the fix
commit's word.** The roadmap requirement (R1) is also satisfied. One nuance surfaced during
verification: fixing H1 (the INDEX.md phantom-path defect) correctly and predictably added a new,
documented, informational-only above-tier gate finding, so the above-tier count is now 5, not the
4 that P6 last measured and this task's brief still names. That fifth finding is explained in
detail in a new document the fix commit added, `docs/internal/upstream-gen-index-boilerplate.md`
(Finding 1b), is entirely expected as a direct consequence of the H1 fix, and does not affect the
declared-tier grade (`node scripts/check.mjs` still reports 0 errors and 0 warnings at Convergent
Silver). Everything else closes cleanly.

**Merge-ready: yes.**

## Verdict table

| ID | Item | Verdict | Evidence |
|---|---|---|---|
| H1 | INDEX.md asserts no non-existent paths | PASS | All 15 distinct paths INDEX.md links to (`README.md`, `AGENTS.md`, the six `skills/critique-*/` dirs, `agents/critique-critic.md`, `library.json`, `.claude-plugin/plugin.json`, `CHANGELOG.md`, `RELEASE-NOTES.md`, `docs/`, `docs/internal/decisions/`, `scripts/`) were enumerated by regex over `INDEX.md` and each tested with a shell existence check; all 15 exist. `node scripts/gen-index.mjs --check` also reports "INDEX.md matches library.json + component frontmatter." |
| H2 | `npm test` runs a nonzero number of real tests and can fail | PASS | `npm test` runs 37 tests (was 0), all passing. Read all 7 `scripts/tests/*.test.mjs` files: they spawn the real scripts as child processes against crafted fixtures and assert on real exit codes and stdout/stderr content (e.g. version-mismatch detection, missing-file detection, RELEASE-NOTES section extraction, phantom-link filtering), not tautologies. Proved they can actually fail: copied `scripts/lib/gen-index-filter.mjs` and its test file to an isolated scratch directory outside this repo, injected a deliberate bug (`dropPhantomRows` made a no-op passthrough), and reran `node --test`: 6 of 12 tests failed with real assertion diffs. Reverted by discarding the scratch copy (never touched the tracked file). |
| H3 | All five Mermaid diagrams have an "In text:" restatement immediately following the fence | PASS | Repo-wide `git grep -c '```mermaid'` finds exactly 5 fences across 4 files (`README.md` x2, `bench/README.md`, `docs/reference/critique-contract.md`, `examples/recipes/revision-loop.md`). Read the lines immediately after each closing fence: all five are followed (after one blank line, consistent with the other four) by a paragraph beginning "In text:". The previously-missing one, README's "How a critique runs" diagram, now has one at line 269. |
| M1 | No stale "12 issues" tier count in tracked files | PASS | `git grep -n "12 issues"` returns only historical execution reports (`P5-report.md`, `P6-report.md`) describing what used to be wrong, correctly framed as history, not a live claim. `CHANGELOG.md` lines 92-94 now read "`node scripts/check.mjs` reports tier Convergent, with 0 errors and 0 warnings at the declared tier" with no parenthetical count at all, the durable-claim fix P6 itself suggested. |
| M2 | CHANGELOG.md and RELEASE-NOTES.md 0.1.0 sections carry the same, current date | PASS | `CHANGELOG.md` line 8: `## [0.1.0] - 2026-08-03`. `RELEASE-NOTES.md` line 9: `## 0.1.0 - 2026-08-03`. Same date, and it matches the fix commit's own date (`git log -1 --format=%ci d08b25b` -> `2026-08-03 23:55:42 -0700`), a deliberate bump from the prior `2026-08-01`, not a silent divergence. |
| M3 | RELEASE_BODY.md is gitignored | PASS | `git check-ignore -v RELEASE_BODY.md` returns `.gitignore:35:RELEASE_BODY.md`, exit 0. |
| M4 | docs/internal/execution/RC-HANDOVER.md exists, is tracked, carries publish steps | PASS | `git ls-files docs/internal/execution/RC-HANDOVER.md` confirms it is tracked. Read the file: it has a "Publish steps" section with 5 numbered steps (review order, resolve before-tag items, merge, tag and push, marketplace re-pin). |
| M5 | Install-path honesty callouts present in README, QUICKSTART, RELEASE-NOTES | PASS | `README.md` line 74 ("Pre-release: none of the paths below resolve yet...") and the "At a glance" table line 420; `QUICKSTART.md` lines 10-14 (same pre-release callout); `RELEASE-NOTES.md` line 81 references "current pre-release status." All three name the private-repo, unpushed-main, unlisted-marketplace reasons plainly. |
| M6 | SECURITY.md and CONTRIBUTING.md carry pre-release notes | PASS | `SECURITY.md` lines 86-88: "Pre-release: both links below 404 today...". `CONTRIBUTING.md` lines 10-12: "Pre-release: opening a PR or issue against this repository does not work yet...". Both explain the private-repo reason and both name the workaround for someone with direct repo access. |
| M7 | README badge no longer claims plain "initial release" | PASS | `README.md` line 12's status badge now reads `status-pre--release` / alt text "Status: pre-release". `git grep -n "initial release" -- '*.md'` returns only the two historical execution reports (`P6-report.md`, `RC-HANDOVER.md`) describing the prior state, not a live claim. |
| M8 | Calibration before/after uses one metric level consistently and labels it, in both README and RELEASE-NOTES, verified against results.json | PASS | `README.md` line 215 now explicitly names both cuts: "location-level recall reads **0.988** on Haiku and **0.965** on Sonnet... Criterion-level recall... reads 0.976 on Haiku and 0.965 on Sonnet." `RELEASE-NOTES.md` uses "Location-level recall" consistently at lines 24 and 45 and never mixes in the criterion-level figure. Checked both figures against `bench/results/results.json`'s `entries` array for `critique-accessibility` 0.1.1: Haiku `recall.value = 0.976`, `recall_location.value = 0.988`; Sonnet `recall.value = recall_location.value = 0.965`. Both exact. Baseline figures (`0.376`/`0.776` recall_location, `0.258`/`0.293` precision_location) also checked exact against the `baseline-generic` entries. |
| R1 | ROADMAP.md exists, sequence-only with no dates, carries "deliberately not doing" and "known limitations" sections, linked from README | PASS | File exists, tracked (added in `d08b25b`). Regex scan for `YYYY-MM-DD`, month names, and `Q[1-4] YYYY` patterns over the file: zero matches. Contains `## Deliberately not doing` (4 bulleted scope exclusions: code review, auto-fix, taste-based criteria, unmeasurable skills) and `## Known limitations carried forward` (5 bullets). Linked from `README.md` twice: the documentation table (line 362) and the Project status section (line 405, "sequence-gated with no dates, is in `ROADMAP.md`"). |

## Above-tier gate issues: expected but recounted

The task brief (and P6, which it is drawn from) names "the four remaining above-tier gate issues"
as 3 upstream `__pycache__`/`SKIP_DIRS` findings plus 1 Gold architecture-doc pair finding. Running
`node scripts/check.mjs` now returns **5**, not 4:

```
[error] index-drift (G4): INDEX.md is out of date with library.json + component frontmatter ...
[error] folder-readme (G8): child "__pycache__" ... -> scripts/README.md
[error] folder-readme (G8): child "__pycache__" ... -> skills/_shared/README.md
[error] folder-readme (G8): meaningful folder has no README.md ... -> skills/__pycache__/README.md
[error] docs-presence (G10): the architecture pair is incomplete ... -> docs

Tier: Convergent (Advanced blocked: 5 issues)
0 error(s), 0 warning(s).
```

This is not a regression the fix commit introduced by accident; it is documented as a direct,
intended consequence of fixing H1. `docs/internal/upstream-gen-index-boilerplate.md` (new in
`d08b25b`) names it as "Finding 1b": the toolkit's own `index-drift` (G4) check diffs the on-disk
`INDEX.md` against the *raw*, unfiltered `renderIndex(ctx)` output, with no existence filtering of
its own. Before the local `dropPhantomRows()` fix, `INDEX.md` was exactly that raw boilerplate, so
`index-drift` passed. After the fix intentionally makes `INDEX.md` diverge from the raw boilerplate
(to stop asserting the seven phantom paths H1 found), `index-drift` reports drift, permanently,
until the fix lands upstream in `agent-skills-toolkit`'s own `gen-index` generator. The document
states this plainly: "a repo cannot both (a) stop asserting phantom paths in its own INDEX.md and
(b) satisfy G4's literal-boilerplate-reproduction check, without the fix in Finding 1 landing
upstream first."

So: the four issues P6 and the task brief expected are present and correctly explained (3
`__pycache__`/`SKIP_DIRS` findings traced to `agent-skills-toolkit/scripts/lib/fs-utils.mjs` line 14's
`SKIP_DIRS` set lacking Python cache directories; 1 Gold `docs-presence` finding for the
deliberately-out-of-scope architecture-overview/detailed doc pair). The fifth is new, was created by
this pass's own H1 fix, is fully documented at its point of origin, and is informational only: it is
Advanced/Gold tier, above this plugin's declared Convergent/Silver tier, and does not affect the
grade or exit code, which still reports 0 errors and 0 warnings. The upstream findings note
(`docs/internal/upstream-gen-index-boilerplate.md`) exists, is tracked
(`git ls-files` confirms), and covers both the `SKIP_DIRS` gap (Finding 2) and the `index-drift`
consequence (Finding 1b) with suggested upstream fixes for each, per the wrap-do-not-vendor rule
(ADR 0011, gate wiring as a toolkit wrapper).

**Verdict on this item: PASS, with the count corrected from 4 to 5 and the fifth explained.** The
substance the brief cares about (the issues are the expected, understood, non-blocking, upstream-
attributable kind, and a findings note exists) holds; only the raw number changed, and it changed
for a reason directly tied to closing H1.

## Other checks run this pass

- `python -m pytest -q`: **784 passed** in 9.46s, matching the unchanged `Tests: 784` badge in
  `README.md`.
- `npm run validate:envelopes`: **502 file(s) valid**.
- `node scripts/check-release-versions.mjs v0.1.0`: **passed**; `package.json`, `library.json`,
  `.claude-plugin/plugin.json` all agree at `0.1.0`.
- `node scripts/gen-readme-catalog.mjs --check`, `node scripts/gen-plugin-manifest.mjs --check`,
  `node scripts/gen-index.mjs --check`: all **match**, including confirmation that
  `AGENTS.md` documents all 7 `ci.yml` commands.
- Dash sweep: scanned every tracked file's bytes for U+2014 and U+2013 (not a text-tool grep, a
  direct codepoint scan in Node): **zero** across 1,100+ tracked files, including the two files new
  in this pass (`ROADMAP.md`, `docs/internal/upstream-gen-index-boilerplate.md`).
- FROZEN files: `git show d08b25b --stat` confirms `contract/critique-contract.schema.json`,
  `docs/explanation/methodology.md`, and no `bench/results/runs*/` path appear in the fix commit's
  changed-file list. Untouched.
- `docs/internal/release-plans/plan_v0.1.0/plan_v0.1.0.md`'s Open Questions table: R1, R2, R3 (a
  different R1-R3 than this report's own R1 roadmap item, both named as-is by the task brief and the
  plan doc respectively) now all read `Resolved`, dated `2026-08-03`, matching the commit message's
  claim of "resolution of release-plan open questions R1-R3."
- AGENTS.md's CI job table and its `unit-node` paragraph were checked, not just the code: line 82
  still reads `unit-node | npm test`, and lines 88-93 now correctly state `unit-node` is not on the
  vacuous-pass list and name what `scripts/tests/*.test.mjs` covers, matching the real inventory in
  `scripts/tests/README.md`.

## Non-blocking observation (outside the assigned checklist)

`CHANGELOG.md`'s `### Added` section was not extended to mention the fix commit's new
`docs/internal/upstream-gen-index-boilerplate.md`, `scripts/lib/gen-index-filter.mjs`, or
`scripts/tests/*.mjs`, even though `INDEX.md` describes `CHANGELOG.md` as "full technical history."
`CHANGELOG.md`'s only edits in `d08b25b` were the date bump (M2) and the stale-count removal (M1).
This is not one of the checklist items above and does not block merge; noted for completeness only.

## Still open

None of the 3 hostile-reader points, 8 must-know items, or the roadmap item remain open. Nothing
from this pass's scope requires further work before tagging.

Carried forward from P6 as v0.1.x / v0.2 scope, unchanged and out of this pass's scope (already
tracked in `ROADMAP.md`'s "Next: v0.1.x" section and `RC-HANDOVER.md`'s "Carry to v0.1.x" /
"Carry to v0.2" lists): the two never-run external validators (`plugin-dev:plugin-validator`,
`plugin-dev:skill-reviewer`), CI runtime measurement on GitHub-hosted runners (impossible before
first push), the `.gitattributes` CRLF-protection gap beyond `bench/corpus/**`, and the golden-
envelope run-metadata labeling question.

## Merge-readiness statement

**Merge-ready.** Every hostile-reader point and every must-know-before-tagging item named in P6
closes under independent verification against primary sources: files read directly, commands run
fresh in this pass, one filter module's test coverage proven capable of failure by deliberately
breaking a scratch copy of it. The one place reality diverged from the task brief's expectation,
the above-tier gate issue count moving from 4 to 5, is a correctly-documented, non-blocking, and
entirely explained side effect of closing H1 (the INDEX.md phantom-path fix), not an unaddressed
defect. The declared-tier grade remains 0 errors and 0 warnings at Convergent (Silver), the full
784-test Python suite and the new 37-test Node suite both pass, all 502 run envelopes validate, and
the release version guard agrees across all three manifests. Nothing in this repository's own
tooling contradicts a claim it makes about itself, which was P6's central complaint. `build/v0.1.0`
is ready to merge and tag.
