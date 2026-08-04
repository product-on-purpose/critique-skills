# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-01

### Added
- Repo scaffold: `library.json`, generated `.claude-plugin/plugin.json`, the conformance gate
  wrapper (`scripts/check.mjs`), the manifest generator (`scripts/gen-plugin-manifest.mjs`),
  `LICENSE` (Apache-2.0), `AGENTS.md`, `README.md`, `RELEASE-NOTES.md`, and the Diataxis docs tree.
- Critique Contract: `contract/critique-contract.schema.json` (JSON Schema draft 2020-12) defining
  the finding object, the run envelope, and the disposition log; a Python validator and CLI
  (`contract/validate.py`, `contract/validate_envelopes.py`) with `--gate` exit-code semantics;
  `docs/reference/severity-scale.md` (the shared 0-4 scale with per-domain anchors) and
  `docs/reference/criterion-ids.md` (the `<SOURCE>-<CRITERION>` ID grammar); the promoted
  constitution at `docs/explanation/methodology.md`.
- Bench harness: a deterministic seeded-defect generator (`bench/generator/`) with a domain-plugin
  API, a 23-artifact corpus across six domains with at least one clean artifact per core domain
  (`bench/corpus/`), metrics for recall, precision, and k=5 Jaccard consistency (`bench/metrics/`),
  a frozen baseline prompt and postprocessor (`bench/baseline/`), and generated, drift-checked
  results tables (`bench/report.py`).
- Skill template pattern: the canonical skill directory shape and self-test runner
  (`docs/internal/skill-template.md`, `scripts/skill-selftest.py`), plus the shared lane library at
  `skills/_shared/`.
- Six critique skills, all shipped active: `critique-clarity` (US Federal Plain Language
  Guidelines, Williams), `critique-accessibility` (WCAG 2.2 AA), `critique-usability` (Nielsen's 10
  heuristics, narrow artifact claim: HTML/markdown UI specs, not live applications),
  `critique-docs` (Diataxis), `critique-microcopy` (NN/g error-message guidelines), and
  `critique-argument` (Toulmin model). Every criterion carries a permanent ID traceable to its
  source; no stretch skill was held back.
- `critique-critic` subagent (`agents/critique-critic.md`): delegated, clean-context critique that
  refuses authorial framing beyond the artifact itself, runs the named skill's scripted and judged
  lanes, and returns exactly one contract-valid envelope with `tools: [Read, Bash]` (no `Write`, no
  `Edit`: this subagent reports, it never changes the artifact).
- CI pipeline: `.github/workflows/ci.yml` (seven jobs: conformance, unit-python, unit-node, schema,
  corpus, drift, audit), `bench.yml` (`workflow_dispatch`-only, secret-gated, dry-run capable),
  `release.yml` (tag-triggered, version-guarded); `scripts/check-release-versions.mjs` and
  `scripts/lib/version-manifest.mjs` (the single version-bearing-file enumeration);
  `scripts/extract-release-notes.mjs` (the RELEASE-NOTES section extractor for the GitHub release
  body).
- v0.1.0 measurement: 462 envelopes (run set `p3-2026-07-31`, all six skills plus the frozen
  baseline, two pinned model tiers `claude-haiku-4-5-20251001` and `claude-sonnet-5`, k=5) plus 40
  calibration envelopes (run set `cal1-2026-08-01`, `critique-accessibility` 0.1.1 only); at
  location level, `critique-accessibility` (0.1.1) and `critique-clarity` beat the frozen baseline on
  recall at equal-or-better precision on both pinned tiers, `critique-usability` does so on the Haiku
  tier only (its Sonnet cell is a narrow, non-qualifying recall win at a small precision cost); all
  three stretch skills shipped on a recorded baseline win plus the R1 consistency floor (0.309), with
  `critique-docs` shipping on precision dominance at equal recall rather than a recall win. See
  `bench/results/README.md` and `bench/results/verdicts.md`.
- Documentation: `README.md`, `QUICKSTART.md`, the Diataxis `docs/` tree (reference, how-to,
  explanation, tutorials), generated results and skill-catalog tables, `INDEX.md`.
- Examples library: `examples/README.md` indexes nine self-contained pages by task rather than by
  file, six one-skill walkthroughs (`examples/accessibility/`, `argument/`, `clarity/`, `docs/`,
  `microcopy/`, `usability/`, each an artifact plus its `envelope.json` and a human's
  `dispositions.json`) and three cross-cutting recipes (`recipes/gate-in-ci.md`,
  `recipes/revision-loop.md`, `recipes/critic-delegation.md`), explaining once which findings are
  bit-for-bit reproducible (`lane: scripted`) and which are curated from this library's own
  validated golden fixtures (`lane: judged`). Cross-linked from `README.md`'s Examples section and
  `QUICKSTART.md`'s closing pointer.
