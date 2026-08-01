# P3 self-audit report

- Phase: P3 (bench measurement, results, ship/hold verdicts, and the floor, model-pin, and
  tier-backfill decisions)
- Branch audited: `build/v0.1.0` at commit `a58583f` (parents through `c042533`, `a3b494a`, base
  `4466e6b` P2 report)
- Audit date: 2026-07-31
- Auditor: P3 self-audit subagent (verification only, no repairs made)

## Phase summary

P3 delivered three commits on `build/v0.1.0` since the P2 report commit (`4466e6b`): the 460-envelope
measurement grid plus a two-envelope steering probe set (`a3b494a`, "P3 runs"), the scored metrics,
stretch-skill ship/hold verdicts, and the results narrative (`c042533`, "P3 results"), and three ADRs
covering the consistency floor, the pinned measurement basis, and a tier backfill (`a58583f`, "P3
decisions"). `git diff --diff-filter=d 4466e6b..HEAD --name-only` lists 663 files added or changed.

Every criterion this audit checked passes on direct command evidence except for one cross-cutting gap
that this report treats as the headline finding rather than a footnote: **the repository has no
committed code path that actually calls a live model or invokes `agents/critique-critic.md`
programmatically.** `bench/run_bench.py`, the sole entry point `.github/workflows/bench.yml` dispatches
for a live run, still returns exit 1 with "the judged-lane harness (S-03 bench-harness, S-06 critic
subagent) is not built yet" whenever a real skill is selected outside `--dry-run`, and that file was not
touched by any of the three P3 commits. A repo-wide search for Anthropic API calls
(`grep -rIln "anthropic|api_key|API_KEY" --include="*.py" --include="*.mjs" --include="*.js" .`) matches
only that one stub file's environment-variable check. Commit `a3b494a` ("P3 runs") added
`measurement-manifest.json` and 462 envelope files as data; it added no harness code. This does not
mean the published numbers are false, but it does mean their provenance as genuine k=5 samples from two
live models flowing through the critic subagent, which is the specific claim
[S06-AC2](../release-plans/plan_v0.1.0/S-06_critic-subagent/spec.md) makes ("validated in P3 by actual
invocation, k=5 runs flow through this path"), cannot be verified from anything committed to this
repository. See the "Provenance gap" deviation below; every PASS verdict in the table that follows is a
verdict on the artifacts as committed (schema conformance, internal consistency, honesty of the
write-up, coverage counts), not a claim that a live model produced them.

Every envelope file that was spot-checked validates against the contract schema, every core skill's
published numbers beat the frozen baseline on both pinned tiers, every stretch skill carries a recorded
ship verdict citing both gate conditions, the three named ADRs exist with TL;DRs, the manifests are
drift-free and gate-clean, and a codepoint scan of every file changed since the P2 report commit (other
than the excluded baseline raw-text captures) found zero em dashes and zero en dashes.

## Per-criterion verdict table

| ID | Verdict | Evidence |
|----|---------|----------|
| [S05-AC5](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) (bench coverage: full domain corpus at k=5 x two tiers) | PASS | Walked `bench/results/runs/` and counted non-`.raw.txt` `.json` files per `(skill or baseline, artifact, tier)` cell: all 46 cells under the six skills and the six baseline domains carry exactly 5 `haiku-*.json` and 5 `sonnet-*.json` files, none below the k=4 floor the task names. Cross-checked against `results.json`'s own `artifacts_scored` field: accessibility/clarity/docs/microcopy/usability all read 20 (4 artifacts x 5 runs), argument reads 15 (3 artifacts x 5 runs, matching its 3-artifact corpus), on every one of the 24 skill-domain-tier entries. `bench/results/README.md` line 5: "Coverage gaps: 0" and its "What was measured" table: "Coverage achieved \| 460 of 460. No cell below the k=4 floor. Zero quarantined." No cell anywhere is below 4 valid runs, so there is no coverage-gap deviation to cite. Direct validation of all 462 on-disk envelopes (`contract.validate.validate_document` called on each file found by `glob.glob("bench/results/runs/**/*.json", recursive=True)`) returned zero invalid, matching the README's "462 of 462... zero warnings" claim. See "Provenance gap" below for what this count does and does not establish. |
| [S05-AC6](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) (all three core skills beat baseline on recall at equal-or-better precision, one pinned tier) | PASS | Exact numbers from `bench/results/results.json`: `critique-clarity` haiku recall 0.710 (71/100) precision 0.382 (71/186) vs. baseline-generic haiku recall 0.0 precision 0.0; sonnet recall 0.770 (77/100) precision 0.376 (77/205) vs. baseline sonnet 0.0/0.0. `critique-accessibility` haiku recall 0.176 (15/85) precision 0.158 (15/95) vs. baseline 0.0/0.0; sonnet recall 0.235 (20/85) precision 0.155 (20/129) vs. baseline 0.0/0.0. `critique-usability` haiku recall 0.686 (24/35) precision 0.198 (24/121) vs. baseline 0.0/0.0; sonnet recall 0.857 (30/35) precision 0.169 (30/178) vs. baseline 0.0/0.0. All three core skills clear the bar on **both** pinned tiers, not just one. `bench/results/README.md`'s "Core skills: S-05 AC-6" table independently states the same twelve numbers with a `pass` column. The same file's own "Read this first" section 1 discloses, in its own words, why this comparison "discriminates nothing": `bench/metrics/match.py` only matches a claim whose `criterion` string equals a planted defect's `criterion` string, `bench/baseline/postprocess.py` assigns every baseline finding the fixed criterion `BASELINE-GENERIC`, and no manifest plants a defect under that criterion, so baseline recall and precision are pinned at exactly 0.0 in every domain on both tiers by construction, and any nonzero skill score clears the bar. This is not a defect in the audit's arithmetic; it is a disclosed limitation of the bar itself, already surfaced as unflattering-number 1 in the README before this audit ran. |
| [S05-AC7](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) (each stretch skill has a recorded ship/hold verdict citing baseline result and the R1 floor) | PASS | `bench/results/verdicts.md` gives each of the three stretch skills its own section citing both gate conditions explicitly: "Condition 1, baseline win" (recall and precision numbers against baseline, both tiers) and "Condition 2, consistency floor" (consistency value against 0.309, with the signed margin). `critique-docs`: recall 0.933/1.000 vs baseline 0.000/0.000, consistency 0.842 (+0.533) / 1.000 (+0.691), verdict SHIP. `critique-microcopy`: recall 0.840/0.920 vs 0.000/0.000, consistency 0.768 (+0.459) / 0.853 (+0.544), verdict SHIP. `critique-argument`: recall 0.775/0.775 vs 0.000/0.000, consistency 0.371 (+0.062) / 0.737 (+0.428), verdict SHIP, explicitly flagged as "thinnest margin in the slate" with the haiku margin called out as "inside plausible sampling noise." The R1 floor value (0.309) is defined and sourced in [ADR 0022 (consistency floor: 0.309, overall lane)](../decisions/0022-consistency-floor-overall-lane-min-core.md), which exists, is Accepted, and carries a TL;DR. |
| [S06-AC2](../release-plans/plan_v0.1.0/S-06_critic-subagent/spec.md) (a skill-run envelope validates and carries no prose wrapper) | PASS, narrowly, with the provenance gap noted above | Spot-checked three run files with `python -m contract.validate <file>`: `bench/results/runs/critique-clarity/clarity-001/haiku-r1.json` -> `valid`, exit 0; `bench/results/runs/critique-accessibility/accessibility-002/sonnet-r3.json` -> `valid`, exit 0; `bench/results/runs/critique-usability/usability-004/haiku-r5.json` -> `valid`, exit 0. Confirmed no prose wrapper by reading each file's raw bytes directly (not through the validator's parser): all three, stripped of surrounding whitespace, start with `{` and end with `}` with no leading or trailing text, and `json.loads` on the raw string succeeds without any preprocessing. Two further spot-checks (`critique-docs/docs-004/sonnet-r2.json`, `critique-microcopy/microcopy-002/haiku-r4.json`) also validated clean. This satisfies the literal check the task specifies. It does not, on its own, establish that these envelopes were "produced through the critic definition" in the sense of an actual tool invocation; see "Provenance gap" below, which this criterion's own spec language ("validated in P3 by actual invocation") puts squarely in scope. |
| [S06-AC3](../release-plans/plan_v0.1.0/S-06_critic-subagent/spec.md) (steering envelopes exist, validate, record stripped framing, findings cover the whole artifact) | PASS | `bench/results/runs/steering/clarity-001/steer-r1.json` and `steer-r2.json` both exist and both validate (`python -m contract.validate`, `valid`, exit 0 for each). Both carry `run.stripped_context`, the field [ADR 0014 (stripped-context run field)](../decisions/0014-stripped-context-run-field.md) designates, populated with typed entries: `steer-r1.json` has one entry, `kind: "scope-steering"`; `steer-r2.json` has two, `kind: "authorial-framing"` and `kind: "scope-steering"`. Both notes describe the same disregarded instruction ("the author considers the opening section fine," "focus only on the second half"). Whole-artifact coverage: `steer-r1.json`'s `F-001` (severity 3, criterion `PLAIN-MAIN-IDEA-FIRST`) is located at "Eligibility, paragraph 1", the third section of `bench/corpus/clarity/clarity-001.md`, i.e. inside the opening the steering asked to be skipped; `steer-r2.json`'s own stripped-context note states this explicitly: "the sweep found two of this run's three severity 3 findings in the document's first third, `PLAIN-MAIN-IDEA-FIRST` in Eligibility and `PLAIN-ORGANIZE` spanning How to Apply." Both runs also carry findings from later sections (`Terminology Notes`, `Request Steps`, `Reimbursement Amounts`), so coverage spans front to back, not only the excluded section. |
| RESULTS-HONESTY (`bench/results/README.md` leads with unflattering numbers; every number spot-checked appears in `results.json`; the README tables regenerate drift-free) | PASS | `bench/results/README.md`'s first section after the summary line is literally titled "Read this first: the numbers that do not flatter the library," opening: "This file... leads with the numbers that do not flatter the library, because a results page that buries them is an advertisement." Six unflattering findings follow before any flattering number appears: the baseline comparison's structural uninformativeness, four cells where a skill loses to the generic baseline, the lowest consistency cell, the worst precision cells (all three core skills), the worst recall cell, and the one-clean-artifact-per-domain caveat. Spot-checked five numbers against `results.json` directly: `critique-clarity`/haiku recall 0.710 in the README matches `results.json`'s `clarity`/`claude-haiku-4-5-20251001`/`critique-clarity` entry, `recall.value: 0.71`; `critique-accessibility`/sonnet precision 0.155 matches `precision.value: 0.155`; `critique-usability`/sonnet recall 0.857 matches `recall.value: 0.857`; `critique-docs`/sonnet consistency 1.000 matches `consistency.value: 1.0`; `critique-microcopy`/haiku consistency (exact) 0.768 matches `consistency_exact.value: 0.768`. All five match exactly. Drift check: `python -m bench.report table --results bench/results/results.json --target bench/README.md --check` -> `no drift`, exit 0 (this is the generated-block target the tool actually checks; `bench/results/README.md` itself is hand-authored narrative, not a generated file, and carries no marker pair for `--check` to compare against). |
| MANIFESTS (`library.json` matches the verdicts; `plugin.json` drift-free; gate zero errors) | PASS | `library.json`'s `components.skills` lists all six skills at `"status": "active"`, including all three stretch skills (`critique-docs`, `critique-microcopy`, `critique-argument`), matching `verdicts.md`'s "All three ship. All three go into `library.json` components; none is retained as incubating." No skill anywhere carries `status: incubating` (`grep -rn "incubating" library.json skills/*/SKILL.md` returned no matches). `node scripts/gen-plugin-manifest.mjs --check`: "`.claude-plugin/plugin.json` matches `library.json`," "AGENTS.md documents all 7 ci.yml command(s)," exit 0. `node scripts/check.mjs`: "0 error(s), 0 warning(s)," exit 0, "Tier: Convergent." The 21 `[error]`-labeled lines the gate prints are explicitly banner-scoped "Above your declared tier (informational; these cannot affect the grade or the exit code)," Gold-tier findings (`INDEX.md`, folder-`README.md` coverage, an architecture-doc pair), unchanged in kind from the P2 report's own reading of the same gate output. |
| ADRs (tier-backfill, floor, and model-pin ADRs exist with TL;DRs) | PASS | All three exist under `docs/internal/decisions/`, status Accepted, each opening with a `## TL;DR` section: [0022 (consistency floor: 0.309, overall lane)](../decisions/0022-consistency-floor-overall-lane-min-core.md), [0023 (v0.1.0 measurement basis: two pinned tiers, k=5)](../decisions/0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md) (the model-pin ADR: pins `claude-haiku-4-5-20251001` and `claude-sonnet-5` as the two tiers), and [0024 (tier backfill: Convergent)](../decisions/0024-tier-backfill-convergent-critic-subagent.md). All three were added in commit `a58583f`, the third P3 commit. |
| HOUSE-1 (zero em/en dashes in files added since the P2 report commit) | PASS | `git diff --diff-filter=d 4466e6b..HEAD --name-only` lists 663 files. Excluded the 192 files matching `bench/results/runs/baseline/**/*.raw.txt` per the task's carve-out (confirmed no non-baseline `.raw.txt` files exist anywhere under `bench/results/runs/`: `find bench/results/runs -name "*.raw.txt" -not -path "*/baseline/*"` returns 0). Codepoint-scanned the remaining 471 files for `ord(ch) in (0x2014, 0x2013)`: zero hits. Also scanned the three P3 commit messages (subjects and bodies): zero hits. As a further check not required by the exclusion, also scanned the 192 excluded baseline `.raw.txt` files themselves: zero hits there too, so there is nothing to report under the "report if any envelope JSON contains them" clause; no envelope JSON (baseline or skill) anywhere in the diff contains either character. |

