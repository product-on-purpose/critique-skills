---
title: critique-forms criterion registry, draft for maintainer review
effort: N2 (critique-forms)
status: draft
date: 2026-09-25
---

# critique-forms: criterion registry draft

**Status: a draft for maintainer review, not a build.** Nothing under `skills/` exists yet. It sits
in `_unassigned/` by the `plab-spec` convention but is not a spec: once the decisions below are
ruled, the ruled registry becomes this effort's `spec.md`, with acceptance criteria, and this file is
its research record. This
document supplies the thing every shipped skill had before its directory was scaffolded, a
per-skill criterion table, which for the first six lived in
[S-05 (skills slate)](../../plan_v0.1.0/S-05_skills-slate/spec.md) and for `critique-forms` lived
nowhere. [`ROADMAP.md`](../../../../../ROADMAP.md) gives forms one sentence and
[N2 (critique-forms)](../../../backlog/new-components.md) gives it a why-gate verdict; neither is a
registry. Lane split, `scripts/checks.py` scope, the corpus module's injectors, and the eval cases
all derive from the table below, so it is the artifact worth ruling on before 40 paid cells are
measured against it.

## What this draft settles, and what it leaves to the maintainer

Settled here, from evidence: which sources are actually readable today, which ground three shipped
skills already own, what the `html` reuse surface really provides, and a proposed criterion set
with lanes.

Left open, as numbered decisions at the end: the source list, the size of the registry, and how
hard to draw each boundary with the three neighbouring skills.

## The reuse surface, measured rather than assumed

N2's cost argument is that forms "reuses `critique-accessibility`'s existing `html` artifact type
and its element, CSS and id resolver". Read against the code, that is true of three things and not
of a fourth:

| Piece | Reused as is | Evidence |
|---|---|---|
| The `html` artifact type and its tolerance rule | Yes. No new type, so no ADR and no `bench/README.md` change | `bench/generator/README.md`, "Checklist for a new domain module", step 1 |
| The composition model (`Element`, `HtmlDocument`) | Yes | `bench/generator/html.py`, shared by `accessibility.py` and `usability.py` |
| The scoring resolver | Yes. It already maps the noun "field" to `input`, `select` and `textarea`, and resolves `#id`, tag, class and `:nth-of-type` | `bench/metrics/resolve_html.py`, `NOUN_TAGS` and `_SIMPLE_SELECTOR` |
| **A forms domain module** | **No: a new build** | `bench/generator/domains/forms.py` must supply vocabulary, composition, one injector per scripted criterion plus at least three judged, and at least three recipes, one of them clean. The two existing `html` modules are 632 and 859 lines |

So "reuse" removes new infrastructure, not new work. The corpus module is the largest single piece
of the build after the rubric itself. One constraint the resolver imposes on the rubric: a finding
locates by an element's `id`, tag, class or ordinal noun, so every scripted criterion should flag a
specific control rather than a region, and the domain module must give every control an `id` in
clean and seeded artifacts alike (the HTML invariant in `bench/README.md`).

## Ground three shipped skills already own

`critique-forms` reviews the same `html` artifacts as `critique-accessibility` and
`critique-usability`, and the same failure moments as `critique-microcopy`. Where one of them
already has a criterion, forms does not get a second one on the same test, because a duplicated
criterion scores the same defect twice in joint routing and splits the user's attention between two
reports saying one thing.

