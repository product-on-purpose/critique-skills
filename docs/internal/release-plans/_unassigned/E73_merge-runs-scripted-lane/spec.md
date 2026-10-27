---
id: E73
title: "The merge step runs the scripted lane itself, instead of trusting the model's copy"
type: spec
status: committed
created: 2026-10-23
updated: 2026-10-26
linked-effort: docs/internal/backlog/enhancements.md
linked-plan: null
linked-release: null
ac-count: 9
source-count: 12
requires-human-review: true
spec-dependencies: []
target-release: v0.3.0
---

# Spec: the merge step runs the scripted lane itself

Ruled by the maintainer on 2026-10-23 (the six decisions below) and built 2026-10-26. The build
covers requirements 1 through 9, D1 through D6, and AC-1 through AC-8. AC-9, the paid re-measure,
stays open until the maintainer gives the dispatch its own go; see "Versions" below for why the
version moves wait with it.

## Task Summary

**Status:** built 2026-10-26; AC-9 (the paid re-measure) stays open, pending the maintainer's go
**Last updated:** 2026-10-26 by Claude, build
**Linked plan:** not yet planned
**Open questions:** 0 (all six were decided 2026-10-23; see Open Questions / Decisions)
**Revisions:** 1 (2026-10-26: moved from the local draft; D1-D3's Context paragraphs reworded from
present to past tense ("Today" to "Before this build"); a Build status line added after D4, D5 and
D6, outside each maintainer-decision quote; AC checklist and Task Summary updated to the build)

### Acceptance Criteria Fulfillment

- [x] **AC-1** - Every finding `checks.py` emits for the artifact enters the merged pool, whatever
  the model wrote
- [x] **AC-2** - A model finding's lane comes from the criterion's list in `SKILL.md`, never from
  the model
- [x] **AC-3** - A model finding on a scripted criterion is handled as D1 rules
- [x] **AC-4** - A model finding on a criterion in neither list is handled as D2 rules
- [x] **AC-5** - A judged finding that states no confidence gets the default D3 rules
- [x] **AC-6** - The bytes `checks.py` reads are the bytes `run.artifact_sha256` hashes
- [x] **AC-7** - A test per registered skill shows a dropped and a mislabeled finding both corrected
- [x] **AC-8** - Pass 4 of every `SKILL.md`, the critic and the skill template say the same thing
- [ ] **AC-9** - Every skill whose output changed is measured as D5 rules before the release ships

## Purpose

The scripted lane is the part of every verdict that needs no trust in a model. It is meant to be
reproducible from committed code alone. Before this build, the envelope's scripted lane was
whatever the model copied into its findings file, so a model could drop a script finding or
relabel its own judgment as the script's, and the envelope recorded either as fact.

This spec makes the merge step compute the scripted lane from the script and assign every model
finding's lane from the skill's own declaration. After it, a scripted finding in an envelope always
came from `checks.py`, and a judged finding always came from the model.

## The defect, reproduced

E73's backlog entry recorded the cause as inferred. It was reproduced before this build, on `main`
at `5ed5a6a`, with no model call, using one committed golden artifact:

1. `checks.py` on `skills/critique-forms/examples/artifacts/golden-02.html` emits 8 findings.
2. A findings file was built from them with one script finding removed, the `FORMS-ADDRESS-FORMAT`
   finding at `#house-number`. Two judged-criterion findings were added: `FORMS-ACTION-HIERARCHY`
   labeled `"lane": "scripted"` with `"confidence": "medium"`, and `FORMS-FIELD-NECESSITY` with no
   lane.
3. `scripts/merge.py --artifact <golden-02.html> --findings <file>` produced a valid envelope in
   which:
   - the removed script finding is absent, and nothing says it was ever emitted;
   - `FORMS-ACTION-HIERARCHY` is recorded as `scripted`, with its confidence raised from `medium` to
     `high`;
   - `FORMS-FIELD-NECESSITY` is recorded as `scripted`, at `high` confidence.

The second result is worse than the backlog entry states (high confidence, verified). A mislabeled
judgment is not only filed in the wrong lane. `_to_raw` then forced its confidence to `high`, because
a scripted finding must be high confidence (`skills/_shared/merge.py`, lines 143 to 150 on `main` at
`5ed5a6a`, before this build). The envelope therefore asserted a certainty that no one held.

