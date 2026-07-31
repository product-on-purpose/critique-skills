# DIATAXIS rubric source

Diataxis (Daniele Procida, 2020-) is the sole rubric source for `critique-docs`. It identifies four
distinct reader needs and four corresponding documentation forms: tutorials (learning-oriented),
how-to guides (task-oriented), reference (information-oriented), and explanation
(understanding-oriented), organized on two axes: action versus cognition (what a reader does versus
what a reader knows), and acquisition versus application (the difference between study and work). A
warning recurs across several of the framework's own pages: blurring the boundary between adjacent
forms, tutorial into how-to, reference into explanation, degrades both sides of the blur at once. That
warning is the throughline connecting most of the criteria below.

## Source

| Field | Value |
|---|---|
| `id` | `DIATAXIS` |
| `citation` | Diataxis (Daniele Procida, 2020-) |
| `url` | https://diataxis.fr/ |
| `accessed` | 2026-07-31 |
| `operationalization` | `open-standard` |

Diataxis is openly published (the site states a CC-BY-SA 4.0 license) and cited directly by canonical
URL, matching [ADR 0006](../../../docs/internal/decisions/0006-copyright-paraphrase-policy.md)'s
`open-standard` treatment for WCAG and Diataxis alike; no ISBN or page range applies. Per-criterion
citations below point at the specific page on diataxis.fr the criterion draws from, for traceability;
`rubric_sources` in `SKILL.md` cites the root URL.

## Criteria

Nine criteria, six judged and three scripted, satisfying the eight-criterion minimum
([S-05 (skills-slate) AC-2](../../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md))
without padding. Listed in ascending ID order, the order the four-pass protocol's criterion sweep
walks them in. `DIATAXIS-ORPHAN` was drafted as scripted and moved to judged once `scripts/checks.py`
was implemented; see "Why DIATAXIS-ORPHAN moved to the judged lane" below.

