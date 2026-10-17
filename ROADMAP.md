<a id="roadmap-top"></a>

# Roadmap

This is a public statement of sequence, not a schedule. It says what shipped, what is next, what depends on what, and - as much as anything else - what has not shipped yet.

## How to read this

**Sequence-only, no dates.** Every version below is gated by the exit criteria of the version before it. `v0.2.0` does not open until `v0.1.x`'s exit gate closes; `v0.3.0` does not open until `v0.2.0`'s does. This is a solo-maintained project that publishes its own honest measurement numbers, and a solo maintainer who commits to dates ends up choosing between missing them in public or quietly padding the numbers to hit them. Sequence-gating avoids that trade entirely: a version opens when its prerequisite work is actually done, not when a calendar says it should be.

**This document is also a list of what is not done.** Reading only the "Now" section tells you what exists. Reading the rest tells you, just as precisely, what does not: no taxonomy survey yet, no BYOR mode yet, no revision loop as a first-class chain yet. Treat every "Next" and "After" item as a feature this library does not currently have, not a promise about when it will.

**Where the numbers live.** Nothing on this page overrides the measured results. `bench/results/README.md` is the source of truth for what the library actually catches; this page only sequences the work that produces future measurements.

**Standards watch.** This plugin is graded against the Advanced Skill Library Standard version pinned in `library.json`. When the Standard publishes a new minor version, the next release of this plugin adopts it, or its release notes say why not.

---

## Now: v0.2.0

v0.2.0 is the first minor release since `v0.1.0`, after six patch releases. It added one skill, `critique-forms`, and made the receipts behind every published number whole. `CHANGELOG.md` carries the detail.

Shipped: seven measured critique skills (`critique-accessibility`, `critique-argument`, `critique-clarity`, `critique-docs`, `critique-forms`, `critique-microcopy`, `critique-usability`), a documentation site generated from this repository, the Critique Contract (finding schema, run envelope, disposition log) frozen with a JSON Schema and validator, the `critique-critic` clean-context subagent, a deterministic seeded-defect benchmark with 851 committed run envelopes across two pinned model tiers, `--gate` mode for CI, and Convergent (Silver) conformance with 0 errors and 0 warnings.

Full detail: [`CHANGELOG.md`](CHANGELOG.md) and [`RELEASE-NOTES.md`](RELEASE-NOTES.md). Measured numbers: [`bench/results/README.md`](bench/results/README.md).

---

<a id="next-v01x"></a>

## Done: v0.1.x

Patch-scope only: bug reports on scripted checks, contract schema errata, severity-anchor wording fixes, README clarity. No new skills and no new criteria land in a patch.

The largest piece of this version is a verification pass that was structurally impossible before the first push to a public remote, because it depends on things that do not exist in a private, unpushed repository:

- **Live Actions planted-failure checks.** Each CI job that is supposed to fail on a bad input needs to actually run on GitHub's infrastructure and actually fail, not just look correct on inspection. **(Met 2026-09-14.)**
- **Tag-guard end to end, from a scratch clone.** `release.yml`'s version guard has to be exercised against a fresh clone rather than the working tree it was authored in. **(Met 2026-09-15.)**
- **CI runtime measurement**, targeted under 4 minutes, which can only be measured once CI is running on real infrastructure instead of being reasoned about from the workflow YAML. **(Met 2026-09-14: 31, 41 and 67 seconds across three `main` runs.)**
- **The first live `bench.yml` dispatch**, to confirm the reproduction harness reproduces the numbers that were generated during the agentic build run, on infrastructure the maintainer does not control end to end. **(Run 2026-08-17 on Haiku and 2026-09-15 on Sonnet. The answer was no.)** On Sonnet, the rewritten harness does not reproduce the published figures within their measured run-to-run spread. The published v0.1.0 figures therefore stand as the measurement of record, with that caveat stated beside them ([ADR 0030](docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md), amended 2026-09-25). Each skill is re-measured through the current harness when a release changes it, starting with `critique-forms` in v0.2.0.

Carried alongside that pass: any fix-list items still open from the v0.1.0 run that did not rise to release-blocking.

**Exit gate:** two consecutive weeks with no open contract or check defect. **(Declared met 2026-09-13, [ADR 0034](docs/internal/decisions/0034-v0.1.x-exit-gate-declaration.md).)**

---

<a id="then-v020"></a>

## Done: v0.2.0

**Released 2026-10-15, with every exit-gate clause below met.**

