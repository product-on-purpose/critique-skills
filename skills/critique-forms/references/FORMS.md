# FORMS rubric source

The criterion registry for `critique-forms`. `FORMS` is a synthesized rubric: this library built it
from the form-design rules that several publishers state independently, under the conditions in
[ADR 0035 (synthesized-rubric namespace)](../../../docs/internal/decisions/0035-synthesized-rubric-namespace.md).
A criterion ID therefore does not name a publisher. Each row below names the sources that state its
rule instead, and grades each source by the strength of its evidence. Every operationalization is
this library's own wording; no source text is reproduced
([ADR 0006, copyright paraphrase policy](../../../docs/internal/decisions/0006-copyright-paraphrase-policy.md)).

## Sources

**Every source handle in the table resolves to a row of the committed bibliography,**
[`sources.md`](../../../docs/internal/release-plans/_unassigned/N2_critique-forms/sources.md). That
file records each source's URL or ISBN, the date it was read, and a checksum of the exact copy read,
so a reader can check any row without trusting this synthesis (ADR 0035, condition 4). The research
record behind each row, with its figures, is the
[criterion registry](../../../docs/internal/release-plans/_unassigned/N2_critique-forms/criterion-registry-draft.md).

`SKILL.md`'s `rubric_sources` lists the publishers behind those handles, one entry per publisher.
The handles themselves are article-level, and a handle's prefix is not always its author:

- **The `silver-` prefix names a research stream, not Adam Silver.** Only `silver-form-design-patterns`
  is Silver's book. `silver-58-form-design-ux-best-practices` is Venture Harbour's,
  `silver-form-design-principles-cxl` is CXL's, `silver-form-ui-design-designlab` is Designlab's,
  and `silver-design-a-better-form` is a Medium article by Allie Paschal.
- **A book is cited by handle and printed page,** for example `wroblewski-web-form-design` p. 78.
  The page numbers are those printed in the edition the bibliography names.

### How a citation is graded

A grade belongs to one source's evidence for one criterion, not to the publisher: one Baymard
article can hold a benchmark figure and an opinion. A row's citations are grouped by grade, strongest
first.

| Grade | Means |
|---|---|
| **PR** | A peer-reviewed paper |
| **LS** | A large-sample benchmark or analytics dataset, with its sample stated |
| **AB** | A controlled comparison or A/B test, with a sample or a significance level stated |
| **US** | A usability or eye-tracking study, with its method described |
| **OG** | Official guidance from a standards body or a government design system, usually research-backed |
| **EX** | Expert guidance with no data |
| **AN** | An anecdote: a result reported without method, sample or significance |

**No figure the registry lists as untraceable to a primary source is cited here as measured.** Those
figures are listed under "Left out", below, so that nobody reintroduces one by accident.

## Artifact and reach

The artifact is an HTML form, or a page or fragment containing one, read through the library's
`html` artifact type. This skill evaluates markup and declared CSS as text. It never evaluates a
rendered page, a running script, or a live interaction. Two consequences follow:

- **Two scripted criteria decide only from what the artifact declares.** `FORMS-INPUT-FONT-SIZE`
  reports nothing unless the artifact's own CSS sets the input's font size, and `FORMS-FIELD-WIDTH`
  reports nothing unless the markup sets the field's width.
