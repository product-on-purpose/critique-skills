---
title: What the revision loop does, and what it leaves to you
description: Why the revision loop takes two invocations, why the library never revises your artifact, and where the library's commitment ends
audience: both
level: intermediate
---

# What the revision loop does, and what it leaves to you

The revision loop is the [`critique-revision-loop` workflow](../../_workflows/critique-revision-loop.md).
It critiques an artifact, records your decision on each finding, and then either stops or pauses
with a revision brief. **It never revises the artifact.** You do, or a tool you choose to run does.
This page explains that line and why it sits where it does.

## The loop takes two invocations

Each pass of the loop runs in two halves, because the step in the middle belongs to you.

1. **The first invocation** critiques the artifact with one `critique-<domain>` skill and takes your
   accept, reject, or defer decision on each finding. A deterministic stop-check then decides
   whether the loop continues. If it continues, the loop writes a revision brief and pauses. The
   brief lists every finding you accepted, each with its criterion, its location, and its fix.
2. **Between the invocations,** you revise the artifact, using the brief or not, as you see fit.
3. **The second invocation** takes the revised artifact and the disposition log from the first,
   re-critiques the artifact with the same skill, and compares the two runs. Then the loop returns
   to your decisions on the new findings.

The loop stops when no finding at severity 3 or above remains, or after the third pass, whichever
comes first ([methodology section 10](methodology.md)). Whatever remains at the bound is decided like
any other finding. It is not carried into a fourth pass. The loop also stops when findings at
severity 3 or above remain but you accepted none of them, because then there is nothing to revise.

## Why the library does not revise

A critique skill reports findings, and a person decides what they mean. That is the library's
safety property, and the disposition log is the record of it. If the library also performed the
revision, it would be grading its own work: the next critique would measure the library's edit, not
your artifact. It would also decide, on your behalf, which of its own findings were worth acting on.
[ADR 0040](../internal/decisions/0040-revision-loop-pauses-with-a-revision-brief.md)
records this ruling, and the roadmap's exclusion of auto-fix stands unchanged.

## Where the commitment ends

The library's commitment covers what the library's own code does, and nothing beyond it.

- **The library commits** that no step of the loop writes to the artifact. A test checks the
  artifact's SHA-256 hash before and after the first invocation, and the brief step refuses an output
  path that is the artifact itself.
- **The library commits** that the brief is a projection of the run envelope and your disposition
  log. It is computed without a model call, and the same inputs always produce the same bytes. The
  brief validates as a contract 1.1.0 revision brief, so another tool can check it independently.
- **The library does not control** what you connect to the brief. Nothing stops you from wiring a
  tool that rewrites the artifact from the brief automatically, and the library does not try to
  prevent it. If you do, that tool acts on your authority, and its edits are yours. The library's
  part ends when the brief is written.

The comparison step makes one more deliberate refusal. It reports how many findings each criterion
and each severity had in each run, and the change between them. It does not say that a finding in
the second run is "the same" finding as one in the first. A finding id is unique only within one run,
and a location describes one version of the artifact, so any claim to pair findings across a
revision would be a guess presented as a measurement.

## See also

- [The critique contract](../reference/critique-contract.md): the disposition log's `iteration`
  field and the revision brief, both added at contract 1.1.0.
- [Recording dispositions](../how-to/dispositions.md): how to write the log the loop reads.
- [The revision loop, worked example](../../examples/recipes/revision-loop.md):
  one artifact through the loop by hand.
