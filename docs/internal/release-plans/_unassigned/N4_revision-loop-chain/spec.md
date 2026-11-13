---
id: N4
title: "The revision-loop chain"
type: spec
status: built
created: 2026-10-26
updated: 2026-11-12
linked-effort: docs/internal/backlog/new-components.md
linked-plan: null
linked-release: v0.3.0
ac-count: 10
source-count: 23
requires-human-review: true
spec-dependencies: []
target-release: v0.3.0
---

# Spec: the revision-loop chain (N4)

Ruled by the maintainer on 2026-10-30 (the nine decisions below), and built on 2026-11-12 in PR 130 (contract 1.1.0) and PR 131 (the chain). Two parts of the build differ from the text below, and both are recorded under Task Summary. [ADR 0040 (the revision loop pauses with a revision brief)](../../../decisions/0040-revision-loop-pauses-with-a-revision-brief.md) settled who performs revise, and this spec restates that ruling as requirements. [ADR 0042 (contract 1.1.0)](../../../decisions/0042-contract-1-1-0-iteration-revision-brief-selector.md) decides the contract change this chain builds. The body below is the draft the maintainer ruled on, so a note that was true on 2026-10-26 can be out of date: E73 (merge runs the scripted lane) is built, and its version moves happened on 2026-10-28.

## Task Summary

**Status:** built 2026-11-12, except D6's frontmatter key, which waits on a version ruling
**Last updated:** 2026-11-12 by Claude, after the build

**Where the build differs from this spec.**

- **The brief is in the contract.** Requirement 3 says the brief stays outside the contract until E54 consumes it. ADR 0042, written after this spec, moved it into contract 1.1.0 as a fourth document type, and PR 130 built that.
- **No skill's frontmatter gained `metadata.chain` yet.** D6 chose to declare each edge both in the contract and in the skill's frontmatter, and its follow-up said to raise the version question if the key changes what a skill run reads. It does: `critique-critic` reads the skill's `SKILL.md` in full, frontmatter included. So the edges live in `agents/_chain-permitted.yaml` only, which is all the toolkit's S4 and G3 checks read, and the frontmatter key waits on the maintainer's ruling.
- **A fourth stop decision exists.** When findings at severity 3 or above remain but the person accepted none, the loop stops with `stop-nothing-accepted`, because an empty brief asks for no revision and the contract rejects one. The spec names only the two stops.
- **`INDEX.md` lists the chain contract but not the workflow.** The toolkit's index generator renders no workflow section, and inserting one locally makes the toolkit's G4 drift check fail, which is a Gold burndown regression. The workflow is listed in `library.json`, `AGENTS.md`, and `README.md`.
**Linked plan:** not yet planned
**Open questions:** 0 (all nine were decided 2026-10-30; see Open Questions / Decisions)
**Revisions:** 0

### Acceptance Criteria Fulfillment

- [x] **AC-1** - The chain runs ADR 0040's five steps, in order, and no step writes to the artifact
- [x] **AC-2** - The chain stops when no finding at severity 3 or above remains, or after the third iteration, whichever comes first
- [x] **AC-3** - A pause writes a revision brief holding one entry per accepted finding, with the finding, its location, its fix, and its criterion
- [x] **AC-4** - The brief is a deterministic projection of the envelope and the disposition log, computable with no model call
- [x] **AC-5** - The disposition log's iteration field is optional, added at contract version 1.1.0, and every existing 1.0.0 log stays valid
- [x] **AC-6** - A resumed run finds its prior state from what the person hands it, by a stated, reproducible rule
- [x] **AC-7** - A re-critique's comparison against the previous envelope emits a stated, deterministic output
- [x] **AC-8** - Every edge `agents/_chain-permitted.yaml` declares for this chain carries at least one G3 eval whose expected output is a revision brief
- [x] **AC-9** - The README states beside N4 that the loop takes two invocations, and the docs state that the commitment covers the library, not a tool a person wires downstream
- [x] **AC-10** - No step of the chain itself requires a paid, model-calling measurement run to validate; every G3 eval and regression case runs on committed fixtures with no API call

## Purpose

`examples/recipes/revision-loop.md` documents the revision loop, critique, disposition, revise,
re-critique, entirely by hand: its own text says the v2 memo "is authored for this recipe" [S1].
N4 asks for that loop as an invokable chain with a real stopping rule, so Gold check G3 (chain and
hook eval coverage) has something real to evaluate instead of passing vacuously [S2]. ADR 0040
ruled, on 2026-10-25, who performs the "revise" step: the chain pauses and hands a revision brief
to a person, or to a tool the person runs on their own authority; the library never writes the
artifact [S3]. This spec frames the decisions ADR 0040 left open so N4 can be built: the chain's
name and shape, the brief's exact format, the contract change's exact field, and what the chain
contract and its G3 coverage have to contain, given how the pinned toolkit actually resolves a
chain edge.

## Scope

- A new component (name and type decided below) implementing the five-step chain ADR 0040 ruled.
- `contract/critique-contract.schema.json`: an optional iteration field on `$defs/dispositionLog`,
  at contract version 1.1.0.
- `contract/validate.py`, `contract/README.md`: coverage and documentation of the new field.
- A documented format for the revision brief, outside the contract (ADR 0040; E52 brief D3 [S4]).
- `agents/_chain-permitted.yaml` (new file; none exists on `main` today, verified: `git cat-file -e
  main:agents/_chain-permitted.yaml` fails) and at least one `evals/*.eval.json` per declared edge.
- `README.md`: a new entry for N4 (location set by D1), carrying a line stating the loop takes two
  invocations (ADR 0040). No such entry exists today; README mentions `examples/` twice, a link in
  the "Start here" table at line 26 and a generic pointer at line 289, and neither names N4 or the
  revision loop.
- `library.json`, `AGENTS.md`: the new component's registration, and, if the chosen component type
  is new to this plugin, the inventory line that names it.

## Non-Goals

