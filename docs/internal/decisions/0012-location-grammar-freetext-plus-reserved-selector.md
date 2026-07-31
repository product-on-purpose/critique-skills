# 0012 - Location grammar: free text now, structured selector reserved and unvalidated

## TL;DR
- **Decision:** `finding.location` is a free-text string, required, constrained only to be non-empty, trimmed, dash-free, and at most 400 characters. A structured pointer lives beside it in an optional `finding.selector` object that contract 1.x reserves and deliberately does not validate: it is the one and only place in `contract/critique-contract.schema.json` where unknown properties are allowed. `finding.instances[]` repeats the same pair in object form for recurring breaches.
- **Why:** the methodology's own operational test for the artifact gate is "can a finding name a location," which is a prose test, and the methodology lists location granularity for non-linear artifacts as an open question. A structured grammar that covers markdown headings, HTML nodes, slide indices, and dashboard regions does not exist yet; inventing one at contract-freeze time would freeze the wrong vocabulary into the one interface every skill, the bench, and the gate depend on. Reserving the field now costs nothing and means v0.2 adds a vocabulary rather than a field.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, build-run P1 contract-designer pass (Claude)

## Context and problem statement

[S-02 (critique-contract spec)](../release-plans/plan_v0.1.0/S-02_critique-contract/spec.md) OQ-1 asks how findings locate themselves in non-linear artifacts, and proposes as its v0.1 answer "free-text location plus optional structured `selector` field reserved but unvalidated," to be confirmed at RC. The question is inherited from the methodology's own open-questions list ("Location granularity: there is no settled convention for locating findings in non-linear artifacts such as designs and dashboards. Text artifacts are straightforward; visual ones are not").

The decision matters more than it looks. `location` is half of the library's ground-truth key: seeded-defect recall matches a planted defect to a reported finding on `(criterion, location)` within a documented tolerance, and run-to-run consistency is the mean pairwise Jaccard similarity over `(criterion_id, location)` sets. If `location` is free text, both metrics need a per-domain tolerance rule to compare two strings that mean the same place. If `location` is structured, both metrics get exact equality, but only for the artifact types the structure covers.

The launch slate makes the coverage problem concrete: `critique-clarity` and `critique-argument` locate in prose (section, paragraph, sentence), `critique-accessibility` locates in a DOM (element, selector, attribute), `critique-docs` locates in a page tree, and `critique-microcopy` locates in a string list whose "position" may be a key rather than a coordinate. One grammar over all five, designed before any of the five skills exist, is a guess.

## Decision drivers

- The methodology's Part 1 gate test is prose by construction: "can a finding name a location? If a finding cannot say 'Section 3, second paragraph' or 'the hero banner' or 'slide 7 title,' the framework fails Part 1." A required structured selector would make the contract stricter than the constitution it implements.
- The methodology's example finding uses `location: "Section 2, hero banner"`, and S-02 AC-7 requires the promoted `docs/explanation/methodology.md` examples to match the shipped schema exactly. Changing `location` to an object would force an edit to the constitution to satisfy a machine convenience, which is the wrong direction of travel.
- Contract-freeze timing: phase A3's decision gate makes any change to finding or envelope required fields after this phase a build-run stop condition. A field added later is a contract minor version; a required field whose shape is wrong is a major version and a rewrite of every skill that emits it.
- [S-03 (bench-harness spec)](../release-plans/plan_v0.1.0/S-03_bench-harness/spec.md) OQ-1 already owns "location-tolerance definitions per domain," documented in `bench/README.md`. Free-text locations make that tolerance rule necessary; they do not make it harder than it already is, because even a structured selector would need tolerance across representations (a heading path versus a line number).
- Strictness elsewhere in the schema is absolute: every object sets `additionalProperties: false`. An unvalidated escape hatch has to be justified as an exception, bounded in blast radius, and unreadable by anything that matters, or it becomes the hole through which the contract leaks.

## Considered options

