# P1 self-audit report

- Phase: P1 (critique contract, bench-core, CI pipeline)
- Branch audited: `build/v0.1.0` at commit `41ee2ff` (parents `f52c3e9`, `fc42d84`, base `0054cee` (P0 report))
- Audit date: 2026-07-31
- Auditor: P1 self-audit subagent (verification only, no repairs made)

## Phase summary

P1 delivered three commits on `build/v0.1.0`, all carrying the required `Co-Authored-By` and
`Claude-Session` trailers:

1. `fc42d84` "P1 contract: schema frozen, validator, constitution, references" - the JSON Schema
   draft 2020-12 contract (`contract/critique-contract.schema.json`), the Python validator and CLI
   (`contract/validate.py`, `contract/validate_envelopes.py`), 327 (116 contract-scoped) pytest
   tests including a 57-case adversarial suite, `docs/reference/severity-scale.md`,
   `docs/reference/criterion-ids.md`, `docs/explanation/methodology.md`, and five ADRs (0012-0016).
2. `f52c3e9` "P1 bench-core: generator, toy domain, metrics, baseline" - the deterministic
   corpus generator and its toy domain plugin, `bench/metrics/`, the frozen baseline prompt and
   post-processing rule, `bench/results/results.schema.json`, `bench/report.py`, and
   `bench/README.md`.
3. `41ee2ff` "P1 ci: workflows and script surface" - `.github/workflows/{ci,bench,release}.yml`,
   `scripts/check-release-versions.mjs`, `scripts/lib/version-manifest.mjs`, and the `AGENTS.md`
   "Checks" section.

`git diff 0054cee..HEAD --name-only` lists 109 files touched since the P0 report commit. All 327
repo-wide pytest tests pass (`python -m pytest`, "327 passed"). The family gate exits 0 at Universal
tier with zero errors. One acceptance criterion, S07-AC2 (workflows contain no validation logic),
fails on a specific, cited finding in `release.yml`; every other checked criterion passes. Three
S-07 criteria and one S-03 criterion are deferred per this audit's scope, consistent with the
release plan's own phasing.

## Per-criterion verdict table

