---
id: E48
title: "Begin disposition telemetry (acceptance rate per criterion)"
type: spec
status: committed
created: 2026-10-27
updated: 2026-11-03
linked-effort: docs/internal/backlog/enhancements.md
linked-plan: null
linked-release: v0.3.0
ac-count: 8
source-count: 22
requires-human-review: true
spec-dependencies: []
target-release: v0.3.0
---

# Spec: begin disposition telemetry, acceptance rate per criterion (E48)

Ruled by the maintainer on 2026-10-30 (the eight decisions below), and not built yet. E48 (begin disposition telemetry: acceptance rate per criterion) is a condition of the v0.3.0 exit gate in [the roadmap](../../../../../ROADMAP.md). The body below is the draft the maintainer ruled on, so a note that was true on 2026-10-27 can be out of date: where it calls N4 (the revision-loop chain) an unruled draft, N4 was ruled on 2026-10-30, and [its spec](../N4_revision-loop-chain/spec.md) sits beside this one.

## Task Summary

**Status:** ruled 2026-10-30, not built
**Last updated:** 2026-11-03 by Claude, promoted from a local draft after the 2026-10-30 walk
**Linked plan:** not yet planned
**Open questions:** 0 (all eight were decided 2026-10-30; see Open Questions / Decisions)
**Revisions:** 0

### Acceptance Criteria Fulfillment

- [ ] **AC-1** - A disposition log counted by the aggregation script carries a provenance marker, set
      by D2's chosen mechanism, that distinguishes it from every authored or illustrative log already
      committed under `examples/*/dispositions.json`
- [ ] **AC-2** - No step of collecting, storing, or aggregating a real-use disposition log adds a
      network call; `SECURITY.md`'s statement that the bench harness is the one network call this
      repository makes stays true, unamended, after E48 ships
- [ ] **AC-3** - Nothing committed to the repository under E48 carries a finding's `note` text or a
      run envelope's `artifact` or `path` field, per D4's chosen storage shape
- [ ] **AC-4** - The aggregation script resolves a disposition's `criterion` from the referenced
      envelope when the log's own denormalized `criterion` field is absent, and excludes any finding
      whose resolved `rubric_source` is `byor` from every published rate
- [ ] **AC-5** - The aggregation script reports a criterion's accept rate only when that criterion's
      disposed-finding count meets the stated minimum; below it, the table shows the count and
      "insufficient data," never a rate
- [ ] **AC-6** - The published acceptance table is generated from a committed aggregate file, never
      hand-edited, following the same `<!-- marker:start/end -->` discipline `bench-results` already
      uses
- [ ] **AC-7** - The aggregation script runs unchanged against a disposition log that carries ADR
      0040's optional `iteration` field and against one that does not
- [ ] **AC-8** - The v0.3.0 exit gate's own three E48 conditions are each met by a named, committed
      artifact: a collection path, an aggregation script, and a published first acceptance table

## Purpose

`ROADMAP.md`'s v0.3.0 exit gate names three things E48 must produce: "Disposition logs from real use
are collected, an aggregation script turns them into acceptance rates per criterion, and the first
acceptance table is published" [S1]. The gate defines "real use" in the same sentence: "runs on real
artifacts, including the maintainer's own, not bench runs," and explicitly excludes the first pruning
pass from this gate, "because it needs months of dispositions" [S1]. E48's own backlog entry restates
the goal and flags one concrete gap: the "deprecate, never delete" rule the pruning pass will need
has no schema field or tooling yet [S2]. Nothing in the repository today collects a disposition log
from outside a hand-authored example or golden fixture, aggregates one into a rate, or publishes one.
This spec frames the decisions that have to be ruled before any of the three gate conditions can be
built.

## Scope

- A stated, narrow definition of which disposition logs count as "real use" for v0.3.0 (D1).
- A provenance mechanism that lets a reader, and the aggregation script, tell a real-use log apart
  from the `examples/*/dispositions.json` fixtures and any future authored illustration (D2).
- A stated collection path: what a contributor does to get a real disposition log into the
  aggregate, and whether anything leaves their machine automatically (D3).
- A stated storage shape for what is actually committed to this public repository (D4).
- The aggregation script's inputs, outputs, rate definition, and minimum sample size per criterion
  (D5).
- The publication mechanism and its required caveats (D6).
- An explicit statement of what E48 does and does not do toward criterion pruning (D7).
- The rule for excluding BYOR-sourced findings (`rubric_source: byor`) from a published rate (D8).

## Non-Goals

