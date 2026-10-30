# 0042 - Contract 1.1.0: the disposition log's iteration field, the revision brief, and the reserved selector's deprecation

## TL;DR
- **Decision:** the next contract version is **1.1.0**, a minor version under
  [ADR 0013](0013-contract-versioning-independent.md), and it carries exactly three changes, all
  optional, so every 1.0.0 document stays valid.
  - The disposition log gains an optional `iteration` field: an integer of at least 1, with no
    schema maximum.
  - The revision brief joins the contract as a fourth document type, with validator coverage.
  - The reserved `selector` object is marked deprecated. It is not deleted.
- **Why one version, not three:** all three were ruled in one sitting, all three land with the
  revision-loop chain's build, and a minor version per field would publish three contract versions
  in one release window for no consumer's benefit.
- **Ruled:** by the maintainer on 2026-10-30, in the decision walks of the N4 (revision-loop chain)
  and E54 (cross-library composition) drafts, and the backlog ruling on E36 (reserved selector).
- **Status:** Accepted (2026-10-30). **Not built.** The schema still reads 1.0.0. N4's
  implementation builds it.

- **Status:** Accepted
- **Date:** 2026-10-30
- **Deciders:** Jonathan Prisant (the rulings). Drafted by Claude from the three rulings,
  `contract/critique-contract.schema.json` as it stands on `main`, and ADRs 0012, 0013 and 0040.

## Builds on

- [0012 - Location grammar: free text plus a reserved selector](0012-location-grammar-freetext-plus-reserved-selector.md),
  whose own confirmation question this ADR answers.
- [0013 - Contract versioning, independent of the plugin](0013-contract-versioning-independent.md),
  whose minor-version rule makes all three changes additive.
- [0040 - The revision loop pauses with a revision brief](0040-revision-loop-pauses-with-a-revision-brief.md),
  which ruled the `iteration` field into contract 1.1.0 and kept the brief outside the contract
  "until a second consumer exists. It joins the contract when E54 (cross-library composition)
  consumes it."
- [N4 (the revision-loop chain)](../backlog/new-components.md),
  [E54 (cross-library composition)](../backlog/enhancements.md) and
  [E36 (confirm or deprecate the reserved selector)](../backlog/enhancements.md).

## Context and problem statement

Three separate rulings each change the contract.

1. **N4's walk** settled the field ADR 0040 left unnamed. It is `iteration`, an integer of at least 1,
   with no schema maximum. The chain's own stop-check enforces the three-iteration bound, so a future
   change to that bound in methodology section 10 does not become a contract change. N4's walk also
   fixed the brief's shape: one JSON document per pause, holding `envelope` (the same reference shape
   `dispositionLog.envelope` already uses), `iteration`, and `items`, an array of
   `{finding_id, criterion, location, fix}` that reuses the finding object's own field names.
2. **E54's walk** chose to have the cross-library recipe produce a revision brief, sequenced after
   N4's build. That makes E54 the second consumer ADR 0040 named, so the brief joins the contract.
3. **E36's ruling** answers ADR 0012's question at release-candidate time: did any skill find
   `selector` insufficient or unnecessary? No skill writes it. No committed envelope, golden example
   or bench run contains it, across all seven shipped skills. ADR 0012 said that, if it was
   unnecessary across the launch skills, "the field is deprecated in contract 1.1 rather than
   deleted".

Each change is additive, so each alone would be a minor version. The question this ADR settles is
whether they ship as one version or several, and what the deprecation means.

## Considered options

1. **One minor version, 1.1.0, carrying all three (chosen).** It lands with N4's build. E54 is
   sequenced after N4, so the brief's schema is written once, beside the code that writes briefs.
2. **One minor version per change, 1.1.0, 1.2.0 and 1.3.0.** Rejected. Nothing consumes the
   intermediate versions, and three bumps triple the edits to every site that states the version.
3. **Delete `selector` instead of deprecating it.** Rejected by ADR 0012's own terms and by
   ADR 0013: removing a property is a major change, and a 1.0.0 envelope that carried one would stop
   validating.

## Decision outcome

Option 1. Contract 1.1.0 is defined by these three changes and nothing else.

- **`$defs/dispositionLog`** gains an optional `iteration`: `{"type": "integer", "minimum": 1}`.
  `additionalProperties: false` stays, so the field must be added to `properties`.
  `contract/validate.py`'s rule 6 (integer literal) covers it, so `"iteration": 2.0` is rejected.
- **`$defs/revisionBrief`** is added as a fourth document type, with `envelope`, `iteration` and
  `items` required and `additionalProperties: false`. The root dispatch, which today tells a
  disposition log from an envelope by the presence of a `dispositions` key, gains a rule for it. The
  build chooses that rule and records it in `contract/README.md`.
- **`$defs/selector`** gains the JSON Schema `deprecated: true` annotation, and its description says
  it is deprecated as of 1.1.0 and why. A document that carries `selector` still validates. Producers
  should stop writing it, and no consumer was ever permitted to read it.

## Consequences

**Positive:** a revision brief becomes something a consumer outside this repository can validate,
which is what E54's recipe needs to be a proof rather than a narration. The one reserved field the
schema never used stops inviting new producers.

**Negative:** the version string is stated in several places, and every one moves together. These
are the schema's own `description` and `$comment`, `contract/README.md`'s opening paragraph, and the
`CONTRACT_VERSION` constant in `skills/_shared/envelope.py`, which stamps every envelope a skill
emits. Envelopes emitted after the bump read 1.1.0, so any test or fixture that pins `1.0.0` for a
newly emitted envelope needs the same change. Committed fixtures and bench envelopes stay at 1.0.0,
because they are evidence.

**Neutral:** no skill version moves for the contract bump alone. The contract is versioned
independently of the skills (ADR 0013).

## What this ADR does not decide

- The root-dispatch rule for the revision brief. N4's build chooses it.
- Whether `selector` is ever removed. That would be contract 2.0.0, and nothing schedules one.
- Anything about a structured location vocabulary. ADR 0012's reasoning still stands for `location`.
