---
title: critique-forms criterion registry, draft for maintainer review
effort: N2 (critique-forms)
status: draft, revision 2, all decisions ruled
date: 2026-09-25
---

# critique-forms: criterion registry draft

**Status: a draft for maintainer review, not a build.** Nothing under `skills/` exists yet. This
document supplies the thing every shipped skill had before its directory was scaffolded, a
per-skill criterion table, which for the first six lived in
[S-05 (skills slate)](../../plan_v0.1.0/S-05_skills-slate/spec.md) and for `critique-forms` lived
nowhere. It sits in `_unassigned/` by the `plab-spec` convention but is not a spec: once the open
decisions are ruled, the ruled registry becomes this effort's `spec.md`, with acceptance criteria,
and this file becomes its research record. Every source is listed in the
[bibliography](sources.md).

## What revision 2 is

Revision 1 proposed 17 criteria from 21 freely readable articles. The maintainer ruled on all six of
its decisions the same day and asked for a broader, more recent, more mobile and more measured
evidence base. Revision 2 is rebuilt from that base:

- **75 sources, 470 extracted findings**, read on 2026-09-25: Wroblewski's *Web Form Design* in
  full, Adam Silver's *Form Design Patterns*, four other books from the maintainer's library,
  Google web.dev, the GOV.UK Design System and its research posts, Nielsen Norman Group, Baymard
  Institute's benchmarks, three peer-reviewed papers, form-analytics datasets, controlled A/B
  tests, and the WHATWG HTML standard.
- **Every figure in this document was copied verbatim from a saved copy of its source** and checked
  again against that copy by a second pass: 135 figures across the five research streams, every one
  found (two needed a manual read where a two-column PDF split the sentence). Quotes are short and exact; everything else is paraphrased under
  [ADR 0006](../../../decisions/0006-copyright-paraphrase-policy.md).
- **Copies of the sources are the maintainer's local record** under `_local/research/critique-forms/`
  (gitignored). Copyrighted text is never committed; the bibliography records each source's URL or
  ISBN, access date and a checksum of the exact copy read.

## Rulings, 2026-09-25

| # | Ruling | Where it stands in revision 2 |
|---|---|---|
| 1 | Expand the research base, including Wroblewski's book | **Done.** The book is read in full (146 findings, page-cited) and cited. It supplies the grouping criterion revision 1 could not source |
| 2 | Leaning toward one `FORMS-` namespace, not firmly | **Ruled (A), second round:** `FORMS`, recorded in [ADR 0035](../../../decisions/0035-synthesized-rubric-namespace.md) |
| 3 | Checkout becomes its own skill | **Done.** Filed as N5 (critique-checkout); the card-specific criteria and 12 checkout findings are seeded there, below |
| 4 | Keep `autocomplete` in forms, sourced to the HTML standard | **Done.** `FORMS-AUTOCOMPLETE` checks tokens against the WHATWG autofill vocabulary, read today, with conversion evidence from Chrome and Zuko |
| 5 | Try the Internet Archive; favour recent, mobile and quantified sources | **Done.** The archived Baymard article was read: it holds no data, and newer web.dev guidance contradicts it, so confirm-email stays out. Mobile findings: 112 of 470 |
| 6 | Keep both `FORMAT-TOLERANCE` and `NNG-H5-PREVENT` with a stated boundary | **Applied.** Harmless or valid input is accepted and normalized; actually wrong input is prevented |

## The reuse surface

Unchanged from revision 1. The `html` artifact type, the shared composition model
(`bench/generator/html.py`) and the scoring resolver (`bench/metrics/resolve_html.py`) are reused as
is. **The forms corpus module is a new build**: `bench/generator/domains/forms.py`, with an
injector per scripted criterion and at least three judged, and at least three recipes, one clean.
The two existing `html` domain modules are 632 and 859 lines. The resolver locates a finding by an
element's `id`, tag, class or ordinal noun ("the third field"), so every scripted criterion flags one
control, and every control the corpus generates carries an `id`.

## Ground other skills own

Forms reviews the same `html` artifacts as `critique-accessibility` and `critique-usability`, and
the same failure moments as `critique-microcopy`. Where one of them already tests something, forms
does not test it again, because a duplicated criterion reports one defect twice.