- **No ruling on any decision below.** This spec frames eight open questions; it rules none of them.
- **No build.** This is a spec, not code. Nothing here is implemented.
- **No criterion pruning pass.** The gate text itself excludes it from this item, stating plainly
  that it needs months of dispositions E48 has not yet collected [S1]. D7 frames only the boundary
  between this item and that future one.
- **No change to the measured-only rule or to how BYOR is measured.** ADR 0039 already ruled that
  BYOR is measured by parity, not by acceptance rate [S12]; D8 only frames how BYOR findings are kept
  out of the acceptance-rate signal, not how BYOR itself is measured.
- **No new network call.** D3 frames this as a near-certain conclusion, not an open design space;
  see D3's recommendation.
- **No opt-in contributor outreach plan.** D1's options name "opt-in contributors" as a possible
  future source; recruiting them is not this spec's job even if that option is chosen.

## Requirements

Restating what is already ruled elsewhere. None of this is reopened by this spec.

1. **"Real use" excludes bench runs and includes the maintainer's own use.** The gate text's own
   wording: "Real use means runs on real artifacts, including the maintainer's own, not bench runs."
   [S1]
2. **The first pruning pass is out of scope for this gate.** "The first pruning pass is not part of
   this gate, because it needs months of dispositions." [S1]
3. **A disposition log's shape is frozen at contract 1.0.0 today, and E48 may not change required
   fields.** `contract_version`, `envelope`, and `dispositions` are required, `additionalProperties`
   is `false`, and an entry's `finding_id` and `disposition` are required with `note`, `criterion`,
   and `decided_at` optional [S3, S4]. Any new field is additive only, under a minor contract bump,
   per ADR 0013's rule that "a 1.0.0 document still validates against a 1.1.0 schema" [S22].
4. **ADR 0040 already adds one optional field to the disposition log at contract 1.1.0.** The
   `iteration` field, for the N4 revision-loop chain, riding the same minor-version mechanism [S11].
   Whatever E48 adds, if anything, must coexist with it; neither is a required field, so a log with
   one, both, or neither still validates.
5. **Acceptance rate per criterion is the library's pruning signal, as already stated.** Methodology
   section 8: "criteria that consistently produce rejected findings are either badly operationalized
   or not worth checking, and get revised or retired." [S9] Methodology section 10 names the same
   signal as one of three jobs the disposition log does. [S9]
6. **A criterion once published is never deleted, only marked deprecated in its skill's registry.**
   `docs/reference/criterion-ids.md`'s permanence rule 2 [S10]. No registry carries a deprecated
   marker today; `critique-clarity`'s registry (`references/PLAIN.md`, `references/WILLIAMS.md`) is a
   table with no status column [S21], and E48's own entry names this as a known gap [S2].
7. **`bench/metrics` does not score a disposition log today.** It explicitly treats a document
   carrying a `dispositions` key as "not scored" [S8]. No code anywhere computes an acceptance rate.
8. **The repository makes exactly one network call today, from the bench harness, and it is
   opt-in and explicit.** `SECURITY.md`: "Nothing else in this repository makes a network call." [S15]
9. **BYOR is measured by parity, not by acceptance rate.** ADR 0039 rules the BYOR measurement method
   on one flagship skill; it does not touch disposition-based acceptance rate at all [S12].
10. **A BYOR-marked finding is not always identifiable by its criterion namespace alone.**
    `contract/README.md`'s own statement: "a user rubric may declare its own namespace, and no
    document records which mode a run was in." [S4]
11. **Generated tables in this repository follow a fixed discipline: edit the source, never the
    marker, and CI fails a hand-edit.** `CONTRIBUTING.md`'s "Generated files" section, and the
    `bench-results` marker pattern in `bench/README.md` and `README.md` [S16, S19].

## Acceptance Criteria

AC-1: Given a committed disposition log, the aggregation script can determine, with no inference
beyond D2's stated mechanism, whether it is a real-use log or an authored example; running it against
the 7 committed `examples/*/dispositions.json` fixtures and against `examples/recipes/revision-loop.md`'s
inline disposition log excludes every one of them from the published rate. [S6, S7]

AC-2: `SECURITY.md`'s "Nothing else in this repository makes a network call" sentence requires no
edit after E48 ships; a diff of `SECURITY.md` before and after shows no change to that section. [S15]

AC-3: Grepping every file E48 commits under its chosen storage path for the literal strings `"note"`,
`"artifact"`, and `"path"` inside a disposition-log-shaped JSON object returns no match. [S4]

AC-4: Given a disposition entry with no `criterion` field, the aggregation script resolves it from
the referenced envelope's matching finding; given a resolved finding whose envelope marks
`rubric_source: "byor"`, that finding's disposition is excluded from every per-criterion count in the
script's output. [S3, S4]