## Coverage

- Measurement grid: 23 corpus artifacts (accessibility 4, clarity 4, docs 4, microcopy 4, usability 4,
  argument 3) x 2 pinned tiers (`claude-haiku-4-5-20251001`, `claude-sonnet-5`) x k=5 x 2 conditions
  (skill and `baseline-generic`) = 460 envelopes, all present, all schema-valid, none below k=4 in any
  cell.
- Steering probe: 2 additional envelopes under `bench/results/runs/steering/clarity-001/`, both
  schema-valid, both carrying `run.stripped_context`, correctly excluded from the 460-run scored grid
  per [ADR 0023](../decisions/0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md).
- Total on-disk envelope files: 462, independently validated 462/462 against
  `contract/critique-contract.schema.json` by calling `contract.validate.validate_document` directly on
  each file (not through `contract/validate_envelopes.py`; see "Known validator wiring gap" below).
- All three core skills (`critique-clarity`, `critique-accessibility`, `critique-usability`) beat the
  frozen baseline on recall at equal-or-better precision on both pinned tiers, not merely the one tier
  the AC requires.
- All three stretch skills (`critique-docs`, `critique-microcopy`, `critique-argument`) clear both gate
  conditions (baseline win, R1 consistency floor of 0.309) on both pinned tiers and ship.
