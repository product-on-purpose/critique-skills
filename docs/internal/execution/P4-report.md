# P4 integration and audit report

- Phase: P4 (integrator and auditor pass: land the remaining P4 docs work, fix what the phase's
  five verification reports found fixable, run the full deterministic suite, commit, then audit)
- Branch: `build/v0.1.0`
- Commits this pass: `1b7beb3` ("P4 docs: README, QUICKSTART, how-tos, INDEX, frontmatter")
- Prior P4-labeled work, not re-committed here per instruction: `8b41fdc` ("P4 integrity: fair
  baseline scoring, reproduction harness, provenance, verdict re-examination") and `246a2a4`
  ("P3-cal1: accessibility calibration, re-measurement, final verdict")
- Date: 2026-08-01
- Author: P4 integrator-and-audit pass (Claude)

## Purpose

Five verification reports landed for this phase: a cold-read of the README (COLD-READER), a
step-by-step QUICKSTART execution (QUICKSTART-EXEC), a four-part sweep for dashes, claim
traceability, survey-claim leakage, and generated-block drift (SWEEPS), a local re-run of every
planted CI failure (CI-PLANTED), and a line-by-line review of the ship verdicts (VERDICT-REVIEW).
This report integrates their fixable findings, commits the remaining P4 docs work, runs the full
deterministic suite, and audits the result against the criteria the launching agent specified.

## 1. What was fixed, and why

**COLD-READER's two weak spots, both fixed in `README.md` (this commit).**

- **Q2, evidence sourcing.** The cold reader found the pointers to `bench/results/README.md` and
  `bench/results/verdicts.md` only at the tail of the Results section (former lines 89-92), so a
  first-time reader had to reach the end before learning `bench/results/` holds more than the raw
  envelopes. Fixed by front-loading the same pointer into the section's opening paragraph: it now
  names all three things `bench/results/` holds (raw envelopes, the narrative README, the verdicts
  doc) in the first paragraph a reader hits, ahead of the generated table. The closing pointer at
  the old location was left in place as reinforcement, not removed.
- **Q4, the thinking-framework-skills boundary.** The cold reader called the boundary section
  (former lines 188-209) dense and something that "requires parsing" before the hard test becomes
  clear. Fixed by adding a bolded one-line TL;DR immediately under the heading, stating the yes/no
  test before the supporting paragraph and the five-row worked-example table that follow it.

I could not re-run an independent, fresh-context 90-second cold read myself: I am not a fresh
reader of this repository at this point in the session, and no subagent-spawning tool was
available to me in this pass. What I did verify directly is that both specific complaints are
textually resolved at the location the cold reader named (see `README.md` lines 6-15 and 192-200).
Treat `S08-AC1` below as "the named defects were fixed and confirmed present at the fix site," not
as an independent re-pass of the 90-second test.

**QUICKSTART-EXEC: no fix needed.** All four steps passed (install correctly skipped, marketplace
unpublished); no residue (`disposition.json`) was left in the repo root; confirmed absent.

**SWEEPS: three of four passed; the fourth is a frozen-file conflict, reported, not fixed.** The
survey-claim scan found two references to the original "40-candidate, 13-domain survey" in
`docs/explanation/methodology.md` (lines 62 and 370, both inside explicitly labeled "Status:
Provisional" / "Open questions" self-disclosure notes). `docs/explanation/methodology.md` was
committed in P1 (`fc42d84`, "P1 contract") and carries zero working-tree modifications going into
this phase, which is the frozen artifact the house rules name: "The contract schema and
methodology are frozen; report conflicts, never edit them." This is a genuine conflict between the
zero-survey-claim requirement and the frozen methodology text, and it is recorded here for P5
rather than resolved by editing a frozen file. See "Open items for P5" below.

**scripts/README.md: fixed, self-discovered.** Running `node scripts/check.mjs` surfaced (as an
informational, above-declared-tier note that does not affect the grade or exit code) that
`scripts/README.md`'s inventory did not list the new `gen-index.mjs`. Added the entry; re-running
the gate confirms the note is gone. The other informational notes in that same block
(`__pycache__` under-listings, missing folder READMEs, the architecture-doc pair) are pre-existing,
above the plugin's declared Universal tier, and out of scope for a docs-integration commit; left
for P5.

**`contract/validate_envelopes.py`: fixed, per explicit instruction.** Before this pass, envelope
discovery was hardcoded to `bench/results/runs/` only. `bench/results/runs-cal1/` (40 envelopes,
committed in `246a2a4` "P3-cal1") was invisible to the validator: `python -m
contract.validate_envelopes` reported `462 file(s) valid` and never touched the calibration set.
Fixed by replacing the single hardcoded `RUNS_DIR` walk with `discover_run_roots()`, which globs
every `bench/results/runs*` directory (currently `runs/` and `runs-cal1/`, future-proof for a
`runs-cal2/` and so on) and validates the union. Three new regression tests were added
(`test_discover_run_roots_finds_the_primary_and_calibration_sets`,
`test_discover_run_roots_missing_results_dir_is_empty`,
`test_main_reaches_a_second_run_root_like_runs_cal1`) plus four existing tests were retargeted to
monkeypatch `RESULTS_DIR` instead of the now-secondary `RUNS_DIR`, so the multi-root path is what
they exercise. Net: 771 pytest tests passing, up from 768.

## 2. Full deterministic suite, run after the commit

| Command | Result |
|---|---|
| `python -m pytest -q` | `771 passed` |
| `node scripts/check.mjs` | `0 error(s), 0 warning(s)`, exit 0 (Convergent-tier notes remain informational only; plugin targets Universal tier at v0.1.0) |
| `npm run gen -- --check` | `.claude-plugin/plugin.json matches library.json.` / `INDEX.md matches library.json + component frontmatter.` / `AGENTS.md documents all 7 ci.yml command(s).` |
| `node scripts/gen-readme-catalog.mjs --check` | `README.md matches library.json + SKILL.md frontmatter.` |
| `python -m bench.report table --results bench/results/results.json --target README.md --check` | `no drift` |
| `python -m contract.validate_envelopes` (and `--strict`) | `502 file(s) valid` (462 under `runs/` + 40 under `runs-cal1/`) |
| `npm test` (`node --test`) | `0 tests`, exit 0 (no `.test.mjs` files exist in the repo yet; matches CI-PLANTED's observation, not a defect) |

`git status` at the end of this pass is clean: `nothing to commit, working tree clean`. No
planted-failure residue from CI-PLANTED remains (that report's own baseline-vs-final comparison
already confirmed this; my own status check corroborates it post-commit).

## 3. Audit

Evidence is command output or direct file reads, captured during this pass.

### S08-AC1, cold read pass

**Pass, with the caveat in section 1.** Both named weak spots (Q2 evidence sourcing, Q4 boundary
density) are fixed at the cited locations in `README.md`. Not independently re-run as a fresh
90-second read; no subagent tool was available to this pass to do so blind.

### S08-AC2, quickstart pass (marketplace-skip noted)

**Pass.** QUICKSTART-EXEC report: all 4 steps passed; Step 1 (Install) correctly skipped with the
stated reason ("plugin is unpublished"); Step 2 found all 4 expected findings (F-001 through
F-004, all severity 2) matching the golden reference exactly; Step 3 confirmed the envelope
structure and gate verdict; Step 4 confirmed `disposition.json` validated via `python -m
contract.validate disposition.json` -> `valid`, with the artifact SHA256 verified. No leftover
`disposition.json` in the repo root (confirmed absent this pass).

### S08-AC3, frontmatter complete

**Pass.** All six `skills/critique-*/SKILL.md` files carry `name`, `description`, `version`,
`license`, `rubric_sources` (each with `id`, `citation`, `url`, `accessed`,
`operationalization`), and `checks`, confirmed by direct read this pass.

### S08-AC4, all generators exist with working --check

**Pass.** `scripts/gen-plugin-manifest.mjs --check` (wraps the native-manifest and INDEX.md drift
checks and the AGENTS.md ci.yml-coverage check), `scripts/gen-index.mjs --check`,
`scripts/gen-readme-catalog.mjs --check`, and `python -m bench.report table ... --check` all ran
clean this pass with zero drift reported.

### S08-AC5, zero em/en dashes in repo-authored files

**Pass.** Scanned all 1057 git-tracked files plus the newly committed docs work for U+2014 and
U+2013: zero hits. Three hits exist under `.memsearch/memory/` and `_local/ai-chats/`, both
gitignored working-notes directories, not repo-authored tracked content, and correctly out of
scope.

### S07-AC1-local, all seven planted failures failed locally and reverted; AC-4-local tag guard blocks mismatch

**Pass, on CI-PLANTED's own evidence plus one item re-verified directly this pass.** CI-PLANTED
reports HEAD unchanged throughout its run and all seven planted defects (conformance,
unit-python, unit-node, schema, corpus, and two more not excerpted in the summary this pass
received) failed as expected and were reverted, `git status` clean. This pass did not re-plant and
re-break the seven failures (that would duplicate CI-PLANTED's own work); it did independently
re-verify the tag guard: `node scripts/check-release-versions.mjs v0.1.0` passes (`version guard
passed: every version-bearing manifest agrees with tag v0.1.0`) and `node
scripts/check-release-versions.mjs v9.9.9` fails as designed (`version guard failed: tag/version
mismatch; aborting before publishing a release`, exit 1).

### INTEGRITY

**Pass, all five sub-items confirmed directly.**

- Location-level baseline numbers in `results.json`: confirmed, each entry carries
  `recall_location` and `precision_location` fields alongside the criterion-level `recall` /
  `precision`.
- `verdicts.md` has the re-examination section: confirmed, `## Location-level re-examination
  (2026-07-31)` is present, plus the "Re-examined 2026-07-31" callout at the top of the file.
- `docs/internal/execution/P3-provenance.md` exists: confirmed.
- The results README carries the provenance block: confirmed, `## Provenance` at
  `bench/results/README.md:577`, opening "The 462 envelope files under `bench/results/runs/` were
  produced by a documented Claude Code multi-agent workflow, not by `bench/run_bench.py`."
- `validate_envelopes` reaches all 462: confirmed, and now reaches all 502 (the original 462 plus
  the 40 committed under `runs-cal1/`) after the fix in section 1. Before this pass's fix, the
  command would validate only the 462 and silently skip the calibration set, exactly the gap the
  launching instruction anticipated.
- `run_bench.py` real with mocked tests green: confirmed. `bench/run_bench.py` is a real
  implementation (parses judged-lane output, calls scripted-lane subprocesses, assembles and
  writes contract-valid envelopes), not a stub; `bench/tests/test_run_bench.py`'s 45 tests all
  pass, exercising it against mocked API calls (no live network I/O in the suite), including
  explicit no-API-key and no-matching-skill guard tests.

### VERDICT-REVIEW spot-check

The launching agent's own report already states `corePass: true, headlineChanged: true`. This
pass did not re-derive every cited figure from scratch; it cross-checked the headline
`critique-accessibility` numbers VERDICT-REVIEW cites against the committed, drift-checked
`README.md` table and found them matching exactly: haiku location recall 0.988 / baseline 0.376,
location precision 0.875 / baseline 0.258 (`README.md` line 74); sonnet location recall 0.965 /
baseline 0.776, location precision 0.672 / baseline 0.293 (`README.md` line 76); consistency 0.625
haiku / 0.808 sonnet against the 0.309 floor (`bench/results/README.md`, confirmed in this
commit's diff). No discrepancy found in the figures checked.

### GATE/TESTS

**Pass.** `node scripts/check.mjs`: 0 errors, 0 warnings, exit 0. `python -m pytest -q`: 771
passed, 0 failed.

## 4. Deviations from a literal reading of the launch instructions

- The audit criterion as given says "validate_envelopes reaches all 462." After the fix in section
  1, it reaches all 502 (462 original plus 40 under `runs-cal1/`), a superset that includes the
  462. Reported as a deviation rather than silently reconciled, since the instruction's own
  integration step explicitly required reaching the cal1 set and the audit line predates that fix
  being requested in the same message.
- S08-AC1 is marked pass on the strength of fixing and confirming the two named defects at their
  cited locations, not on an independent fresh-context re-read, because no subagent tool was
  available in this pass to perform one blind. Flagged rather than asserted as an unqualified pass.
- S07-AC1-local's planted-failure replay was not independently repeated in this pass; it relies on
  CI-PLANTED's own report plus this pass's `git status` confirmation of no residue and a direct
  re-check of the tag guard specifically (the one sub-item explicitly named in the audit
  criterion's second clause).

## 5. Open items for P5

1. **Survey-claim conflict in `docs/explanation/methodology.md`** (lines 62, 370). The file is
   frozen; the zero-survey-claim requirement and the frozen "Status: Provisional" self-disclosure
   text conflict. P5 needs either an explicit unfreeze-and-amend decision for those two lines, or
   the zero-survey-claim rule scoped to exclude labeled provisional/open-question self-disclosure.
2. **Cosmetic table-cell nit in `bench/results/README.md`.** One row under "Cells where a skill is
   worse than the generic prompt" reads `critique-accessibility 0.1.0 | sonnet | Consistency` with
   no separator between the skill name and its version in that cell. Pre-existing from earlier P4
   work, not flagged by any of the five verification reports this pass received, so left as-is
   rather than edited without instruction; noted for a future pass.
3. **`node scripts/check.mjs` Convergent-tier informational notes** (13 items, now 12 after the
   `gen-index.mjs` fix): missing folder READMEs for `agents/`, `.github/workflows/`, each
   `skills/critique-*/`, and the missing architecture-overview/architecture-detailed doc-role
   pair. All above the plugin's declared Universal tier at v0.1.0 and do not affect the gate;
   listed here only so a future tier-advancement pass has a starting inventory.
4. **True cold-read re-verification.** If a fresh-context reviewer or subagent becomes available,
   re-run the 90-second cold read against the current `README.md` to confirm S08-AC1 passes
   independently, not just at the level of "the two named defects are fixed at their cited
   locations."
