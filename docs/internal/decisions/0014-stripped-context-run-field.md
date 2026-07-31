# 0014 - Stripped framing is recorded in a typed `run.stripped_context` ledger, not a notes field

## TL;DR
- **Decision:** an envelope records disregarded framing in `run.stripped_context`, an optional array of `{kind, note}` objects where `kind` is one of `authorial-framing`, `requester-opinion`, `prior-critique`, `scope-steering`, `other` and `note` is required prose. The field is optional and, when present, must hold at least one entry: absence asserts that nothing was stripped, and an empty array is rejected because it says nothing a missing key does not. There is no free-text `run.notes` in contract 1.x.
- **Why:** clean-context critique is a load-bearing methodology claim, not a footnote, and [S-06 (critic-subagent spec)](../release-plans/plan_v0.1.0/S-06_critic-subagent/spec.md) AC-3 needs a field a test can assert against deterministically. A `notes` string is a junk drawer: it cannot be counted, compared across runs, or checked, and anything else that wants a place to put prose will end up in it. A typed ledger makes "how often does framing reach the critic, and of what kind" a measurable number instead of an anecdote.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, build-run P1 contract-designer pass (Claude)

## Context and problem statement

[S-06 (critic-subagent spec)](../release-plans/plan_v0.1.0/S-06_critic-subagent/spec.md) OQ-1 asks for the "envelope field for stripped-framing notes (`run.notes` versus a dedicated field)" and directs it to be resolved with [S-02 (critique-contract spec)](../release-plans/plan_v0.1.0/S-02_critique-contract/spec.md) during phase P1 so the schema ships it. S-06 AC-3 fixes the behaviour under test: given an invocation that includes "the author thinks section 2 is fine, focus elsewhere," the subagent's output ignores the steering and its envelope notes the stripped framing in a run-level field.

The methodology's clean-context rule (section 7) is short and absolute: "Critique runs in a fresh context that has not seen the artifact being authored. A critic that inherits the author's framing inherits the author's blind spots." S-06 operationalizes it two ways: the subagent refuses inputs that embed authorial framing beyond the artifact itself, and, per AC-3, when framing arrives anyway it proceeds on its own terms and says so. Those are different paths and both need to exist: refusal is for an invocation so contaminated that a clean critique is impossible, and the ledger is for framing that arrived, was disregarded, and must leave a trace. Without a trace, "the critic ignored the steering" is an unverifiable claim about a model's behaviour.

## Decision drivers

- The claim being evidenced is one of the library's differentiators. A published envelope that says which framing arrived and was set aside is checkable by a skeptical reader; a claim in a SKILL.md that the critic ignores framing is not.
- S-06 AC-3 is a test. A test needs a deterministic assertion target: a key at a known path with a known type. `run.notes` containing an English sentence forces the test to grep prose, which makes the acceptance criterion depend on wording.
- Acceptance-rate telemetry already taught the library this lesson once. The disposition log is schema-defined rather than free-form precisely because a free-form record cannot produce the signal it exists to produce. The same argument applies here: `kind` makes the ledger aggregable across a corpus, so "framing reached the critic in 12 of 20 bench runs, 9 of them scope-steering" is a query, not a reading exercise.
- Every other object in `contract/critique-contract.schema.json` sets `additionalProperties: false`. A free-text `notes` field is the standard way that discipline erodes: it becomes the place emitters put anything the schema will not accept, and within two releases it carries semantics nobody agreed to.
- The field must not become mandatory ceremony. Most runs strip nothing, and an emitter forced to write `"stripped_context": []` on every clean run learns to treat the field as noise.

## Considered options

1. **`run.notes`, a free-text string or array of strings.** Rejected: uncountable, ungreppable without depending on wording, and an open invitation for unrelated prose. It would also make S-06 AC-3 a substring assertion.
2. **`run.clean_context`, a boolean.** Rejected: records that something happened while discarding what happened. A false value with no detail cannot be audited, and a reader cannot tell whether the stripped item was a stray opinion or a full prior review.
3. **Per-finding annotation.** Rejected: the framing arrives with the invocation, not with a finding, so attaching it to findings duplicates it across every finding and leaves nowhere to record framing that touched no finding at all. S-06 AC-3 also says run-level explicitly.
4. **A separate top-level envelope key, a sibling of `run`, `findings`, and `summary`.** Rejected: the fact describes the run, and the top level of the envelope is deliberately three keys. Adding a fourth for a rare condition costs every consumer a branch.
5. **Typed `run.stripped_context` array, optional, non-empty when present (chosen).**

## Decision outcome

Option 5, as `$defs/strippedContext`:

- `type: array`, `minItems: 1`, `uniqueItems: true`. Optional on `run`. Absence is the positive assertion that nothing was stripped; an empty array is a contract violation.
- Items are objects with `additionalProperties: false` and both `kind` and `note` required.
- `kind` is a closed enum: `authorial-framing` (the author's account of the artifact), `requester-opinion` (what the requester believes is fine or broken), `prior-critique` (earlier findings or reviews), `scope-steering` (instructions to concentrate on or avoid part of the artifact), and `other`.
- `other` exists so a novel case produces a valid envelope with a readable note rather than a lost note or an invalid document. Because `note` is required in every case, `other` degrades to the prose option only for the classification, never for the content.
- `note` is `$defs/prose` capped at 1000 characters: non-empty, trimmed, no em dash or en dash, like every other prose field in the contract.

The AC-3 case produces an entry of kind `requester-opinion` or `scope-steering`, both of which fit "the author thinks section 2 is fine, focus elsewhere"; the test asserts on the field's presence and its `kind` being in the enum, not on a specific member, so a defensible classification either way passes.

Relationship to the refusal rule: refusal and recording are not alternatives. The subagent refuses an invocation whose contamination makes a clean critique impossible, and returns no envelope. Where it proceeds, every piece of framing it set aside gets an entry. An envelope that proceeded despite framing and left `stripped_context` absent is a lie the contract cannot catch, which is why S-06's own definition, not the schema, carries the behavioural requirement.

## Consequences

**Positive:** the clean-context claim becomes evidence in the published record instead of an assertion in documentation. The bench can count framing exposure across a corpus and per model. S-06 AC-3 gets a stable assertion target that no rewording can break. The contract keeps `additionalProperties: false` everywhere except the one reserved selector object (see [0012 - Location grammar](0012-location-grammar-freetext-plus-reserved-selector.md)), with no general-purpose prose sink anywhere.

**Negative:** a closed enum will meet a case it does not fit, and `other` will absorb it until a contract minor version adds a member. Adding an enum member is a minor bump under [0013 - Contract versioning](0013-contract-versioning-independent.md), so the cost is small but real. Emitters also have to classify, which is one more judgment in a component whose job is to make judgment auditable.

**Neutral:** most envelopes will omit the field entirely. Consumers must treat absent and empty as the same thing at read time even though the schema permits only the former.

## Implementation sites

- `contract/critique-contract.schema.json`: `$defs/strippedContext` and the `run.stripped_context` property.
- `contract/README.md`: the run-record field table and the note that absence asserts nothing was stripped.
- Not yet created: `agents/critique-critic.md` (S-06, critic-subagent spec), whose definition must populate the ledger whenever it proceeds despite framing, and its AC-3 test.