AC-5: Given a criterion with fewer disposed findings than D5's stated minimum, the published table
shows that criterion's count and the literal text "insufficient data," and shows no numeric rate for
it. [S9]

AC-6: The published acceptance table lives inside a `<!-- marker:start -->` / `<!-- marker:end -->`
pair (name set by D6), and `npm run gen -- --check` (or an equivalent drift check this spec's
implementation adds under the same pattern) fails if the table inside the markers differs from what
regenerating from the committed aggregate file produces. [S16, S19]

AC-7: A disposition-log fixture with an `iteration` field set to 1, 2, or 3, and a second fixture
with no `iteration` field at all, both produce identical aggregation output for every other field
held equal; the script does not require, reject, or treat differently the presence of that field.
[S11]

AC-8: Each of the three ROADMAP gate clauses, "disposition logs...are collected," "an aggregation
script turns them into acceptance rates per criterion," and "the first acceptance table is published,"
names a specific committed path or script in this spec's eventual build plan, traceable back to this
sentence. [S1]

## Sources & Evidence

- **[S1]** `ROADMAP.md`, "Next: v0.3.0" exit gate (read in full 2026-10-27; the E48 clause: "Disposition
  logs from real use are collected, an aggregation script turns them into acceptance rates per
  criterion, and the first acceptance table is published...Real use means runs on real artifacts,
  including the maintainer's own, not bench runs. The first pruning pass is not part of this gate,
  because it needs months of dispositions.") and "After" > v0.4.0+ "Samples corpus" bullet ("Samples
  never enter `bench/` and never carry ground-truth manifests") - class A
- **[S2]** `docs/internal/backlog/enhancements.md`, "## E48 - Begin disposition telemetry (acceptance
  rate per criterion)," lines 1107-1117 (read in full 2026-10-27) - class A
- **[S3]** `contract/critique-contract.schema.json`, `$defs/dispositionLog` (line 238) and
  `$defs/dispositionEntry` (line 267), read directly 2026-10-27: three required top-level keys,
  `additionalProperties: false`; entry requires `finding_id` and `disposition`, with `note`,
  `criterion`, and `decided_at` optional - class A
