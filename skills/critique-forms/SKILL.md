---
name: critique-forms
description: "Reviews HTML forms for how easy they are to complete, especially on a phone: input types and mobile keyboards, autofill tokens, field widths, required and optional marking, password rules, button labels, and layout, against convergent research from Baymard, GOV.UK, web.dev, NN/g and others. Judges the cost of filling the form in, not WCAG conformance (critique-accessibility covers that), a whole interface's flow against Nielsen's heuristics (critique-usability covers that), or the wording of error messages (critique-microcopy covers that). Use when the user asks for a form review, feedback, a second opinion, a red-line pass, or a quality check on a sign-up, sign-in, contact, profile, or address form."
metadata:
  version: 0.1.0
license: Apache-2.0
rubric_sources:
  - id: BAYMARD
    citation: "Baymard Institute: form and checkout usability articles, benchmarks and the Touch Keyboard Types cheat sheet, 2010 to 2026. Article-level handles in references/FORMS.md."
    url: https://baymard.com/
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: GOOGLE
    citation: "Google: web.dev form guides (Dutton 2020; Nalpas 2021 and 2024), Chrome for Developers (Nalpas 2024), and The Keyword (Khurana 2024)."
    url: https://web.dev/
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: GOVUK
    citation: "GOV.UK Design System patterns and components, and Government Digital Service blog posts, 2015 to 2026."
    url: https://design-system.service.gov.uk/
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: WHATWG
    citation: "WHATWG HTML Living Standard, section 4.10.18.7, Autofill."
    url: https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#autofill
    accessed: 2026-09-25
    operationalization: open-standard
  - id: NNGROUP
    citation: "Nielsen Norman Group articles on form design (Budiu 2015 and 2019, Whitenton 2016, Li 2017, Sherwin 2018)."
    url: https://www.nngroup.com/
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: ZUKO
    citation: "Zuko Analytics form-analytics datasets and articles, including autofill and password-field abandonment data."
    url: https://www.zuko.io/
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: WROBLEWSKI
    citation: "Wroblewski, L. (2008). Web Form Design: Filling in the Blanks. Rosenfeld Media. ISBN 978-1-933820-25-5. Also his lukew.com articles, 2007 and 2010."
    url: https://www.lukew.com/
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: SILVER
    citation: "Silver, A. (2018). Form Design Patterns. Smashing Media. ISBN 978-3-945749-73-9."
    url: null
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: ALHARBI
    citation: "Alharbi, O., Stuerzlinger, W. and Putze, F. (2020). The Effects of Predictive Features of Mobile Keyboards on Text Entry Speed and Errors. Proceedings of the ACM on Human-Computer Interaction 4 (ISS), Article 183."
    url: https://vvise.iat.sfu.ca/user/data/papers/autocorrectfrustration.pdf
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: PENZO
    citation: "Penzo, M. (2006). Label Placement in Forms. UXmatters."
    url: https://www.uxmatters.com/mt/archives/2006/07/label-placement-in-forms.php
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: SPEERO
    citation: "Labay, B. (2016). Should You Use Single or Multi-Column Forms? Speero, formerly CXL Institute."
    url: https://speero.com/post/form-field-usability-should-you-use-single-or-multi-column-forms-original-research
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: HUBSPOT
    citation: "Vaughan, P. (2023). Disproving Best Practices: The One- vs. Two-Column Form Test. HubSpot Blog."
    url: https://blog.hubspot.com/marketing/one-vs-two-column-form-conversion-test
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: CXL
    citation: "Birkett, A. (2022). Form Design Principles: 13 Empirically Backed Best Practices. CXL."
    url: https://cxl.com/blog/form-design-best-practices/
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: VENTUREHARBOUR
    citation: "Taylor, M. (2016). 58 Form Design and UX Best Practices. Venture Harbour."
    url: https://ventureharbour.com/form-design-best-practices/
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: PASCHAL
    citation: "Paschal, A. (2023). Design a better form. Medium, Design Bootcamp."
    url: https://medium.com/design-bootcamp/design-a-better-form-b9adaa372fb3
    accessed: 2026-09-25
    operationalization: paraphrased
  - id: DESIGNLAB
    citation: "Team Designlab (2019). Form UI Design: A UX/UI Guide to Designing User-Friendly Forms. Designlab."
    url: https://designlab.com/blog/form-ui-design-best-practices
    accessed: 2026-09-25
    operationalization: paraphrased
