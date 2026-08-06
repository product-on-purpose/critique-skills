---
name: critique-clarity
description: "Reviews markdown or plain-text prose for clarity against the Federal Plain Language Guidelines and Williams' Style: readability, passive voice, sentence length, and nominalization density. Use when the user asks for feedback, a second opinion, a red-line pass, or a quality check on a memo, PRD, proposal, or any prose document before it goes out."
version: 0.1.0
license: Apache-2.0
rubric_sources:
  - id: PLAIN
    citation: "Federal Plain Language Guidelines, Plain Language Action and Information Network (PLAIN), March 2011, Revision 1, May 2011."
    url: https://www.plainlanguage.gov/guidelines/
    accessed: 2026-07-31
    operationalization: open-standard
  - id: WILLIAMS
    citation: "Williams, J. M., & Bizup, J. (2016). Style: Lessons in Clarity and Grace (12th ed.). Pearson. ISBN 978-0-13-408041-3, ch. 3-6, 8-11."
    url: null
    accessed: 2026-07-31
    operationalization: paraphrased
checks:
  scripted:
    - PLAIN-ACTIVE
    - PLAIN-CONCISE
    - PLAIN-DOUBLE-NEGATIVE
    - PLAIN-HEADINGS
    - PLAIN-JARGON
    - PLAIN-LISTS
    - PLAIN-MUST
    - PLAIN-NOMINALIZATION
    - PLAIN-PARAGRAPH
    - PLAIN-PRONOUNS
    - PLAIN-SENTENCE-LENGTH
    - PLAIN-SUBJECT-VERB-OBJECT
    - PLAIN-TRANSITIONS
    - WILLIAMS-PARALLELISM
    - WILLIAMS-SHAPE
  judged:
    - PLAIN-AUDIENCE
    - PLAIN-CONSISTENT-TERMS
    - PLAIN-MAIN-IDEA-FIRST
    - PLAIN-ORGANIZE
    - WILLIAMS-CHARACTER-ACTION
    - WILLIAMS-COHERENCE
    - WILLIAMS-COHESION
    - WILLIAMS-STRESS
---

# critique-clarity

Reviews a markdown or plain-text prose document against two operationalized rubrics: the Federal Plain
Language Guidelines (`PLAIN`, open standard) and Joseph M. Williams and Joseph Bizup's *Style: Lessons
in Clarity and Grace* (`WILLIAMS`, paraphrased). Together they cover readability mechanics such as
active voice, sentence length, and nominalization density, alongside judged qualities such as audience
fit and passage-level cohesion, and report findings as a contract-valid run envelope.

**Artifact claim.** This skill evaluates markdown or plain-text prose documents: memos, PRDs, proposals,
policy explanations, and similar continuous prose. It does not evaluate HTML rendering, visual layout,
non-prose structured data, or any of the other five launch skills' artifact types; a document that is
mostly a UI spec, an error-message list, or an argumentative essay's structure specifically is better
served by `critique-usability`, `critique-microcopy`, or `critique-argument` respectively.

## Contract

Every finding this skill emits conforms to `contract/critique-contract.schema.json`. See
`docs/reference/critique-contract.md` for the field contracts a schema cannot check on its own:
location navigable unaided, evidence quoted or measured rather than characterized, violation naming the
breach, fix actionable and specific.

## Protocol

Follow these four passes in order. Do not skip ahead to severity or fixes while still sweeping.

1. **Inventory.** Map the artifact's structure (sections, headings, components, whatever the
   artifact type has). No judgments yet, no findings yet. This pass exists so the sweep in step 2
   does not anchor on whatever was noticed first.
2. **Criterion sweep, in ID order.** Walk every criterion in `checks.scripted` and `checks.judged`,
   in ascending ID order, evaluating each against the whole artifact before moving to the next.
   Run the scripted lane via `scripts/checks.py <artifact>`; perform the judged lane yourself,
   criterion by criterion, in the same fixed order.
   One-time prerequisite: `pip install "jsonschema>=4.20,<5"`. Claude Code's `/plugin install`
   does not install Python packages, and `checks.py` names this command itself if the package
   is absent.
3. **Severity assignment, as a separate pass.** Once every criterion has been swept, go back and
   assign severity to every finding using the weighing order in
   `docs/reference/severity-scale.md` (impact, then frequency, then persistence) and this skill's
   own `references/severity-anchors.md`. Do not assign severity while still discovering problems;
   that inflates it.
4. **Rank and bound.** Order all findings by severity, then apply the output bound: every severity
   3 and 4 finding, plus at most five below that threshold, ranked. Count everything suppressed in
   `summary.suppressed_count`; nothing disappears without being counted.

This skill's registry carries 23 criteria: 15 scripted (`references/PLAIN.md`, `references/WILLIAMS.md`)
and 8 judged, matching the S-05 (skills-slate spec) expectation of a scripted-heavy lane balance for
clarity. `checks.scripted` covers readability mechanics detectable by fixed lexical or measurable
patterns (passive voice, nominalization density, sentence length, wordy phrases, and similar);
`checks.judged` covers audience fit, document organization, term consistency, main-idea ordering, and
Williams' passage-level cohesion, coherence, character-as-subject, and stress criteria, none of which
reduce to a fixed pattern without a judgment call. See `references/PLAIN.md` and
`references/WILLIAMS.md` for the full seven-column criterion registry (operationalization, operational
test, severity 2 and 3 anchors, lane, and lane rationale for every ID above).

## Output bounding

Report every severity 3 and 4 finding. Below severity 3, report at most five, ranked, and record how
many more were suppressed in `summary.suppressed_count`. Never omit a suppressed count to make the
output shorter. The scripted lane gets this for free from `skills/_shared/envelope.py`; a judged-lane
pass performed inline must apply it by hand.

## Clean-context critique

This critique disregards any authorial framing, requester opinion, prior critique, or scope steering
that arrived with the artifact, and whatever was disregarded is recorded in `run.stripped_context`.
"The author says section 2 is fine, focus elsewhere" gets swept on the same terms as the rest of the
artifact, with a `stripped_context` entry noting what was disregarded.

## Delegation

Where the subagent tool is available, delegate this critique to the `critique-critic` subagent,
passing only the artifact (path or inline content), this skill's name (`critique-clarity`), and,
if the caller supplied one, a severity-3 gate threshold. Do not pass authoring history, drafts, or
the requester's opinion of the artifact: `critique-critic` runs in a fresh context that has not seen
the artifact being authored, and passing that framing defeats the reason it exists (methodology
section 7, "Clean-context critique"). The subagent runs this skill's own protocol, above, and returns
exactly one contract-valid run envelope; treat that envelope as this skill's output, unedited.

Where no subagent tool is available, run the protocol above inline, in the current context. Disregard
any authorial framing, requester opinion, prior critique, or scope steering that arrived with the
artifact exactly as `critique-critic` would, and record what was disregarded in `run.stripped_context`.

## Bench domain module

This skill's bench corpus module is `bench/generator/domains/clarity.py`; see
`bench/generator/README.md` for what it must cover.
