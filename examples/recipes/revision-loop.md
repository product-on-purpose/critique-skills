---
title: The revision loop, worked example
description: One artifact through critique, disposition, revise, and re-critique, from a real golden fixture, plus the three-iteration bound and why it exists
audience: both
level: intermediate
---

# The revision loop, worked example

[Dispositions](../../docs/how-to/dispositions.md) documents the disposition-log format. This recipe
walks one artifact through the full loop the library supports: critique, disposition, revise,
re-critique, converging to zero findings at severity 3 or above.

**What's real here and what's authored.** The v1 memo and its two severity-3 findings are not
constructed for this recipe. They are `skills/critique-argument/examples/argument-golden-01-warrant-gap.md`
and its recorded envelope, `skills/critique-argument/examples/golden-01.json`, a validated golden
fixture belonging to `critique-argument`'s own test suite, copied here byte for byte. Both `TOULMIN-REBUTTAL`
and `TOULMIN-WARRANT` are judged-lane criteria, so this envelope is curated illustration in the same
sense `examples/argument/README.md` uses that phrase for judged findings: what you would see from a
real run, not the literal output of a deterministic script. The disposition log below is authored for
this recipe, one plausible reviewer's decision on the two findings. The revised v2 memo is authored for
this recipe. The re-critique envelope at the end is also authored, not a live rerun, and says so again
at the point it matters, with the reason spelled out there. All four JSON documents below were
validated with the exact commands shown, against the exact JSON shown, before this page was written.

## v1: the memo as first drafted

Verbatim from `skills/critique-argument/examples/argument-golden-01-warrant-gap.md`:

```markdown
# Recommendation: Switch Ticketing Platforms to Vendor A

We recommend adopting Vendor A's ticketing platform for the support team, effective next quarter.

Vendor B's per-seat licensing price rose 40 percent at our last renewal, from 12 dollars to 17
dollars per agent per month. Our support team currently has 40 seats, so the increase added
roughly 2,400 dollars a year to the ticketing budget with no corresponding change in features.

The support team has used a ticketing platform of some kind since 2019, and the current renewal
cycle runs through the end of this fiscal year.

We should complete the migration before the next contract renewal date.
```

## The critique: two severity-3 findings

From `skills/critique-argument/examples/golden-01.json`'s `expected_envelope`, both findings, in full:

```json
{
  "id": "F-001",
  "criterion": "TOULMIN-REBUTTAL",
  "lane": "judged",
  "severity": 3,
  "location": "the whole document, under its \"Recommendation: Switch Ticketing Platforms to Vendor A\" heading",
  "evidence": "0 of the memo's 4 paragraphs raise or answer an objection. The nearest thing to a limiting condition is its closing sentence, \"We should complete the migration before the next contract renewal date.\", which sets a deadline rather than naming a circumstance under which switching would be the wrong call.",
  "violation": "The memo answers none of the conditions its own grounds leave open: the migration cost and disruption its recommendation creates, and the alternative of renegotiating with Vendor B, which a price increase on its own does not rule out. A reader reaches the ask with no exception, cost, or competing option stated anywhere in the artifact.",
  "fix": "Add a short paragraph naming one condition the grounds leave open, for example the migration cost the switch creates or the option of renegotiating with Vendor B, and answer it.",
  "confidence": "medium"
}
```

```json
{
  "id": "F-002",
  "criterion": "TOULMIN-WARRANT",
  "lane": "judged",
  "severity": 3,
  "location": "the whole document, under its \"Recommendation: Switch Ticketing Platforms to Vendor A\" heading",
  "evidence": "The memo's only supporting paragraph is entirely about Vendor B: \"Vendor B's per-seat licensing price rose 40 percent at our last renewal, from 12 dollars to 17 dollars per agent per month.\" Vendor A's price, features, or any other property is never stated anywhere in the artifact.",
  "violation": "The claim recommends adopting Vendor A, but the grounds establish only a fact about Vendor B's price increase; the memo never states the principle connecting a fact about Vendor B to a conclusion about Vendor A, so a reader cannot see why this evidence supports switching to Vendor A specifically rather than negotiating with Vendor B or choosing a third vendor.",
  "fix": "State the principle connecting the grounds to the claim explicitly, for example by adding Vendor A's own price, or by naming a standing policy that a price increase past a stated threshold triggers a vendor search.",
  "confidence": "high"
}
```

