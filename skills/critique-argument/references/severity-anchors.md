# Severity anchors: critique-argument

This file extends [`docs/reference/severity-scale.md`](../../../docs/reference/severity-scale.md)
with the calibration specific to argumentative prose. The shared 0-4 scale and its weighing order
(impact, then frequency, then persistence) are unchanged here; nothing in this file redefines a level.
Per-criterion anchors at levels 2 and 3 live in [`TOULMIN.md`](TOULMIN.md); what follows is the
cross-criterion judgment those anchors assume.

## What impact means for an argument

The reader of an argumentative artifact is deciding whether to accept its conclusion. Impact is
therefore measured against one question: how far can a reader get toward that decision, and can they
recover on their own when the argument fails them?

- A defect the reader can repair by supplying the missing piece themselves is minor. An unstated
  principle the target reader ([`TOULMIN.md`](TOULMIN.md), The target reader) would supply without
  prompting costs them a moment, not the decision. The reader here is always that one defined
  construct, never whichever audience would make the artifact look best.
- A defect that leaves the reader unable to reconstruct why the conclusion follows is major. They
  cannot repair it from the artifact, because the artifact never contained the piece.
- A defect at the artifact's load-bearing point outranks the same defect anywhere else. An unsupported
  aside and an unsupported central claim are not the same finding at a different frequency; they are
  different impacts.

## Persistence compounds faster here than in prose critique

An argument is a chain. A missing warrant early in the chain does not merely inconvenience a reader
at that point: every later step that depends on it inherits the gap, so a reader who kept going has
been accumulating unearned conclusions. This is why persistence pulls argument findings upward more
readily than it does in, say, a clarity critique, where an awkward paragraph's effect usually ends
with the paragraph.

The practical rule: when a defect sits upstream of other claims in the same artifact, weigh it at the
top of the band impact set, not the bottom.

## Level 4 in this domain

Level 4 is catastrophic and blocking, and it is genuinely rare in argumentative prose because a bad
argument is usually recoverable by rewriting it. Reserve it for a case where acting on the artifact
as written causes harm the artifact itself conceals: a recommendation whose grounds contradict its
own conclusion while reading as though they support it, or a claim stated as settled where the
artifact elsewhere records the evidence against it. Both are misdirection a reader cannot detect from
the artifact, which is what separates them from a level 3 gap they can at least see.

Do not use level 4 for an argument that is merely weak, unsupported, or one-sided. That is a level 3
at most, and inflating it defeats the gate.

## Level 0 and level 1

Level 0 is a criterion swept and found satisfied, recorded but not reported. Level 1 is cosmetic: a
signposting phrase a reader would have appreciated, a counterargument acknowledged in a footnote
where the body would have carried it better. Neither changes whether the reader can evaluate the
conclusion.

## Calibration for the scripted lane

The two scripted criteria report measurable properties, not argument quality, and their severities
follow fixed bands rather than judgment ([`TOULMIN.md`](TOULMIN.md), Thresholds). Two consequences
worth stating so the judged pass does not double-count:

- A `TOULMIN-CLAIM-MARKER` finding at severity 3 and a `TOULMIN-CLAIM` finding at severity 3 on the
  same artifact are two separate defects, not one reported twice. The first says the conclusion is
  not signposted; the second says there is no single conclusion to signpost. An artifact can have
  either without the other.
- A high hedged-sentence ratio does not by itself raise any judged finding's severity. If the hedging
  actually obscures which claims the author stands behind, that shows up in `TOULMIN-QUALIFIER` on
  its own evidence, assessed against the grounds rather than against the count.

## Existing cross-domain anchors

[`docs/reference/severity-scale.md`](../../../docs/reference/severity-scale.md) already carries four
Argument anchors, written before this skill was built to calibrate levels 2 and 3 across all six
domains. They remain valid and this skill's registry is consistent with them: the missing-warrant
example there is the same shape as `TOULMIN-WARRANT`'s severity 3 anchor, and the absent-rebuttal
example is the same shape as `TOULMIN-REBUTTAL`'s. Where the two files ever disagree, this skill's
registry is the authoritative one for `TOULMIN-*` findings and the shared scale is authoritative for
the meaning of the levels themselves.
