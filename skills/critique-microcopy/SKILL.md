---
name: critique-microcopy
description: "Reviews error messages, empty states, and other short microcopy strings, including screens annotated with placement, container, timing, and behavior context, against NN/g's error-message guidelines: plain language, specificity, constructive next steps, neutral tone, and recovery grace. Use when the user asks for a review, feedback, a second opinion, a red-line pass, or a quality check on error copy, empty-state copy, form validation messages, or other short UI text before it ships."
version: 0.1.0
license: Apache-2.0
rubric_sources:
  - id: NNG-EM
    citation: "Neusesser, T. and Sunwall, E. (2023). Error-Message Guidelines. Nielsen Norman Group. Published May 14, 2023."
    url: https://www.nngroup.com/articles/error-message-guidelines/
    accessed: 2026-07-31
    operationalization: paraphrased
checks:
  scripted:
    - NNG-EM-NOT-COLOR-ONLY
    - NNG-EM-TIMING
    - NNG-EM-PLAIN-LANGUAGE
    - NNG-EM-CONSTRUCTIVE
    - NNG-EM-NEUTRAL-TONE
    - NNG-EM-PRESERVE-INPUT
  judged:
    - NNG-EM-PROXIMITY
    - NNG-EM-SALIENT
    - NNG-EM-SEVERITY-CONTAINER
    - NNG-EM-PREVENT
    - NNG-EM-SELECTABLE-FIX
    - NNG-EM-EXPLAIN
    - NNG-EM-GRACE
    - NNG-EM-SPECIFIC
---

# critique-microcopy

Reviews error messages, empty states, and other short user-facing microcopy strings against NN/g's
error-message guidelines, operationalized into the 14 `NNG-EM-*` criteria in
`references/NNG-EM.md`: where and how prominently a message appears, what it says, how much work it
leaves the reader, and whether a total failure still leaves some goodwill.

**Narrow artifact claim.** This skill's artifact format is annotated screens described in text,
placement, container, timing, and behavior notated alongside each message, per
[ADR 0018 (microcopy artifact format)](../../docs/internal/decisions/0018-microcopy-artifact-format-annotated-context.md),
which chose that format over a bare string list precisely because eight of the fourteen criteria have
nothing to read without it. A bare list of strings is still accepted as degraded input, at the
coverage cost pass 2 below states; it is not the format this skill is measured on. Either way, this
skill does not critique live applications or rendered screenshots: a screen's context arrives as
structured text annotation, never as an image, and "the button looked wrong" is out of scope because
nothing in the artifact states what the button looked like. See `references/NNG-EM.md`, "Artifact
format", for the exact annotation grammar.

## Contract

Every finding this skill emits conforms to `contract/critique-contract.schema.json`. See
`docs/reference/critique-contract.md` for the field contracts a schema cannot check on its own:
location navigable unaided, evidence quoted or measured rather than characterized, violation naming
the breach, fix actionable and specific.

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

For a bare-string-list artifact, the eight criteria that read an annotation field, `NNG-EM-NOT-COLOR-ONLY`,
`NNG-EM-PRESERVE-INPUT`, `NNG-EM-PREVENT`, `NNG-EM-PROXIMITY`, `NNG-EM-SALIENT`,
`NNG-EM-SELECTABLE-FIX`, `NNG-EM-SEVERITY-CONTAINER`, and `NNG-EM-TIMING`, have nothing to evaluate
and produce no findings. The six that read the `Message` text alone, `NNG-EM-CONSTRUCTIVE`,
`NNG-EM-EXPLAIN`, `NNG-EM-GRACE`, `NNG-EM-NEUTRAL-TONE`, `NNG-EM-PLAIN-LANGUAGE`, and
`NNG-EM-SPECIFIC`, still run in full. Say so in the prose accompanying the envelope, naming the eight,
so a reader knows the sweep was partial and why. Do **not** record it in `run.stripped_context`: that
field is the clean-context ledger for framing that arrived with the artifact and was disregarded
(methodology section 7; schema `$defs/strippedContext`), and an entry there asserts a strip that did
not happen. An artifact that carries no annotation had nothing stripped from it.

## Output bounding

Report every severity 3 and 4 finding. Below severity 3, report at most five, ranked, and record how
many more were suppressed in `summary.suppressed_count`. Never omit a suppressed count to make the
output shorter. The scripted lane gets this for free from `skills/_shared/envelope.py`; a judged-lane
pass performed inline must apply it by hand.

## Clean-context critique

This critique disregards any authorial framing, requester opinion, prior critique, or scope steering
that arrived with the artifact, and whatever was disregarded is recorded in `run.stripped_context`.
"The author says the payment-failure message is fine, focus on the signup form" gets swept on the
same terms as the rest of the artifact, with a `stripped_context` entry noting what was disregarded.

## Delegation

Where the subagent tool is available, delegate this critique to the `critique-critic` subagent,
passing only the artifact (path or inline content), this skill's name (`critique-microcopy`), and,
if the caller supplied one, a severity-3 gate threshold. Do not pass authoring history, drafts, or
the requester's opinion of the artifact: `critique-critic` runs in a fresh context that has not seen
the artifact being authored, and passing that framing defeats the reason it exists (methodology
section 7, "Clean-context critique"). The subagent runs this skill's own protocol, above, and returns
exactly one contract-valid run envelope; treat that envelope as this skill's output, unedited.

Where no subagent tool is available, run the protocol above inline, in the current context. Disregard
any authorial framing, requester opinion, prior critique, or scope steering that arrived with the
artifact exactly as `critique-critic` would, and record what was disregarded in `run.stripped_context`.

## Bench domain module

This skill's bench corpus module is `bench/generator/domains/microcopy.py`; see
`bench/generator/README.md` for what it must cover, and
[ADR 0018](../../docs/internal/decisions/0018-microcopy-artifact-format-annotated-context.md) for the
annotation grammar it must compose artifacts in.
