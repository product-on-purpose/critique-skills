# 0016 - The contract enforcement boundary: machine-checked, and published where it stops

## TL;DR
- **Decision:** the critique contract is enforced in three named layers, schema, validator, and review, and the boundary between the second and third is **published rather than approximated**. Every cross-document consistency rule that a validator can decide is implemented and tested, including the ones an adversarial pass found missing at the freeze: integer literals across the whole summary, house style in the reserved `selector`, calendar-valid timestamps, and a warning when a run passes the gate only on the threshold it declared for itself. Everything remaining, the eight methodology field contracts that need the artifact or the critic's intent to decide, is accepted as review-lane, listed in `docs/reference/critique-contract.md`, and deliberately **not** approximated by a heuristic in the validator.
- **Why:** a heuristic that guesses whether `evidence` is a quotation would produce false failures on correct findings and false passes on wrong ones, and a green validator would then be read as "this critique is good", which is the exact confusion the contract exists to prevent. A boundary that is written down is a boundary reviewers can hold; a boundary that is half-automated is one nobody holds.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, build-run P1 contract adversarial-review pass (Claude)

## Context and problem statement

[S-02 (critique-contract spec)](../release-plans/plan_v0.1.0/S-02_critique-contract/spec.md) AC-8 requires an adversarial review agent to attempt "a finding that is schema-valid but violates a methodology field contract", to document what it finds, and to close every hole or record its acceptance here. This ADR is the second half of that acceptance criterion. The contract is frozen at this commit, and after it a change to a required field is a build-halting event, so the question of what the machine can and cannot decide has to be answered now rather than discovered by a skill pipeline in P2.

The attack surface has two distinct halves, and conflating them is the real risk.

The first half is **documents that lie about themselves**. An envelope's `summary` is the only thing the gate reads, so any disagreement between `summary` and `findings[]` is a way to buy a passing exit code. This half is decidable: both sides of the disagreement are in the document.

The second half is **documents that lie about the artifact**. A finding whose `evidence` characterizes instead of quoting, whose `location` cannot be navigated to, or whose `fix` is not actionable is a well-formed document making a worthless claim. Deciding this needs the artifact, the rubric, and in some cases the critic's own intent. No schema and no validator has any of the three.

The methodology already states the field contracts. What was missing was a statement of which of them anything checks.

## Decision drivers

- The gate is the library's contact with other people's CI. A hole that lets a severity-4 finding exit 0 is not a documentation problem, it is a false claim made automatically, at scale, on someone else's pipeline.
- Anything decidable from the document alone must be decided, or the published boundary is a rationalization for missing work rather than a description of a real limit.
- The converse discipline matters as much: a validator that reports on things it cannot actually decide teaches its users to ignore it, and an ignored validator is worse than none because it still carries authority.
- The methodology is the constitution, and it says a finding "must" do things no machine can verify. Removing those rules to make the document match the tooling would weaken the standard to fit the implementation, which is backwards.
- Whatever is accepted here has to be legible to a skill author in P2, who is the person the review lane actually falls on.

## Considered options

1. **Enforce only the schema, and treat every semantic rule as review.** Rejected outright. The counts in `summary` are checkable against `findings[]` from the same file, and leaving them unchecked makes the gate advisory. The adversarial pass built a working exploit against this posture in one attempt.
2. **Approximate the field contracts with heuristics.** For example, flag `evidence` that contains no digit and no quotation mark, or `location` containing "throughout". Rejected as the most damaging option available. It fails in both directions: a measurement written as prose ("body text renders lighter than its background at a ratio below the AA minimum") is correct evidence with no quotation mark, and "the hero banner throughout the marketing pages" is a poor location that a keyword list would have to guess at. Worse, it converts a reviewer's judgment into a lint the reviewer then defers to, and the field contracts stop being read.
3. **Require a structured `evidence` object, quotation or measurement as separate typed fields, so the contract becomes checkable.** Rejected for v0.1, and worth recording because it is the only option that could genuinely move the boundary. It would force every skill to classify its own evidence, which is a real change to what a finding is, and it interacts with the unsettled `selector` vocabulary ([0012 - location grammar](0012-location-grammar-freetext-plus-reserved-selector.md)). Freezing that shape on the strength of an untested guess is exactly what 0012 declined to do for locations. Revisit in 2.x with evidence from six shipped skills.
4. **Close every decidable hole, publish the rest, and name the layer each rule belongs to (chosen).**

## Decision outcome

Option 4.

### Closed at the freeze

Four holes were found by constructing documents and invocations that passed and should not have. Each is now an error or a warning with a regression test in `contract/tests/test_adversarial.py`.