The two symptoms in the paid run match this mechanism. Sonnet dropped 11 script claims in 6 of 20
runs of `critique-forms`, and Haiku labeled 10 judged-criterion findings `scripted` in 3 of 20
([ADR 0037 (critique-forms ship verdict)](../../../decisions/0037-critique-forms-ship-verdict.md),
check 6). Every skill uses the same assembler, so every skill was exposed.

This build re-ran the reproduction's three steps against `skills/_shared/merge.py` as built here:
the removed finding is restored, and the mislabeled finding is filed `judged` at confidence
`medium`, not forced to `high`. See `skills/_shared/tests/test_merge_lanes.py`,
`test_a_judged_criterion_mislabeled_scripted_is_refiled_as_judged` and
`test_the_skill_shim_restores_a_script_finding_the_findings_file_omits`, both parametrized over
`critique-forms`.

## Scope

- `skills/_shared/merge.py`: the change itself.
- Each registered skill's `SKILL.md`: the pass-4 text, and `metadata.version` if D4 moves it.
- `agents/critique-critic.md`: its assembly step, which repeats the pass-4 instruction.
- `docs/internal/skill-template.md`: its pass-4 template text, so a new skill inherits the new rule.
- Tests under `skills/_shared/tests/`, parametrized over every registered skill.

## Non-Goals

- **No change to any `checks.py`.** The script's findings are taken as it emits them.
- **No change to the contract.** The `lane` enum stays `scripted` and `judged`.
- **No change to bounding or ranking.** `skills/_shared/envelope.py` keeps its rule.
- **No change to the bench harness or the metrics.** They read envelopes, which keep their shape.
- **No build of E67 (accessibility expansion)** here; this spec only sequences against it.

## Requirements

1. **Merge runs the script itself.** `skills/_shared/merge.py` loads the skill's own
   `scripts/checks.py` as a module and calls its `check(artifact)`. That is what
   `skills/_shared/runner.py`'s `_run` does. The call returns the raw findings before ranking and
   bounding. Running `checks.py` as a subprocess would not do, because its output is already
   bounded, so findings below severity 3 beyond the fifth would be lost before the merge. All seven
   skills and the template fixture expose `check(artifact)` today (verified).
2. **The scripted lane is the script's output, and only that.** Every finding `check()` returns
   enters the pool, with `lane` set to `scripted`, exactly as the script emitted it.
3. **A model finding's lane comes from the declaration.** Merge reads `checks.scripted` and
   `checks.judged` from the `SKILL.md` frontmatter, with a parser in the style of
   `read_skill_version`. A model finding whose criterion is in `checks.judged` is filed as `judged`,
   whatever its `lane` says. The `lane` the model wrote is ignored.
4. **A model finding on a scripted criterion is handled as D1 rules.** The recommendation is to drop
   it and report the count on standard error.
5. **A model finding on a criterion in neither list is handled as D2 rules.** The recommendation is
   to file a finding marked `rubric_source: byor` as `judged`, whatever its namespace, and to reject
   any other.
6. **A judged finding that states no confidence gets the default D3 rules.** The recommendation is
   `medium`. Before this build it got `high`, the scripted default, which overstates a judgment.
7. **One file, one hash.** `checks.py` reads the `--artifact` file that `run.artifact_sha256` hashes.
   A findings file written for a different artifact cannot change which bytes the script reads.
8. **Merge stays tolerant of the old pass 4.** A findings file that still contains the script's
   findings, as every `SKILL.md` asked before this build, must still produce a correct envelope.
   Those copies are dropped under requirement 4, so the old and new instructions give the same
   result.
9. **Pass 4 says what merge now does.** Each `SKILL.md`, the critic and the skill template tell the
   model to write its judged-lane findings only, and say that merge runs the scripted lane itself.
   Pass 2 still runs `checks.py`, because seeing its output helps the inventory and keeps the model
   from duplicating it.

## What changed in each skill

