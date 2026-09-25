# Backlog

Local-first, version-controlled backlogs (Standard sec 7.1). Two files, plus this index:

- **[enhancements.md](enhancements.md)** - features, fixes and refinements to components that already
  exist. 65 items, `E1` through `E65`.
- **[new-components.md](new-components.md)** - proposals to ADD a skill, command, subagent, hook or
  chain. 4 items, `N1` through `N4`, each with a recorded why-gate verdict.

This is committed maintainer governance, not published documentation. `docs/internal/` is never
routed to the site by design, so nothing here appears at
`product-on-purpose.github.io/critique-skills/`.

## Why this directory exists

The Standard has specified this location all along. `STANDARD.md` sec 7.1 says a plugin SHOULD
maintain two distinct backlogs as structured markdown under `docs/internal/backlog/`, and the
toolkit's own backlog README states the requirement more strongly still: recommended at Bronze,
**required at Silver and above**. This plugin declares Convergent (Silver) and had neither file.

That gap was invisible for a reason worth recording: **no check module enforces sec 7.1.** The
conformance run reports 0 errors and 0 warnings, which is accurate about what it checks and silent
about this. `scripts/gen-index.mjs:21` documents the other half of the same story: the upstream
`gen-index` generator assumes `docs/internal/backlog/` exists, and this repository carried a local
`dropPhantomRows()` filter to strip the resulting dangling links from `INDEX.md`.

The practical gap it left is the one the 2026-09-11 session log names directly. Open work lived in
three places with different lifespans and no home that outlived a release:

| Where | Scope | What went wrong |
|---|---|---|
| `ROADMAP.md` | Public, version-scoped intentions | Holds promises, not defects. Never a list of what is broken. |
| `docs/internal/execution/RC-HANDOVER.md` | The v0.1.0 execution artifact | Froze at the tag. Over half its list closed without anyone striking it through, discovered by re-checking rather than by reading. |
| Session logs, gitignored | The live maintainer decisions | Survived five sessions only by being retyped by hand into each continuation prompt. |

The GitHub issue tracker held zero open issues throughout. That is worth stating plainly, because
the v0.1.x exit gate is written as "two consecutive weeks with no open contract or check defect": an
empty tracker satisfies that gate while also measuring nothing but reporting volume. See
[E14 (rule whether a site-guard defect resets the exit-gate clock)](enhancements.md).

## How an item moves

```
enhancements.md / new-components.md      <- recorded here first, always
        |
        |  when it is worth acceptance criteria
        v
docs/internal/release-plans/_unassigned/S-NN_<slug>/spec.md      (/plab-spec)
        |
        |  when it is committed to a release
        v
docs/internal/release-plans/plan_NN_<slug>/S-NN_<slug>/          (/plab-release-plan --promote)
```

Two ID namespaces, deliberately separate. `E<n>` and `N<n>` are backlog intake numbers and live
here. `S-NN` are effort and spec IDs; `S-01` through `S-08` are consumed by the v0.1.0 plan, so the
next spec written from this backlog is `S-09`. An item keeps its `E` number forever, including after
it graduates to a spec; the spec cites the `E` number rather than replacing it.

**Never write a bare ID.** Write "E2 (sonnet unblock)", not "E2". Every heading in both files
carries a handle so this costs nothing.

## Prioritization frame

Cost of deferral crossed with what the item unblocks.

**Cost of deferral** asks whether this gets more expensive, more embarrassing, or less recoverable
the longer it waits. In a project whose whole argument is that every published claim carries a
receipt, a claim that is wrong right now (a stale number in the README, a published explainer that
says the harness has never run live, 31 envelopes declaring a model ID outside the two pinned tiers)
carries a high cost of deferral even when the fix is fifteen minutes. Those rank above larger
positioning work.

**Unblocks** asks how many other items wait on this one.

Ties break toward the cheaper item. An item reported independently by two or three audit surfaces is
treated as more important, not less. Ranks are a do-first order for one person, not a queue for a
team.

## The root decision

