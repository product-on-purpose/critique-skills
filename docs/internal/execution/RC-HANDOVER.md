# RC handover: v0.1.0

**Status:** release candidate on `build/v0.1.0`, last audited at commit `be8f4c1` ("P6 report").
Merge-ready per that audit, with the before-tag items below still open at that commit.

This page carries only what a human needs to review, merge, tag, and publish. For the build-run
narrative, self-audits, and evidence trails behind every claim here, see the phase reports in this
folder, especially [P5 (release-prep finalization report)](P5-report.md) and
[P6 (pre-merge completeness critique)](P6-report.md). Where this page and either report disagree,
the report is correct; this page restates neither in full.

> [!NOTE]
> This branch may carry uncommitted work beyond what P6 audited and beyond this page's own scope.
> Run `git status` and `git diff` before tagging to see what is actually going to ship, and
> reconcile it against the open items below.

## What shipped

- **Six critique skills**, all shipping active, each against a named published standard:
  `critique-clarity` (US Federal Plain Language Guidelines and Williams' *Style*),
  `critique-accessibility` (WCAG 2.2 AA, at v0.1.1 after one calibration pass), and
  `critique-usability` (Nielsen's 10 heuristics, narrow artifact claim: HTML/markdown UI specs, not
  live applications) as the three core skills; `critique-docs` (Diataxis),
  `critique-microcopy` (NN/g error-message guidelines), and `critique-argument` (Toulmin model) as
  the three stretch skills. Every finding carries a permanent criterion ID traceable to its source.
- **`critique-critic`** ([agents/critique-critic.md](../../../agents/critique-critic.md)), the
  clean-context subagent every skill delegates to where a subagent tool is available: `Read` and
  `Bash` tools only, no `Write` or `Edit`.
- **The Critique Contract**
  ([contract/critique-contract.schema.json](../../../contract/critique-contract.schema.json)), the
  finding, run-envelope, and disposition-log shapes, frozen since P1
  ([P1 (critique contract, bench-core, CI pipeline)](P1-report.md)); see
  [ADR 0016 (contract enforcement boundary)](../decisions/0016-contract-enforcement-boundary.md).
- **The benchmark harness** (`bench/`): a deterministic seeded-defect generator, a 23-artifact
  corpus across six domains, 502 committed run envelopes, and `bench/run_bench.py` as the
  reproduction path.
- **Conformance: Silver / Convergent, 0 errors and 0 warnings at the declared tier**
  (`node scripts/check.mjs`); see
  [ADR 0024 (tier backfill: Convergent, critic subagent)](../decisions/0024-tier-backfill-convergent-critic-subagent.md).
- **Docs**: README, QUICKSTART, the Diataxis `docs/` tree, CHANGELOG plus curated RELEASE-NOTES,
  CONTRIBUTING, SECURITY, and 29 ADRs under `docs/internal/decisions/` recording every material
  build-run decision.
- **CI**: `ci.yml` (seven jobs), `bench.yml` (`workflow_dispatch`-only, secret-gated), `release.yml`
  (tag-triggered, version-guarded).

## The honest numbers, first

- **The consistency floor is 0.309** (`critique-clarity` on Haiku, overall lane), replacing the 0.7
  placeholder proposed before any data existed. Judged-lane-only consistency dips as low as 0.150
  (`critique-clarity` on Haiku).
- **Precision is the weak axis**: 0.155 to 0.38 for core skills at criterion level.
- **`critique-usability`'s Sonnet cell does not qualify on its own** (location precision 0.169
  against a baseline of 0.181); the skill ships on its Haiku-tier win.
- **`critique-argument` carries the thinnest stretch margin**: +0.062 over the consistency floor on
  Haiku, small enough that a different set of five runs could move it.
- **The calibration story**: `critique-accessibility` 0.1.0 shipped and then lost to the unrubricked
  baseline on location-level recall on both tiers (0.176 against 0.376 on Haiku, 0.306 against 0.776
  on Sonnet). The cause was a location-formatting defect, not a detection gap; version 0.1.1 fixed
  it and nothing else, moving recall to 0.988 (Haiku) and 0.965 (Sonnet), beating baseline on both
  tiers and both metrics. Both versions stay published side by side, the failure alongside the fix.

Full numbers, unflattering ones first: [bench/results/README.md](../../../bench/results/README.md).
Per-skill ship reasoning: [bench/results/verdicts.md](../../../bench/results/verdicts.md). Curated
narrative: [RELEASE-NOTES.md](../../../RELEASE-NOTES.md).

## Open items by version

Synthesized from P6's "Must know before tagging" and "Open items" sections (P6, above); see that
report for full evidence on each. Items this pass already closed are checked off and kept here only
so the list stays complete.

### Before tag

- [x] **`RELEASE_BODY.md` was not gitignored** (P6 must-know item 3). Closed by this pass: added to
      `.gitignore`.
