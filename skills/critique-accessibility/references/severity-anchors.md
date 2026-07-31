# Severity anchors

This skill's own domain-anchor prose, extending `docs/reference/severity-scale.md`'s "Domain anchors"
section for accessibility. Artifact type: HTML pages and fragments, markdown where mappable, evaluated
as static markup and declared CSS, never as a rendered or live-interacted page.

Severity is assigned by weighing impact first, then frequency, then persistence, exactly as
`docs/reference/severity-scale.md` specifies. The anchors below calibrate that weighing across the
domain as a whole; the per-criterion severity 2 and severity 3 anchors already carried in
`references/WCAG.md` are the authoritative anchors for any single criterion. Nothing here restates
WCAG's own criterion text; all examples are original.

## Impact sets the level, and impact in accessibility means recoverability

The question that sets severity first is not how the page looks but what a reader who depends on the
missing signal can still do. A sighted mouse user never notices a missing skip link; a keyboard-only
user tabs through it every time. That asymmetry, not the defect's visual size, is what impact measures
here.

A defect that costs an assistive-technology user extra effort but still lets them complete the task
caps at severity 2: a decorative icon with noisy alt text, a link whose purpose takes one extra look at
surrounding text to confirm, a focus outline that is present but faint. A defect that removes the
user's ability to complete the task at all, or forces them to guess with no way to confirm the guess,
reaches severity 3: body text below the contrast minimum across a page whose whole purpose is reading,
a form section with no labels on any of its fields, a modal that traps focus with no way out. Severity
4 is reserved for defects that make the artifact fully non-functional for a whole class of user, such
as a page with no way to reach its content at all without a mouse; none of this skill's 22 criteria are
anchored at severity 4 by default; a 4 is a finding-level judgment about a specific artifact, not a
property of a criterion.

## Frequency and persistence pull within the range impact set

A single missing alt attribute on one decorative icon and the same missing alt attribute repeated
across every image in a photo gallery are the same defect by impact, but not the same severity: the
gallery case recurs across every instance a reader encounters, so the reader never gets a moment of
relief from it. That recurrence is what pulls a severity 2 anchor toward 3 within a single criterion,
never frequency by itself divorced from what the defect actually costs the reader when it happens once.

Persistence works the same way across a page rather than within one instance. A single ambiguous
instruction a reader misreads once and then self-corrects persists for one moment; a mislabeled control
in a multi-step flow persists for the rest of the flow, because every subsequent step is now built on a
reader's incorrect understanding of what that control does. The second case is worse at the same
frequency, because its effect compounds rather than resolving where it occurred.

## Scripted and judged findings are calibrated on the same scale

A scripted-lane finding (a contrast ratio computed from resolved colors, a missing lang attribute) and
a judged-lane finding (an instruction relying on sensory characteristics, a heading that fails to
describe its section) are assigned severity by the identical weighing order. Confidence, not severity,
is where the lane distinction shows up in a finding: a scripted check reports high confidence by
construction, while a judged check's confidence reflects how much interpretation the call required.
Severity itself never gets inflated or discounted because of which lane produced the finding.

## Thresholds the scripted lane applies

The per-criterion anchors in `references/WCAG.md` describe two calibrated points; a real artifact
lands between them constantly, and two reviewers who each interpolate by feel will disagree. The
boundaries `scripts/checks.py` actually applies are listed here so a judged-lane reviewer, or anyone
re-deriving a severity by hand, grades the same defect the same way the script does. Each one is the
mechanical reading of that criterion's own two anchor rows, not an independent policy.

- **Recurrence, for the criteria whose two anchors differ in how many places the defect appears**
  (WCAG-1.1.1, the heading-skip half of WCAG-1.3.1, WCAG-1.4.12, WCAG-2.4.4, WCAG-2.5.3,
  WCAG-3.3.2): one instance in the artifact is severity 2, two or more is severity 3, and every
  instance in a run carries the escalated value rather than only the second one onward. The reader
  never gets relief from a defect that recurs, which is the calibration in "Frequency and persistence"
  above.
- **Text contrast (WCAG-1.4.3)**: below the applicable minimum by less than a full point of ratio is
  severity 2; a full point or more below it is severity 3. The applicable minimum is 3:1 for
  large-scale text (at least 24px, or at least 18.66px when the resolved weight is 700 or more) and
  4.5:1 otherwise.
- **Component-boundary contrast (WCAG-1.4.11)**: a ratio of at least 2:1 but under the 3:1 minimum is
  severity 2; under 2:1 is severity 3, the point at which a boundary stops being locatable rather than
  merely faint.
- **Reflow (WCAG-1.4.10)**: a fixed width of 600px or more is severity 3, below that severity 2. The
  pixel width stands in for how much of the page the reader has to scroll past horizontally, which is
  what separates the banner and body-wrapper anchor rows.
- **Criteria that fire at most once per page** (WCAG-1.4.4, WCAG-2.4.1, WCAG-2.4.2, WCAG-3.1.1) are
  not gradable by recurrence, so each is graded by which branch of its condition fired: a partial
  zoom cap rather than a total block, one focusable element ahead of the content rather than a whole
  navigation block, a placeholder title rather than none at all, a lang declaration surviving on a
  subtree rather than nowhere. In every case the lesser branch is severity 2 and the total one is
  severity 3, matching that criterion's anchor rows.
- **Table header association (the second half of WCAG-1.3.1)** is severity 3 whenever it fires: an
  unmarked multi-row, multi-column table is a single structural failure covering every cell in it at
  once, so there is no lesser branch to grade.

A judged-lane finding has no equivalent table, by construction: its severity comes from the weighing
order applied to that criterion's own two anchor rows. What the list above prevents is the opposite
failure, a scripted finding and a judged finding on comparable defects landing at different levels
because only one of them had a stated boundary.

## Clean is not a special case

Not every page or fragment this skill critiques carries a defect. A page with a proper landmark
structure, sufficient contrast throughout, descriptive link text, and labeled form controls produces a
run with zero findings, and a scripted lane that reports nothing on a genuinely clean artifact is
correct output, not a check that failed to run.