| Ground | Owned by | So forms |
|---|---|---|
| A control with no label at all | `WCAG-3.3.2` and `NNG-H6-LABELED`, both scripted | does not test label presence |
| Error text and the error summary | `WCAG-3.3.1`, `NNG-H9-IDENTIFY`, the `NNG-EM` set | does not test error content |
| Recovery after an error | `NNG-H9-RECOVER`, `NNG-EM-PRESERVE-INPUT` | does not test it |
| When validation fires | `NNG-EM-TIMING` | does not test timing. The evidence is also contested: Bargas-Avila's 2007 study found validating on leaving a field caused *more* errors |
| Preventing a wrong entry by constraint | `NNG-H5-PREVENT`, `NNG-EM-PREVENT` | tests only the opposite failure, rejecting input that is valid or harmless (decision 6) |
| One action, one label, across a flow | `NNG-H4-CONTROL-NAMING` | tests whether a submit label is specific, not whether it is consistent |
| A radio or checkbox group's `fieldset` and `legend` | `WCAG-1.3.1`, structure exposed in markup | does not test it |
| Colour as the only signal | `WCAG-1.4.1` | does not test it |
| `autocomplete` as a WCAG conformance claim | **Accessibility, once E67 lands.** WCAG 2.2 SC 1.3.5 requires it; the maintainer ruled on 2026-09-25 to add it to `critique-accessibility` ([E67](../../../backlog/enhancements.md)) | **tests the same attribute for a different reason, deliberately**, as `WCAG-3.3.2` and `NNG-H6-LABELED` both test label presence. Accessibility's finding cites conformance; forms' cites the autofill completion and conversion evidence (decision 4). Each skill's description points to the other for the other angle |

## How the evidence is graded

Each criterion below names its sources by their bibliography handle and grades its strongest
evidence. The grade belongs to the finding, not the publisher: one Baymard article can hold a
benchmark figure and an opinion.

| Grade | Means |
|---|---|
| **PR** | Peer-reviewed paper |
| **LS** | Large-sample benchmark or analytics dataset, with its sample stated |
| **AB** | Controlled comparison or A/B test, with a sample or a significance level stated |
| **US** | Usability or eye-tracking study, with its method described |
| **OG** | Official guidance from a standards body or government design system, usually research-backed |
| **EX** | Expert guidance, no data |
| **AN** | Anecdote: a result reported without method, sample or significance |

Three rules the table follows:

- **Correlation is labelled.** Chrome's autofill figures come from Chrome's own correlational study,
  and Chrome says so. They are quoted as correlations.
- **Counter-evidence is shown beside the claim it counters**, not dropped. Two criteria carry it.
- **A criterion needs at least two independent sources, or one controlled study with a stated
  sample.** Two meet that bar only through expert sources, are kept by decision 7, and say so;
  a third, grouping, is deferred by the same decision.

Three grades the research agents assigned were corrected here: a 2023 principles book's application
of Hick's and Fitts's laws to forms is EX, not PR (the laws are peer-reviewed; the application is
not); an Unbounce button-wording result with no stated sample is AN, not AB; and Wroblewski's
"over 10 percent higher" completion for top-aligned labels, reported without sample or period, is
AN, not AB.

## Proposed registry: 24 criteria, 18 scripted and 6 judged

The `FORMS` namespace is ruled (decision 2, [ADR 0035](../../../decisions/0035-synthesized-rubric-namespace.md)). The scripted lane carries the markup-level
checks, most of them mobile, where the evidence is also strongest and most recent.