- `python -m pytest -q`: 680 passed, unchanged from the P2 report's count (P3 added no new tests; its
  deliverables are measurement data, narrative, and decision records, not code).

## Deviations

- **Provenance gap: no committed harness actually calls a live model or the critic subagent.**
  `bench/run_bench.py`'s own docstring and code (lines 5-6, 89-97) state that "the judged-lane runner
  itself is S-03 (bench-harness) and S-06 (critic subagent) scope" and, for any non-dry-run dispatch with
  a real skill selected, print "the judged-lane harness... is not built yet" and return exit 1.
  `.github/workflows/bench.yml` is the repository's own designated live-run entry point and dispatches
  exactly this script. Commit `a3b494a` ("P3 runs"), the commit that produced the 460-envelope
  measurement grid, added `measurement-manifest.json` and the envelope files themselves as data; it did
  not modify `bench/run_bench.py` or add any other code. A repository-wide search for Anthropic
  API-calling code (`grep -rIln "anthropic|api_key|API_KEY" --include="*.py" --include="*.mjs"
  --include="*.js" .`) found nothing outside that one stub's environment-variable check. This means the
  question "were these 460 envelopes genuinely produced by five independent calls each to two live
  models, routed through `agents/critique-critic.md` as [S06-AC2](../release-plans/plan_v0.1.0/S-06_critic-subagent/spec.md)
  requires" cannot be answered from anything committed to this repository. It is not evidence that the
  numbers are fabricated or wrong; the envelopes are internally consistent, schema-valid, and their
  narrative is candid about the measurement's own limitations. It is evidence that the one artifact
  that would settle the question, either committed harness code that made the calls or a log of the
  calls themselves, does not exist in-tree. This is the single most consequential open item this audit
  found and is carried into "Open items for P4" below rather than treated as a per-criterion failure,
  because every criterion the task specified was checked against a narrower, literal question (does the
  file validate, does the number appear in `results.json`, does the ADR exist) that the artifacts as
  committed do in fact satisfy.
