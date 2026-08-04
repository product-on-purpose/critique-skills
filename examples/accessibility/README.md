---
title: Worked example, critique-accessibility
description: A failing dashboard page, the scripted-lane command that catches most of it, and a filled-in disposition log
audience: both
level: beginner
---

# Worked example: critique-accessibility

This walks through one complete pass of `critique-accessibility` against a real (if fictional)
HTML page: what the tool actually outputs, what each finding means in plain language, and how a
human reviewer disposed of each one. It exists so a PM, designer, or writer can decide whether to
trust this skill before running it on their own work.

**Honesty labeling, up front, because this matters more than anything else on this page:**

- The **scripted-lane command** below is bit for bit reproducible. Run it yourself against
  `artifact.html` in this folder and you will get the same findings shown here (the only fields
  that differ are the run's own timestamp and the artifact path it was pointed at, neither of
  which is a finding). This is the part of the example you don't have to take on faith.
- **`envelope.json`** is a verbatim copy of a validated golden fixture: a human-checked "this is
  the correct output" reference the skill's own test suite is calibrated against, not a live model
  run. It represents the full critique (scripted lane plus a judged lane swept by a reviewer or the
  `critique-critic` subagent), not only the scripted lane. As it happens, every finding in it is
  scripted, because this particular fixture was deliberately built clean on the nine judged
  criteria, so its full, correct output and its scripted-lane output are the same six findings.
  That is stated plainly below, not left for you to discover.
- The **findings tour** and the **disposition log** are curated illustration: plain-language
  commentary and a worked example of the human decision step, written for this walkthrough. Neither
  is a live run transcript.

## The artifact

`artifact.html` in this folder is a verbatim copy of
[`skills/critique-accessibility/examples/artifacts/golden-04.html`](../../skills/critique-accessibility/examples/artifacts/golden-04.html),
one of this skill's own golden fixtures. It is a small internal dashboard, "Storm response
dashboard": a header with two navigation links, a promo banner, a status update, and a refresh
button. Nothing in it is exotic; every problem below is the kind of thing that ships in an
ordinary sprint.

## Running the scripted lane yourself

From the repository root:

```
python skills/critique-accessibility/scripts/checks.py examples/accessibility/artifact.html
```

This is the deterministic half of the skill: thirteen mechanical checks (`checks.scripted` in
[`SKILL.md`](../../skills/critique-accessibility/SKILL.md)) run directly against the markup and
declared CSS as text, no model call involved. We ran this exact command against this exact file
before writing this page. It produced six findings and a failing gate, matching `envelope.json`
in this folder finding for finding: same IDs, criteria, severities, locations, evidence, and
fixes. The only differences were `run.artifact` (it echoed the path we pointed it at) and
`run.timestamp` (the moment we ran it), neither of which is a finding. Reproduce it and compare
for yourself; that comparison is the whole point of shipping the command alongside the output.

## Running the full critique

The scripted lane alone only covers part of the rubric. To get the full critique, which also
sweeps the nine judged criteria a script cannot check mechanically (things like whether a heading
actually describes its section, or whether an error message is specific enough), ask Claude Code
to run it in natural language, in a session with this repository open:

> Critique `examples/accessibility/artifact.html` with critique-accessibility.

Claude Code delegates that to the `critique-critic` subagent (`SKILL.md`, "Delegation"), which
runs the full four-pass protocol, scripted lane and judged lane both, in a clean context that has
never seen this page being written, and returns one contract-valid run envelope. For this
particular artifact, per the validated golden fixture, the judged lane turns up nothing that
clears the reporting bar, so a full run's findings match the six scripted-lane findings below. A
different artifact would not necessarily be that clean on the judged side; see
[`skills/critique-accessibility/examples/golden-05.json`](../../skills/critique-accessibility/examples/golden-05.json)
for a fixture that is clean on every scripted check and carries judged-only findings instead.

## Findings tour

