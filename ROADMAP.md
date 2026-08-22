<a id="roadmap-top"></a>

# Roadmap

This is a public statement of sequence, not a schedule. It says what shipped, what is next, what depends on what, and - as much as anything else - what has not shipped yet.

## How to read this

**Sequence-only, no dates.** Every version below is gated by the exit criteria of the version before it. `v0.2.0` does not open until `v0.1.x`'s exit gate closes; `v0.3.0` does not open until `v0.2.0`'s does. This is a solo-maintained project that publishes its own honest measurement numbers, and a solo maintainer who commits to dates ends up choosing between missing them in public or quietly padding the numbers to hit them. Sequence-gating avoids that trade entirely: a version opens when its prerequisite work is actually done, not when a calendar says it should be.

**This document is also a list of what is not done.** Reading only the "Now" section tells you what exists. Reading the rest tells you, just as precisely, what does not: no taxonomy survey yet, no BYOR mode yet, no docs site deployed yet, no revision loop as a first-class chain yet. Treat every "Then" and "After" item as a feature this library does not currently have, not a promise about when it will.

**Where the numbers live.** Nothing on this page overrides the measured results. `bench/results/README.md` is the source of truth for what the library actually catches; this page only sequences the work that produces future measurements.

---

## Now: v0.1.6

Six patch releases have shipped since `v0.1.0`. None added a skill, a criterion, or a re-score, which is what patch scope means here; each fixed defects found by running something that had never been run. `CHANGELOG.md` carries the detail.

Shipped: six measured critique skills (`critique-accessibility`, `critique-argument`, `critique-clarity`, `critique-docs`, `critique-microcopy`, `critique-usability`), the Critique Contract (finding schema, run envelope, disposition log) frozen with a JSON Schema and validator, the `critique-critic` clean-context subagent, a deterministic seeded-defect benchmark with 502 committed run envelopes across two pinned model tiers, `--gate` mode for CI, and Convergent (Silver) conformance with 0 errors and 0 warnings.

Full detail: [`CHANGELOG.md`](CHANGELOG.md) and [`RELEASE-NOTES.md`](RELEASE-NOTES.md). Measured numbers: [`bench/results/README.md`](bench/results/README.md).

---

## Next: v0.1.x

Patch-scope only: bug reports on scripted checks, contract schema errata, severity-anchor wording fixes, README clarity. No new skills and no new criteria land in a patch.

The largest piece of this version is a verification pass that was structurally impossible before the first push to a public remote, because it depends on things that do not exist in a private, unpushed repository:

- **Live Actions planted-failure checks.** Each CI job that is supposed to fail on a bad input needs to actually run on GitHub's infrastructure and actually fail, not just look correct on inspection.
- **Tag-guard end to end, from a scratch clone.** `release.yml`'s version guard has to be exercised against a fresh clone rather than the working tree it was authored in.
- **CI runtime measurement**, targeted under 4 minutes, which can only be measured once CI is running on real infrastructure instead of being reasoned about from the workflow YAML.
- **The first live `bench.yml` dispatch**, to confirm the reproduction harness reproduces the numbers that were generated during the agentic build run, on infrastructure the maintainer does not control end to end.

Carried alongside that pass: any fix-list items still open from the v0.1.0 run that did not rise to release-blocking.

**Exit gate:** two consecutive weeks with no open contract or check defect.

---

## Then: v0.2.0

Widening the skill base and regenerating the research spine underneath the catalog, roughly in this order:

**1. Taxonomy survey regeneration.** The library currently makes no public claim about how many critique frameworks exist or how many domains they span, because no such survey has actually been run. This version runs a real research pass across candidate critique frameworks, records a gate verdict per candidate against the Two-Part Gate, and publishes it as `docs/internal/research/critique-framework-survey.md`. This gates the survey-scale claim: until the survey exists, the library does not make it.

**2. Second skill wave**, 2-3 skills, sequenced by the survey's findings but expected to run:

   - `critique-deck` first: assertion-evidence presentation critique. Markdown decks are a scriptable artifact format and the corpus work is straightforward, so it is the lowest-risk next skill.
   - `critique-forms` second: Wroblewski- and Baymard-sourced form-usability critique. HTML forms have a strong scriptable share and the skill reuses accessibility's existing HTML tooling rather than building new infrastructure.
   - `critique-dataviz` third: Tufte- and Cairo-sourced chart critique. This has the strongest demand signal of the three but the hardest corpus problem, because chart-spec artifacts need a new generator mode that does not exist yet. It goes last because it is the only one that is blocked on new infrastructure rather than reuse.

**3. BYOR mode** (bring your own rubric) on one flagship skill, as the pattern-setter for every skill after it. This is what lets a user hand the library a rubric it did not ship with, using the `rubric_source: byor` finding marker already defined in the methodology.

