# 0035 - A namespace may name a synthesized rubric, when its criteria are convergent

## TL;DR
- **Decision:** a criterion namespace may name **a rubric this library synthesized from several
  publishers**, not only a single publisher, when most of its criteria are stated independently by
  two or more of them. `critique-forms` is the first, with namespace **`FORMS`**. Its
  `rubric_sources` lists every publisher, and each criterion's row in `references/` cites its own.
- **Why:** the alternative credits a convergent finding to one publisher. "Give email fields the
  email keyboard" is stated independently by Baymard, Google, GOV.UK, Silver, NN/g and Wroblewski;
  filing it as `BAYMARD-INPUT-TYPE` would attribute it to one of six. That is the misattribution
  [ADR 0019](0019-clarity-two-namespaces-merged-duplicate-criteria.md) was written to prevent, arriving
  from the other direction.
- **What it does not change:** the ID grammar, the permanence rules, or any shipped namespace.
  `WCAG`, `NNG`, `PLAIN`, `WILLIAMS`, `DIATAXIS` and `TOULMIN` each still name one source, correctly,
  because each of those rubrics is one source's.
- **Status:** Accepted
- **Date:** 2026-09-25
- **Deciders:** Jonathan Prisant

## Builds on

- [`docs/reference/criterion-ids.md`](../../reference/criterion-ids.md), which reads an ID as
  `SOURCE-CRITERION` and invents IDs for a source without its own numbering (permanence rule 3).
- [0019 - clarity: two namespaces, merged duplicate criteria](0019-clarity-two-namespaces-merged-duplicate-criteria.md),
  which kept `PLAIN` and `WILLIAMS` apart so no criterion is credited to a source that never stated it.
- [`docs/internal/skill-template.md`](../skill-template.md), "`rubric_sources`": a `rubric_sources`
  entry's `id` "is usually, but need not be, the criterion namespace". This ADR uses exactly that
  allowance; it needed no change to the template.
- [N2 (critique-forms) registry draft](../release-plans/_unassigned/N2_critique-forms/criterion-registry-draft.md),
  decision 2, ruled by the maintainer on 2026-09-25.

## Context and problem statement

Every shipped skill's rubric came from one source, or from two sources kept apart by namespace. The
convention that a namespace names a publisher was never written as a rule, only followed, because it
was never tested.

`critique-forms` tests it. Its research pass read 75 sources and found most form-design rules stated
by several of them at once: the input-type rule by six, required-and-optional marking by five, the
password rules by three. None of those publishers owns the rule. A publisher-named ID must pick one,
and picking one misstates where the rule comes from.

## Considered options

1. **A synthesized-rubric namespace (`FORMS`).** Chosen.
2. **Each criterion under its strongest publisher** (`BAYMARD-`, `GOVUK-`, `WEBDEV-`, `NNG-`,
   `WROBLEWSKI-`). Rejected: five or more namespaces for one skill, "strongest" is often a toss-up
   between sources of equal standing, and a convergent rule is still credited to one of them.
3. **Mixed:** `FORMS-` for convergent rules, a publisher namespace for single-source ones. Rejected
   on permanence: IDs are never renamed, so a single-source rule that later gains a second source
   would carry a misattribution forever.

## Decision

A namespace may name a synthesized rubric when all of the following hold:

1. **Most of the rubric's criteria are convergent**, each stated independently by two or more
   publishers. A rubric that is mostly one publisher's keeps that publisher's namespace, as `NNG` and
   `WCAG` do.
2. **Attribution moves from the ID to the row, and is never lost.** `rubric_sources` in `SKILL.md`
   lists every publisher the rubric draws on, and each criterion's row in `references/` names the
   sources that state it, graded by strength of evidence.
3. **The namespace names the rubric, not a person or organization**, the way `TOULMIN` names a model
   rather than its author. It is short and reads as the domain: `FORMS`.
4. **The research record behind the synthesis is committed as a bibliography**, so a reader can
   check any row's sources without trusting the synthesis: for `FORMS`,
   [the N2 bibliography](../release-plans/_unassigned/N2_critique-forms/sources.md).

## Consequences

- **A reader cannot see a finding's publisher from its ID alone.** They see it in the criterion's
  row. That is the cost of the decision, accepted because the alternative shows a publisher that is
  wrong for most rows.
- **`run.rubrics` records `FORMS`**, the rubric the run drew on, which is accurate.
- **A precedent for N5 (critique-checkout)**, whose research base will be convergent in the same
  way, so it can take `CHECKOUT` under the same conditions without a new ADR.
- **The conditions are a gate, not a default.** A future skill built mostly from one source keeps
  that source's name, and this ADR does not license renaming any shipped namespace.

## Implementation sites

- **Checked 2026-09-25: the contract accepts it with no change.** Validator rule 5 requires every
  finding's namespace to appear in `run.rubrics`, and `run.rubrics` is never built from
  `rubric_sources` ids. `skills/_shared/merge.py` (`_rubrics_for`) derives it from the namespaces the
  findings actually cite, and each skill's `scripts/checks.py` passes its list explicitly (clarity
  passes `["PLAIN", "WILLIAMS"]`). So `critique-forms`' `checks.py` passes `["FORMS"]`, and its
  `rubric_sources` entries can name every publisher without touching validation.
- `skills/critique-forms/SKILL.md` `rubric_sources` and `references/`, when N2 is built.
- [`docs/reference/criterion-ids.md`](../../reference/criterion-ids.md) gains a `FORMS` row in its
  namespace registry, and one sentence under "Grammar" pointing here, **when `critique-forms`
  ships**. It is deliberately not edited before then, because that page is published and a registry
  row for a skill that does not exist yet would be a claim ahead of the fact.