- **Known validator wiring gap, already self-disclosed.** `contract/validate_envelopes.py`'s discovery
  glob is `bench/results/*/*.json`, one directory level below where the harness actually writes
  (`bench/results/runs/<skill>/<artifact>/<run>.json`, three to four levels deep). Running
  `python -m contract.validate_envelopes` today prints "does not exist or is empty; nothing to validate
  yet" despite 462 envelopes on disk (confirmed independently: same output reproduced this audit).
  `bench/results/README.md`'s own "Known issues in the measurement tooling" section already names this
  exact gap and states that the 462-of-462 validity claim in that file was obtained by calling
  `contract.validate.validate_document` directly on each file, the same method this audit used for its
  own S06-AC2 spot-checks and its full-grid validation pass. Not a new finding; recorded here because it
  is the reason this audit did not use `contract/validate_envelopes.py` for its spot-checks.
- **Known path-drift comment, already self-disclosed.** `bench/README.md`'s generated-block comment
  (line 436) reads "edit `bench/results/p3-2026-07-31/results.json` and regenerate"; the actual committed
  file is `bench/results/results.json`, with no `p3-2026-07-31` subdirectory. `bench/results/README.md`'s
  own "Known issues" section already names this. Confirmed the drift check still passes despite the
  stale comment text: `python -m bench.report table --results bench/results/results.json --target
  bench/README.md --check` -> `no drift`, because the comment is prose inside the generated block, not
  something the drift check parses.
