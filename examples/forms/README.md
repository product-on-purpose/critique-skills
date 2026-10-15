---
title: critique-forms worked example
description: A sign-up form critiqued for completion cost on a phone, reproducing the scripted lane yourself, reading a judged-lane touch-target finding taken from a golden fixture, and a filled-in disposition log
audience: both
level: beginner
---

# critique-forms worked example

This is one complete pass through `critique-forms`: an artifact, a critique of it, and the human
decisions that came after. If you are a PM, a designer, or anyone deciding whether to trust this
skill before pointing it at your own sign-up or checkout form, this page is the place to see what it
actually produces first.

## The artifact

`artifact.html` in this folder is "Join Meridian Outfitters," a fictional account sign-up form:
fourteen required fields (name, email, a new password, a street address, a phone number, a company
website, a membership number, an account number, a postal code, a shipping-speed choice, a
given-name and family-name pair, an organization name, and a preferred contact time), one optional
secondary-phone field, and three buttons, a "View details" button, the primary "Create account"
submit, and a "Clear form" reset control. Nothing about it is exotic; it is the kind of form that
ships in an ordinary sprint once a few fields get bolted on over time.

It is copied verbatim from
[`skills/critique-forms/examples/artifacts/golden-05.html`](../../skills/critique-forms/examples/artifacts/golden-05.html),
one of this skill's own golden fixtures, so this folder is self-contained: everything needed to
reproduce what follows is here, byte for byte identical to its source, confirmed by matching
`artifact_sha256` below. Of this skill's five golden fixtures, this one was chosen for this
walkthrough because it is the only one whose critique includes a judged-lane finding: the other
four are built to exercise the scripted lane only.

## Honesty labeling

Two different things are true about the findings below, and this page keeps them apart:

- **Scripted lane, bit for bit reproducible.** Eight findings come from `scripts/checks.py`, a
  deterministic script. Run the exact command below yourself and you get the exact JSON below,
  every time, on any machine. This was verified by actually running the command against the copy of
  the artifact in this folder, not typed from memory.
- **Judged lane, curated from a validated golden fixture.** One finding, the touch-target finding on
  the "View details" button, comes from a model reading the form's declared CSS against
  `FORMS-TOUCH-TARGET`, the same four-pass protocol a live `critique-forms` run follows. It is not
  something this page ran live and pasted in; it is copied verbatim from this skill's own golden
  envelope
  ([`skills/critique-forms/examples/golden-05.json`](../../skills/critique-forms/examples/golden-05.json)),
  a fixture that passed `python -m contract.validate` before it was accepted into the skill's test
  suite, and that golden's own note names the eight committed benchmark runs (of ten) whose judged
  lane independently converged on this same finding. A live judged-lane run against the same
  artifact should land on the same criterion and severity, but the exact wording of `violation` and
  `fix` can vary run to run, the way any model output does.

Nothing on this page is authored content presented as a live run. Where a claim is reproducible, the
command to reproduce it is given. Where it is curated, that is stated plainly, right next to it.

## Running the scripted lane yourself

From the repository root:

```
python skills/critique-forms/scripts/checks.py examples/forms/artifact.html
```

This is the deterministic half of the skill: eighteen mechanical checks (`checks.scripted` in
[`SKILL.md`](../../skills/critique-forms/SKILL.md)) run directly against the markup and declared CSS
as text, no model call involved. We ran this exact command against this exact file before writing
this page. It produced eight findings and a failing gate, matching the eight scripted findings in
`envelope.json` in this folder field for field: same criteria, severities, locations, evidence, and
fixes. The only differences were `run.artifact` (it echoed the path we pointed it at),
`run.timestamp` (the moment we ran it), and the `id` values, because the scripted lane numbers
findings within its own eight-finding run while the full envelope numbers all nine findings, both
lanes, together, after ranking by severity. Content, not the label or the number, is the
reproducible part.

**Worth noticing on this artifact in particular:** the scripted lane alone reports four severity-3
findings. The full envelope has five, because the judged-lane touch-target finding is itself a
severity 3 that the scripted lane, which never reads declared CSS for anything but font size and
field width, cannot see at all. A scripted-only pass still correctly fails the gate here, but it
would understate how many release-blocking problems this form actually has.

## Running the full critique

Inside a Claude Code session with this plugin installed, the natural way to ask for the full
critique, both lanes, is to just say so:

> Critique `examples/forms/artifact.html` with critique-forms.

Claude Code delegates that to the `critique-critic` subagent (`SKILL.md`, "Delegation"), which runs
the full four-pass protocol, scripted lane and judged lane both, in a clean context that has never
seen this page being written, and returns one contract-valid run envelope, the same shape as
`envelope.json` in this folder. Unlike the command above, this step calls a model, so it is not bit
for bit reproducible; expect the same criterion and severity on the touch-target finding, not always
identical wording.

