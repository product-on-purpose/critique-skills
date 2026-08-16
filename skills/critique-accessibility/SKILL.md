---
name: critique-accessibility
description: "Reviews HTML pages and fragments (markdown where mappable) against WCAG 2.2 AA: contrast, alt text, heading hierarchy for screen readers, link text, and keyboard and screen-reader access. Judges conformance against WCAG, not an interface's general usability, flow, or controls (critique-usability covers that). Use when the user asks for an accessibility review, feedback, a second opinion, a red-line pass, an a11y audit, or a pre-launch quality check on a page or component."
version: 0.1.1
license: Apache-2.0
rubric_sources:
  - id: WCAG
    citation: "WCAG 2.2 (W3C Recommendation), https://www.w3.org/TR/WCAG22/"
    url: https://www.w3.org/TR/WCAG22/
    accessed: 2026-07-31
    operationalization: open-standard
checks:
  scripted:
    - WCAG-1.1.1
    - WCAG-1.3.1
    - WCAG-1.4.3
    - WCAG-1.4.4
    - WCAG-1.4.10
    - WCAG-1.4.11
    - WCAG-1.4.12
    - WCAG-2.4.1
    - WCAG-2.4.2
    - WCAG-2.4.4
    - WCAG-2.5.3
    - WCAG-3.1.1
    - WCAG-3.3.2
  judged:
    - WCAG-1.3.2
    - WCAG-1.3.3
    - WCAG-1.4.1
    - WCAG-2.4.3
    - WCAG-2.4.5
    - WCAG-2.4.6
    - WCAG-3.1.2
    - WCAG-3.3.1
    - WCAG-4.1.2
---

# critique-accessibility

Reviews an HTML page or fragment (markdown where its structure maps cleanly to HTML, such as headings,
links, and images) against WCAG 2.2 AA, covering both success-criterion levels A and AA required for
AA conformance. The artifact claim is narrow and static: this skill evaluates markup and declared CSS
as text, never a rendered page, a running application, or live keyboard and pointer interaction. Four
WCAG 2.2 success criteria that require observing a page respond to input over time (No Keyboard Trap,
Timing Adjustable, Pointer Gestures, Dragging Movements) are out of this skill's reach for that reason
and are not in its registry; see `references/WCAG.md`, "Scope", for the full boundary and reasoning.

## Contract

Every finding this skill emits conforms to `contract/critique-contract.schema.json`. See
`docs/reference/critique-contract.md` for the field contracts a schema cannot check on its own:
location navigable unaided, evidence quoted or measured rather than characterized, violation naming
the breach, fix actionable and specific.

## Naming a location

A finding names the element it is about, not the region the element sits in. For an HTML artifact,
in this order of preference:

1. **The element's `id`, written as a `#hero-image` token**, whenever the markup carries one. This
   is the first choice every time, and generated or hand-written markup usually carries ids.
2. **A CSS selector in double quotes** for an element with no id: `"main > section:nth-of-type(2) >
   p"`. Keep it to tag, `#id`, `.class`, descendant, child, and `:nth-of-type`. The double quotes
   are part of the rule, not decoration: a bare `div.wizard-steps` dropped into a sentence reads as
   prose, and a reader following it by hand has to guess which one was meant.
   One-time prerequisite: `pip install "jsonschema>=4.20,<5"`. Claude Code's `/plugin install`
   does not install Python packages, and `checks.py` names this command itself if the package
   is absent.
3. **The element's own text in double quotes**, at least eight characters and unique on the page,
   when the markup offers neither of the above: `"Reset your password"`.

Then say what kind of element it is, and anything else that helps a person get there:
`#s3-form-submit, <button> control, visible label 'Submit', line 68`.

A line number on its own is not a location, and neither is a section title, a class name mentioned
in prose, nor a phrase like "the wizard near the top of the schedule section". Each describes a
neighbourhood and leaves the reader to find the element inside it. `scripts/checks.py` emits
locations in exactly the form above; a judged-lane finding written by hand is held to the same
rule, because a reader cannot tell which lane a finding came from and should not have to.

## Protocol

Follow these four passes in order. Do not skip ahead to severity or fixes while still sweeping.

1. **Inventory.** Map the artifact's structure (sections, headings, components, whatever the
   artifact type has). No judgments yet, no findings yet. This pass exists so the sweep in step 2
   does not anchor on whatever was noticed first. Record each element's `id` while mapping: the
   sweep needs it to name locations, and recovering it afterwards is where locations decay into
   line numbers and section titles.
