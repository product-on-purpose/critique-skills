---
title: Methodology
description: How this library decides what belongs in it, how its skills produce findings, and how those findings are measured
audience: both
level: intermediate
---

# Methodology

How this library decides what belongs in it, how its skills produce findings, and how those findings are measured.

**Status:** v0.1 draft. Sections are marked `Stable`, `Provisional`, or `Open` so you can tell which parts are load-bearing commitments and which are still being calibrated against evidence.

---

## 1. The problem this library exists to solve

Ask a language model to critique your work and you get fluent, confident, forgettable commentary. It changes between runs. It cites nothing. It cannot tell you whether it found everything or merely something. It has no way to be wrong.

Three failures compound:

**Critique without authority is opinion.** A model asked to "act as a harsh critic" draws on the statistical average of critique it has read. That average is not a standard. There is no citation, no shared vocabulary, and no way for you to disagree on grounds other than taste.

**Critique without structure cannot be automated.** Free-form prose findings cannot feed a revision loop, gate a pipeline, or be counted. You can read them. You cannot compose them.

**Critique without ground truth cannot be trusted.** If nobody knows what defects an artifact actually contains, nobody can say whether the critique caught them. Recall is unmeasured, so quality is unfalsifiable.

This library's response is narrow and specific: **every skill operationalizes a published external rubric, emits machine-parseable findings with evidence, and reports measured performance against seeded defects.**

The claim is not that these skills critique better than a good model does. It is that they critique *accountably*, which is a different and more durable property. As models improve, generic critique gets better. It does not acquire citations, repeatability, or ground truth. Those are properties of the system built around the model.

---

## 2. The Two-Part Gate

**Status: Stable.** This is the library's constitution. It determines what becomes a skill, what gets rejected, and where the boundary sits with sibling libraries.

A candidate framework earns a skill only if it passes both parts.

### Part 1: Artifact dependency

**The framework must evaluate a concrete, inspectable artifact.**

An artifact is something that exists and can be examined: a document, a design, a deck, a message, a page, a diagram, a form. Not a situation. Not a decision. Not a plan for the future. If there is nothing to point at, there is nothing to cite as evidence, and every finding collapses into assertion.

The operational test: **can a finding name a location?** If a finding cannot say "Section 3, second paragraph" or "the hero banner" or "slide 7 title," the framework fails Part 1.

### Part 2: External rubric

**A published, citable standard must exist that the skill operationalizes.**

The skill does not invent criteria. It encodes someone else's, with attribution. The standard must be public, stable enough to cite, and specific enough to generate discrete criteria that can be given permanent identifiers.

The operational test: **can every criterion trace to a source with a URL or an ISBN?** If the criteria come from the skill author's judgment, the framework fails Part 2.

### Why both parts, and not either

Part 1 alone produces structured guesswork: findings with locations but no authority behind the judgment. Part 2 alone produces standards discourse: authoritative criteria applied to nothing checkable. Together they produce the only thing worth automating, which is a falsifiable claim about a specific object measured against a published standard.

### The gate applied

**Status: Provisional.** The domain slate below is a working proposal and needs reconciliation with the author's original 40-candidate, 13-domain survey. Treat the pass/fail column as directionally right and the specific membership as unsettled.

Passes both parts:

| Domain | Standard operationalized |
|---|---|
| Usability and interaction | [Nielsen's 10 usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) |
| Accessibility | [WCAG 2.2](https://www.w3.org/TR/WCAG22/) |
| Visual design and layout | CRAP principles (Robin Williams, *The Non-Designer's Design Book*); Gestalt grouping |
| Prose clarity | Joseph M. Williams, *Style: Lessons in Clarity and Grace*; [Federal Plain Language Guidelines](https://www.plainlanguage.gov/guidelines/) |
| Document structure | Minto Pyramid Principle (concepts, paraphrased) |
| Technical documentation | [Diátaxis](https://diataxis.fr/) |
| Argumentation | Toulmin model (Stephen Toulmin, *The Uses of Argument*) |
| Presentations | Assertion-evidence structure (Michael Alley, *The Craft of Scientific Presentations*) |
| Data visualization | Tufte principles; Alberto Cairo's qualities of great visualization |
| Error messages and microcopy | [NN/g error message guidelines](https://www.nngroup.com/articles/error-message-guidelines/) |
| Forms and input | Luke Wroblewski, *Web Form Design*; Baymard form usability research |
| Naming and terminology | Project glossary or style guide conformance (see BYOR, Section 3) |

Fails the gate, with reasons:

| Candidate | Fails | Why |
|---|---|---|
| SWOT analysis | Part 1 | Evaluates a situation, not an artifact |
| Pre-mortem | Part 1 | Prospective; the thing being assessed does not exist yet |
| Six Thinking Hats | Part 2 | A process protocol, not a standard with criteria |
| First-principles reasoning | Both | A lens, not a rubric, applied to problems rather than objects |
| "Is this strategy sound?" | Part 2 | No published rubric for strategic soundness that survives citation |
| "Does this feel on-brand?" | Part 2 | Unless a brand guide is supplied, in which case see BYOR |
| Code review | Out of scope | Passes the gate but is well served elsewhere; see Section 9 |

The rejections matter more than the acceptances. A gate that admits everything is not a gate.

---

## 3. Bring Your Own Rubric (BYOR)

**Status: Provisional.**

Part 2 requires a published standard, which excludes a large class of legitimate critique: conformance to *your* style guide, *your* brand system, *your* design tokens, *your* editorial policy.

BYOR resolves this without weakening the gate. A user supplies a rubric file; the skill operationalizes it using the same contract, the same severity scale, and the same evidence requirements. The standard is external to the model even though it is not public.

BYOR rubrics must declare criteria with stable IDs in the same format as bundled rubrics. A skill running in BYOR mode marks every finding with `rubric_source: byor` so downstream consumers can distinguish conformance findings from published-standard findings.

What BYOR is not: a hatch for taste. A rubric with criteria like "should feel modern" produces findings that cannot be evidenced, and the skill should refuse them.

---

## 4. Criterion identifiers

**Status: Stable.**

Every criterion has a permanent, uppercase, namespaced identifier. This is the single most important mechanism in the library, because IDs are what convert impressionistic critique into countable events.

Format: `<SOURCE>-<CRITERION>`

```
NNG-H4            Nielsen heuristic 4, consistency and standards
WCAG-1.4.3        WCAG 2.2 success criterion (use the standard's own IDs)
PLAIN-ACTIVE      Plain Language Guidelines, active voice
TOULMIN-WARRANT   Toulmin model, warrant present and stated
PYRAMID-MECE      Pyramid Principle, groupings mutually exclusive
DIATAXIS-MODE     Diátaxis, document does not mix modes
AE-TITLE          Assertion-evidence, slide title states an assertion
BYOR-<KEY>        User-supplied rubric criterion
```

Rules:

1. **IDs are permanent.** Once published, an ID is never reassigned to a different criterion. Retired criteria are marked deprecated, not deleted.
2. **Adopt upstream IDs where they exist.** WCAG has canonical success criterion numbers. Use them rather than inventing a parallel scheme.
3. **One criterion, one ID.** If a rubric item bundles two checkable things, split it.

IDs make findings diffable across runs, comparable across models, aggregable across artifacts, and countable in the benchmark. Nothing else in this document works without them.

---

## 5. The Critique Contract

**Status: Stable** for the finding schema, **Provisional** for the run envelope.

No finding exists without structure. Every skill emits findings in this shape:

```yaml
id: F-007
criterion: WCAG-1.4.3
lane: scripted            # scripted | judged
severity: 3               # 0-4, see Section 6
location: "Section 2, hero banner"
evidence: "body text #8a8a8a on background #f5f5f5"
violation: "Contrast ratio 2.9:1, below the 4.5:1 AA minimum"
fix: "Darken text to #595959 or darker"
confidence: high          # high | medium | low
```

Field contracts:

- **`location`** must be specific enough that a reader can navigate to it unaided. "Throughout the document" is not a location; if a problem recurs, emit one finding per instance or one finding with an instance list.
- **`evidence`** must be a short quotation or a measurement taken from the artifact, not a characterization of it. This is the field that makes a finding falsifiable.
- **`violation`** states which part of the criterion was breached, not merely that something is bad.
- **`fix`** must be actionable and specific. "Improve clarity" is not a fix.
- **`lane`** records whether the finding came from a deterministic script or from model judgment. Consumers weight these differently, and honesty here is the basis of the library's determinism claims.
- **`confidence`** applies to the judged lane. Scripted findings are always `high` or they are bugs.

Every run is wrapped in an envelope that makes results reproducible and comparable:

```yaml
run:
  skill: critique-clarity
  skill_version: 1.2.0
  contract_version: 1.0.0
  artifact: docs/prd.md
  artifact_sha256: cbf4787a1567f6fef3e683c5215533430d94a7ae8518ba1118eaa66385747bbf
  model: claude-sonnet-4-5-20250929
  timestamp: 2026-07-17T14:22:03Z
  rubrics: [PLAIN, PYRAMID]
findings: [ ... ]
summary:
  by_severity: { "0": 0, "1": 3, "2": 5, "3": 2, "4": 0 }
  suppressed_count: 3
  gate: fail
  severity_3_threshold: 0
```

`by_severity` counts every finding the run produced; `findings` carries only the ones it emitted. This run found ten, of which eight were below severity 3, so the output bound in Section 7 let five of those through and suppressed three: seven findings in `findings`, three in `suppressed_count`, and the sum of `by_severity` equal to the two added together. Nothing disappears, and the arithmetic is checkable, which is why the validator checks it.

The envelope is what makes `--gate` mode possible: a CI job reads `summary.by_severity` and exits nonzero on any severity 4, or on severity 3 counts above `summary.severity_3_threshold`. It is also what makes benchmark results honest, because model ID, skill version, and contract version are pinned to every number the library publishes.

`severity_3_threshold` is policy, and the run that carries it is produced by the skill being judged. An envelope may therefore declare a threshold that passes itself; the validator warns when a run passes only because of one, and a consumer that gates on someone else's envelope should set the threshold rather than read it.

---

## 6. Severity

**Status: Provisional.** The scale is adopted; cross-domain anchoring is still being calibrated.

The library uses one severity scale everywhere, adapted from [Nielsen's severity ratings](https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/). One scale across all domains beats bespoke scales per skill, because vocabulary drift is the largest single source of run-to-run inconsistency.

| Level | Meaning | Disposition |
|---|---|---|
| 0 | Not a problem. Noted and dismissed. | Ignore |
| 1 | Cosmetic. Fix only if time permits. | Optional |
| 2 | Minor. Low priority. | Backlog |
| 3 | Major. Important to fix. | Fix before release |
| 4 | Catastrophic. Imperative to fix. | Blocking |

Severity is assigned by weighing three factors, in this order:

1. **Impact.** How much does this obstruct the reader or user? Can they recover?
2. **Frequency.** Does it occur once, or throughout the artifact?
3. **Persistence.** Is it a one-time stumble, or does it compound as the reader continues?

Domain anchoring: the numeric scale is fixed, but each skill's reference file supplies domain-specific anchor examples so that a severity 3 in prose critique means something comparable to a severity 3 in accessibility critique. Whether the scale generalizes cleanly from interaction design to argumentation is an open empirical question, and the anchors will be revised as consistency data accumulates.

Severity is never inflated to get attention. A library where everything is a 4 is a library nobody gates on.

---

## 7. Determinism model

**Status: Stable** in principle, **Provisional** in thresholds.

The design principle: **compute what is computable, and spend model judgment only where judgment is required.**

### Two lanes

Every skill splits its criteria into two lanes and declares the split in frontmatter:

```yaml
checks:
  scripted: [readability_grade, passive_ratio, heading_orphans, link_integrity]
  judged: [pyramid_order, audience_fit, mece_grouping]
```

**The scripted lane** runs in `scripts/checks.py` and is bit-for-bit reproducible: readability grades, passive-voice ratios, sentence-length distributions, heading depth and orphan detection, alt-text presence, contrast ratios, link integrity, and the machine-checkable subset of WCAG. Same input, same output, every time, on any model.

**The judged lane** requires a model: audience fit, argument structure, heuristic violations, whether a grouping is genuinely MECE.

The manifest makes the determinism claim auditable per skill rather than asserted globally. The library never claims the judged lane is deterministic. It claims the judged lane is *measured*, which is Section 8.

### The four-pass protocol

Judged-lane critique follows a fixed sweep order in every skill:

1. **Inventory.** Map the artifact's structure. No judgments, no findings. This pass exists to prevent the model from anchoring on whatever it noticed first.
2. **Criterion sweep.** Walk the rubric in fixed ID order, evaluating each criterion against the whole artifact. Fixed ordering suppresses salience-driven wandering, where a model fixates on one vivid flaw and free-associates outward from it.
3. **Severity assignment.** Rate every finding against the Section 6 anchors, as a separate pass. Assigning severity while discovering problems inflates it.
4. **Rank and bound.** Order by severity, then apply the output bound.

### Output bounding

Verbosity is variance. Runs that emit twenty findings one time and sixty the next cannot be compared. Skills report all severity 3 and 4 findings plus at most five below that threshold, with forced ranking. Suppressed findings are counted in the summary so nothing disappears silently.

### Clean-context critique

Critique runs in a fresh context that has not seen the artifact being authored. A critic that inherits the author's framing inherits the author's blind spots. Where subagents are available, the critic runs as one.

---

## 8. Evaluation

**Status: Provisional.** The methods are settled; the thresholds are not.

The library publishes its own performance. Four measures:

### Seeded-defect recall

A deterministic generator produces synthetic artifacts with a manifest of planted violations keyed to criterion IDs. Because ground truth is known, recall and precision are directly computable:

- **Recall:** what fraction of planted defects did the skill find?
- **Precision:** what fraction of reported findings correspond to planted defects or to genuine unplanted ones?

Generation is seeded and reproducible, so the corpus is a stable target across skill versions.

### Run-to-run consistency

Each skill is run k=5 times against the same artifact. Consistency is the mean pairwise Jaccard similarity over the set of `(criterion_id, location)` pairs.

An initial target of 0.7 is proposed as a release gate. This number is a placeholder and will be replaced by an empirically calibrated threshold once baseline data exists. It is entirely possible that the realistic ceiling for judged-lane consistency is lower, in which case the target moves and the library says so publicly.

### Baseline comparison

Every skill is compared against a generic prompt ("critique this document") on the same corpus, on at least two model tiers. A skill that does not beat the baseline does not ship. Results tables pin model IDs and dates, because these numbers decay.

### Acceptance rate

Disposition logs (Section 10) record accept, reject, or defer per finding ID. Acceptance rate per criterion is the library's pruning signal: criteria that consistently produce rejected findings are either badly operationalized or not worth checking, and get revised or retired.

Published results live in `bench/results/` with the raw run envelopes, not just summary tables.

---

## 9. What this library is not

**Status: Stable.**

**Not a thinking-framework library.** Sibling libraries cover upstream reasoning: lenses applied to problems, decisions, and situations before an artifact exists. Those frameworks fail Part 1 of the gate by design. The relationship is a value chain: think, make, judge, revise. A pre-mortem is thinking. A heuristic evaluation is critique. "Red-team this strategy" is thinking, unless scored against a published rubric, in which case it graduates.

**Not code review.** Code review passes the gate but is already well served by dedicated tools and skills, and it has different evidence conventions. Out of scope by choice, not by principle.

**Not auto-fix.** Skills report; they do not edit. See Section 10.

**Not taste.** If a criterion cannot cite a source, it does not exist here. The library has no opinion of its own, and that is the point.

---

## 10. Human-in-the-loop by contract

**Status: Stable.**

Critique never auto-applies fixes. This is a contract, not a default setting.

The reason is not caution. It is that the disposition step is where the value is, and where the library's telemetry comes from. For each finding the human records accept, reject, or defer, producing a disposition log keyed to finding and criterion IDs.

That log does three jobs: it keeps judgment with the person accountable for the artifact, it produces the acceptance-rate signal that drives criterion pruning, and it makes the revision loop auditable.

The revision loop, when used, is bounded: critique, disposition, revise, re-critique, stopping when zero findings remain at severity 3 or above or after three iterations, whichever comes first. Unbounded loops converge on the model's preferences, not the rubric's.

---

## 11. Provenance and intellectual property

**Status: Stable.**

Every skill declares its sources in frontmatter:

```yaml
rubric_sources:
  - id: NNG-HEURISTICS
    citation: "Nielsen, J. (1994, updated 2024). 10 Usability Heuristics for User Interface Design. Nielsen Norman Group."
    url: https://www.nngroup.com/articles/ten-usability-heuristics/
    accessed: 2026-07-17
    operationalization: paraphrased
```

The `operationalization` field is a policy, not documentation:

- **`paraphrased`** means the skill encodes an operationalization of the source in original wording, with citation. Required for all copyrighted material, including NN/g articles and the Pyramid Principle.
- **`open-standard`** means the source is openly licensed and may be referenced directly. WCAG is a W3C standard; Diátaxis is openly published.
- **`byor`** means the rubric was supplied by the user.

The library never reproduces copyrighted rubric text. It encodes checkable operationalizations and points to the original. Contributors who paste source text will have the contribution rejected.

---

## 12. Contributing a skill

**Status: Provisional.**

A contribution is reviewed against this document in order:

1. **Gate.** Does the framework pass both parts? State the artifact it evaluates and the standard it operationalizes, with a link.
2. **IDs.** Are criteria enumerated with permanent, namespaced identifiers?
3. **Lanes.** Is the scripted/judged split declared, and is the scripted lane actually deterministic?
4. **Contract.** Do findings conform to Section 5, with real locations and quoted or measured evidence?
5. **Severity.** Are domain anchors supplied for the shared 0-4 scale?
6. **Provenance.** Are sources cited with the correct `operationalization` value, and is no source text reproduced?
7. **Evidence.** Is there a seeded corpus and a results table? A skill with no measured performance is a draft, not a contribution.

Step 7 is the one most likely to be skipped and the one least negotiable. The library's entire claim is that its skills are measured. A well-written unmeasured skill weakens that claim more than a missing skill does.

---

## 13. Open questions

These are unresolved and are stated here rather than hidden:

- **Domain slate.** The Section 2 table is a working proposal and needs reconciliation against the original 40-candidate survey. Membership will change.
- **Cross-domain severity.** Whether Nielsen's anchors transfer cleanly to prose and argumentation is untested. Per-domain anchor wording under a shared numeric scale is the current hypothesis.
- **Consistency ceiling.** The 0.7 target is a placeholder with no empirical basis yet.
- **Location granularity.** There is no settled convention for locating findings in non-linear artifacts such as designs and dashboards. Text artifacts are straightforward; visual ones are not.
- **Instance explosion.** A criterion violated forty times should probably not produce forty findings, but the aggregation rule is undecided.
- **Model sensitivity.** Consistency and recall vary by model and version. How often benchmarks must be re-run to stay honest is unknown.

---

*This document governs the library. Where a skill and this document disagree, this document is correct and the skill is a bug.*