- Skill-template conformance now runs in CI: `scripts/tests/test_skills_conformance.py` globs
  `skills/critique-*/` and runs `scripts/skill-selftest.py` against each of the six shipped skills
  as a parametrized pytest case, collected automatically by the existing `unit-python` job with no
  workflow edit. Closes S-04's AC-3 ("a template-conformance script validates all six skills
  uniformly in CI"); the spec now records all seven ACs fulfilled. Full suite: 784 tests passing
  (777 prior plus 7 new: one guard test plus six parametrized skill cases).
- Mermaid diagrams, each followed by a plain-text restatement of the same flow: the benchmark
  pipeline, seed and generator version through the corpus, skill and baseline runs, metrics, to
  published tables (`bench/README.md`, "The pipeline, at a glance"); how a scripted-lane finding
  and a judged-lane finding merge into one run envelope (`docs/reference/critique-contract.md`,
  "The two lanes, merged into one envelope"); and the critique, disposition, revise, re-critique
  loop with its three-iteration bound (`examples/recipes/revision-loop.md`).
- `CONTRIBUTING.md`: the Two-Part Gate as the entry test for a new skill, the seven-item review
  order from `docs/explanation/methodology.md` Section 12, the copyright paraphrase policy, and how
  to run the conformance gate and the generated-file regeneration step locally.
- `SECURITY.md`: an inventory of what the repository ships and what it executes, naming the bench
  harness's live-model call as the one network call anything here makes (opt-in, `workflow_dispatch`
  only, never on `push` or `pull_request`), the supply-chain posture (pinned GitHub Actions, zero
  third-party npm runtime dependencies, CI `npm audit` on every push and pull request), and the
  GitHub Private Vulnerability Reporting channel for reports.
- 29 ADRs under `docs/internal/decisions/` recording every material build-run decision, from the
  `critique-` prefix and full-slate scope through the measurement basis, the consistency floor, and
  the accessibility calibration.

### Changed
- `README.md` restructured to the family's badge-and-table-of-contents style: status and
  conformance-tier badges, a collapsible table of contents, a "What this is" comparison table,
  Mermaid flowcharts for "How a critique runs" and the Two-Part Gate, a generated release-history
  table, and a widened "The family" section that now also lists `writing-style-catalog`. The
  conformance-tier claim was updated to match the tree: `node scripts/check.mjs` reports "Tier:
  Convergent (Advanced blocked: 12 issues)" with 0 errors and 0 warnings at the declared tier,
  replacing the prior wording that the plugin "targets Universal tier... with `critique-critic`
  already at Convergent."
- Location-level rescoring added to `bench/results/` (results schema version 1.1.0): recall and
  precision now also compute on location match alone, criterion ID ignored, alongside the original
  criterion-level cut, because the criterion-level baseline comparison is pinned at zero by
  construction and cannot discriminate skill quality. See ADR 0026 (location-level re-examination of
  the baseline gates) in `docs/internal/decisions/`.
- `critique-accessibility` 0.1.1: findings now name the element they are about with its `id` (or a
  bounded CSS selector when it has none) instead of a bare line number, in both the scripted lane
  (`scripts/checks.py`) and the judged lane (`SKILL.md`, "Naming a location"). No criterion was
  added, removed, or weakened. This was the one pre-committed calibration iteration for a core skill
  that had lost its baseline comparison; location recall moved from 0.176/0.306 (haiku/sonnet) to
  0.988/0.965, beating the baseline on both tiers and both metrics, with the 0.1.0 failure published
  alongside the fix. See ADR 0027 (accessibility location-emission calibration) and ADR 0028
  (post-calibration verdict) in `docs/internal/decisions/`.
- `docs/explanation/methodology.md`: corrected two references to an unverified "40-candidate,
  13-domain survey" (Section 2's gate table and Section 13's open questions) to state plainly that
  the domain slate is a provisional working proposal and that a critique-framework survey is a
  tracked v0.2 deliverable, not a document that already exists. See ADR 0029 (methodology survey
  claim: correction, not a scope change) in `docs/internal/decisions/`.

### Fixed
- `release.yml`'s RELEASE-NOTES extraction moved from an inline shell/`awk` verdict computation
  (which the family CI rule forbids) to `scripts/extract-release-notes.mjs`, mirroring how the
  tag-version guard was already delegated to a script.
- `contract/validate_envelopes.py`'s envelope discovery now walks every `bench/results/runs*`
  directory instead of the single hardcoded `bench/results/runs/`, so the calibration run set under
  `bench/results/runs-cal1/` is no longer silently skipped.
- `bench/report.py`'s per-`(domain, model)` comparison cell now keys on `(skill, skill_version)`
  instead of skill name alone, so publishing a recalibrated skill version no longer silently drops
  the prior version's row from the generated comparison table.