In plain terms: the memo's only evidence paragraph is entirely about a different vendor than the one
it recommends (`TOULMIN-WARRANT`, no stated principle connecting Vendor B's price to choosing Vendor A),
and it never raises or answers a single objection to switching, not cost, not disruption, not the
option of just renegotiating (`TOULMIN-REBUTTAL`). Both are severity 3, major, fix before release, per
the shared 0-4 scale: a skeptical reader cannot reconstruct why the recommendation follows from what
the memo actually says.

Validated and gated, against the JSON above assembled into one envelope:

```
$ python -m contract.validate golden-01-envelope.json
valid
$ echo $?
0

$ python -m contract.validate golden-01-envelope.json --gate --threshold 0
valid
$ echo $?
2
```

Exit 2, not 1: both findings are severity 3, and neither is severity 4, so the gate fails on the
severity-3 count exceeding the threshold rather than on a catastrophic finding
([Gate in CI](../../docs/how-to/gate-in-ci.md#exit-codes)).

## Disposition: a human decides

Critique never auto-applies its own fixes ([Methodology, section 10](../../docs/explanation/methodology.md#10-human-in-the-loop-by-contract)).
Here the reviewer accepts both findings:

```json
{
  "contract_version": "1.0.0",
  "envelope": {
    "skill": "critique-argument",
    "skill_version": "0.1.0",
    "artifact": "skills/critique-argument/examples/argument-golden-01-warrant-gap.md",
    "artifact_sha256": "64ab59a38fe597cbc5c0ea40dc2b59154f2aeff30b0ad5708348eaaf730567c7",
    "timestamp": "2026-07-31T18:05:00Z"
  },
  "dispositions": [
    {
      "finding_id": "F-001",
      "criterion": "TOULMIN-REBUTTAL",
      "disposition": "accept",
      "note": "Fair: nothing in the memo names or answers an objection. Adding a paragraph on the renegotiation option and the migration cost before this goes to the team.",
      "decided_at": "2026-08-01T10:00:00Z"
    },
    {
      "finding_id": "F-002",
      "criterion": "TOULMIN-WARRANT",
      "disposition": "accept",
      "note": "Correct: the grounds are entirely about Vendor B, and the memo never says why that implies Vendor A. Adding Vendor A's own price and the procurement policy that connects the two.",
      "decided_at": "2026-08-01T10:00:00Z"
    }
  ]
}
```

Validated as a document on its own, then resolved against the referenced envelope, both for real:

```
$ python -m contract.validate dispositions.json
valid
$ echo $?
0
```

```python
from contract.validate import load_document, validate_document
log = load_document("dispositions.json")
envelope = load_document("golden-01-envelope.json")
validate_document(log, referenced_envelope=envelope)
# ValidationResult(errors=[], warnings=[])
```

Both `finding_id`s resolve, and both denormalized `criterion`s match. This is not always-accept for
its own sake; a real review just as often rejects or defers a finding (see `examples/clarity/README.md`
for a worked reject-and-defer disposition on a different run). Here both findings held up, so both are
accepted, which is what commits the memo's author to revising on both.

## v2: the revision

```markdown
# Recommendation: Switch Ticketing Platforms to Vendor A

We recommend adopting Vendor A's ticketing platform for the support team, effective next quarter.

Vendor B's per-seat licensing price rose 40 percent at our last renewal, from 12 dollars to 17
dollars per agent per month. Our support team currently has 40 seats, so the increase added
roughly 2,400 dollars a year to the ticketing budget with no corresponding change in features.
Vendor A's published per-seat price for the equivalent tier is 11 dollars per agent per month, and
its feature set matches Vendor B's on every capability our team actually uses today. Our standing
procurement policy triggers a vendor search whenever a renewal increase exceeds 15 percent, and
this renewal exceeded that threshold by 25 points, which is why a switch, not a renegotiation, is
the recommended path.

We considered renegotiating with Vendor B instead of switching. Vendor B's account team confirmed
in writing that the 40 percent increase reflects a new pricing floor, not a promotional rate, so
no renegotiation was on offer short of a multi-year lock-in, and a multi-year lock-in would remove
our ability to revisit vendors again before the market price settles. Switching carries a one-time
cost of an estimated 15 support-agent hours for data migration and re-training, against roughly
2,600 dollars in projected first-year savings from the lower per-seat price alone.

The support team has used a ticketing platform of some kind since 2019, and the current renewal
cycle runs through the end of this fiscal year.

We should complete the migration before the next contract renewal date.
```

What changed, mapped back to the two findings: the second paragraph now states Vendor A's own price
and the procurement policy connecting a renewal increase to a vendor search, the missing principle
`TOULMIN-WARRANT` flagged. A new third paragraph raises the renegotiation option and the migration-cost
objection and answers both, exactly the condition `TOULMIN-REBUTTAL` found unaddressed.

## Re-critique: converging to zero

**This envelope is authored, not a live rerun, and here is why that matters more than it would
elsewhere in this folder.** I wrote the revision above. Critiquing my own edit in the same context I
wrote it in is exactly the failure [clean-context critique](critic-delegation.md) exists to prevent: a
critic that has seen the author's reasoning inherits the author's blind spots
([Methodology, section 7](../../docs/explanation/methodology.md#7-determinism-model)). A real second
iteration of this loop would hand v2 to the `critique-critic` subagent, or to `critique-argument` run
inline where no subagent tool is available, exactly as the first iteration did, not back to whoever
just revised the memo. What follows is this recipe's best-effort illustration of what that clean pass
would find, marked so accordingly, and validated for contract shape only, not for whether the judgment
is one a live pass would reach:

```json
{
  "run": {
    "skill": "critique-argument",
    "skill_version": "0.1.0",
    "contract_version": "1.0.0",
    "artifact": "docs/vendor-switch-memo.md",
    "artifact_sha256": "aa0df2aff19b2a8caa4994912c064bd62a5c7cf710c52418e6e3b031c9d9c475",
    "model": "authored-illustration",
    "timestamp": "2026-08-01T11:30:00Z",
    "rubrics": ["TOULMIN"]
  },
  "findings": [],
  "summary": {
    "by_severity": {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0},
    "suppressed_count": 0,
    "gate": "pass",
    "severity_3_threshold": 0
  }
}
```

`run.model` deliberately reads `authored-illustration` rather than a pinned model ID, so this excerpt
cannot be mistaken for a real run's output if it is copied out of this page. It is schema-valid, for
real:

```
$ python -m contract.validate re-critique-envelope.json
valid
$ echo $?
0

$ python -m contract.validate re-critique-envelope.json --gate --threshold 0
valid
$ echo $?
0
```

Zero findings at any severity, gate passes. The loop stops here: both findings from v1 have no
surviving counterpart in v2 at severity 3 or above, which is the loop's own stopping condition.

## The three-iteration bound

The revision loop this library supports is bounded on purpose:

> The revision loop, when used, is bounded: critique, disposition, revise, re-critique, stopping when
> zero findings remain at severity 3 or above or after three iterations, whichever comes first.
> Unbounded loops converge on the model's preferences, not the rubric's.
>
> [Methodology, section 10](../../docs/explanation/methodology.md#10-human-in-the-loop-by-contract)

This run converged in one iteration, v1 to v2, well inside the cap. Had v2 still carried a severity-3
finding, the same four steps would run again against v2: disposition on whatever remains, a v3
revision, a third critique. If a severity-3 or higher finding is still open after the third critique,
the loop stops anyway; what remains gets dispositioned like anything else, accepted, rejected, or
deferred, rather than fed into a fourth round.

The reason is not patience. A rubric has a fixed set of criteria; a model asked to revise the same
passage a fifth or sixth time is no longer checking those criteria; it is pattern-matching on its own
prior edits and its own sense of what "better" sounds like, which drifts from what the rubric actually
requires the further the loop runs. Three iterations is enough for a real gap to get fixed and
re-checked; past that point, continuing to loop optimizes for the model's taste, not the standard the
skill is supposed to be enforcing. That is the same reasoning [Methodology, section 9](../../docs/explanation/methodology.md#9-what-this-library-is-not)
gives for why this library has no opinion of its own: a criterion that cannot cite a source does not
belong here, and a fourth revision round with no criterion driving it is exactly that, taste standing
in for a standard.

## See also

- [Dispositions](../../docs/how-to/dispositions.md), the disposition log's full field reference and
  what the acceptance-rate signal it produces is for.
- [Gate in CI](gate-in-ci.md), gating a build before a human ever reaches disposition.
- [Critic delegation](critic-delegation.md), why the re-critique step above has to run clean, and how
  to invoke it that way.
- [Methodology](../../docs/explanation/methodology.md), sections 7, 8, and 10, for the determinism
  model, the acceptance-rate evaluation this loop feeds, and the human-in-the-loop contract itself.
