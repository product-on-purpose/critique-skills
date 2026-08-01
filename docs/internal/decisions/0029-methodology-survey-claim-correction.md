# 0029 - Methodology survey claim: correcting two sentences, and why the freeze had to be broken to do it

## TL;DR
- **Decision:** `docs/explanation/methodology.md` is frozen by house rule, and this ADR is the
  explicit, one-time exception. Two sentences (Section 2's gate table and Section 13's open
  questions) claimed the domain slate "needs reconciliation with the author's original 40-candidate,
  13-domain survey." No such survey document exists anywhere in this repository or in the planning
  archive it draws from. Both sentences are corrected to say what is actually true: the domain slate
  is a provisional working proposal, and a critique-framework survey is a tracked v0.2 deliverable,
  not a document already in hand.
- **Why:** a factual claim that fails the library's own evidence bar is exactly the failure mode this
  library exists to catch in other people's work. P4's SWEEPS verification found the claim and
  flagged it as a genuine conflict between the zero-survey-claim house rule and the frozen
  methodology text (`docs/internal/execution/P4-report.md`, "SWEEPS" and "Open items for P5"). This
  release-packaging pass carries the explicit authorization to resolve it, so the fix lands here
  rather than staying an open item through another release.
- **Scope discipline:** only the two sentences naming the survey are touched. Nothing else in
  `docs/explanation/methodology.md` is edited, and no other frozen file (`contract/critique-contract.schema.json`,
  any other methodology section) is touched under this authorization.
- **Status:** Accepted (2026-08-01).

- **Status:** Accepted
- **Date:** 2026-08-01
- **Deciders:** Jonathan Prisant, release-packaging pass (Claude)

## Builds on

- [P4-report.md](../execution/P4-report.md), "SWEEPS: three of four passed; the fourth is a
  frozen-file conflict, reported, not fixed," and "Open items for P5," item 1: the report that found
  this claim and correctly declined to fix it without explicit authorization, because the file is
  frozen.
- [0016 - The contract enforcement boundary](0016-contract-enforcement-boundary.md), the closest
  precedent for treating a gap between a frozen document's claims and what the repository actually
  contains as a named, recorded finding rather than a silent edit.

## Context and problem statement

The house rule for this build run is stated plainly in the release-packaging instructions and echoed
in `P4-report.md`: "the contract schema and methodology are frozen; report conflicts, never edit
them." That rule exists so that the interface every skill, the bench, and the critic subagent depend
on cannot drift out from under them mid-build. It is the right rule for interface stability. It is
the wrong rule for a factual claim about the world that turns out to be false.

`docs/explanation/methodology.md` Section 2 and Section 13 both assert that the domain slate "needs
reconciliation with the author's original 40-candidate, 13-domain survey," as if that survey is a
completed artifact waiting to be consulted. The P0 planning pass verified no such document exists:
not in this repository, not in `_local/initial-plan/`, not in `_local/initial-discovery/` (the
original methodology draft this file was promoted from, `_local/initial-discovery/2026-07-27_claude-opus_methodology.md`,
carries the identical wording, so the claim predates this repository and was never backed by an
artifact here either). A library whose entire premise is "every criterion traces to a source with a
URL or an ISBN" (Section 2, "The gate applied") cannot itself carry an untraceable claim about its
own provenance. That is not a stylistic problem; it is the library failing its own Part 2 test
against its own founding document.

## Decision drivers

- **The library's evidence bar applies to the library's own claims, not only to the artifacts it
  critiques.** Section 2's operational test for Part 2 is "can every criterion trace to a source with
  a URL or an ISBN?" A survey that cannot be pointed at fails that test as surely as an uncited
  criterion would.
- **The freeze protects interface stability, not factual accuracy.** Nothing about the finding
  schema, the envelope, the severity scale, or any operationalized criterion is touched by this
  correction. The two sentences are self-disclosure prose inside explicitly labeled "Status:
  Provisional" and "Open questions" sections, not interface surface any consumer parses.
  Correcting them changes no skill's behavior and no contract field.
