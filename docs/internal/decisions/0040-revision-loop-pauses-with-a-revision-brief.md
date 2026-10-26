# 0040 - The revision-loop chain pauses at revise and hands over a revision brief

## TL;DR
- **Decision:** the revision-loop chain runs critique, takes the person's dispositions, writes a
  revision brief of the accepted findings, and stops. A person, or a tool the person runs on their
  own authority, writes the next version. The chain resumes with a re-critique of it. The library
  never writes the artifact.
- **The auto-fix exclusion and methodology section 10 stand unchanged.** No published wording moves.
- **The iteration count is an optional field in the disposition log**, added as contract version
  1.1.0, so a resumed chain knows which of its three iterations it is on.
- **The revision brief is a documented format outside the contract** until a second consumer
  exists. It joins the contract when E54 (cross-library composition) consumes it.
- **Ruled:** by the maintainer on 2026-10-25, choosing the recommended option on each of three
  decisions.
- **Status:** Accepted (2026-10-25). Closes E52.

- **Status:** Accepted
- **Date:** 2026-10-25
- **Deciders:** Jonathan Prisant (the ruling). Drafted by Claude from `ROADMAP.md`, the methodology,
  the contract schema and the agent-skills-toolkit Standard.

## Builds on

- [Methodology section 10 (human-in-the-loop by contract)](../../explanation/methodology.md), status
  Stable, which this ADR keeps word for word.
- [0004 - Plugin surface: skills plus critic subagent](0004-plugin-surface-skills-and-critic-subagent.md),
  which records that the critic never edits the artifact.
- [0013 - The critique contract versions independently](0013-contract-versioning-independent.md),
  whose minor-version rule admits a new optional field.
- [E52 (who performs revise)](../backlog/enhancements.md), which this ADR closes, and
  [N4 (the revision-loop chain)](../backlog/new-components.md), which builds under it.

## Context and problem statement

N4 asks for the revision loop as an invokable chain: critique, disposition, revise, re-critique.
Today `examples/recipes/revision-loop.md` performs every step by hand, and says so: "The revised v2
memo is authored for this recipe." Nothing in the repository says who revises once the loop is a
chain.

Two published commitments bound the answer.

- **ROADMAP, "Deliberately not doing":** "Auto-fix. Skills report findings; a human disposes them.
  Nothing here rewrites an artifact on its own authority, and that will not change as the catalog
  grows."
- **Methodology section 10, status Stable:** "Critique never auto-applies fixes. This is a contract,
  not a default setting." The same section bounds the loop. It stops "when zero findings remain at
  severity 3 or above or after three iterations, whichever comes first", because "unbounded loops
  converge on the model's preferences, not the rubric's."

E52's entry framed the item as "a decision, not a proposal to relax the exclusion". The v0.3.0 exit
gate requires the ruling to be recorded, and it requires N4 to be built under it.

## Decision drivers

- **Keep both commitments as written.** A ruling that needs either one reworded is a different item
  from the one E52 recorded.
- **Keep the disposition step meaningful.** Section 10 says "the disposition step is where the value
  is". A person should rule on findings, not approve a model's prose.
- **Make the chain invokable and testable.** Gold check G3 in the agent-skills-toolkit Standard
  requires each chain contract to have at least one eval or regression case, run in CI. It also
  requires a regression check that changing one component does not silently break a chained
  consumer. N4 declares its chain contract at `agents/_chain-permitted.yaml`.
- **Grow the contract only where a stated requirement needs it.** A contract addition is cheap to
  make and slow to undo.

## Considered options

Three decisions, each ruled on the recommended option.

**Who performs revise.**

1. **The chain pauses and writes a revision brief (chosen).** A person, or a tool the person runs,
   revises from it.
2. **The chain pauses, and the person revises from the envelope and the dispositions alone.** Not
   taken. It is a sound minimum, but the pause is a dead end. A G3 eval of it could expect little
   more than that the chain stopped.
3. **A model drafts the next version as a separate file, which the person accepts, edits or
   discards.** Rejected. It keeps the exclusion in letter only. A person who accepts a whole drafted
   version approves the model's prose rather than ruling on findings.