| Ground | Already owned by | So forms |
|---|---|---|
| A control has no label at all | `WCAG-3.3.2` (scripted) and `NNG-H6-LABELED` (scripted), whose own severity example is a form labelled only by placeholder text | does not test label presence |
| Error text identifies the item and the problem | `WCAG-3.3.1`, `NNG-H9-IDENTIFY`, and the `NNG-EM` set | does not test error-message content |
| Recovery after an error | `NNG-H9-RECOVER`, `NNG-EM-PRESERVE-INPUT` | does not test it |
| When validation fires | `NNG-EM-TIMING` (scripted) | does not test timing |
| Preventing a foreseeable wrong entry | `NNG-H5-PREVENT`, `NNG-EM-PREVENT` | tests only the form-specific mechanisms (input type, format tolerance), and cites the boundary |
| One action, one label, across a flow | `NNG-H4-CONTROL-NAMING` (scripted) | tests whether an action label is specific, not whether it is consistent |
| Custom controls expose name, role, value | `WCAG-4.1.2` | does not test it |

What is left is the structural ground Wroblewski's and Baymard's form research covers and none of
the three touches: input types and keyboards, autocomplete tokens, split and duplicated fields,
required and optional marking, field sizing, the action hierarchy, grouping, field count, and
layout. The proposed registry below stays inside it.

## Sources, read 2026-09-25

The rule this has to meet is `ROADMAP.md`'s: every criterion traces to a published source with a
URL or an ISBN. The template adds that `accessed` is the date the source was actually read, so a
source nobody could open does not count. Every source below was fetched and read on 2026-09-25.

**Baymard Institute, 17 freely readable articles.** Baymard's full guideline database is behind a
paid membership and is not used. Its public research articles are free and carry stable URLs.
`baymard.com/blog/<slug>` now redirects to `baymard.com/research-articles/<slug>`, so the build
cites the resolved form.

| Short handle | Article | Published |
|---|---|---|
| field-width | Form Field Usability: Matching User Expectations | 2010-08-31 |
| label-position | Field Label UX: Place Labels Above the Field | 2013-03-19 |
| inline-labels | Mobile Form Usability: Never Use Inline Labels | 2013-06-04 |
| form-design | Form Design: 6 Best Practices for Better E-Commerce UI | 2021-12-16 |
| single-input | Mobile Form Usability: Avoid Splitting Single Input Entities | 2013-02-12 |
| required-optional | Checkouts Need to Mark Both Required and Optional Fields Explicitly | 2018-10-02 |
| input-fields | 8 Recommendations for Creating Effective Input Fields | 2021-12-06 |
| inline-validation | Usability Testing of Inline Form Validation | 2024-01-09 |
| expiry-date | Format the "Expiration Date" Fields Exactly the Same as the Physical Card | 2023-10-03 |
| input-masking | Consider Using Localized Input Masks for "Phone" and Other Restricted Inputs | 2017-11-28 |
| address-lookup | Provide a "Fully Automatic Address Lookup" Feature | 2023-03-24 |
| card-spaces | The "Credit Card Number" Field Must Allow and Auto-Format Spaces | 2017-01-11, updated 2025-06-05 |
| field-count | Checkout Optimization: 5 Ways to Minimize Form Fields in Checkout | 2024-06-26 |
| address-line-2 | Form Usability: Getting "Address Line 2" Right | 2022-10-04 |
| phone-reason | Phone Number UX: Always Explain Why the "Phone Field" Is Required | 2020-03-16, updated 2025-07-29 |
| button-design | Button Design: Best Practices for Optimal UI Buttons | 2021-12-15 |
| password-rules | Avoid Unnecessarily Complex Password-Creation Requirements | 2022-11-29 |

**Luke Wroblewski, three free articles** at `lukew.com/ff/entry.asp?571` (primary and secondary
actions, 2007), `?504` (label alignment, 2007) and `?1000` (form input on mobile, 2010), plus
"Inline Validation in Web Forms", *A List Apart*, 2009-09-01.

**Wroblewski's book is verified but not read.** *Web Form Design: Filling in the Blanks*, Rosenfeld
Media, 2008, ISBN 978-1-933820-24-8, confirmed with its chapter list from the publisher's page.
Nobody in this session has read it, and the template's `accessed` field means read. It is listed
here as decision 1, not cited below.