- [x] **`SECURITY.md` and `CONTRIBUTING.md` carried no pre-release caveat**, even though both point
      readers at `github.com/product-on-purpose/critique-skills` URLs that 404 while the repository
      is private (P6 must-know item 6). Closed by this pass: one callout added to each.
- [x] **`README.md`'s badge row read "status: initial release"**, with the pre-release qualifier
      living only in a callout 13 lines below (P6 must-know item 7). Closed by this pass: the badge
      now reads "pre-release".
- [x] **The RC handover lived only in gitignored `_local/`** and did not travel with the branch (P6
      must-know item 4). Closed by this pass: this document.
- [x] **`CHANGELOG.md` and `RELEASE-NOTES.md` both dated the 0.1.0 section 2026-08-01**, while
      substantive content landed later (P6 must-know item 2). Closed by this pass: both sections
      bumped to match the tag date.
- [ ] **`CHANGELOG.md`'s conformance-tier sentence may still cite a stale above-tier issue count.**
      P6 found it read "12 issues" against an actual `node scripts/check.mjs` result of 4 (must-know
      item 1). Confirm the committed `CHANGELOG.md` matches the live tool output before tagging.
- [ ] **`plan_v0.1.0.md`'s Open Questions table** may still mark R1 (consistency floor), R2
      (usability artifact-type claim), and R3 (baseline model tiers) as `Open`, though all three are
      settled elsewhere (P6 open items, carried from P5). Confirm the committed table reflects that
      before tagging.
- [ ] **`README.md`'s "How a critique runs" diagram** may still lack a plain-text restatement, the
      only one of five new diagrams without one, in a repository shipping `critique-accessibility`
      against WCAG 2.2 AA (P6 finding 3). Confirm the committed README carries one before tagging.
- [ ] **`INDEX.md` links seven paths that do not exist** in this repository (P6 finding 1). Not
      hand-fixable: `INDEX.md` is generated, so the fix belongs in the generator
      (`scripts/gen-index.mjs`) or upstream in the toolkit's own `gen-index` generator, never in
      `INDEX.md` itself.

### Carry to v0.1.x (not tag blockers)

- **`unit-node` (`npm test`) runs zero tests and cannot fail** (P6 finding 2). Either give the Node
  spine (`scripts/lib/version-manifest.mjs`, `check-release-versions.mjs`,
  `extract-release-notes.mjs`) real `*.test.mjs` coverage, or fold the `drift` job's `--check` runs
  into `unit-node` so the job name describes something real.
- **File the upstream `SKIP_DIRS` issue against `agent-skills-toolkit`.** Adding `__pycache__` and
  `.pytest_cache` to `scripts/lib/fs-utils.mjs`'s `SKIP_DIRS` clears three of the four remaining
  above-tier gate issues here, and in every other Python-bearing family plugin.
- **Reconcile `README.md`'s 0.976 accessibility recall figure with `RELEASE-NOTES.md`'s 0.988**, or
  label the README figure as criterion-level so a single before-and-after story does not switch
  metrics mid-paragraph.
- **`.gitattributes` protects only `bench/corpus/**` with `-text`.** `core.autocrlf` converts every
  other text file to CRLF on a fresh Windows clone, which would invalidate the `artifact_sha256`
  values recorded in the 29 `skills/*/examples/golden-*.json` fixtures if anything ever started
  verifying them. Widen the rule before that happens.

### Carry to v0.2

- **Run the two named external validators**, `plugin-dev:plugin-validator` and
  `plugin-dev:skill-reviewer` (release plan phase B5), never run against this release.
- **Measure CI runtime on GitHub-hosted runners** (the CI-pipeline spec's AC-6), impossible before
  the first push.
- **Gold tier**: the `architecture-overview` / `architecture-detailed` doc pair, deliberately out of
  scope for v0.1.0.
- **Label or regenerate golden-envelope run metadata.** Every `skills/*/examples/golden-*.json` and
  `examples/*/envelope.json` carries a `model` and `timestamp` for envelopes that were not produced
  by a live call to that model; either label the `run` block as illustrative or regenerate it from
  real calls.
- **Human acceptance data.** Disposition-based acceptance rate remains unmeasured.
- **`results.json` cannot say which run set an entry came from**, and scoring `bench/results/runs`
  without excluding `runs/steering/` silently changes the `critique-clarity` / Sonnet numbers.

## Publish steps

Nothing below has been done as part of this pass; all of it is a human action.

1. Review the branch, in the order P5 and P6 already establish: contract and severity anchors
   first, results skeptically second, README cold third.
2. Resolve every "before tag" item above, or make a deliberate, recorded decision not to.
3. `git checkout main && git merge build/v0.1.0` (or merge via PR, if you prefer the history).
4. Tag `v0.1.0` (annotated), push branch and tag. This is the first push, so it is also the first
   live run of everything that could previously only be simulated locally: the planted-failure
   check, the scratch-clone tag-version guard, and CI runtime on GitHub-hosted runners.
5. Marketplace re-pin: update the `product-on-purpose/agent-plugins` marketplace entry to the real
   commit SHA on the pushed tag, with `strict: true`.
