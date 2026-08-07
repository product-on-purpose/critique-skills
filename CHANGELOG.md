# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2026-08-07

Everything here comes from asking the runtime a question instead of reasoning about it. No skill behavior changed, no criterion was added, removed, or re-scored, and no run envelope was touched. The measured numbers in `bench/results/` are the v0.1.0 numbers.

### Fixed

- **`agents/README.md` was registering as a live subagent.** Claude Code discovers subagents by scanning `agents/` for `*.md` and loads every one it finds. Loading this repository as a plugin and asking what it had returned `critique-skills:critique-critic, critique-skills:README`: a second subagent, with no name and no description, silently, with no warning or error. A probe plugin pinned down the rule, registering three subagents from a directory holding `real-agent.md`, `README.md`, `_README.md` and `README.txt`; the underscore prefix does not protect a file and only the non-`.md` extension is skipped. The cause was upstream, in the family Standard's `G8` check, which **required** a folder README there, so following the rule produced the defect. Fixed in `agent-skills-toolkit` v1.10.0 and adopted here by bumping `TOOLKIT_REF`; the file is deleted. Its content is not lost: the design rationale it carried moves into `docs/explanation/architecture-detail.md`, along with the rule this taught, which is that `agents/` holds subagent definitions and nothing else.
- **Three of the six skill descriptions could not be told apart on the cases most likely to arrive.** `critique-accessibility` and `critique-usability` both accept HTML and markdown UI artifacts, and neither disclaimed the other, so "check the colour contrast on this landing page" routed to usability. Both now name the other. Found by measurement, not review: the case had been written into the eval fixture as an unambiguous control.

### Added

- **A `smoke` CI job that answers the question no other job asked: does this plugin run for someone who just installed it?** Every other job installs dependencies before it runs anything, so none of them sees what `/plugin install` delivers, which is a git clone and nothing else. That gap shipped the v0.1.1 install crash while 784 tests passed and the conformance gate was clean. `scripts/smoke.py` runs every skill's scripted lane on a real committed artifact and asserts the outcome for the environment: with no dependencies each skill must fail naming the exact install command and printing no traceback, and with them each must emit a usable envelope. Both are asserted, in that order, on one runner, because asserting only the second would have missed the original defect. Confirmed able to fail: against the pre-fix code it fails 6 of 6.
- **The joint-routing eval is scored, not just written.** `scripts/run-joint-routing.py` drives `claude --plugin-dir` so all six descriptions sit in context exactly as they do for a user, then puts one query at a time to a pinned model. Result on sonnet at k=3: **18/18**, with contested 9/9, ambiguous 6/6, control 3/3. Routing turned out to be stochastic, so the runner takes `--k`, scores the modal answer, and reports unanimity per case; a k=1 run is an anecdote, which is the same conclusion `bench/` reached with k=5. Two cases remain non-unanimous, both `critique-microcopy` against `critique-usability`, and both are fixture cases labelled ambiguous, where a split is the correct behavior rather than a failure.
- **ADR 0030 (replace the API key in the bench harness), Accepted.** `claude setup-token` mints a long-lived token from a Claude subscription, so a CI benchmark run can authenticate without an API key, and the acceptance gate ran: a one-skill run through `claude --plugin-dir` produced a contract-valid envelope with findings across both lanes citing real criterion IDs. Recorded with the constraint that `--bare` mode reads only `ANTHROPIC_API_KEY` and never OAuth, and the decision that the frozen baseline condition stays on the API path, because moving it would break comparability with every published figure. The key narrows to one condition rather than disappearing.

### Changed

- **`TOOLKIT_REF` bumped twice**, to `9439699` and then to `cafe6b6`, adopting `agent-skills-toolkit` PRs #189 and #193. Above-tier gate findings went 5 to 0 across those adoptions plus the new architecture pair, and `tier-report` now reports `Convergent (no blockers detected)`, meaning nothing blocks Advanced (Gold). The declared tier stays Convergent; declaring Gold is a commitment to keep meeting it, not a score to claim once.

## [0.1.1] - 2026-08-05

The first release after publication, and the first shaped by evidence from outside this repository.
`critique-skills` went public and was listed in the `product-on-purpose` marketplace on 2026-08-04;
two external validators were then run against the shipped v0.1.0, the first time this library had
been checked by anything it did not write itself. Everything below traces to that, or to closing an
item the RC handover carried.

No skill behavior changed. No criterion was added, removed, or re-scored. No run envelope was
touched. The measured numbers in `bench/results/` are the v0.1.0 numbers, unchanged.

### Fixed

- **A fresh install crashed before reading an artifact.** `contract/validate.py` did a bare
  module-level `import jsonschema`, and every skill's `scripts/checks.py` reaches it through
  `skills/_shared/runner.py` and `gate.py`. Claude Code's `/plugin install` clones a repository and
  does not run `pip`, so on any machine without the package a freshly installed plugin answered
  step 2 of every skill's protocol with a raw `ImportError` traceback and no indication of the
  remedy, which existed only in `QUICKSTART.md`, a file no invoking agent reads. The import is now
  lazy behind `_jsonschema()`, raising `MissingDependencyError` whose message carries the exact
  install command; both CLI boundaries catch it and print that message with no traceback, using the
  exit-code convention every other environment error here already uses (4 under `--gate`, 1
  otherwise). The prerequisite is now stated in each of the six `SKILL.md` protocol blocks and in
  `agents/critique-critic.md`. Found by an external plugin validator, not by 784 passing tests or a
  clean conformance gate: the repository's own tooling structurally cannot see the fresh-install
  path.