| # | ID | Lane | Mobile | Flags | Best evidence |
|---|---|---|---|---|---|
| 1 | `FORMS-INPUT-TYPE` | scripted | yes | An email, telephone, URL or search field whose `type` does not match its purpose | LS |
| 2 | `FORMS-NUMERIC-INPUTMODE` | scripted | yes | A digit string that is not a quantity (a one-time code, an account or reference number, a card-like string) using `type="number"`, or plain text without `inputmode="numeric"` | LS, OG |
| 3 | `FORMS-AUTOCOMPLETE` | scripted | yes | A personal, contact, address or credential field with no `autocomplete` token, a token outside the WHATWG vocabulary, or `autocomplete="off"` on data that is not one-time | LS |
| 4 | `FORMS-AUTOCORRECT` | scripted | yes | A name, email, username or address field left with autocorrect, auto-capitalization or spellcheck on | LS, PR |
| 5 | `FORMS-PLACEHOLDER-INSTRUCTION` | scripted | yes | A labelled field whose format instruction or example exists only in its placeholder | US, OG |
| 6 | `FORMS-REQUIRED-OPTIONAL` | scripted | no | A form mixing required and optional fields whose difference is not visible in label text: nothing marked, a symbol with no legend, or a marker only in a placeholder | OG |
| 7 | `FORMS-SPLIT-ENTITY` | scripted | yes | One entity split across several inputs: a phone number, a one-time code, a name split where one field serves. Dates are excluded | OG, US |
| 8 | `FORMS-FIELD-WIDTH` | scripted | no | A field of predictable length whose width in markup is far from its expected input | OG |
| 9 | `FORMS-FORMAT-TOLERANCE` | scripted | yes | A restriction that rejects valid or harmless input: a `pattern` refusing spaces, dashes or brackets in a phone number, letters in a postcode, or non-Latin letters in a name; an email `maxlength` under 254 | OG |
| 10 | `FORMS-PASSWORD-RULES` | scripted | no | A new-password field that forces composition through `pattern`, sets `minlength` below 8, or sets any `maxlength` | LS, OG |
| 11 | `FORMS-CONFIRM-PASSWORD` | scripted | yes | A second "confirm password" field | OG |
| 12 | `FORMS-ACTION-LABEL` | scripted | no | A primary submit labelled with a generic word from a fixed set (Submit, Send, OK, Go, Enter). "Continue" is excluded | EX, kept by decision 7 |
| 13 | `FORMS-RESET-BUTTON` | scripted | no | A reset or clear-all control in the form | EX, kept by decision 7 |
| 14 | `FORMS-INPUT-FONT-SIZE` | scripted | yes | A text input whose font size, where the artifact's CSS determines it, is below 16px, which makes iOS zoom the page on focus | OG |
| 15 | `FORMS-OPTION-CONTROL` | scripted | yes | A single-choice `select` with fewer than five options, where visible radio buttons would show every choice | LS, AB |
| 16 | `FORMS-DATE-SELECTS` | scripted | yes | A memorable date, such as a birth date, entered through three `select` dropdowns | OG, US |
| 17 | `FORMS-PHONE-REASON` | scripted | no | A required phone field with no adjacent or `aria-describedby` text saying why the number is needed | US |
| 18 | `FORMS-ADDRESS-FORMAT` | scripted | yes | An address form that forces house number and street into separate inputs, or requires a county-style field that postal delivery does not need | OG |
| 19 | `FORMS-FIELD-NECESSITY` | judged | no | Fields the task does not need now, the same information asked twice, or questions that could be deferred | LS |
| 20 | `FORMS-SINGLE-COLUMN` | judged | yes | Fields laid side by side so the completion order is ambiguous, except short related fields such as city, region and postcode | AB, contested |
| 21 | `FORMS-LABEL-POSITION` | judged | yes | Labels beside their fields on a mobile or short form, or label alignment mixed within one form | US, OG |
| 22 | `FORMS-ACTION-HIERARCHY` | judged | no | A secondary action as prominent as the primary, actions placed away from the column of fields, or actions at the top of the form | US |
| 23 | `FORMS-SELECTION-DEPENDENT` | judged | no | Conditional fields shown badly: every branch's fields exposed at once, or revealed far from the choice that triggers them | US |
| 24 | `FORMS-TOUCH-TARGET` | judged | yes | Tappable controls too small or too close together for a finger | OG |

## Evidence per criterion

Figures are quoted exactly as their sources state them. Handles resolve in the
[bibliography](sources.md).

1. **`FORMS-INPUT-TYPE`.** LS: Baymard's 48-site benchmark found "54% of mobile sites fail to invoke
   optimized touch keyboards" for phone, ZIP or card fields (`baymard-mobile-touch-keyboards`). OG:
   `webdev-signin-form`, `webdev-payment-address-form`, `baymard-touch-keyboard-cheatsheet`. EX:
   `silver-form-design-patterns` p. 34, `nng-mobile-input-checklist`, `lukew-mobile-input`.
