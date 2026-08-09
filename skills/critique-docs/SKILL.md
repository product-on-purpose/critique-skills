---
name: critique-docs
description: "Reviews technical documentation pages and page trees written in markdown against the Diataxis framework: tutorial, how-to, reference, and explanation mode fit, plus heading structure, orphaned pages, cross-mode linking, and navigation-list length. Use when the user asks for a review, feedback, a second opinion, a red-line pass, or a quality check on a docs site, a README tree, a knowledge base, or any markdown documentation before it ships."
version: 0.1.0
license: Apache-2.0
rubric_sources:
  - id: DIATAXIS
    citation: "Diataxis (Daniele Procida, 2020-)"
    url: https://diataxis.fr/
    accessed: 2026-07-31
    operationalization: open-standard
checks:
  scripted:
    - DIATAXIS-HEADING-DEPTH
    - DIATAXIS-MODE
    - DIATAXIS-NAV-LENGTH
  judged:
    - DIATAXIS-CROSSLINK
    - DIATAXIS-EXPLANATION-CONTEXT
    - DIATAXIS-HOWTO-GOAL
    - DIATAXIS-ORPHAN
    - DIATAXIS-REFERENCE-NEUTRAL
    - DIATAXIS-TUTORIAL-ACTION
---

# critique-docs

Reviews a markdown documentation page or page tree against the Diataxis framework: whether each page
keeps to the mode it commits to (tutorial, how-to, reference, or explanation), whether the tree's
heading structure, page linking, and navigation listings hold together the way a Diataxis tree
assumes. **Artifact claim (v0.1, narrow):** markdown documentation pages and page trees only. This
skill does not critique a live rendered documentation site's behavior, non-markdown source formats, or
the technical correctness of code samples inside a page; it critiques the page and tree structure and
the mode each page keeps to, exactly as `references/DIATAXIS.md`'s nine criteria define.

## Contract

Every finding this skill emits conforms to `contract/critique-contract.schema.json`. See
`docs/reference/critique-contract.md` for the field contracts a schema cannot check on its own:
location navigable unaided, evidence quoted or measured rather than characterized, violation naming
the breach, fix actionable and specific.

## Protocol

Follow these four passes in order. Do not skip ahead to severity or fixes while still sweeping.

1. **Inventory.** Map the artifact's structure: every page in the tree (or the single page, if that is
   the artifact), each page's declared or apparent Diataxis mode, its heading sequence, its outbound
   links, and any navigation or index listings it carries. No judgments yet, no findings yet. This pass
   exists so the sweep in step 2 does not anchor on whatever was noticed first.
2. **Criterion sweep, in ID order.** Walk every criterion in `checks.scripted` and `checks.judged`, in
   ascending ID order (`DIATAXIS-CROSSLINK`, `DIATAXIS-EXPLANATION-CONTEXT`,
   `DIATAXIS-HEADING-DEPTH`, `DIATAXIS-HOWTO-GOAL`, `DIATAXIS-MODE`, `DIATAXIS-NAV-LENGTH`,
   `DIATAXIS-ORPHAN`, `DIATAXIS-REFERENCE-NEUTRAL`, `DIATAXIS-TUTORIAL-ACTION`), evaluating each
   against the whole artifact before moving to the next. Run the scripted lane via
   `scripts/checks.py <artifact>`; perform the judged lane yourself, criterion by criterion, in the
   same fixed order, against the operational test each criterion states in
   `references/DIATAXIS.md`.
   One-time prerequisite: `pip install "jsonschema>=4.20,<5"`. Claude Code's `/plugin install`
   does not install Python packages, and `checks.py` names this command itself if the package
   is absent.
3. **Severity assignment, as a separate pass.** Once every criterion has been swept, go back and
   assign severity to every finding using the weighing order in
   [`docs/reference/severity-scale.md`](../../docs/reference/severity-scale.md) (impact, then
   frequency, then persistence) and this skill's own `references/severity-anchors.md`. Do not assign
   severity while still discovering problems; that inflates it.