Five of the six findings, picked to cover the range: all three severity-3 findings (the ones that
fail the release gate on their own) and two of the three severity-2 findings, chosen because they
show two different failure shapes (a color problem and a layout problem) rather than two similar
ones. The sixth, `F-004`, is a fixed-width promo banner that forces horizontal scrolling on a
narrow screen; it is real and it is in the disposition log below, just not walked through here in
depth, to keep this tour to a size someone will actually read.

### F-001, the page blocks browser zoom (WCAG-1.4.4, severity 3)

**What you'd see:** on a phone or with a low-vision browser zoom setting, pinch-to-zoom simply
does nothing on this page.

**Why it's a violation:** the page's viewport meta tag carries `user-scalable=no`. WCAG-1.4.4
requires that a reader can enlarge text up to 200 percent using the browser's own zoom without the
page blocking it. This is graded by which branch fired, not by how often; disabling zoom outright
is the severity-3 branch, a zoom cap that still allows some enlargement would have been severity 2
([`references/severity-anchors.md`](../../skills/critique-accessibility/references/severity-anchors.md),
"Criteria that fire at most once per page").

**What the fix means:** remove `user-scalable=no` from the meta tag. One line, no redesign.

**What severity 3 signals:** major, fix before release, per
[the severity scale](../../docs/reference/severity-scale.md). It is not the worst thing on the
scale (that's 4, catastrophic), but by default it fails the gate and blocks a release.

### F-002, no way to skip the header (WCAG-2.4.1, severity 3)

**What you'd see:** nothing visually. A sighted mouse user never notices. Tab through the page
with a keyboard and you land on both navigation links before you ever reach the dashboard's actual
content.

**Why it's a violation:** the page has neither a `<main>` landmark nor a skip link, and two
focusable elements sit ahead of the first heading. WCAG-2.4.1 exists so a reader has some way past
repeated header content. This is again graded by branch: one stray focusable element ahead of
content would be severity 2, a whole navigation block ahead of it is severity 3.

**What the fix means:** wrap the dashboard's actual content in a `<main>` element, or add a skip
link as the first focusable thing on the page.

**What severity 3 signals:** same as above, major and gate-failing. This one compounds: it costs
every keyboard user two extra tab presses on every single page load, not once.

### F-003, the page's language tag is nonsense (WCAG-3.1.1, severity 3)

**What you'd see:** nothing visually again. A screen reader, or a translation tool, would try to
read or translate the page using whatever fallback language it defaults to, because it cannot
parse the one the page claims.

**Why it's a violation:** `<html lang="englandshire">`. That is not a real BCP 47 language tag
(the real one would be `en`, `en-GB`, and so on). WCAG-3.1.1 requires the page's language be
identified so assistive technology picks the right pronunciation and voice. No element inside the
page supplies a usable one either, so the failure covers the whole page, which is the severity-3
branch.

**What the fix means:** change `lang="englandshire"` to `lang="en"`.

**What severity 3 signals:** major and gate-failing, same as the two above. Three separate
severity-3 findings is why this run's gate reads fail, not pass.

### F-005, a button's border is too faint to see (WCAG-1.4.11, severity 2)

**What you'd see:** the "Refresh status" button's outline is there, technically, but it is hard to
make out against the white background, especially for anyone with low vision.

**Why it's a violation:** the border color `#a8a8a8` against a `#ffffff` background resolves to a
2.38:1 contrast ratio. WCAG-1.4.11 requires interactive component boundaries to hit at least 3:1.
The scale here runs on the ratio itself: 2:1 up to 3:1 is severity 2, under 2:1 (where the boundary
stops being locatable at all, not just faint) is severity 3.

**What the fix means:** darken the border color, or change the background it sits against, until
the ratio clears 3:1.

**What severity 2 signals:** minor, goes to the backlog rather than blocking release. Real, worth
fixing, not urgent enough to hold a launch for on its own.

### F-006, a status message can get clipped (WCAG-1.4.12, severity 2)

**What you'd see:** nothing, under normal settings. If a reader applies wider line spacing or
letter spacing (an accessibility setting some people rely on permanently), the status box's text
could get cut off, because the box has a fixed 60px height and `overflow: hidden`.

**Why it's a violation:** WCAG-1.4.12 requires that no content gets lost when a reader overrides
spacing up to the standard's minimums. A fixed height paired with clipped overflow on a text
container is exactly the pattern that breaks that. One instance of this pattern is severity 2;
two or more elsewhere on the same page would escalate to severity 3.

**What the fix means:** drop the fixed height so the box grows with its content, or change
`overflow: hidden` to `visible` or `auto`.

**What severity 2 signals:** same as F-005, minor and backlogged, not blocking. Whether it is
actually a live risk depends on what content the box actually renders, which is exactly what the
disposition below argues.

## Disposition log

The full log is in [`dispositions.json`](dispositions.json) in this folder, schema-valid
(`python -m contract.validate dispositions.json` reports `valid`, and its `finding_id` values all
resolve against `envelope.json`). This is curated illustration, one reviewer's plausible call on
each finding, not a record of a real incident. It is deliberately not all accepts: real review
means some findings get pushed back on or pushed out, and a log where everything is accepted
without question is not a log anyone should trust.

| Finding | Criterion | Disposition | Why |
|---|---|---|---|
| F-001 | WCAG-1.4.4 | accept | Confirmed on the rendered page; removing `user-scalable=no` is a one-line fix, shipping next deploy. |
| F-002 | WCAG-2.4.1 | accept | Confirmed with a keyboard; wrapping the content in `<main>` is a small template change. |
| F-003 | WCAG-3.1.1 | accept | `englandshire` is a leftover placeholder, not an intentional value. Fixing to `en`. |
| F-004 | WCAG-1.4.10 | defer | Real, but the promo banner is already being replaced by a responsive card component next sprint. Tracked against that rework instead of patched separately. |
| F-005 | WCAG-1.4.11 | accept | Confirmed at 2.38:1; darkening the border to the design system's standard token clears it. |
| F-006 | WCAG-1.4.12 | reject | This status box's content is generated server side and truncated to one short line before render, so the wrap-and-clip scenario this finding describes cannot happen with the content it actually shows. Revisit if the truncation limit changes. |

The reject on F-006 is worth sitting with for a second: the finding is not wrong about what the
markup allows, it is a judgment call about what content actually reaches that markup in practice.
That is exactly the kind of call the disposition step exists for
([`docs/how-to/dispositions.md`](../../docs/how-to/dispositions.md)); the schema and validator can
check that the log is well-formed and that its finding IDs resolve, but whether F-006's reject
holds up is a call only a human accountable for the artifact can make, and it is one a stricter
reviewer might reasonably have made the other way.

## Files in this folder

- `README.md`, this walkthrough.
- `artifact.html`, a verbatim copy of
  [`skills/critique-accessibility/examples/artifacts/golden-04.html`](../../skills/critique-accessibility/examples/artifacts/golden-04.html).
- `envelope.json`, a verbatim copy of the `expected_envelope` object from
  [`skills/critique-accessibility/examples/golden-04.json`](../../skills/critique-accessibility/examples/golden-04.json),
  validated with `python -m contract.validate envelope.json` (`valid`).
- `dispositions.json`, the disposition log tabulated above, validated the same way and resolved
  against `envelope.json`.

## See also

- [`skills/critique-accessibility/SKILL.md`](../../skills/critique-accessibility/SKILL.md), the
  skill's own run protocol.
- [`docs/reference/severity-scale.md`](../../docs/reference/severity-scale.md), the 0-4 scale
  cited above.
- [`docs/how-to/dispositions.md`](../../docs/how-to/dispositions.md), the disposition log format
  and why it exists.