**4. Measurement debt from the v0.1.0 run**, closed here rather than carried further: per-entry `run_set` and a lane dimension added to the results schema; the methodology's location-level metrics section written up properly; `verdicts.md` rewritten as one document instead of a layered amendment trail; an automated check for the evidence-quotes-not-characterizes field contract; `severity_expected` scoring turned on; and `critique-usability`'s Sonnet cell re-measured, the one precision cell that still does not qualify against baseline on its own tier.

**5. Consistency threshold v2.** The 0.309 floor below is a provisional number measured once, on one run set. This version replaces it with a calibrated per-lane threshold, published with its method rather than asserted.

**6. Disposition telemetry begins.** Acceptance-rate-per-criterion data from real use starts feeding the first criterion pruning pass.

**7. Samples corpus.** Worked, narrative samples distinct from the benchmark: multiple skills applied across a small set of running example threads, each following the same scenario-to-disposition shape, with machine-validated envelopes checked in CI and provenance honestly labeled as illustrative single runs, never conflated with k=5 measurement. Samples never enter `bench/` and never carry ground-truth manifests; that boundary is what keeps a compelling example from being mistaken for a measured claim.

**8. Astro docs site. This item's sequence position was overtaken on 2026-08-18 and the site is being built now, ahead of the samples corpus.** The original order put it after the samples on the reasoning that they are the content which gives a site an information architecture worth designing, and that a site built before that content exists is just a nicer-looking README. That reasoning still holds for the site's *content*, and it is not what moved the item. What moved it was a decision that the README is the project's front door, which makes the site a prerequisite for fixing the README rather than a reward for finishing the samples. **None of the three trigger conditions this item named actually fired**: the README is 517 lines against the roughly 600 named here, the marketplace listing has produced no traffic worth calling real, and no public essay has shipped. The item was pulled early for a reason it did not anticipate, and saying so is more useful than retrofitting a trigger. Work in progress: the scaffold and the generated documentation tree exist and build, nothing is deployed, and the exit gate below still reads "docs site deployed", which is unchanged and unmet.

**Exit gate:** survey published; every listed skill measured; BYOR pattern documented and shipped on one skill; docs site deployed; every new component in this version built and measured to the same bar as v0.1.0.

---

## After

### v0.3.0

- **Revision loop as a first-class chain.** The critique, disposition, revise, re-critique loop exists today as a documented recipe (`examples/recipes/revision-loop.md`); this version makes it a real, invokable chain with a defined convergence rule.
- **Gate hardening.** `--gate` exit codes exercised and documented across every shipped skill as a CI recipe for consumer repositories, not just this one.
- **Cross-library composition.** One documented workflow where a sibling library's output is critiqued by this one, as the concrete proof of the family's think-make-judge value chain rather than an assertion about it.
- **Gold-tier groundwork.** Chain and hook evaluation coverage, folder-README and docs-frontmatter completion, source docblocks - conformance work that only becomes meaningful once the revision-loop chain above exists to evaluate.

### v0.4.0+

Priority among these is set by what telemetry from v0.2.0 and v0.3.0 says is actually pulling demand, not by the order listed here:

- **Benchmark harness as a standalone asset.** Publishing the corpus generator and grading harness so third-party skill authors can measure their own skills against the same discipline this library holds itself to.
- **Remaining domain waves**, drawn from whatever the v0.2.0 survey admits: visual design, naming and terminology, and any newcomer the survey surfaces.
- **Further domain and Gold-tier work**, continued from v0.3.0 as coverage and telemetry justify it.

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

- **The 0.309 consistency floor.** Run-to-run agreement on `critique-clarity`'s Haiku cell calibrated to 0.309, well below the 0.7 figure proposed before any data existed. It is the floor because it is the lowest any core skill measured, not because it is a comfortable number.
- **`critique-usability`'s non-qualifying Sonnet cell.** Its Haiku tier beats baseline outright; its Sonnet tier wins recall narrowly at a precision cost that does not clear the bar on that tier alone. The skill ships qualified through Haiku, not unconditionally.
- **Precision is the weak axis across the board.** Recall numbers are consistently the stronger of the two measured metrics; precision is where most of the remaining gap to a clean win sits, cell by cell.
- **No human acceptance data yet.** Every number published so far comes from the benchmark's seeded-defect corpus, not from real users disposing real findings. Disposition telemetry, which is what closes that gap, does not begin until v0.2.0.
- **The benchmark corpus is agent-generated.** The seeded defects, and the clean artifacts they are seeded into, were produced by the same class of system being measured, not hand-authored by an independent party. That is a known limitation of the measurement, not a hidden one.

<p align="right">(<a href="#roadmap-top">back to top</a>)</p>
