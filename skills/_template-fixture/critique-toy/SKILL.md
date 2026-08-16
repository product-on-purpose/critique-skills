---
name: critique-toy
description: "Reviews short markdown field-operations notices, memos, and similar prose documents against the toy TOY-* grammar, covering a passive-voice recast that deletes the actor, a hedging phrase stacked ahead of an otherwise direct statement, and a subheading left with no body before the next heading of equal or higher level. Use when the user asks for a review, feedback, a second opinion, a red-line pass, or a quality check on one of this fixture's worked-example documents. This is the skill template's own committed fixture, not a shipped critique-family skill, and it is never registered in library.json."
version: 0.1.0
license: Apache-2.0
rubric_sources:
  - id: TOY
    citation: "Internal fixture rubric: the toy domain criteria defined in bench/generator/README.md, Worked example: the toy domain. Not a published external source."
    url: null
    accessed: 2026-07-31
    operationalization: paraphrased
checks:
  scripted:
    - TOY-ACTIVE
    - TOY-HEDGE
    - TOY-ORPHAN
  judged: []
---

# critique-toy

Reviews a markdown-prose artifact composed in the toy domain's own grammar (`bench/generator/README.md`,
"Worked example: the toy domain") against its three TOY-* criteria: a passive-voice recast that deletes
the actor (TOY-ACTIVE), a hedging phrase stacked ahead of an otherwise direct statement (TOY-HEDGE), and
a subheading left with no body before the next heading of equal or higher level (TOY-ORPHAN). This skill
is `docs/internal/skill-template.md`'s own committed fixture: it exists to prove the template builds end
to end (S-04 spec, Behavior/Examples), not as a seventh launch skill. It lives under
`skills/_template-fixture/` rather than directly under `skills/` precisely so it is never discovered as
a shipped component, and it is never registered in `library.json`.

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
3. **Severity assignment, as a separate pass.** Once every criterion has been swept, go back and
   assign severity to every finding using the weighing order in
   `docs/reference/severity-scale.md` (impact, then frequency, then persistence) and this skill's
   own `references/severity-anchors.md`. Do not assign severity while still discovering problems;
   that inflates it.
4. **Rank and bound.** Order all findings by severity, then apply the output bound: every severity
   3 and 4 finding, plus at most five below that threshold, ranked. Count everything suppressed in
   `summary.suppressed_count`; nothing disappears without being counted.

This skill's `checks.judged` list is empty (`judged: []`). Every TOY-* criterion the toy domain defines
(TOY-ACTIVE, TOY-HEDGE, TOY-ORPHAN) is deterministically checkable by a fixed pattern, matching this
template's own "Scripted lane discipline" guidance, so step 2's judged sweep has nothing to evaluate for
this fixture. A real critique-family skill is not expected to look like this: an all-scripted rubric is
what makes the toy domain a useful harness fixture and a poor model of a shipped skill's lane split.

## Output bounding

Report every severity 3 and 4 finding. Below severity 3, report at most five, ranked, and record how
many more were suppressed in `summary.suppressed_count`. Never omit a suppressed count to make the
output shorter. The scripted lane gets this for free from `skills/_shared/envelope.py`.

## Clean-context critique

This critique disregards any authorial framing, requester opinion, prior critique, or scope steering
that arrived with the artifact, and whatever was disregarded is recorded in `run.stripped_context`.
"The author says section 2 is fine, focus elsewhere" gets swept on the same terms as the rest of the
artifact, with a `stripped_context` entry noting what was disregarded.

## Delegation

Where the subagent tool is available, delegate this critique to the `critique-critic` subagent,
passing the artifact (path or inline content), this skill's name (`critique-toy`), the absolute path
of this skill's own directory, and, if the caller supplied one, a severity-3 gate threshold.
Pass nothing else. Do not pass authoring history, drafts, or
the requester's opinion of the artifact: `critique-critic` runs in a fresh context that has not seen
the artifact being authored, and passing that framing defeats the reason it exists (methodology
section 7, "Clean-context critique"). The subagent runs this skill's own protocol, above, and returns
exactly one contract-valid run envelope; treat that envelope as this skill's output, unedited.

**The skill directory is not optional.** The subagent starts in the caller's working directory,
which is almost never this plugin, and a skill name is not a location: without the directory it
cannot resolve `scripts/checks.py` or `scripts/merge.py`. Pass the "Base directory for this skill"
this invocation was given. Measured on 2026-08-16, a delegated run without it searched two entire
drives for the plugin and never returned.

Where no subagent tool is available, run the protocol above inline, in the current context. Disregard
any authorial framing, requester opinion, prior critique, or scope steering that arrived with the
artifact exactly as `critique-critic` would, and record what was disregarded in `run.stripped_context`.

## Bench domain module

This skill's bench corpus module is `bench/generator/domains/toy.py`; see `bench/generator/README.md`
for what it must cover.
