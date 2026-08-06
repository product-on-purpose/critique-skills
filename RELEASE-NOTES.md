# Release notes

Curated, user-facing highlights. For the full technical history, see `CHANGELOG.md`.

## Unreleased

Nothing yet.

## 0.1.1 - 2026-08-05

**What outside eyes found in the first release.** v0.1.0 went public and was listed in the
`product-on-purpose` marketplace on 2026-08-04. Two external validators were then pointed at it, the
first time this library had been checked by anything it did not write itself. This release is what
they found, plus the open items the v0.1.0 handover had carried.

**No skill behavior changed.** No criterion was added, removed, or re-scored; no run envelope was
touched; the measured numbers in `bench/results/` are the v0.1.0 numbers, unchanged. If you are
reading these notes to decide whether the figures moved, they did not.

**If you installed v0.1.0, upgrade.** The most important fix here is that a fresh install could
crash before it read anything.

### The install crash

`critique-skills` needs one Python package, `jsonschema`. Claude Code's `/plugin install` clones a
repository; it does not install Python packages. In v0.1.0 that package was imported the moment any
skill's scripted lane loaded, so on a machine without it you got a raw Python traceback on the very
first command of the five-minute quickstart, with no indication of what to do about it. The remedy
was documented, but only in `QUICKSTART.md`, which is not a file an agent reads before running a
skill.

Now the import happens only when it is actually needed, and if the package is missing you get three
lines naming the exact command to run instead of a traceback. The prerequisite is also stated in
every skill's protocol and in the `critique-critic` subagent, where an agent will actually encounter
it. Related: the subagent's documented commands said `python`, which does not exist on stock Linux
or macOS; they now say `python3`.

### Telling the six skills apart

Six sibling skills in one namespace, all of them about critique, is a routing problem, and nothing
in the pipeline was testing for it: each skill's trigger fixture is validated in isolation, so no
instrument ever compared one description against another. Three pairs turned out to be genuinely
hard to separate. `critique-argument` and `critique-clarity` both claimed proposals and memos, and
each one's own fixture asserted that generic requests like "give me feedback on this document"
should fire **it**. `critique-microcopy` and `critique-usability` both claimed error states.
`critique-accessibility` and `critique-docs` both used the phrase "heading structure" while meaning
different things by it.

Each description now says what it does **not** cover and names the sibling that does. That had to go
in the description rather than the body, because the body is not read until after a skill has
already been chosen.

There is also a new `evals/joint-routing.eval.json`: 18 queries meant to be scored with all six
descriptions in view at once, including four lifted verbatim from the skills' own fixtures where
each is currently claimed by a different skill. It is deliberately not scored in CI, and the fixture
says why in its own file.

### Evidence that had quietly stopped being true

Every example artifact in `skills/*/examples/` records a sha256 of its own contents. On any Windows
checkout, all 22 of those recorded hashes were wrong, and had been since they were written: git
stores the files with Unix line endings and Windows checkouts convert them, which changes the bytes
and therefore the hash. The repository was correct; every Windows copy of it was not; and because
nothing read the hashes, nothing noticed. The v0.1.0 handover had listed this as something that
*would* happen if anything ever checked. It had already happened.

Both halves are fixed: the line endings are now pinned, and there is a test that recomputes every
recorded hash so this cannot silently rot again.

### New documentation

- **An architecture pair.** [`docs/explanation/architecture.md`](docs/explanation/architecture.md)
  is the shape: five parts, how one critique runs, and what the design refuses to do.
  [`docs/explanation/architecture-detail.md`](docs/explanation/architecture-detail.md) is the
  reasoning behind each choice, and what would count as changing the architecture rather than
  fixing a bug.
- **A provenance record for the calibration run set**, which three separate documents had flagged as
  missing. It is explicit about being written after the fact by a session that was not present, and
  lists what it cannot establish rather than inferring it. It also corrects a previously published
  count and records two anomalies nobody had noticed.

### Conformance

Above-tier findings went from five to zero, mostly by fixing the grader rather than this
repository: four of the five were defects in `agent-skills-toolkit`, which grades every plugin in
the family, and are fixed upstream. Nothing blocks Gold now. The declared tier stays Convergent
(Silver), because declaring Gold is a commitment to keep meeting it, not a score to claim once.

## 0.1.0 - 2026-08-03

**Critique that has to show its work.** Ask a general-purpose model to review your document, page,
or argument and you get fluent commentary that changes between runs, cites no standard, and has no
way to be wrong. `critique-skills` answers that for one job: every finding a skill in this library
produces names a permanent criterion ID that traces to a published external standard, not to the
model's own taste, carries a severity on a shared 0-4 scale, points at a location specific enough to
navigate to unaided, and quotes or measures its evidence rather than characterizing it. And the
library publishes its own performance instead of asserting it: every skill below is scored against a
seeded-defect corpus with known ground truth, five times per artifact, on two pinned model tiers,
against the same rubric-free generic prompt a skill has to beat to ship.