| ID | Operationalization | Operational test | Severity 2 anchor | Severity 3 anchor | Lane | Lane rationale |
|---|---|---|---|---|---|---|
| DIATAXIS-CROSSLINK | A page links outward to the page in the complementary Diataxis mode that a reader moving through the learn, apply, consult, and reflect cycle would need next for the same subject, rather than leaving the reader with no path out of the page's own mode. | Identify whether the page's subject has an existing counterpart page in a complementary mode elsewhere in the tree (a how-to's command has a reference entry, a tutorial's workflow has an explanation of why it works, an explanation's concept has a how-to for applying it); flag a violation when that counterpart exists in the tree and the page carries no link to it. | A how-to page's one step relies on a command that has its own reference entry elsewhere in the tree, and the how-to page never links to that entry, though a reader can still find the command by searching the reference section directly. | A tutorial walks a learner through an entire workflow start to finish and links to nothing else in the tree, so a learner who wants to understand why any step works, or look up a command afterward, has no link from the page that just taught it to them. | judged | Deciding which complementary-mode page a given page's subject actually needs, and whether an existing link already satisfies that need, requires understanding what both pages cover, not a pattern match. |
| DIATAXIS-EXPLANATION-CONTEXT | An explanation page discusses background, reasoning, and how a topic connects to the wider system, written for a reader consulting it away from active work, and its content does not shift into an imperative sequence of steps a reader is meant to carry out. | Read the page's content as a whole; flag a violation where a stretch of the page changes from discursive background or rationale into an ordered, imperative sequence of actions a reader would follow while working rather than while thinking. | An explanation page about why a system is structured a certain way includes one short numbered list showing how to apply that structure, set among otherwise discursive paragraphs. | A page filed as an explanation of a design's reasoning is, for most of its length, a numbered sequence of imperative steps rather than discussion, so a reader consulting it for background is handed instructions instead. | judged | Whether a stretch of prose is still discursive background or has become an executable procedure is a matter of the page's overall register, which needs the whole page read together to decide. |
| DIATAXIS-HEADING-DEPTH | A page's headings descend one level at a time from its title, so a heading is never nested more than one level deeper than the heading immediately before it. | Parse the page's heading sequence in document order by level number; flag a violation at any heading whose level exceeds the immediately preceding heading's level by more than one. | A page jumps once from a level-2 heading straight to a level-4 heading in a single subsection, while the rest of its heading structure descends in order. | A page skips a heading level two or more times, so the skipping reads as the page's own habitual structure rather than one slip, and a reader or a tool relying on heading level to infer nesting cannot reconstruct which sections belong under which. | scripted | Heading levels are numbers a parser reads directly from the page; whether one exceeds the previous by more than one is arithmetic, not judgment. |
| DIATAXIS-HOWTO-GOAL | A how-to page carries a reader who already has working competence through exactly the steps one concrete, real-world task requires, without re-teaching a concept the reader is assumed to know or widening into other tasks the reader did not ask for. | Identify the one task the page names as its goal; flag a violation where the page's content either explains a concept a competent reader would already have, or carries the reader through a second task beyond the one named. | A how-to page for changing one setting includes one paragraph defining a basic term that any reader capable of finding the setting would already know. | A how-to page framed around one task instead walks through three loosely related tasks in sequence, so a reader who needs only the first has to read and discard the other two to find their own step. | judged | Deciding what a competent reader can be assumed to already know, and whether added content genuinely serves the one named task, is a judgment about audience and scope, not a fixed pattern. |
| DIATAXIS-MODE | A page's sentences stay inside the register its declared mode uses (imperative and action-first for tutorial and how-to pages, neutral and descriptive for reference pages, discursive for explanation pages), and no sentence on the page opens with a fixed lexical marker drawn from a different mode's register. | Read the page's declared mode from its frontmatter, then test the opening of every sentence in every paragraph and every list item against the closed marker lexicons in Marker registry and thresholds below; flag a violation at any sentence whose opening matches a marker foreign to that declared mode. The match is sentence-initial and at a word boundary, so a marker occurring anywhere later in a sentence is never a violation of this criterion, and a page with no declared mode, or a mode value outside the closed set, yields no finding for this criterion at all. | A how-to page's step list contains one sentence opening with a because-clause, a single explanation-mode marker, surrounded on both sides by otherwise pure instruction. | A reference page opens two or more of its entries with an imperative first, then, next sequencing marker, so the how-to register recurs on the page rather than appearing once and the page reads as habitually instructional rather than descriptive. | scripted | Matches a closed, fixed list of lexical markers at the start of each sentence; no reading of the page as a whole is needed to find them. |
| DIATAXIS-NAV-LENGTH | Every listing on a page stays short enough for a reader to scan it in one glance, split into named subgroups once it would otherwise grow past a small, fixed item count. The guidance behind this is aimed at navigation and index listings, and the criterion holds every listing to it, because a listing a reader navigates by and a listing that is page content are not separable by any fixed pattern. | Count the top-level items in each list block on the page, navigation or otherwise; flag a violation for any block exceeding seven top-level items that carries no subgrouping, meaning no nested items beneath it and no sub-heading breaking the run into named groups (a run split by a sub-heading parses as two blocks and is counted separately). Whether a flagged listing is one a reader actually navigates by is weighed at severity assignment, not at detection. | An index listing runs to nine flat items, two past the threshold, and the items are still short enough that a reader can scan the whole list without much effort. | A navigation listing runs to more than twenty flat items with no subgrouping at all, so a reader has to read the entire list top to bottom to find any one item. | scripted | Counting top-level items in a list block and checking for nested items is arithmetic and structure detection; the one judgment this criterion needs, whether the listing is navigation or page content, is deferred to severity assignment rather than folded into detection. |
| DIATAXIS-ORPHAN | Every page that exists in the tree, and every page a needed topic requires, is reachable by at least one link from some other page already in that tree. | Build the tree's link graph from every page's outbound links; flag as a violation any page in the tree that receives zero inbound links from any other page in the same tree. | One low-traffic reference entry, covering an edge-case parameter, receives no inbound link from any other page, though a reader could still reach it through a search index or a direct URL shared elsewhere. | A page documenting a step every new user must complete before anything else works receives no inbound link from any tutorial, how-to, or explanation page in the tree, so a reader following the tree's own navigation has no way to reach it at all. | judged | Reachability itself is arithmetic once every page's outbound links are visible, but `scripts/checks.py` receives exactly one page per invocation, so the other pages' links are data this script structurally cannot see; see "Why DIATAXIS-ORPHAN moved to the judged lane" below. |
| DIATAXIS-REFERENCE-NEUTRAL | A reference page describes its subject completely and even-handedly, laid out to mirror the structure of the thing it describes, and it does not carry a recommendation, a narrative aside, or an instructional sequence in place of description. | Compare the page's organization to the structure of the thing it documents (fields in a schema, endpoints in an API, options in a command); flag a violation where the organization departs from that structure, or where the page's content includes a subjective recommendation, a narrative aside, or a step-by-step procedure rather than description. | One entry in an otherwise neutral, field-by-field reference page adds a short aside recommending a particular way to use that field. | A reference page for a configuration file's fields is written as continuous narrative prose rather than organized by the file's own field order, so a reader looking up one field has to read the whole page to find it. | judged | Deciding whether an organization actually mirrors its subject, and whether a passage is description rather than opinion or instruction, requires reading the page against the thing it describes. |
| DIATAXIS-TUTORIAL-ACTION | A tutorial page keeps a learner performing a concrete, guided sequence of actions that ends in a visible result, and it does not pause that sequence to explain underlying mechanisms, justify a design choice, or offer the learner a branching choice. | Read the tutorial's step sequence as a whole; flag a violation at any point where the sequence is interrupted by explanatory or justificatory prose, or by an offered choice or branch, before the learner reaches the visible result the tutorial promises. | A single paragraph mid-tutorial pauses the step sequence for a short aside on why the underlying tool behaves that way, then resumes the next numbered step. | A tutorial pauses at nearly every step to explain the underlying mechanism or offer an alternative approach, so a first-time learner cannot complete the sequence by following it straight through. | judged | Whether a given passage genuinely interrupts the action sequence, versus being a short grounding aside that does not disrupt it, requires reading the whole sequence rather than matching a pattern. |

### Per-criterion source pages

Each criterion above operationalizes `DIATAXIS` (the `rubric_sources` entry in
[`SKILL.md`](../SKILL.md)) as a whole; this table records which page of the framework each one draws
from, so a reader can check an operationalization against the material it came from without reading
the site end to end. Every operationalization above is original wording, not a restatement of any of
these pages ([ADR 0006](../../../docs/internal/decisions/0006-copyright-paraphrase-policy.md)).

| ID | Page it draws from |
|---|---|
| DIATAXIS-CROSSLINK | https://diataxis.fr/map/ |
| DIATAXIS-EXPLANATION-CONTEXT | https://diataxis.fr/explanation/ |
| DIATAXIS-HEADING-DEPTH | https://diataxis.fr/complex-hierarchies/ |
| DIATAXIS-HOWTO-GOAL | https://diataxis.fr/how-to-guides/ |
| DIATAXIS-MODE | https://diataxis.fr/tutorials-how-to/ and https://diataxis.fr/reference-explanation/ |
| DIATAXIS-NAV-LENGTH | https://diataxis.fr/complex-hierarchies/ |
| DIATAXIS-ORPHAN | https://diataxis.fr/complex-hierarchies/ |
| DIATAXIS-REFERENCE-NEUTRAL | https://diataxis.fr/reference/ |
| DIATAXIS-TUTORIAL-ACTION | https://diataxis.fr/tutorials/ |

### Why DIATAXIS-MODE and the four per-mode-fit criteria are not the same criterion

`docs/internal/skill-template.md`'s lane-manifest rule holds that a criterion that is sometimes
scripted and sometimes judged is two criteria, not one. Mode-mixing has exactly that shape here: a
closed, pattern-matchable subset of it (a fixed lexical marker for one mode's register appearing where
it should not) is deterministically checkable, while the broader question of whether a page's overall
purpose actually serves its declared mode requires reading the whole page. DIATAXIS-MODE is the
former; DIATAXIS-TUTORIAL-ACTION, DIATAXIS-HOWTO-GOAL, DIATAXIS-REFERENCE-NEUTRAL, and
DIATAXIS-EXPLANATION-CONTEXT are the latter, one per mode rather than one merged mode-fit criterion,
so a finding can name which of the four needs was actually failed.

### Why DIATAXIS-ORPHAN and DIATAXIS-CROSSLINK are not the same criterion

Both concern links, but in opposite directions. DIATAXIS-ORPHAN asks whether anything in the tree
points at a given page; deciding it needs no interpretation of what any page is about, only counting
links, once every page's outbound links are visible. DIATAXIS-CROSSLINK asks whether a given page
points out to the complementary-mode page its own subject needs; it is a property of one page's
content, and deciding which counterpart it needs requires reading that content, no matter how many
other pages are available to read alongside it. A page can fail one without the other: a well-linked-to
reference entry that itself links nowhere fails only CROSSLINK, and a how-to page with excellent
outbound links that nothing else in the tree links to fails only ORPHAN. The two criteria differ again
on why each sits in the judged lane: CROSSLINK because the decision itself needs judgment, ORPHAN
because the data it needs is out of the scripted lane's reach, below.

### Why DIATAXIS-ORPHAN moved to the judged lane

DIATAXIS-ORPHAN was drafted scripted, on the reasoning above: no judgment call, just link counting.
That reasoning is correct about judgment and silent about data. `scripts/checks.py`'s scripted lane is
built on `skills/_shared.runner.run_scripted_lane`, which hands a check function exactly one loaded
artifact per invocation ([`skills/_shared/artifact.py`](../../_shared/artifact.py),
`load_artifact`), and [`bench/README.md`](../../../bench/README.md)'s own location-tolerance rule
states the same constraint from the corpus side: "one artifact is one page" for the `markdown-tree`
type this skill's tree artifacts use. DIATAXIS-ORPHAN's operational test needs every *other* page's
outbound links to decide whether the page in hand has zero inbound links; that information does not
exist inside one page's own bytes, so a script invoked on a single page cannot compute it, regardless
of how little judgment the arithmetic itself requires once the data exists.

This is a different failure than the usual reason a criterion stays judged
([`docs/internal/skill-template.md`](../../../docs/internal/skill-template.md), "Scripted lane
discipline"): the usual reason is that the decision itself needs a judgment call; here the decision is
pure arithmetic and the failure is that the scripted lane's own architecture never hands the check the
inputs that arithmetic needs. Both failures land in the same place, because the template's discipline
is stated as an outcome ("the same artifact produces the same finding, every run, on any machine"), not
as a diagnosis: a script that is structurally blind to data its own operational test depends on cannot
honor that claim, whatever the reason. The judged lane, carried out by an agent that reads the whole
tree during the four-pass protocol's own Inventory pass (`SKILL.md`, pass 1), does not have this
limitation, because nothing there restricts the agent to one page.

## Marker registry and thresholds

Concrete constants the three scripted checks use, copied into `scripts/checks.py` as named
constants so the two files cannot silently drift apart; a change to either belongs here first.

**DIATAXIS-NAV-LENGTH.** The two anchors in the criteria table above are also the threshold
definitions: a flat listing is a violation past 7 items (the severity 2 anchor's "nine flat items, two
past the threshold" fixes the threshold at 7), and severity rises to 3 past 20 items (the severity 3
anchor's "more than twenty flat items"). Both numbers come directly from this table's own anchors, not
from an independent estimate.

**DIATAXIS-MODE.** A page declares its Diataxis mode in a minimal frontmatter block at the top of the
file: a `---`-delimited block carrying a `mode:` key, one of `tutorial`, `how-to` (or `howto`),
`reference`, or `explanation`. A page with no such block, or a `mode` value outside this set, has no
declared mode this check can read, and produces no DIATAXIS-MODE findings rather than guessing one;
this is a v0.1 convention this reference file defines, not an established Diataxis or repository
standard, and the eventual `bench/generator/domains/docs.py` module must plant its DIATAXIS-MODE
defects against pages carrying this same frontmatter. Two closed, sentence-initial marker lexicons
follow directly from the operationalization's own register description ("imperative and action-first
for tutorial and how-to pages... discursive for explanation pages"):

- Action markers (the register tutorial and how-to pages use natively): `first,`, `next,`, `then,`,
  `finally,`, `after that,`, `once you have`, `now,`.
- Explanation markers (the register explanation pages use natively): `because`, `since`, `this is
  because`, `the reason is`, `as a result,`, `in other words,`, `consequently,`.

A page's declared mode is checked against whichever marker group is foreign to its own register: action
markers are foreign to a reference or an explanation page, explanation markers are foreign to a
tutorial or a how-to page. Reference pages are neutral and descriptive by default rather than by a
positive marker set of their own, so both groups are foreign to a reference page.

**Recurrence-based severity.** DIATAXIS-HEADING-DEPTH and DIATAXIS-MODE both anchor severity the same
way in the criteria table above: a single instance on a page is severity 2, two or more instances on
the same page read as the page's own habitual structure rather than a slip and rise to severity 3. This
mirrors [`references/severity-anchors.md`](severity-anchors.md)'s "Frequency and persistence pull
within the range impact sets" section. All three thresholds here (7, 20, and the 1-versus-2-or-more
recurrence rule) are v0.1 defaults chosen so the scripted lane is deterministic and reproducible, which
is the property claimed for it; none is calibrated against the corpus yet. P3 measurement is where they
get their first evidence, and moving one is a revision to this file, not a contract change.

## Sources consulted

All pages on diataxis.fr, accessed 2026-07-31:

- https://diataxis.fr/ (site root, framework overview)
- https://diataxis.fr/start-here/ (five-minute overview, the two axes)
- https://diataxis.fr/tutorials/
- https://diataxis.fr/how-to-guides/
- https://diataxis.fr/reference/
- https://diataxis.fr/explanation/
- https://diataxis.fr/map/ (the compass/map, quadrant boundaries, the user's cycle)
- https://diataxis.fr/tutorials-how-to/ (the tutorial/how-to conflation specifically)
- https://diataxis.fr/reference-explanation/ (the reference/explanation conflation specifically)
- https://diataxis.fr/complex-hierarchies/ (heading/landing-page structure, the seven-items navigation guidance)

## See also

- [`references/severity-anchors.md`](severity-anchors.md) - this skill's domain-anchor prose, extending
  [`docs/reference/severity-scale.md`](../../../docs/reference/severity-scale.md).
- [`SKILL.md`](../SKILL.md) - the lane manifest these nine IDs populate, and the protocol that sweeps
  them.
- [`scripts/checks.py`](../scripts/checks.py) - the scripted lane implementing DIATAXIS-HEADING-DEPTH,
  DIATAXIS-MODE, and DIATAXIS-NAV-LENGTH against the constants in "Marker registry and thresholds"
  above.
