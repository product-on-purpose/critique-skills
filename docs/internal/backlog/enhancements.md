# Enhancement backlog

> Features, fixes, and refinements to existing components (Standard sec 7.1). Each item references
> the target component and describes the change. Proposals to ADD a component live in
> [new-components.md](new-components.md) instead. Items are recorded by hand.

## How to read this file

- **The ID is an intake number, not a priority.** `E7` was recorded seventh. What it costs to defer
  is the `Rank at intake` line and the release tag; re-ranking an item never renumbers it, because
  other documents cite the ID.
- **Always pair an ID with its handle.** Write "E2 (sonnet unblock)", never a bare "E2". Every
  heading below carries a handle for exactly this purpose.
- **Every item cites evidence you can open.** An item whose evidence does not support it is a
  defect in this file, not a judgement call. `Confidence: verified` means someone read the cited
  file and the gap was present on 2026-09-11; `likely` means strong indirect evidence; `speculative`
  means a judgement worth the maintainer seeing, not a finding.
- **Release tags below the v0.1.x line are provisional** until [E1 (the v0.2.0 shape ruling)](#e1---rule-the-v020-shape-pick-one-of-the-four-options)
  is made. They currently follow Option A (receipts first). Picking B or C moves them.
- **Nothing here is a commitment.** The backlog is what is known to be undone. `ROADMAP.md` is what
  the project has said in public it will do, and the two are deliberately not the same document.

## Intake: backlog expansion, 2026-09-11

Every item below entered in one pass on 2026-09-11. Eight scoped audits swept independent evidence
surfaces (the public roadmap and README claims; all 33 ADRs; the benchmark and its measurement debt;
CI, the contract and conformance; the site and the Diataxis tree; the six skills and the criterion
registry; seven session logs plus the external audit and the pre-build planning archive; and a
mechanical code-marker sweep), producing 81 raw candidates. Deduplication across surfaces collapsed
those to 64, of which 60 are enhancements and 4 are new-component proposals. A completeness critic
then re-opened the cited files, spot-checked citations against the repository, and its corrections
are carried inline as `Review note` lines.

Before this pass the project's open work lived in three places with different lifespans: `ROADMAP.md`
(version-scoped intentions), `docs/internal/execution/RC-HANDOVER.md` (frozen at the v0.1.0 tag, and
over half its list had closed without anyone striking it through), and the live maintainer decisions,
which survived five sessions only by being retyped by hand into each continuation prompt. The
GitHub issue tracker held zero issues. This file is the durable home the Standard already specified
and the repository did not have.

---

## E1 - Rule the v0.2.0 shape: pick one of the four options

- **Target:** `ROADMAP.md`, `docs/internal/release-plans`, `_local/_session-logs/2026-09-11_20-18_claude_w8-merge-and-the-fidelity-gate-receipts.md`
- **Change:** Known decision 5, blocked since 2026-08-08. Pick Option A, B, C or D from [the v0.2.0 shape options brief](../release-plans/v0.2.0-shape-options.md); each names its items, exit gate and cost. Done looks like a dated ruling recorded in a committed document (an ADR or a ROADMAP.md edit), not a session log, naming the shape, the release tags it implies for E44, E45, E46, E47, E48, N1, N2 and N3, and the ruling on E11.
- **Why:** 35 days blocked; every L and XL item in this backlog is unordered until it is ruled, the sonnet-fix decision has stayed unmade partly because its payoff is v0.2.0 content of unknown shape, and RELEASE-NOTES.md still says 'Nothing yet' over 35 unreleased bullets.
- **Evidence:** ROADMAP.md:44-70; docs/internal/release-plans/ (only plan_v0.1.0/ present, no plan_v0.2.0/); _local/_session-logs/2026-09-11_20-18_claude_w8-merge-and-the-fidelity-gate-receipts.md:140,183; RELEASE-NOTES.md:5-7
- **Derives from:** The five live maintainer decisions (decision 5); ROADMAP.md 'Then: v0.2.0'
- **Size:** S. **Release:** v0.2.0. **Category:** decision. **Confidence:** verified.
- **Blocks:** E11, E12, E44, E45, E47, E48, N1, N2 and N3 and every v0.2.0 release tag
- **Depends on:** Nothing; E10 informs the choice between A and B but does not gate the ruling
- **RULED 2026-09-11: v0.2.0 is Option A plus Option C** (receipts first, plus the research
  spine). E44 (taxonomy survey) and N1 (critique-deck) move into v0.2.0; N3 (critique-dataviz)
  moves out of any numbered release and is held unscheduled in the backlog, which is what makes
  the exit gate closable. Recorded in
  [the v0.2.0 shape options brief](../release-plans/v0.2.0-shape-options.md).
- **Not discharged by the ruling:** the three riders. E11 (the askit and CodeQL commitments) still
  needs an explicit cut-or-schedule, E12 (re-cut the published exit gate) still needs the edit,
  and E14 (the v0.1.x exit-gate declaration) still comes first.
- **Rank at intake:** 1 of 64. **Status:** RULED 2026-09-11; the three riders remain open.

## E2 - Unblock sonnet cells: RESOLVED, sonnet was already working

- **Target:** `bench/run_bench.py`, `CHANGELOG.md`, `bench/tests/test_run_bench.py`
- **Change:** PARTIALLY DONE 2026-09-11. `--timeout` shipped: the 900-second ceiling was hardcoded at two sites with no way to raise it for a slower tier, and is now `DEFAULT_TIMEOUT_SECONDS` with a `--timeout` CLI override threaded through `_client_factory`, covered by four new tests. **The path fix was NOT applied, because the recorded diagnosis is wrong.** Remaining: capture a fresh post-v0.1.6 sonnet trace, identify the actual failure, fix it, and complete one sonnet cell through `bench.yml`.
- **Why:** Cheapest item with the largest unblock: the sonnet tier has never produced an envelope through the rewritten harness, and the usability re-measure, consistency v2, the sonnet fidelity gate and any new skill's two-tier measurement all queue behind it.
- **Evidence:** bench/run_bench.py:619; bench/run_bench.py:494 and :586 (timeout: int = 900); bench/run_bench.py:955-999 (_build_arg_parser, no --timeout option); CHANGELOG.md v0.1.6 entry describing the find / -maxdepth 6 -iname hang; bench/tests/test_run_bench.py grep for staged_path.name found no hits; docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md (Amendment, 2026-08-16: hard-coded 900 second ceiling, no CLI flag to raise it)
- **Derives from:** Known decision 3 (the sonnet fix); ADR 0030 (replace the API key in the bench harness); ADR 0031 (fidelity gate acceptance band)
- **Size:** S. **Release:** v0.1.x. **Category:** measurement. **Confidence:** verified.
- **Blocks:** E19, E20 and E26; two-tier k=5 measurement of N1, N2 and N3
- **Depends on:** A fresh sonnet trace, which costs a live run
- **Correction 2026-09-11, with evidence.** The recorded one-line fix (`staged_path.name` to
  `staged_path` at `bench/run_bench.py:619`) targets the **artifact** reference. The 2026-08-16
  trace at `_local/sonnet-tier/sonnet-diagnostic-2026-08-16.txt` shows the artifact resolved
  correctly at +10.0s (`tool_result: ./clarity-001.md`). What the run then spent about 120 of its
  130 seconds on was hunting for the **plugin root**, searching for `Projects` and then
  `*critique-skills*` across two drives, before reading `SKILL.md` from the real repository at
  +129.2s and being killed. The artifact was never the failure.
- **Why the change was not made anyway.** Two reasons. `bench/run_bench.py:615-617` states the
  bare filename is deliberate, and `staged_artifact()` is the actual isolation mechanism.
  More decisively, the artifact name is interpolated into `_SKILL_RUN_INSTRUCTION`, so changing
  it **changes the prompt for every cell the committed evidence was measured with**. The comment
  directly below it makes exactly that argument about `severity_3_threshold`. That is a
  measurement decision needing an ADR, not a bug fix. A test now pins the current behaviour so it
  cannot change quietly.
- **What is actually known.** `agents/critique-critic.md:29-40` requires an absolute `skill_dir`
  and names searching for it as the failure mode, citing this same 2026-08-16 measurement.
  `skills/critique-clarity/SKILL.md:156-160` ("The skill directory is not optional") was the
  v0.1.6 prose fix for it. But `RELEASE-NOTES.md`'s 0.1.6 entry says the expensive tier still
  "hits a second version of the same searching problem, **in a different place**". No trace of
  that post-fix failure exists in the repository, so the current root cause is genuinely
  unidentified and cannot be inferred from the pre-fix trace.
- **RESOLVED 2026-09-13, by running it rather than by changing anything.** One cell,
  `critique-clarity` / `clarity-001` / sonnet (`claude-sonnet-5`, the pinned tier), k=1, against a
  single-artifact scratch corpus. **It completed**, producing a schema-valid envelope (0 errors
  against the frozen contract) with 5 scripted and 3 judged findings.
- **The two numbers that settle the diagnosis.** The scripted count is non-zero, so the skill
  resolved its own `scripts/checks.py` instead of searching for it: the plugin-hunting failure is
  gone. And it took **639 seconds, inside the 900-second ceiling that was already in force**, so
  the `--timeout` flag shipped earlier the same day is **not** what unblocked it. Neither recorded
  cause was the cause.
- **What most likely fixed it:** v0.1.6's change giving the critic subagent its own `skill_dir`
  (`skills/critique-clarity/SKILL.md:156-160`). Sonnet was never re-run after that shipped, so the
  "still cannot complete a cell" claim propagated into `bench/results/README.md`, ADR 0031 and the
  changelog on the authority of a pre-fix trace. **The tier was working for roughly four weeks and
  nobody knew.**
- **Scope, stated at the same length.** One skill, one artifact, one repetition. It says nothing
  about the other five skills, the other three clarity artifacts, or any published figure. The
  envelope is a diagnostic probe, not a measurement, and is not committed into any run set.
- **Follow-on:** `bench/results/README.md` corrected. `RELEASE-NOTES.md`'s 0.1.6 section and ADR
  0031 still carry the old claim and were deliberately left alone as dated records. E19 (fidelity
  gate on sonnet) and E20 (usability sonnet re-measure) are now genuinely unblocked.
- **Rank at intake:** 2 of 64. **Status:** RESOLVED 2026-09-13.

## E3 - Regenerate README/ROADMAP stale receipts (541 envelopes, 907/126 tests) and guard them

- **Target:** `README.md`, `ROADMAP.md`, `CHANGELOG.md`
- **Change:** README.md's badge and body say 502 run envelopes and its Fast-facts table says 902 Python / 111 Node tests; ROADMAP.md:21 says 502. Main already holds 541 valid envelopes and the suites pass 907 and 126. None of the four figures is covered by a generator or check. Done: figures corrected and either generated from the validator/test output or covered by a drift check the way the scoreboard marker already is.
- **Why:** Two badge-level numbers are wrong on main right now in the document that invites readers to 'Decide whether to believe it', with no mechanism to catch the next drift.
- **Evidence:** README.md:16,27,186,301; ROADMAP.md:21; the commit body for 8950878 (`git log -1 --format=%B 8950878`), which is where '541 valid, up from 502' actually appears; it is NOT in CHANGELOG.md; scripts/gen-readme-catalog.mjs (only regenerates the skill-catalog table, not badges or the status table); scripts/check-readme-links.mjs (full read, checks only site-link resolution and door/card label parity); scripts/check-release-versions.mjs:1-40 (checks only semver fields via scripts/lib/version-manifest.mjs); verified by running python -m pytest -q (907 passed) and node --test scripts/tests/*.mjs (126 passed)
- **Derives from:** Stale claim surfaced by comparing README.md/ROADMAP.md against verified current state and CHANGELOG.md
- **Size:** S. **Release:** v0.1.x. **Category:** docs. **Confidence:** verified.
- **Blocks:** Nothing; should land before the next release is cut
- **Depends on:** Nothing
- **Review note:** The critic corrected this item's citation. The figures '541 valid, up from 502'
  were originally attributed to `CHANGELOG.md`, which does not contain them; they are in the commit
  body for `8950878`. The underlying finding was independently reproduced (`python -m
  contract.validate_envelopes` returns 541; the suites return 907 and 126).
- **Rank at intake:** 3 of 64. **Status:** backlog (recorded 2026-09-11).

## E4 - Fix the two false claims in the published benchmark-harness explainer

- **Target:** `docs/explanation/the-benchmark-harness.md`, `bench/run_bench.py`, `bench/results/README.md`
- **Change:** docs/explanation/the-benchmark-harness.md, served on the live site, still says the harness has never been run live and that the judged lane is a prompt the harness assembles. Run 31988100372 dispatched through bench.yml on 2026-08-17 with 39 committed envelopes, and run_bench.py's own docstring says it runs the real skill. Done: both passages rewritten against the current harness and CHANGELOG.
- **Why:** The page exists to establish the harness's credibility as a prove-it mechanism and currently contradicts the repository's own commit history on the live site.
- **Evidence:** docs/explanation/the-benchmark-harness.md:107, 156-157; bench/run_bench.py:12-20 module docstring; bench/results/README.md Provenance section (that dispatch has since happened); CHANGELOG.md Unreleased Added first bullet, run 31988100372
- **Derives from:** Verified by cross-reading the doc against run_bench.py's docstring, CHANGELOG.md, and bench/results/README.md
- **Size:** S. **Release:** v0.1.x. **Category:** docs. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 4 of 64. **Status:** backlog (recorded 2026-09-11).

## E5 - Retire fabricated run metadata across all 31 example and golden envelopes

- **Target:** `skills/critique-accessibility/examples/golden-01..05.json`, `skills/critique-argument/examples/golden-01..03.json`, `skills/critique-clarity/examples/golden-01..04.json`
- **Change:** RC-HANDOVER tracks six examples/*/envelope.json files; the skills audit read all 25 skills/*/examples/golden-*.json plus the 3 toy fixtures and found 17 declaring claude-sonnet-4-5-20250929 (not a pinned tier) and the rest carrying hand-authored timestamps, while examples/README.md:17-30 tells the reader no judged call was ever made live. Two halves: (a) regenerate the 8-11 scripted-only files now by re-running each skill's scripts/checks.py (free, deterministic, model stays 'none'); (b) define an illustrative-run sentinel (schema-legal today, modelId is free-form) and relabel the 17 judged-lane files, then add a check that no run.model outside the pinned tiers or the sentinel exists under skills/ or examples/. Also correct RC-HANDOVER.md:116's '29 fixtures' to 25.
- **Why:** This is the file set most likely to be checked first against the receipts pitch, the tracked count undercounts the real set by 25 files, and the machine-readable fields contradict the adjacent prose disclosure.
- **Evidence:** skills/critique-accessibility/examples/golden-01..05.json; skills/critique-argument/examples/golden-01..03.json; skills/critique-clarity/examples/golden-01..04.json; skills/critique-docs/examples/golden-01..04.json; skills/critique-microcopy/examples/golden-01..03.json; skills/critique-usability/examples/golden-01..03.json; skills/_template-fixture/critique-toy/examples/golden-01..03.json; examples/clarity/envelope.json; docs/internal/decisions/0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md:44-45; docs/internal/execution/RC-HANDOVER.md:127-130; docs/internal/execution/RC-HANDOVER.md:116; examples/README.md:17-30; contract/critique-contract.schema.json:489-495
- **Derives from:** RC-HANDOVER.md 'Carry to v0.2' item 'Label or regenerate golden-envelope run metadata'; ROADMAP.md v0.2.0 E7's honest-provenance principle
- **Size:** M. **Release:** v0.2.0. **Category:** contract. **Confidence:** verified.
- **Blocks:** Nothing downstream; load-bearing for the receipts argument
- **Depends on:** Half (a) nothing; half (b) the sentinel decision, which is part of this item
- **Rank at intake:** 5 of 64. **Status:** backlog (recorded 2026-09-11).

## E6 - Add per-entry run_set and a lane dimension to results.schema.json (v1.2.0)

- **Target:** `bench/results/results.schema.json`, `bench/metrics/__main__.py`, `bench/results/README.md`
- **Change:** results.schema.json carries one file-level run_set and an entry object with additionalProperties false; today's results.json already pools two run sets distinguishable only by skill_version, and the judged/scripted cuts in bench/results/README.md and verdicts.md are hand-derived outside the schema. Done: a minor schema bump with optional per-entry run_set and a lane enum, build_results stamping both, and report.py drift-checking the lane columns like every other number.
- **Why:** RC-HANDOVER confirmed-open defect and a named v0.2.0 measurement-debt item; CHANGELOG.md:71 records bench.variance already having to reverse-engineer grouping from filenames because the field does not exist.
- **Evidence:** bench/results/results.schema.json:7-35 file-level run_set, :39-131 entry required fields; bench/metrics/__main__.py:122,201,225,235-237 single run_set threaded through build_results and the --run-set flag; bench/results/README.md:742-759 Judged-lane figures are derived, and :837-843 results.json cannot say which run set an entry came from; ROADMAP.md:58 (measurement debt bullet 1); CHANGELOG.md:71 ('the run_set and lane schema debt ROADMAP.md already lists')
- **Derives from:** ROADMAP.md v0.2.0 E4, sub-E1; RC-HANDOVER confirmed-open item
- **Size:** M. **Release:** v0.2.0. **Category:** contract. **Confidence:** verified.
- **Blocks:** Publishing judged and scripted cuts as committed, drift-checked numbers
- **Depends on:** Nothing
- **Rank at intake:** 6 of 64. **Status:** backlog (recorded 2026-09-11).

## E7 - Move bench/results/runs/steering/ out of the runs* glob

- **Target:** `bench/results/runs/steering/clarity-001`, `bench/results/README.md`, `bench/README.md`
- **Change:** The steering probe set sits inside the scored grid directory; only a manual rm -rf step in the reproduction recipe keeps it out, and bench/results/README.md's own Known issues section names the fix it never applied (a separate top-level directory for probe run sets). Done: the directory relocated, the recipe and layout doc updated, validate_envelopes and report still passing.
- **Why:** RC-HANDOVER confirmed-open defect with a documented consequence: scoring runs/ directly inflates critique-clarity/sonnet from 20 scored runs to 22 and 40 consistency pairs to 51.
- **Evidence:** bench/results/runs/steering/clarity-001/ (steer-r1.json, steer-r2.json on disk); bench/results/README.md:828-832; bench/README.md:56-58 Layout section
- **Derives from:** RC-HANDOVER confirmed-open item on steering skewing scoring, extended to the fix the project's own doc names
- **Size:** S. **Release:** v0.1.x. **Category:** measurement. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing (independent of E6; both close the same footgun)
- **Rank at intake:** 7 of 64. **Status:** backlog (recorded 2026-09-11).

## E8 - Retire methodology.md's stale 0.7 consistency-target placeholder

- **Target:** `docs/explanation/methodology.md`, `docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md`, `docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md`
- **Change:** docs/explanation/methodology.md Section 8 and Section 13 still say the 0.7 target is a placeholder awaiting baseline data. ADR 0022 (consistency floor: overall lane-min core) set the empirical 0.309 floor on 2026-07-31 and both ADR 0022 and ADR 0026 flagged this update as owed. Done: both passages replaced with the 0.309 floor, its ADR, and a pointer to the consistency-v2 item.
- **Why:** Three surfaces found it independently; the page actively misstates a resolved, load-bearing release gate as unresolved five weeks after it was set.
- **Evidence:** docs/explanation/methodology.md:281 placeholder language, :372 no empirical basis yet; docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md:97; docs/internal/decisions/0026-location-level-re-examination-of-baseline-gates.md:116; bench/results/README.md and verdicts.md repeatedly citing floor 0.309, ADR 0022 as the live gate
- **Derives from:** ADR 0022, ADR 0026, ROADMAP.md v0.2.0 E5
- **Size:** S. **Release:** v0.1.x. **Category:** docs. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 8 of 64. **Status:** backlog (recorded 2026-09-11).

## E9 - Delete the stale validate_envelopes known-issue from bench/results/README.md

- **Target:** `bench/results/README.md`, `contract/validate_envelopes.py`, `.github/workflows/ci.yml`
- **Change:** The Known issues section still says contract/validate_envelopes.py's glob is one level too shallow and the schema job is not exercising the envelopes. The glob was fixed in commit 1b7beb3 (2026-08-01), the validator reports 541 files valid, and ci.yml's schema job calls it. Done: the bullet removed or marked resolved with the commit.
- **Why:** A skeptical reader checking this specific claim finds the primary results document wrong about its own validator; one-paragraph fix.
- **Evidence:** bench/results/README.md:821-827; contract/validate_envelopes.py current source (RUNS_DIR, discover_run_roots, RUN_ROOT_GLOB); git show 1b7beb3 -- contract/validate_envelopes.py; python -m contract.validate_envelopes output 541 file(s) valid; .github/workflows/ci.yml:143-166 schema job
- **Derives from:** Verified by direct command execution plus git history
- **Size:** S. **Release:** v0.1.x. **Category:** docs. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 9 of 64. **Status:** backlog (recorded 2026-09-11).

## E10 - Rule how BYOR is measured under the measured-only exclusion

- **Target:** `ROADMAP.md`, `docs/explanation/methodology.md`, `docs/internal/skill-template.md`
- **Change:** ROADMAP.md:113 says any skill that cannot be measured against ground truth does not ship, and the v0.2.0 exit gate requires every new component measured to the v0.1.0 bar; BYOR criteria are supplied at run time and cannot be seeded into a criterion-ID-keyed corpus. No ADR, spec or roadmap passage says whether BYOR counts as a component under that clause. Done: a recorded ruling (measured how, or exempt why) before BYOR opens.
- **Why:** Needed to size Option B honestly; without it BYOR either violates the project's own stated rule or requires a rule amendment nobody has made.
- **Evidence:** ROADMAP.md 'Deliberately not doing' section ('Any skill that cannot be measured'); ROADMAP.md v0.2.0 exit-gate line ('every new component in this version built and measured to the same bar as v0.1.0'); docs/explanation/methodology.md section 3 (Bring Your Own Rubric); docs/internal/skill-template.md 'Corpus-module obligation' section; grep of docs/internal/decisions/*.md for byor (0013, 0016, plus the S-02/S-04/S-05 specs, none addressing measurement)
- **Derives from:** Tension between ROADMAP.md's v0.2.0 exit gate, its BYOR E3, and its 'Deliberately not doing' section
- **Size:** M. **Release:** v0.2.0. **Category:** decision. **Confidence:** speculative.
- **Blocks:** E45; the honesty of Option B
- **Depends on:** Nothing; it is itself a prerequisite decision
- **Rank at intake:** 10 of 64. **Status:** backlog (recorded 2026-09-11).

## E11 - Rule on the two v0.2.0 commitments that vanished: askit-* authoring and CodeQL

- **Target:** `_local/_session-logs/2026-08-04_08-27_claude-opus-5_critique-skills-v0.1.0-build-and-release.md`, `_local/initial-plan/02-roadmap.md`, `_local/initial-plan/04-ci-plan.md`
- **Change:** The local plan made every new v0.2.0 component buildable through an agent-skills-toolkit askit-* authoring skill (E9 of _local/initial-plan/02-roadmap.md, with its own exit-gate clause) and scheduled CodeQL for v0.2 in both 04-ci-plan.md and S-07 (CI pipeline spec) Non-Goals. Neither appears in the public ROADMAP.md and no record cuts them. Done: a recorded adopt-or-drop ruling for each, plus a one-pass sweep of the local plans for any other v0.2.0-v0.4.0 line item that failed the same transition.
- **Why:** Whichever shape wins, new components start being authored immediately; once built by hand or without a CodeQL workflow, both commitments become impossible to honor retroactively.
- **Evidence:** _local/_session-logs/2026-08-04_08-27_claude-opus-5_critique-skills-v0.1.0-build-and-release.md:57,116-127,163-169; _local/initial-plan/02-roadmap.md:48-58; _local/initial-plan/04-ci-plan.md (Secrets and supply chain section, 'CodeQL adoption follows the family pattern in v0.2'); _local/initial-plan/specs/S-07_ci-pipeline/spec.md:36 (Non-Goals: 'CodeQL (v0.2)'); ROADMAP.md:44-70 (no mention of either item); no hits for 'askit' or 'codeql' anywhere in ROADMAP.md or CHANGELOG.md
- **Derives from:** 2026-08-04 session log decision 'agent-skills-toolkit dogfooding deferred to v0.2' + local roadmap E9 + S-07 spec Non-Goals
- **Size:** S. **Release:** v0.2.0. **Category:** decision. **Confidence:** verified.
- **Blocks:** E12; a defensible v0.2.0 exit-gate declaration
- **Depends on:** E1
- **Rank at intake:** 11 of 64. **Status:** backlog (recorded 2026-09-11).

## E12 - Re-cut the v0.2.0 exit gate to match the shape ruling

- **Target:** `ROADMAP.md`
- **Change:** ROADMAP.md:70 transitively requires all three second-wave skills, including the XL dataviz item, before v0.2.0 can close. Done: the exit-gate sentence and the v0.2.0/v0.3.0/v0.4.0+ item lists rewritten to the ruled shape, with the overtaken-item note pattern ROADMAP.md:66 already uses.
- **Why:** Without it the document silently commits to the all-eight-items scope regardless of what was ruled.
- **Evidence:** ROADMAP.md:70 (the exit gate sentence); ROADMAP.md:48-64 (the 8 items it spans); ROADMAP.md:66 (the overtaken-item note pattern)
- **Derives from:** Sub-task hanging off known decision 5
- **Size:** S. **Release:** v0.2.0. **Category:** docs. **Confidence:** likely.
- **Blocks:** Any tagging of v0.2.0
- **Depends on:** E1 and E11
- **Rank at intake:** 12 of 64. **Status:** backlog (recorded 2026-09-11).

## E13 - Update ROADMAP.md's v0.1.x section: two of four verification items are met

- **Target:** `ROADMAP.md`, `docs/internal/release-plans/plan_v0.1.0/S-07_ci-pipeline/spec.md`, `CHANGELOG.md`
- **Change:** The 'Next: v0.1.x' list shows all four verification items as open. CI runtime is measured at 34 seconds and the first live bench.yml dispatch happened (CHANGELOG says it discharged that commitment). Done: those two struck through with dates in the pattern ROADMAP.md:70 already uses, the other two (E15 and E16) left visibly open.
- **Why:** Sub-task of known decision 4: the section that should settle whether the exit gate is honestly met currently reads 4 of 4 open when it is 2 of 4.
- **Evidence:** ROADMAP.md:27-40; ROADMAP.md:33-35 (the four items, none marked complete); ROADMAP.md:70 (the strikethrough pattern used for the site item); docs/internal/release-plans/plan_v0.1.0/S-07_ci-pipeline/spec.md:22-40 (AC-1, AC-4, AC-6 unchecked with reasoning); CHANGELOG.md [Unreleased] 'Added' entry (fidelity-gate run 31988100372, 'discharging the ROADMAP.md v0.1.x commitment to a live run')
- **Derives from:** ROADMAP.md 'Next: v0.1.x' section; S-07 (CI pipeline spec) AC-1 / AC-4
- **Size:** S. **Release:** v0.1.x. **Category:** docs. **Confidence:** verified.
- **Blocks:** An honest v0.1.x exit-gate declaration (decision 4), which per ROADMAP.md:9 gates v0.2.0 opening
- **Depends on:** Nothing
- **Rank at intake:** 13 of 64. **Status:** backlog (recorded 2026-09-11).

## E14 - Rule whether a site-guard defect resets the v0.1.x exit-gate clock

- **Target:** `.memsearch/memory/2026-08-26.md`, `_local/_session-logs/2026-09-11_20-18_claude_w8-merge-and-the-fidelity-gate-receipts.md`, `ROADMAP.md`
- **Change:** The gate reads 'two consecutive weeks with no open contract or check defect'; the edit-link guard bug (found and fixed 2026-08-22) is a check defect in the broad reading and not in the narrow one, which moves the earliest opening between 2026-08-31 and 2026-09-05. The 2026-09-11 declaration takes the narrow reading without saying so. Done: one sentence in ROADMAP.md defining 'check defect' as contract and plugin gates, or the broad reading with the later date.
- **Why:** Sub-task of known decision 4: the declaration rests on an unstated interpretive choice in a repo whose standard is to state such choices.
- **Evidence:** .memsearch/memory/2026-08-26.md:8-9 (the question raised and escalated); _local/_session-logs/2026-09-11_20-18_claude_w8-merge-and-the-fidelity-gate-receipts.md:140,183 (the declaration, silent on the question); ROADMAP.md:40 ('two consecutive weeks with no open contract or check defect', still undefined)
- **Derives from:** 2026-08-26 session, decision #2 in a nine-item decision walkthrough
- **Size:** S. **Release:** v0.1.x. **Category:** decision. **Confidence:** likely.
- **Blocks:** Nothing further; the declaration it gated is made.
- **Depends on:** Nothing
- **CLOSED 2026-09-13** by [ADR 0034 (the v0.1.x exit gate is met, and what it does not say)](../decisions/0034-v0.1.x-exit-gate-declaration.md).
  Ruled: **a site-guard defect does count** as a check defect and does reset the clock. The gate
  says "check defect" without qualification and a site guard is a check. Ruled while the answer
  was still free, since every candidate clock start clears two weeks: 2026-08-16 (28 days),
  2026-08-22, the site-guard defect (22 days), and 2026-08-25, when `main` first had branch
  protection at all (19 days). The gate requires 14.
- **What the same ADR declined to declare:** that v0.1.x is finished. E15 and E16, two of the four
  verification items the version is named for, have never been run. The clause measures quiet;
  it does not measure completion.
- **Rank at intake:** 14 of 64. **Status:** CLOSED 2026-09-13.

## E15 - Exercise the tag-guard's negative path from a scratch clone (S-07 AC-4)

- **Target:** `ROADMAP.md`, `CHANGELOG.md`, `docs/internal/execution/P6-report.md`
- **Change:** release.yml's version guard has run live on six tagged releases (positive path only); the only mismatched-tag test is local (GITHUB_REF_NAME=v9.9.9 in P4-report). S-07 (CI pipeline spec) AC-4 (tag-guard from a scratch clone) is still unchecked. Done: one scratch clone, one deliberately mismatched tag, the guard failing on live infrastructure, and the AC checked with the run URL.
- **Why:** Three surfaces independently flagged it as the cheaper of the two open v0.1.x verification items; one scratch-repo test closes it.
- **Evidence:** ROADMAP.md:34; CHANGELOG.md:292 (release.yml tag-triggered, version-guarded); docs/internal/execution/P6-report.md:358 ('release.yml runs it on a throwaway checkout'); docs/internal/execution/P4-report.md:141-143 (only a local mismatch test, not a live one); _local/initial-plan/specs/S-07_ci-pipeline/spec.md:22,56,59; .memsearch/memory/2026-08-25.md:33-37
- **Derives from:** ROADMAP.md v0.1.x E2; S-07 (CI pipeline spec) AC-4
- **Size:** S. **Release:** v0.1.x. **Category:** ci. **Confidence:** likely.
- **Blocks:** Declaring the v0.1.x exit gate fully met with all four sub-items closed
- **Depends on:** Nothing
- **Rank at intake:** 15 of 64. **Status:** backlog (recorded 2026-09-11).

## E16 - Run the live planted-failure checks on GitHub Actions (S-07 AC-1)

- **Target:** `ROADMAP.md`, `docs/internal/execution/P4-report.md`, `CHANGELOG.md`
- **Change:** Each CI job that should fail on bad input needs to actually fail on GitHub infrastructure; the only evidence is seven planted failures failing locally (P4-report) and a 2026-08-25 review counting 1 of 9 categories tested live. Done: a throwaway branch per remaining job category, each run failing on Actions, the AC checked with run URLs.
- **Why:** Three surfaces flagged it; it is the one v0.1.x verification item with no evidence of ever running on real infrastructure, and it directly gates decision 4.
- **Evidence:** ROADMAP.md:33; docs/internal/execution/P4-report.md:134 ('all seven planted failures failed locally and reverted'); CHANGELOG.md (no entry mentioning a live planted-failure run); _local/initial-plan/specs/S-07_ci-pipeline/spec.md:22,56,59; .memsearch/memory/2026-08-25.md:33-37 (1-of-9 and not-started status)
- **Derives from:** ROADMAP.md v0.1.x E1; S-07 (CI pipeline spec) AC-1
- **Size:** M. **Release:** v0.1.x. **Category:** ci. **Confidence:** likely.
- **Blocks:** Declaring the v0.1.x exit gate fully met with all four sub-items closed
- **Depends on:** Nothing
- **Rank at intake:** 16 of 64. **Status:** backlog (recorded 2026-09-11).

## E17 - Write RELEASE-NOTES.md's Unreleased section and pick the release that absorbs it

- **Target:** `RELEASE-NOTES.md`, `CHANGELOG.md`
- **Change:** RELEASE-NOTES.md says 'Nothing yet' while CHANGELOG.md [Unreleased] carries roughly 35 bullets (fidelity gate's first live result, aggregate CI gate, README Concept C, the site going live). Done: curated notes written and a decision on whether they ship as v0.1.7 or as part of v0.2.0.
- **Why:** Sub-task of decision 4: 'Nothing yet' is verifiably false today and no release can be cut without it.
- **Evidence:** RELEASE-NOTES.md:5-7 ('## Unreleased' followed by 'Nothing yet.'); CHANGELOG.md's [Unreleased] section (approximately 35 bullets, most recent commit 8950878)
- **Derives from:** Stale claim surfaced by comparing RELEASE-NOTES.md against CHANGELOG.md
- **Size:** S. **Release:** v0.1.x. **Category:** docs. **Confidence:** verified.
- **Blocks:** Cutting the next release
- **Depends on:** A decision on which release absorbs the content (decisions 4 and 5)
- **Rank at intake:** 17 of 64. **Status:** backlog (recorded 2026-09-11).

## E18 - Fix QUICKSTART.md's stale v0.1.0 marketplace-pin claim

- **Target:** `QUICKSTART.md`, `README.md`, `badge/text`
- **Change:** QUICKSTART.md's first install step says the marketplace pins critique-skills to the v0.1.0 tag; it pins v0.1.6 (registry 1.65.0, commit 30ec617). Done: the sentence corrected, ideally to a form that does not hard-code the patch number.
- **Why:** A new user following the getting-started doc literally is told the wrong version is installed in its first paragraph.
- **Evidence:** QUICKSTART.md:11 ('the product-on-purpose marketplace pins critique-skills to the v0.1.0 release tag'); README.md:9 (badge/text confirming v0.1.6 is the pinned release)
- **Derives from:** Stale claim surfaced by comparing QUICKSTART.md against the verified current state
- **Size:** S. **Release:** v0.1.x. **Category:** docs. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 18 of 64. **Status:** backlog (recorded 2026-09-11).

## E19 - Run the fidelity gate on the sonnet tier

- **Target:** `docs/internal/decisions/0031-fidelity-gate-acceptance-band.md`, `docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md`, `CHANGELOG.md`
- **Change:** ADR 0031 (fidelity gate acceptance band) has only ever validated haiku; sonnet, one of the two pinned tiers the published v0.1.0 numbers rest on, has never produced an envelope through the rewritten harness. Done: a bench.yml dispatch on sonnet across the skill grid, envelopes committed under a runs-dispatch-* root, the acceptance band re-evaluated on that tier.
- **Why:** Half the published measurement basis is currently unreproducible through the shipped harness; this is the first dispatch that changes that.
- **Evidence:** docs/internal/decisions/0031-fidelity-gate-acceptance-band.md; docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md (Amendment, 2026-08-16); CHANGELOG.md:10 ('sonnet, which still cannot complete a cell'); bench/results/runs-dispatch-31988100372/ (haiku envelopes only)
- **Derives from:** ADR 0031 (fidelity gate acceptance band); the 'blocks' field of the sonnet-fix candidates from the bench and adr surfaces
- **Size:** S. **Release:** v0.2.0. **Category:** measurement. **Confidence:** verified.
- **Blocks:** E20 and E26; the 'every listed skill measured' exit-gate clause on the sonnet tier
- **Depends on:** E2; CLAUDE_CODE_OAUTH_TOKEN current; wall-clock for 900s-class runs
- **Review note:** The critic found this item's v0.2.0 tag is a version label, not a real dependency: once E2 (sonnet unblock) lands, nothing else gates it. Treat it as ready the moment E2 is done.
- **Rank at intake:** 19 of 64. **Status:** backlog (recorded 2026-09-11).

## E20 - Re-measure critique-usability's Sonnet cell

- **Target:** `ROADMAP.md`, `README.md`, `CHANGELOG.md`
- **Change:** The one precision cell that does not qualify against baseline on its own tier (0.169). Done: the cell re-run through the shipped harness on sonnet and the scoreboard, verdicts and the Known-limitations bullet updated either way.
- **Why:** Named twice in ROADMAP.md as the one unresolved ship qualification; it is one cell once E2 lands.
- **Evidence:** ROADMAP.md:58 (measurement debt bullet 6); README.md:24 (scoreboard row: usability precision 0.169 sonnet); CHANGELOG.md:10 ('sonnet, which still cannot complete a cell'); ROADMAP.md:122
- **Derives from:** ROADMAP.md v0.2.0 E4, sub-E6; retires the 'non-qualifying Sonnet cell' known limitation
- **Size:** S. **Release:** v0.2.0. **Category:** measurement. **Confidence:** verified.
- **Blocks:** Declaring critique-usability unconditionally shipped rather than 'qualified through Haiku'
- **Depends on:** E2 and E19
- **Rank at intake:** 20 of 64. **Status:** backlog (recorded 2026-09-11).

## E21 - Backfill the missing fidelity-dispatch cell clarity-001/haiku-r1.json

- **Target:** `bench/results/runs-dispatch-31988100372/critique-clarity/clarity-001`, `bench/results/README.md`, `CHANGELOG.md`
- **Change:** The 2026-08-17 dispatch committed 39 of 40 envelopes; critique-clarity/clarity-001/ holds haiku-r2 through r5 only. ADR 0031 rebuilt its band over the reduced coverage. Done: one bench.yml dispatch scoped to the missing cell and the band re-evaluated at 20 of 20.
- **Why:** Cheapest improvement to the fidelity gate's statistical power; closes a gap the project has already explained around twice.
- **Evidence:** bench/results/runs-dispatch-31988100372/critique-clarity/clarity-001/ directory listing (haiku-r2..r5.json present, haiku-r1.json absent); bench/results/README.md Provenance section, 39 envelopes not the 40 the grid intended; CHANGELOG.md Added entry, coverage came in at 19 of 20 skill cells
- **Derives from:** The fidelity dispatch set being 19 of 20 with clarity-001/haiku-r1.json absent
- **Size:** S. **Release:** v0.1.x. **Category:** measurement. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** GitHub Actions secret CLAUDE_CODE_OAUTH_TOKEN being current, per docs/explanation/the-benchmark-harness.md
- **Rank at intake:** 21 of 64. **Status:** backlog (recorded 2026-09-11).

## E22 - Turn on severity_expected scoring

- **Target:** `bench/metrics/claims.py`, `bench/metrics/match.py`, `bench/generator/api.py`
- **Change:** Every planted defect in every corpus manifest already carries severity_expected (the 7 manifests without it are clean controls with no defects) and Claim already carries .severity. What is missing is that match.match_claims_to_defects returns two index sets and discards which claim matched which defect. Done: match.py also returns paired indices, score.py adds a severity-agreement aggregate, results.schema.json gains the field, report.py gains the column, with tests.
- **Why:** Named v0.2.0 measurement debt whose data has sat in every manifest since v0.1.0; the change is one function's return shape plus plumbing.
- **Evidence:** bench/metrics/claims.py:14-19 Claim.severity; bench/metrics/match.py:33-89 especially line 47 return signature; bench/generator/api.py:55,85,241-244 severity_expected validated 1-4; grep of severity_expected across bench/corpus manifests and bench/generator/domains, present in every domain; bench/README.md:194-196; ROADMAP.md:58 (measurement debt bullet 5); bench/corpus/accessibility/accessibility-001.manifest.json
- **Derives from:** ROADMAP.md v0.2.0 E4, sub-E5
- **Size:** M. **Release:** v0.2.0. **Category:** measurement. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing, self-contained within bench/metrics
- **Rank at intake:** 22 of 64. **Status:** backlog (recorded 2026-09-11).

## E23 - Write methodology.md's location-level metrics section

- **Target:** `ROADMAP.md`, `docs/explanation/methodology.md`, `bench/results/results.schema.json`
- **Change:** Section 8's Evaluation subsection never defines recall_location or precision_location although results.schema.json v1.1.0 and every published table have carried them since the 2026-07-31 rescore, and location-level is the metric the README scoreboard reports. Done: the section written with the definitions, the resolver behavior per artifact type, and the relationship to criterion-level.
- **Why:** The methodology's explanation of the metric the scoreboard leads with is load-bearing for anyone trying to verify the numbers.
- **Evidence:** ROADMAP.md:58 (measurement debt bullet 2); docs/explanation/methodology.md Section 8 lines 262-291 with no recall_location or precision_location mention; bench/results/results.schema.json (v1.1.0 location fields)
- **Derives from:** ROADMAP.md v0.2.0 E4, sub-E2
- **Size:** M. **Release:** v0.2.0. **Category:** docs. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 23 of 64. **Status:** backlog (recorded 2026-09-11).

## E24 - Add an automated evidence-quotes-not-characterizes check

- **Target:** `ROADMAP.md`, `docs/reference/critique-contract.md`
- **Change:** The contract requires a finding's evidence field to quote or measure from the artifact rather than characterize it; nothing enforces it. Done: a validator rule (or contract/validate.py check) with tests, run in CI over golden examples and committed envelopes.
- **Why:** An unenforced contract property drifting silently is the failure class the 0.1.6 release notes admit to; named v0.2.0 measurement debt.
- **Evidence:** ROADMAP.md:58 (measurement debt bullet 4); docs/reference/critique-contract.md (defines the evidence field but no cited automated check for this property)
- **Derives from:** ROADMAP.md v0.2.0 E4, sub-E4
- **Size:** M. **Release:** v0.2.0. **Category:** contract. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 24 of 64. **Status:** backlog (recorded 2026-09-11).

## E25 - Rewrite verdicts.md as one current-state document

- **Target:** `bench/results/verdicts.md`, `ROADMAP.md`
- **Change:** bench/results/verdicts.md (484 lines) is a 2026-07-31 original, a same-day location-level re-examination inserted into it, and a 2026-08-01 post-calibration amendment prepended, each marked to be read in sequence; the document itself admits the layering debt. Done: one current-state verdict per skill, referencing the ADRs for the history instead of re-deriving it.
- **Why:** A reader reconstructs any skill's current status by mentally applying three patches; named v0.2.0 measurement debt.
- **Evidence:** bench/results/verdicts.md full read: lines 1-35 three-layer preamble and the layering debt is real admission; bench/results/verdicts.md:33 (the amendment note); lines 207-317 the inserted location-level re-examination section; lines 85-206 the post-calibration amendment; bench/results/verdicts.md:36,55,85,207,319,358,390 (layered section headers); ROADMAP.md:58 (measurement debt bullet 3)
- **Derives from:** ROADMAP.md v0.2.0 E4, sub-E3
- **Size:** L. **Release:** v0.2.0. **Category:** docs. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing (a consolidation, not a re-measurement); ideally after E20 so the usability verdict is final
- **Rank at intake:** 25 of 64. **Status:** backlog (recorded 2026-09-11).

## E26 - Calibrate a per-lane consistency threshold (v2)

- **Target:** `ROADMAP.md`, `README.md`
- **Change:** The 0.309 floor is a provisional number measured once on one run set and the README's NOTE callout leads with it. Done: a calibrated per-lane threshold published with its method, replacing the floor in README, methodology, verdicts and the Known-limitations bullet.
- **Why:** A public floor number with an unpublished, single-measurement method is a gap in the receipts argument; it cannot be calibrated honestly until both tiers run.
- **Evidence:** ROADMAP.md:60; README.md:12 (the NOTE callout leading with 0.309); ROADMAP.md:120 (Known limitations: 'The 0.309 consistency floor')
- **Derives from:** ROADMAP.md v0.2.0 E5; retires the '0.309 consistency floor' known limitation
- **Size:** L. **Release:** v0.2.0. **Category:** measurement. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** E2 and E19 (sonnet dispatches actually completing; wall-clock cost beyond session count)
- **Rank at intake:** 26 of 64. **Status:** backlog (recorded 2026-09-11).

## E27 - Isolate the bench harness from the working tree it measures

- **Target:** `docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md`, `bench/run_bench.py`, `working-tree-copy/staging-of-the-plugin-itself`
- **Change:** ADR 0030 (replace the API key in the bench harness) records a probe run leaving a copy of the staged artifact inside skills/critique-clarity/, caught only because the conformance gate flagged an un-inventoried file; run_bench.py still points --plugin-dir at the live tree. Done: runs execute against a copy of the plugin (or a git worktree) and a post-run cleanliness assertion fails the run on any stray write.
- **Why:** It has already happened once; a stray write from a live dispatch could corrupt corpus fixtures or git state, the evidence chain the credibility rests on.
- **Evidence:** docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md:279-289; bench/run_bench.py (no working-tree-copy/staging-of-the-plugin-itself mechanism, only staged_artifact() for the corpus file)
- **Derives from:** ADR 0030 (replace the API key in the bench harness)
- **Size:** M. **Release:** v0.2.0. **Category:** measurement. **Confidence:** verified.
- **Blocks:** A fully-trusted live bench.yml dispatch on sonnet or any delegating tier
- **Depends on:** Nothing
- **Rank at intake:** 27 of 64. **Status:** backlog (recorded 2026-09-11).

## E28 - Pin or record the Claude Code CLI version bench.yml installs

- **Target:** `.github/workflows/bench.yml`, `anthropic-ai/claude-code`, `docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md`
- **Change:** bench.yml runs npm install -g @anthropic-ai/claude-code unpinned, and no envelope run block records a CLI or harness version, so two dispatches months apart could run under different CLI builds with nothing in the committed evidence to tell them apart. Done: a pinned version in bench.yml, and either a harness_version field in the run block (contract minor bump) or the CLI version recorded in the run-set provenance note.
- **Why:** ADR 0030's reproducibility argument for the CLI-bundled skills namespace rests on the CLI being pinned, and the first real dispatch has already happened without it; every further dispatch is an incomplete receipt.
- **Evidence:** .github/workflows/bench.yml:74 (`npm install -g @anthropic-ai/claude-code`, no version); docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md lines ~268-272 ("a property of the pinned runtime"); contract/critique-contract.schema.json `run` object fields (no CLI/harness-version field); docs/internal/release-plans/plan_v0.1.0/S-07_ci-pipeline/spec.md:87 (NFR: "Workflows pin action versions by SHA")
- **Derives from:** ADR 0030 (replace the API key in the bench harness) and S-07 (CI pipeline spec) Non-Functional Requirements
- **Size:** S. **Release:** v0.1.x. **Category:** ci. **Confidence:** verified.
- **Blocks:** Nothing directly; weakens reproducibility of every future dispatch
- **Depends on:** Nothing
- **Rank at intake:** 28 of 64. **Status:** backlog (recorded 2026-09-11).

## E29 - Make release.yml's re-run suite match what it claims to run

- **Target:** `.github/workflows/release.yml`, `AGENTS.md`, `scripts/gen-plugin-manifest.mjs`
- **Change:** release.yml re-runs 7 of ci.yml's 9 gating jobs, never smoke (fresh-install crash class) or build-site, while its header comment and AGENTS.md:186 claim full parity and the drift job's coverage check scopes itself to ci.yml only. Done: either add the two steps (smoke no-deps before pip install) or narrow both comments and record why the release gate excludes them.
- **Why:** A release is pending with 35 unreleased bullets and the release gate cannot catch the exact failure class (a fresh install crashing while 784 tests passed) that motivated smoke.py; nothing would ever alarm on the gap widening.
- **Evidence:** .github/workflows/release.yml (7 steps, no smoke.py or check-site.mjs call, header comment lines 3-5); AGENTS.md:186; AGENTS.md:79-89 (9-row CI table); scripts/gen-plugin-manifest.mjs:108-111 (checkAgentsDocCoverage docstring, scoped to ci.yml only); docs/internal/decisions/0033-aggregate-ci-gate.md:30
- **Derives from:** S-07 (CI pipeline spec) Requirements section and ADR 0033 (aggregate CI gate)
- **Size:** S. **Release:** v0.1.x. **Category:** ci. **Confidence:** verified.
- **Blocks:** Nothing directly; leaves the release gate weaker than the PR gate
- **Depends on:** Nothing
- **Rank at intake:** 29 of 64. **Status:** backlog (recorded 2026-09-11).

## E30 - Fix two gaps in skill-template.md before the next skill is built from it

- **Target:** `docs/internal/skill-template.md`, `evals/joint-routing.eval.json`, `CHANGELOG.md`
- **Change:** The template's directory shape omits the skills/critique-<domain>/README.md every shipped skill carries to satisfy the G8 folder-readme rule (so a from-template build trips the family gate at step 13), and its 13-step checklist never mentions evals/joint-routing.eval.json although test_the_fixture_covers_every_skill fails CI the moment a seventh skill directory exists, and the fix needs new contested cases plus edits to the six existing descriptions and a manual k>=3 hand-scoring run. Done: both added to the template, with the cross-skill cost stated.
- **Why:** These surface as a gate failure and a confusing CI failure the first day work on critique-deck begins; two paragraphs now save a debugging session then.
- **Evidence:** docs/internal/skill-template.md:15-16, 34-48, 783-786 (step 13, npm run check / family gate); docs/internal/skill-template.md:760-786 (no mention of evals/joint-routing.eval.json anywhere); CHANGELOG.md's 'Two documentation findings surfaced, both invisible at the gate's default level' entry (G8 folder-readme rule); skills/critique-clarity/README.md and its five siblings, present on disk; scripts/tests/test_joint_routing_eval.py (test_the_fixture_covers_every_skill and test_contested_pairs_name_each_other_in_their_descriptions); evals/README.md:20-21, 35-38; ROADMAP.md line 52 (critique-deck named first)
- **Derives from:** docs/internal/skill-template.md's own directory-shape section and checklist, stale against the gate and tests they must satisfy
- **Size:** S. **Release:** v0.1.x. **Category:** skills. **Confidence:** verified.
- **Blocks:** A clean from-template build of N1 (critique-deck)
- **Depends on:** Nothing
- **Rank at intake:** 30 of 64. **Status:** backlog (recorded 2026-09-11).

## E31 - Add criterion-table completeness to skill-selftest.py

- **Target:** `docs/internal/skill-template.md`, `scripts/skill-selftest.py`, `scripts/gen-site.mjs`
- **Change:** skill-template.md:404-405 rules that every ID in checks.scripted or checks.judged has exactly one row in the references table; skill-selftest.py's table check only verifies an Operationalization column exists and carries no quotes. The rule holds today (96 IDs, zero duplicates, hand-verified) by author diligence only; gen-site.mjs:507-508 guards cross-skill duplicates but not completeness. Done: the self-test cross-references table IDs against the declared lane lists.
- **Why:** The next criterion edit (a seventh skill, or the pruning pass) can silently add or drop a row with no CI signal.
- **Evidence:** docs/internal/skill-template.md:404-405 and 713-728; scripts/skill-selftest.py (check_paraphrase_heuristic function, ~lines 750-806, no ID cross-reference present); scripts/gen-site.mjs:507-508 (duplicate-ID guard only)
- **Derives from:** docs/internal/skill-template.md's own stated criterion-table completeness rule, currently unenforced
- **Size:** S. **Release:** v0.1.x. **Category:** skills. **Confidence:** verified.
- **Blocks:** Nothing today; protects the registry at the next skill or pruning pass
- **Depends on:** Nothing
- **Rank at intake:** 31 of 64. **Status:** backlog (recorded 2026-09-11).

## E32 - Close S-03 AC-3: flip the checkbox and add a corpus-composition CI check

- **Target:** `docs/internal/release-plans/plan_v0.1.0/S-03_bench-harness/spec.md`, `docs/internal/execution/P2-report.md`, `bench/generator/verify.py`
- **Change:** S-03 (bench harness spec) AC-3 (corpus composition: >=20 artifacts, >=3 per core domain, >=1 clean per core domain) is still unchecked although P2-report's CORPUS row and a live recount (23 artifacts, 4/3/4/4/4/4) clear it; and the corpus CI job only checks sha256 reproducibility, so deleting artifacts or adding a domain without a clean example would pass every job. Done: one test asserting the thresholds, wired into the corpus job, and the AC checked with a citation.
- **Why:** The composition guarantees are true only because nobody has touched them since a one-time manual audit; the paperwork half is minutes and the check half is one test.
- **Evidence:** docs/internal/release-plans/plan_v0.1.0/S-03_bench-harness/spec.md:22,26-29,74; docs/internal/execution/P2-report.md CORPUS row; bench/generator/verify.py ('Regenerate and compare every sha256'); bench/generator/__main__.py `_cmd_verify`; .github/workflows/ci.yml corpus job; live recount: bench/corpus/{accessibility,argument,clarity,docs,microcopy,usability}/*.manifest.json = 4,3,4,4,4,4 = 23 total; grep across bench/ and scripts/ for AC-3's numeric thresholds returns no hits
- **Derives from:** S-03 (bench harness spec) AC-3
- **Size:** S. **Release:** v0.1.x. **Category:** ci. **Confidence:** verified.
- **Blocks:** Nothing; latent regression risk
- **Depends on:** Nothing
- **Rank at intake:** 32 of 64. **Status:** backlog (recorded 2026-09-11).

## E33 - Correct ROADMAP's Gold-tier bullet (3 of 4 done) and decide the tier declaration

- **Target:** `ROADMAP.md`, `scripts/check.mjs`, `.agent-skills-toolkit/scripts/tier-report.mjs`
- **Change:** ROADMAP.md:81 bundles chain/hook evaluation, folder-README and docs-frontmatter completion, and source docblocks as pending v0.3.0 groundwork. A live run of the pinned toolkit (node scripts/check.mjs --strict; tier-report --json) shows zero blockers to Advanced/Gold: G4, G5, G7, G8, G9, G10 pass on real content; only G1 (hook documentation) and G3 (library regression/eval coverage) pass vacuously because the repo declares no hooks and no chain contract. The roadmap surface's 'complete folder-README/frontmatter/docblocks' candidate is superseded by this. Done: the bullet narrowed to chain/hook coverage, and a recorded decision on whether and when library.json declares tier: advanced (CHANGELOG calls it 'a separate decision' that nothing tracks), noting agents/ must never get a folder README per RELEASE-NOTES 0.1.2.
- **Why:** An inaccurate roadmap risks redoing finished conformance work, and the tier-declaration decision is free-standing with nobody queuing it.
- **Evidence:** ROADMAP.md:81 (v0.3.0 bullet); live run: `node scripts/check.mjs --strict` -> "Tier: Convergent (no blockers detected)"; `node .agent-skills-toolkit/scripts/tier-report.mjs "$(pwd)" --json` -> {"tier":"convergent","satisfies":["universal","convergent"],"blocked":{},"declaredTier":"convergent"}; .agent-skills-toolkit/docs/reference/gold-checks.md (G1-G10 table with conditional flags); CHANGELOG.md [Unreleased] 'Changed' entry; library.json:6 (tier: convergent); .agent-skills-toolkit/scripts/check.mjs:31 (--strict bypasses applyStandardDowngrade); RELEASE-NOTES.md 0.1.2 entry ('The subagent nobody wrote' - agents/ must not get a folder README)
- **Derives from:** ROADMAP.md v0.3.0 section and CHANGELOG.md [Unreleased] 'Changed' entry
- **Size:** S. **Release:** v0.1.x. **Category:** docs. **Confidence:** verified.
- **Blocks:** Nothing; clarifies real v0.3.0 scope
- **Depends on:** Nothing for the correction; the tier declaration is a maintainer call
- **Review note:** Retagged from v0.2.0 to v0.1.x by the critic: the correction half depends on nothing, and every other zero-dependency doc fix is v0.1.x.
- **Rank at intake:** 33 of 64. **Status:** backlog (recorded 2026-09-11).

## E34 - Close the SKIP_DIRS carry-forward note - fixed upstream and already adopted

- **Target:** `.agent-skills-toolkit/scripts/lib/fs-utils.mjs`, `CHANGELOG.md`, `.github/workflows/ci.yml`
- **Change:** RC-HANDOVER and the P6/P7 reports carry a 'file an upstream issue' item for agent-skills-toolkit's SKIP_DIRS missing Python cache dirs. The pinned TOOLKIT_REF (cafe6b69) already includes __pycache__ and .pytest_cache via the toolkit's PR #189, which CHANGELOG names as adopted. Done: the note marked closed with the commit; this dispositions one of RC-HANDOVER's four not-re-verified items.
- **Why:** Filing an issue for an already-fixed defect wastes a maintainer session; the note itself is what is stale.
- **Evidence:** .agent-skills-toolkit/scripts/lib/fs-utils.mjs:20-30 (SKIP_DIRS includes __pycache__, .pytest_cache); .agent-skills-toolkit git log showing commit 9439699 ('fix: grade plugins against their own tree, not this toolkit's', #189) pre-dating the pinned cafe6b69 checkout; CHANGELOG.md [Unreleased] 'Changed' entry naming PR #189 and the TOOLKIT_REF bump; .github/workflows/ci.yml and release.yml env.TOOLKIT_REF
- **Derives from:** docs/internal/execution/RC-HANDOVER.md 'Carry to v0.2' list
- **Size:** S. **Release:** v0.1.x. **Category:** hygiene. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 34 of 64. **Status:** backlog (recorded 2026-09-11).

## E35 - Run plugin-dev:plugin-validator and plugin-dev:skill-reviewer, or record why not

- **Target:** `docs/internal/execution/RC-HANDOVER.md`, `docs/internal/execution/P7-report.md`, `CHANGELOG.md`
- **Change:** Both external validators were named in release plan phase B5 and RC-HANDOVER as 'never run against this release'; a grep of every CHANGELOG entry through v0.1.6 confirms neither has run six releases later. Done: run both against the next release candidate and record findings, or a one-line decision that they are not worth running and why. This confirms one of RC-HANDOVER's not-re-verified items as still open.
- **Why:** Release-engineering hygiene explicitly named in the plan; a deliberate decision beats letting it age across every subsequent release.
- **Evidence:** docs/internal/execution/RC-HANDOVER.md:121-122; docs/internal/execution/P7-report.md:133-134; `grep -n 'plugin-validator\|skill-reviewer' CHANGELOG.md` returns no matches
- **Derives from:** Release plan implementation phase B5, docs/internal/release-plans/plan_v0.1.0/implementation/IMPL-B-skills-to-rc.md
- **Size:** S. **Release:** v0.2.0. **Category:** ci. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 35 of 64. **Status:** backlog (recorded 2026-09-11).

## E36 - Confirm or deprecate the reserved selector field per ADR 0012's own RC question

- **Target:** `docs/internal/decisions/0012-location-grammar-freetext-plus-reserved-selector.md`, `docs/internal/release-plans/plan_v0.1.0/S-02_critique-contract/spec.md`, `bench/results/runs`
- **Change:** ADR 0012 (location grammar: free text plus reserved selector) deferred the field's fate to RC with one question: did any launch skill find selector insufficient or unnecessary? No ADR or handover entry answers it, and no committed skill example or bench envelope populates it. Done: a dated answer appended to ADR 0012 and, if unnecessary, the field deprecated (not deleted) in contract 1.1.
- **Why:** A self-described RC checkpoint left permanently unanswered undercuts the 'frozen finding contract' claim, and the v0.1.x exit gate is about to be declared.
- **Evidence:** docs/internal/decisions/0012-location-grammar-freetext-plus-reserved-selector.md:44; docs/internal/release-plans/plan_v0.1.0/S-02_critique-contract/spec.md:98; grep for selector across skills/*/examples/*.json and bench/results/runs* returned zero matches with real content
- **Derives from:** ADR 0012 (location grammar: free text plus reserved selector)
- **Size:** S. **Release:** v0.1.x. **Category:** contract. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 36 of 64. **Status:** backlog (recorded 2026-09-11).

## E37 - Run the TOULMIN-HEDGE-DENSITY false-positive check ADR 0017 named, and fix TOULMIN.md's future tense

- **Target:** `docs/internal/decisions/0017-argument-lane-split-scripted-assists-as-criteria.md`, `skills/critique-argument/references/TOULMIN.md`, `bench/results/README.md`
- **Change:** ADR 0017 (critique-argument lane split: scripted assists as criteria) said the first thing P3 should look at is a false positive on cautious clean prose. P3 ran a month ago, but references/TOULMIN.md's Thresholds section still says P3 is where they get their first evidence, and bench/results/README.md publishes only an aggregate clean-artifact figure. Done: the criterion checked against a deliberately hedge-heavy clean artifact, the result recorded, TOULMIN.md updated to past tense with the numbers.
- **Why:** A named, self-identified risk on a shipped skill's only fully-scripted criterion, cheap to check.
- **Evidence:** docs/internal/decisions/0017-argument-lane-split-scripted-assists-as-criteria.md (Consequences, 'the failure it should look for is a false positive on a clean corpus artifact'); skills/critique-argument/references/TOULMIN.md:91-95; bench/results/README.md:287-292
- **Derives from:** ADR 0017 (critique-argument lane split: scripted assists as criteria)
- **Size:** S. **Release:** v0.1.x. **Category:** skills. **Confidence:** likely.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 37 of 64. **Status:** backlog (recorded 2026-09-11).

## E38 - Measure critique-accessibility's location fix on id-poor markup

- **Target:** `docs/internal/decisions/0028-post-calibration-verdict-accessibility-clears-ac-6.md`, `bench/results/README.md`, `ROADMAP.md`
- **Change:** ADR 0028 (post-calibration verdict: critique-accessibility clears AC-6) names its weakest assumption: the corpus is unusually id-rich and how much of the 0.176-to-0.988 gain survives on markup without ids is unmeasured; it handed 'measure the id-poor case before v0.2' to the orchestrator. No id-poor artifact exists in bench/corpus/accessibility/ and ROADMAP's measurement-debt list omits it. Done: one id-poor accessibility artifact added to the corpus and the location metrics re-run on it.
- **Why:** This is the result that discharged v0.1.0's only release-blocking benchmark failure; if the gain is a corpus artifact, real-world location accuracy is unknown.
- **Evidence:** docs/internal/decisions/0028-post-calibration-verdict-accessibility-clears-ac-6.md:129; bench/results/README.md:704-709 (Limitations); ROADMAP.md:58 (measurement-debt list omits this item)
- **Derives from:** ADR 0028 (post-calibration verdict: critique-accessibility 0.1.1 clears AC-6)
- **Size:** S. **Release:** v0.2.0. **Category:** measurement. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 38 of 64. **Status:** backlog (recorded 2026-09-11).

## E39 - Record the CLAUDE_CODE_OAUTH_TOKEN retention decision and a rotation procedure

- **Target:** `_local/_session-logs/2026-08-09_21-10_claude-opus-5_adr-0030-fidelity-and-two-releases.md`, `.memsearch/memory/2026-08-15.md`, `.github/workflows/bench.yml`
- **Change:** The keep-or-remove call was raised in the 2026-08-08/09 session logs, settled ('retain, required for gate and live dispatch') only in a compressed memsearch summary of an unwrapped 2026-08-15 session, and never recorded durably. Separately ADR 0030 describes the token as a long-lived personal-subscription credential with rotation summarized in one clause and no runbook. Done: an ADR amendment recording the retention decision, its reasoning, and a short rotation/revocation procedure. The retention half is likely; the procedure half is the ci-contract surface's speculative extension.
- **Why:** The token is load-bearing (bench.yml's only live-run credential) and the project's discipline is that every load-bearing fact lives in one authored place.
- **Evidence:** _local/_session-logs/2026-08-09_21-10_claude-opus-5_adr-0030-fidelity-and-two-releases.md:163,322 (raised, left open); .memsearch/memory/2026-08-15.md:454 (the only record that it was actually decided); .github/workflows/bench.yml:78 (the secret is still live and load-bearing); docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md lines ~157-159; CHANGELOG.md [Unreleased] 'Added' entry naming run 31988100372
- **Derives from:** 2026-08-08 session log 'Decide whether to keep the CLAUDE_CODE_OAUTH_TOKEN repository secret'; ADR 0030 (replace the API key in the bench harness)
- **Size:** S. **Release:** v0.1.x. **Category:** docs. **Confidence:** likely.
- **Blocks:** Nothing operationally
- **Depends on:** Nothing
- **Rank at intake:** 39 of 64. **Status:** backlog (recorded 2026-09-11).

## E40 - Look at a Mermaid diagram in light and dark on the live site

- **Target:** `CHANGELOG.md`, `docs/explanation/architecture.md`, `docs/explanation/architecture-detail.md`
- **Change:** CHANGELOG's 'site is live' entry says explicitly that Mermaid rendering in both themes was not checked and is not claimed; two published explanation pages each carry a mermaid fence and no automated check renders Mermaid. Done: both diagrams viewed in both themes, the CHANGELOG caveat closed with a dated note.
- **Why:** A self-acknowledged unclosed loop in the shipped record, three weeks old, closable in minutes.
- **Evidence:** CHANGELOG.md:34; docs/explanation/architecture.md (1 mermaid fence); docs/explanation/architecture-detail.md (1 mermaid fence); site/astro.config.mjs:36-48 (astro-mermaid integration)
- **Derives from:** CHANGELOG.md [Unreleased] bullet describing something unfinished
- **Size:** S. **Release:** v0.1.x. **Category:** site. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 40 of 64. **Status:** backlog (recorded 2026-09-11).

## E41 - Remove bench/README.md's stale '.gitattributes does not exist yet' prerequisite

- **Target:** `bench/README.md`
- **Change:** bench/README.md:116 tells the reader .gitattributes does not exist and must be created before the first corpus commit; it has existed since 2026-08-04. Done: the sentence removed.
- **Why:** False setup guidance in the harness doc; one-line fix with no dependencies.
- **Evidence:** bench/README.md:116; verified .gitattributes exists at repo root (1640 bytes, dated 2026-08-04)
- **Derives from:** bench/README.md Prerequisites section (v0.1.0 planning phase, now obsolete)
- **Size:** S. **Release:** v0.1.x. **Category:** docs. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 41 of 64. **Status:** backlog (recorded 2026-09-11).

## E42 - Reconcile 'frozen with a JSON Schema' against 'freezes at v1.0'

- **Target:** `ROADMAP.md`, `README.md`
- **Change:** ROADMAP.md:21 says the contract is already frozen, ROADMAP.md:102 says the schema and registry freeze at v1.0, and README.md:12 calls them stable commitments; together they do not say whether a breaking contract change before v1.0 is a minor release or a v2 event. Done: one sentence in ROADMAP.md defining pre-v1.0 contract-change policy, with README aligned.
- **Why:** Three documents describe the same commitment at three strengths, and the difference matters to anyone building against the contract before v1.0.
- **Evidence:** ROADMAP.md:21 ('frozen with a JSON Schema and validator'); ROADMAP.md:102 ('At v1.0, the finding schema and the criterion ID registry freeze'); README.md:12 ('stable commitments')
- **Derives from:** Wording ambiguity surfaced by cross-referencing ROADMAP.md's two uses of frozen/freeze against README.md
- **Size:** S. **Release:** unscheduled. **Category:** docs. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 42 of 64. **Status:** backlog (recorded 2026-09-11).

## E43 - Create a v1.0 readiness tracker for the four declaration criteria

- **Target:** `ROADMAP.md`, `README.md`, `errors/0`
- **Change:** ROADMAP.md:97-100 names four v1.0 criteria (per-skill benchmark cycle plus telemetry pruning; survey slate fully triaged; Silver stable across two consecutive minors; one external consumer gating in CI) and no artifact tracks any of them. Done: one table (in ROADMAP.md or docs/internal/) with a row per criterion, per skill where applicable; the conformance row can be filled today (Convergent, 0/0 at v0.1.6), the others fill as E44, E48 and E56 land.
- **Why:** Without a home, v1.0 declaration would require re-deriving all four states from scratch; the conformance row is startable now at near-zero cost.
- **Evidence:** ROADMAP.md:97; ROADMAP.md:98; ROADMAP.md:99; ROADMAP.md:100 ('a repository or workflow not owned by this project'); README.md:299 (current tier: convergent (Silver), 0 errors/0 warnings)
- **Derives from:** ROADMAP.md v1.0.0 declaration criteria 1-3 (three roadmap candidates merged)
- **Size:** S. **Release:** v1.0.0. **Category:** docs. **Confidence:** verified.
- **Blocks:** Declaring v1.0.0 without re-derivation
- **Depends on:** Nothing to create; rows depend on E44, E48 and E56
- **Rank at intake:** 43 of 64. **Status:** backlog (recorded 2026-09-11).

## E44 - Run the taxonomy survey and triage the Gemini audit's slate through it

- **Target:** `ROADMAP.md`, `docs/internal/research`, `_local/audit/2026-08-18_audit_gemini-pro-research_Review`
- **Change:** ROADMAP.md v0.2.0 E1 commits to a research pass with a Two-Part Gate verdict per candidate, published at docs/internal/research/critique-framework-survey.md; the directory does not exist. The 2026-08-20 session directed that the Gemini audit's slate (four architectural recommendations: slash commands revisited, Critique-Diff, MCP exposure, a CI Action; five candidate skills) be treated as survey input, and none has a recorded verdict. Done: the survey published with every candidate, including that slate, shipped/deferred/rejected with a reason, feeding E43 row 2.
- **Why:** It sequences the skill wave, the v0.4.0+ domain waves and the v1.0 triage criterion, and its absence has left external recommendations with no institutional verdict for a month. The 2026-09-11 ruling brought it into v0.2.0.
- **Evidence:** ROADMAP.md:48; docs/internal/research/ (confirmed absent in repo); _local/audit/2026-08-18_audit_gemini-pro-research_Review Critique Skills GitHub Repo.md:138-172 (the four Part 1 recommendations) and :179-238 (the five candidate skills); _local/_session-logs/2026-08-20_22-10_claude_readme-drafts-and-audit-review.md:99-103 ('treat the Gemini audit as survey input rather than a plan'); ROADMAP.md:44-114
- **Derives from:** ROADMAP.md v0.2.0 E1 (Taxonomy survey regeneration); the 2026-08-20 audit-review decision
- **Size:** L. **Release:** v0.2.0. **Category:** research. **Confidence:** verified.
- **Ruling 2026-09-11:** the maintainer ruled v0.2.0 as Option A plus Option C (receipts
  first, and the research spine). Moved from v0.3.0 into v0.2.0; the survey is Option C's
  core and is now in scope for this release.
- **Blocks:** Sequencing of N2 and N3; E58; E43 row 2
- **Depends on:** E1
- **Rank at intake:** 44 of 64. **Status:** backlog (recorded 2026-09-11).

## E45 - Build BYOR on one named flagship skill

- **Target:** `contract/critique-contract.schema.json`, `docs/reference/criterion-ids.md`, `docs/explanation/methodology.md`
- **Change:** The contract, BYOR-* namespace, merge layer and frontmatter validator already handle a byor finding with zero code change; the invocation surface does not exist: critique-critic's contract is closed to four parameters, checks.py is hard-wired, no SKILL.md mentions byor, no golden or recipe demonstrates it, and no flagship is named. Done: a rubric-intake format, an extended subagent contract, one skill's SKILL.md and checks path accepting it, a golden example and an examples/recipes/ entry, documented as the pattern every later skill follows.
- **Why:** The only v0.2/v0.3 candidate that changes what a user can do with the library; its true cost (invocation layer, not contract layer) is now known and should not be re-derived.
- **Evidence:** contract/critique-contract.schema.json:87-93,111-125,418-424; docs/reference/criterion-ids.md:57,64; docs/explanation/methodology.md section 3 (Bring Your Own Rubric, Status: Provisional); scripts/skill-selftest.py:87; skills/_shared/tests/test_findings.py:65-76; skills/_shared/merge.py:130-145; agents/critique-critic.md:28-33; docs/internal/skill-template.md lines 250-257 and :256 ('byor - ... not used by any v0.1 skill'); examples/README.md and examples/recipes/ (no byor recipe); grep of all six skills/critique-*/SKILL.md for 'byor' (zero matches); ROADMAP.md:56
- **Derives from:** ROADMAP.md v0.2.0 E3 (BYOR mode); live decision 5
- **Size:** L. **Release:** v0.3.0. **Category:** skills. **Confidence:** verified.
- **Blocks:** Every later skill's BYOR support
- **Depends on:** E1 and E10; a named flagship skill
- **Rank at intake:** 45 of 64. **Status:** backlog (recorded 2026-09-11).

## E46 - Sync the samples-corpus THREAD_PROFILES placeholders from pm-skills

- **Target:** `_local/initial-plan/samples-corpus/THREAD_PROFILES.md`, `_local/initial-plan/samples-corpus/README.md`, `ROADMAP.md`
- **Change:** The samples-corpus plan's only authored source marks user_base, real_competitors and character_naming_convention as sync-required for the Brainshelf and Workbench threads and says they must be copied verbatim from pm-skills before the first sample is authored, never invented. Nothing has touched it since 2026-08-02. Done: a fresh read of pm-skills' current THREAD_PROFILES.md and the three fields filled.
- **Why:** It is the one concrete gap between 'plan' and 'buildable' for E47, small enough to close whenever a pm-skills session is open.
- **Evidence:** _local/initial-plan/samples-corpus/THREAD_PROFILES.md:13,63,70-71,99,106-107 (the sync-required markers and the instruction not to invent them); _local/initial-plan/samples-corpus/README.md:6-7 (dated 2026-08-02, status 'scheduled v0.2 roadmap E7'); ROADMAP.md:64
- **Derives from:** ROADMAP.md v0.2.0 E7 (samples corpus)
- **Size:** S. **Release:** v0.4.0+. **Category:** research. **Confidence:** verified.
- **Blocks:** E47 (the first Brainshelf or Workbench sample)
- **Depends on:** A fresh read of pm-skills' current THREAD_PROFILES.md
- **Rank at intake:** 46 of 64. **Status:** backlog (recorded 2026-09-11).

## E47 - Build the samples corpus

- **Target:** `ROADMAP.md`, `examples/recipes/revision-loop.md`, `_local/initial-plan/samples-corpus/README.md`
- **Change:** Worked narrative samples across a small set of running example threads, each scenario-to-disposition, with machine-validated envelopes in CI and provenance labeled illustrative, never entering bench/ and never carrying manifests. The fabricated-metadata fix (E5) is split out and lands first; the sentinel it defines is what the samples' provenance labels reuse. Done: the samples published on the site with the sentinel-labeled envelopes validating in CI.
- **Why:** The site now exists to host it, which was the original ordering argument; the 2026-09-11 ruling leaves it as v0.4.0+ content.
- **Evidence:** ROADMAP.md:64; examples/recipes/revision-loop.md (shows the pattern of clearly labeling authored vs. real content); _local/initial-plan/samples-corpus/README.md:6-7; _local/initial-plan/samples-corpus/SAMPLE_CREATION.md
- **Derives from:** ROADMAP.md v0.2.0 E7 (samples corpus)
- **Size:** L. **Release:** v0.4.0+. **Category:** docs. **Confidence:** likely.
- **Blocks:** Nothing
- **Depends on:** E1 and E5 (sentinel), 46
- **Rank at intake:** 47 of 64. **Status:** backlog (recorded 2026-09-11).

## E48 - Begin disposition telemetry (acceptance rate per criterion)

- **Target:** `ROADMAP.md`, `docs/reference/criterion-ids.md`
- **Change:** No human acceptance data exists anywhere; every published number comes from the seeded-defect benchmark. ROADMAP commits to acceptance-rate-per-criterion data from real dispositions feeding the first pruning pass, and the v1.0 criterion requires every skill to survive that pass. Note the 'deprecate, never delete' rule at docs/reference/criterion-ids.md:41 has no schema field or tooling yet, which the pruning pass will need. Done: a disposition-log collection path, an aggregation script, and the first published acceptance table. Absorbs RC-HANDOVER's 'human acceptance data' not-re-verified item.
- **Why:** The only path that closes the 'No human acceptance data yet' limitation, and it needs usage volume no session count can buy, so starting late costs calendar time.
- **Evidence:** ROADMAP.md:62; ROADMAP.md:124 (Known limitations: 'No human acceptance data yet'); docs/reference/criterion-ids.md:41
- **Derives from:** ROADMAP.md v0.2.0 E6; retires the 'No human acceptance data yet' known limitation
- **Size:** L. **Release:** v0.3.0. **Category:** measurement. **Confidence:** verified.
- **Blocks:** The v1.0 per-skill pruning criterion (E43 row 1)
- **Depends on:** E1; real usage volume
- **Rank at intake:** 48 of 64. **Status:** backlog (recorded 2026-09-11).

## E49 - Write one real tutorial for the empty Diataxis Tutorials quadrant

- **Target:** `docs/tutorials/README.md`, `site/src/content/docs/tutorials/index.md`, `docs/how-to`
- **Change:** docs/tutorials/README.md says 'None yet' and points at QUICKSTART.md; the site renders that verbatim at /tutorials/ while the other three quadrants carry 279, 296 and 908 lines. ROADMAP never lists a tutorial. Done: one end-to-end tutorial (install, run one skill on a provided artifact, read the envelope, disposition a finding) published through gen-site.
- **Why:** The 50-page site is visibly incomplete the moment a reader clicks Tutorials and finds an apology.
- **Evidence:** docs/tutorials/README.md:1-17; site/src/content/docs/tutorials/index.md; docs/how-to/*.md, docs/reference/*.md, docs/explanation/*.md (line counts compared); ROADMAP.md (grepped for 'tutorial', no match)
- **Derives from:** Diataxis coverage assessment: the thinnest quadrant
- **Size:** M. **Release:** v0.2.0. **Category:** docs. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 52 of 64. **Status:** backlog (recorded 2026-09-11).

## E50 - List critique-skills in agent-plugins' convergence table

- **Target:** `.memsearch/memory/2026-08-22.md`, `.memsearch/memory/2026-08-23.md`, `.memsearch/memory/2026-08-25.md`
- **Change:** Identified 2026-08-22 and re-deferred on 08-23, 08-25 and 08-26 because it requires editing the agent-plugins registry repo without authorization; it appears in no committed document here. The deliverable is this project's marketplace presentation, so it is kept; the edit happens in the sibling repo. Done: the row added, or an explicit decline recorded here.
- **Why:** Re-surfaced four times without a ruling; each re-surfacing cost a maintainer question.
- **Evidence:** .memsearch/memory/2026-08-22.md:49; .memsearch/memory/2026-08-23.md:12; .memsearch/memory/2026-08-25.md:38; .memsearch/memory/2026-08-26.md:7
- **Derives from:** 2026-08-22 session, identified as one of W8's remaining items
- **Size:** S. **Release:** v0.1.x. **Category:** distribution. **Confidence:** likely.
- **Blocks:** Nothing functional
- **Depends on:** Maintainer authorization to edit the agent-plugins repository
- **Rank at intake:** 53 of 64. **Status:** backlog (recorded 2026-09-11).

## E51 - Give the precision and corpus-provenance limitations a retirement path or an explicit 'accepted'

- **Target:** `ROADMAP.md`
- **Change:** ROADMAP's Known limitations names precision as the weak axis across the board and the corpus as agent-generated, and no version item anywhere addresses either beyond one usability cell. Whether each deserves a plan or stays a disclosed permanent limitation is a maintainer call. Done: one sentence per limitation in ROADMAP.md saying which.
- **Why:** A document whose stated purpose is to say what is not done currently names two structural gaps with no stated position on whether they ever close.
- **Evidence:** ROADMAP.md:122 ('Precision is the weak axis across the board'); ROADMAP.md:125 ('The benchmark corpus is agent-generated'); ROADMAP.md:48-89 (full v0.2.0 through v0.4.0+ item list, containing no precision-broad or corpus-provenance item)
- **Derives from:** Gaps surfaced by cross-referencing the Known limitations section against the full item list (two roadmap candidates merged)
- **Size:** S. **Release:** unscheduled. **Category:** decision. **Confidence:** speculative.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 54 of 64. **Status:** backlog (recorded 2026-09-11).

## E52 - Decide who performs 'revise' in the automated revision loop before building it

- **Target:** `ROADMAP.md`, `examples/recipes/revision-loop.md`
- **Change:** ROADMAP.md:111 says nothing rewrites an artifact on its own authority; the v0.3.0 item asks for an invokable critique-disposition-revise-re-critique chain; in the recipe, a human authors v2. Done: an ADR ruling whether the chain pauses for a human revise step or something else, and how that squares with the auto-fix exclusion.
- **Why:** A boundary question better settled in an ADR than discovered mid-implementation; kept as a decision, not a proposal to relax the exclusion.
- **Evidence:** ROADMAP.md:107-108 (Deliberately not doing: auto-fix exclusion); examples/recipes/revision-loop.md ('The revised v2 memo is authored for this recipe'); ROADMAP.md:78
- **Derives from:** Pre-implementation gap in ROADMAP.md v0.3.0 E1 cross-referenced against Deliberately not doing
- **Size:** S. **Release:** v0.3.0. **Category:** decision. **Confidence:** speculative.
- **Blocks:** N4
- **Depends on:** Nothing
- **Rank at intake:** 55 of 64. **Status:** backlog (recorded 2026-09-11).

## E53 - Harden --gate as a documented per-skill CI recipe for consumers

- **Target:** `ROADMAP.md`, `docs/how-to/gate-in-ci.md`, `examples/recipes/gate-in-ci.md`
- **Change:** One how-to and one recipe exist; ROADMAP is explicit that exercised-and-documented exit codes across every shipped skill, for consumer repositories, is not yet met. Done: exit codes exercised per skill with a copy-pasteable consumer workflow.
- **Why:** The precondition for the v1.0 external-consumer criterion: something to hand a candidate consumer.
- **Evidence:** ROADMAP.md:79; docs/how-to/gate-in-ci.md and examples/recipes/gate-in-ci.md (one doc and one recipe, not per-skill)
- **Derives from:** ROADMAP.md v0.3.0 E2 (Gate hardening)
- **Size:** M. **Release:** v0.3.0. **Category:** docs. **Confidence:** likely.
- **Blocks:** E56
- **Depends on:** Nothing
- **Rank at intake:** 57 of 64. **Status:** backlog (recorded 2026-09-11).

## E54 - Ship one documented cross-library composition workflow

- **Target:** `ROADMAP.md`, `README.md`, `examples/recipes`
- **Change:** README asserts the family's think-make-judge chain; no worked example exists in examples/ where a sibling library's output (thinking-framework-skills or pm-skills) is critiqued by this one. Done: one recipe demonstrating it. This is a same-org demonstration and does not count toward the v1.0 external-consumer criterion.
- **Why:** The difference between an asserted positioning claim and a demonstrated one.
- **Evidence:** ROADMAP.md:80; README.md ('The family' section, asserts the think-make-judge chain with no worked cross-library example); examples/recipes/ (revision-loop.md, gate-in-ci.md, critic-delegation.md - none cross-library)
- **Derives from:** ROADMAP.md v0.3.0 E3 (Cross-library composition)
- **Size:** M. **Release:** v0.3.0. **Category:** docs. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 58 of 64. **Status:** backlog (recorded 2026-09-11).

## E55 - Build chain and hook evaluation coverage (Gold checks G1 and G3)

- **Target:** `ROADMAP.md`, `.agent-skills-toolkit/docs/reference/gold-checks.md`
- **Change:** The only two Gold checks that do not pass on real content, and they pass vacuously today because the repo declares no hooks and no chain contract. Done: once N4 exists, hook documentation and chain eval coverage that make G1 and G3 earned rather than vacuous, unlocking the tier declaration in E33.
- **Why:** Explicitly sequenced behind the revision-loop chain; scoped now so it is not lost as a separate deliverable.
- **Evidence:** ROADMAP.md:81; .agent-skills-toolkit/docs/reference/gold-checks.md (G1-G10 table with conditional flags)
- **Derives from:** ROADMAP.md v0.3.0 E4 (Gold-tier groundwork), sub-part 1
- **Size:** M. **Release:** v0.3.0. **Category:** ci. **Confidence:** verified.
- **Blocks:** The tier: advanced declaration (E33, second half)
- **Depends on:** N4
- **Rank at intake:** 59 of 64. **Status:** backlog (recorded 2026-09-11).

## E56 - Plan the external-consumer path for the v1.0 criterion

- **Target:** `ROADMAP.md`
- **Change:** The fourth v1.0 criterion needs a repository not owned by this project gating in CI on the finding contract; no outreach or adoption tracking exists, and the v0.3.0 cross-library item does not count. Done: a named candidate consumer, the recipe from E53 handed over, and the outcome tracked in E43 row 4.
- **Why:** The one v1.0 criterion that depends on external adoption rather than internal engineering, so it needs a different kind of plan and a longer lead.
- **Evidence:** ROADMAP.md:100 ('a repository or workflow not owned by this project'); ROADMAP.md:80 (cross-library composition is same-family, not independent)
- **Derives from:** ROADMAP.md v1.0.0 declaration criterion 4
- **Size:** M. **Release:** v1.0.0. **Category:** distribution. **Confidence:** speculative.
- **Blocks:** Declaring v1.0.0
- **Depends on:** E53
- **Rank at intake:** 60 of 64. **Status:** backlog (recorded 2026-09-11).

## E57 - Publish the benchmark harness as a standalone asset

- **Target:** `ROADMAP.md`, `bench/run_bench.py`
- **Change:** bench/ is internal with no packaging or docs for third-party use, though a dry run already works with nothing but Python and jsonschema. Done: the generator and grading harness packaged and documented so a third-party skill author can measure their own skill.
- **Why:** Correctly unscheduled until v0.2.0/v0.3.0 telemetry says it is pulling demand; the item most reusable by the sibling libraries.
- **Evidence:** ROADMAP.md:87; python bench/run_bench.py --skills critique-clarity --k 1 --dry-run (runs cleanly on this Windows checkout with no CLI or model)
- **Derives from:** ROADMAP.md v0.4.0+ E1 (Benchmark harness as a standalone asset)
- **Size:** L. **Release:** v0.4.0+. **Category:** distribution. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Telemetry signal from E48 and later
- **Rank at intake:** 61 of 64. **Status:** backlog (recorded 2026-09-11).

## E58 - Scope the remaining domain waves once the survey lands

- **Target:** `ROADMAP.md`
- **Change:** Visual design, naming and terminology, and any newcomer the survey surfaces; no candidate list exists because the survey has not run. Done: a scoped list with a Two-Part Gate verdict each, derived from E44.
- **Why:** Placeholder so it is not lost; not scopable before the survey.
- **Evidence:** ROADMAP.md:88
- **Derives from:** ROADMAP.md v0.4.0+ E2 (Remaining domain waves)
- **Size:** XL. **Release:** v0.4.0+. **Category:** research. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** E44
- **Rank at intake:** 62 of 64. **Status:** backlog (recorded 2026-09-11).

## E59 - Verify what the marketplace consumes the homepage field for

- **Target:** `_local/astro/02-decision-log-and-critical-path.md`, `.claude-plugin/plugin.json`, `CHANGELOG.md`
- **Change:** The site's decision log said to verify what the marketplace does with homepage before changing it; library.json and plugin.json now carry the site URL and nothing records the verification. The registry pin predates the change, so the effect is unobserved. Done: one check at the next re-pin and a one-line note.
- **Why:** Low urgency; the next marketplace re-pin is where an unverified assumption becomes visible to users.
- **Evidence:** _local/astro/02-decision-log-and-critical-path.md:94-97 (question 3, and the 'verify... before changing it' instruction); library.json:28; .claude-plugin/plugin.json:9; CHANGELOG.md:40
- **Derives from:** Decision-log-vs-shipped comparison for the Astro site
- **Size:** S. **Release:** unscheduled. **Category:** distribution. **Confidence:** speculative.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Rank at intake:** 63 of 64. **Status:** backlog (recorded 2026-09-11).

## E60 - Fix the Mermaid brand line color when the shared family docs preset lands

- **Target:** `site/astro.config.mjs`, `CHANGELOG.md`
- **Change:** site/astro.config.mjs sets lineColor to the brand #5C7CFA but Mermaid renders its default #6366f1 because the theme is default, not base; CHANGELOG records it left unchanged on purpose pending a shared preset for all four family sites. Done: the preset adopted here when it exists, or the theme switched locally if the preset never lands.
- **Why:** Cosmetic and deliberately deferred, but a live wrong setting with no tracking entry in this repo; easy to lose once the preset lands.
- **Evidence:** site/astro.config.mjs:44 (lineColor: '#5C7CFA'); CHANGELOG.md:41 (documents the #6366f1 rendered mismatch and the deferred-preset reasoning)
- **Derives from:** CHANGELOG.md [Unreleased] bullet describing something unfinished
- **Size:** S. **Release:** unscheduled. **Category:** site. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** The shared family docs preset landing (outside this repo)
- **Rank at intake:** 64 of 64. **Status:** backlog (recorded 2026-09-11).

## E61 - Rule the site lockfile version spread against the family baseline

- **Target:** `site/package.json`, `site/package-lock.json`
- **Change:** This repository's install resolved `astro` to 7.2.4 and `mermaid` to 11.17.0, against
  the family's committed 7.2.0 / 7.2.1 and 11.16.1. `site/package.json` declares `astro` with a
  caret (`^7.2.0`) and pulls `mermaid` transitively through `astro-mermaid` (`~2.1.0`), so neither
  resolution is pinned and a fresh install can move again. Done: a recorded ruling on whether this
  repo is the family reference or should be brought back to the family versions, and the caret
  replaced with a pin either way so the resolution is reproducible.
- **Why:** The astro spread is patch-level and harmless on its own; the mermaid gap is a real minor
  version. The cost of deferring is not breakage, it is that the site's dependency state is
  currently unpinned and undeclared, so no one can say whether a future divergence is intentional.
- **Evidence:** `site/package.json` (`"astro": "^7.2.0"`, `"astro-mermaid": "~2.1.0"`);
  `site/package-lock.json` (`node_modules/astro` 7.2.4, `node_modules/mermaid` 11.17.0), both
  re-verified 2026-09-11.
- **Derives from:** The five live maintainer decisions (the site lockfile question, blocked since
  2026-08-21). Prior recommendations on the record: leave the resolutions and name this repo the
  family reference (2026-09-11), and pin the caret for reproducibility (2026-08-26).
- **Size:** S. **Release:** v0.1.x. **Category:** site. **Confidence:** verified.
- **Blocks:** Nothing
- **Depends on:** Nothing
- **Review note:** Added after the audit pass. The intake briefing told every auditor not to report
  the five known live decisions, and three of them (E1, E2, E14) reached the backlog anyway through
  synthesis while this one did not. It is recorded here because the argument for this directory is
  precisely that a decision surviving only in session logs eventually gets dropped.
- **Rank at intake:** unranked (added 2026-09-11, after the 64-item pass). **Status:** backlog.