2. **`FORMS-NUMERIC-INPUTMODE`.** OG with research: GOV.UK moved away from `type="number"` after
   finding Chrome silently discards non-numeric characters and that the field fails in Dragon and
   NVDA (`govuk-blog-number-input-type`). OG: `webdev-payment-address-form`, `webdev-signin-form`;
   Silver p. 100 cites the HTML specification's own advice. LS: on an iPhone 6S the numeric
   keyboard's keys are "521% larger" in hit area than the standard keyboard's
   (`baymard-mobile-touch-keyboards`). Date parts are deliberately not in scope: the same GOV.UK post
   lists dates among the genuinely incrementable numbers where `type="number"` is acceptable.
3. **`FORMS-AUTOCOMPLETE`.** LS, correlational: "users abandon forms 75% less frequently when they
   use autofill", and time spent filling forms is "approximately 35% lower"
   (`chrome-autofill-insights-2024`, which states the study is correlational). LS: across 215 forms,
   autofill users completed at "71% whilst for non-users it was 59%"; most forms showed the
   positive relationship and a minority showed the reverse (`zuko-browser-autofill-conversion`).
   LS, vendor-reported and checkout-scoped: Shopify guest checkouts using autofill "had a 45% higher
   CCR" (`google-blog-chrome-autofill-2024`). OG: the token vocabulary is the WHATWG standard
   (`whatwg-html-autofill`); web.dev names the typical failure, a non-standard token such as
   `first-name` where `given-name` is correct (`webdev-autofill-measure`), and says
   `autocomplete="off"` belongs only on one-off values (`webdev-autofill-learn`).
4. **`FORMS-AUTOCORRECT`.** LS: disabling auto-correct on the address line is honoured by "21% adhere"
   and violated by 79% of 48 benchmarked sites (`baymard-touch-keyboard-cheatsheet`). PR: fixing a
   wrong autocorrection costs "on average 5.5 seconds" (`alharbi-predictive-keyboards-2020`). OG:
   `govuk-names-pattern` (`spellcheck="false"` on names). EX: `nng-mobile-input-checklist`, Silver
   p. 203.
5. **`FORMS-PLACEHOLDER-INSTRUCTION`.** US: placeholder text strains memory once typing starts and
   makes empty fields less noticeable in eye tracking (`nng-placeholders-harmful`). OG: it
   disappears, is not always announced by screen readers, and its default styling often fails
   contrast (`govuk-text-input-component`). EX: `baymard-inline-labels`, Wroblewski p. 170, Silver
   pp. 22 to 23. Boundary: `NNG-H6-LABELED` owns the field with no label at all.
6. **`FORMS-REQUIRED-OPTIONAL`.** The sources disagree on *which* convention to use: GOV.UK marks
   optional fields and never uses an asterisk (`govuk-question-pages`), NN/g marks every required
   field with an asterisk (`nng-required-fields`), Baymard marks both
   (`baymard-required-optional`). **The criterion tests only what all of them agree on**: the
   difference is visible in label text, a symbol has a legend (Wroblewski p. 123), and colour or a
   placeholder alone does not count. The author chooses the convention. An unmarked optional
   "address line 2" is the commonest instance (`baymard-address-line-2`).
7. **`FORMS-SPLIT-ENTITY`.** OG: `webdev-payment-address-form` (one input for phone and card
   numbers; one name field), `govuk-names-pattern` (one full-name field, because not every name
   fits first and last). US: `baymard-single-input`. EX: three practitioner articles. **Dates are
   excluded** because GOV.UK's tested date pattern is three text inputs.
8. **`FORMS-FIELD-WIDTH`.** OG: an email field should show "at least 30 characters at once"
   (`govuk-email-addresses-pattern`). EX with data: in one dataset "99.9% of city names were 19
   characters or shorter" (`nng-web-form-design`). EX: `baymard-field-width`, Silver p. 82,
   Wroblewski pp. 116 to 118. Scripted only when the width is set in markup.
9. **`FORMS-FORMAT-TOLERANCE`.** OG: accept phone numbers in any format (`govuk-phone-numbers-pattern`);
   silently ignore case, spacing and punctuation in postcodes (`govuk-addresses-pattern`); match
   names with Unicode letters, not Latin-only patterns (`webdev-payment-address-form`); iOS's phone
   keyboard cannot type the special characters a strict pattern demands, and several countries'
   postcodes contain letters (`baymard-touch-keyboard-cheatsheet`); an email field must accommodate
   "up to 254 characters" (`govuk-email-addresses-pattern`). Boundary: decision 6.