- **No ruling on who performs revise.** ADR 0040 already decided this; see Requirements.
- **No build.** This is a spec, not code. Nothing here is implemented.
- **No change to the auto-fix exclusion or methodology section 10.** ADR 0040's TL;DR is explicit
  that no published wording moves [S3].
- **No E54 (cross-library composition) work.** The brief stays outside the versioned contract until
  E54 consumes it; moving it in is E54's decision, not this one [S4].
- **No G1 (hook documentation) coverage.** N4 introduces no hooks. G1 stays vacuous until something
  else ships a hook; E55 tracks G1 and G3 together but G1 is out of scope here [S5].
- **No paid, model-calling measurement run.** Decision D9 frames the alternative and its cost, but
  building or dispatching it needs the maintainer's own, separate approval.

## What the pinned toolkit's checks actually read

Four facts, each read directly from the pinned toolkit's own code rather than inferred from the
Standard's prose, because D1 and D6 below both turn on them and the E52 brief named this gap
outright: "What the chain contract file N4 names... has to contain for Gold check G3... I did not
read it for this brief" [S4, "What I do not know"].

1. **A chain-contract caller or callee name must be an on-disk skill or subagent, never a
   workflow.** S4's phantom check builds its known-name set from
   `[...(ctx.skills || []), ...(ctx.subagents || [])]` only; `ctx.workflows` is read elsewhere, only
   to decide whether a contract file must exist at all, and never feeds this set. [S11]
2. **A workflow's own `steps:` are not yet checked against the chain contract.** The Standard's
   prose (sec 3.4) requires it, but the toolkit's own workflow-builder reference says plainly: "A
   workflow-step chain-permission (orphan) check is a planned enhancement." [S13, S14]
3. **A workflow's `steps:` entries must each name an existing skill, and only a skill.** S5's own
   known-name set is `(ctx.skills || []).map(s => s.name)`, built with no subagent and no wildcard
   or pattern entry; "any registered `critique-<domain>` skill" cannot appear in frontmatter as one
   entry. [S22]
4. **G3 reads edges only from `agents/_chain-permitted.yaml`, nothing from `_workflows/`.** Its
   `contractEdges` function parses that one file and nothing else; an eval's `covers.chain` is
   matched against those edges by exact string pair. [S11]

## Requirements

Restating ADR 0040's ruling as binding inputs. None of these is reopened by this spec.

1. **The chain runs five steps, in order, and never writes the artifact.** Critique the artifact;
   take the person's dispositions into the disposition log; stop if no finding at severity 3 or
   above remains or if this was the third iteration; otherwise write the revision brief and pause;
   on resume with a new version, re-critique it, compare the result with the previous envelope, and
   return to step 2. "No step writes the artifact." [S3, line 123]
2. **The revision brief holds one entry per accepted finding: the finding, its location, its fix,
   and its criterion.** [S3, line 125]
3. **The brief is a documented format outside the versioned contract until a second consumer
   exists.** It moves into the contract schema, with validator coverage, when E54 (cross-library
   composition) consumes it. [S3, line 11; S4, D3]
4. **The disposition log gets an optional iteration field, added as contract version 1.1.0.** Every
   existing 1.0.0 disposition log stays valid, because the field is optional and a 1.0.0 document
   still validates against a 1.1.0 schema under ADR 0013's minor-version rule [S6, S7]. The chain
   writes the field on every iteration. [S3, line 128; S4, D2]

   **Where "1.0.0" to "1.1.0" actually has to move (implementation sites, verified).** The schema
   file's own `description` and `$comment` both assert "contract version 1.0.0" in prose (lines 5
   and 6) and need the same edit as the version bump itself. `contract/README.md`'s opening
   paragraph makes the same assertion ("it is JSON Schema draft 2020-12, contract version
   **1.0.0**") and needs the matching edit. `contract/validate.py`'s Rule 6 ("every integer-typed
   contract field must be a JSON integer literal") enumerates the specific fields it checks; the new
   iteration field must join that enumeration, or a value written as `"iteration": 2.0` would pass
   schema validation and the validator's own integer check alike. Whether this is a new, append-only
   rule or an extension of rule 6's existing list is D4's concern once the field's name is fixed. [S7,
   S20, S24]
5. **Each edge in N4's chain contract gets at least one eval, with the revision brief as its
   expected output.** [S3, line 132]
6. **The README states, beside N4, that the loop takes two invocations.** [S3, line 136; S3 TL;DR]
7. **The docs state the boundary: the commitment covers what the library does, not what a person
   builds downstream.** The library cannot stop a person wiring an automatic reviser to the brief;
   that is stated plainly rather than left implicit. [S3, line 135]
8. **The auto-fix exclusion and methodology section 10 stand exactly as published.** No wording in
   `ROADMAP.md`'s "Deliberately not doing" section or in methodology section 10 changes. [S3 TL;DR;
   S8, lines 342-350]

## Acceptance Criteria

AC-1: Running the chain against a fixture artifact and a disposition log produces, in order, a
critique envelope, a recorded disposition, a stop-check result, and (when the check says continue)
a revision brief; the artifact's own `artifact_sha256`, as recorded in the envelope before the run
and read from the file after it, is identical, so no step wrote to it. [S1, S3]

AC-2: Given an envelope with zero findings at severity 3 or 4, the chain's stop-check returns
"stop, converged" without writing a brief. Given an envelope with a severity-3 or higher finding and
an iteration count of 3, the stop-check returns "stop, bound reached" without writing a brief. Given
a severity-3 or higher finding and an iteration count below 3, it returns "continue" and a brief is
written. [S3, S8]

AC-3: For a disposition log in which N findings are accepted, the written revision brief contains
exactly N entries, each carrying that finding's `id` (or equivalent), `criterion`, `location`, and
`fix`, copied from the referenced envelope. [S3]

AC-4: Two runs of the brief-writing step against the same envelope and disposition log, with no
model call in between, produce byte-identical briefs (apart from a timestamp field, if one exists).
[Inferred from Requirement 2's wording, "holds," read as a projection rather than a judgment; not
separately sourced.]

