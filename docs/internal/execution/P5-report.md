# P5 release-prep finalization report

- Phase: P5 (release prep and RC handover: apply the completeness critic's fix-now findings,
  run the full deterministic suite, commit)
- Branch: `build/v0.1.0`
- Commits this pass: `a608daa` ("P5 release prep: changelog, notes, versions, hygiene"), plus
  this report's own commit
- Date: 2026-08-01
- Author: P5 finalizer pass (Claude)

## Purpose

This pass started from a working tree that already held an uncommitted release-packaging draft
(CHANGELOG promotion, RELEASE-NOTES curation, all eight release-plan specs and `plan_v0.1.0.md`'s
gate table brought current, one new ADR) plus a fix-now list of eight defects a completeness
critic found in that draft's own claims. This report records what this pass verified, what it
fixed, what it could not verify because the input was incomplete, and the consolidated open items
for the eventual `rc-handover.md`.

## Packaging summary (inherited draft, verified this pass)

- `CHANGELOG.md`: `[Unreleased]` promoted to a dated `0.1.0` section covering the repo scaffold,
  the Critique Contract, the bench harness, the six skills, the `critique-critic` subagent, the CI
  pipeline, the v0.1.0 measurement, documentation, and 29 ADRs, plus `Changed`/`Fixed` entries for
  location-level rescoring, the `critique-accessibility` 0.1.1 calibration, and the methodology
  survey-claim correction.
- `RELEASE-NOTES.md`: curated per-skill highlights, a "calibration story" section, and a "known
  limitations" section. Its per-skill framing for `critique-usability` and `critique-docs` was
  already correct (narrow/partial wins, not blanket "beats baseline on both tiers"); this pass
  copied that framing into `CHANGELOG.md` and the plan's gate (g) row, which had drifted from it
  (fix-now items 1 and 2).
- Eight release-plan specs (`S-01` through `S-08`) and `plan_v0.1.0.md`: status, AC checkboxes, and
  the Hygiene Gates / release-specific gates tables brought current against
  `docs/internal/execution/` reports.
- New ADR: `docs/internal/decisions/0029-methodology-survey-claim-correction.md`, correcting an
  unverified "40-candidate, 13-domain survey" claim in `docs/explanation/methodology.md`.
- Version consistency re-confirmed this pass: `GITHUB_REF_NAME=v0.1.0 node
  scripts/check-release-versions.mjs` reports `package.json`, `library.json`, and
  `.claude-plugin/plugin.json` all at `0.1.0`.

## External-validator findings and dispositions

This finalizer pass was not given the raw output of the two external validators the release plan
names for the B5 phase (`plugin-dev:plugin-validator`, `plugin-dev:skill-reviewer`; see
`docs/internal/release-plans/plan_v0.1.0/implementation/IMPL-B-skills-to-rc.md`, row B5). No
corresponding report exists under `docs/internal/execution/` or `_local/`. The only in-repo
automated proxy available to this pass is the family conformance gate, re-run and confirmed this
pass:

`node scripts/check.mjs` -> Tier: Convergent (Advanced blocked: 12 issues); **0 error(s), 0
warning(s)**. All 12 blocked-tier issues print as "above your declared tier (informational)" per
the gate's own output (missing per-folder READMEs for `agents/`, `.github/workflows/`, each
`skills/*/` directory, and `skills/__pycache__/`; two under-listed `__pycache__` children; one
incomplete architecture-doc pair) and none affect the exit code or the Convergent-tier PASS.

**Disposition:** recorded as an open item below, not fabricated or assumed clean. The release owner
should confirm whether `plugin-validator` and `skill-reviewer` ran anywhere in this build and, if
so, locate their output before tagging.

## Completeness-critic verdicts

### What this pass received

A fix-now list of eight items, each anchored to specific lines in `CHANGELOG.md`,
`plan_v0.1.0.md`, `README.md`, and `bench/README.md`. No separate open-items list or narrative
verdict document from the critic was included in what this pass received, and item 8's own text
arrived truncated mid-sentence ("...does not exist. Envelop"). This pass reconstructed the correct
fix for item 8 by reading the actual `bench/results/` directory layout on disk and
`bench/results/README.md`'s own already-documented "Path drift in the generated block" known
issue, verified the fix against a real, passing scoring command, and applied it. The truncation
itself is carried forward as an open item: it is possible the critic's original item 8 named a
different or additional correction that did not survive transcription.