10. **`FORMS-PASSWORD-RULES`.** LS: across 1,362 forms the password field has the highest mean
    abandonment of the common fields, "a mean abandonment rate of 10.5%" (`zuko-25-conversion-stats`,
    `zuko-field-ux-problems`), and "almost 50% of sessions have to return to a password field"
    (`zuko-password-advice`). OG: "set a minimum length of at least 8 characters" and no maximum
    (`govuk-passwords-pattern`). `baymard-password-rules` agrees on dropping composition rules.
11. **`FORMS-CONFIRM-PASSWORD`.** OG: `webdev-signup-form` and `webdev-signin-form` (asking twice
    adds work and breaks with autofill). EX: Silver p. 39 (a reveal toggle instead). AN: a vendor
    case study reports "a 56% increase in conversions" from removing the field
    (`zuko-field-ux-problems`). **Confirm-email is excluded**: Baymard's archived 2011 article
    recommends it, while web.dev (`webdev-signup-form`, `webdev-signin-form`) and
    `silver-58-form-design-ux-best-practices` recommend against it. Silver's book addresses only the
    password case.
12. **`FORMS-ACTION-LABEL`.** Expert sources only: `baymard-button-design`, Wroblewski p. 78,
    `silver-form-ui-design-designlab`. The one wording result found (Unbounce, via a listicle) is
    AN. "Continue" is excluded because Wroblewski recommends it for steps of a multi-page form.
13. **`FORMS-RESET-BUTTON`.** EX: `nng-web-form-design`, `silver-form-design-principles-cxl`,
    Wroblewski p. 141, all on the risk of wiping entered data by accident. The closest measured
    evidence is an analogy, not a test of reset controls: in the Etre study behind Wroblewski's
    chapter 6 (six layouts, 23 participants), "26 percent of the people tested mistakenly clicked the
    Cancel button" in the worst layout (pp. 147 to 148). Graded EX, because the analogy is not a
    measurement of the thing the criterion flags.
14. **`FORMS-INPUT-FONT-SIZE`.** OG: mobile text needs to be larger than desktop, "20px is about
    right on mobile" (`webdev-signin-form`). EX: "a font size of at least 16 pixels" (Silver p. 32),
    and iOS zooms the page on focus below 16px (`silver-58-form-design-ux-best-practices`,
    `silver-design-a-better-form`). Scripted only where the artifact's own CSS sets the size.
15. **`FORMS-OPTION-CONTROL`.** LS: "55% of users across our testing were observed to open a
    drop-down, just to see what it contained" and close it again, and "Drop-downs are generally a
    poor choice for offering fewer than 5 or more than 10 options" (`baymard-dropdown-usability`),
    which is where the threshold comes from, verbatim. The article scopes its findings to checkout
    flows and says other contexts may deviate, so the threshold carries that caveat into forms. AB: radio buttons were completed "2.5 seconds faster" than a multi-select control,
    n = 354 per arm (`silver-form-design-principles-cxl`). EX: Silver p. 125.
16. **`FORMS-DATE-SELECTS`.** OG with research: three text inputs, and a live service's errors
    dropped once the month field accepted names (`govuk-date-input-component`). EX: avoid three
    drop-downs (`nng-date-input`); drop-downs still allow "31 February 2017" (Silver p. 155).
17. **`FORMS-PHONE-REASON`.** US: `baymard-phone-reason` (its title's percentage is not re-verified
    and is not quoted). EX: explain any request whose purpose is not obvious (Silver p. 77). AN: a
    listicle attributes an abandonment drop "from 39% to 4%" to making the field optional, with no
    method (`silver-58-form-design-ux-best-practices`).
18. **`FORMS-ADDRESS-FORMAT`.** OG: do not require house number and street in separate inputs
    (`webdev-payment-address-form`); county is not needed for UK delivery and should be optional or
    removed (`govuk-addresses-pattern`); postcode formats vary by country
    (`baymard-touch-keyboard-cheatsheet`). Address lookup is left to N5.