AC-5: A disposition log with no iteration field validates against the 1.1.0 schema. A disposition
log with an iteration field of 1, 2, or 3 validates against the 1.1.0 schema. Every one of the 7
standalone disposition-log fixtures committed under `examples/*/dispositions.json` today
(`contract_version: "1.0.0"`, no iteration field) still validates unchanged. [S6, S9]

AC-6: Given the artifact's new version and the prior brief or disposition log (per D2's chosen
shape), the chain's resume step locates the prior envelope and iteration count with no ambiguity
when exactly one such record exists for that artifact, and reports an error naming the conflict
when more than one does. [S3; D2]

AC-7: Given two envelopes for the same artifact at different iterations, the comparison step emits
a per-criterion and per-severity count delta; it does not claim to match individual findings by ID
across the two envelopes. [S3; D5]

AC-8: `node .agent-skills-toolkit/scripts/tier-report.mjs "$(pwd)" --json`'s `blocked.advanced` list
carries no G3 item naming a chain edge this spec declares, and each declared edge's eval file states
`"covers": {"chain": [...]}` matching that edge exactly. (G3 is a burndown item at this plugin's
declared Convergent tier, not a gate failure, per `gold-checks.md`'s own line 10 [S10]; this AC
checks that the burndown item for N4's own edges is cleared, not that the whole gate turns strict.)
[S10, S11]

AC-9: `README.md` gains a new entry for N4, in a location D1's component type decides, that states
beside it the loop takes two invocations; and a page under `docs/` states that the commitment binds
the library's own code, not a tool the person runs on the brief. Verified: README carries no mention
of N4 or the revision loop today, only its two existing mentions of `examples/`: the "Start here"
table's link at line 26 and a generic pointer at line 289 to
"`examples/` | Worked walkthroughs for all seven skills, plus cross-cutting recipes". [S3, line
135-136; S17]

AC-10: Every `evals/*.eval.json` file this spec adds runs against a committed fixture (a golden
artifact, envelope, and disposition log already in the repository, or new ones added with this
build) with no `run.model` value outside a documented sentinel, and no test added by this spec calls
`bench/run_bench.py` without `--dry-run`. [S12]

## Sources & Evidence

- **[S1]** The hand-authored recipe - `examples/recipes/revision-loop.md` (read in full 2026-10-26;
  "The revised v2 memo is authored for this recipe") - class A
- **[S2]** N4's own backlog entry - `docs/internal/backlog/new-components.md`, lines 196-220
  ("## N4 - Revision loop as a first-class, invokable chain") - class A
- **[S3]** [ADR 0040 (the revision loop pauses with a revision brief)](../../../decisions/0040-revision-loop-pauses-with-a-revision-brief.md)
  (read in full 2026-10-26, cited by line number throughout) - class A
- **[S4]** The E52 decision brief, D2 and D3 -
  a local decision brief, not part of the shipped repository - class B (an uncommitted local artifact, read in full; ADR 0040 is the class
  A record of the same ruling, and is cited separately as [S3] wherever both agree)
- **[S5]** E55's own text - `docs/internal/backlog/enhancements.md`, lines 1201-1209 ("## E55 -
  Build chain and hook evaluation coverage") - class A
- **[S6]** [ADR 0013 (contract versioning)](../../../decisions/0013-contract-versioning-independent.md),
  "Minor (1.x.0)" rule - class A
- **[S7]** `contract/critique-contract.schema.json`, `$defs/contractVersion` (line 506,
  `"pattern": "^1\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)..."`, major pinned to 1) and
  `$defs/dispositionLog` (line 238, `"additionalProperties": false`, three allowed keys) - class A
- **[S8]** `docs/explanation/methodology.md`, section 10 "Human-in-the-loop by contract", lines
  342-350 (status Stable) - class A
- **[S9]** Count of committed disposition-log fixtures - `git grep -l "\"dispositions\":" main --
  examples/ contract/ docs/` returns 11 files (run 2026-10-26): the schema file itself, one doc page
  (`docs/how-to/dispositions.md`), one recipe with an inline disposition log in prose
  (`examples/recipes/revision-loop.md`), `contract/tests/fixtures.py` (embeds disposition-log
  fixtures in Python, not as a standalone JSON file), and exactly 7 standalone JSON fixtures,
  `examples/<domain>/dispositions.json` for accessibility, argument, clarity, docs, forms,
  microcopy, and usability. Separately, `git grep -l "\"contract_version\": \"1.0.0\"" main --
  contract/ docs/ examples/ skills/` returns 51 files total, the 11 above plus 40 envelope and
  golden-example fixtures that carry `contract_version` but are run envelopes, not disposition logs
  - class A (counted both ways, not estimated)
- **[S10]** `.agent-skills-toolkit/docs/reference/gold-checks.md`, G3 row and the paragraph below the
  table ("G3 is the baseline... the check delivers the presence half of it... The Standard
  explicitly defers the multi-tier eval engine... CI executes them is checked by nothing in the
  spine") - class A
- **[S11]** `.agent-skills-toolkit/scripts/checks/chain-contract.mjs` (S4, read in full 2026-10-26:
  `known` is built only from `ctx.skills` and `ctx.subagents`, never `ctx.workflows`, lines
  `const components = [...(ctx.skills || []), ...(ctx.subagents || [])];` and
  `const known = new Set(components.map((c) => c.name));`) and
  `.agent-skills-toolkit/scripts/checks/library-regression.mjs` (G3, read in full 2026-10-26: edges
  come only from `agents/_chain-permitted.yaml`, matched by exact string pair, with no check against
  `known`) - class A
- **[S12]** This task's own binding rules (the workflow harness's computed task text, not
  `AGENTS.md`): no `python bench/run_bench.py` without `--dry-run`, no `workflow_dispatch`, no paid
  run of any kind - class A (the task's own rules)
- **[S13]** `.agent-skills-toolkit/docs/reference/askit-build-workflow.md` ("A workflow-step
  chain-permission (orphan) check is a planned enhancement") - class A
- **[S14]** `.agent-skills-toolkit/STANDARD.md`, section 3.4 (Workflow, Convergent) and section 3.6
  (Chain contract, Convergent), read in full 2026-10-26 - class A
- **[S15]** `.agent-skills-toolkit/STANDARD.md`, section 3.8 (Frontmatter contract), the per-type row
  for Workflow (`steps`, `agent-targets`, `exit-criteria`; no `chain` key listed for workflows) -
  class A
- **[S16]** `library.json` (this plugin), line 9 (`"components": {`), with keys `skills` (7
  entries), `subagents` (1 entry), `commands` (0 entries); no `workflows` key present - class A
  (read directly, counted)
- **[S17]** `AGENTS.md` (this plugin), "Components" section (Skills, Subagents, Commands: none yet)
  and the CI table (lines 87-95, `conformance`, `unit-python`, `unit-node`, and the rest), plus the
  drift rule "`npm run gen -- --check` also enforces that every command in the table above appears
  in this file" (line 144) - class A
- **[S18]** `agents/critique-critic.md` frontmatter and "Invocation contract" section, read in part
  2026-10-26: no `metadata.chain` key is declared; delegation from every `critique-<domain>` skill to
  this subagent is described in prose (ADR 0004), not in frontmatter - class A
- **[S19]** `docs/how-to/dispositions.md`, the field table for `dispositionLog` and its entries,
  read in full 2026-10-26 - class A
- **[S20]** `contract/README.md`, "Disposition log" section and "Versioning and extension" section,
  read in full 2026-10-26 - class A
- **[S21]** The local walk record for that brief, not part of the shipped repository -
  class B (an uncommitted local artifact, read in full, not itself a ruled or published record;
  ADR 0040 is the class A record of the same ruling)
- **[S22]** `.agent-skills-toolkit/scripts/checks/workflow-skills.mjs` (S5, read in full 2026-10-26:
  `known` is built only from `ctx.skills`, with no subagent and no pattern or wildcard entry;
  `steps[].skill` must name exactly one existing skill) and
  `.agent-skills-toolkit/templates/workflow.md` (the scaffold's `steps:` entries are each one
  literal `skill:` name) - class A
- **[S23]** E73's spec, for its "Measurement and sequencing" section's counting
  convention (skill envelopes at k, tiers) -
  `docs/internal/release-plans/_unassigned/E73_merge-runs-scripted-lane/spec.md` (ruled 2026-10-23, built in PR 105) - class A
- **[S24]** `contract/validate.py`, `_rule_integer_literal`, line 481 (`"""Rule 6: every
  integer-typed contract field must be a JSON integer\n    literal.`) - class A

## Open Questions / Decisions

| ID | Title | Resolution | Status | Updated |
|----|-------|------------|--------|---------|
| D1 | The chain's name, component type, and entry point | Option A | Decided | 2026-10-30 |
| D2 | The invocation shape across the pause, and how a resumed run finds its prior state | Option A | Decided | 2026-10-30 |
| D3 | The revision brief's file name, location, format, and field names | Option A | Decided | 2026-10-30 |
| D4 | The iteration field's name, and whether the contract bounds it structurally at 3 | Option A | Decided | 2026-10-30 |
| D5 | What the re-critique comparison step outputs | Option A | Decided | 2026-10-30 |
| D6 | What `agents/_chain-permitted.yaml` must declare, given how the pinned toolkit actually resolves a chain edge | Option A | Decided | 2026-10-30 |
| D7 | Which skills the chain accepts | Option A | Decided | 2026-10-30 |
| D8 | Where the G3 eval and regression cases live, and where CI runs them | Option A | Decided | 2026-10-30 |
| D9 | Whether N4 needs any model-calling measurement, or only deterministic evals | Option A | Decided | 2026-10-30 |

### D1: The chain's name, component type, and entry point (Decided)

**Summary.** Decide what N4 is called, which Standard component type it registers as, and how a
person starts it.

**Context.** The backlog entry calls N4 "a chain" with "the contract at
`agents/_chain-permitted.yaml`" [S2], but the Standard does not define "chain" as a registrable
component type: that file is a governance list of which skills or subagents may invoke which
others (sec 3.6), and the component type built for "an ordered arc chaining multiple skills toward
an outcome" is the **Workflow** (sec 3.4) [S14]. This plugin registers no workflow today;
`library.json`'s `components` object carries only `skills`, `subagents`, and `commands` keys, the
last empty [S16].

**Desired outcome.** A name that cannot be misread (the N5 rename away from `critique-checkout`
because it read as `git checkout` is the test [S2, N5 section]), a component type the pinned Standard
actually gates correctly, and a clear instruction for how a person starts the first invocation and
the second.

**Options / approaches.**

* **Option A:** A Workflow, `_workflows/critique-revision-loop.md`, registered under a new
  `library.json` `components.workflows` key. Its documented steps are the five from Requirement 1.
  A person starts it by following the workflow page, which names the exact commands for each step
  (run a `critique-<domain>` skill, record dispositions, run the stop-check script, read the brief).
  Fits the Standard's own vocabulary for this exact shape (sec 3.4) [S14]. Costs a first-of-its-kind
  registration: `library.json`, `AGENTS.md`'s component index, and `INDEX.md` generation all gain a
  workflow entry. It also costs a real constraint on the frontmatter `steps:` list itself: S5 checks
  each `steps[].skill` entry against on-disk skill names one at a time, with no subagent and no
  pattern entry [S22], so "any of the seven skills D7 accepts" cannot be written as a single
  parametrized step; it is either one literal `steps:` entry per accepted skill, or the skill choice
  is left to the body prose and `steps:` names only the two literal invocations (critique,
  re-critique) a single run actually performs.
* **Option B:** A Command, `/critique-revision-loop`, mapping (`maps-to`) to a new skill that holds
  the full five-step protocol in its own `SKILL.md`. A person runs the command twice by name, which
  matches ADR 0040's "two invocations" language most literally [S3]. Costs folding stateful,
  non-rubric bookkeeping (the stop-check, the brief write) into a component type built around
  rubric-matched model judgment, which is an odd fit: a skill's description is matched by a model
  against a request (sec 8.1), and nothing here needs that matching once the person has already
  chosen to run the loop.
* **Option C:** No new registered component. Promote `examples/recipes/revision-loop.md` into a
  documented, scriptable recipe (in the style of `examples/recipes/gate-in-ci.md`) plus a script
  under `scripts/` that a person runs twice. Keeps "the library never writes the artifact" visually
  obvious (it is a recipe, not a governed component), and avoids every question this decision raises
  about workflow registration. Costs the clearest reading of the backlog entry's own "done looks
  like: an invokable chain" [S2], and gives G3 nothing new to evaluate on its own, which is the
  problem N4 exists to fix.

**Recommendation.** Option A, medium confidence. It is the Standard's own name for this shape, it
is what gives the plugin's component index an honest new line rather than a recipe dressed as
infrastructure, and the per-step scripts it documents are exactly what Option C would also need. The
workflow-step chain-permission check is a documented planned enhancement, not yet built [S13], so
choosing Option A does not by itself create any new S4 or G3 obligation; D6 frames what does.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: a Workflow, `_workflows/critique-revision-loop.md`, under a new `library.json` `components.workflows` key
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. It is the Standard's own name for this shape.
> * **Follow-up:** Build in N4's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/N4_revision-loop-chain/spec.md`; it includes the first workflow registration in `library.json`, `AGENTS.md` and `INDEX.md`.
> * **Decided by / date:** jprisant / 2026-10-30

### D2: The invocation shape across the pause, and how a resumed run finds its prior state (Decided)

**Summary.** Decide what a person passes on the first invocation, what they get back, and what they
pass on the second invocation so the chain knows which artifact, which prior envelope, and which
iteration it is resuming.

**Context.** ADR 0040 fixes the five steps and says the loop "takes two invocations" but leaves the
mechanics of finding state across them to N4's spec [S3]. The iteration count lives in the
disposition log once D4 is settled (Requirement 4), but a disposition log is keyed to one envelope
by `skill`, `artifact_sha256`, and `timestamp` [S19], not to "the artifact's current revision in
general." A resumed run needs to find the right prior disposition log (or brief) for the new
artifact version, not an arbitrary one.

**Desired outcome.** A rule simple enough that a person (or a script acting on their behalf) can
state unambiguously, on the second invocation, which prior run this is a resumption of, with no
silent fallback to "the newest file in a folder."

**Options / approaches.**

* **Option A:** The person passes the path to the prior disposition log explicitly on the second
  invocation, alongside the new artifact. No implicit location convention exists; the chain reads
  whatever log it is handed and trusts the person to have picked the right one. Matches how the
  existing worked recipe already treats envelope and disposition-log files, as separate, explicitly
  named documents [S1].
* **Option B:** A fixed naming convention colocates state beside the artifact:
  `<artifact>.disposition-log.json` and, when paused, `<artifact>.revision-brief.json`. The second
  invocation looks for these two names next to the new artifact path with no argument needed beyond
  the artifact itself. Cheaper to invoke; silently wrong if the person renamed or moved the artifact
  between iterations.
* **Option C:** A `.critique/` state directory per project, keyed by a stable identifier (the
  artifact's original path, not its current one) rather than by filename colocation. Most robust to
  a renamed artifact; adds a new on-disk convention this plugin has never used anywhere else.

**Recommendation.** Option A, medium confidence. It costs the person one more argument on the second
invocation and nothing else; it introduces no new filename or directory convention for N4's build to
define and the toolkit's checks to learn about; and it fails loudly (wrong file, wrong resolution)
rather than silently (wrong file picked by a naming guess).

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: the person passes the prior disposition log's path on the second invocation
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. It costs one argument and fails loudly rather than guessing.
> * **Follow-up:** Build in N4's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/N4_revision-loop-chain/spec.md`.
> * **Decided by / date:** jprisant / 2026-10-30

### D3: The revision brief's file name, location, format, and field names (Decided)

**Summary.** Decide the brief's exact file name or naming pattern, where it is written, its
serialization, and the name of each field inside it.

**Context.** ADR 0040 fixes the brief's content, one entry per accepted finding, with the finding,
its location, its fix, and its criterion, and rules that it is documented outside the versioned
contract until E54 consumes it [S3, S4-D3]. Nothing yet fixes its file name, its exact JSON field
names, or whether it carries anything besides the four named items (an envelope reference, so a
re-critique has something to resume against, and the iteration count, so the stop-check at resume
does not need to re-derive it from the disposition log alone).

**Desired outcome.** A shape G3's eval `expect` field can assert against byte-for-byte or
structurally, that a reader who has never seen this spec can understand from the docs alone, and
that does not duplicate fields the disposition log or envelope already carry in an inconsistent
name.

**Options / approaches.**

* **Option A:** A single JSON document per pause, named `<artifact-stem>.revision-brief.json` beside
  the artifact by default (independent of whichever resolution rule D2 picks for finding state on
  resume, since a brief needs a name the moment it is written, before any resume happens), with
  top-level `envelope` (same shape as
  `dispositionLog.envelope`, reused rather than reinvented [S19]), `iteration`, and `items`, an array
  of `{finding_id, criterion, location, fix}`, field names matching the finding object's own field
  names exactly [S20] so no renaming happens at the brief boundary.
* **Option B:** The same fields, but as Markdown prose, one bullet per accepted finding, for a human
  reader to act on directly with no JSON tooling. Costs a second, harder-to-assert format for G3's
  eval, whose `expect` is strongest against a structured document.
* **Option C:** Both: a JSON document as the structured source of truth, and a generated Markdown
  rendering of it for a person reading by hand, in the style this plugin already uses for machine
  output paired with a human summary (the envelope plus the curated README catalog is one example
  of the pattern, though not the same documents).

**Recommendation.** Option A, medium confidence. It is the cheapest shape to assert against in a G3
`expect`, and it reuses the disposition log's own `envelope` shape and the finding schema's own field
names rather than inventing parallel vocabulary, which keeps the eventual E54 contract addition
(Requirement 3) a straightforward lift rather than a rename. Option C is worth it once a person is
actually expected to read briefs by hand often; nothing in the ADR requires that yet.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: one JSON brief per pause, `<artifact-stem>.revision-brief.json`, with `envelope`, `iteration` and `items`
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. It is the easiest shape for an eval to assert, and it reuses the contract's field names.
> * **Follow-up:** Build in N4's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/N4_revision-loop-chain/spec.md`; a Markdown rendering (Option C) waits until people read briefs by hand often.
> * **Decided by / date:** jprisant / 2026-10-30

### D4: The iteration field's name, and whether the contract bounds it structurally at 3 (Decided)

**Summary.** Decide the exact property name added to `$defs/dispositionLog` for contract 1.1.0, and
whether its schema enforces the three-iteration bound as a maximum, or leaves the bound to the
chain's own logic.

**Context.** ADR 0040 rules that the field is optional, minor version 1.1.0, on the disposition log
[S3]. It does not name the field. `$defs/dispositionLog` today has exactly three properties,
`contract_version`, `envelope`, `dispositions`, with `additionalProperties: false` [S7], so the new
property is additive, not a replacement. The bound itself, "after three iterations," is a
methodology rule (section 10, [S8]), not stated as a number inside the schema anywhere today.

**Desired outcome.** A field name a reader can guess correctly from the methodology's own wording,
and a decision about whether the schema is the place that enforces the bound or only the place that
records which iteration a given log belongs to.

**Options / approaches.**

* **Option A:** `iteration`, type integer, `minimum: 1`, no stated maximum in the schema. The chain's
  own stop-check logic enforces the bound at 3; the field is a plain record of fact, not a rule.
* **Option B:** `iteration`, type integer, `minimum: 1, maximum: 3`. The schema itself rejects a
  fourth iteration's log, which hard-codes methodology section 10's specific number into contract
  1.1.0 and makes a future change to the bound (were section 10 ever revised) a contract change too.
* **Option C:** `revision_iteration`, to avoid colliding with any future unrelated use of the bare
  word "iteration" elsewhere in the contract; otherwise as Option A.

**Recommendation.** Option A, medium confidence. The field's job, per ADR 0040, is to let a resumed
chain know which of its three iterations it is on [S3, TL;DR], which is a record, not an
enforcement point; enforcement already belongs to the chain's own stop-check (Requirement 1), and
keeping a methodology number out of the schema keeps a future change to that number from forcing a
major contract version. `iteration` is unambiguous enough in context that Option C's longer name adds
nothing a reader needs.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: `iteration`, integer, `minimum: 1`, no schema maximum; the stop-check enforces 3
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. The field records a fact; the chain enforces the bound.
> * **Follow-up:** Build in N4's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/N4_revision-loop-chain/spec.md`; contract 1.1.0, with `contract/validate.py` rule 6 covering the field.
> * **Decided by / date:** jprisant / 2026-10-30

### D5: What the re-critique comparison step outputs (Decided)

**Summary.** Decide what "compare the result with the previous envelope" (step 5 of Requirement 1)
actually produces, and where that output lives.

**Context.** A finding's `id` is unique only within its own envelope [S19], and `location` is free
text written against a specific version of the artifact [S20], so neither is a safe key for matching
one finding in the new envelope to "the same" finding in the old one across a revision. A criterion
ID, by contrast, is stable across runs. ADR 0040 requires the comparison step to exist but does not
say what it emits [S3].

**Desired outcome.** A comparison a person can read in one glance to see whether the revision worked,
that does not claim a finding-level correspondence the data cannot support.

**Options / approaches.**

* **Option A:** A per-criterion and per-severity count delta: for each criterion present in either
  envelope, the count at this iteration minus the count at the last one, plus the same delta on
  `summary.by_severity`. No claim that finding `F-003` in the new envelope "is" finding `F-003` in
  the old one.
* **Option B:** A full finding-level diff, pairing findings across envelopes by a similarity
  heuristic on `location` and `evidence`. Gives a more satisfying "fixed vs. still broken" answer when
  it works, but the pairing is heuristic, not deterministic, which is a weak foundation for a G3
  `expect` that has to be asserted exactly.
* **Option C:** No stored comparison output at all; the person reads the two envelopes side by side.
  Costs nothing to build, but leaves "compare" as a step ADR 0040 named with nothing concrete to show
  for it, and gives G3 nothing to assert for this edge of the chain.

**Recommendation.** Option A, high confidence. It is the only one of the three that is fully
deterministic from the two envelopes alone, which is exactly the property a G3 eval's `expect` needs,
and it does not promise a per-finding correspondence the contract's own ID scoping rules out.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: per-criterion and per-severity count deltas
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. It is the only fully deterministic option.
> * **Follow-up:** Build in N4's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/N4_revision-loop-chain/spec.md`.
> * **Decided by / date:** jprisant / 2026-10-30

### D6: What `agents/_chain-permitted.yaml` must declare, given how the pinned toolkit actually resolves a chain edge (Decided)

**Summary.** Decide which concrete caller-to-callee edges N4's chain contract declares, given what
the pinned toolkit's checks actually read, not only what the Standard's prose says.

**Context.** This is the one unknown the E52 brief named outright: "What the chain contract file N4
names... has to contain for Gold check G3... I did not read it for this brief" [S4, "What I do not
know"]. Per "What the pinned toolkit's checks actually read" above, a workflow's name cannot appear
in `agents/_chain-permitted.yaml` as a caller or callee (it is a phantom under S4), and a workflow's
`steps:` carry no chain-permission check yet regardless of what the Standard's prose intends [S11,
S13]. The real candidate edges are therefore between already-resolvable components: a
`critique-<domain>` skill and the `critique-critic` subagent. That delegation runs on every
critique and every re-critique this chain performs, and it is real but currently undeclared:
`agents/critique-critic.md` carries no `metadata.chain` key, and no skill's frontmatter declares
`chain: critique-critic` [S18]. Nothing breaks by leaving it undeclared, but G3 then has no real
edge for N4 to evaluate unless this spec is what declares one.

**Desired outcome.** A contract file that actually earns the G3 coverage E55 is waiting on [S5],
built from edges the pinned checks can resolve, not from a caller name the checks cannot see.

**Options / approaches.**

* **Option A:** Formalize the existing-but-undeclared delegation. Each `critique-<domain>` skill this
  chain can run (see D7) adds `metadata.chain: critique-critic` to its frontmatter; the contract gets
  one entry per accepted skill, `critique-<domain>: [critique-critic]`; one `evals/*.eval.json` per
  edge, each with the revision brief as its `expect` (Requirement 5). Costs editing every accepted
  skill's frontmatter, which is a small, mechanical, well-scoped change, and is the option the G3
  eval's "revision brief as expected output" wording [S3, line 132] fits most literally, since the
  eval asserts the loop's own behavior, not merely the bare delegation. If this lands in the same
  release as E73 (the merge-step spec, unruled, draft only [S23]), E73's own D4 already moves every
  skill's version once for an unrelated reason; this option's frontmatter edit can ride that same
  move rather than open a second version question. If N4 ships on its own, this option raises a
  version question (does adding `metadata.chain` move a skill's version) this spec does not resolve.
* **Option B:** Narrow to the one skill the existing worked recipe already uses,
  `critique-argument: [critique-critic]` [S1], and widen to the rest only when D7 widens the chain's
  accepted skills. Lower first-build cost; defers most of the real coverage E55 is waiting on.
* **Option C:** Declare no new edge at all. Per sec 3.6's own conditional-MUST wording, "a plugin
  that contains no inter-component invocation is NOT required to ship a `_chain-permitted.yaml`"
  [S14]. This keeps N4's build smallest, but it leaves G3 exactly as vacuous as it is today, which
  is the condition N4's own backlog entry names as the reason to build the contract file at all [S2].

**Recommendation.** Option A, medium confidence. It is the smallest change that gives G3 real,
resolvable edges rather than none, it does not invent a new orchestration component purely to have
something chainable (writing a brief or comparing two envelopes is a deterministic script, not a
model-judgment step, so it should not become a subagent only to earn a chain edge), and D7's own
recommendation (all seven skills) sizes the resulting edge count directly.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: declare `critique-<domain>: [critique-critic]` for every accepted skill, with `metadata.chain` in each skill's frontmatter and one eval per edge
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. The draft's note about riding E73's version moves is stale: E73 is built and its moves happened on 2026-10-28. The walk read a frontmatter metadata key as not a prose change to the measured prompt, so it moves no skill version (medium confidence, inferred).
> * **Follow-up:** Build in N4's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/N4_revision-loop-chain/spec.md`; if the build finds the key does change what a skill run reads, raise the version question before merging.
> * **Decided by / date:** jprisant / 2026-10-30

### D7: Which skills the chain accepts (Decided)

**Summary.** Decide whether the revision-loop chain runs against any registered `critique-<domain>`
skill, a named subset, or starts with one pilot skill.

**Context.** The five-step loop (Requirement 1) is written in skill-agnostic terms: critique,
disposition, stop-check, brief, resume. Nothing in the loop's own logic depends on which skill
produced the envelope, since every skill emits the same contract-valid envelope and disposition-log
shape. The only worked illustration that exists today uses `critique-argument` [S1]. `library.json`
currently registers seven skills [S16], all `active` per AGENTS.md's own component list.

**Desired outcome.** A scope statement that does not silently under-serve a skill the maintainer
expects to use the loop with, and that sizes D6's edge count correctly.

**Options / approaches.**

* **Option A:** All seven registered, `active` `critique-<domain>` skills, uniformly. The loop's
  logic reads only the contract, which every skill already satisfies identically.
* **Option B:** Start with the one skill the existing recipe already illustrates, `critique-argument`,
  and widen to the rest in a later change once the chain is built and measured once.
* **Option C:** Any skill the person names at invocation time, registered or not, with no
  enumeration in the chain's own definition; the chain contract gains an edge only for a skill it is
  actually run against, added on demand rather than declared up front for all seven.

**Recommendation.** Option A, medium confidence. The loop's own logic does not distinguish skills,
so restricting it to one or a few buys nothing in build cost and would read as an arbitrary
limitation to a maintainer who reaches for it on an eighth or ninth skill later (including N5,
`critique-payment-checkout`, once it ships). Option C costs an on-demand contract edit every time a
new skill is used with the loop, which is friction without a corresponding safety benefit, since
every registered skill already emits the same contract-valid shape the loop depends on.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: all seven registered skills, uniformly
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. The loop reads only the contract, which every skill satisfies identically.
> * **Follow-up:** Build in N4's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/N4_revision-loop-chain/spec.md`.
> * **Decided by / date:** jprisant / 2026-10-30

### D8: Where the G3 eval and regression cases live, and where CI runs them (Decided)

**Summary.** Decide the eval files' location and count, and which CI job executes the behavioral
cases inside them (not merely checks their presence).

**Context.** G3's deterministic half, checked by `library-regression.mjs`, only confirms that an
`evals/*.eval.json` file exists per declared edge and that its `covers.chain` names a permitted edge;
it does not execute the `cases` array inside the file at all [S10, S11]. "CI executes them" (the
Standard's own G3 wording) is therefore something this plugin's own test suite has to do, not
something the toolkit's spine does for it [S10]. This repository's CI table runs nine named jobs,
each one command, with a drift check that fails if the table and `AGENTS.md`'s own listing disagree
[S17].

**Desired outcome.** Eval presence that satisfies the structural half of G3 today, and execution of
the behavioral cases that does not require a new CI job, since a new job means editing both the
workflow file and `AGENTS.md`'s table and `ci-ok`'s dependency list in the same change.

**Options / approaches.**

* **Option A:** One `evals/*.eval.json` file per declared edge (count set by D6 and D7's
  resolutions), each with a `covers.chain` pair and one or more `{given, expect}` cases. The
  behavioral cases are executed by new tests under `contract/tests/` or
  `skills/_shared/tests/`, parametrized the way `skills/_shared/tests/` already parametrizes over
  registered skills, run by the existing `unit-python` job (`python -m pytest`) with no new CI job.
* **Option B:** As Option A, but the executing tests live in a new top-level `evals/tests/`
  directory, run by a new CI job dedicated to eval execution. Keeps eval execution visually
  separate from the rest of the test suite, at the cost of a new job that both `AGENTS.md`'s CI
  table and its `ci-ok` `needs` list must be edited to include, in the same change, or the `drift`
  job fails [S17].
* **Option C:** The `cases` arrays are documentation only, read by a person, with no executing test
  at all. Satisfies G3's structural presence check, which is all the toolkit's spine actually grades
  at this plugin's declared tier [S10], but does not satisfy the Standard's own "CI executes them"
  wording in substance, only in the letter the spine happens to check.

**Recommendation.** Option A, medium confidence. It reuses an existing, already-drift-checked CI job
rather than adding a tenth named job for one new eval suite, and it gives the eval cases a real,
executing test rather than leaving G3's behavioral half true only because nothing checks it.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: one `evals/*.eval.json` per edge, executed by pytest in the existing `unit-python` job
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. It needs no new CI job.
> * **Follow-up:** Build in N4's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/N4_revision-loop-chain/spec.md`.
> * **Decided by / date:** jprisant / 2026-10-30

### D9: Whether N4 needs any model-calling measurement, or only deterministic evals (Decided)

**Summary.** Decide whether validating N4 needs a live, model-calling run at all, beyond the
deterministic G3 evals D8 frames, and if so, size it rather than build it.

**Context.** Every step the chain itself performs (Requirement 1) is deterministic bookkeeping: the
stop-check is arithmetic over an existing envelope's `summary`, and the brief is a projection of an
envelope and a disposition log (Requirement 3, AC-4). The two steps that do call a model, critique
and re-critique, are each already the job of a `critique-<domain>` skill, which is independently
measured through the bench harness today; N4 does not change what either skill does or reports. This
task's binding rules forbid any paid, model-calling run and any `workflow_dispatch` without
explicit separate approval.

**Desired outcome.** A measurement plan that validates the chain's own new logic without re-running
work that is already measured elsewhere, stated with enough cost detail that a maintainer who wants
the live option anyway can approve it knowing what it costs.

**Options / approaches.**

* **Option A:** Deterministic evals only (D8), over committed golden fixtures (existing or newly
  authored envelopes and disposition logs), with no model call anywhere in the test suite this spec
  adds. The critique and re-critique steps are exercised by feeding the chain's bookkeeping logic a
  committed envelope directly, never by invoking a skill live.
* **Option B:** One live, model-calling smoke test: run the full two-invocation loop once, end to
  end, against one golden artifact (for example `critique-argument`'s `golden-01`), at k=1, on one
  pinned tier. Counted, not estimated: one invocation of critique plus one of re-critique is 2 skill
  envelopes; at k=1 on one tier that is 2 envelopes total; at k=5 on both pinned tiers, the
  measurement unit this project's other specs count in [S23], that would be 2 (critique,
  re-critique) x 5 (k) x 2 (tiers) = 20 skill envelopes. This option needs the maintainer's own,
  separate, explicit approval before any dispatch, per this task's binding rules, and is not
  pre-approved by this spec.
* **Option C:** No measurement of any kind, deterministic or live, treating the chain as adequately
  covered by the critique skills' own existing bench figures. Cheapest, but gives nobody evidence
  that the chain's own new logic, the stop-check and the brief, behaves correctly on a real envelope
  shape rather than only on a hand-constructed fixture.

**Recommendation.** Option A, high confidence. The chain's own new logic is deterministic and fully
testable against committed fixtures; the only genuinely model-dependent behavior in the loop belongs
to skills that are already measured on their own schedule. Option B is worth having eventually as a
realism check, but it is not needed to validate what N4 itself adds, and this task's own rules bar
building or dispatching it without the maintainer's separate go-ahead.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: deterministic evals only, no model call
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. The chain's new logic is fully testable on committed fixtures.
> * **Follow-up:** None needed; a live smoke run (Option B) would need its own paid go.
> * **Decided by / date:** jprisant / 2026-10-30

## What I do not know

- Whether `library.json`'s JSON Schema (wherever it is validated, if anywhere beyond the toolkit's
  own `components-index` check) accepts a new `workflows` key without a separate schema change; I
  read the Standard's own description of the key (sec 5.1, [S14]) but did not find or read a JSON
  Schema file for `library.json` itself in this repository.
- Whether `scripts/gen-readme-catalog.mjs` or `scripts/check-site.mjs`, which generate parts of
  `README.md` and the documentation site from `library.json` and skill frontmatter, would need
  changes to carry a workflow entry or the "two invocations" note; I did not read either generator.
- Whether any of the seven `critique-<domain>` skills' existing `SKILL.md` pass-4 or delegation text
  (beyond `agents/critique-critic.md`'s own frontmatter, which I did read) already uses wording that
  would conflict with adding `metadata.chain: critique-critic`; I read the critic's own frontmatter
  but not all seven skills' `SKILL.md` files in full.
- The exact cost, in dollars or tokens, of the Option B measurement in D9; I counted envelopes, not
  price, and this spec's own rules bar me from looking up current per-token pricing against a paid
  run that is explicitly out of scope to draft further.
- Whether `docs/internal/release-plans/README.md` or the v0.3.0 exit gate (referenced in ROADMAP.md
  and the backlog but not read in full for this spec) names N4 as a gating condition with its own
  stated acceptance language that this spec's AC-1 through AC-10 should match more closely; I read
  the N4 and E55 backlog entries and ADR 0040, not the full v0.3.0 exit-gate document.
