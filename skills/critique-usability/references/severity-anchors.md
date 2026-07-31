# Severity anchors

This skill's own domain-anchor prose, extending
[`docs/reference/severity-scale.md`](../../../docs/reference/severity-scale.md)'s "Domain anchors"
section for `critique-usability`. Artifact type: HTML or markdown UI specs and page mockups, not live
running applications.

Per-criterion severity 2 and 3 anchors live in [`references/NNG-HEURISTICS.md`](NNG-HEURISTICS.md),
one pair per criterion. This file carries the calibration that is domain-wide rather than
per-criterion, and the second rubric source this skill declares.

## Second rubric source: NNG-SEVERITY

`SKILL.md` declares two `rubric_sources`. The second one, `NNG-SEVERITY`, is operationalized here
rather than in a criterion table, because it contributes no criterion IDs
([ADR 0020 (usability severity source)](../../../docs/internal/decisions/0020-usability-severity-ratings-anchor-not-criteria.md)).
There is nothing in a UI spec that is a severity-3 problem on its own; severity is applied after a
heuristic finding already exists, to say how bad that finding is.

- **Living reference (canonical URL):** Nielsen, J. (1994-11-01). Severity Ratings for Usability
  Problems. Nielsen Norman Group.
  `https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/` Accessed
  2026-07-31.
- **Original book source (ISBN + chapter):** Nielsen, J. (1993). *Usability Engineering*, ch. 4
  sec. 4.9 (Interface Evaluation), with the heuristics themselves in ch. 5. Boston: Academic Press /
  Morgan Kaufmann. ISBN 0-12-518406-9 (paperback), 0-12-518405-0 (hardcover).
- `rubric_sources.operationalization`: `paraphrased` (copyrighted NN/g material).

## What this skill takes from that source, and what it drops

The shared 0-4 scale in `docs/reference/severity-scale.md` is already adapted from this source, and
the methodology says so (section 6). This skill inherits that scale unchanged: it does not define a
parallel one, and a severity 3 here means what a severity 3 means in every other skill of the family.

The source weighs four factors. `docs/reference/severity-scale.md` weighs three of them, in a fixed
order: impact, then frequency, then persistence. The fourth factor, the problem's effect on the
product's market reception, **is deliberately not weighed by this skill**. The reason is this skill's
artifact claim: a static UI spec or page mockup carries no evidence about how a shipped product is
received, so a market-impact judgment made against it would be the critic's own speculation wearing a
severity number. That omission is a stated decision, not an oversight
([ADR 0020 (usability severity source)](../../../docs/internal/decisions/0020-usability-severity-ratings-anchor-not-criteria.md)).

The source also recommends averaging severity ratings across several independent evaluators. This
family gets the same reliability property by a different route, so no skill implements averaging:
run-to-run consistency across k runs is measured directly by the bench harness
(methodology section 8), and the acceptance-rate signal from the disposition log is what prunes
criteria that a human reader keeps rejecting.

## Rating a design defect from a static artifact

Impact is judged against the user the artifact describes, not against the reader of the artifact. A
missing confirmation on a destructive action is severe because a user would lose work, even though
nobody loses anything by reading the spec. The reverse also holds: a spec that is confusing to read
but describes a sound interface is not a usability finding at all, and belongs to `critique-clarity`
or `critique-docs`.

Where the artifact is silent, severity is assigned to what the artifact commits to, and the finding
says so. A mockup that never specifies what happens after an action is a real NNG-H1 finding, because
an unspecified state is an unbuilt state; it is not rated as though the worst possible runtime
behavior were certain. In practice this caps most silence-based findings at 3 rather than 4: level 4
is reserved for a design that, as specified, destroys user work or blocks the artifact's primary task
outright with no path around it.

Frequency in a static artifact counts screens and controls, not sessions. A defect appearing on one
screen of a twelve-screen spec is a single occurrence; the same defect on every screen of a flow is
the recurrence that pulls a borderline finding up within the range impact already set. Persistence
asks whether the user carries the cost forward: a mislabeled control they learn once and then know is
less persistent than a value they must re-derive at every step.

## Fixed severities for the scripted lane

The scripted lane is a determinism claim, so its severities are computed by rule rather than judged.
`scripts/checks.py` emits exactly these, and the judged pass does not re-rate a scripted finding:

- **NNG-H3-DEADEND**: severity 3 when the dead-end state has at least one incoming edge, because a
  user can reach it and then cannot leave. Severity 2 when it has no incoming edge either, because
  the defect sits in a fragment of the artifact no user path reaches and reads as spec hygiene.
- **NNG-H4-CONTROL-NAMING**: severity 2 when exactly two distinct members of one synonym set appear,
  which the user resolves by inference. Severity 3 when three or more appear, at which point the
  artifact offers no stable naming to infer from.
- **NNG-H6-LABELED**: severity 2 for an unnamed control among labeled siblings, whose neighbours give
  a partial cue. Severity 3 when every control in one container is unnamed, so there is no labeled
  neighbour left to infer from. Container is read per grammar, and the reading is the whole rule, so
  it is stated here rather than left to the code: in HTML it is the nearest enclosing `form` or
  `nav`, or the nearest element with `role` `toolbar`, `menu`, or `menubar`; in a markdown spec it is
  the control or field list the entry sits in. Controls with no such enclosing container are compared
  against each other as one document-level group, so an artifact whose every ungrouped control is
  unnamed is severity 3 on the same reasoning, and a single unnamed control among named ungrouped
  ones is severity 2.

## Clean is not a special case

Not every UI spec this skill critiques carries a usability defect. A run that reports zero findings on
a genuinely clean artifact is the correct output, and the bench corpus plants nothing in at least one
artifact per domain on purpose. Manufacturing a severity 1 finding to avoid an empty report is the
inflation the shared scale exists to prevent.