## Findings tour

`envelope.json` in this folder is the full, validated golden envelope for this artifact, both lanes
combined: nine findings, five at severity 3 and four at severity 2. The tour below walks through all
five severity-3 findings, the ones that fail the release gate on their own; the four severity-2
findings are real and are in the disposition log below, just not walked through in the same depth,
to keep this tour to a size someone will actually read.

### F-001, a required phone field with no stated reason (FORMS-PHONE-REASON, severity 3, scripted)

**What you'd see:** a field labeled "Phone number," marked required, with nothing beside it saying
why a phone number is needed.

**Why it's a violation:** the form also collects an email address, and a person who expects to be
contacted by email treats an unexplained, required phone request as suspicious. This is the greater
branch of `FORMS-PHONE-REASON`: an unexplained phone field is severity 2 when it is the form's only
contact field, and severity 3 when the form also asks for email, which this one does.

**What the fix means:** add a line beside the field saying what the number is used for, for example
that it confirms a shipment, or make the field optional.

**What severity 3 signals:** major, fix before release, per
[the severity scale](../../docs/reference/severity-scale.md).

### F-002, a format rule that disappears on the first keystroke (FORMS-PLACEHOLDER-INSTRUCTION, severity 3, scripted)

**What you'd see:** the membership-number field's placeholder reads "Must be 8 digits." The moment
you start typing, that text is gone, and nothing else on the page restates the rule.

**Why it's a violation:** a placeholder is not a label and not hint text; it vanishes exactly when
someone most needs the rule, mid-entry. Stating a rule only in the placeholder is this criterion's
severity-3 branch; stating only an example there, rather than a hard rule, would be severity 2.

**What the fix means:** move "Must be 8 digits" into hint text beside the field, linked to it with
`aria-describedby`, so it stays visible while typing.

**What severity 3 signals:** major and gate-failing, same as above.

### F-003, required and optional fields that are not told apart (FORMS-REQUIRED-OPTIONAL, severity 3, scripted)

**What you'd see:** fourteen fields marked required and one, "Secondary phone," that is not, and
nothing on the page, not a label, not a placeholder, says which is which.

**Why it's a violation:** a form that mixes required and optional fields has to mark the difference
somewhere. This form has exactly one optional field buried among fourteen required ones with zero
marking anywhere, which is this criterion's severity-3 branch; marking some fields but leaving the
marker unexplained would only be severity 2.

**What the fix means:** mark the one optional field with the word "optional" in its label. One field
to mark is simpler than marking all fourteen required ones.

**What severity 3 signals:** major and gate-failing. It also recurs across the whole form, not once,
which is why the finding's location names the first optional field and counts the other fourteen as
instances rather than reporting fifteen separate findings.

### F-004, a reset control beside the submit button (FORMS-RESET-BUTTON, severity 3, scripted)

**What you'd see:** a "Clear form" button sitting directly next to "Create account."

**Why it's a violation:** a control that destroys every entered value, placed where a mistaken tap
aimed at the real submit button can land on it instead, risks losing a completed form to one bad
tap. Severity 3 is the branch for a reset control adjacent to the primary submit; a reset control
elsewhere on the form would only be severity 2.

**What the fix means:** remove the reset control. Nothing about this form needs a dedicated way to
destroy everything just typed.

**What severity 3 signals:** major and gate-failing, same as the three above. Four separate
severity-3 scripted findings is already enough to fail this run's gate before the judged lane adds a
fifth.

### F-005, a touch target far smaller than a fingertip needs (FORMS-TOUCH-TARGET, severity 3, judged)

**What you'd see:** on a phone, the "View details" button is tiny, a sliver of text with almost no
padding around it, and tapping it reliably takes more than one try.