### AC table

From each spec's own Task Summary (`- AC: [x]/[ ] ...` checkboxes), unchanged by this pass except
where a fix-now item closed a gap the checkbox already claimed was closed (see the S-05 note
below).

| Spec | Status | AC checked | AC unevidenced / deferred |
|---|---|---|---|
| S-01 repo scaffold | fulfilled | 7/7 | none |
| S-02 critique contract | fulfilled | 8/8 | none |
| S-03 bench harness | committed | 7/8 | AC-3 (corpus-size verdict never explicitly re-stated by a report, though `P2-report.md`'s counts clear the stated targets) |
| S-04 skill template | committed | 1/7 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-7 (shipped in P2, never separately verdicted per criterion) |
| S-05 skills slate | fulfilled | 8/8 | none as checked; see note below on AC-8 |
| S-06 critic subagent | fulfilled | 5/5 | none |
| S-07 CI pipeline | committed | 3/6 | AC-1, AC-4 (local replay only, not the live-Actions scenario the criterion names), AC-6 (CI runtime never measured) |
| S-08 docs and packaging | committed | 5/7 | AC-6 (version consistency verified this pass, not by a prior execution report), AC-7 (`rc-handover.md` does not exist) |

**Note on S-05 AC-8.** Marked PASS, evidenced by `P2-report.md`, requiring "critique-usability's
SKILL.md and README entry state the narrow artifact claim explicitly." Before this pass, the
README catalog entry did not carry that clause: `scripts/gen-readme-catalog.mjs` truncates the
frontmatter description at `" Use when..."`, which is exactly where the clause sits in
`skills/critique-usability/SKILL.md`. Fix-now item 6 closed this by adding the sentence outside the
generated markers. `S-05/spec.md` was not re-edited to cite this pass's fix (out of this pass's
given scope); see Open Items.

### Gates

From `plan_v0.1.0.md`, "Hygiene Gates" and "Release-specific gates", re-verified this pass.

| Gate | Status |
|---|---|
| (a) Spec status | PASS |
| (b) Coupled plan | PASS |
| (c) AC coverage | PASS |
| (d) Phases done | PARTIAL as of the packaging draft (no committed P5 execution report existed); this report closes that gap |
| (e) Staleness | FAIL, administratively (spec `updated` dates postdate the two implementation plans'; hygiene bookkeeping only, no requirement/AC/scope change) |
| (f) Conformance | PASS (0 errors, 0 warnings; re-confirmed this pass) |
| (g) Measurement | PASS, corrected this pass (fix-now items 1 and 2): no longer claims all three core skills or all three stretch skills beat baseline on both pinned tiers; the envelope count now separates the 460 scored grid envelopes from the 2 excluded steering-probe envelopes |
| (h) Stretch gating | PASS |
| (i) Honesty sweep | PASS, corrected this pass (fix-now item 3): the cited drift command is now the runnable form, and the codepoint scan claim is now scoped to the 1,058 tracked files it actually verified, not "1,059 tracked and untracked" |

### Hostile-reader points

The specific falsifiable claims the critic caught, as received in the fix-now list:

1. `CHANGELOG.md`'s "all three core skills beat baseline ... both pinned tiers" was contradicted
   by `bench/results/README.md` itself: `critique-usability`/sonnet precision 0.169 against the
   baseline's 0.181 ("no pass on this tier"), and `critique-docs` ties baseline recall on both
   tiers (0.933/0.933, 1.000/1.000). `RELEASE-NOTES.md` already had the correct framing.
2. `plan_v0.1.0.md` gate (g) repeated the same false claim, plus counted 462 `p3-2026-07-31`
   envelopes as if all 462 were in the scored grid, when 460 are scored and 2 are excluded
   steering probes.
3. `plan_v0.1.0.md` gate (i) cited a drift command that does not run
   (`python -m bench.report table --check` errors, missing required `--results`) and a codepoint
   scan claim of "1,059 tracked and untracked files" that the critic's own re-scan (1,090 files, 36
   dash-bearing lines, all inside gitignored `_local/`/`.memsearch/`) found imprecise; the
   tracked-only claim (1,058 files, zero hits) is the one that survives and is the one that
   matters.
4. `README.md`'s provenance sentence named only `bench/results/runs/`, but the release's headline
   `critique-accessibility` 0.1.1 numbers trace to `bench/results/runs-cal1/`.