- **Most scripted criteria first work out what a field is for,** lexically, from its label text, its
  `name`, its `id` or its `autocomplete` token. That inference is deterministic, so it belongs in the
  scripted lane, but it is a heuristic. The generated bench corpus uses vocabulary the heuristic
  recognizes, so the benchmark measures it favourably. Its miss and false-alarm rates on real forms
  are measured separately, before any paid run, by the real-forms check in the
  [effort's spec](../../../docs/internal/release-plans/_unassigned/N2_critique-forms/spec.md)
  (AC-10 and AC-13).

Each scripted finding locates exactly one control, by its `id` where the markup carries one. When a
defect belongs to the form as a whole, such as no field marked as required or optional, the finding
locates the first control it affects and counts the rest as instances.

## How a field's purpose is read

Twelve scripted criteria first decide what a field is for. They read four signals, in this order,
and the first signal that names a purpose wins:

1. **The `autocomplete` token,** when it is a valid field name in the HTML standard's autofill
   vocabulary (`email`, `tel`, `given-name`, `postal-code`, `one-time-code`, and the rest).
2. **The `type` attribute,** for the types that state a purpose outright: `email`, `tel`, `url`,
   `search` and `password`.
3. **The `name` and `id` attributes,** split into words at hyphens, underscores and case changes.
4. **The label text:** the `label` element whose `for` matches the field's `id`, or the `label`
   element that wraps the field.

Each signal is matched against one fixed vocabulary per purpose, case-insensitively, as whole words.
The purposes and their cue words are:

| Purpose | Cue words |
|---|---|
| email | email, e-mail |
| phone | phone, telephone, tel, mobile, cell |
| web address | website, url, homepage, web address |
| search | search, query, q |
| name | name, first name, last name, surname, given name, family name, full name, forename |
| username | username, user name, login, user id |
| new password | a password field whose cues include new, create, choose, set or register, or whose token is `new-password` |
| current password | any other password field |
| street address | address, street, address line |
| house number | house number, street number, building number, house no |
| postal code | postcode, post code, postal code, zip, zip code |
| city | city, town |
| county | county |
| region | state, province, region |
| country | country |
| one-time code | one-time code, verification code, security code, otp, passcode |
| account number | account number, reference number, membership number, customer number, policy number |
| birth date | birth, date of birth, dob, born |
| date part | day, month, year |
| quantity | quantity, qty, amount, number of, count, age |

Where two purposes match one signal, the more specific wins: house number before street address,
postal code before one-time code, and every other purpose before name, so that a field called user
name reads as a username. A field no signal names has no inferred purpose, and no criterion that
depends on purpose reports anything about it. That silence is deliberate. A field the heuristic
cannot read is a miss, which the real-forms check counts, and never a false alarm.

A form's **primary submit** is its first `button` with no `type` or with `type=submit`, or its first
`input` with `type=submit`. Its label is the button's text, or the input's `value`.

A field is **required** when it carries the `required` attribute or `aria-required=true`.

## Ground other skills own

Forms reviews the same HTML artifacts as `critique-accessibility` and `critique-usability`, and the
same failure moments as `critique-microcopy`. Where one of them already tests something, forms does
not test it again, because a duplicated criterion reports one defect twice. No operational test
below flags any of this ground:

| Ground | Owned by | So forms |
|---|---|---|
| A control with no label at all | `WCAG-3.3.2`, `NNG-H6-LABELED` | does not test label presence |
| Error text and the error summary | `WCAG-3.3.1`, `NNG-H9-IDENTIFY`, the `NNG-EM` set | does not test error content |
| Recovery after an error | `NNG-H9-RECOVER`, `NNG-EM-PRESERVE-INPUT` | does not test recovery |
| When validation fires | `NNG-EM-TIMING` | does not test timing |
| Preventing a wrong entry by constraint | `NNG-H5-PREVENT`, `NNG-EM-PREVENT` | tests only the opposite failure, a restriction that rejects valid or harmless input |
| One action, one label, across a flow | `NNG-H4-CONTROL-NAMING` | tests whether a submit label is specific, never whether it is consistent |
| A radio or checkbox group's `fieldset` and `legend` | `WCAG-1.3.1` | does not test grouping markup |
| Colour as the only signal | `WCAG-1.4.1` | does not test colour |

### Two deliberate overlaps

Two criteria test a property that `critique-accessibility` also covers once E67 (accessibility
expansion) adds the matching WCAG 2.2 success criteria. Both overlaps were ruled deliberately on
2026-09-25. In each pair, accessibility reports a conformance failure and forms reports a completion
cost, so the two findings name one property for two different reasons.

- **`FORMS-AUTOCOMPLETE` overlaps WCAG 1.3.5 (Identify Input Purpose).** Forms grades the finding by
  what happens to autofill, which a pass-or-fail conformance finding cannot do. A missing token is
  severity 2, because the browser falls back to guessing and may still fill the field. A token
  outside the standard's vocabulary, or autocomplete switched off on address or credential data, is
  severity 3, because autofill is then certainly broken.
- **`FORMS-TOUCH-TARGET` overlaps WCAG 2.5.8 (Target Size (Minimum)).** WCAG sets a conformance
  floor of 24 by 24 CSS pixels. Forms tests the larger sizes that mobile-usability guidance
  recommends for a finger, which is a different threshold for a different reason.

## Registry

Twenty-four criteria, in ascending ID order, the order `SKILL.md`'s pass 2 sweeps them in.

Each Operationalization cell ends with the row's sources, grouped by grade, strongest first.

| ID | Operationalization | Operational test | Severity 2 anchor | Severity 3 anchor | Lane | Lane rationale |
|---|---|---|---|---|---|---|
| FORMS-ACTION-HIERARCHY | The primary action is the most prominent control and sits where the fields end, in line with them. A secondary action is visibly lesser, and no action sits above the fields. Sources: US `wroblewski-web-form-design` pp. 142 to 149, `silver-design-a-better-form`; EX `nng-web-form-design`, `lukew-primary-secondary`. | Compare the form's actions using the markup and its declared CSS. Flag a secondary action styled as prominently as the primary, actions placed away from the column of fields, and actions placed above the fields. Whether a button's label is specific is `FORMS-ACTION-LABEL`'s question, not this one. | A settings form gives Cancel and Save the same filled style side by side, so the person must read both labels to find the one that saves. | A long application form puts its submit and cancel buttons above the fields, so a person who meets them first believes the form ends there and submits it unfinished. | judged | Prominence and placement are judged relative to the form's other controls, which requires reading its layout as a whole. |
| FORMS-ACTION-LABEL | A form's primary button says what it does, such as Create account or Send message, rather than a generic word that would fit any form. A bare Continue on one step of a longer form is acceptable. This is expert opinion without measured support, kept by ruling, and the sources support it unevenly: Designlab names generic button words directly, Baymard argues for descriptive button text in general, and the cited Wroblewski page is a guest essay asking for meaningful link labels, which this criterion extends to buttons. Sources: EX `silver-form-ui-design-designlab`, `baymard-button-design`, `wroblewski-web-form-design` p. 78. | Flag a form's primary submit when its whole label, ignoring case and surrounding punctuation, is Submit, Send, OK, Go or Enter. Never flag Continue, and never flag a label that adds anything to one of those words, such as Send message. Whether one action keeps one name across a flow is `NNG-H4-CONTROL-NAMING`'s question; this criterion tests only whether the label is specific. The scripted lane assigns severity 2 to every finding. | A newsletter sign-up form's only button reads Submit, so the person must read the rest of the form to learn what pressing it does. | Not assigned. A generic label slows the decision to press but never blocks it, so the scripted lane grades every instance 2. | scripted | The primary submit is found by a fixed rule and its label is compared with a closed word list. |
| FORMS-ADDRESS-FORMAT | An address form lets a person write the address the way it is written. It does not force the house number and the street into separate fields, and it does not require a field that postal delivery does not need, such as a county. Address formats vary by country. Sources: OG `webdev-payment-address-form`, `govuk-addresses-pattern`, `baymard-touch-keyboard-cheatsheet`. | Flag a field whose inferred purpose is house number when the same form also has a street-address field: severity 3 when the house-number field is required, because an address with no number cannot then be entered, and severity 2 when it is optional. Flag a required field whose purpose is county at severity 2. A required state, province or region field is never flagged, because several countries' postal addresses need one. | A UK address form requires a County field, so a person in a city with no county must invent a value to continue. | A delivery form requires a House number field separate from the street, so a person whose house has a name but no number cannot complete the address. | scripted | The house-number and county purposes come from the cue vocabulary, and required status is an attribute, so the check is a fixed reading. |
| FORMS-AUTOCOMPLETE | A field asking for personal, contact, address or sign-in data carries a token from the HTML standard's autofill vocabulary, so a browser or password manager can fill it, and autofill is switched off only for a value used once. Users who autofill a form complete it more often, a correlation the source studies state as such. Sources: LS `chrome-autofill-insights-2024`, `zuko-browser-autofill-conversion`, `google-blog-chrome-autofill-2024`; OG `whatwg-html-autofill`, `webdev-autofill-measure`, `webdev-autofill-learn`. | Check each field whose inferred purpose is name, email, phone, username, new or current password, street address, postal code, city, county, region, country or birth date. Severity 2 when it has no `autocomplete` attribute, or only the value `on`. Severity 3 when the value is not a valid autofill detail: an optional token beginning `section-`, then an optional `shipping` or `billing`, then an optional contact type (`home`, `work`, `mobile`, `fax`, `pager`) only before a phone, email or `impp` field name, then exactly one field name, then an optional `webauthn`, compared without regard to case. Severity 3 when the value is `off` on an address or credential field; severity 2 when it is `off` on a name, phone or email field. A one-time code may switch autofill off. An `autocomplete=off` on the `form` element applies to every field that sets no token of its own. Overlap: WCAG 1.3.5 (Identify Input Purpose) covers the same attribute as a conformance requirement, which `critique-accessibility` reports once E67 adds it. This criterion grades the attribute by what happens to autofill instead. | A delivery form's postal-code field has no autocomplete attribute, so the browser guesses from the field's name and label and may or may not fill it. | A sign-up form marks its email field with the token e-mail and its first-name field with first-name, neither of which the standard defines, so autofill is certainly broken for both. | scripted | Purpose comes from the cue vocabulary, and validity is a lookup against a closed vocabulary under a fixed token grammar. |
| FORMS-AUTOCORRECT | A field for a name, an email address, a username or an address line switches off autocorrection and spellchecking. A phone keyboard's dictionary does not know most of these values, so it replaces them silently, and fixing a wrong correction costs the person time. Sources: PR `alharbi-predictive-keyboards-2020`; LS `baymard-touch-keyboard-cheatsheet`; OG `govuk-names-pattern`; EX `nng-mobile-input-checklist`, `silver-form-design-patterns` p. 203. | Check each `input` whose `type` is `text` or absent and whose inferred purpose is name, email, username or street address. Flag it when it carries neither `autocorrect=off` nor `spellcheck=false`. Flag an email or username field also when it lacks `autocapitalize=none` or `autocapitalize=off`, since a capital the person never typed breaks the value; a name field is exempt from this branch, because a capital is usually right there. Each field yields at most one finding. One flagged field in the form is severity 2; two or more make every one of them severity 3. | A sign-up form leaves spellchecking on in its single full-name field, so an unusual surname can be corrected to a dictionary word and the person must notice and undo it. | A delivery form leaves autocorrection on in its name, street and city fields, so an unfamiliar name in any of them can be replaced as the person types and shipped wrong. | scripted | Purpose comes from the cue vocabulary, and the two switches are attributes, so the check is a fixed comparison. |
| FORMS-CONFIRM-PASSWORD | A form asks for a new password once, ideally with a way to show what was typed, instead of asking for it a second time to confirm it. Asking twice adds work for every person and gains nothing when a browser fills the password. Sources: OG `webdev-signup-form`, `webdev-signin-form`; EX `silver-form-design-patterns` p. 39; AN `zuko-field-ux-problems`. | Flag the second of two password fields in one form when its cues include confirm, repeat, re-enter, retype, again or verify, or when both fields carry `autocomplete=new-password`. A current-password field followed by one new-password field is never flagged. The scripted lane assigns severity 2 to every finding. | A sign-up form asks for the password, then asks for it again under Confirm password, doubling the typing for every person who signs up. | Not assigned. Asking twice doubles the work of one field but never blocks completion, so the scripted lane grades every instance 2. | scripted | Two password fields and the confirm cue words are fixed readings of the markup. |
| FORMS-DATE-SELECTS | A date the person knows by heart, such as a date of birth, is typed into day, month and year fields, not picked from three drop-downs. Drop-downs cost a tap and a scroll for each part and still allow impossible dates. Sources: OG `govuk-date-input-component`; EX `nng-date-input`, `silver-form-design-patterns` p. 154. | Find three `select` elements in one form whose cues name a day, a month and a year. Flag the first of them when their cues name a birth date, or when the year select offers more than 30 options, which only a date far in the past needs. Severity 3 when the year select offers more than 30 options, because the person must scroll a long list; severity 2 otherwise. A date the person must look up, such as an appointment, is outside this criterion. | A form asks for a date of birth through three drop-downs whose year list is short, so each part still costs an open and a tap. | A sign-up form asks for a date of birth through drop-downs whose year list runs back a hundred years, so the person scrolls a long list to reach their year. | scripted | The three selects, their date cues and the count of year options are fixed readings of the markup. |
| FORMS-FIELD-NECESSITY | A form asks only for what its task needs now: nothing the service could do without, nothing the form already asked, and nothing that could wait until after the task is done. The test is necessity, not count, because field count alone does not predict completion. The benchmark figure behind this row comes from checkout flows. Sources: LS `baymard-cart-abandonment-list`, with counter-evidence LS `zuko-25-conversion-stats`; OG `govuk-question-pages`, `govuk-names-pattern`; EX `silver-form-design-patterns` p. 27; AN `wroblewski-web-form-design` p. 45. | Name the form's task from its heading, its submit label and its fields. Flag a field when the task cannot use its answer, when it asks again for something the form already asked, or when its answer serves a later step and could be asked then. Never flag a field only for being one of many: a long form whose every field the task uses passes. | A newsletter sign-up asks an optional question about how the person heard of the service, an answer the task does not use and could ask later. | An account sign-up requires a title, a date of birth and a home address before creating an account that uses none of them. | judged | Whether a task needs an answer depends on reading the form's purpose as a whole. |
| FORMS-FIELD-WIDTH | A field whose answer has a predictable length is sized to that length, so its width hints at what to enter and the whole entry stays visible while it is typed and checked. Sources: OG `govuk-email-addresses-pattern`; EX `nng-web-form-design`, `baymard-field-width`, `silver-form-design-patterns` p. 82, `wroblewski-web-form-design` pp. 116 to 118. | Read a width only from the field's `size` attribute or a CSS width in `ch` units that the artifact declares for it, and report nothing for any other field. Severity 3 for a field narrower than its value: email under 20 characters, phone under 10, city under 13, postal code under 5, one-time code under 4. Severity 2 for a short fixed-length field more than three times wider than its value: postal code or one-time code over 24 characters, a year over 12, a day or month over 6. These thresholds are this skill's own, set from the sources' figures: two-thirds of the 30 characters an email field should show, and of the 19 characters that hold almost every city name. | A postal-code field declares a width of 40 characters, so its width suggests a long answer and the person may wonder what else to type. | An email field declares a width of 15 characters, so most addresses scroll out of view while typed and the person cannot check the address before sending it. | scripted | The width is a declared attribute or CSS value and the thresholds are fixed numbers, so the comparison needs no judgment. |
| FORMS-FORMAT-TOLERANCE | A field accepts every valid or harmless way of writing its value: spaces, dashes or brackets in a phone number, letters in a postcode, non-Latin letters in a name, and an email address of any legal length. Sources: OG `govuk-phone-numbers-pattern`, `govuk-addresses-pattern`, `govuk-email-addresses-pattern`, `webdev-payment-address-form`, `baymard-touch-keyboard-cheatsheet`. | Test the field's `pattern` attribute, matched against the whole value as a browser applies it, against fixed valid samples for the field's inferred purpose. Severity 3 for a phone field whose pattern rejects a number written with spaces, with dashes, with brackets or with a leading plus; for a name field whose pattern rejects an accented letter, a non-Latin letter, a hyphen or an apostrophe; and, in a form offering a choice of country, for a postal-code field whose pattern rejects a postcode containing letters. Severity 2 for an email field whose `maxlength` is below 254. A pattern that cannot be compiled is not judged. Preventing a genuinely wrong entry by constraint is `NNG-H5-PREVENT` and `NNG-EM-PREVENT`; this criterion flags only a restriction that rejects a valid value. | An email field sets a maximum length of 50 characters, so the rare person with a longer address cannot enter it. | A phone field's pattern accepts digits only, so a correct number typed with spaces, as people commonly write it, is rejected. | scripted | A pattern either matches a fixed sample or does not, and a maximum length is a number, so the check is deterministic. |
| FORMS-INPUT-FONT-SIZE | Text in a form's entry fields is at least 16 pixels, so a phone does not zoom the page when a field is focused and the entry is readable on a small screen. Sources: OG `webdev-signin-form`; EX `silver-form-design-patterns` p. 32, `silver-58-form-design-ux-best-practices`, `silver-design-a-better-form`. | Resolve the font size the artifact's own CSS declares for each text-entry control (a text-like `input`, a `textarea` or a `select`), from its `style` attribute or a stylesheet rule matching its tag, class or `id`, counting `rem` and `em` at 16 pixels each. Report nothing for a control whose size the artifact does not set. Severity 2 for a declared size below 16 pixels; severity 3 below 12 pixels. | A sign-in form's stylesheet sets its inputs to 14 pixels, so a phone zooms the page each time a field is tapped and the person must zoom back out. | A form's stylesheet sets its inputs to 11 pixels, so the entry is hard to read on a phone even after the page zooms in. | scripted | The declared size is a CSS value read from the artifact, and the thresholds are fixed numbers. |
| FORMS-INPUT-TYPE | A field that collects an email address, a phone number, a web address or a search term declares the input type built for that value, so a phone shows the keyboard that suits it. Sources: LS `baymard-mobile-touch-keyboards`; OG `webdev-signin-form`, `webdev-payment-address-form`, `baymard-touch-keyboard-cheatsheet`; EX `silver-form-design-patterns` p. 34, `nng-mobile-input-checklist`, `lukew-mobile-input`. | Check each `input` whose inferred purpose is email, phone, web address or search, and flag it when its `type` is not `email`, `tel`, `url` or `search` respectively. An absent `type` counts as `text`. A phone field using `type=number` is flagged here, because a number keypad lacks the characters phone numbers are written with. One flagged field in the form is severity 2; two or more make every one of them severity 3. | A sign-up form's email field declares the text type while its phone field correctly declares tel, so one field opens the full keyboard and the person hunts for the at sign. | A contact form declares the text type on its email, phone and website fields alike, so every field the person types into opens the wrong keyboard. | scripted | Purpose comes from the cue vocabulary and the type is an attribute, so the comparison needs no judgment. |
| FORMS-LABEL-POSITION | Labels sit above their fields on a mobile or short form, and one form keeps one label alignment throughout. Labels beside fields remain acceptable on a long form of unfamiliar data, where slower reading is useful. Sources: US `penzo-2006-label-placement`; OG `govuk-text-input-component`, `webdev-signin-form`; EX `nng-web-form-design`, `baymard-label-position`, `wroblewski-web-form-design` pp. 96 and 103. | Decide where each label renders relative to its field, using the markup and its declared CSS. Flag a form whose labels sit beside their fields when it has eight fields or fewer, or declares a mobile layout such as a viewport meta tag or a narrow-screen media query. Flag a form that mixes labels above fields with labels beside them. A field with no label at all is `WCAG-3.3.2`'s and `NNG-H6-LABELED`'s, not this criterion's. | A short contact form sets its labels to the left of its fields at desktop width, so each label sits a long eye movement away from its field. | A mobile sign-up form sets labels to the left of narrow fields, so the fields shrink to a few characters and the labels wrap. | judged | Where a label renders depends on layout and on the form's length and audience, which require reading the form as a whole. |
| FORMS-NUMERIC-INPUTMODE | A string of digits that is not a quantity, such as a one-time code or an account number, uses a text field that asks for the numeric keypad. The number type is built for values a person counts or measures, and browsers handle other digit strings in it badly. Sources: LS `baymard-mobile-touch-keyboards`; OG `govuk-blog-number-input-type`, `webdev-payment-address-form`, `webdev-signin-form`, and the HTML standard's own advice as quoted in `silver-form-design-patterns` p. 100. | Check each `input` whose inferred purpose is one-time code or account number. Severity 3 when its `type` is `number`, because the browser may alter or refuse what is typed. Severity 2 when its `type` is `text` or absent and it lacks `inputmode=numeric`, because the person types digits on the full keyboard. Quantities and the parts of a date are never flagged, because they are numbers a person may count up or down. Phone numbers are `FORMS-INPUT-TYPE`'s. | A verification-code field is a plain text field with no numeric input mode, so the person types six digits on the full keyboard's small keys. | An account-number field uses the number type, so a turn of the mouse wheel over it can change the number unnoticed, and a person dictating with Dragon cannot enter it at all. | scripted | Purpose comes from the cue vocabulary, and the type and input mode are attributes, so the check is a fixed comparison. |
| FORMS-OPTION-CONTROL | A single choice among fewer than five options is offered as visible radio buttons, not a drop-down, so the person sees every option without opening anything. The five-option threshold comes from checkout research and is applied here to forms generally. Sources: LS `baymard-dropdown-usability`; AB `silver-form-design-principles-cxl`; EX `silver-form-design-patterns` p. 125. | Flag a `select` without the `multiple` attribute that offers fewer than five real options, not counting an option that is disabled or has an empty value, which serves as a prompt. One such select in the form is severity 2; two or more make every one of them severity 3. | A contact form asks how to reply through a drop-down offering email or phone, so the person opens it just to see two choices. | A profile form asks three short questions, each through a drop-down of two or three options, so every answer costs an extra tap to reveal choices that could all have been visible. | scripted | Counting a select's options is a fixed reading of the markup. |
| FORMS-PASSWORD-RULES | A field that sets a new password asks for at least eight characters and imposes no maximum length and no forced mix of character types. The password field is where people most often abandon a form. Sources: LS `zuko-25-conversion-stats`, `zuko-field-ux-problems`, `zuko-password-advice`; OG `govuk-passwords-pattern`; EX `baymard-password-rules`. | Check each field whose inferred purpose is new password. Severity 3 for a `pattern` attribute, because it enforces a composition rule the person meets only by being rejected. Severity 3 for any `maxlength`, because it stops a long passphrase or a generated password partway. Severity 2 for a `minlength` below 8. | A registration form's new-password field sets a minimum length of six characters, which lets a person choose a password too short to be safe. | A new-password field carries a pattern demanding an upper-case letter, a digit and a symbol, and states none of it, so the person learns each rule only by being rejected. | scripted | The new-password purpose and the three attributes are fixed readings of the markup. |
| FORMS-PHONE-REASON | A form that requires a phone number says beside the field why it needs one. People hesitate to give a number without a reason, and some give a false one or leave, most often when they expect to be contacted by email. Sources: US `baymard-phone-reason`; EX `silver-form-design-patterns` pp. 76 to 77; AN `silver-58-form-design-ux-best-practices`. | Check each required field whose inferred purpose is phone. Collect its label text, the text of every element its `aria-describedby` names, and the text of other elements inside the field's parent element. Flag the field when none of that text contains a reason marker: so, in case, to contact, to call, to text, about your, for delivery, we will, we'll, only use, used to, or why. Severity 3 when the same form also asks for an email address, because a person who expects email contact finds an unexplained phone request suspicious; severity 2 when the phone is the form's only contact field, so its purpose is easier to guess. | A callback-request form requires a phone number under the label Phone, with no word on why, though the form offers no other way to reach the person, so the purpose is guessable. | A sign-up form asks for an email address and then requires a phone number with no word on why, so a person who expected email contact suspects sales calls and may give a false number or leave. | scripted | Required status is an attribute, the email purpose comes from the cue vocabulary, and the reason markers are a closed list searched in nearby text, so the check is a fixed reading. |
| FORMS-PLACEHOLDER-INSTRUCTION | A format rule or an example the person needs while typing sits in the label or in hint text beside the field, never only in the placeholder, which disappears as soon as typing starts. The sources agree on rules. On examples they divide, which is why an example grades lower than a rule. Sources: US `nng-placeholders-harmful`; OG `govuk-text-input-component`; EX `wroblewski-web-form-design` p. 170, `silver-form-design-patterns` pp. 22 to 23; with counter-evidence EX `baymard-inline-labels`, which accepts an example in the placeholder of a field whose label stays visible, though not a rule. | Check each field that has a label; a field with no label at all is `WCAG-3.3.2`'s and `NNG-H6-LABELED`'s. Read its `placeholder`. It states a rule when it contains must, at least, characters, digits, format, or a date mask such as DD/MM/YYYY; it gives an example when it contains e.g., for example, example, an at sign, or a run of three or more digits. Flag the field when its placeholder states a rule or gives an example and neither its label text nor any text its `aria-describedby` names contains a rule or example marker. Severity 3 for a stated rule, because the field enforces what the person can no longer see; severity 2 for an example. | A phone field labelled Phone number shows an example number only as its placeholder, so the example vanishes at the first keystroke and the person types from memory. | A date field labelled Date of birth states the order DD/MM/YYYY only in its placeholder, so the order vanishes as the person types and a date in another order is rejected. | scripted | The label, the hint and the placeholder are text in the markup, and the markers are a closed list, so the comparison needs no judgment. |
| FORMS-REQUIRED-OPTIONAL | When a form mixes required and optional fields, the difference shows in each label's text, by whichever convention the author chooses. A symbol is explained in words, and a placeholder never carries the difference alone. Sources: OG `govuk-question-pages`; EX `nng-required-fields`, `baymard-required-optional`, `baymard-address-line-2`, `wroblewski-web-form-design` p. 123. | Check only a form with at least one required and at least one optional field. A label is marked when its text contains an asterisk, the word required, or the word optional. Severity 3, located at the first optional field and counting every unmarked field as an instance, when no label in the form is marked. Severity 2, at the first asterisk-marked field, when no text in the form outside the labels pairs an asterisk with the word required or mandatory. Severity 2 for a field whose placeholder carries the marker while its label does not. Colour as the only signal is `WCAG-1.4.1`'s and is not tested. | A form marks its required fields with an asterisk and never says what the asterisk means, so the person must infer it. | A form with four required and three optional fields marks none of them, so the person cannot tell which fields they may leave empty. | scripted | Required status is an attribute and the markers are fixed strings in label text, so the check is a fixed reading. |
| FORMS-RESET-BUTTON | A form has no control that clears everything entered, because one mistaken press destroys work the person cannot get back. This is expert consensus without a measurement of reset controls themselves, kept by ruling. Sources: EX `nng-web-form-design`, `silver-form-design-principles-cxl`, `wroblewski-web-form-design` pp. 141 and 147 to 148. | Flag any `input` or `button` with `type=reset` inside a form, and any button labelled Reset, Clear, Clear all or Clear form. Severity 3 when it sits next to the primary submit, as the adjacent element or a consecutive button in the same container, because a press aimed at the submit can land on it. Severity 2 anywhere else in the form. | A long application form places a Clear form button at its top, far from the submit, where a stray press is unlikely but still wipes everything. | A contact form sets a Reset button directly beside Send, styled the same, so a press aimed at Send can erase the whole message. | scripted | The reset type and the label list are fixed attributes and strings, and adjacency is a fixed position in the markup. |
| FORMS-SELECTION-DEPENDENT | Fields that apply only after a particular choice appear once that choice is made, next to the choice that revealed them. Sources: US `wroblewski-web-form-design` pp. 276 to 301, one controlled study with a stated sample. | Find each choice that governs other fields: a radio group, checkbox or select whose options make other fields relevant. Flag a form that shows every branch's fields at once, and a form whose revealed fields sit far from their trigger, after unrelated fields. Read only what the artifact declares: a field hidden by the `hidden` attribute or a declared display rule counts as not shown. | A choice of how to be contacted reveals its phone field at the bottom of the form, after unrelated fields, so the person must hunt for what the choice opened. | A registration form shows the fields for individuals and for companies at once, so a person fills fields that do not apply and cannot tell which ones matter. | judged | Whether a field depends on a choice, and whether it sits near enough to it, requires reading the form's logic as a whole. |
| FORMS-SINGLE-COLUMN | Fields run in one column so the order of completion is never in doubt, though short related fields such as city, region and postcode may share a row. The evidence is mixed, so a finding never exceeds severity 2. Sources: AB `speero-single-vs-multicolumn-2016`, with counter-evidence AB `hubspot-one-vs-two-column-test`; EX `nng-web-form-design`, `wroblewski-web-form-design` p. 67. | Using the markup and its declared CSS, find fields placed side by side: a grid or flex row, a table row, or inline fields on one line. Flag a row whose fields are not short parts of one related group, when a person could read the form across the rows or down the columns. Severity never exceeds 2. | A registration form sets email and phone side by side, so a person may finish the left column first and miss the phone field. | Not assigned. Severity is capped at 2: one controlled study found one column faster, while one controlled test found two columns converted better. | judged | Whether a row reads in an ambiguous order depends on the rendered layout as a whole. |
| FORMS-SPLIT-ENTITY | A value a person thinks of as one thing, such as a phone number, a one-time code or a name, goes in one field, not several, unless a system genuinely needs the parts. Dates are the exception, because the tested date pattern uses separate day, month and year fields. Sources: US `baymard-single-input`; OG `webdev-payment-address-form`, `govuk-names-pattern`; EX `silver-58-form-design-ux-best-practices`, `silver-form-design-principles-cxl`, `silver-form-ui-design-designlab`. | Flag the first field of a run of two or more consecutive inputs that split one value: phone-number parts (each with an inferred purpose of phone, or the tokens `tel-area-code`, `tel-local-prefix` and `tel-local-suffix`), one-time-code parts (each with `maxlength=1` and a purpose of one-time code), or a name split into given and family name fields. Never flag day, month and year fields. One split value in the form is severity 2; two or more make every one of them severity 3. | A sign-up form splits the person's name into first-name and last-name fields, so a name that does not fit that shape must be forced into it. | An account form splits both the phone number into three boxes and the verification code into six one-digit boxes, so the person moves between boxes in two places and a pasted code may land in the first box only. | scripted | The parts are consecutive inputs with fixed name, token and length cues, so the run is found by a fixed rule. |
| FORMS-TOUCH-TARGET | Every tappable control in a form is large enough for a fingertip, and far enough from its neighbours that a tap lands where intended, at the sizes mobile-usability guidance recommends, around 44 to 48 CSS pixels. Sources: OG `webdev-signin-form`; EX `silver-form-design-patterns` p. 32. | From the declared CSS, estimate each tappable control's rendered size, counting padding and any associated label that enlarges the target. Flag a control smaller than about 44 CSS pixels in either dimension, or two adjacent controls close enough that one fingertip covers both. Report nothing where the CSS gives no basis for an estimate. Overlap: WCAG 2.5.8 (Target Size (Minimum)) sets a conformance floor of 24 by 24 CSS pixels, which `critique-accessibility` reports once E67 adds it. This criterion tests the larger size mobile-usability guidance recommends, for a different reason. | A form's buttons render 32 pixels tall, above the conformance floor but below the recommended size, so taps sometimes need a second try. | A survey form's radio buttons render at 16 pixels with 4 pixels between them, and their labels do not enlarge the target, so a fingertip often selects the neighbouring option. | judged | Rendered size depends on styling, inheritance and layout that the artifact may only partly declare. |

## Lane split

Eighteen scripted, six judged.

- **Scripted (18):** every criterion that a fixed reading of the markup, its attributes and its
  declared CSS can decide. Most of them are mobile, where the evidence is also strongest and most
  recent.
- **Judged (6):** `FORMS-ACTION-HIERARCHY`, `FORMS-FIELD-NECESSITY`, `FORMS-LABEL-POSITION`,
  `FORMS-SELECTION-DEPENDENT`, `FORMS-SINGLE-COLUMN` and `FORMS-TOUCH-TARGET`. Each requires reading
  the form as a whole, or a rendered size the artifact may not declare.

No criterion sits in both lanes. A scripted criterion firing clean is not a verdict on the form's
usability. `FORMS-INPUT-TYPE` passing does not mean the form asks only for what it needs; that is
`FORMS-FIELD-NECESSITY`'s judged question.

## Left out

**Contested by the sources themselves,** so not a criterion until the evidence settles:

- Disabling the submit button until the form is valid.
- Asking for an email address twice.
- When validation fires, which `NNG-EM-TIMING` owns in any case.

**Deferred until a measured study is found:** organising a long form into titled sections. It is a
judged rule with expert support and no measured result, and judged rules without a measured basis
are the likeliest source of noisy findings.

**Supported but thin or single-sourced,** deferred to a later review: multi-select list boxes,
help-text placement, smart defaults and pre-checked marketing opt-ins, progress signals for
multi-page forms, double-barreled questions, and blocking paste into password fields.

**Checkout-specific rules** belong to N5 (critique-checkout): card-number formatting, expiry dates,
security-code hints, coupon fields, billing defaults, guest checkout and address lookup.

**Figures that could not be traced to a primary source, which no row cites as measured:** the
Expedia Company-field revenue story, a CAPTCHA abandonment figure attributed to Stanford, a
phone-field abandonment drop attributed to Clicktale, Amazon's latency-to-revenue figure, Zuko's
restatement of an inline-validation uplift, and the Iyengar jam study.

## See also

- [`docs/internal/skill-template.md`](../../../docs/internal/skill-template.md), "Criterion tables",
  the seven-column format this file implements.
- [ADR 0035 (synthesized-rubric namespace)](../../../docs/internal/decisions/0035-synthesized-rubric-namespace.md),
  why one namespace names a rubric built from several publishers.
- [`docs/reference/severity-scale.md`](../../../docs/reference/severity-scale.md), the shared scale
  the anchors below calibrate against, and this skill's own
  [`severity-anchors.md`](severity-anchors.md).
- [The N2 (critique-forms) spec](../../../docs/internal/release-plans/_unassigned/N2_critique-forms/spec.md),
  the acceptance criteria this registry meets.