**Re-cut on 2026-09-14.** This section used to promise a wider catalog on a regenerated research spine: the taxonomy survey, three new skills, BYOR, telemetry and a samples corpus, all in one version. Its exit gate required every one of them, including a chart-critique skill blocked on a generator nobody had scoped, so the version could not close. The re-cut v0.2.0 did two things. It makes every receipt the project already publishes whole, and it adds one skill. Everything that moved is listed under "Moved out of v0.2.0" below, with where it went.

**1. Measurement debt from the v0.1.0 run**, closed here rather than carried further:

   - ~~Per-entry `run_set` and a lane dimension added to the results schema~~ **(done 2026-09-14)**.
   - ~~`critique-usability`'s Sonnet cell re-measured~~ **(done 2026-09-25)**. It still does not qualify against baseline on that tier; see "Known limitations" below.
   - ~~The methodology's location-level metrics section written up properly~~ **(done 2026-10-15)**.
   - ~~`verdicts.md` rewritten as one document instead of a layered amendment trail~~ **(done 2026-10-15)**.
   - ~~An automated check for the evidence-quotes-not-characterizes field contract~~ **(done 2026-10-14)**.
   - ~~`severity_expected` scoring turned on~~ **(done 2026-10-14)**.
   - ~~The example and golden envelopes carry only real model values or a documented sentinel, not run metadata written by hand~~ **(done 2026-10-14)**.
   - ~~The benchmark harness isolated from the working tree it measures, and the Claude Code CLI version it installs pinned or recorded~~ **(done 2026-10-15)**.

**2. Consistency threshold v2.** **Done 2026-10-15** ([ADR 0038](docs/internal/decisions/0038-consistency-threshold-v2-per-tier-floors.md)). The single 0.309 floor was a provisional number measured once, on one run set. It is replaced by a floor per tier on the overall lane: 0.450 on Sonnet, from the current benchmark harness, and 0.309 on Haiku, carried until the core skills have current-harness Haiku data. The scripted lane has an expected value of 1.000, and the judged lane is published as a diagnostic.

**3. `critique-forms`**: form-usability critique sourced to Wroblewski, Baymard's research, GOV.UK, web.dev and others. It is built and registered `experimental` (PR 60): 24 criteria, 18 checked by script and 6 by judgment. **It shipped on 2026-10-06** ([ADR 0037](docs/internal/decisions/0037-critique-forms-ship-verdict.md)) and is now `active`, in the README catalog, the scoreboard and the site. Its figures are the first to come from the current benchmark harness, measured at k=5 on both pinned tiers with the generic baseline beside it in the same run. On Haiku it beats the baseline on both location metrics; on Sonnet it leads on recall, and its precision lead sits inside run-to-run noise. It came before `critique-deck` because it reuses the shipped HTML artifact type and `critique-accessibility`'s element resolver, while a deck skill needs a corpus module for an artifact type this project has never built.

**4. Astro docs site: shipped 2026-08-22, ahead of the samples corpus.** It moved ahead on 2026-08-18, when the README was ruled the project's front door, which made the site a prerequisite for fixing the README. None of the three trigger conditions this item named had fired, and saying so is more honest than retrofitting one.

**The site is live as of 2026-08-22** at `https://product-on-purpose.github.io/critique-skills/`. At launch it served 50 pages: the six skill pages, an explorer for all 96 criterion IDs, an explorer for every measured benchmark cell, the four Diataxis quadrants, and the worked examples. It is generated from this repository's own sources at build time and nothing lives only there. The old exit gate named the site as one of its conditions, and the site met it; the re-cut gate below does not repeat a condition that is already met.

**Exit gate** (re-cut 2026-09-14):