checks:
  scripted:
    - FORMS-ACTION-LABEL
    - FORMS-ADDRESS-FORMAT
    - FORMS-AUTOCOMPLETE
    - FORMS-AUTOCORRECT
    - FORMS-CONFIRM-PASSWORD
    - FORMS-DATE-SELECTS
    - FORMS-FIELD-WIDTH
    - FORMS-FORMAT-TOLERANCE
    - FORMS-INPUT-FONT-SIZE
    - FORMS-INPUT-TYPE
    - FORMS-NUMERIC-INPUTMODE
    - FORMS-OPTION-CONTROL
    - FORMS-PASSWORD-RULES
    - FORMS-PHONE-REASON
    - FORMS-PLACEHOLDER-INSTRUCTION
    - FORMS-REQUIRED-OPTIONAL
    - FORMS-RESET-BUTTON
    - FORMS-SPLIT-ENTITY
  judged:
    - FORMS-ACTION-HIERARCHY
    - FORMS-FIELD-NECESSITY
    - FORMS-LABEL-POSITION
    - FORMS-SELECTION-DEPENDENT
    - FORMS-SINGLE-COLUMN
    - FORMS-TOUCH-TARGET
---

# critique-forms

Reviews an HTML form, or a page or fragment containing one, for how easy it is to complete,
especially on a phone. The rubric is `FORMS`, which this library synthesized from the rules that
several form-design publishers state independently: Baymard Institute, GOV.UK, Google's web.dev,
Nielsen Norman Group, Luke Wroblewski, Adam Silver and others, with the HTML standard for autofill.
Each criterion's row in `references/FORMS.md` names the sources behind it and grades their evidence.
The artifact claim is narrow and static: this skill evaluates markup and declared CSS as text, never
a rendered page, a running script, or a live interaction.

## Contract

Every finding this skill emits conforms to `contract/critique-contract.schema.json`. See
`docs/reference/critique-contract.md` for the field contracts a schema cannot check on its own:
location navigable unaided, evidence quoted or measured rather than characterized, violation naming
the breach, fix actionable and specific.

## Scope

Forms borders three sibling skills, and it does not test their ground. Label presence, error text,
recovery after an error, validation timing, preventing a wrong entry by constraint, consistent action
naming across a flow, `fieldset` and `legend` grouping, and colour as the only signal all belong to
`critique-accessibility`, `critique-usability` or `critique-microcopy`. `references/FORMS.md`,
"Ground other skills own", lists each one and its owner. A form that lacks a label gets no forms
finding for it, even though the defect is real; the owning skill reports it.

Two criteria overlap `critique-accessibility` deliberately. `FORMS-AUTOCOMPLETE` grades the same
attribute as WCAG 1.3.5 by its effect on autofill, and `FORMS-TOUCH-TARGET` tests a larger target
size than WCAG 2.5.8's conformance floor. Report them on forms' terms, as their rows state.

## Naming a location

A finding names the element it is about, not the region the element sits in. For an HTML artifact,
in this order of preference:

1. **The element's `id`, written as a `#email` token**, whenever the markup carries one. This is the
   first choice every time, and form markup usually carries ids.
2. **A CSS selector in double quotes** for an element with no id: `"form > fieldset:nth-of-type(2) >
   input"`. Keep it to tag, `#id`, `.class`, descendant, child, and `:nth-of-type`. The double
   quotes are part of the rule, not decoration: a bare `div.actions` dropped into a sentence reads as
   prose, and a reader following it by hand has to guess which one was meant.