**RULED 2026-09-11: v0.2.0 is Option A plus Option C**, receipts first plus the research spine.
E1 was the root node and was blocked since 2026-08-08; nine of the ten largest items could not be
ordered until it was settled. The ruling, what moved, and the resulting exit gate are recorded in
**[the v0.2.0 shape options brief](../release-plans/v0.2.0-shape-options.md)**, which keeps all
four options beneath the ruling unedited.

In short: v0.2.0 is all of Option A's measurement debt, plus E44 (taxonomy survey) and N1
(critique-deck). N3 (critique-dataviz) is held unscheduled in `new-components.md` rather than
dropped, because it was the one XL item making the published exit gate unclosable.

**Three riders survive the ruling** and are not discharged by it: E11 (cut or schedule the vanished
askit and CodeQL commitments), E12 (re-cut the published exit gate to match), and E14 (declare the
v0.1.x gate met, which comes first).

One consequence worth naming: because Option C's skill must be measured on both pinned tiers,
**E2 (sonnet unblock) now gates the v0.2.0 exit gate itself**, not just three measurement items.

## Ready now

**33 items depend on nothing and can start today.** Derived from each item's own
`Depends on` field rather than asserted, and regenerated whenever an item closes.

| ID | Item | Size | Release |
|---|---|---|---|
| E62 | Rule the Standards-watch commitment, and the 0.12 pin it is measured against | S | v0.1.x |
| E64 | Rule on ADR 0030 now that the sonnet fidelity gate has failed | S | v0.1.x |
| E13 | Update ROADMAP.md's v0.1.x section: two of four verification items are met | S | v0.1.x |
| E28 | Pin or record the Claude Code CLI version bench.yml installs | S | v0.1.x |
| E29 | Make release.yml's re-run suite match what it claims to run | S | v0.1.x |
| E30 | Fix two gaps in skill-template.md before the next skill is built from it | S | v0.1.x |
| E31 | Add criterion-table completeness to skill-selftest.py | S | v0.1.x |
| E32 | Close S-03 AC-3: flip the checkbox and add a corpus-composition CI check | S | v0.1.x |
| E33 | Correct ROADMAP's Gold-tier bullet (3 of 4 done) and decide the tier declaration | S | v0.1.x |
| E34 | Close the SKIP_DIRS carry-forward note - fixed upstream and already adopted | S | v0.1.x |
| E35 | Run plugin-dev:plugin-validator and plugin-dev:skill-reviewer, or record why not | S | v0.2.0 |
| E36 | Confirm or deprecate the reserved selector field per ADR 0012's own RC question | S | v0.1.x |
| E37 | Run the TOULMIN-HEDGE-DENSITY false-positive check ADR 0017 named, and fix TOULMIN.md's future tense | S | v0.1.x |
| E38 | Measure critique-accessibility's location fix on id-poor markup | S | v0.2.0 |
| E65 | Decide whether critique-clarity's critic should emit instances | S | v0.2.0 |
| E39 | Record the CLAUDE_CODE_OAUTH_TOKEN retention decision and a rotation procedure | S | v0.1.x |
| E40 | Look at a Mermaid diagram in light and dark on the live site | S | v0.1.x |
| E42 | Reconcile 'frozen with a JSON Schema' against 'freezes at v1.0' | S | unscheduled |
| E43 | Create a v1.0 readiness tracker for the four declaration criteria | S | v1.0.0 |
| E51 | Give the precision and corpus-provenance limitations a retirement path or an explicit 'accepted' | S | unscheduled |
| E52 | Decide who performs 'revise' in the automated revision loop before building it | S | v0.3.0 |
| E59 | Verify what the marketplace consumes the homepage field for | S | unscheduled |
| E10 | Rule how BYOR is measured under the measured-only exclusion | M | v0.2.0 |
| E22 | Turn on severity_expected scoring | M | v0.2.0 |
| E23 | Write methodology.md's location-level metrics section | M | v0.2.0 |
| E24 | Add an automated evidence-quotes-not-characterizes check | M | v0.2.0 |
| E27 | Isolate the bench harness from the working tree it measures | M | v0.2.0 |
| E63 | Bring the dispatch run sets into results.json, or amend the rule they break | M | v0.2.0 |
| E49 | Write one real tutorial for the empty Diataxis Tutorials quadrant | M | v0.2.0 |
| E53 | Harden --gate as a documented per-skill CI recipe for consumers | M | v0.3.0 |
| E54 | Ship one documented cross-library composition workflow | M | v0.3.0 |
| E25 | Rewrite verdicts.md as one current-state document | L | v0.2.0 |
| E26 | Calibrate a per-lane consistency threshold (v2) | L | v0.2.0 |

