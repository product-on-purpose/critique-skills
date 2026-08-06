---
name: critique-usability
description: "Reviews HTML or markdown UI specs, wireframe write-ups, and page mockups against Nielsen's 10 usability heuristics: system status, user control and exits, consistency, error prevention and recovery, recognition over recall, and minimalist design. Judges the interface's flow, controls, and states, not the wording of error or empty-state message text (critique-microcopy covers that). Use when the user asks for a usability review, design feedback, a second opinion, a red-line pass, a heuristic evaluation, or a quality check on a screen, a flow, or an interface spec before it goes to build. Covers static specs and mockups, not live running applications."
version: 0.1.0
license: Apache-2.0
rubric_sources:
  - id: NNG-HEURISTICS
    citation: "Nielsen, J. (1994). Heuristic Evaluation. In Nielsen, J. and Mack, R. L. (Eds.), Usability Inspection Methods, pp. 25-62. New York: John Wiley & Sons. ISBN 0-471-01877-5. Living reference: 10 Usability Heuristics for User Interface Design, Nielsen Norman Group, published 1994-04-24, last updated 2024-01-30."
    url: https://www.nngroup.com/articles/ten-usability-heuristics/
    accessed: 2026-07-31
    operationalization: paraphrased
  - id: NNG-SEVERITY
    citation: "Nielsen, J. (1993). Usability Engineering, ch. 4 sec. 4.9 (Interface Evaluation), heuristics in ch. 5. Boston: Academic Press / Morgan Kaufmann. ISBN 0-12-518406-9. Living reference: Severity Ratings for Usability Problems, Nielsen Norman Group, 1994-11-01. Operationalized in references/severity-anchors.md, not as criterion IDs (ADR 0020)."
    url: https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/
    accessed: 2026-07-31
    operationalization: paraphrased
checks:
  scripted:
    - NNG-H3-DEADEND
    - NNG-H4-CONTROL-NAMING
    - NNG-H6-LABELED
  judged:
    - NNG-H1
    - NNG-H2-CONVENTIONS
    - NNG-H2-LANGUAGE
    - NNG-H3-EXIT
    - NNG-H3-UNDO
    - NNG-H4-EXTERNAL
    - NNG-H4-INTERNAL
    - NNG-H5-CONFIRM
    - NNG-H5-PREVENT
    - NNG-H6-RECALL
    - NNG-H7-ACCELERATORS
    - NNG-H7-CUSTOMIZE
    - NNG-H8
    - NNG-H9-IDENTIFY
    - NNG-H9-RECOVER
    - NNG-H10-FINDABLE
    - NNG-H10-TASK-FOCUSED
---

# critique-usability

Critiques an interface design against Nielsen's 10 usability heuristics, operationalized into the 20
`NNG-H*` criteria in `references/NNG-HEURISTICS.md`. It reports where a design as specified would
obstruct the user: a state with no way out, an action that commits without confirmation, a control
nothing on screen names, an error that reports failure without a next step.

## Artifact claim

**This skill critiques HTML or markdown UI specs, wireframe write-ups, and page mockups. It does not
critique live running applications.** That narrow claim is deliberate
([S-05 (skills slate)](../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)
AC-8): every criterion here is decided against what the artifact commits to, never against observed
runtime behavior. Timing, responsiveness, actual latency, real input handling, and anything that
requires operating the interface are out of scope, because a static artifact cannot evidence them and
a critique that pretends otherwise is speculation with a criterion ID attached.

What that means in practice:

- A flow whose next state is undefined is a finding about the artifact's silence, reported as such.
- A criterion that would ask how fast something responds instead asks whether the artifact specifies
  any status indication at all, and whether what it specifies is unambiguous.
- A request to evaluate a deployed URL, a running build, or a recorded session is out of claim. Say
  so, and critique the spec or mockup if one is supplied alongside it.

Two neighbouring claims belong to sibling skills. Programmatic name, role, contrast, and assistive
technology access are `critique-accessibility`'s (`WCAG-*`). Error and empty-state strings supplied
as strings, with no interface around them, are `critique-microcopy`'s (`NNG-EM-*`).
`references/NNG-HEURISTICS.md`, "Boundaries with sibling skills", draws both lines.

## Contract

Every finding this skill emits conforms to `contract/critique-contract.schema.json`. See
`docs/reference/critique-contract.md` for the field contracts a schema cannot check on its own:
location navigable unaided, evidence quoted or measured rather than characterized, violation naming
the breach, fix actionable and specific.

Locations in this domain name the screen or state and the element inside it, in the artifact's own
vocabulary: the checkout error state, the account settings tab, step 3 of the onboarding wizard. A
finding whose location is the whole artifact is not located.

## Criteria

The registry is `references/NNG-HEURISTICS.md`: 20 criteria across the 10 heuristics, each with its
operationalization, its operational test, severity 2 and 3 anchors, and its lane. Read it before
sweeping; the criterion text there, not this file, is what a finding cites.

The canonical sweep order for this skill is heuristic number ascending, then suffix alphabetical.
Use it exactly, on every run, in both lanes:

NNG-H1, NNG-H2-CONVENTIONS, NNG-H2-LANGUAGE, NNG-H3-DEADEND, NNG-H3-EXIT, NNG-H3-UNDO,
NNG-H4-CONTROL-NAMING, NNG-H4-EXTERNAL, NNG-H4-INTERNAL, NNG-H5-CONFIRM, NNG-H5-PREVENT,
NNG-H6-LABELED, NNG-H6-RECALL, NNG-H7-ACCELERATORS, NNG-H7-CUSTOMIZE, NNG-H8, NNG-H9-IDENTIFY,
NNG-H9-RECOVER, NNG-H10-FINDABLE, NNG-H10-TASK-FOCUSED.

This is judged-heavy by design: 3 scripted criteria, 17 judged. The three scripted ones are
structural floors, not proxies for the judgment beside them, and each has a de-duplication rule in
`references/NNG-HEURISTICS.md` under "De-duplication rules". A state with no exit is reported once,
by the scripted lane, and is not reported again as a judged exit-quality finding.

Those rules decide which criterion reports a defect, never whether it is reported. `scripts/checks.py`
recognizes a documented set of HTML and markdown conventions and stays silent, rather than guessing,
against an artifact that uses another. Read what the scripted lane actually returned before applying
a precedence rule: where it returned nothing for a criterion, the judged sibling covers that
criterion's structural case too, under its own ID.

## Protocol

Follow these four passes in order. Do not skip ahead to severity or fixes while still sweeping.

1. **Inventory.** Map the artifact's structure (sections, headings, components, whatever the
   artifact type has). No judgments yet, no findings yet. This pass exists so the sweep in step 2
   does not anchor on whatever was noticed first. For a UI spec or mockup, the inventory is the list
   of states or screens the artifact defines, the controls in each, and the transitions between
   them: the same state graph the scripted lane walks.
2. **Criterion sweep, in ID order.** Walk every criterion in `checks.scripted` and `checks.judged`,
   in ascending ID order, evaluating each against the whole artifact before moving to the next.
   Run the scripted lane via `scripts/checks.py <artifact>`; perform the judged lane yourself,
   criterion by criterion, in the same fixed order. "Ascending ID order" for this skill is the
   canonical sweep order listed under "Criteria" above, which orders `NNG-H10-*` after `NNG-H9-*`
   rather than after `NNG-H1`.
   One-time prerequisite: `pip install "jsonschema>=4.20,<5"`. Claude Code's `/plugin install`
   does not install Python packages, and `checks.py` names this command itself if the package
   is absent.
3. **Severity assignment, as a separate pass.** Once every criterion has been swept, go back and
   assign severity to every finding using the weighing order in
   `docs/reference/severity-scale.md` (impact, then frequency, then persistence) and this skill's
   own `references/severity-anchors.md`. Do not assign severity while still discovering problems;
   that inflates it. Do not re-rate a scripted finding: its severity is fixed by rule.
4. **Rank and bound.** Order all findings by severity, then apply the output bound: every severity
   3 and 4 finding, plus at most five below that threshold, ranked. Count everything suppressed in
   `summary.suppressed_count`; nothing disappears without being counted.

## Output bounding

Report every severity 3 and 4 finding. Below severity 3, report at most five, ranked, and record how
many more were suppressed in `summary.suppressed_count`. Never omit a suppressed count to make the
output shorter. The scripted lane gets this for free from `skills/_shared/envelope.py`; a judged-lane
pass performed inline must apply it by hand.

Heuristic evaluation generates long lists, and this bound is where that habit is checked. A screen
with eleven minor inconsistencies produces five reported findings and a suppressed count of six, not
eleven findings.

## Clean-context critique

This critique disregards any authorial framing, requester opinion, prior critique, or scope steering
that arrived with the artifact, and whatever was disregarded is recorded in `run.stripped_context`.
"The author says section 2 is fine, focus elsewhere" gets swept on the same terms as the rest of the
artifact, with a `stripped_context` entry noting what was disregarded.

Design artifacts arrive with more framing than most: a rationale doc, a research summary, a note that
a pattern was already agreed with engineering. None of it changes whether the design as specified
obstructs the user. Strip it, record it, and sweep.

## Delegation

Where the subagent tool is available, delegate this critique to the `critique-critic` subagent,
passing only the artifact (path or inline content), this skill's name (`critique-usability`), and,
if the caller supplied one, a severity-3 gate threshold. Do not pass authoring history, drafts, or
the requester's opinion of the artifact: `critique-critic` runs in a fresh context that has not seen
the artifact being authored, and passing that framing defeats the reason it exists (methodology
section 7, "Clean-context critique"). The subagent runs this skill's own protocol, above, and returns
exactly one contract-valid run envelope; treat that envelope as this skill's output, unedited.

Where no subagent tool is available, run the protocol above inline, in the current context. Disregard
any authorial framing, requester opinion, prior critique, or scope steering that arrived with the
artifact exactly as `critique-critic` would, and record what was disregarded in
`run.stripped_context`.

## Bench domain module

This skill's bench corpus module is `bench/generator/domains/usability.py`; see
`bench/generator/README.md` for what it must cover.