- Every entry in `bench/results/results.json` carries `run_set` and `lane` **(met 2026-09-14)**, and `bench.report` drift-checks the judged and scripted columns **(met 2026-10-14)**.
- At least one Sonnet envelope per skill is committed through the shipped harness, and the fidelity-gate verdict is re-evaluated on that tier **(met 2026-10-14)**. The verdict was re-evaluated on 2026-09-15 and came back a failure (see v0.1.x above). All seven skills now have Sonnet envelopes through the shipped harness: four dispatches on 2026-10-14 added `critique-accessibility`, `critique-argument`, `critique-docs` and `critique-microcopy`. Read against their published bands, `critique-microcopy` lands inside on both gated figures, and `critique-argument` and `critique-accessibility` each miss one figure by less than half the band's width. `critique-docs` misses a band of zero width by one stray claim ([ADR 0031](docs/internal/decisions/0031-fidelity-gate-acceptance-band.md)).
- Consistency threshold v2 is published with its method **(met 2026-10-15, [ADR 0038](docs/internal/decisions/0038-consistency-threshold-v2-per-tier-floors.md))**.
- No `run.model` value outside the two pinned tiers appears under `skills/` or `examples/`, unless it is a documented sentinel, and a check enforces that **(met 2026-10-14)**.
- `bench/results/verdicts.md` is one current-state document **(met 2026-10-15)**.
- `severity_expected` is scored in the results table **(met 2026-10-14)**.
- The evidence-quotes check runs in CI **(met 2026-10-14)**.
- ~~`bench/results/runs/steering/` no longer sits inside the `runs*` glob~~ **(met 2026-09-14)**.
- ~~A recorded ruling exists on `askit-*` authoring and CodeQL~~ **(met 2026-09-15: both adopted, CodeQL shipped)**.
- `critique-forms` is measured at k=5 on both pinned tiers, and a recorded ship or hold verdict cites the figures. On a ship verdict it appears in the README scoreboard; on a hold it stays `experimental`, with its figures published in the full results table. **(Met 2026-10-06: shipped, [ADR 0037](docs/internal/decisions/0037-critique-forms-ship-verdict.md).)**

### Moved out of v0.2.0

| Item | Now | Why |
|---|---|---|
| Taxonomy survey regeneration | Unscheduled | Deferred on 2026-09-14. The library still makes no claim about how many critique frameworks exist, and will not until the survey runs. |
| `critique-deck` | Dropped 2026-10-15 | Deprioritized behind `critique-forms` on 2026-09-14, then dropped: a critique of markdown slide source sees the text, but not the visual presentation that makes a slideshow work. |
| `critique-dataviz` | Unscheduled | It depends on a chart-spec corpus generator that has not been scoped, and dating a skill before its blocker is sized would be a guess. |
| BYOR mode | v0.3.0 | Unchanged in substance; it moves with the skill wave. |
| Disposition telemetry | v0.3.0 | Unchanged in substance. |
| Samples corpus | v0.4.0+ | Unchanged in substance. |

---

<a id="next-v030"></a>

## Next: v0.3.0

- **BYOR mode** (bring your own rubric) on one flagship skill, as the pattern-setter for every skill after it. This is what lets a user hand the library a rubric it did not ship with, using the `rubric_source: byor` finding marker already defined in the methodology.
- **Disposition telemetry begins.** Acceptance-rate-per-criterion data from real use starts feeding the first criterion pruning pass.
- **Revision loop as a first-class chain.** The critique, disposition, revise, re-critique loop exists today as a documented recipe (`examples/recipes/revision-loop.md`); this version makes it a real, invokable chain with a defined convergence rule.
- **Gate hardening.** `--gate` exit codes exercised and documented across every shipped skill as a CI recipe for consumer repositories, not just this one.
- **Cross-library composition.** One documented workflow where a sibling library's output is critiqued by this one, as the concrete proof of the family's think-make-judge value chain rather than an assertion about it.
- **Gold-tier groundwork.** Chain and hook evaluation coverage, folder-README and docs-frontmatter completion, source docblocks - conformance work that only becomes meaningful once the revision-loop chain above exists to evaluate.
- **Accessibility expansion.** `critique-accessibility` adds the five WCAG 2.2 success criteria it could check from markup and declared CSS and does not yet: 1.3.4 Orientation, 1.3.5 Identify Input Purpose, 2.4.7 Focus Visible, 2.5.8 Target Size (Minimum) and 4.1.3 Status Messages. That takes it from 22 to 27 of the 55 Level A and AA criteria, as a new skill version measured on both pinned tiers.

---

## After

### v0.4.0+

Priority among these is set by what telemetry from v0.3.0 onward says is actually pulling demand, not by the order listed here:

- **Samples corpus.** Worked, narrative samples distinct from the benchmark: multiple skills applied across a small set of running example threads, each following the same scenario-to-disposition shape, with machine-validated envelopes checked in CI and provenance honestly labeled as illustrative single runs, never conflated with k=5 measurement. Samples never enter `bench/` and never carry ground-truth manifests; that boundary is what keeps a compelling example from being mistaken for a measured claim.
- **Benchmark harness as a standalone asset.** Publishing the corpus generator and grading harness so third-party skill authors can measure their own skills against the same discipline this library holds itself to.
- **Remaining domain waves**, drawn from whatever the taxonomy survey admits once it runs: visual design, naming and terminology, and any newcomer the survey surfaces.
- **Further domain and Gold-tier work**, continued from v0.3.0 as coverage and telemetry justify it.