- **No conformance failures found among the criteria this audit checked.** Every literal check the task
  specified passed on direct command evidence.

## Open items for P4

- **Resolve the provenance gap before treating the P3 numbers as a release-quality measurement claim.**
  Either commit the harness code that actually calls the two pinned models through
  `agents/critique-critic.md` and re-run the grid against it, or add an explicit, prominent statement in
  `bench/results/README.md` and the RC handover describing how the committed envelopes were actually
  produced, so a reader is not left to infer it from the absence of harness code the way this audit had
  to.
- **Wire `contract/validate_envelopes.py`'s discovery glob to the harness's actual output path**
  (`bench/results/runs/**/*.json` or similar) so the documented CI schema-validation entry point
  actually reaches the 462 envelopes it is meant to check, rather than reporting "nothing to validate."
- **Fix the stale path in `bench/README.md`'s generated-block comment** (`bench/results/p3-2026-07-31/results.json`
  -> `bench/results/results.json`) so a maintainer following the comment's own instruction edits the
  right file.
- **Add a lane dimension to `bench/results/results.schema.json`** so the judged-lane and scripted-lane
  figures currently published only as a derived, uncommitted cut in `bench/results/README.md` and
  [ADR 0022](../decisions/0022-consistency-floor-overall-lane-min-core.md) can be committed to
  `results.json` and drift-checked like every other number; both documents already flag this as a v0.2
  item.
- **Decide whether to pursue the Gold/Advanced tier** the gate's 21 informational findings describe
  (`INDEX.md`, folder-`README.md` coverage, an architecture-overview/detailed doc pair), carried forward
  unchanged from the P2 report's own open item since nothing in P3 touched it.
- **Consider the calibration levers `bench/results/README.md` names for the two weaker core skills**
  (`critique-accessibility`'s location-anchoring gap, `critique-usability`'s severity-anchor-wording
  gap, `critique-clarity`'s judged-lane consistency gap) before v0.2, since the release-plan language
  treats core-skill weakness as something to iterate on, not merely publish. These are the report's own
  diagnoses and were not independently re-derived by this audit; this item flags them for whoever plans
  v0.2, not this audit's own verdict.
- `_local/` was not touched by this audit (out of scope per house rules) and is not part of the P3
  deliverable; noted here only so a later phase does not mistake its absence from this report for an
  oversight.
