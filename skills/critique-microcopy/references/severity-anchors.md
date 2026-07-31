# Severity anchors: critique-microcopy

Domain calibration for the shared 0-4 scale in
[`docs/reference/severity-scale.md`](../../../docs/reference/severity-scale.md). That file's weighing
order (impact first, then frequency, then persistence) is the rule; this file only says what those
three factors look like in a screen of microcopy, and what the per-criterion anchors in
[`NNG-EM.md`](NNG-EM.md) are calibrated against.

Where this file and `NNG-EM.md`'s own per-criterion anchor columns appear to disagree, the
per-criterion column wins: it is calibrated to one criterion's operational test, and this file is
calibrated to the domain as a whole.

## What impact means here

A microcopy defect's impact is measured by what it costs the reader who hits it, in the moment they
hit it, on the assumption they cannot see anything the artifact does not state. Three questions, in
this order:

1. **Can the reader still get out?** A message that leaves a way forward, even an inconvenient one,
   is bounded. A message that leaves no way forward is not.
2. **Does the reader even notice it?** A message that is present but easy to miss is not the same
   defect as a message that is present, noticed, and unhelpful; a message that clears itself before
   the reader looks up is closer to absent than to present.
3. **What does the reader lose by getting it wrong?** Typed input, a completed multi-step flow, an
   order, saved work. Losing minutes of entry ranks above being briefly confused.

## The levels in this domain

**0, not a problem.** House style, brand voice, a preference between two wordings that both name the
cause and the next step. Two reviewers disagreeing on which of two compliant messages reads better is
a level 0 disagreement, and neither wording is a finding.

**1, cosmetic.** A wording that is correct and complete but clumsy: a redundant clause, a message
that says please twice, a capitalization inconsistency between two error strings on the same screen.
Nothing the reader has to work around. Level 1 is rare in this domain, because a short string has
little room to be merely untidy without also being unclear.

**2, minor.** The reader can still finish the task, and the cost is friction rather than a dead end.
The characteristic level-2 shape is a message that is right about one thing and silent about another:
it names the problem but not the fix, or names the fix but not why, or is presented in a container
that stays on screen so a reader who missed the styling can still read it. A second attempt succeeds.

**3, major.** The reader cannot finish the task from what the message tells them, or the message is
gone before they can use it, or correcting the problem costs them work they had already done. The
characteristic level-3 shape is a message that a reader could follow to the letter and still fail:
the generic failure that could mean five different things, the blocking failure shown in a toast that
clears itself, the long form that empties on submit. Frequency and persistence pull a borderline case
here: the same missing instruction on one screen out of ten is a 2, and on every validation message in
a flow is a 3, because the reader learns that this product's error messages never help.

**4, catastrophic.** Reserved, in this domain, for a message that actively causes loss or actively
misleads: copy that tells the reader to take an action that destroys their data, that reports success
on a failed operation, or that is the only notice of an unrecoverable loss and states nothing the
reader can act on and nowhere to go. A message that is merely unhelpful is never a 4, however bad the
underlying failure is: the severity belongs to the copy, not to the outage behind it.

## The line reviewers most often get wrong

**Do not inherit severity from the underlying failure.** A payment system being down is a serious
event; a message about it is not automatically a serious finding. Rate the copy against what a reader
holding only that copy can do. `NNG-EM-GRACE`'s own severity-3 anchor is severe because the message
offers nothing, not because sync failed.

**Do not stack criteria into severity.** One message can breach `NNG-EM-CONSTRUCTIVE`,
`NNG-EM-PLAIN-LANGUAGE`, and `NNG-EM-SPECIFIC` at once. That is three findings at their own severities,
not one finding promoted to 4. The shared scale's warning about inflation applies with particular
force in a domain where every criterion targets the same handful of words.

**Do not rate the annotation field, rate what it describes.** `Container: toast` is not a defect. A
toast carrying a message the reader must act on to continue is. The eight context fields exist so a
reviewer can judge the screen without seeing it, not so that any single token is a finding on its own.

## Scripted-lane severity is not a judgment call

The six scripted criteria assign severity from fixed rules, stated in `NNG-EM.md`'s Operational test
column and implemented in `scripts/checks.py`: `Suggested fix` for `NNG-EM-CONSTRUCTIVE`, a repetition
marker for `NNG-EM-NEUTRAL-TONE`, how much plain text survives the code span for
`NNG-EM-PLAIN-LANGUAGE`, `Container` for `NNG-EM-NOT-COLOR-ONLY`, the section's message count for
`NNG-EM-PRESERVE-INPUT`, and an error-toned marker in the message for `NNG-EM-TIMING`. A judged-lane
pass performed inline must not re-rate a scripted finding it disagrees with; the determinism claim is
the whole reason those six sit in that lane. Disagreement with a scripted severity is a rubric bug to
raise against `NNG-EM.md`, not a per-run adjustment.

## See also

- [`docs/reference/severity-scale.md`](../../../docs/reference/severity-scale.md), the shared scale
  and its Microcopy domain-anchor table this file extends.
- [`NNG-EM.md`](NNG-EM.md), the per-criterion severity 2 and 3 anchors these levels calibrate.
- [`docs/explanation/methodology.md`](../../../docs/explanation/methodology.md), section 6, why one
  scale is shared across all six domains.