19. **`FORMS-FIELD-NECESSITY`.** LS, checkout-scoped: "the average US checkout flow contains 23.48
    form elements" against a far smaller need (`baymard-cart-abandonment-list`). OG: never ask the
    same thing twice (`govuk-question-pages`); avoid a title field (`govuk-names-pattern`). EX: the
    question protocol (Silver p. 27). AN: moving optional questions after registration "increased
    answers by almost 40 percent" (Wroblewski p. 45). **Counter-evidence:** Zuko's dataset finds field
    count is not strongly correlated with completion (`zuko-25-conversion-stats`), which is why the
    test is necessity, not count.
20. **`FORMS-SINGLE-COLUMN`.** AB: across 702 desktop participants, one column took "102.3 seconds
    against 117.8 seconds" for multi-column, measuring time only, not abandonment
    (`speero-single-vs-multicolumn-2016`). **Counter-evidence, AB:** on a 13-field lead form "the
    two-column form converted 22% better", at a 99% confidence level, sample not disclosed
    (`hubspot-one-vs-two-column-test`). EX: `nng-web-form-design`, Wroblewski p. 67. **The evidence is
    mixed**, so the criterion is judged and its severity is capped at 2.
21. **`FORMS-LABEL-POSITION`.** US: moving from a top-aligned label to its field took "just 50ms",
    against a typical "500ms" for left-aligned labels (`penzo-2006-label-placement`, sample not
    stated, familiar data only). OG: `govuk-text-input-component`, `webdev-signin-form`. EX:
    `nng-web-form-design`, `baymard-label-position`; do not mix alignments (Wroblewski p. 103). Left
    alignment remains legitimate for long forms of unfamiliar data (Wroblewski p. 96).
22. **`FORMS-ACTION-HIERARCHY`.** US: the Etre study (23 participants, six designs) found the layout
    separating primary and secondary actions led "26 percent" to click Cancel by mistake, and
    centred buttons made people "around six seconds slower" (Wroblewski pp. 142 to 149). US:
    buttons at the top of a form made testers think they had reached its end
    (`silver-design-a-better-form`). EX: `nng-web-form-design`, `lukew-primary-secondary`.
23. **`FORMS-SELECTION-DEPENDENT`.** US: the Etre study of eight designs with 23 participants found
    exposing every branch's fields cost "a whopping 18 more fixations" than the best design, and that
    hiding irrelevant controls until chosen worked best (Wroblewski pp. 276 to 301). One source, a
    controlled study with a stated sample.
24. **`FORMS-TOUCH-TARGET`.** OG: "the recommended target size for touchscreen objects is 7-10 mm",
    Apple suggests 48x48 px, and "the W3C suggest at least 44x44 CSS pixels" (`webdev-signin-form`;
    web.dev's own dash, normalized here). EX: 44px (Silver p. 32).
    Boundary: WCAG 2.2 SC 2.5.8 sets a conformance minimum of 24 by 24 CSS pixels and is being added
    to `critique-accessibility` by E67. Forms tests the larger mobile-usability sizes above, a
    different threshold for a different reason, the same deliberate overlap as `autocomplete`. Judged
    because rendered size depends on styling the artifact may not contain.

## Left out, and why

**Contested by the sources themselves**, so not a criterion until the evidence settles:
- Disabling the submit button until the form is valid: Silver and Wroblewski (p. 153) say never,
  Designlab says always, one practitioner says short forms only.
- Confirm-email: Baymard 2011 for it; web.dev and a Venture Harbour article against.
- Validation timing: owned by microcopy, and contested (see the ownership table).

**Deferred by decision 7:** `FORMS-GROUPING` (organise long forms into titled sections), backed
by Wroblewski chapter 2 (p. 42, and p. 52's "an additional 15 visual elements" from stacked
separators) and Designlab, with no measured result. It is a judged rule, and judged rules without a
measured basis are the likeliest source of noisy findings in the lane where this library's precision
is already weakest. It returns when a study is found.

**Supported, but thin or single-sourced**, deferred to a v1.1 review: a multi-select list box
(evidence from 2008 to 2009), help-text placement, smart defaults and pre-checked marketing opt-ins,
progress signals for multi-page forms, double-barreled questions (Jarrett), and blocking paste into
password fields.

**Statistics that could not be traced to a primary source**, which must never be cited as measured:
- the Expedia "$12 million" Company-field story, which traces only to a retold quote;
- a listicle's CAPTCHA "up to 30%" figure attributed to Stanford;
- "39% to 4%" phone-field abandonment attributed to Clicktale;
- Amazon's "100 milliseconds" revenue figure;
- Zuko's "22% completion uplift" restatement of inline-validation research (the primary is the
  *A List Apart* study, already read);
