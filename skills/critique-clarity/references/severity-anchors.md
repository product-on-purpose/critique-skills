# critique-clarity severity anchors

Extends the "Domain anchors" section of
[`docs/reference/severity-scale.md`](../../../docs/reference/severity-scale.md) for this skill's
artifact claim: markdown or plain-text prose documents. The numeric scale itself does not vary by
domain and is not restated here. Read that document first; this file adds only the calibration a
clarity critique needs on top of it, and does not override it anywhere.

Per-criterion severity 2 and severity 3 anchors live in the criterion registries,
[`PLAIN.md`](PLAIN.md) and [`WILLIAMS.md`](WILLIAMS.md), one pair per row. What follows is the
cross-criterion calibration those rows assume.

## Applying the weighing order to prose

The shared weighing order is impact, then frequency, then persistence. In a prose document those
three read as follows.

**Impact** is what the reader cannot do because of the defect. Ask what the reader is trying to
extract from the passage - a rule, a deadline, an instruction, a recommendation - and whether the
defect stops them extracting it on one pass. A sentence that is merely inelegant has no impact. A
sentence whose subject a reader has to reconstruct before they can act does.

**Frequency** in prose is the share of a unit, not a raw count. Most of this skill's scripted checks
express it that way on purpose: three passive sentences in a four-sentence paragraph is a pattern,
while the same three in a twenty-sentence section is an occasional lapse. When a criterion's
scripted rule uses a ratio, the judged lane should reason in the same terms rather than counting
occurrences.

**Persistence** is whether the reader carries the confusion forward. A vague heading costs one act
of scanning and then stops mattering. An inconsistent term for a central concept follows the reader
through every later section that uses either word, which is why term drift outranks a single
awkward sentence even when the awkward sentence is uglier.

## Where the levels sit in prose

**Severity 1, cosmetic.** The reader loses nothing; the prose is merely below the document's own
standard. A single wordy phrase in a document that is otherwise tight. A paragraph that could open
more directly but still opens clearly. This skill's scripted lane emits no severity 1 findings by
construction: every scripted check fires at 2 or 3, because a check that fires deterministically on
something worth nothing should not be a criterion (methodology section 8, acceptance rate as the
pruning signal). A judged-lane finding at severity 1 is legitimate and rare.

**Severity 2, minor.** The reader has to work slightly harder, and gets there unaided. One lapse,
recovered within the same paragraph. The characteristic shape is an isolated instance in an
otherwise clean passage: one passive sentence among several active ones, one undefined jargon term,
one paragraph over the length threshold whose topic sentence still previews it correctly.

**Severity 3, major.** The reader cannot complete the passage's own task on one pass, or completes
it wrongly. The characteristic shape is a defect that has become the passage's default rather than
an exception to it: every step of a procedure in passive voice, every sentence of an explanation
running its action through an abstraction, a governing rule that arrives only after three sentences
of conditions. Severity 3 is also where a defect in a structurally privileged position lands, even
as a single instance, because position multiplies impact: an opening paragraph, a section that
states the one binding requirement, or the sentence carrying the deadline.

**Severity 4, catastrophic.** Reserved, and rare in this domain. A clarity defect reaches 4 only
when the document states the opposite of what it means, or when the passage a reader must act on
cannot be resolved to a single reading at all: a stacked negation whose logical sign genuinely
inverts a rule, or two sections that give contradictory instructions with no signal which governs.
Poor writing that is merely hard is never a 4. If a run reports a 4 for prose that is simply dense,
the severity is inflated and the finding should be re-rated.

## Calibration against the sibling skills

A clarity severity 3 is meant to cost a reader about what an accessibility severity 3 costs: the
primary reading task becomes hard to complete rather than merely unpleasant. Two comparisons worth
holding on to, drawn from the shared scale's own anchor tables:

- Body copy at 2.9:1 contrast across a whole article is accessibility's severity 3. Its clarity
  equivalent is a whole procedure written in passive voice: in both cases the reader can still
  technically get through, and in both cases the document's main job has become work.
- A modal dialog with no keyboard exit is accessibility's severity 3 by blocking, not by volume. Its
  clarity equivalent is the opening paragraph that buries the recommendation: one instance, in the
  one position where a single instance stops the reader from getting the document's point.

## Two failure modes this domain is prone to

**Inflating on aesthetics.** Prose critique invites taste, and taste inflates. A finding is a 3
because the reader is obstructed, never because the sentence is bad. If the violation field cannot
name what the reader fails to do, the finding is a 2 at most, and possibly a 1.

**Stacking severities on one underlying defect.** One long, interrupted, nominalized sentence can
legitimately cite three criteria at once, and each finding is genuine. Rate each against its own
criterion's anchors rather than escalating all three because the sentence as a whole is bad; the
output bound already ranks them, and the summary already counts them.
