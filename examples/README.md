---
title: critique-skills examples
description: Every worked walkthrough and cross-cutting recipe in this repository, organized by what you're trying to do
audience: both
level: beginner
---

# critique-skills examples

Nine pages, each self-contained and runnable or verifiable against files sitting right next to it.
Six are one-skill walkthroughs: an artifact, one skill's critique of it, and a human's disposition
on each finding. Three are recipes: how the pieces of this library click together across a CI
pipeline, a multi-round revision, and the clean-context subagent every skill delegates to. Start
with whichever row below matches what you are actually trying to do; the six walkthroughs assume
nothing beyond QUICKSTART.md, and the three recipes assume you have already read at least one of
them.

## Honesty labeling, explained once

Every page in this folder keeps two different kinds of content visibly apart, and restates which is
which at the point it matters, not only here:

- **Scripted lane, bit-for-bit reproducible.** Findings or output described as `lane: scripted`
  come from a deterministic script, a skill's own `scripts/checks.py`, or `contract/validate.py`
  for envelope and disposition-log checks. Run the exact command printed on the page yourself and
  you get the same output, field for field; only a timestamp or a file path ever differs.
- **Judged lane, curated from a validated golden fixture.** Findings described as `lane: judged`
  come from a model reading an artifact's meaning against a rubric. No page in this folder ran that
  model call live and pasted in the result; each one is copied verbatim from the skill's own golden
  envelope, a fixture checked into that skill's test suite and validated with
  `python -m contract.validate` before it was accepted. A fresh judged-lane run against the same
  artifact should land on the same criteria and severities; the exact wording of a `violation` or
  `fix` can vary run to run, the way any model output does.
- **Curated illustration.** Disposition logs, findings-tour commentary, and (inside `recipes/`) one
  fictional consumer repository are authored for these pages, not sampled from a live run. Each page
  says so at the point it matters.

Nothing here presents authored content as a live run, and nothing here hides which parts are which.

## Critique a document

| I want to... | Go to | What you'll see |
|---|---|---|
| Critique an HTML page for accessibility (WCAG 2.2) | [`accessibility/`](accessibility/README.md) | A small internal dashboard failing contrast, alt text, and heading-structure checks: six scripted findings and a disposition log. |
| Critique argumentative prose (Toulmin model) | [`argument/`](argument/README.md) | An onboarding-pilot memo checked for claim, grounds, warrant, backing, qualifier, and rebuttal, including the scripted lane's hedge-density and claim-marker checks. |
| Critique prose for clarity (Federal Plain Language Guidelines, Williams' Style) | [`clarity/`](clarity/README.md) | A three-sentence checklist and notification paragraph where two rubrics, and two lanes, each catch a genuinely different problem in the same few words. |
| Critique a docs page against Diataxis | [`docs/`](docs/README.md) | A how-to page for resetting a password that quietly widens into a second task: one severity-3 judged finding and one severity-2 scripted finding, both tracing to the same root cause. |
| Critique error messages and other microcopy (NN/g) | [`microcopy/`](microcopy/README.md) | Three annotated signup and checkout error strings, both lanes, run against this skill's richest golden fixture. |
| Critique a UI spec for usability (Nielsen's heuristics) | [`usability/`](usability/README.md) | A "Team workspace settings" spec: an unconfirmed delete-workspace control, a mislabeled button, and an unhelpful bulk-import error message. |

## See how the pieces fit together

| I want to... | Go to | What you'll see |
|---|---|---|
| Wire a quality gate into CI | [`recipes/gate-in-ci.md`](recipes/gate-in-ci.md) | A fictional storefront repo's CI job running `contract/validate.py --gate`: one run that fails the build on a seeded defect, one that passes after the fix, both exit codes real. |
| Run a full revision loop: critique, disposition, revise, re-critique | [`recipes/revision-loop.md`](recipes/revision-loop.md) | Two severity-3 findings from a real golden fixture, a human's accept decisions, a revision that answers both, and a re-critique that converges to zero, plus the three-iteration bound and why it exists. |
| Delegate critique to a clean-context subagent | [`recipes/critic-delegation.md`](recipes/critic-delegation.md) | What clean-context critique means, how to invoke `critique-critic` directly, steering-strip evidence pulled from recorded bench runs, and the inline fallback a skill uses when no subagent tool is available. |

[`recipes/README.md`](recipes/README.md) is that folder's own entry point if you want the recipes'
shared framing before picking one.

## See also

- [Methodology](../docs/explanation/methodology.md), the design behind clean-context critique, the
  human-in-the-loop contract, and the revision-loop bound the recipes above build on.
- [Critique contract](../docs/reference/critique-contract.md), the field-by-field envelope reference
  every `envelope.json` in this folder conforms to.
- [Dispositions](../docs/how-to/dispositions.md), the full shape and purpose of the disposition-log
  format used in every walkthrough above.
- [Severity scale](../docs/reference/severity-scale.md), the 0-4 scale every finding's severity
  comes from.
- `QUICKSTART.md`, the five-minute path if you have not run a critique in this repository at all
  yet.