4. **A model revises on every accepted disposition, and section 10 is amended to allow it.**
   Rejected. It reverses a commitment marked Stable, and it is the loop section 10 bounds in order to
   avoid.

**Where the chain keeps its iteration count.** A paused chain resumes on a new version, so the
three-iteration bound needs a count that survives the pause. The disposition log's schema allows
exactly three properties, `contract_version`, `envelope` and `dispositions`, with
`additionalProperties: false`. An iteration field therefore needs a contract change.

1. **An optional iteration field in the disposition log, as a minor contract version (chosen).**
   Section 10 names the log as what "makes the revision loop auditable", so the count that bounds the
   loop belongs in it.
2. **A separate loop-state file beside the log, outside the contract.** Not taken. One variant of it,
   in which the revision brief itself carries "iteration N of 3", is the fallback if N4's spec finds
   the contract change unwanted.
3. **Infer the iteration from how many envelopes exist for the artifact.** Rejected. The count breaks
   as soon as someone re-runs a critique by hand.

**Whether the revision brief joins the versioned contract.**

1. **Document the brief as a plain format in N4's docs, outside the contract, until a second
   consumer exists (chosen).** Today the only consumer is a person.
2. **Define the brief in the contract schema now, with validator coverage, as a minor contract
   version.** Deferred, not rejected. It becomes the right answer when E54 consumes the brief.
3. **Emit the brief as prose for people only, with no stated format.** Rejected. G3's regression
   check needs a stated format to assert against.

**Why the count joins the contract and the brief does not.** The two decisions apply different tests.
The wait-for-a-second-consumer test fits an exchange format, which the brief is. The iteration count
is read back by the chain itself, and section 10 requires the bound to be auditable in the log. That
requirement is stated now, so the count does not wait for a second consumer.

## Decision outcome

**The chain.** N4 runs these steps, in order.

1. Critique the artifact.
2. Take the person's dispositions into the disposition log.
3. Stop if no finding at severity 3 or above remains, or if this was the third iteration.
4. Otherwise, write the revision brief and pause.
5. On resume with a new version, re-critique it, compare the result with the previous envelope, and
   return to step 2.

No step writes the artifact.

**The revision brief.** It holds one entry per accepted finding: the finding, its location, its fix
and its criterion. N4's docs state the format, and N4's spec fixes the field names.

**The iteration count.** It is an optional field in the disposition log, added as contract version
1.1.0 under ADR 0013's minor-version rule. Because the field is optional, every existing 1.0.0 log
stays valid. The chain writes the field on every iteration.

**G3 coverage.** Each edge in N4's chain contract gets at least one eval, with the revision brief as
its expected output. The regression check asserts against the brief's documented format.

**The boundary, stated in the docs.** The commitment covers what the library does. The library cannot
stop a user from wiring an automatic reviser to the brief, and the docs say so plainly. The README
says beside N4 that the loop takes two invocations.

## Consequences

**Positive:** both commitments stand as published, and no ADR has to argue that a fix is not a fix.
The chain is invokable, and its own steps are deterministic bookkeeping that G3 can evaluate. The
brief gives another library's reviser, or a person's own editor, a defined point to consume.

**Negative:**

- **A chain that pauses is less of a chain.** A user who wants one command from draft to clean will
  find two. That is the exclusion working as published.
- **A tool the user runs could revise automatically anyway.** The commitment covers the library, not
  what a user builds downstream.
- **The contract moves to 1.1.0 for one optional field.** A 1.1.0 log can fail against the 1.0.0
  schema, the asymmetry ADR 0013 accepts for every minor version.
- **The brief's format becomes a contract in practice once a sibling consumes it.** That is why E54
  is the trigger for moving it into the schema.

**Neutral:** no code changes in this ADR. N4 builds the chain, the field and the format.

## What this ADR does not decide

- The chain's entry point, its name and its invocation shape, which N4's spec settles.
- The iteration field's name, and the brief's exact field names, which N4's spec fixes.
- When the brief joins the contract, which waits for E54.