- the Iyengar jam study, which is real but about jam displays, not forms.

## Seeds for N5 (critique-checkout)

38 findings are tagged checkout-only and move to [N5](../../../backlog/new-components.md). The main ones:
- card-number format and length, including allowing spaces (`webdev-payment-address-form`,
  `baymard-card-spaces`);
- card expiry in the card's own MM/YY form (`baymard-expiry-date`, Silver p. 156);
- payment fields in card order, and a security-code hint saying where to find it (Silver p. 104);
- a coupon field collapsed behind a link (`silver-form-design-principles-cxl`, `baymard-field-count`);
- billing defaulting to the delivery address (Silver p. 105);
- guest checkout (Silver p. 75, `webdev-signup-form`);
- stripping navigation from checkout (Wroblewski p. 68);
- automatic address lookup with a manual fallback (`baymard-address-lookup`, Silver p. 84), which
  Baymard's dropdown research finds only 38% of sites fully implement;
- checkout length ("17% of US online shoppers" abandoned over a long or complicated checkout,
  `baymard-cart-abandonment-list`);
- Shopify's autofill guest-checkout figure.

## What "scripted" rests on

Most scripted rows first work out what a field is for, and they do it lexically, from its label,
`name`, `id` or `autocomplete` token. That is deterministic, so it belongs in the scripted lane,
but it is a heuristic, and the generated corpus will use vocabulary the heuristic recognises, so
the benchmark will measure it favourably. **The miss and false-alarm rate on real forms, with
idiosyncratic naming, is unmeasured.** Two rows (`INPUT-FONT-SIZE`, `FIELD-WIDTH`) can only decide
when the artifact itself carries the relevant CSS or attribute, and stay silent otherwise.

## Downstream, once ruled

- **Corpus:** `bench/generator/domains/forms.py` needs 18 scripted injectors and at least three
  judged, across sign-up, contact, profile and address recipes, with one clean form.
- **Routing:** three contested pairs, forms with accessibility, usability and microcopy. Each needs a
  boundary clause in both descriptions, per the E30 checklist step.
- **Authoring:** built through `askit-build-skill` in fallback mode per the E11 ruling, judging
  conformance with this repository's pinned `node scripts/check.mjs`, with every point of friction
  filed to the toolkit's backlog.
- **Measurement is a paid stop:** k=5 on both pinned tiers needs the maintainer's go-ahead.

## Decisions ruled, second round, 2026-09-25

| # | Ruling | Consequence |
|---|---|---|
| 2 | **(a) A synthesized-rubric namespace, `FORMS`** | Recorded as [ADR 0035](../../../decisions/0035-synthesized-rubric-namespace.md), which also sets the conditions a future skill such as N5 (critique-checkout) must meet to do the same. `docs/reference/criterion-ids.md` gains the `FORMS` row when the skill ships, not before |
| 7 | **(c) Keep the two scripted expert-only rules, defer grouping** | `FORMS-ACTION-LABEL` and `FORMS-RESET-BUTTON` stay, labelled as expert consensus. `FORMS-GROUPING` moves to "Left out" until a measured study is found. The registry is 24 criteria |
| 8 | **(b) Expand `critique-accessibility` now** | Found while preparing this decision: the skill implements **22 of WCAG 2.2's 55 Level A and AA success criteria**. Four are declared out of reach, and 29 are never mentioned, while its scope statement claims A and AA "required for AA conformance". E67 now carries that corrected scope and the ruling: add the criteria checkable from static markup and CSS (1.3.4, 1.3.5, 2.4.7, 2.5.8, 4.1.3), as a new version with a paid re-measure, confirmed before dispatch. Narrowing the claim for what remains uncovered follows as E68 |

Nothing in this registry is still open. The next artifact is the effort's `spec.md`.