3. **The element's own text in double quotes**, at least eight characters and unique on the page,
   when the markup offers neither of the above: `"Create your account"`.

Then say what kind of element it is, and anything else that helps a person get there:
`#signup-email, <input> field, label 'Email address', line 42`.

A line number on its own is not a location, and neither is a section title, a class name mentioned
in prose, nor a phrase like "the address fields near the bottom". Each describes a neighbourhood and
leaves the reader to find the element inside it. `scripts/checks.py` emits locations in exactly the
form above; a judged-lane finding written by hand is held to the same rule, because a reader cannot
tell which lane a finding came from and should not have to.

## Protocol

Follow these four passes in order. Do not skip ahead to severity or fixes while still sweeping.

1. **Inventory.** Map the artifact's structure: each form, its fields in document order with their
   labels, hints and `required` state, its choices that reveal other fields, and its actions. No
   judgments yet, no findings yet. This pass exists so the sweep in step 2 does not anchor on
   whatever was noticed first. Record each element's `id` while mapping: the sweep needs it to name
   locations, and recovering it afterwards is where locations decay into line numbers.
2. **Criterion sweep, in ID order.** Walk every criterion in `checks.scripted` and `checks.judged`,
   in ascending ID order, evaluating each against the whole artifact before moving to the next.
   Run the scripted lane via `scripts/checks.py <artifact>`; perform the judged lane yourself,
   criterion by criterion, in the same fixed order.
   One-time prerequisite: `pip install "jsonschema>=4.20,<5"`. Claude Code's `/plugin install`
   does not install Python packages, and `checks.py` names this command itself if the package
   is absent.

   Sweep each judged criterion against every element it governs, not against the first one that
   looks wrong: every action for `FORMS-ACTION-HIERARCHY`, every field for
   `FORMS-FIELD-NECESSITY`, every label for `FORMS-LABEL-POSITION`, every choice that reveals other
   fields for `FORMS-SELECTION-DEPENDENT`, every row holding more than one field for
   `FORMS-SINGLE-COLUMN`, and every tappable control for `FORMS-TOUCH-TARGET`. Apply each
   criterion's operational test from `references/FORMS.md` as written. A criterion with nothing to
   report has still been swept, and the scripted lane's silence on a judged criterion means only
   that no script was asked to look.
3. **Severity assignment, as a separate pass.** Once every criterion has been swept, go back and
   assign severity to every finding using the weighing order in
   `docs/reference/severity-scale.md` (impact, then frequency, then persistence) and this skill's
   own `references/severity-anchors.md`. Do not assign severity while still discovering problems;
   that inflates it. A `FORMS-SINGLE-COLUMN` finding never exceeds severity 2.
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
output shorter. The scripted lane gets this for free from `skills/_shared/envelope.py`, and a
judged-lane pass gets it from `skills/_shared/merge.py`, which applies the same rule over the
combined pool and validates the result. Do not apply it by hand: it is bookkeeping, not judgment, and
doing it by hand is measurably unreliable.

## Clean-context critique

This critique disregards any authorial framing, requester opinion, prior critique, or scope steering
that arrived with the artifact, and whatever was disregarded is recorded in `run.stripped_context`.
"We already tested this sign-up form with users, just check the password field" gets swept on the
same terms as the rest of the artifact, with a `stripped_context` entry noting what was disregarded.

## Delegation

Where the subagent tool is available, delegate this critique to the `critique-critic` subagent,
passing the artifact (path or inline content), this skill's name (`critique-forms`), the absolute path
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
artifact exactly as `critique-critic` would, and record what was disregarded in
`run.stripped_context`.

## Bench domain module

This skill's bench corpus module is `bench/generator/domains/forms.py`; see
`bench/generator/README.md` for what it must cover.