1. **Free-text `location` only, no reserved field.** Rejected: when a domain does produce a usable structured pointer (accessibility has CSS selectors today, for free, from the same DOM walk that finds the defect), there is nowhere to put it, so the information is discarded or smuggled into the prose string, which corrupts the metric key.
2. **Structured `location` object with a required grammar per artifact type.** Rejected: no such grammar has been validated against a single real skill yet; three of the six launch domains do not exist as code at contract-freeze time. It also contradicts the methodology's prose test and its own open question, and it breaks the constitution's example.
3. **Free-text `location` plus an optional, reserved, unvalidated `selector` object (chosen).** The prose string stays the contract and the metric key. `selector` is accepted, carried, and ignored: producers may write it, consumers must not depend on it, and no v0.1 metric reads it. When the vocabulary settles, contract 1.x adds the validation in place, with no field migration.
4. **Free-text `location` plus a reserved `selector` typed as a free-form string.** Rejected: a string forces every producer to invent an encoding immediately (is it CSS? a JSON pointer? a heading path?), which is the same guess as option 2 with none of the enforcement. An object with named keys lets each domain namespace its own pointer without colliding.

## Decision outcome

Option 3.

- `finding.location` is `$defs/prose` with `maxLength: 400`. Non-empty, trimmed, no em dash or en dash. The methodology's rule that "throughout the document" is not a location is review-lane, not schema-checkable, and `contract/README.md` says so explicitly rather than pretending the schema catches it.
- `finding.selector` is `$defs/selector`: `{"type": "object", "minProperties": 1}` and nothing else. Empty objects are rejected because an empty selector is noise, not data. This is the single extensibility exception in the schema, and its blast radius is exactly one optional field that no consumer is permitted to read in v0.1.
- `finding.instances[]` items are objects of `{location, selector?, evidence?}` with `additionalProperties: false`, `minItems: 2`, and `uniqueItems: true`. Instances are objects rather than bare strings so that a recurring finding can carry a per-instance selector and, more importantly, per-instance evidence: without it, an instance list of forty locations would carry one quotation and thirty-nine unevidenced assertions, which breaks the methodology's evidence contract in the exact place the methodology already flags as an open question (instance explosion).
- Aggregation of instances into or out of separate findings stays out of scope, as S-02 (critique-contract spec) Non-Goals requires; this decision only guarantees the shape is expressible when the rule is settled.

Confirmation at RC, per S-02 OQ-1, means one question: did any launch skill find `selector` insufficient or unnecessary? If unnecessary across all six, the field is deprecated in contract 1.1 rather than deleted.

## Consequences

**Positive:** the contract cannot be wrong about a grammar it does not assert. The constitution's example validates unchanged. Skills that have a cheap structured pointer can record it from day one, so the v0.2 vocabulary design starts from collected evidence rather than from a whiteboard. `location` remains directly human-readable, which matters because the disposition step, where the library says its value lives, is a person reading findings.

**Negative:** recall and consistency depend on string matching with a per-domain tolerance, which is a documented approximation and a known source of measurement noise; S-03 (bench-harness spec) OQ-1 carries that cost and must publish the tolerance rule per domain. Two runs that name the same place differently ("Section 2, hero banner" and "the hero banner in section 2") score as different locations unless the tolerance rule normalizes them, which understates consistency. This is measured noise, not hidden noise, and the alternative was unmeasured coverage gaps.

**Neutral:** `selector` is dead weight in envelopes that do not use it, at a cost of one optional key. Consumers written against contract 1.0 that later meet a 1.1 envelope carrying validated selectors keep working, because they were forbidden from reading the field anyway.

## Implementation sites

- `contract/critique-contract.schema.json`: `$defs/locationText`, `$defs/selector`, `$defs/instance`, and `finding.instances`.
- `contract/README.md`: the "What the schema does not check" section names the location-quality rule as review-lane, and the extensibility note names `selector` as the only object accepting unknown properties.
- Not yet created: `bench/README.md` location-tolerance rules per domain (S-03, bench-harness spec, OQ-1), and `docs/reference/critique-contract.md` commentary.