**Figures are not trusted yet.** Several Baymard titles carry a percentage ("Only 14% Do So"). The
fetches passed through a summarizer, and one article's figure came back three different ways. Any
figure the build quotes must first be re-read verbatim. One criterion below does use a number, and
it was: `BAYMARD-CARD-NUMBER-FORMAT`'s 19 comes from the card-spaces article's own text, re-fetched
raw on 2026-09-25, which lists card-number lengths up to 19 digits (Maestro 12 to 19, UnionPay 16 to
19, Visa reserving 13 to 19). The article does not state a `maxlength` rule; deriving one from those
lengths is this draft's step, and the row says so.

**Not usable:** Baymard's article on confirming e-mail rather than password. Its URL now redirects
to the research index, not the article (decision 5).

## Proposed registry: 17 criteria, 12 scripted and 5 judged

Two namespaces, `BAYMARD` and `WROBLEWSKI`, following the `WILLIAMS` and `TOULMIN` precedent of
naming the source (decision 2). Both are `paraphrased` under
[ADR 0006](../../../decisions/0006-copyright-paraphrase-policy.md). The lean toward the scripted lane
is deliberate: forms is the domain N2 chose because much of it is checkable from markup, and the
scripted lane is the part of every shipped skill that measures precisely.

**What "scripted" rests on here, stated plainly.** Six of the twelve scripted rows (`INPUT-TYPE`,
`SPLIT-ENTITY`, `CARD-NUMBER-FORMAT`, `EXPIRY-FORMAT`, `PHONE-REASON`, `ADDRESS-LINE-2`) first have to
work out what a field is for, and they do it lexically, from its label, `name` or `id`. That is
deterministic, so it belongs in the scripted lane, but it is a heuristic. The generated corpus will
use vocabulary those heuristics recognise, so the benchmark will measure them favourably. **Their
false-positive and miss rate on real-world forms, with idiosyncratic names, is unmeasured**, and
that is the honest ceiling on "checkable from markup".