| Component | File | Change | Version |
|---|---|---|---|
| Shared assembler | `skills/_shared/merge.py` | Requirements 1 to 8 | Not versioned; covered by its tests |
| Seven skill entry points | `skills/critique-*/scripts/merge.py` | None. Each is a 44-line shim that adds `--skill` and calls the shared module, and the seven differ only in the skill name in their docstring (verified) | Not versioned separately |
| `critique-accessibility` | `SKILL.md` pass 4 | Requirement 9 | Per D4; moves once with E67, see "Sequencing" |
| `critique-argument` | `SKILL.md` pass 4 | Requirement 9 | Per D4 |
| `critique-clarity` | `SKILL.md` pass 4 | Requirement 9 | Per D4 |
| `critique-docs` | `SKILL.md` pass 4 | Requirement 9 | Per D4 |
| `critique-forms` | `SKILL.md` pass 4 | Requirement 9 | Per D4 |
| `critique-microcopy` | `SKILL.md` pass 4 | Requirement 9 | Per D4 |
| `critique-usability` | `SKILL.md` pass 4 | Requirement 9 | Per D4 |
| `critique-critic` subagent | `agents/critique-critic.md`, step 5 | Requirement 9 | Per D4 |
| Skill template | `docs/internal/skill-template.md`, "Assemble the envelope" block | Requirement 9 | Not versioned |
| Template fixture | `skills/_template-fixture/critique-toy/` | None. It has no `merge.py`, so the template doc is its only surface (verified) | Not registered |

A version move edits three places per skill: `metadata.version` in `SKILL.md`, the `library.json`
entry, and the `skill_version=` argument in `checks.py`. `skills/_shared/tests/test_read_skill_version.py`
fails if they disagree (`docs/internal/skill-template.md`, "Where the version goes").

## Tests

All parametrized from `library.json`'s registered skills, as the E53 gate tests are, so a skill
registered later is covered without an edit. Each case uses a skill's committed golden artifact,
named by the golden file's `artifact` field, and builds its findings file in the test. No model is
called.

Committed in `skills/_shared/tests/test_merge_lanes.py` and, for the CLI plumbing and the assemble()
behaviors that do not depend on lane routing, `skills/_shared/tests/test_merge_cli.py`.

| Case | Input findings file | Expected envelope |
|---|---|---|
| Dropped script finding | `checks.py`'s findings with one removed | The removed finding is in `findings[]` or counted in `summary.suppressed_count` |
| Mislabeled judgment | A judged-criterion finding labeled `scripted`, confidence `medium` | That finding is `judged`, confidence `medium` |
| No lane | A judged-criterion finding with no `lane` | That finding is `judged` |
| Model copy of a script criterion | A scripted-criterion finding the script did not emit | Per D1 |
| Unknown criterion | A finding on a criterion in neither list | Per D2 |
| Old pass 4 | Every script finding plus every judged finding, as the pre-build `SKILL.md` asked | The same envelope as the new pass 4 gives for the judged findings alone |

One more test is shared across skills: **every finding `checks.py` emits for an artifact is either
listed in the merged envelope or counted in `suppressed_count`.** The scripted findings in a merged
envelope cannot be compared byte for byte with `checks.py`'s own envelope. Bounding runs over the
combined pool, so a script finding below severity 3 can lose one of the five places to a judged
finding of higher rank (`skills/_shared/envelope.py`, `rank_and_bound`).

## Versions

**`skill_version` is the provenance of every envelope.** If the merge step changes a skill's output
and the version stays, envelopes from before and after are indistinguishable by their run record. The
precedent is [ADR 0027 (accessibility location-emission calibration)](../../../decisions/0027-accessibility-location-emission-calibration.md),
which moved `critique-accessibility` to 0.1.1 for a change that was mostly in `checks.py`.

This change alters what every skill's envelope can contain. A dropped script finding now reappears,
and a mislabeled judgment changes lane and confidence. So every skill's output changes whenever its
model would have erred, even though no rubric changes. D4 ruled that this moves every version.

