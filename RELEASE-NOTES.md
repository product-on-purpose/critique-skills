# Release notes

Curated, user-facing highlights. For the full technical history, see `CHANGELOG.md`.

## Unreleased

Nothing yet.

## 0.1.6 - 2026-08-16

**Three things that had never actually been run, run for the first time. All three were broken.**

No criterion changed, no skill's judgment changed, and no published number moved.

### The one that affects you

**A critique could hang instead of finishing.** Each skill can hand the work to a separate reviewer that starts with a clean slate, which is how the library keeps a critique honest about work you wrote yourself. That reviewer was told where to find the skill's own scripts using a path that only worked if you happened to be sitting in the library's own folder. From anywhere else it could not find them.

It did not stop and say so. It went looking, and when the obvious places did not turn one up it began searching your drives. In our test it scanned two entire drives and never came back.

The reviewer is now told exactly where the skill lives, and told in as many words to stop and say it does not know rather than go looking. Searching for a missing path is not a fallback; it is the failure.

If you have ever had a critique sit there doing nothing, this is very likely why, and it is fixed.

### The ones that affect what you can trust

**Every published score now shows its spread.** The results tables report one number per skill per tier, and each of those is five separate runs pooled together. Those five runs disagree with each other more than the single number suggests. One accessibility figure published as 0.306 came from runs measuring 0.529, 0.294, 0.353, 0.118 and 0.235.

That spread is now published alongside the scores, computed from the same committed evidence with no new runs. Read it before treating any single figure here as precise. Two things it makes visible: the cheaper model tier is noticeably less consistent than the more expensive one, and the run-to-run agreement figure has no error bar at all, which we now say plainly rather than leave implied.

**The command that reproduces our numbers could never have run.** The benchmark workflow is the thing that lets someone else check our figures on infrastructure we do not control. It had one missing setting that made it exit immediately, before reaching a model, on every attempt. It had never been tried, because trying it costs money and it only ever runs on request. Fixed, and there is now a test that fails if it regresses.

### Still open, stated rather than buried

The benchmark can currently only reproduce the cheaper tier's half of our published figures. The expensive tier hits a second version of the same searching problem, in a different place, and no run on it has completed yet. Until that is resolved the published figures remain the ones we measured originally, and nothing here claims otherwise.

### The part worth admitting

The reviewer's broken path was the *same mistake* the previous release fixed one layer up. That release moved a script "because that path resolves", rewrote six files to match, and left the reviewer's own instructions pointing at the old location. Its own recorded lesson was that the instruction a run follows is the one it actually reads, and it did not apply that lesson to itself. There is now a test that checks the commands rather than the prose around them.

## 0.1.5 - 2026-08-09

**The skills stop doing arithmetic in their heads.**

No criterion was added, removed, or re-scored. No run envelope was touched. What changed is the last step of how a critique is assembled.

### The problem

Every critique ends by combining what the automated checks found with what the model judged, ranking it, keeping the important findings, counting what was left out, and tallying the result. Until now the skills were told to do that in prose, by hand, every time.

They were not reliable at it. Measured against a small model, **only 2 runs in 7 produced a usable report.** The critiques themselves were fine. The bookkeeping was wrong: a tally that did not add up, or a field filled in where it should have been left empty. Good work, discarded over arithmetic.

The counting is now done by a script that ships with each skill, which also refuses to hand back a report that does not pass its own validation. **After the change: 3 of 4 runs usable, and none of the remaining failures were bookkeeping.**

### The part worth admitting

The first two attempts at this fix did not work, and we only found out by running the skills the way you actually use them: from an ordinary folder, with the plugin installed somewhere else. The script could not be found from there, and each time a skill could not find it, it fell back to writing a readable summary instead of a structured report.

That is a worse failure than the one being fixed, because a readable summary looks fine to a person and is unusable by anything automated. The script now sits in the same place as the checks each skill already runs, which is a path that has worked in every release so far.

### Also

The benchmark tool that produces our published numbers no longer inherits whatever else you happen to have installed when it runs, so two people running it now measure the same thing.

## 0.1.4 - 2026-08-09

**The API key is gone from this project entirely, including from our own benchmark tool.**

No skill behavior changed. No criterion was added, removed, or re-scored. No run envelope was touched.

### What changed

The last release explained that you never needed an API key to use these skills, and split the packaging so it stopped looking like you did. One thing stayed behind: our own benchmark tool, the one that produces the published performance numbers, still called a paid API and still needed a key to run.

That is gone too. The benchmark now reaches the model through Claude Code itself, signing in from a Claude subscription rather than a key. The API client package has been deleted from this repository, along with the separate dependency file that carried it.