- **`agents/critique-critic.md` hardcoded `python`, which does not resolve on stock Linux or
  macOS.** Now `python3`, with a note that neither name is portable alone. The six `SKILL.md` files
  were already interpreter-agnostic; the hardcoding was only in the one subagent every skill
  delegates to.
- **Every recorded example-artifact hash was wrong on any Windows checkout.** `.gitattributes`
  protected only `bench/corpus/**`, so the 25 artifacts hashed into
  `expected_envelope.run.artifact_sha256` were left to git's end-of-line normalization. Measured
  before the fix: 22 of 22 matched the LF form stored in git and 0 matched the bytes on disk. The
  repository was right and every Windows checkout was wrong, and nothing read the hashes, so nothing
  complained. Fixed with `skills/**/examples/** -text` and, more importantly,
  `scripts/tests/test_example_artifact_hashes.py`, which recomputes every recorded hash and reports
  a line-ending mismatch as that specific defect with its remedy. The RC handover had carried this
  as hypothetical.
- **The six skills were not distinguishable at trigger time.** Nothing in the pipeline tested
  cross-skill discrimination: each skill's `evals/triggers.eval.json` is validated in isolation and
  the description scorer is per-skill and mechanical, so neither instrument had a term for "is this
  distinguishable from its five siblings". Three collisions are closed in the descriptions
  themselves, which is where they must be, because a `SKILL.md` body is not read until after a skill
  has already been selected: `critique-argument` and `critique-clarity` both claimed proposals and
  memos; `critique-microcopy` and `critique-usability` both claimed error states; and
  `critique-accessibility` and `critique-docs` both used the literal phrase "heading structure" while
  meaning different things by it.
- **Install-path and security-channel documentation that publication made false.** `README.md`,
  `QUICKSTART.md`, `RELEASE-NOTES.md`, and `SECURITY.md` each stated the repository was private and
  that no install path resolved. GitHub Private Vulnerability Reporting was also enabled, since
  `SECURITY.md` names it the preferred channel and links to a form that 404s with the setting off.

### Added

- **`docs/explanation/architecture.md` and `docs/explanation/architecture-detail.md`**, the
  architecture pair. The overview is the shape: the five parts, how one critique runs end to end,
  and the three things the design structurally refuses to do. The detail page is the reasoning: what
  decides the scripted/judged line, why the contract is frozen, why clean context is a structural
  guarantee, the four measurement choices that carry the weight, why the gate points at another
  repository, and what would count as an architecture change rather than a bug fix.
- **`evals/joint-routing.eval.json`**, 18 queries scored with all six descriptions in view, in three
  kinds: `contested` (a defensible winner plus the sibling it contests), `ambiguous` (no correct
  single winner, where asking is the right behavior), and `control`. Four of the ambiguous cases are
  taken verbatim from the skills' own fixtures, where each is currently asserted as an unambiguous
  positive for a different skill. It is deliberately **not scored in CI**: routing is a model
  decision over descriptions in context, and a lexical proxy would measure string overlap rather
  than routing, which is exactly the kind of number this library exists not to publish.
  `scripts/tests/test_joint_routing_eval.py` enforces what can be checked deterministically.
- **`docs/internal/execution/P3-cal1-provenance.md`**, closing an item `bench/results/README.md`,
  `P3-cal1-report.md`, and ADR 0028 all carried as open. It is explicit that it does not reach
  `P3-provenance.md`'s standard, because it was written four days later by a session that was not
  present for the runs. It corrects the round-number timestamp count from six to nine and records
  two anomalies not previously noted: ten envelopes timestamped a day before the calibration date
  the manifest records, and one envelope recording the staging path rather than the corpus path.
  What it cannot establish is listed under "Not established" rather than inferred.

### Changed

- **`TOOLKIT_REF` bumped `6cfd68b` to `9439699`** in `ci.yml` and `release.yml`, adopting
  `agent-skills-toolkit` PR #189. That PR fixed two defects in the grader that were producing four
  of this repository's five above-tier findings: `SKIP_DIRS` covered the Node ecosystem's scratch
  directories and not Python's, so the folder-README check walked into `__pycache__`; and
  `gen-index`'s two boilerplate sections were hardcoded to the toolkit's own repository layout and
  emitted seven links to paths that do not exist here. Verified before bumping: the patched
  toolkit's raw `INDEX.md` output is byte-identical to the committed one.
- **Above-tier gate findings 5 to 0.** `tier-report` now reports `Convergent (no blockers
  detected)`, meaning nothing blocks Advanced (Gold). The declared tier is unchanged at Convergent
  (Silver); declaring Gold is a separate decision with its own ongoing commitments.

## [0.1.0] - 2026-08-03

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
  conformance-tier claim was updated to match the tree: `node scripts/check.mjs` reports tier
  Convergent, with 0 errors and 0 warnings at the declared tier, replacing the prior wording that
  the plugin "targets Universal tier... with `critique-critic` already at Convergent."
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