- **Leaving it as an open item through another release compounds the claim.** P4 already found and
  named this gap and declined to fix it for lack of authorization (correctly, under the freeze rule
  as it stood). This release-packaging pass carries that explicit authorization. Deferring again with
  authorization already in hand would be choosing to publish a known-false claim.
- **An ADR is the correct instrument for a freeze exception**, not a silent edit. The freeze's value
  depends on every exception being visible and justified in the same place a reader would look for
  any other methodology change.

## Considered options

1. **Leave the claim as written, publish v0.1.0 with it unresolved.** Rejected. The claim is false as
   written, the P4 report already surfaced it, and shipping a release with a known, named, unfixed
   factual error in the library's own constitution is the least defensible option available, not a
   neutral one.
2. **Scope the zero-survey-claim rule to exclude labeled provisional and open-question
   self-disclosure**, per P4's second suggested remedy. Rejected as the primary fix: this would
   permit the specific sentence to keep asserting a survey exists, merely because it does so inside a
   "Status: Provisional" label. A false claim wrapped in a caveat is still a false claim; the caveat
   here ("Status: Provisional") qualifies the domain slate's membership, not the survey's existence.
3. **Delete the survey references entirely, with no replacement statement about future work.**
   Rejected: this would understate the real, tracked plan. A critique-framework survey is a
   legitimate v0.2 roadmap item; removing the sentence entirely would lose that signal along with the
   false claim.
4. **Amend the two sentences to state the true, current position, and record the freeze exception
   here (chosen).**

## Decision outcome

Option 4. Both sentences are corrected in place:

- Section 2 ("The gate applied"), the "Status: Provisional" line, now reads: "The domain slate below
  is a working proposal. No completed candidate survey exists yet to reconcile it against; a
  critique-framework survey is a tracked v0.2 deliverable, not a document already in hand. Treat the
  pass/fail column as directionally right and the specific membership as unsettled."
- Section 13 ("Open questions"), the "Domain slate" bullet, now reads: "The Section 2 table is a
  working proposal with no completed candidate survey behind it yet. A critique-framework survey is a
  tracked v0.2 deliverable. Membership will change."

Both edits preserve the original claim's honest core (the domain slate is provisional and its
membership may change) and remove only the false part (that a survey already exists to reconcile it
against). Nothing else in the file changed: no criterion, no gate definition, no other section.

This ADR is the freeze exception. Any future edit to `docs/explanation/methodology.md` still needs
its own authorization; this decision does not reopen the file generally.

## What this does not establish

- **The critique-framework survey itself remains undone.** This ADR corrects a claim about the
  survey's existence; it does not commission, schedule, or scope the survey. It is named here as a
  tracked v0.2 deliverable because that is the truthful status, not because this ADR creates the
  tracking.
- **The domain slate's membership is still unsettled**, exactly as both corrected sentences say. This
  ADR does not validate, revise, or defend the twelve-domain table in Section 2.

## Consequences

**Positive:** the methodology's own founding document now passes the evidence test it applies to
every skill it governs. The zero-survey-claim sweep (release-plan hygiene gate (i)) can read PASS
without an unresolved exception carried forward. The correction is small, auditable, and reversible
if a real survey document is later produced and should be cited instead.

**Negative:** none identified. No interface, criterion, schema field, or skill behavior changed.

**Neutral:** the freeze rule itself is unchanged for every other sentence in the file. A future reader
who wants to know why these two sentences read differently from the surrounding frozen prose has this
ADR to consult.

## Implementation sites

- `docs/explanation/methodology.md`: Section 2 ("The gate applied," the "Status: Provisional" line)
  and Section 13 ("Open questions," the "Domain slate" bullet).
- [`docs/internal/execution/P4-report.md`](../execution/P4-report.md): "SWEEPS" and "Open items for
  P5," item 1, the report that found and named this conflict, closed by this ADR.