**Why it's a violation:** the button's declared style sets `padding:1px 2px;font-size:11px`, which
the judged lane estimates renders at roughly 13 to 15 CSS pixels tall, with no associated label
enlarging the target, far under the roughly 44-pixel target mobile-usability guidance recommends.
Nothing in the eighteen scripted checks reads a control's rendered size this way; this is exactly
the kind of estimate `references/FORMS.md` reserves for the judged lane (`FORMS-TOUCH-TARGET`'s own
"Lane rationale": "Rendered size depends on styling, inheritance and layout that the artifact may
only partly declare").

**Where this finding comes from:** copied verbatim from
[`skills/critique-forms/examples/golden-05.json`](../../skills/critique-forms/examples/golden-05.json),
not run live for this page. That golden's note records that eight of the ten committed envelopes
from paid benchmark run 37091134037 (four of five on each pinned tier) independently reported this
same criterion, at this same severity, on this same button, which is part of why this artifact was
chosen for this skill's first judged-lane golden.

**What the fix means:** remove the font-size and padding overrides, or raise them so the rendered
button reaches at least 44 by 44 CSS pixels, matching the form's other buttons.

**What severity 3 signals:** major and gate-failing, same weighing order as every scripted finding
above; the judged lane is calibrated on the identical severity scale, not a softer or harder one of
its own ([`references/severity-anchors.md`](../../skills/critique-forms/references/severity-anchors.md),
"Scripted and judged findings are calibrated on the same scale").

## Disposition log

The full log is in [`dispositions.json`](dispositions.json) in this folder, schema-valid
(`python -m contract.validate dispositions.json` reports `valid`, and its `finding_id` values all
resolve against `envelope.json`). This is curated illustration, one reviewer's plausible call on
each finding, not a record of a real incident. It is deliberately not all accepts: real review means
some findings get pushed back on or pushed out, and a log where everything is accepted without
question is not a log anyone should trust.

| Finding | Criterion | Severity | Disposition | Why |
|---|---|---|---|---|
| F-001 | FORMS-PHONE-REASON | 3 | accept | Confirmed; adding a line explaining the number is used only to confirm a shipment. |
| F-002 | FORMS-PLACEHOLDER-INSTRUCTION | 3 | accept | Confirmed; moving the digit-count rule into hint text linked with `aria-describedby` next release. |
| F-003 | FORMS-REQUIRED-OPTIONAL | 3 | accept | Confirmed; marking the one optional field is simpler than marking all fourteen required ones. |
| F-004 | FORMS-RESET-BUTTON | 3 | accept | Confirmed; removing the reset control, nothing in support tickets has ever asked for it. |
| F-005 | FORMS-TOUCH-TARGET | 3 | accept | Confirmed against the declared style; raising the button's padding and font size to match the form's other buttons. |
| F-006 | FORMS-NUMERIC-INPUTMODE | 2 | accept | Confirmed; adding `inputmode=numeric` is a one-attribute change. |
| F-007 | FORMS-OPTION-CONTROL | 2 | defer | Real, but this select uses the shared design-system component already being replaced by a visible-options variant next quarter. Tracked against that rework instead of patched once here. |
| F-008 | FORMS-PASSWORD-RULES | 2 | accept | Confirmed; raising the minimum length to 8, matching the account team's own password policy. |
| F-009 | FORMS-SPLIT-ENTITY | 2 | reject | Given name and family name are collected separately on purpose: a downstream legal-identity verification step requires the two parts distinct, not one free-text name. Revisit if that requirement ever changes. |

The reject on F-009 is worth sitting with for a second: the finding is not wrong about what the
markup does, a name that does not fit the given-name-and-family-name shape must still be forced into
it, it is a judgment call that a specific downstream requirement outweighs that cost here. That is
exactly the kind of call the disposition step exists for
([`docs/how-to/dispositions.md`](../../docs/how-to/dispositions.md)); the schema and validator can
check that the log is well-formed and that its finding IDs resolve, but whether F-009's reject holds
up is a call only a human accountable for the artifact can make.

## Validating the files in this example

Both JSON files here were checked against the contract before this page was written, not asserted
clean:

```
python -m contract.validate examples/forms/envelope.json
valid
python -m contract.validate examples/forms/envelope.json --gate
valid
(exit code 2, meaning "fail": five severity-3 findings above the default threshold of 0)

python -m contract.validate examples/forms/dispositions.json
valid
```

Resolving `dispositions.json`'s finding IDs against `envelope.json` needs both files loaded together
(the single-file CLI cannot do this on its own; see `docs/how-to/dispositions.md`), and that check
also ran clean before this page shipped: every `finding_id` in the log resolves in the envelope, and
every denormalized `criterion` matches.

## Files in this folder

| File | What it is |
|---|---|
| `artifact.html` | The sign-up form being critiqued. Verbatim copy of `skills/critique-forms/examples/artifacts/golden-05.html`. |
| `envelope.json` | The full, validated run envelope for this artifact, both lanes. Verbatim copy of the `expected_envelope` in `skills/critique-forms/examples/golden-05.json`. |
| `dispositions.json` | This walkthrough's disposition log against `envelope.json`. |
| `README.md` | This page. |

## See also

- [`skills/critique-forms/SKILL.md`](../../skills/critique-forms/SKILL.md), the skill's own protocol
  and artifact claim.
- [`skills/critique-forms/references/FORMS.md`](../../skills/critique-forms/references/FORMS.md),
  the full twenty-four-criterion registry, operational tests, and lane split cited above.
- [`docs/reference/severity-scale.md`](../../docs/reference/severity-scale.md), the 0-4 scale every
  finding's severity comes from.
- [`docs/how-to/dispositions.md`](../../docs/how-to/dispositions.md), the full shape and purpose of
  the disposition log format used above.