5. `README.md`'s "the lowest number in the whole published run set is 0.309" is falsifiable from
   the README's own tables: lower precision, recall, and consistency figures exist elsewhere for
   other skills, other lanes, and the baseline.
6. `README.md` never stated `critique-usability`'s narrow "static specs and mockups, not live
   running applications" claim, though `SKILL.md` carries it twice and S-05 AC-8 requires it in
   both places; the skill-catalog generator truncates the frontmatter description before that
   clause.
7. `bench/README.md`'s corpus counts disagreed with each other and with disk: prose said 21
   scored artifacts, the table summed to 22, and disk holds 23 (`docs` row understated at 3
   manifests instead of 4).
8. `bench/README.md`'s Layout section and two reproduction command blocks documented a
   `results/<run-set>/*.json` / `results/<run-set>/results.json` convention that was never built;
   the actual layout is `results/runs/`, `results/runs-cal1/`, and a single committed
   `results/results.json`.

## Fix-now items applied

All eight items were tractable within this pass; none were demoted to open items.

| # | Location | Was wrong | Fixed to | Verified |
|---|---|---|---|---|
| 1 | `CHANGELOG.md` (v0.1.0 measurement bullet) | Claimed all three core skills beat baseline on recall at equal-or-better precision on both pinned tiers | Names which two core skills do (`critique-accessibility` 0.1.1, `critique-clarity`), that `critique-usability` only does on Haiku, and that `critique-docs` ships on precision dominance at equal recall rather than a recall win | Text now matches `bench/results/README.md`'s own location-level table and `RELEASE-NOTES.md`'s framing |
| 2 | `plan_v0.1.0.md` gate (g) | Same false "both pinned tiers" claim; "462 `p3-2026-07-31` envelopes" implied all 462 were scored | Same correction as item 1; envelope count now reads "460 scored grid envelopes plus 2 steering probe envelopes (462 JSON files under `bench/results/runs/`)" | Matches `bench/results/README.md`'s "460 of 460... Zero quarantined" and "462 of 462 files on disk validate" distinction |
| 3 | `plan_v0.1.0.md` gate (i) | Cited a non-runnable drift command; claimed "1,059 tracked and untracked" files scanned | Command corrected to `python -m bench.report table --results bench/results/results.json --check`; scan claim scoped to "1,058 tracked" files | Ran the corrected command (`no drift`); ran an independent tracked-file-only scan (`git ls-files`, 1,058 files, zero U+2014/U+2013) |
| 4 | `README.md` line 93 | "Every number above traces to a committed run envelope under `bench/results/runs/`" omits `runs-cal1/` | Names both directories: `bench/results/runs*/`, `runs/` for the scored grid and steering probes, `runs-cal1/` for the accessibility 0.1.1 calibration | Confirmed `bench/results/runs-cal1/critique-accessibility/` holds the 0.1.1 envelopes cited in the table above it |
| 5 | `README.md` lines 123-125 | "The lowest number in the whole published run set is... 0.309" | Reworded to "the lowest consistency among the shipped core skills", with a pointer to `bench/results/README.md` for lower numbers elsewhere | Cross-checked against `bench/results/README.md`'s worst-number list (precision 0.155/0.169/0.198, judged-lane recall 0.130, judged-only consistency 0.090, baseline consistency 0.032); 0.309 remains true as "lowest core-skill consistency" per ADR 0022 |
| 6 | `README.md`, near the skill-catalog block | Catalog table omits `critique-usability`'s narrow artifact claim | Added a sentence outside the `<!-- skill-catalog:start/end -->` markers stating the "static specs and mockups, not live running applications" claim | `node scripts/gen-readme-catalog.mjs --check` still reports no drift (sentence sits outside the generated region); satisfies S-05 AC-8's README requirement |
| 7 | `bench/README.md` line 39 and corpus table | Prose said 21 scored artifacts, table summed to 22, disk holds 23; `docs` row said 3 | Prose corrected to 23; `docs` row corrected to 4 | Counted manifests on disk (`bench/corpus/*/​*.manifest.json`): clarity 4, accessibility 4, usability 4, docs 4, microcopy 4, argument 3 = 23 |
| 8 | `bench/README.md` lines 25-31 and reproduction commands at (then) 426-428 and 529-532 | Documented a `results/<run-set>/*.json` / `results/<run-set>/results.json` layout that does not exist on disk | Layout block rewritten to the real `runs/`, `runs-cal1/`, `results.json` structure; both command blocks corrected to real, runnable paths, with a pointer to `bench/results/README.md`'s "Reproduction" section for the full per-run-set recipe | Ran the corrected example command (`python -m bench.metrics score --corpus bench/corpus --runs bench/results/runs-cal1 --out ... --run-set cal1-2026-08-01`) and the corrected check command (`python -m bench.report table --results bench/results/results.json --check`); both succeed |