**Six skills, all shipping active, each against a real published standard:**

- **`critique-accessibility`** (WCAG 2.2 AA) - contrast, alt text, heading structure, link text,
  keyboard and screen-reader access. Location-level recall 0.988 (Haiku) / 0.965 (Sonnet) against a
  baseline of 0.376 / 0.776, precision 0.875 / 0.672 against 0.258 / 0.293 - see the calibration
  story below for why this is version 0.1.1, not 0.1.0.
- **`critique-clarity`** (Federal Plain Language Guidelines, Williams' *Style*) - readability,
  passive voice, sentence length, nominalization density, audience fit. Location-level recall 0.780
  (Haiku) / 0.890 (Sonnet), beating baseline on both tiers.
- **`critique-usability`** (Nielsen's 10 heuristics; HTML/markdown UI specs and mockups, not live
  applications) - location-level recall 0.800 on Haiku against a baseline that found nothing at all;
  the Sonnet tier is a real but narrow win, recall +0.028 at a small precision cost.
- **`critique-docs`** (Diataxis) - ties the baseline on location-level recall but needs a third as
  many claims to do it (32 claims at 0.875 precision versus the baseline's 102 at 0.275): it ships on
  precision, not on finding defects the generic prompt misses.
- **`critique-microcopy`** (NN/g error-message guidelines) - beats baseline on both tiers, both
  metrics, cleanly: location-level recall 0.920 / 0.960 against 0.813 / 0.840.
- **`critique-argument`** (Toulmin model) - beats baseline on both tiers, both metrics, but carries
  the thinnest consistency margin in the slate: 0.371 against the 0.309 stretch-gate floor on Haiku,
  a margin a different set of five runs could plausibly move.

**The calibration story, in two sentences.** `critique-accessibility` 0.1.0 shipped, then lost to
the unrubricked generic prompt on location-level recall on both pinned tiers (0.176 against 0.376 on
Haiku, 0.306 against 0.776 on Sonnet) - the skill was finding the right defects and then failing to
say where. Version 0.1.1 fixed exactly that reporting defect and nothing else, recall moved to 0.988
and 0.965, and both versions are published side by side in the results tables because a results page
that deletes its own failure once fixed is an advertisement, not a measurement.

**Worked examples for every skill.** `examples/` ships nine self-contained pages: one walkthrough
per skill above, an artifact, its critique, and a human's disposition on each finding, plus three
cross-cutting recipes covering a CI quality gate, a multi-round revision loop, and delegating to the
clean-context `critique-critic` subagent. Every page states plainly which parts you can reproduce
bit-for-bit yourself (the scripted lane) and which are curated from this library's own validated
golden fixtures (the judged lane); nothing in the folder presents authored content as a live run.
Start at `examples/README.md`, organized by what you are trying to do rather than by file.

**Known limitations, stated so you do not have to infer them:**

- The corpus is generated by a deterministic seeded generator, not collected from real documents; it
  measures whether a skill finds defects of a known kind, planted deliberately, not real-world
  performance.
- Precision is a conservative lower bound: a genuinely correct finding that was not planted counts
  against a skill rather than for it.
- The results only cover two pinned model tiers (`claude-haiku-4-5-20251001`, `claude-sonnet-5`) on
  a single date; these numbers decay and are not a claim about any other model.
- k=5 carries real sampling noise; `critique-argument`'s Haiku margin over the consistency floor is
  0.062, small enough that a different five runs could move it either way.
- The accessibility calibration corpus is unusually id-rich, and the fixed skill's location strategy
  leans on element ids first; how much of the 0.176-to-0.988 gain survives on markup without ids is
  not yet measured.
- The measurement grid's provenance is documented after the fact
  (`docs/internal/execution/P3-provenance.md`) rather than from a committed, independently
  reproducible harness log, and the calibration run's own provenance record is still an open item
  for v0.2.
- No human acceptance data exists yet; disposition-based acceptance rate is a v0.2 measure, not a
  v0.1.0 one.

Full numbers, every unflattering one stated first: `bench/results/README.md`. Per-skill ship
reasoning: `bench/results/verdicts.md`. Install path: the product-on-purpose marketplace, which
pins this release's tag, or `npx skills add product-on-purpose/critique-skills`; see
`QUICKSTART.md` for a no-branch first run, or `examples/README.md` for a worked walkthrough of
every skill.
