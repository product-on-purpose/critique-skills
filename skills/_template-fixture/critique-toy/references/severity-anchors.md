# Severity anchors

This skill's own domain-anchor prose, extending `docs/reference/severity-scale.md`'s "Domain anchors"
section for the toy fixture domain. Artifact type: short markdown-prose field-operations notices,
composed entirely from the toy grammar's own closed vocabulary (`bench/generator/domains/toy.py`).

Severity is assigned by weighing impact first, then frequency, then persistence, exactly as
`docs/reference/severity-scale.md` specifies; the anchors below calibrate that weighing for this
fixture's three criteria and are not a substitute for the per-criterion anchors already carried in
`references/TOY.md`.

## Impact sets the level

A single passive recast (TOY-ACTIVE) or a single stacked hedge (TOY-HEDGE) never blocks a reader from
recovering the intended meaning; the actor or the qualification is missing, but the sentence still
parses and the surrounding paragraphs supply enough context to guess correctly. That caps both
criteria at severity 2 on a single occurrence, matching the toy domain's own recipes, which plant
every TOY-ACTIVE and TOY-HEDGE defect at `severity_expected: 2`.

An orphan subheading (TOY-ORPHAN) is a structural promise the document breaks: a reader who navigates
by headings expects content under the heading they just followed and finds none. That is a worse
failure mode than a single confusing sentence, which is why the toy domain's own recipe plants
TOY-ORPHAN at `severity_expected: 3` rather than 2.

## Frequency and persistence pull within the range impact set

A hedge or a passive recast that recurs across every paragraph of a section reads as the document's own
voice rather than a slip, and it compounds: each new instance costs the reader trust or clarity again
rather than resolving the moment the reader moves past it. That pattern of recurrence is what would
justify raising either criterion above the single-instance anchor in `references/TOY.md`, never
frequency alone divorced from impact.

## Clean is not a special case

Not every artifact this skill critiques carries a defect; the toy domain's own `toy-003` recipe plants
nothing (`plants=()`), on purpose, so a scripted lane that reports zero findings on a genuinely clean
artifact is not a bug to explain away.