With S-07's AC-4 closed, every criterion in that spec passes and
[ADR 0034](../decisions/0034-v0.1.x-exit-gate-declaration.md)'s two named conditions for calling
v0.1.x finished are both discharged.

## Critical paths

- **Opening v0.2.0 at all.** E13, E14, E15 and E16 close the v0.1.x verification list, which lets the
  exit gate be declared met, which is what opens v0.2.0. In parallel, E1 gates E11 (the askit and
  CodeQL ruling) gates E12 (exit-gate re-cut) gates any v0.2.0 tag.
- **The sonnet chain, and the critical path inside the ruled shape.** E2 gates E19 (sonnet
  fidelity dispatch) gates E20 (usability re-measure) and E26 (consistency threshold v2). E2 also
  gates two-tier k=5 measurement for N1, N2 and N3. **Discharged 2026-09-24:** E2 and E19 are closed,
  E20 is recorded with only its ROADMAP wording outstanding, and E26 is ready. The gate itself failed
  on sonnet, which opened E64 (ADR 0030's ruling) and E65 (clarity and `instances`).
- **The skill wave, the longest chain overall.** E1 gates E44 (taxonomy survey), which orders but
  does not gate N1 (critique-deck); N1's hard dependencies are E30, E2 and a corpus module. N1 gates
  N2, which gates N3, which additionally needs a chart-spec generator mode that does not exist.
- **BYOR.** E10 (the measurement ruling) gates E45 (the build) gates every later skill's BYOR support.
- **Gold tier.** E52 (who performs revise) gates N4 (the revision-loop chain) gates E55 (G1 and G3
  coverage) gates any tier declaration above Convergent.
- **v1.0.0.** E48 (disposition telemetry) is the true critical path, because it needs calendar time
  for real dispositions to accumulate before a pruning pass can run, in parallel with E56's external
  adoption. No amount of session throughput buys either.

## Structural findings

Eight patterns visible only across surfaces. These are about how the project works, not about any
one item, and several are worth more than the items that expose them.

1. **A guard exists for one twin and not the other, and every stale-number finding landed in the
   unguarded twin.** The README scoreboard marker is generated and drift-checked while the badges,
   Fast-facts table and the count at `ROADMAP.md:21` beside it are hand-typed (E3). `gen-site.mjs`
   guards duplicate criterion IDs while `skill-selftest.py` never checks table completeness (E31).
   `ci.yml`'s job list is drift-checked while `release.yml`'s is not (E29). The corpus is verified
   byte-for-byte for reproducibility while nothing checks its composition (E32). The fix class is the
   same each time: extend the existing guard to the twin, rather than invent a new guard.
2. **"Known issues", "open questions" and prerequisite sections have no close convention**, so
   resolved entries stay open indefinitely. Seven instances across five surfaces (E4, E8, E9, E13,
   E15, E16, E32, E34, E41). A one-line convention, a date plus a strikethrough or a Resolved
   subsection, prevents the whole class.
3. **Self-imposed RC checkpoints are written well and never swept at release time.** ADR 0012's
   selector question (E36), ADR 0017's false-positive check (E37), ADR 0028's id-poor measurement
   (E38), S-07 AC-1 and AC-4 (E15, E16), S-03 AC-3 (E32), the external validators (E35). Six releases
   shipped past all of them. A release-checklist step that greps ADRs and specs for "before v0.2",
   "at RC" and unchecked AC boxes would have caught every one.
4. **The sonnet tier is half the published measurement basis and has never produced an envelope
   through the shipped harness.** The v0.1.0 sonnet numbers predate the ADR 0030 rewrite, the
   fidelity gate validated haiku only, and usability's cell, threshold v2 and every new skill's
   measurement all queue behind one S-sized fix that has been an open decision since v0.1.6. Largest
   lever in the backlog; also the cheapest item on it.
5. **Fabricated provenance was itself an undercounted receipt.** RC-HANDOVER tracks six files; the
   audit found 31, of which 17 declare a model ID that is not one of the two pinned tiers, and
   `RC-HANDOVER.md:116`'s own fixture count is off by four. The project's tracking of its own honesty
   gap was inaccurate in the direction that flatters it (E5).
6. **The backlog had no durable home and lost state at every session boundary.** At least eight
   sessions between 2026-08-15 and 2026-08-26 were never wrapped. The OAUTH_TOKEN decision (E39), the
   exit-gate clock question (E14) and the agent-plugins convergence row (E50) each dropped out of the
   record entirely, and two v0.2.0 commitments (E11) vanished in a document rewrite with no recorded
   cut. This directory is the response; it will decay the same way if items are closed in
   conversation rather than struck here.
7. **The conformance badge reads stronger than it is.** The entire Silver and Gold tiers are house
   checks, and G1 and G3 pass vacuously because the repo declares no hooks and no chain contract. Not
   this repo's defect to fix, but "Convergent (Silver), 0 errors, 0 warnings" should be phrased as a
   house-check result until the toolkit surfaces provenance. The absent sec 7.1 check described at the
   top of this file is the same pattern.
8. **The public `ROADMAP.md` was substantially rewritten, not trimmed, from the local plans, and the
   rewrite is where commitments were lost** (E11). Any future local-plan to public-doc transition
   should diff the two item lists rather than re-author from scratch.

## Known blind spots in this intake

Stated so the next pass knows where not to assume coverage. None of these produced a finding; none
of them was read exhaustively either.

- `CONTRIBUTING.md` and `SECURITY.md` were never read in full by any surface.
- `contract/validate.py` (932 lines): its rule inventory was taken from the README rather than
  re-derived from the source.
- `bench/generator/` (build, pipeline, blockparse, html, leak, verify, rng, api) and `bench/metrics/`
  (resolve_html, resolve_markdown, resolve_stringlist, locate, ordinals, markdown_blocks, text_util)
  were named as unopened.
- ADRs 0001-0011, 0013-0016 and 0018-0021 were checked only for whether their referenced files still
  exist, not for other live obligations.
- The roughly 50 built site pages, beyond the specific link and route checks.
- The v0.1.0 specs `S-01`, `S-02`, `S-04`, `S-05`, `S-06` and `S-08`. Only `S-03` and `S-07` were
  opened for AC status, so other unchecked acceptance criteria may exist.

## Provenance of this intake

Recorded 2026-09-11 against `main` at commit `8950878`, with v0.1.6 tagged and 0 open issues.

Eight scoped audits swept independent evidence surfaces and produced 81 raw candidates; cross-surface
deduplication collapsed those to 64. A completeness critic then re-opened the cited files and
spot-checked citations against the repository. It found one citation defect (corrected inline at E3),
two release tags that were version labels rather than real dependencies (corrected at E19 and E33),
and confirmed that all 81 raw candidates are accounted for as merged, promoted or rejected with a
stated reason. Corrections it produced are carried as `Review note` lines on the affected items.

One item was added after that pass. The intake briefing told every auditor not to re-report the five
known live maintainer decisions, on the reasoning that they were already tracked. Three reached the
backlog anyway through synthesis (E1, E2, E14) and one resolves by merging or closing an open PR, but
the site lockfile question would have been dropped by that exclusion. It is recorded as E61. The
exclusion rule was the right call for the audit and the wrong call for the file, which is a small
instance of exactly the failure structural finding 6 describes.

Two candidates were rejected as belonging to the toolkit's own repository rather than this one, and
are folded into structural finding 7. Note that the toolkit's backlog uses the same `E<n>` shape for
its own items; a reference to "the toolkit's E21" is not this file's E21.