**The version moves are not part of this build.** D4 places them "in the release that carries E67",
and this build changes no `metadata.version`, no `library.json` entry, and no `checks.py`
`skill_version=` argument. `scripts/gen-site.mjs` shows each skill only its active version's cells
(`activeCut`, and the skill pages' own version filter against `library.json`), and
`bench/results/results.json` carries no `0.1.1` cells yet for six of the seven skills. Moving a
version now, before a dispatch has measured anything under it, would blank that skill's published
figures on the site rather than show a result. The versions move together, with the shared paid
re-measure E67 also needs (see "Measurement and sequencing with E67" below); AC-9 tracks that it
happens before the release carrying this change ships.

`critique-accessibility` is at 0.1.1, and E67 moves it again. If E73 lands first and both ship in one
release, accessibility can move once, to 0.2.0 for the new criteria, and carry this change with it.

## Measurement and sequencing with E67

**The rule.** `ROADMAP.md` line 40: "Each skill is re-measured through the current harness when a
release changes it." A version move under D4 therefore commits the release to a re-measure of every
moved skill.

**The cost (derived from the corpus, high confidence).** The corpus holds 27 artifacts across the seven
skills: 4 each for accessibility, clarity, docs, forms, microcopy and usability, and 3 for argument.
At k=5 on two pinned tiers, that is 270 skill envelopes. The `critique-forms` dispatch
`37091134037` also re-ran the baseline inside its own run set; its directory holds a `baseline/`
folder beside `critique-forms/`. Doing the same here adds 270 baseline envelopes.

**The sequencing.** E67 (accessibility expansion) also needs a paid re-measure of
`critique-accessibility` on both tiers. If E73 lands before E67's build and both are in one release,
one dispatch measures both changes. In the other order, the first paid run measures a merge step
already known to be defective, and accessibility is measured twice. The order is therefore E73's
ruling, E73's build, E67's build, then one dispatch for all seven skills. This build is the second
step; E67's build and the shared dispatch are still ahead, and the dispatch needs the maintainer's
own explicit go (never run unprompted; see `AGENTS.md`, "Bench").

**A cheaper first look, with limits (medium confidence, inferred, not built).** The post-E73
envelope is computable from committed evidence without a model call. Take each committed envelope,
replace its scripted lane with `checks.py`'s output for the same artifact, refile every other finding
by its criterion's list, and score the result with `bench/metrics`. ADR 0037's check 6 did this
arithmetic by hand for forms. It found Sonnet's criterion recall rising from 0.790 to 0.895, and
location precision falling from 0.317 to 0.312. The replay has two limits. A committed envelope has
already lost its suppressed findings, so a script finding the model dropped below the bound cannot be
restored exactly. And a model given the new pass-4 text may judge differently. D5 ruled that a
replay sizes the change first; it is not built in this change.

## Acceptance Criteria

AC-1: For any registered skill and any artifact, every finding the skill's `check()` returns for that
artifact is in the merged envelope's `findings[]` or counted in `summary.suppressed_count`, whatever
the findings file contains. [S1, S2, S5]

AC-2: A model finding whose criterion is in `checks.judged` is filed as `judged`, whatever its `lane`
field says or omits. [S1, S2]

AC-3: A model finding whose criterion is in `checks.scripted` is handled as D1 rules, and the
handling is stated on standard error when it applies. [S1]

AC-4: A model finding whose criterion is in neither list is handled as D2 rules. [S1, S8]

AC-5: A judged finding with no `confidence` is recorded with the default D3 rules. [S2]

AC-6: The file `check()` reads is the `--artifact` file whose bytes `run.artifact_sha256` hashes. [S2]

AC-7: For every skill in `library.json`, a test shows a dropped script finding restored and a
mislabeled judged finding refiled, with no model call. [S1]
  Given: the skill's golden artifact and a findings file with one script finding removed and one
  judged-criterion finding labeled `scripted`
  When: the skill's `scripts/merge.py` assembles the envelope
  Then: the removed finding is listed or counted as suppressed, and the relabeled finding is `judged`

AC-8: Pass 4 of every registered skill's `SKILL.md`, step 5 of `agents/critique-critic.md`, and the
pass-4 template in `docs/internal/skill-template.md` tell the model to write judged findings only,
and say that merge runs the scripted lane. [S3, S9, S10]

AC-9: Before the release that carries this change is tagged, every skill whose version moved under
D4 is measured as D5 rules, and `bench/results/results.json` carries the result or the release notes
say why not. [S6, S7]

## Sources & Evidence

- **[S1]** E73 backlog entry, with its 2026-10-15 ruling - `docs/internal/backlog/enhancements.md`,
  section "E73" - class A
- **[S2]** The assembler, as built - `skills/_shared/merge.py`, `assemble`, `_route_model_findings`
  and `run_script_checks` - class A
- **[S3]** A skill's pass 4 - `skills/critique-forms/SKILL.md`, "Protocol", step 4 - class A
- **[S4]** The reproduction in "The defect, reproduced", first run 2026-10-23 on `5ed5a6a`, re-run
  against this build 2026-10-26 and committed as
  `skills/_shared/tests/test_merge_lanes.py` (`test_a_judged_criterion_mislabeled_scripted_is_refiled_as_judged`
  and `test_the_skill_shim_restores_a_script_finding_the_findings_file_omits`, parametrized over
  every registered skill, `critique-forms` included) - class A
- **[S5]** The scripted-lane runner - `skills/_shared/runner.py`, `_run` - class A
- **[S6]** The re-measure rule - `ROADMAP.md`, line 40 - class A
- **[S7]** [ADR 0037 (critique-forms ship verdict)](../../../decisions/0037-critique-forms-ship-verdict.md),
  check 6 - class A
- **[S8]** The contract's `lane` enum, `scripted` and `judged` only -
  `contract/critique-contract.schema.json`, `$defs/lane` - class A
- **[S9]** The critic's assembly step - `agents/critique-critic.md`, step 5 - class A
- **[S10]** The skill template's pass 4 - `docs/internal/skill-template.md`, "Assemble the envelope"
  block - class A
- **[S11]** The version precedent - [ADR 0027](../../../decisions/0027-accessibility-location-emission-calibration.md) - class A
- **[S12]** E67's ruling and scope - `docs/internal/backlog/enhancements.md`, section "E67" - class A

## Open Questions / Decisions

| ID | Title | Resolution | Status | Updated |
|----|-------|------------|--------|---------|
| D1 | A model finding on a scripted criterion the script did not emit | Option A | Decided | 2026-10-23 |
| D2 | A model finding on a criterion in neither list | Option A | Decided | 2026-10-23 |
| D3 | The default confidence of a judged finding that states none | Option A | Decided | 2026-10-23 |
| D4 | Whether every skill's version moves | Option A | Decided | 2026-10-23 |
| D5 | How the change is measured before release | Option A | Decided | 2026-10-23 |
| D6 | Whether the E35 findings ride the same version move | Option B | Decided | 2026-10-23 |

### D1: A model finding on a scripted criterion the script did not emit (Decided)

**Summary.** Decide what merge does when the model reports a scripted criterion that the script did
not find.

**Context.** Every scripted criterion is decided by a fixed reading of the markup. When the model
reports one the script did not, either the model is wrong or the script's heuristic missed a case.
`FORMS.md` counts a heuristic miss as a known limit, measured by the real-forms check. Before this
build such a finding entered the envelope as `scripted`, so it looked like the script's output.

**Desired outcome.** The scripted lane holds only what the script found, and a real heuristic miss
still gets noticed somewhere.

**Options / approaches.**

* **Option A:** Drop the finding, and print on standard error how many were dropped and on which
  criteria. The envelope's scripted lane is then exactly the script's.
* **Option B:** Keep it, filed as `judged`. That breaks the rule that no criterion sits in both
  lanes, which `skill-selftest.py` enforces for the declarations as `lane-overlap`.
* **Option C:** Fail the merge. One stray finding would then cost the whole run.

**Recommendation.** Option A. It keeps the lane split exact, and the standard-error count leaves a
trace for anyone studying heuristic misses. A miss belongs in the real-forms style of check, not in
the envelope.

---

> **Maintainer decision:** Decided 2026-10-23 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A. Drop the finding, and print on standard error how many were dropped and on which criteria.
> * **Reasoning:** The maintainer answered "Ok", accepting the recommendation. Dropping keeps the scripted lane exactly the script's output, and it also absorbs the script-finding copies that today's pass 4 asks for (requirement 8).
> * **Follow-up:** Build requirement 4, verified by AC-3, in this spec.
> * **Decided by / date:** jprisant / 2026-10-23

### D2: A model finding on a criterion in neither list (Decided)

**Summary.** Decide what merge does with a criterion the skill does not declare.

**Context.** Before this build merge accepted any criterion the model named, if it matched the
contract's ID pattern. A typo or an invented ID was recorded as `scripted`. E45 (BYOR on one flagship
skill) will bring user-supplied criteria that arrive at run time and appear in no list. The contract
allows only `scripted` and `judged` lanes, so a BYOR finding can only be `judged`. The contract marks
a BYOR finding by `rubric_source: byor`, not by its ID: a `BYOR-` ID must carry that mark, but a user
rubric "may declare its own namespace" (`contract/critique-contract.schema.json`, the `BYOR-`
conditional's `$comment`).

**Desired outcome.** An undeclared ID never enters an envelope by accident, and BYOR still works when
E45 lands.

**Options / approaches.**

* **Option A:** File a finding marked `rubric_source: byor` as `judged`, whatever its namespace, and
  reject the merge for any other undeclared ID, naming it.
* **Option B:** File every undeclared finding as `judged`. Typos and invented IDs then pass silently.
* **Option C:** Drop every undeclared finding, BYOR included, until E45 designs its own path.

**Recommendation.** Option A. It turns an invented ID into a visible failure, and it gives E45 the
one path it needs, without designing E45 here. Keying on `rubric_source` rather than the `BYOR-`
prefix follows the contract, which lets a user rubric name its own namespace. Whether merge should
also check a BYOR finding's ID against the rubric the user supplied is E45's question.

---

> **Maintainer decision:** Decided 2026-10-23 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A. File a finding marked `rubric_source: byor` as `judged`, and fail the merge for any other undeclared ID, naming it.
> * **Reasoning:** The maintainer answered "Ok", accepting the recommendation after the walk showed its cost: in 4 of 19 Haiku `critique-clarity` envelopes in dispatch 31988100372 (2026-08-17), the model named an undeclared, namespace-swapped ID such as `WILLIAMS-AUDIENCE`, so this option would have left those runs with no envelope. No other envelope among 444 committed skill runs named an undeclared ID.
> * **Follow-up:** Build requirement 5, verified by AC-4, in this spec. Whether merge also checks a BYOR finding's ID against the user's rubric stays with E45 (BYOR on one flagship skill).
> * **Decided by / date:** jprisant / 2026-10-23

### D3: The default confidence of a judged finding that states none (Decided)

**Summary.** Decide what confidence merge records for a judged finding that omits it.

**Context.** Before this build, the assembler defaulted a missing confidence to `high`, the right
default for a scripted finding. Once lanes come from the declaration, the default matters only for
judged findings, where `high` claims more certainty than the model stated.

**Desired outcome.** An envelope never records more certainty than anyone expressed.

**Options / approaches.**

* **Option A:** Default to `medium`, the middle of the contract's three values.
* **Option B:** Keep `high`, which changes nothing about today's records.
* **Option C:** Fail the merge, which costs a whole run over a missing field.

**Recommendation.** Option A. It is the honest reading of "no confidence stated". Few findings will
hit it, because each `SKILL.md` already asks the model to state confidence.

---

> **Maintainer decision:** Decided 2026-10-23 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A. Default to `medium`.
> * **Reasoning:** The maintainer answered "Ok", accepting the recommendation. An envelope then never records more certainty than the model stated.
> * **Follow-up:** Build requirement 6, verified by AC-5, in this spec.
> * **Decided by / date:** jprisant / 2026-10-23

### D4: Whether every skill's version moves (Decided)

**Summary.** Decide whether this change moves every skill's version, and the critic's.

**Context.** The rubrics, the scripts and the corpus are unchanged. But every skill's envelopes now
differ whenever its model would have dropped or mislabeled a finding, and pass 4's text changes in
every `SKILL.md`. `skill_version` is how a reader tells envelopes from before and after apart. The
2026-10-14 ruling kept the launch skills' versions fixed for v0.2.0; this change was not part of that
release.

**Desired outcome.** Every envelope's version identifies the merge behaviour that produced it, and no
skill moves twice in one release.

**Options / approaches.**

* **Option A:** A patch move for every skill and the critic, in one release with E67, with
  accessibility moving once to carry both.
* **Option B:** No version moves, because no rubric changed. Envelopes from before and after then
  share a version.
* **Option C:** Move only the skills a replay shows to change, if D5 runs one.

**Recommendation.** Option A. The change is in every skill's output path, so the provenance argument
covers all seven, and ADR 0027 is the precedent. Option C saves nothing on measurement, because the
re-measure rule then applies to whichever skills move.

---

> **Maintainer decision:** Decided 2026-10-23 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A. A patch move for every skill and the critic, in one release with E67, with accessibility moving once to carry both.
> * **Reasoning:** The maintainer answered "Ok", accepting the recommendation. The change is in every skill's output path, and ADR 0027 is the precedent for a version move over a non-rubric change.
> * **Follow-up:** Move each version in the three places this spec's "Versions" section names, in the release that carries E67 (accessibility expansion).
> * **Decided by / date:** jprisant / 2026-10-23

**Build status:** Not done in this build; see "Versions" above.

### D5: How the change is measured before release (Decided)

**Summary.** Decide how the moved skills are measured, and whether a free replay comes first.

**Context.** `ROADMAP.md` line 40 requires a re-measure through the current harness when a release
changes a skill. One dispatch for all seven skills is 270 skill envelopes, or 540 with a re-run
baseline. A replay over committed envelopes calls no model, and it would size the change before the
money is spent. It cannot restore suppressed findings, and it cannot predict how a model responds to
the new pass-4 text.

**Desired outcome.** The published figures for each moved skill come from the current harness, and
the paid run is spent once.

**Options / approaches.**

* **Option A:** A replay first, to size the change and catch surprises. Then one paid dispatch,
  shared with E67, whose results are published.
* **Option B:** One paid dispatch, shared with E67, and no replay.
* **Option C:** A replay only, published as the measurement. That would amend the re-measure rule,
  because a replay does not run the current harness.

**Recommendation.** Option A. The replay is cheap, it validates the build before a paid run, and it
gives the paid run an expected result to check against. Option C would weaken the rule that every
published figure comes from a real run.

---

> **Maintainer decision:** Decided 2026-10-23 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A. A replay over committed envelopes first, then one paid dispatch shared with E67, whose results are published.
> * **Reasoning:** The maintainer answered "Ok", accepting the recommendation. The replay costs nothing and gives the paid run an expected result to check against.
> * **Follow-up:** Build the replay after E73's build, then draft the shared dispatch; AC-9 in this spec tracks the measurement. The paid dispatch still needs its own explicit go when it is drafted.
> * **Decided by / date:** jprisant / 2026-10-23

**Build status:** Neither the replay nor the dispatch is built in this change.

### D6: Whether the E35 findings ride the same version move (Decided)

**Summary.** Decide whether the `SKILL.md` findings that the E35 validator run listed are fixed in the
same version move.

**Context.** The E35 run (`docs/internal/execution/E35-validator-run.md`) listed five findings for
the skills' next versions and one for the critic's. R1: the critique-docs description names no sibling
skill. R2: critique-clarity's out-of-scope list omits forms. R3: critique-microcopy's frontmatter
lists are out of ID order. R4 and V1: the shared docs are cited by repository-root path, with one
exception. V2: the critic's text calls its model "pinned". This spec already moves every version
and pays for one re-measure.

**Desired outcome.** Each listed finding is fixed once, in a version that is measured, without
mixing a change to triggering into a change to measurement.

**Options / approaches.**

* **Option A:** All six ride along. R1 changes a description, which decides when the skill is chosen,
  not what it reports.
* **Option B:** R2, R3, R4, V1 and V2 ride along; R1 waits for its own change, because a description
  change deserves a trigger-eval run of its own.
* **Option C:** None ride along. Each waits for a later version move.

**Recommendation.** Option B. Five of the six are wording or ordering fixes with no effect on what a
skill reports, so they cost nothing extra. R1 is the one that changes behaviour, and it is measured
by the trigger evals, not by the bench.

---

> **Maintainer decision:** Decided 2026-10-23 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option B. R2, R3, R4, V1 and V2 ride the D4 version move; R1 waits for its own change.
> * **Reasoning:** The maintainer answered "Ok", accepting the recommendation. Five of the six are wording or ordering fixes that do not change what a skill reports, and R1 changes triggering, which the trigger evals measure.
> * **Follow-up:** Fix R2, R3, R4, V1 and V2 in E73's build, and update their dispositions in `docs/internal/execution/E35-validator-run.md` in the same change. R1 waits for a change of its own with a trigger-eval run.
> * **Decided by / date:** jprisant / 2026-10-23

**Build status:** Done in this build; see `docs/internal/execution/E35-validator-run.md` for the updated dispositions.