- **Integer literals, contract-wide.** JSON Schema's `integer` type accepts `3.0`, so every count in `summary` could be written as a float the schema admits. The cross-check helpers read a non-integer as "unreadable, skip", so a single character turned rules 2, 3, and 4 off at once. The exploit: one real severity-4 finding, `by_severity` of `{"4": 0.0}`, `gate: "pass"`. It validated clean and `--gate` exited 0. Fixed on both sides, the rule now covers the whole summary, and the cross-checks now read integral floats as the numbers they are so no single mistake can disable them.
- **House style in the reserved `selector`.** The spec requires the validator to reject an em dash or en dash in any string field. Enforcement was by schema pattern, and patterns reach only typed fields, so the one object with `additionalProperties` open was a way in, for keys as well as values. The check now walks every string in the parsed document, which also covers any field a later minor version adds.
- **Calendar-valid timestamps.** The pattern fixes the shape and the trailing `Z` and cannot reject `2026-02-31`. A run timestamp is one third of the composite key a disposition log joins on, so an impossible date is a join key nothing can reproduce. Leap seconds are accepted, per RFC 3339.
- **A negative `--threshold`.** `--threshold -1` made a run with zero severity-3 findings exit 2, because every count is above minus one. `severity_3_threshold` is a count with a minimum of 0 in the schema and the CLI override now agrees with it. The neighbouring case, `--gate` on a disposition log, was already correct and already exited 4; it was untested, and is now pinned rather than fixed.

### Accepted, with the reasoning

**The producer declares its own pass mark.** `severity_3_threshold` is policy, and the envelope carrying it was produced by the skill under test. Ten severity-3 findings under a declared threshold of ten is internally consistent and passes. This cannot be an error, because a nonzero threshold is a legitimate project policy and the field exists so the exit code is computable from `summary` alone. It is instead a warning, fatal under `--strict`, and the documentation now tells a consumer gating on someone else's envelope to pass `--threshold` explicitly. Policy set by the judged party is a governance problem, and the honest fix is to make it visible, not to pretend a number can detect it.

**Severity is unverifiable.** The validator makes `by_severity` agree with `findings[]`; nothing can make either agree with the artifact. A run that rates a catastrophe a 2 emits a valid envelope, and so does one that rates everything a 4. The methodology's answer is the disposition log: acceptance rate per criterion is the pruning signal, and a criterion that inflates gets caught by humans rejecting its findings, over runs, which is slower than a validator and is the only mechanism that can work at all.

**Suppressed findings are counts, not documents.** Their severities are the producer's claim. Rules 2 and 3 force suppression to land in severities 0 to 2, which bounds the damage without verifying the claim.

**The eight field contracts.** `location` navigable, `evidence` quoted or measured, `violation` naming the breached part, `fix` actionable, `lane` honest, `severity` deserved, `stripped_context` complete, `rubric_source` correct for a BYOR run. All eight need the artifact, the rubric, or the critic's intent. All eight are listed in `docs/reference/critique-contract.md` under "Where enforcement stops", alongside the matching list of what a passing validator **does** mean, so the boundary reads in both directions.

**One grammar inconsistency, documented rather than fixed.** `criterionId` allows 64 characters while `rubricNamespace` caps a namespace at 32, so a criterion with a 40-character namespace is well formed and can never appear in a valid envelope, because the namespace it needs listed in `run.rubrics` cannot be listed. Narrowing a published pattern is a major contract version and nothing real is near either limit. Recorded in `docs/reference/criterion-ids.md` and pinned by a test.

## Consequences

**Positive:** the gate is now sound against every attack the freeze review could construct from a document alone, and each attack is a named test, so a regression is a red build rather than a quiet false claim. The boundary is published in the reference documentation, which gives a P2 skill author a checklist of what their own instructions have to carry, and gives an external reader an honest account of what a green validator asserts.

**Negative:** the review lane is now explicitly load-bearing, and nothing in v0.1 measures whether it holds. A skill could emit characterizing evidence on every finding and pass CI indefinitely. The bench measures whether findings land on planted defects, not whether their evidence is quoted, and `bench/README.md` says so under "What the bench does not measure". The first real evidence about the review lane will come from disposition logs, which need users.

Rule 11 will warn on legitimate envelopes. A project that genuinely sets a severity-3 threshold of 2 sees a warning on every run that uses it. That is the intended noise: the warning is about the shape of the arrangement, not about a mistake, and `--strict` is opt-in.

**Neutral:** three of the four fixes are validator-only and cost no contract version. The `noEmDash` pattern changed form, from a `$` anchor to the end-of-input assertion used everywhere else in the file, which is editorial: both schemas were updated together and the CI drift check between them still passes byte for byte.

## Implementation sites

- `contract/validate.py`: rules 6, 9, 10, and 11, and the `_as_count` coercion that keeps rules 2, 3, and 4 alive in the presence of a float. Written.
- `contract/tests/test_adversarial.py`: one test per attack, including the ones asserting that the accepted residue is exactly as permissive as this ADR says. Written.
- `contract/README.md`: the eleven rules and the expanded "What the schema does not check". Written.
- `docs/reference/critique-contract.md`: "Where enforcement stops", the three-layer table, and both directions of the boundary. Written.
- `docs/explanation/methodology.md`: the section 5 example envelope now reconciles with the section 7 output bound it previously contradicted, and the threshold caveat is stated in the constitution. Written.
- Not yet created: the skill template's own critique protocol (S-04), which is where the review-lane rules become instructions a skill actually follows.