**There is now no API key anywhere in this project, for you or for us.** Installing it pulls exactly one small open-source package, which is all it ever needed.

### Why this is more than tidiness

We publish numbers about how well our own skills perform. The tool that produces those numbers exists so that somebody who does not trust us can re-run the measurement and check. That argument only works if re-running it is actually practical, and requiring a separate paid API account put a bill between a skeptical reader and the receipt. Now it costs whatever your existing Claude subscription already costs.

### Also

We found and corrected three documents that still described the old arrangement. One of them was our security policy, which is public, and which was telling readers we required a key we no longer use.

## 0.1.3 - 2026-08-07

**This library never needed an API key from you, and now it stops looking like it does.**

No skill behavior changed. No criterion was added, removed, or re-scored. No run envelope was touched.

### The problem

Installing this plugin's one Python dependency, with the obvious command, also installed an Anthropic API client you have no use for.

That was our packaging mistake, not a requirement. The dependency file listed two things: the small open-source package the skills actually need, and an API client that only our own benchmark tool uses. Anyone reading that reasonably concluded they were expected to bring an API key.

**You are not.** A skill is a set of instructions that the AI assistant you are already using reads and follows. It never places a call of its own, so there is nothing to authenticate and nothing to pay for beyond whatever you already have.

The two are now separate files. The default one installs a single package. We verified it by running every skill on a machine with the API client deliberately absent: all six work.

### The explanation, for anyone who wants it

There is a new page, [The benchmark harness, and why it does not affect you](docs/explanation/the-benchmark-harness.md). It opens by answering the question directly and telling you that you can stop reading there.

If you carry on, it explains the one tool in this repository that *can* use an API key: what it does, why a library about honest measurement keeps it around, and why it has never actually been run. Short version: we publish numbers about how well our own skills perform, and that tool exists so somebody who does not trust us can re-run the measurement and check. It is a receipt, not a feature.

### Also

The check on whether the right skill gets picked, out of the six, now runs on both of the AI models we measure against. Both score 18 out of 18.

## 0.1.2 - 2026-08-07

**The release where we stopped reasoning about the runtime and started asking it.** Every fix below came from running something and reading the answer, and two of them contradicted a confident conclusion written down earlier in this repository.

**No skill behavior changed.** No criterion was added, removed, or re-scored; no run envelope was touched; the measured numbers in `bench/results/` are the v0.1.0 numbers. If you are reading these notes to see whether the figures moved, they did not.

**If you installed v0.1.1, upgrade.** It shipped a subagent nobody wrote.

### The subagent nobody wrote

Claude Code finds subagents by looking for markdown files in the `agents/` folder, and it loads every one it finds. This plugin had a `README.md` in there, describing the folder. So it was being loaded as a subagent, called `README`, with no description and no purpose. Silently, with no warning.

We found it by loading the plugin and asking what subagents it had. The answer came back with two names where there should have been one.

The cause was not ours. The family quality standard this library is graded against **required** a documentation file in that folder, so following the rule created the problem. That rule is withdrawn upstream, and the file is gone. What it explained has moved into the architecture documentation, along with the lesson: `agents/` holds subagent definitions and nothing else.

### Telling two skills apart

`critique-accessibility` and `critique-usability` both review interfaces, and neither said what it did *not* cover. So "check the colour contrast on this landing page" went to the usability skill, when contrast is an accessibility question.

Worth saying how this was found: not by review. The case had been written into our own test fixture as an obvious one that could not possibly go wrong. It went wrong. Both descriptions now name the other.

### Two new things that check the library rather than describe it

**A "does it actually run" check.** Every other test in this project installs its dependencies first, so none of them saw what a real install looks like: a download and nothing else. That blind spot is exactly how v0.1.1 shipped a crash. There is now a check that runs every skill the way a brand-new user's machine would, with nothing installed, and requires it to fail with a clear instruction rather than a wall of Python errors. Then it installs the dependency and requires everything to work. Both halves matter; checking only the second is what missed the original bug.

**We now measure whether the right skill gets picked.** Six skills that all do critique is a real problem: when you ask for "feedback on this document," something has to choose. Until now nothing tested that choice. It is now measured, by loading all six descriptions the way you get them and asking. **18 out of 18.**

One finding from that worth passing on: the choice is not perfectly repeatable. The same question can get different answers on different days, so a single run proves nothing. The measurement runs each question several times and reports how often the answers agreed.

### Conformance

Outstanding issues above our declared quality tier went from five to zero. Four of the five were bugs in the grader, not in this library, and are fixed upstream. Nothing now blocks the top tier. We are staying at the current one anyway, because claiming a tier is a promise to keep meeting it, not a score to bank.

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