2. **Criterion sweep, in ID order.** Walk every criterion in `checks.scripted` and `checks.judged`,
   in ascending ID order, evaluating each against the whole artifact before moving to the next.
   Run the scripted lane via `scripts/checks.py <artifact>`; perform the judged lane yourself,
   criterion by criterion, in the same fixed order.

   Sweep each judged criterion against every element it governs, not against the first one that
   looks wrong: every custom control for WCAG-4.1.2, every label, state marker, and error message
   for WCAG-1.4.1 and WCAG-3.3.1, every sequence whose order carries meaning for WCAG-1.3.2, every
   heading and label for WCAG-2.4.6. Name the element you are judging, by `id`, as you judge it. A
   criterion with nothing to report has still been swept; a criterion is never skipped because the
   scripted lane already reported something nearby, and the scripted lane's silence on a judged
   criterion means only that no script was asked to look.
3. **Severity assignment, as a separate pass.** Once every criterion has been swept, go back and
   assign severity to every finding using the weighing order in
   `docs/reference/severity-scale.md` (impact, then frequency, then persistence) and this skill's
   own `references/severity-anchors.md`. Do not assign severity while still discovering problems;
   that inflates it.
4. **Assemble the envelope. Do not do this pass by hand.** Write every finding from both lanes to
   one JSON file, then hand that file to the library's own assembler. Two steps, in this order:

   ```
   # 1. Write the combined pool. Use an ABSOLUTE path; you are about to change directory.
   cat > /absolute/path/to/findings.json << 'EOF'
   {"findings": [ ...every finding from both lanes... ]}
   EOF

   # 2. Assemble, from this skill's directory, exactly as you ran scripts/checks.py in pass 2.
   python3 scripts/merge.py --artifact <the SAME artifact path you gave checks.py> --findings /absolute/path/to/findings.json
   ```

   It ranks by severity, applies the output bound (every severity 3 and 4 finding, plus at most
   five below that threshold), assigns `F-NNN` ids after ranking, counts everything suppressed into
   `summary.suppressed_count` so nothing disappears uncounted, builds `summary.by_severity` over
   **everything found** rather than only what survived bounding, computes the gate, normalises
   prose to the contract's rules, and validates before printing.

   `scripts/merge.py` sits beside `scripts/checks.py` and is run the same way, from the same
   directory, so if pass 2 worked then this works. It knows its own skill name from its own
   location, so there is no `--skill` to get wrong. Use the same artifact path you gave
   `checks.py`. Add `--severity-3-threshold N` if a threshold was supplied.

   **If it fails, say so and stop.** Report the command and its error as your final message.
   Never substitute a prose write-up of the findings: the output contract is one envelope or
   nothing, and a readable summary that is not an envelope looks like success to everything
   downstream while being unusable by it.

   Return its output verbatim. It prints nothing at all rather than print an invalid envelope, so
   if you have output you have a valid one, and editing it afterwards makes it unvalidated again.
   Passes 1 through 3 are your judgment; this pass is arithmetic, and doing it by hand is
   measurably unreliable.

## Output bounding

Report every severity 3 and 4 finding. Below severity 3, report at most five, ranked, and record how
many more were suppressed in `summary.suppressed_count`. Never omit a suppressed count to make the
output shorter. The scripted lane gets this for free from `skills/_shared/envelope.py`, and a judged-lane pass
gets it from `skills/_shared/merge.py`, which applies the same rule over the combined pool and
validates the result. Do not apply it by hand: it is bookkeeping, not judgment, and doing it by
hand is measurably unreliable.

## Clean-context critique

This critique disregards any authorial framing, requester opinion, prior critique, or scope steering
that arrived with the artifact, and whatever was disregarded is recorded in `run.stripped_context`.
"The client signed off on the contrast already, just check the headings" gets swept on the same terms
as the rest of the artifact, with a `stripped_context` entry noting what was disregarded.

## Delegation

Where the subagent tool is available, delegate this critique to the `critique-critic` subagent,
passing the artifact (path or inline content), this skill's name (`critique-accessibility`), the absolute path
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

This skill's bench corpus module is `bench/generator/domains/accessibility.py`; see
`bench/generator/README.md` for what it must cover.