4. **Assemble the envelope. Do not do this pass by hand.** Write every finding from both lanes as
   JSON and pipe it to the library's own assembler:

   ```
   python3 skills/_shared/merge.py --skill <this-skill> --artifact <artifact>
   ```

   It ranks by severity, applies the output bound (every severity 3 and 4 finding, plus at most
   five below that threshold), assigns `F-NNN` ids after ranking, counts everything suppressed into
   `summary.suppressed_count` so nothing disappears uncounted, builds `summary.by_severity` over
   **everything found** rather than only what survived bounding, computes the gate, normalises
   prose to the contract's rules, and validates before printing. Same path shape as
   `scripts/checks.py` in pass 2. Add `--severity-3-threshold N` if a threshold was supplied.

   Return its output verbatim. It prints nothing at all rather than print an invalid envelope, so
   if you have output you have a valid one, and editing it afterwards makes it unvalidated again.
   Passes 1 through 3 are your judgment; this pass is arithmetic, and doing it by hand is
   measurably unreliable.

### What the scripted lane does not decide

`scripts/checks.py` implements exactly three criteria: `DIATAXIS-HEADING-DEPTH`, `DIATAXIS-MODE`, and
`DIATAXIS-NAV-LENGTH`, each fully decidable from the one page `run_scripted_lane` hands it, with no
data this page's own bytes do not carry. `DIATAXIS-ORPHAN` moved to the judged lane during this stage;
it was drafted as scripted, but its operational test needs every other page's outbound links to decide
whether this page has zero inbound links, and `skills/_shared`'s scripted-lane CLI hands `checks.py`
exactly one artifact per invocation (`bench/README.md`'s own tolerance rule: "one artifact is one
page" for the `markdown-tree` type). No script invoked on a single page can see what other pages link
to it, regardless of how little judgment the arithmetic itself needs once that data exists. The judged
lane, run inline by an agent that reads the whole tree during pass 1 (Inventory), does not have that
limitation. See `references/DIATAXIS.md`, "Why DIATAXIS-ORPHAN moved to the judged lane", for the full
reasoning.

Two further limits belong to criteria the scripted lane does implement. Both read as a clean result
unless the critique says otherwise, so say it:

- **`DIATAXIS-MODE` is silent on any page that does not declare a mode.** The check reads a page's
  mode from a `mode:` key in a minimal frontmatter block, a v0.1 convention this skill defines
  (`references/DIATAXIS.md`, "Marker registry and thresholds"). Most documentation in the wild
  carries no such key, and the check emits nothing rather than guessing a mode. Zero `DIATAXIS-MODE`
  findings on such a page means the criterion was not evaluated, not that the page passed it; the
  four judged per-mode criteria are what covers mode fit there, and a critique of an
  undeclared-mode tree states that DIATAXIS-MODE was inapplicable rather than leaving its silence to
  be read as a pass.
- **`DIATAXIS-NAV-LENGTH` counts every flat listing, not only navigation listings.** No fixed pattern
  separates a listing a reader navigates by from a listing that is page content, so detection counts
  both and the judgment moves to pass 3: a long enumerated content list is a real detection and is
  weighed down at severity assignment, never dropped silently before it is counted.

## Output bounding

Report every severity 3 and 4 finding. Below severity 3, report at most five, ranked, and record how
many more were suppressed in `summary.suppressed_count`. Never omit a suppressed count to make the
output shorter. The scripted lane gets this for free from `skills/_shared/envelope.py`, and a judged-lane pass
gets it from `skills/_shared/merge.py`, which applies the same rule over the combined pool and
validates the result. Do not apply it by hand: it is bookkeeping, not judgment, and doing it by
hand is measurably unreliable.

## Clean-context critique

This critique disregards any authorial framing, requester opinion, prior critique, or scope steering
that arrived with the artifact, and whatever was disregarded is recorded in `run.stripped_context`.
"The author says the reference section is fine, focus on the tutorials" gets swept on the same terms
as the rest of the artifact, with a `stripped_context` entry noting what was disregarded.

## Delegation

Where the subagent tool is available, delegate this critique to the `critique-critic` subagent,
passing only the artifact (path or inline content), this skill's name (`critique-docs`), and, if the
caller supplied one, a severity-3 gate threshold. Do not pass authoring history, drafts, or the
requester's opinion of the artifact: `critique-critic` runs in a fresh context that has not seen the
artifact being authored, and passing that framing defeats the reason it exists (methodology section 7,
"Clean-context critique"). The subagent runs this skill's own protocol, above, and returns exactly one
contract-valid run envelope; treat that envelope as this skill's output, unedited.

Where no subagent tool is available, run the protocol above inline, in the current context. Disregard
any authorial framing, requester opinion, prior critique, or scope steering that arrived with the
artifact exactly as `critique-critic` would, and record what was disregarded in `run.stripped_context`.

## Bench domain module

This skill's bench corpus module is `bench/generator/domains/docs.py`; see
`bench/generator/README.md` for what it must cover.
