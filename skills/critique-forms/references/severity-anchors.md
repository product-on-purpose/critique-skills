# Severity anchors

This skill's own domain-anchor prose, extending `docs/reference/severity-scale.md`'s "Domain anchors"
section for form usability. Artifact type: HTML forms, or pages and fragments containing them,
evaluated as static markup and declared CSS, never as a rendered or live-interacted page.

Severity is assigned by weighing impact first, then frequency, then persistence, exactly as
`docs/reference/severity-scale.md` specifies. The anchors below calibrate that weighing across the
domain as a whole. The per-criterion severity 2 and severity 3 anchors in `references/FORMS.md` are
the authoritative anchors for any single criterion. All examples here are original.

## Impact means the cost of completing the form

The question that sets severity first is what the defect costs a person trying to finish the form.
Form defects rarely make a form impossible to complete. They add work: a keyboard to switch, a value
to retype, a choice to hunt for, a rule to guess. Impact grows with how much work the defect adds,
and with how likely that work is to make someone give up.

A defect that adds a small, recoverable step caps at severity 2. A phone field that opens the full
keyboard is one: the person can still type the number, a little slower. A name field that leaves
autocorrect on is another, since the person can undo a wrong correction. A defect that blocks valid
input, destroys entered data, or makes completion depend on guessing reaches severity 3. Examples
are a pattern that rejects a correctly typed phone number, a reset button beside the submit button,
and a password rule the person cannot see until the form rejects them.

Severity 4 is reserved for a form that cannot be completed at all by a whole class of person, such
as an address form whose required fields no valid address can satisfy. None of this skill's 24
criteria is anchored at severity 4 by default. A 4 is a finding-level judgment about a specific
artifact, not a property of a criterion.

## Frequency and persistence move a finding within its range

A single field without the right keyboard and every numeric field in the form without one are the
same defect by impact. They are not the same severity. The second recurs at every field the person
fills in, so its cost compounds across the form. Recurrence pulls a severity 2 toward 3 within one
criterion. Frequency alone never sets the level; what the defect costs at one occurrence does.

Persistence works across a flow rather than within one field. A defect on an optional field that
most people skip persists for nobody. The same defect on a required field in the first step of a
sign-up form persists for everyone who starts.

## Two criteria grade by a ruled scale rather than by the general weighing

- **`FORMS-AUTOCOMPLETE` grades by its effect on autofill,** as ruled on 2026-09-25. A personal,
  contact or address field with no token is severity 2: the browser falls back to guessing from the
  field's name and label, and may still fill it. A token outside the HTML standard's autofill
  vocabulary, or autocomplete switched off on address or credential data, is severity 3: autofill is
  then certainly broken for that field, and a password manager cannot help.
- **`FORMS-SINGLE-COLUMN` is capped at severity 2,** because the evidence on side-by-side fields is
  mixed. A controlled study found one column faster, and a controlled test on a lead form found two
  columns converted better. A reviewer who believes a layout is severe records that belief in the
  finding's evidence and keeps the severity at 2.

## Scripted and judged findings are calibrated on the same scale

A scripted finding, such as an email field with the wrong input type, and a judged finding, such as
a secondary action styled as prominently as the primary, are assigned severity by the identical
weighing order. Confidence, not severity, is where the lane shows in a finding. A scripted check
reports high confidence by construction, while a judged check's confidence reflects how much
interpretation the call required. Severity is never inflated or discounted because of the lane that
produced the finding.

## Thresholds the scripted lane applies

The per-criterion anchors in `references/FORMS.md` describe two calibrated points, and a real form
lands between them constantly. Where a scripted criterion's severity depends on a count or a field
type, `scripts/checks.py` applies the split stated in that criterion's operational test, so a
judged-lane reviewer re-deriving a severity by hand grades the same defect the way the script does.

- **Recurrence, for the criteria whose two anchors differ in how many fields the defect touches**
  (`FORMS-AUTOCORRECT`, `FORMS-INPUT-TYPE`, `FORMS-OPTION-CONTROL`, `FORMS-SPLIT-ENTITY`): one
  instance in the form is severity 2, and two or more make every instance severity 3, not only the
  second one onward. This is the same rule `critique-accessibility` applies to its recurring
  criteria, so the two HTML skills grade a repeated defect alike.
- **Branch, for the criteria whose condition has a lesser and a greater form.** The lesser branch
  is severity 2 and the greater is severity 3:
  - `FORMS-ADDRESS-FORMAT`: an optional house-number field or a required county is 2; a required
    house-number field is 3.
  - `FORMS-AUTOCOMPLETE`: a missing token, or autocomplete switched off on a name, phone or email
    field, is 2; an invalid token, or autocomplete switched off on address or credential data, is
    3. This is the ruled scale above.
  - `FORMS-DATE-SELECTS`: a year list of 30 options or fewer is 2; a longer one is 3.
  - `FORMS-FIELD-WIDTH`: a short field far too wide is 2; a field too narrow to show its value is 3.
  - `FORMS-FORMAT-TOLERANCE`: an email maximum length below 254 is 2; a pattern that rejects a
    valid sample is 3.
  - `FORMS-INPUT-FONT-SIZE`: a declared size from 12 up to 16 pixels is 2; below 12 pixels is 3.
  - `FORMS-NUMERIC-INPUTMODE`: a text field without the numeric input mode is 2; the number type is
    3.
  - `FORMS-PASSWORD-RULES`: a minimum length below 8 is 2; a pattern or any maximum length is 3.
  - `FORMS-PLACEHOLDER-INSTRUCTION`: an example only in the placeholder is 2; a rule only in the
    placeholder is 3.
  - `FORMS-REQUIRED-OPTIONAL`: an unexplained asterisk, or a marker only in a placeholder, is 2; no
    marking at all is 3.
  - `FORMS-RESET-BUTTON`: a reset control elsewhere in the form is 2; one next to the primary
    submit is 3.
- **Fixed at severity 2** (`FORMS-ACTION-LABEL`, `FORMS-CONFIRM-PASSWORD`, `FORMS-PHONE-REASON`):
  each defect costs work or trust but never blocks completion, and none has a greater form that
  does. Their severity 3 anchor cells say so rather than invent an example.

A judged-lane finding has no equivalent list, by construction. Its severity comes from the weighing
order applied to its criterion's own two anchor rows, with `FORMS-SINGLE-COLUMN` capped at 2.