| ID | Lane | What it flags | Source | Boundary with a shipped skill |
|---|---|---|---|---|
| `WROBLEWSKI-INPUT-TYPE` | scripted | A text input whose label, `name` or `id` says e-mail, phone, URL or number, but whose `type` or `inputmode` does not match, so a phone shows the wrong keyboard | lukew ?1000; Baymard input-fields | Not `NNG-H5-PREVENT`: this tests the keyboard and input mechanism, not whether a wrong value is ruled out |
| `BAYMARD-SPLIT-ENTITY` | scripted | One data entity split across several inputs: a phone number in three boxes, a name in first and last where one field serves | Baymard single-input; field-count | None |
| `BAYMARD-REQUIRED-OPTIONAL` | scripted | A form mixing required and optional fields that does not mark both kinds in visible label text, or marks them only in a placeholder or a page-level legend | Baymard required-optional | `WCAG-3.3.2` as operationalized checks only that a label exists, not how requiredness is shown |
| `BAYMARD-PLACEHOLDER-INSTRUCTION` | scripted | A labelled field whose format instruction ("MM/YY", "name@example.com") exists only in its placeholder, which disappears once typing starts | Baymard inline-labels | `NNG-H6-LABELED` owns the field with no label at all; this is the labelled field whose instructions vanish |
| `BAYMARD-FIELD-WIDTH` | scripted | A fixed-length field (postcode, card security code, expiry) whose `size`, `maxlength` or inline width is far from the input it expects | Baymard field-width | None |
| `BAYMARD-CARD-NUMBER-FORMAT` | scripted | A card-number field whose `pattern` rejects spaces, or whose `maxlength` cannot hold the longest card numbers the source lists (19 digits, plus separators where spaces are allowed; the threshold is derived, not stated by the source) | Baymard card-spaces | None |
| `BAYMARD-EXPIRY-FORMAT` | scripted | A card-expiry control that does not follow the card's own MM/YY form: a four-digit year, or month names in place of numbers | Baymard expiry-date | None |
| `BAYMARD-PASSWORD-RULES` | scripted | A password field whose `pattern` forces character-class composition, or whose `maxlength` is unnecessarily low | Baymard password-rules | None |
| `BAYMARD-FORMAT-TOLERANCE` | scripted | A phone or similar field whose `pattern` rejects harmless formatting characters (spaces, dashes, parentheses) | Baymard input-masking; input-fields | **The one real tension**: `NNG-H5-PREVENT` asks for constraint. This flags rejecting input that carries no error, not the presence of constraint (decision 6) |
| `BAYMARD-PHONE-REASON` | scripted | A required phone field with no adjacent or `aria-describedby` text saying why the number is needed | Baymard phone-reason | None |
| `BAYMARD-ADDRESS-LINE-2` | scripted | An "address line 2" field not marked optional | Baymard address-line-2 | None |
| `BAYMARD-ACTION-LABEL` | scripted | A submit control labelled with a generic word from a fixed set ("Submit", "Continue", "OK", "Go") rather than what happens next | Baymard button-design | `NNG-H4-CONTROL-NAMING` owns consistency of one action's label across a flow; this is specificity within one form |
| `WROBLEWSKI-ACTION-HIERARCHY` | judged | Primary and secondary actions presented as visual twins, or a secondary action (Cancel, Reset) as prominent as the primary one | lukew ?571 | None |
| `WROBLEWSKI-LABEL-ALIGNMENT` | judged | Label alignment that works against the form: labels positioned so they detach from or hide their fields, or an alignment that suits neither a short familiar form nor a long unfamiliar one | lukew ?504; Baymard label-position | None |
| `BAYMARD-FIELD-COUNT` | judged | Fields the task does not need, or that could be deferred or revealed on demand | Baymard field-count | None |
| `BAYMARD-SINGLE-COLUMN` | judged | Fields laid out in several columns so the completion order is ambiguous | Baymard form-design | None |
| `BAYMARD-OPTION-CONTROL` | judged | A short set of options hidden in a dropdown where visible radio buttons would show every choice at once | Baymard form-design; lukew ?1000 | None |

**Deliberately left out:**
- Label presence (`WCAG-3.3.2`, `NNG-H6-LABELED`).
- Error content, timing and recovery (`WCAG-3.3.1`, `NNG-H9-*`, `NNG-EM-*`). Baymard's
  inline-validation research and Wroblewski's *A List Apart* study are read and cited only as
  background for that boundary.
- Automatic address lookup, which needs a live address database to test.
- `autocomplete` tokens and confirmation fields, for want of a readable source (decisions 4 and 5).

## Downstream of the registry, once ruled

- **Lane balance sets the corpus.** `bench/generator/domains/forms.py` needs an injector for each
  of the 12 scripted criteria and at least three of the judged, and at least three recipes with one
  clean. The payment criteria (card number, expiry, address line 2, phone reason) mean at least one
  recipe must be a checkout form.
- **Routing, using the E30 checklist step.** Three contested pairs: forms with accessibility and
  with usability (same artifact type), and forms with microcopy (the same failure moments). Each
  needs a boundary clause in both descriptions, so three shipped skills' descriptions change, and
  their U5 scores are re-run with them. The microcopy pair is contested even though forms stays out
  of error content: a user holding a form full of validation errors could reasonably ask for either
  skill, and the four `NNG-EM` criteria in the ownership table above are microcopy's. The two
  descriptions have to route that request to one of them.
- **The `askit-build-skill` mandate** ([E11](../../../backlog/enhancements.md)) is the outer loop
  of the build, in fallback mode, reading its `SKILL.md` from the sibling checkout. Its step 6
  grades with the sibling's `evaluate.mjs` against Standard 0.16, not the pinned 0.12 (E62), so
  conformance is judged with this repo's `node scripts/check.mjs`. Every place its procedure does
  not fit a critique skill is a friction finding for the toolkit's backlog, logged from the first
  step.