- **[S4]** `contract/README.md`, "Disposition log" section and "What the schema does not check"
  section (the BYOR-namespace caveat: "a user rubric may declare its own namespace, and no document
  records which mode a run was in") - class A
- **[S5]** `docs/how-to/dispositions.md` (read in full 2026-10-27), the field table and "Why the log
  exists" section ("Pruning telemetry...Without logged dispositions there is no signal") - class A
- **[S6]** `examples/accessibility/dispositions.json` (read in full 2026-10-27), a committed,
  schema-valid, but authored example - class A
- **[S7]** `examples/recipes/revision-loop.md` (read in full 2026-10-27; "The disposition log below is
  authored for this recipe, one plausible reviewer's decision...The revised v2 memo is authored for
  this recipe...This envelope is authored, not a live rerun") - class A
- **[S8]** `bench/metrics/__main__.py`, lines 68-69: `if not isinstance(data, dict) or "dispositions"
  in data: return None  # a disposition log, or not a document at all; not scored` - class A
- **[S9]** `docs/explanation/methodology.md`, section 8 "Evaluation," "Acceptance rate" subsection,
  and section 10 "Human-in-the-loop by contract" (both read in full 2026-10-27) - class A
- **[S10]** `docs/reference/criterion-ids.md`, "Permanence rules," rule 2: "Deprecate, never delete. A
  criterion the library stops checking is marked deprecated in its skill's registry." - class A
- **[S11]** [ADR 0040 (the revision loop pauses with a revision brief)](../../../decisions/0040-revision-loop-pauses-with-a-revision-brief.md)
  (read in full 2026-10-27; the optional `iteration` field, contract version 1.1.0) - class A
- **[S12]** [ADR 0039 (BYOR measured by parity)](../../../decisions/0039-byor-measured-by-parity.md)
  (read in full 2026-10-27; BYOR is measured by parity on `critique-microcopy`, not by acceptance
  rate) - class A
- **[S13]** [N4's spec](../N4_revision-loop-chain/spec.md) (read in full 2026-10-27; this spec's own format
  model, and D2/D4's framing of the same `iteration`-field contract bump this spec must coexist with)
  - class B when cited (then an uncommitted draft; ruled 2026-10-30)
- **[S14]** `docs/internal/backlog/new-components.md`, "## N4 - Revision loop as a first-class,
  invokable chain" (read in full 2026-10-27) - class A
- **[S15]** `SECURITY.md`, "The one network call: the bench harness" section (read in full 2026-10-27;
  "Nothing else in this repository makes a network call") - class A
- **[S16]** `CONTRIBUTING.md` (read in full 2026-10-27), "Generated files: edit the source, not the
  output" section, and the PR-based contribution flow as the repository's existing consent-by-action
  pattern; also notes the document's own unresolved "Pre-release...currently private" line, which
  conflicts with the repository's otherwise-public state (live site, public CI, public GitHub issue
  and advisory links in `SECURITY.md`) - class A, with the private/public conflict flagged as
  unresolved documentation drift outside this spec's scope
- **[S17]** `ROADMAP.md`, "Known limitations carried forward": "No human acceptance data yet. Every
  number published so far comes from the benchmark's seeded-defect corpus, not from real users
  disposing real findings. Disposition telemetry, which is what closes that gap, does not begin until
  v0.3.0." - class A
- **[S18]** `docs/internal/execution/RC-HANDOVER.md`, line 144: "Human acceptance data.
  Disposition-based acceptance rate remains unmeasured." - class A
- **[S19]** `bench/README.md`, line 41 (the `bench-results` marker's generation description: "The
  published tables in this repository, marked by the `bench-results` comments, are generated from
  that file, never hand-edited") and lines 494-596 (the marker pair itself); `scripts/gen-site.mjs`
  and `scripts/check-readme-figures.mjs` as the confirmed generators that read `results.json` (via
  `git grep -ln "bench-results\|results.json" -- scripts/ site/src`, run 2026-10-27) - class A
- **[S20]** A direct search of this repository for existing privacy, telemetry-consent, or opt-in
  policy text specific to disposition data (`grep -rniE "privacy|telemetry"` across tracked
  Markdown, and a separate search for "consent"/"opt-in", run 2026-10-27) returns no policy document
  of any kind beyond `SECURITY.md`'s network-call scope and the unrelated `BYOR` and `--strict`
  opt-in mentions already cited above - a verified negative, not an inferred one - class A
- **[S21]** `skills/critique-clarity/SKILL.md`, lines 126-133 (read 2026-10-27): "This skill's
  registry carries 23 criteria...See `references/PLAIN.md` and `references/WILLIAMS.md` for the full
  seven-column criterion registry," with no status or deprecated column named among the seven - class
  A
- **[S22]** `docs/internal/decisions/0013-contract-versioning-independent.md`, "Minor (1.x.0)" rule
  (read 2026-10-27): "A 1.0.0 document still validates against a 1.1.0 schema." - class A

## Open Questions / Decisions

| ID | Title | Resolution | Status | Updated |
|----|-------|------------|--------|---------|
| D1 | What counts as "real use" and where logs come from | Option A | Decided | 2026-10-30 |
| D2 | Whether the disposition-log schema needs a provenance marker | Option A | Decided | 2026-10-30 |
| D3 | Whether anything leaves a contributor's machine, and how consent works | Option A | Decided | 2026-10-30 |
| D4 | What is actually committed to the public repository | Option C | Decided | 2026-10-30 |
| D5 | The aggregation script's inputs, outputs, rate definition, and minimum sample size | Option A, minimum n = 5 | Decided | 2026-10-30 |
| D6 | How the acceptance table is published, and with what caveats | Option A with B's display rule | Decided | 2026-10-30 |
| D7 | E48's boundary against the criterion-pruning pass | Option A | Decided | 2026-10-30 |
| D8 | How BYOR-sourced findings are excluded from the acceptance-rate signal | Option A | Decided | 2026-10-30 |

### D1: What counts as "real use" and where logs come from (Decided)

**Summary.** Decide which sources of disposition logs count toward the v0.3.0 gate: the maintainer's
own use, opt-in contributors, or the output of N4's revision-loop chain once it ships.

**Context.** The gate text already names one source outright: "runs on real artifacts, including the
maintainer's own, not bench runs" [S1]. It does not say whether that is the only source for v0.3.0 or
a floor that other sources add to. N4, the revision-loop chain, is itself an unruled draft
([N4 (the revision-loop chain)](../N4_revision-loop-chain/spec.md)) whose own disposition logs, once it
exists, would be real-use logs by the same gate definition, produced as a side effect of normal use
rather than a dedicated collection effort [S11, S13, S14].

**Desired outcome.** A source list narrow enough to build against now, that does not silently exclude
a source the maintainer already expects to use, and that does not make E48 wait on N4's own open
decisions to close.

**Options / approaches.**

* **Option A:** Maintainer's own use only, for v0.3.0. Matches the gate text's own wording exactly and
  needs no new collection or consent mechanism beyond whatever the maintainer already does when
  running a skill against a real artifact.
* **Option B:** Maintainer's own use plus any contributor who opts in by submitting a disposition log
  through a PR. Needs an explicit submission path (a PR template, an issue form, or a script) that
  does not exist today, and a stated consent story (D3) before it can be offered to anyone outside
  the maintainer.
* **Option C:** Maintainer's own use plus whatever N4's chain produces once it ships, with no separate
  contributor-outreach mechanism. Widens the source for free once N4 exists, but makes E48's own
  completion depend on N4's unruled decisions landing first, which neither this spec nor the gate text
  requires.

**Recommendation.** Option A, high confidence. The gate text already licenses exactly this scope, it
needs no new mechanism to build, and nothing in the backlog or the gate text requires E48 to wait on
N4 or on recruiting outside contributors before its own three conditions can be met.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: the maintainer's own use only, for v0.3.0
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. It is exactly what the gate text licenses.
> * **Follow-up:** Build in E48's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E48_disposition-telemetry/spec.md`. The gate also needs the maintainer to produce real disposition logs on their own documents.
> * **Decided by / date:** jprisant / 2026-10-30

### D2: Whether the disposition-log schema needs a provenance marker (Decided)

**Summary.** Decide whether a real-use disposition log needs something that distinguishes it,
machine-readably, from the authored example logs already committed under `examples/*/dispositions.json`,
and if so, whether that marker is a schema field or a structural convention.

**Context.** Seven committed disposition-log fixtures already exist, and the one recipe that shows a
full disposition log in prose says outright that it is "authored for this recipe" [S6, S7]. Nothing in
the schema or anywhere else marks a log as real versus authored [S3, S4]. If the aggregation script
(D5) ever globbed the whole repository for files carrying a `dispositions` key, it would count these
seven fixtures as real acceptance data, which would be wrong in a way nothing downstream could detect.

**Desired outcome.** A rule simple enough that the aggregation script can state its own input set
unambiguously, with no risk of silently absorbing a fixture.

**Options / approaches.**

* **Option A:** No schema change. Real-use logs live in a dedicated directory the aggregation script
  reads from exclusively, and nothing outside that directory is ever in its input set, regardless of
  whether it carries a `dispositions` key. Costs no contract version bump.
* **Option B:** Add an optional field at contract 1.1.0, for example `source: "real" | "example" |
  "bench"`, riding the same minor-version mechanism ADR 0040 already opened for the `iteration` field
  [S11, S22]. Makes provenance checkable from the file alone, wherever it lives, at the cost of a
  schema change and updating `contract/validate.py`'s coverage.
* **Option C:** A sidecar manifest file listing which committed disposition-log paths are real-use,
  leaving both the schema and the directory layout untouched.

**Recommendation.** Option A, medium confidence. It needs no contract change at all, and this
repository already relies on "where a file lives tells you what it is" for an analogous distinction
(the samples corpus is kept out of `bench/` for the same kind of reason [S1]). It does require D5's
aggregation script to state its input directory explicitly rather than searching broadly, which this
spec's AC-1 already requires regardless of which option is chosen.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: no schema change; real-use logs live in one dedicated directory, the script's only input
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. Read with D4's Option C, that directory is local and gitignored.
> * **Follow-up:** Build in E48's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E48_disposition-telemetry/spec.md`.
> * **Decided by / date:** jprisant / 2026-10-30

### D3: Whether anything leaves a contributor's machine, and how consent works (Decided)

**Summary.** Decide whether collecting a real-use disposition log involves any automatic transmission
off the machine that produced it, and if so, what a contributor agrees to before that happens.

**Context.** `SECURITY.md` states plainly that the bench harness's opt-in CLI call is the one network
call anything in this repository makes, and that "nothing else in this repository makes a network
call" [S15]. A direct search of the repository turns up no existing telemetry-consent or opt-in policy
text for disposition data specifically [S20]. `CONTRIBUTING.md` already documents a PR-based
contribution flow, which is itself an existing consent-by-action pattern: nothing in this repository
is published without the contributor choosing to open a pull request [S16].

**Desired outcome.** A collection story that does not require amending `SECURITY.md`'s own stated
scope, and that does not invent a consent flow this repository has no other instance of.

**Options / approaches.**

* **Option A:** Nothing leaves a machine automatically. A person who wants their disposition log
  counted commits it themselves, through the same PR flow every other contribution already uses
  [S16]. No new network call, no amendment to `SECURITY.md`.
* **Option B:** A collection script a person runs locally that uploads an anonymized summary to some
  endpoint. Requires a new network call `SECURITY.md` does not describe today, its own ADR, and a
  `SECURITY.md` amendment before it could ship.
* **Option C:** No collection path in software at all. The maintainer transcribes counts from logs
  they already hold into the published aggregate by hand, with no raw log file required to leave the
  authoring machine or enter the repository.

**Recommendation.** Option A, high confidence. It needs no new network call and no new consent
mechanism beyond the PR flow `CONTRIBUTING.md` already documents, and it keeps `SECURITY.md`'s "nothing
else makes a network call" sentence true without an edit, which this spec's AC-2 states as a direct
check. Option C is the fallback if D1 stays maintainer-only, since a PR-based flow is only needed once
a second contributor is in scope.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: nothing leaves a machine automatically; sharing goes through the pull-request flow
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. With D4's Option C, what is shared is the aggregate counts, not the logs.
> * **Follow-up:** Build in E48's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E48_disposition-telemetry/spec.md`; `SECURITY.md` stays unamended.
> * **Decided by / date:** jprisant / 2026-10-30

### D4: What is actually committed to the public repository (Decided)

**Summary.** Decide whether a real-use disposition log is committed verbatim, in a redacted form, or
not at all, with only the aggregate counts the script computes ever entering the repository.

**Context.** This repository is public and permanent; anything committed stays visible in git history
even if later removed. A disposition entry's `note` field is free prose, and the docs call it "most
valuable on reject" [S5], meaning the field most likely to carry candid commentary about a real
artifact is also the one field with no sanitization rule anywhere. A log's `envelope` reference can
also carry `artifact` and `path`, which can reveal a contributor's own project layout [S3, S4].

**Desired outcome.** A storage shape that lets the published rate exist without exposing a
contributor's private document content, file paths, or candid notes, none of which the published
acceptance rate itself needs.

**Options / approaches.**

* **Option A:** Commit raw disposition logs verbatim, the same shape the seven existing
  `examples/*/dispositions.json` fixtures already use [S6]. Cheapest, but commits `note`, `artifact`,
  and `path` text with no review step defined anywhere.
* **Option B:** Commit a redacted projection of each log, stripped of `note`, `artifact`, and `path`,
  keeping only `finding_id`, `disposition`, and `criterion`. Avoids leaking prose or file layout, at
  the cost of a stated redaction step before anything is committed.
* **Option C:** Commit nothing at the per-log level. Raw logs stay local (or in a gitignored
  directory), and only the aggregate counts the script computes, `(criterion, accept, reject, defer,
  n)`, are ever committed.

**Recommendation.** Option C, medium confidence. The repository's own permanence and the `note`
field's documented tendency to carry the most candid commentary argue for keeping raw per-finding
content out of the repository entirely; the published acceptance table only ever needs the aggregate
counts, so nothing is lost by not committing the logs themselves. This spec's AC-3 states the check
this recommendation implies.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option C: commit aggregate counts only, `(criterion, accept, reject, defer, n)`
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. The published table needs only the counts, so no note, artifact or path text can leak.
> * **Follow-up:** Build in E48's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E48_disposition-telemetry/spec.md`.
> * **Decided by / date:** jprisant / 2026-10-30

### D5: The aggregation script's inputs, outputs, rate definition, and minimum sample size (Decided)

**Summary.** Decide where the aggregation script lives, what it reads, what it emits, how it defines
an acceptance rate, and how many disposed findings a criterion needs before a rate is published for
it.

**Context.** `bench/metrics/__main__.py` explicitly treats any document carrying a `dispositions` key
as "not scored" [S8], so nothing today computes this figure. A disposition entry's `criterion` field
is optional and denormalized; resolving it when absent needs the referenced envelope, not the log
alone [S3, S4]. ADR 0040 adds an optional `iteration` field the script must tolerate either way [S11].
`ROADMAP.md` already keeps the samples corpus out of `bench/` "because samples never enter bench/ and
never carry ground-truth manifests," for a comparable reason (real-use content, not seeded-defect
measurement) [S1].

**Desired outcome.** A script whose output is honest about thin data rather than reporting a rate
from one observation, and whose location keeps real-use telemetry visibly separate from the
seeded-defect benchmark the way the samples corpus is already kept separate.

**Options / approaches.**

* **Option A:** A standalone script outside `bench/` (for example under `scripts/` or a new
  `telemetry/` directory), reading every log from D2's chosen location, resolving `criterion` from the
  envelope when the log omits it, and emitting `(criterion, accept, reject, defer, n)` per criterion,
  with the accept rate shown only once `n` meets a stated floor.
* **Option B:** Extend `bench/metrics/__main__.py` to stop skipping disposition logs and compute the
  same output inline, reusing existing scoring infrastructure at the cost of blurring the line
  `ROADMAP.md` already draws between measured benchmark figures and real-use data.
* **Option C:** No minimum sample size; publish whatever `n` each criterion has, including `n=1`, with
  a caveat stated beside every number rather than a floor that withholds some of them.

**Recommendation.** Option A for location (medium confidence: it mirrors the samples-corpus precedent
for keeping real-use content out of `bench/`), paired with a stated minimum `n` rather than Option C
(high confidence: a single-observation "rate" reads as precise when it is not, and this project
already uses k=5 as its own convention for how much repetition it trusts before publishing a figure
[S9], which is a defensible floor to reuse rather than invent).

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: a standalone script outside `bench/`, with a minimum of 5 disposed findings per criterion before a rate is shown
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. The floor of 5 borrows the bench's k=5 by analogy and is a starting value, not a derived one.
> * **Follow-up:** Build in E48's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E48_disposition-telemetry/spec.md`; revisit the floor once real counts exist.
> * **Decided by / date:** jprisant / 2026-10-30

### D6: How the acceptance table is published, and with what caveats (Decided)

**Summary.** Decide where the first acceptance table lives, how it is regenerated, and what it shows
for a criterion that has not yet cleared D5's minimum sample size.

**Context.** This repository already has one generated-table pattern: the `bench-results` marker
pair in `bench/README.md` and `README.md`, generated from `results.json` and "never hand-edited" [S16,
S19]. `scripts/gen-site.mjs` and `scripts/check-readme-figures.mjs` are the confirmed generators that
read `results.json` today for those figures [S19]. No acceptance-rate page or marker exists yet. Under
D1's recommended scope (maintainer-only, v0.3.0), the first table's volume will be small against the
library's full criterion count, so most cells will not clear D5's minimum.

**Desired outcome.** A published table that follows this repository's own "generated from a committed
source, never hand-edited" discipline, and that is honest about sparse coverage rather than hiding it.

**Options / approaches.**

* **Option A:** A new marker-delimited table, generated from a new committed aggregate file (for
  example `bench/results/acceptance.json` or a new `telemetry/results.json`), inside an existing page
  such as `bench/README.md` or a new `docs/reference/acceptance-rates.md`, following the same
  never-hand-edit discipline and drift check as `bench-results` [S16, S19].
* **Option B:** A dedicated new site page, built the way the criterion-ID explorer is built, showing
  per-criterion accept/reject/defer counts, with any criterion below D5's floor shown as "insufficient
  data" rather than omitted from the page entirely.
* **Option C:** Fold the acceptance rate into the existing per-skill README and site criterion tables
  as one more column, updated whenever the aggregation script runs.

**Recommendation.** Option A for the generation discipline (high confidence: it matches an established
pattern this project already enforces by CI drift check) combined with Option B's "insufficient data"
display rule inside that same table (medium confidence) rather than hiding sparse cells silently.
Option C is premature until most criteria clear the minimum-`n` floor, which the first table, scoped
under D1, is not expected to do.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A's generated, marker-delimited table from a committed aggregate file, with Option B's "insufficient data" display for criteria below the floor
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. Most criteria will be thin in the first table, so the table says so rather than hiding them.
> * **Follow-up:** Build in E48's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E48_disposition-telemetry/spec.md`.
> * **Decided by / date:** jprisant / 2026-10-30

### D7: E48's boundary against the criterion-pruning pass (Decided)

**Summary.** Decide whether E48 builds any part of the deprecation mechanism the pruning pass will
need, or defers all of it, given that the gate text excludes the pruning pass itself from this item.

**Context.** The v0.3.0 gate states outright that "the first pruning pass is not part of this gate,
because it needs months of dispositions" [S1]. `docs/reference/criterion-ids.md`'s permanence rule 2
says a retired criterion is "marked deprecated in its skill's registry" [S10], but no registry carries
such a marker today; `critique-clarity`'s own registry table has no status column [S21], and E48's own
backlog entry names this as a known gap with "no schema field or tooling yet" [S2].

**Desired outcome.** A scope line that does not quietly build speculative tooling against a pruning
threshold that is not decided yet, while still leaving a clear, named next step for whoever specs the
pruning pass later.

**Options / approaches.**

* **Option A:** E48 builds collection and aggregation only, and explicitly defers any registry schema
  change (a `deprecated` field or tooling) to the pruning-pass item itself, whenever it is scheduled.
* **Option B:** E48 also adds the `deprecated` marker mechanism now, a registry column or front-matter
  field, even though nothing will be marked yet, so the tooling exists before the first pruning pass
  needs it.
* **Option C:** E48 makes no reference to pruning at all, leaving the connection between the
  acceptance table and any future pruning pass entirely implicit.

**Recommendation.** Option A, high confidence. The gate text draws this line explicitly and for a
stated reason, insufficient data, and building deprecation tooling now would be speculative work
against a pruning threshold and process that do not exist yet either.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: collection and aggregation only; the `deprecated` registry marker is deferred to the pruning item
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. Deprecation tooling now would be speculative.
> * **Follow-up:** None needed in E48; the pruning-pass item owns the registry marker.
> * **Decided by / date:** jprisant / 2026-10-30

### D8: How BYOR-sourced findings are excluded from the acceptance-rate signal (Decided)

**Summary.** Decide how the aggregation script keeps a BYOR-sourced finding's disposition out of the
acceptance-rate signal, given that ADR 0039 measures BYOR by a different method entirely.

**Context.** ADR 0039 rules that BYOR is measured by parity on one flagship skill, not by acceptance
rate [S12]. `contract/README.md` names a documented gap: "a user rubric may declare its own namespace,
and no document records which mode a run was in," so filtering on the `BYOR-` criterion-namespace
prefix alone is not reliable [S4]. The reliable signal is a finding's `rubric_source: byor` field,
which lives on the finding inside the run envelope, not on the disposition-log entry itself, which
only denormalizes `criterion` [S3, S4].

**Desired outcome.** An exclusion rule that does not rely on the documented namespace gap, using a
signal that is already required reading for other reasons (D5 already requires resolving the
envelope when `criterion` is absent).

**Options / approaches.**

* **Option A:** Resolve each disposition against its referenced envelope and drop any finding whose
  `rubric_source` is `byor` before counting. Requires the script to always load the envelope, which
  D5 already requires for the separate reason of resolving an absent `criterion`.
* **Option B:** Exclude by criterion namespace prefix (`BYOR-`) read directly off the disposition
  log's own denormalized `criterion` field, with no envelope lookup needed. Cheaper, but inherits
  exactly the gap `contract/README.md` names: a user-defined namespace that does not start with
  `BYOR-` would slip through uncaught.
* **Option C:** Do not exclude BYOR findings at all. Publish one combined acceptance rate per
  criterion regardless of rubric source, with a caveat noting the mixture.

**Recommendation.** Option A, high confidence. It is the only option without the documented gap Option
B carries, and D5's aggregation script already has to resolve the envelope for an unrelated reason, so
this check costs nothing new to add alongside it.

---

> **Maintainer decision:** Decided 2026-10-30 by jprisant
>
> * **Status:** Decided
> * **Choice:** Option A: resolve each disposition against its envelope and drop `rubric_source: byor` findings
> * **Reasoning:** "ok", accepting every recommendation in the 2026-10-30 walk. It is the only option without the namespace gap, and the script loads envelopes anyway.
> * **Follow-up:** Build in E48's implementation, after this draft moves to `docs/internal/release-plans/_unassigned/E48_disposition-telemetry/spec.md`.
> * **Decided by / date:** jprisant / 2026-10-30

## What I do not know

- Whether `scripts/gen-site.mjs` or `scripts/check-readme-figures.mjs` would need structural changes
  to carry a new marker pair for an acceptance table, versus being extendable with a new, independent
  generator script; I confirmed both files reference `results.json` by name but did not read either
  in full.
- Whether any maintainer-run disposition logs already exist locally, uncommitted, from real use of
  this library's own skills before this spec was drafted; I found none committed anywhere in the
  tracked repository, but a local, gitignored log would not show up in a tracked-file
  search and I did not ask.
- The exact minimum sample size `n` a floor in D5 should use; I recommended reusing the k=5 convention
  by analogy to the benchmark harness's own repetition count, but no document states that k=5 was
  chosen for the same statistical reason a disposition-count floor would need, and I did not verify
  that the analogy holds beyond surface similarity.
- Whether `CONTRIBUTING.md`'s "Pre-release...currently private" line is simply stale (the repository
  otherwise reads as public: a live site, public CI badges, and public GitHub advisory and issue
  links in `SECURITY.md`) or reflects some access state I am not able to check from inside the
  checkout; I flagged the conflict in [S16] but did not resolve it, and D1 and D3's recommendations
  assume the repository is in fact public, consistent with everything except this one line.
- Whether any criterion registry outside `critique-clarity`'s has a status or deprecated column I
  did not find by spot-checking one skill; I read only `critique-clarity`'s `SKILL.md` for this
  check, not all seven skills' registries.
