# Severity anchors

This skill's own domain-anchor prose, extending
[`docs/reference/severity-scale.md`](../../../docs/reference/severity-scale.md)'s Domain anchors
section for the docs domain. Artifact type: technical documentation pages and page trees written in
markdown, spanning all four Diataxis modes (tutorial, how-to, reference, explanation) plus the
tree-level navigation and linking structure that spans pages.

Severity is assigned by weighing impact first, then frequency, then persistence, exactly as
`docs/reference/severity-scale.md` specifies; the anchors below calibrate that weighing across this
skill's nine DIATAXIS-* criteria and are not a substitute for the per-criterion anchors already
carried in [`references/DIATAXIS.md`](DIATAXIS.md).

## Impact sets the level

A single passage that leans toward a neighboring mode, without derailing the reader's task, caps a
finding at severity 2: DIATAXIS-MODE's single stray marker, DIATAXIS-HOWTO-GOAL's one extra
definition, DIATAXIS-REFERENCE-NEUTRAL's one editorial aside, and DIATAXIS-EXPLANATION-CONTEXT's one
short how-to list all share this shape. The reader notices the lapse and keeps going; nothing about it
blocks the task the page exists for.

A finding rises to severity 3 when the mode failure or structural gap actually blocks the reader's
task rather than merely interrupting it: a tutorial a learner cannot follow straight through, a how-to
padded with unrelated tasks a reader must wade through, a reference page a reader cannot navigate by
its own structure, or a page the tree's own navigation provides no path to at all.

DIATAXIS-ORPHAN and DIATAXIS-CROSSLINK need their own discriminator, because the obvious one does not
work. Every page in every tree is reachable by search or by a URL someone pastes into a chat, so
"could a determined reader still get there" separates nothing and two reviewers applying it would
land wherever their optimism about readers put them. The discriminator is what the unreachable page
carries, not how a reader might route around its absence: severity 3 when the page sits on the
critical path of a task the tree exists to support, so a reader working through the tree's own
navigation is stopped, and severity 2 when the page covers an edge case a reader reaches only after
already succeeding at the main task. The criteria table's own two anchors in
[`references/DIATAXIS.md`](DIATAXIS.md) are exactly that pair: a prerequisite step every new user
must complete against a single edge-case parameter entry.

## Frequency and persistence pull within the range impact sets

A mode lapse (DIATAXIS-MODE) that happens twice or more on one page reads as the page's own habitual
register rather than a slip, and it compounds: each recurrence costs the reader's task-focus again
rather than resolving once the reader passes it. That recurrence is what distinguishes a severity-2
single-instance lapse from a severity-3 habitual one for the same criterion, never frequency judged
alone. DIATAXIS-HEADING-DEPTH turns on the same count for the same reason. Two is the line rather
than some larger share of the page because two is where a reader stops reading the lapse as an
accident, and because it is a count a reviewer and `scripts/checks.py` can reach the same verdict on;
`references/DIATAXIS.md`, "Recurrence-based severity", states it as the operative rule for both
criteria and both severity-3 anchors are written to it. The same logic applies to
DIATAXIS-NAV-LENGTH by size rather than by count: a listing a few items past the threshold is a minor
severity-2 case, while a listing many times past it, with no subgrouping anywhere, persists as a
navigation obstacle for as long as the reader keeps using that listing.

## Clean is not a special case

Not every page or tree this skill critiques carries a defect. A tutorial that never pauses its action
sequence, a reference page organized exactly like the thing it describes, and a tree where every page
both links out to its complementary modes and is linked in from somewhere else, together describe a
clean pass on all nine criteria, and a critique that reports zero findings on such a tree is not a bug
to explain away.