- **Measurement is a paid stop.** k=5 on both pinned tiers is two dispatches of 40 cells each, and
  needs the maintainer's go-ahead when the build reaches it.

## Decisions for the maintainer

**Rulings, 2026-09-25.** The maintainer answered all six the same day:

| # | Ruling | Consequence for this draft |
|---|---|---|
| 1 | **Expand the research base**: read Wroblewski's book from the maintainer's library, add Adam Silver's *Form Design Patterns* and other local books, and search for current sources, with copies kept as a local record | A second research pass is under way (see "Research pass 2" below). The registry is revised from its results, not from this draft's 21 sources alone |
| 2 | Leaning toward one `FORMS-` namespace, not firmly | Re-decided after pass 2. If most criteria end up backed by several sources, a namespace named after one source is arbitrary, which favours `FORMS-` with attribution carried in `rubric_sources` (the template allows a namespace that differs from the rubric id) |
| 3 | **Checkout becomes its own skill** with its own large research base | Filed as [N5 (critique-checkout)](../../../backlog/new-components.md). The two card-specific criteria move there. Address line 2 and phone reason stay here, since they apply to any address or phone field |
| 4 | **Keep `autocomplete` in forms (option B)**: autofill is tied to conversion, which is what form design is for | Added back, and pass 2 looks specifically for conversion and completion evidence on autofill |
| 5 | **Try the Internet Archive, and broaden the sources**, favouring recent, mobile-first, and quantified work (large A/B tests and studies) | Pass 2 targets exactly that and grades every source's evidence |
| 6 | **Keep both** `BAYMARD-FORMAT-TOLERANCE` and `NNG-H5-PREVENT` with the stated boundary | Settled: harmless variation is accepted and normalized; actually wrong input is prevented |

**Research pass 2**, started 2026-09-25: five agents read Wroblewski's book, Silver's book and four
saved articles, other mobile and UX books in the library, current mobile-first web guidance
(web.dev, GOV.UK, NN/g, platform guidelines), and quantified studies (peer-reviewed papers,
form-analytics benchmarks, A/B tests). Every figure must be copied verbatim from a saved copy.
Copies live under `_local/research/critique-forms/` (gitignored), with a manifest recording each
source's URL or ISBN, access date and checksum.

The original decision text follows, kept as asked.

1. **Wroblewski's book.** It is not cited because nobody read it, and the template's `accessed`
   field means read. What its contents would source is unknown, not assumed: from their titles alone,
   chapters 2 (Form Organization) and 4 to 6 (Labels, Input Fields, Actions) look relevant. The
   question is whether the maintainer has a copy and wants the ground those chapters may cover,
   grouping in particular, which nothing read so far sources. Built from the free articles alone, as
   drafted, the registry has no grouping criterion.
2. **Namespaces.** `BAYMARD` and `WROBLEWSKI`, registered in `docs/reference/criterion-ids.md`, or
   shorter handles. IDs are permanent once shipped.
3. **Registry size and scope.** 17 criteria, four of them payment-specific. Keeping the four pulls
   forms toward checkout; dropping them leaves 13 criteria, 8 scripted.
4. **`autocomplete`.** No dedicated free Baymard or Wroblewski source was found. It could be sourced
   to the WHATWG HTML autofill specification (an open standard) as an `open-standard` rubric, but
   that is a third source for one criterion. Recommendation: leave it out of v1.
5. **Confirmation fields** (confirm e-mail, confirm password). The one source no longer resolves. It
   stays out unless an archived copy is read.
6. **`BAYMARD-FORMAT-TOLERANCE` against `NNG-H5-PREVENT`.** The two pull in opposite directions on
   the same field. The draft keeps both and draws the line at rejecting input that carries no error.
   The alternative is to drop the forms criterion and let usability own format handling.