### Unscheduled

Accepted, but deliberately not given a version, because what they depend on has not been sized:

- **Taxonomy survey regeneration.** A real research pass across candidate critique frameworks, with a gate verdict per candidate against the Two-Part Gate, published as `docs/internal/research/critique-framework-survey.md`. Until it exists, the library makes no survey-scale claim.
- **`critique-dataviz`**: Tufte- and Cairo-sourced chart critique. It has the strongest demand signal of the planned skills and the hardest corpus problem, because chart-spec artifacts need a generator mode that does not exist yet.
- **`critique-payment-checkout`**: checkout and payment flow critique, from cart review to order confirmation. It waits on a research pass that decides how much of checkout a static page can measure.

---

## v1.0.0

v1.0 is a claim about **contract and criterion-registry stability**, not catalog size. It is declared when all of the following are true:

- Every shipped skill has survived a public benchmark cycle and a disposition-telemetry pruning pass.
- The survey-derived candidate slate is fully triaged: every candidate is shipped, deferred, or rejected with a recorded reason.
- Convergent (Silver) conformance is stable across two consecutive minor releases.
- At least one external consumer, a repository or workflow not owned by this project, gates in CI on a critique-skills finding contract.

At v1.0, the finding schema and the criterion ID registry freeze. A breaking change to either after that point is a v2 event, not a minor release. Adding a seventh skill, an eighth, or a fortieth is not what v1.0 is waiting on.

---

## Deliberately not doing

Scope discipline is a trust signal here, not an oversight. Four things this library will not do, on purpose:

- **Code review.** Well served elsewhere, by tools built for exactly that job. Out of scope by choice, not by gap.
- **Auto-fix.** Skills report findings; a human disposes them. Nothing here rewrites an artifact on its own authority, and that will not change as the catalog grows.
- **Taste-based criteria with no citable source.** Every criterion traces to a published standard with a URL or an ISBN, or to a rubric the user supplied themselves under BYOR mode. "This just feels better" does not clear the bar, no matter how often it would be correct.
- **Any skill that cannot be measured.** A seeded-defect corpus and a results table are load-bearing, not optional polish. A skill that cannot be measured against ground truth does not ship, regardless of how well-written its rubric is.

---

## Known limitations carried forward

Stated plainly rather than left for the results tables to surface on their own:

- **The consistency floors are low, and each rests on thin evidence.** The Haiku floor, 0.309, is still one measurement of `critique-clarity`, taken through the mechanism the current harness replaced. The Sonnet floor, 0.450, rests on committed envelopes that no published `results.json` scores yet. Both are well below the 0.7 figure proposed before any data existed. They are the floors because they are the lowest any core skill measured, not because they are comfortable numbers ([ADR 0038](docs/internal/decisions/0038-consistency-threshold-v2-per-tier-floors.md)).
- **`critique-usability`'s non-qualifying Sonnet cell.** Its Haiku tier beats baseline outright. At v0.1.0 its Sonnet tier won recall narrowly at a precision cost that did not clear the bar on that tier alone, and a 2026-09-15 re-measure through the shipped harness confirmed it: the skill now trails a re-run baseline on both location metrics, by margins inside run-to-run spread. The skill ships qualified through Haiku, not unconditionally.
- **`critique-accessibility` checks 22 of WCAG 2.2's 55 Level A and AA success criteria.** A report from it with no findings is not a conformance claim. Its reference file lists the 33 criteria it does not check and the reason for each. Most need a rendered page, live interaction, media files or several pages; five could be checked from markup and declared CSS and are not implemented.
- **Precision is the weak axis across the board.** Recall numbers are consistently the stronger of the two measured metrics; precision is where most of the remaining gap to a clean win sits, cell by cell.
- **No human acceptance data yet.** Every number published so far comes from the benchmark's seeded-defect corpus, not from real users disposing real findings. Disposition telemetry, which is what closes that gap, does not begin until v0.3.0.
- **The benchmark corpus is agent-generated.** The seeded defects, and the clean artifacts they are seeded into, were produced by the same class of system being measured, not hand-authored by an independent party. That is a known limitation of the measurement, not a hidden one.

<p align="right">(<a href="#roadmap-top">back to top</a>)</p>