| ID | Verdict | Evidence |
|----|---------|----------|
| S02-AC1 | PASS | `jsonschema.Draft202012Validator.check_schema()` on the loaded schema raised no error; `schema["$schema"]` is `"https://json-schema.org/draft/2020-12/schema"`. Built an envelope missing `run.skill` and ran `python -m contract.validate <file>`: exit 1, stderr `run.skill: missing required field 'skill'` (plus three other field-naming lines for other planted defects in the same file: `run.rubrics`, `summary.severity_3_threshold`, `summary.gate`). |
| S02-AC2 | PASS | `contract/tests/fixtures.py::FINDING_REQUIRED_FIELDS` lists exactly the nine required finding fields. `pytest contract/tests/test_schema_examples.py`: `test_example_finding_validates`, `test_example_envelope_validates`, and 9+9 parametrized `test_malformed_finding_missing_field_fails_naming_the_field[<field>]` / `test_malformed_finding_fails_the_full_envelope_too[<field>]` (one per required field) all pass. Independently re-ran the methodology's worked example envelope (section 5, `F-007`/`WCAG-1.4.3`) through `python -m contract.validate` directly: `valid`, exit 0. |
| S02-AC3 | PASS | `contract/critique-contract.schema.json` `$defs` contains `dispositionLog` and `dispositionEntry`. `pytest contract/tests/test_disposition_log.py::test_sample_disposition_log_validates` passes. |
| S02-AC4 | PASS | `docs/reference/severity-scale.md` "The scale" table has rows 0-4 with Meaning and Disposition columns. "Domain anchors" has one subsection per launch domain (Usability, Accessibility, Clarity, Docs, Microcopy, Argument): each subsection's table has exactly 2 severity-2 rows and 2 severity-3 rows, satisfying "at least two anchor examples per launch domain." |
| S02-AC5 | PASS | `docs/reference/criterion-ids.md` "Grammar" states `^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+(?:\.[A-Z0-9]+)*)+(?![\s\S])`. Loaded the schema and read `$defs.criterionId.pattern`: identical string, character for character. |
| S02-AC6 | PASS | `python -m contract.validate --help` shows `--gate` and `--threshold`. `pytest contract/tests/test_gate.py` (14 tests, including `test_severity_4_envelope_gate_exit_code_is_one`) passes. Independently constructed a severity-4 envelope (adapted from the methodology's WCAG example, `by_severity: {"4": 1}`, `gate: "fail"`) and ran `python -m contract.validate --gate <file>`: `valid`, exit 1. |
| S02-AC7 | PASS | Codepoint scan of `docs/explanation/methodology.md`: 0 occurrences of U+2014, 0 of U+2013. 13 `Status:` label occurrences found by regex. The section-5 example finding's fields (`F-007`, `WCAG-1.4.3`, `#8a8a8a`/`#f5f5f5`, `2.9:1`, `#595959`) match `contract/tests/fixtures.py::example_finding()` verbatim, which is itself schema-valid (confirmed via `test_schema_examples.py`). |
| S02-AC8 | PASS | `docs/internal/decisions/0016-contract-enforcement-boundary.md` ("The contract enforcement boundary") documents four holes an adversarial pass found and closed at the freeze (non-integer summary counts, house style unenforced in the reserved `selector`, calendar-invalid timestamps, negative `--threshold`), each with a regression test named in `contract/tests/test_adversarial.py`, plus an explicit "Accepted, with the reasoning" section for the eight review-lane field contracts that stay unautomated by design. `pytest contract/tests/test_adversarial.py`: 57 passed. |
| S03-AC1 | PASS | `python -m bench.generator verify --corpus bench/corpus`: "verify OK: 7 file(s) byte-identical" (the tool's own regenerate-and-hash-compare command). Independently ran `python -m bench.generator build --out <tmp1>` and `--out <tmp2>` to two fresh directories and `diff -rq <tmp1> <tmp2>`: no output, exit 0 (byte-identical, confirmed outside the tool's own verification code path). `.gitattributes` marks `bench/corpus/** -text` so Windows checkout does not rewrite line endings under the recorded `artifact_sha256` values. |
| S03-AC2 | PASS | `bench/generator/README.md` (668 lines) has a "Worked example: the `toy` domain" section (lines 363-608) walking `bench/generator/domains/toy.py` end to end: vocabulary, composition, injectors keyed by criterion ID, addressing, and recipes, plus "What `toy-001` generates" and "What `toy-001` records." `pytest bench/generator/tests` (118 tests, including `test_toy_domain.py`) passes. |
| S03-AC3 | DEFERRED | Corpus currently holds 3 `toy` artifacts (`bench/corpus/toy/toy-00{1,2,3}.md`), not the >=20-artifact, >=3-per-core-domain, >=1-clean-per-core-domain target. The release plan's `IMPL-B-skills-to-rc.md` places per-domain defect libraries under S-05 (skills slate), which has not landed; `bench/generator/README.md`'s stated model is that domain modules are contributed by each skill pipeline against the plugin API this effort defines. Recorded as an expected deviation per this audit's scope, not a build defect. |
| S03-AC4 | PASS | `bench/metrics/tests/test_score_ac4.py` module docstring: "perfect run, empty run, duplicate findings, location-tolerance edge, and clean-artifact false positive... one test function each." Read all five: `test_perfect_run_matches_every_defect_at_full_precision`, `test_empty_run_scores_zero_recall_and_undefined_precision`, `test_duplicate_findings_earn_recall_once_and_cost_precision_every_time`, `test_location_tolerance_edge_hit_at_plus_one_miss_at_plus_two`, `test_clean_artifact_claims_count_against_precision_and_fp_rate`. `pytest bench/metrics/tests`: 69 passed. |
| S03-AC5 | PASS | `bench/baseline/prompt.txt` exists and is committed in `f52c3e9`. `bench/baseline/postprocess.py` maps the frozen prompt's four-line block format to contract fields; `pytest bench/baseline/tests`: 12 passed. |
| S03-AC6 | PASS | `bench/results/results.schema.json` exists (`$schema` draft 2020-12). `pytest bench/tests/test_report.py`: 12 passed, including `test_cli_check_reports_no_drift_after_update` and `test_cli_check_detects_drift_before_update`. Independently built a synthetic `results.json` and target markdown file outside the test suite: `python -m bench.report table --results ... --target ... --check` reported drift (exit 1) before the table existed in the target, then `... table` wrote it (exit 0), then `--check` reported "no drift" (exit 0). |
| S03-AC7 | PASS | `bench/README.md` headings cover "Corpus design," "Location tolerance," "Metrics," and "Reproduction," with a "Content and licensing" subsection citing `ADR 0005 (licensing: Apache-2.0 repo, CC-BY-4.0 corpus)`. Independently ran all four numbered reproduction commands from the README ("Reproduction" section) by hand: `bench.generator build`/`verify` (byte-identical), `bench.generator leak-check` ("leak check OK"), and confirmed `bench.metrics score` and `bench.report table` exist and run (both used above under S03-AC4/AC6). |
| S03-AC8 | PASS | `bench/generator/tests/test_leak.py` exists with 10 tests covering description-leak (verbatim quote, normalization, shingle boundary), criterion-ID leak, and path leak, plus `test_leak_check_corpus_over_a_freshly_built_toy_corpus_finds_nothing`. All 10 pass. Independently ran `python -m bench.generator leak-check --corpus bench/corpus`: "leak check OK", exit 0. |
| S07-AC2 | FAIL | `ci.yml` and `bench.yml` contain no verdict-computing shell logic beyond one defensible orchestration check (`bench.yml` line 67, `if [ -z "$(git status --porcelain -- bench/results)" ]`, decides whether there is anything new to push, not a correctness judgment). `release.yml` lines 91-99, however, run an inline `awk` script to extract the tagged version's `RELEASE-NOTES.md` section into `RELEASE_BODY.md`, then `if [ ! -s RELEASE_BODY.md ]; then ... exit 1; fi`: this is a shell pipeline that computes a verdict (does this tag have release notes) and fails the job on it, inline in the workflow, unlike the tag-version guard on the same file which is correctly delegated to `scripts/check-release-versions.mjs`. This is exactly the pattern the criterion's own grep-auditable definition forbids ("no shell pipelines that compute verdicts"). Recommend extracting this into a script (e.g. `scripts/extract-release-notes.mjs`), documented in `AGENTS.md`, mirroring how the tag guard is already handled. |
| S07-AC3 | PASS | `bench.yml` `on:` block has only `workflow_dispatch` (no `push`/`pull_request`). Ran `bench/run_bench.py` directly with `ANTHROPIC_API_KEY` unset: without `--dry-run`, exit 1, stderr "ANTHROPIC_API_KEY is required for a live run... pass --dry-run to validate wiring without it"; with `--dry-run`, exit 0, no secret required, prints the dry-run wiring-validation messages. |
| S07-AC5 | PASS | `AGENTS.md` "Checks" section's CI table lists all seven `ci.yml` jobs' commands verbatim (`npm run check`, `python -m pytest`, `npm test`, `npm run validate:envelopes`, `python -m bench.generator verify --corpus bench/corpus`, `npm run gen -- --check`, `npm audit --audit-level=high`), plus the bench and release reproduction commands. Ran `npm run gen -- --check`: "gen --check: AGENTS.md documents all 7 ci.yml command(s)." exit 0. Read `scripts/gen-plugin-manifest.mjs`'s `checkAgentsDocCoverage()`: it parses every `ci.yml` line ending `# doc-check` and fails if the exact command string is not a substring of `AGENTS.md`, confirming the drift-on-omission mechanism is real, not just a passing message. |
| S07-AC1 | DEFERRED | Per this audit's scope: planted-failure verification (one deliberate failure per job category, in a test branch) is scheduled for P4 per `IMPL-A-foundation.md` phase A4's own verification note ("S-07 AC-1..AC-5 (AC-6 measured at P5)" recorded as the phase's target, with runtime-dependent proof deferred). Not exercised in this audit. |
| S07-AC4 | DEFERRED | Per this audit's scope: the scratch-clone test-tag block scenario needs a real tag push against a disposable clone, scheduled P4-P5 per plan. `scripts/check-release-versions.mjs` exists and its logic was read (reads `scripts/lib/version-manifest.mjs`'s enumeration, compares each file's version to the tag, fails on any mismatch) but not exercised end to end against a live tag in this audit. |
| S07-AC6 | DEFERRED | Per this audit's scope: `ci.yml` runtime is only measurable on GitHub-hosted runners, scheduled for measurement at P5 per plan. Not exercised in this audit. |
| GATE | PASS | `node scripts/check.mjs`: "0 error(s), 1 warning(s)." at "Tier: Universal." All `[error]`-prefixed lines are under the explicit banner "Above your declared tier (informational; these cannot affect the grade or the exit code)" and target Convergent/Gold-tier checks (`agent-targets`, `index-drift`, `folder-readme` x7, `docs-presence`), not Universal. Exit code 0 (command completed, no shell error). |
| HOUSE-1 | PASS | Two independent scans of the 109 files `git diff 0054cee..HEAD --name-only` lists (everything added/changed on this branch since the P0 report commit): a Python codepoint scan reading each file directly and testing `ord(ch) in (0x2014, 0x2013)` for every character (zero found across all 109 files) and a Grep-tool Unicode-class search for the two dash codepoints across the whole working tree excluding `.git`/`node_modules`/`__pycache__`/`.pytest_cache` (zero files matched). Commit messages for all three P1 commits (`fc42d84`, `f52c3e9`, `41ee2ff`) were also scanned by codepoint and contain no em-dash or en-dash. |

## Deviations from the implementation plan

- **S07-AC2 fails on one cited finding** (see table above): `release.yml`'s RELEASE-NOTES extraction
  and empty-body guard is inline shell/`awk` logic that computes a verdict, rather than being
  delegated to a script the way the neighboring tag-version guard is. This is a real conformance gap
  against the criterion as written, not a documentation nit; recommend closing it in P2 before RC by
  moving the extraction into a small Node script under `scripts/`, documented in `AGENTS.md`
  alongside the existing release commands.
- **S03-AC3 deferred as instructed**, consistent with the release plan: `IMPL-B-skills-to-rc.md`
  places per-domain corpus content under S-05 (skills slate), which starts at P2. The `toy` domain
  (3 artifacts, 1 clean) is the harness's own self-test fixture, not an attempt at the >=20-artifact
  target, and the generator's plugin API (S03-AC2) is what P2's skill pipelines will build against
  to reach it.
- **S07-AC1, AC-4, AC-6 deferred as instructed.** `IMPL-A-foundation.md` phase A4's own verification
  line names AC-6 as "measured at P5" and groups AC-1 through AC-5 together as the phase target;
  this audit's scope note additionally defers AC-1 and AC-4 to the same later phases (P4-P5) because
  both need a live GitHub Actions run or a disposable tag push that a local, offline self-audit
  cannot exercise. No evidence contradicts these being achievable later: `run_bench.py`'s dry-run
  path and `check-release-versions.mjs`'s logic were both read and, where locally exercisable
  (dry-run only, not a live tag), passed.
- No other deviations found. Every other AC in scope for this audit passed on direct command
  evidence, matching what the P1 commits' own docstrings and ADRs (0012-0016) claim they built.

## Open items for P2

- Close the S07-AC2 finding: extract `release.yml`'s RELEASE-NOTES section into a documented script
  before RC, so a grep for inline `if` blocks in `.github/workflows/` returns nothing outside
  `bench.yml`'s orchestration check, or record an ADR explicitly accepting this inline extraction as
  out of scope for AC-2's grep-auditable definition if that is the intended reading.
- `bench/corpus/` still holds only the `toy` domain (3 artifacts). S-05 (skills slate) is where the
  six launch domains' generators land and where S03-AC3's >=20-artifact, >=3-per-core-domain,
  >=1-clean-per-core-domain target becomes checkable for real.
- `library.json`'s `components.skills` is still empty, so `bench/run_bench.py --dry-run` reports "0
  of 0 declared skill(s)" and a live dispatch would do nothing; this is expected at P1 and resolves
  once S-05 populates it.
- S07-AC1, AC-4, and AC-6 remain unverified against a live GitHub Actions run. Schedule the
  planted-failure branch (AC-1), the scratch-clone test-tag block (AC-4), and the runtime
  measurement (AC-6) for P4-P5 per the existing plan, and re-run this audit's checks against them
  once exercised.
- `docs/internal/decisions/0016-contract-enforcement-boundary.md` flags its own residual risk in
  "Consequences": "nothing in v0.1 measures whether [the review lane] holds." No action needed at
  P1; noted here so a later phase does not lose the thread.