## Suite outputs

All commands run from `E:/Projects/product-on-purpose/critique-skills` on branch `build/v0.1.0`
after the fixes above, before committing.

| Command | Result |
|---|---|
| `python -m pytest -q` | **771 passed** |
| `node scripts/check.mjs` | **0 error(s), 0 warning(s)** (Tier: Convergent; 12 informational above-tier notes, do not affect exit code) |
| `python -m bench.report table --results bench/results/results.json --check` | **no drift** |
| `node scripts/gen-readme-catalog.mjs --check` | **matches library.json + SKILL.md frontmatter** |
| `node scripts/gen-index.mjs --check` | **matches library.json + component frontmatter** |
| `node scripts/gen-plugin-manifest.mjs --check` (aggregate) | **matches library.json; AGENTS.md documents all 7 ci.yml commands** |
| `python -m contract.validate_envelopes` | **502 file(s) valid** |
| `GITHUB_REF_NAME=v0.1.0 node scripts/check-release-versions.mjs` | **version guard passed**: `package.json`, `library.json`, `.claude-plugin/plugin.json` all `0.1.0` |
| `node scripts/extract-release-notes.mjs v0.1.0` | **wrote 65 line(s) for 0.1.0** to `RELEASE_BODY.md` (deleted after verification; this is a release-time CI artifact, not a committed file, and is not referenced anywhere as one) |
| Tracked-file codepoint scan (independent of gate (i)'s own command) | **1,058 tracked files, zero U+2014/U+2013** |

All required checks pass. `node --test` was also run for completeness (not part of the specified
suite): 0 tests found, no `*.test.mjs`/`*.test.js` files exist in the repo, which is the expected,
pre-existing state, not a regression from this pass.

## Open items

Carried forward for `rc-handover.md`. None of these were fixed by this pass; per this pass's
instructions, open items are reported, not resolved. Grouped by source.

**Gaps in what this pass received:**

- The fix-now list's item 8 arrived truncated mid-sentence. This pass reconstructed and verified a
  correction from the actual repository state, but the critic's original wording for item 8, and
  whether it specified something beyond what this pass inferred, could not be confirmed.
- No separate open-items list or narrative verdict document from the completeness critic was
  included in what this pass received, only the eight-item fix-now list. If the critic produced a
  fuller report, it was not passed through to this pass.
- No external-validator (`plugin-dev:plugin-validator`, `plugin-dev:skill-reviewer`) output was
  available to this pass, though the release plan's B5 phase row names both. `node scripts/check.mjs`
  is the closest in-repo automated proxy and passes (0 errors, 0 warnings), but it is not a
  substitute for those two named validators.

**Already-recorded gaps this pass re-confirmed rather than closed (all pre-existing, out of this
pass's given scope):**

- S-03 AC-3, S-04 AC-1/2/3/4/5/7, S-07 AC-1/4/6, S-08 AC-6/7: unevidenced or deferred per each
  spec's own Task Summary (see AC table above). S-07 AC-6 in particular means CI runtime on
  GitHub-hosted runners has never been measured.
- Gate (e) (staleness): FAIL, administratively. The two implementation plans'
  (`IMPL-A-foundation.md`, `IMPL-B-skills-to-rc.md`) `updated` field still reads `2026-07-31`
  against the specs' `2026-08-01`; a future pass can bump them to close this without touching
  scope.
- `plan_v0.1.0.md`'s Open Questions table still marks R1 (consistency floor), R2 (usability
  artifact-type claim), and R3 (baseline model tiers) as `Open`, even though all three are
  functionally settled elsewhere (R1: ADR 0022 sets the floor at 0.309; R2: `SKILL.md`'s narrow
  claim, now also in `README.md` per fix-now item 6; R3: both tiers pinned and used throughout
  `bench/results/`). The table's `Status` column was not updated by this pass.
- `rc-handover.md` does not exist anywhere in the repository (S-08 AC-7). The Doc-Update Checklist
  in `plan_v0.1.0.md` still shows the git-tag and `agent-plugins` registry rows unchecked, both
  marked "(human)".
- `S-05/spec.md`'s AC-8 evidence citation still points only to `P2-report.md`; it was not updated
  to also cite this pass's README fix (fix-now item 6), even though that fix is what makes the
  AC-8 checkbox now literally true.
- `bench/results/README.md`'s own "Known issues in the measurement tooling" section: `results.json`
  cannot say which run set an individual entry came from (a schema limitation, already flagged as
  a v0.2 item), and scoring `bench/results/runs` directly (without excluding `runs/steering/`)
  silently changes the `critique-clarity`/sonnet numbers, a documented but still-fragile gotcha in
  the reproduction recipe.
- No human acceptance data exists yet (disposition-based acceptance rate is a stated v0.2 measure,
  per `RELEASE-NOTES.md`'s "Known limitations").

## Recommendation

Suite is green, all eight fix-now items are applied and verified, and the packaging draft plus
this report are committed to `build/v0.1.0`. Per the autonomous-run publish boundary, this pass did
not tag, push, or open a PR. Handing over to the release owner for RC review; the open items above,
especially the missing external-validator output and the truncated fix-now item 8, are worth a
direct look before tagging `v0.1.0`.

## Remediation addendum (2026-08-01)

A follow-on critic pass, working from this report, found two more issues in the packaging draft
this report had signed off on plus two hygiene gaps outside it. A remediation pass fixed all four
and this addendum records what closed and what is still open, so a single section can be cited by
`rc-handover.md` instead of two more reports.

### What the critic found and what closed

1. **Front page led with a structurally rigged comparison.** The criterion-level baseline
   comparison table pinned `baseline-generic` at 0.000 recall/precision by construction (it has no
   rubric to cite a criterion under, so it can never match a planted defect at that level), which
   made every "beats baseline" verdict at that level true regardless of measurement, and it ran
   *before* the one comparison in the file the baseline could actually lose. Worse, the
   location-level table's verdict was recall-only: `critique-usability`/sonnet read "beats
   baseline" on 0.857 recall against the baseline's 0.829 while quietly losing precision, 0.169
   against 0.181.
   **Fixed:** `bench/report.py` reordered the front page to lead with the fair, location-level
   table; the criterion-level table is retitled "Rubric operationalization (criterion-level)",
   drops the baseline and verdict columns entirely (a caption explains why, rather than showing a
   comparison that cannot lose), and moves after the full per-run entries table. A new
   `_dominance_verdict` checks recall *and* precision, so `critique-usability`/sonnet now reads
   `no pass on this tier (qualifies via haiku)`, generically computed by looking at the same
   skill+version+domain's other pinned tier, not hardcoded to this one case. `README.md` and
   `bench/README.md` were regenerated from the changed generator, never hand-edited; both pass
   `python -m bench.report table --check` with no drift. 9 tests in `bench/tests/test_report.py`
   rewritten or added to cover the new verdict logic, the dropped columns, and the front-page
   ordering; `python -m pytest bench/tests/test_report.py` is 19 passed.
2. **The "lowest number" sentence was hedged but unfalsifiable.** `README.md` named 0.309 as a
   floor while parenthetically admitting lower numbers existed elsewhere "for other metrics and for
   the baseline" without ever naming them, which does not survive a one-click check.
   **Fixed:** the sentence now names 0.309 explicitly as the consistency floor (cited to
   `docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md`) and states plainly
   that it is not the lowest published number, then names three verified lower ones by category:
   precision 0.155 (`critique-accessibility` 0.1.0/Sonnet, present in the criterion-level table on
   the same page), judged-lane recall 0.130 and judged-lane consistency 0.150 (both
   `critique-clarity`/Haiku, verified against `bench/results/README.md` lines 284 and 242 where the
   source document states them directly), with a pointer to `bench/results/README.md` for the full
   account.
3. **`checks.py` heading-skip fix string named the wrong target level.** `_check_structure`'s
   detection loop and its separate reporting loop both used variables named `prev_level`/`cur_level`;
   Python loop variables leak, so the reporting loop silently reused whatever pair the detection loop
   had examined *last*, not the skip pair actually being reported. On the real corpus artifact
   (`bench/corpus/accessibility/accessibility-001.html`) this produced `<h5>` for an h2-to-h4 skip
   where `<h3>` is correct; a synthetic 3-heading test case had masked the bug because its skip pair
   happened to also be the last pair scanned.
   **Fixed:** `prev_level` is now recomputed from the skip pair's own `prev` node inside the
   reporting loop (`checks.py`, `_check_structure`). Two regression tests added
   (`test_heading_skip_fix_recommends_next_sequential_level`,
   `test_multiple_heading_skips_each_recommend_their_own_prev_level`);
   `python -m pytest skills/critique-accessibility` is 101 passed, `python
   scripts/skill-selftest.py skills/critique-accessibility` is 0 errors/0 warnings, and re-running
   `checks.py` against `accessibility-001.html` now emits `<h3>`, matching `golden-02.json`'s
   pre-existing expectation. No envelope under `bench/results/runs*/` was touched (the historical
   `runs-cal1/critique-accessibility/.../haiku-r5.json` envelope, which already happened to read
   `<h3>`, stays exactly as produced; every sibling envelope in `runs/` and `runs-cal1/` still reads
   the pre-fix `<h5>`). `bench/results/README.md`'s existing disclosure of this discrepancy now has
   an added paragraph explaining the root cause and that it is fixed going forward in 0.1.1 code
   without touching the frozen historical envelopes.
4. **QUICKSTART.md's install path silently assumed a repo checkout.** Step 4 runs `python -m
   contract.validate disposition.json`, which depends on `jsonschema`; the plugin-install path
   (`/plugin install critique-skills@product-on-purpose`) sets up the skill only, not a Python
   environment, and the walkthrough never named the dependency or distinguished the two install
   paths' different working-directory assumptions.
   **Fixed:** `QUICKSTART.md` now documents both install paths (plugin vs. repo checkout) with
   path-relative guidance for each, and names `jsonschema` as the one prerequisite either way with
   `pip install "jsonschema>=4.20,<5"`.

A related but separate finding surfaced while auditing item 3 above's neighborhood: `S-04`
(skill-template)'s Task Summary had six of seven ACs marked unchecked with "not evidenced" notes
even though the template and toy skill had shipped in P2. A fresh per-criterion audit this pass
found AC-1, AC-2, AC-4, AC-5, AC-6, AC-7 all genuinely PASS (each independently re-verified: the
template guide's coverage read directly, the five AC-2 failure-mode tests run by name, `--gate`
exit codes checked against two real skills, golden/anti-example shape spot-checked,
paraphrase-policy tests run by name). **AC-3 is a real FAIL, not a documentation gap**: nothing in
`.github/workflows/ci.yml` or any test module runs `skill-selftest.py` against the real
`skills/critique-*` directories in CI; the only place all six skills were ever swept with it is a
one-time manual audit recorded in `P2-report.md`, which is not CI. `S-04_skill-template/spec.md`
now records this per-criterion breakdown (6 PASS, 1 FAIL, named). `IMPL-A-foundation.md` and
`IMPL-B-skills-to-rc.md` were updated from `status: draft` to `status: executed` with phase
checkboxes and evidence pointers, which also closes gate (e) (staleness) in `plan_v0.1.0.md` from
FAIL to PASS (the two implementation plans' `updated` field now matches the specs' `2026-08-01`,
closing the exact gap this report's own Open Items section named above under "Already-recorded
gaps").

### Suite outputs, re-run after the remediation pass

| Command | Result |
|---|---|
| `python -m pytest -q` | **777 passed** (up from this report's own 771; net +6 from 2 new accessibility regression tests plus net new tests in `bench/tests/test_report.py`) |
| `node scripts/check.mjs` | **0 error(s), 0 warning(s)** (same 12 above-tier informational notes as this report recorded) |
| `python -m bench.report table --results bench/results/results.json --target README.md --check` | **no drift** |
| `python -m bench.report table --results bench/results/results.json --target bench/README.md --check` | **no drift** |
| `node scripts/gen-plugin-manifest.mjs --check` | **matches library.json; AGENTS.md documents all 7 ci.yml commands** |
| `node scripts/gen-index.mjs --check` | **matches library.json + component frontmatter** |
| `node scripts/gen-readme-catalog.mjs --check` | **matches library.json + SKILL.md frontmatter** |
| `python -m contract.validate_envelopes` | **502 file(s) valid** |
| `GITHUB_REF_NAME=v0.1.0 node scripts/check-release-versions.mjs` | **version guard passed**: all three manifests at `0.1.0` |
| `node scripts/extract-release-notes.mjs v0.1.0` | **wrote 65 line(s)** to `RELEASE_BODY.md` (deleted after verification, same as this report's own run) |
| Codepoint scan of every file this pass touched | **zero U+2014/U+2013** |

No envelope under `bench/results/runs*/` and no line of `bench/results/results.json` was touched;
confirmed via `git diff` showing no changes to those paths.

### Open items (carried forward verbatim from this report's own list, still open)

None of the items below were in scope for or touched by this remediation pass; they are repeated
here unedited so `rc-handover.md` has one place to read the full open-items list rather than two
reports.

- The fix-now list's item 8 arrived truncated mid-sentence. This pass reconstructed and verified a
  correction from the actual repository state, but the critic's original wording for item 8, and
  whether it specified something beyond what this pass inferred, could not be confirmed.
- No separate open-items list or narrative verdict document from the completeness critic was
  included in what this pass received, only the eight-item fix-now list. If the critic produced a
  fuller report, it was not passed through to this pass.
- No external-validator (`plugin-dev:plugin-validator`, `plugin-dev:skill-reviewer`) output was
  available to this pass, though the release plan's B5 phase row names both. `node scripts/check.mjs`
  is the closest in-repo automated proxy and passes (0 errors, 0 warnings), but it is not a
  substitute for those two named validators.
- S-03 AC-3, S-04 AC-1/2/4/5/6/7 are now individually evidenced PASS (closed by this addendum's
  S-04 audit, above); S-04 AC-3 is now a confirmed FAIL, not merely unevidenced (also closed to a
  verdict by this addendum). S-07 AC-1/4/6, S-08 AC-6/7 remain unevidenced or deferred per each
  spec's own Task Summary. S-07 AC-6 in particular means CI runtime on GitHub-hosted runners has
  never been measured.
- Gate (e) (staleness) is now PASS, not FAIL: this addendum's `IMPL-A-foundation.md` /
  `IMPL-B-skills-to-rc.md` update closed the exact gap named here (their `updated` field now reads
  `2026-08-01`, matching the specs).
- `plan_v0.1.0.md`'s Open Questions table still marks R1 (consistency floor), R2 (usability
  artifact-type claim), and R3 (baseline model tiers) as `Open`, even though all three are
  functionally settled elsewhere (R1: ADR 0022 sets the floor at 0.309; R2: `SKILL.md`'s narrow
  claim, also in `README.md` per fix-now item 6; R3: both tiers pinned and used throughout
  `bench/results/`). The table's `Status` column was not updated by this pass.
- `rc-handover.md` does not exist anywhere in the repository (S-08 AC-7). The Doc-Update Checklist
  in `plan_v0.1.0.md` still shows the git-tag and `agent-plugins` registry rows unchecked, both
  marked "(human)".
- `S-05/spec.md`'s AC-8 evidence citation still points only to `P2-report.md`; it was not updated
  to also cite this report's README fix (fix-now item 6), even though that fix is what makes the
  AC-8 checkbox now literally true.
- `bench/results/README.md`'s own "Known issues in the measurement tooling" section: `results.json`
  cannot say which run set an individual entry came from (a schema limitation, already flagged as
  a v0.2 item), and scoring `bench/results/runs` directly (without excluding `runs/steering/`)
  silently changes the `critique-clarity`/sonnet numbers, a documented but still-fragile gotcha in
  the reproduction recipe.
- No human acceptance data exists yet (disposition-based acceptance rate is a stated v0.2 measure,
  per `RELEASE-NOTES.md`'s "Known limitations").

### Recommendation

All four remediation items verified fixed; the S-04 AC-3 FAIL is now an honestly recorded gap
rather than a silent "not evidenced" checkbox. Suite is green (777 passed, 502 envelopes valid, all
generator `--check` commands clean, version guard passed). Still worth a direct look before tagging
`v0.1.0`: the missing external-validator output, the truncated fix-now item 8, S-07 AC-6 (CI
runtime never measured), S-04 AC-3 (skill-template conformance not actually run in CI), and the
absent `rc-handover.md`.
