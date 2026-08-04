---
title: critique-skills recipes
description: Cross-cutting recipes showing how the pieces of this library work together, gating CI, the revision loop, and clean-context delegation
audience: both
level: intermediate
---

# critique-skills recipes

The five folders next to this one, `examples/accessibility/`, `examples/argument/`,
`examples/clarity/`, `examples/microcopy/`, and `examples/usability/`, each walk one skill through
one run: artifact in, findings out, a human's disposition on each finding. This folder is different.
It does not add a seventh domain. It shows how those single-run pieces connect to the parts of the
library that sit around them: a CI pipeline, a multi-round revision, and the clean-context subagent
every skill delegates to. Read at least one of the five walkthroughs above before this folder; the
recipes below assume you already know what a run envelope and a disposition log look like.

**Honesty labeling, restated for this folder.** Every recipe here marks its own parts, but the split
is the same shape throughout: exit-code behavior, `python -m contract.validate` output, and any
`scripts/checks.py` output shown are real commands run against real files before the page was
written, and re-running the printed command reproduces them bit for bit. Envelope excerpts built for
a fictional artifact are curated illustration, authored for this recipe, not the output of a live
model run; where that is the case, the recipe says so at the point it matters, not only here. Nothing
in this folder claims to be a live run when it is authored, and nothing authored is presented as if
`python -m contract.validate` could not tell the difference.

## Inventory

| File | What it shows |
|---|---|
| [`gate-in-ci.md`](gate-in-ci.md) | Wiring `contract/validate.py --gate` into a consumer repository's CI, worked through a tiny fictional repo: one run that fails the build (a severity-4 finding, exit 1) and one that passes it (exit 0), both gated for real. |
| [`revision-loop.md`](revision-loop.md) | One full turn of critique, disposition, revise, re-critique on a real golden fixture: two severity-3 findings, a human's accept decisions, a revision that answers both, and a re-critique that converges to zero. States the three-iteration bound and why an unbounded loop stops serving the rubric. |
| [`critic-delegation.md`](critic-delegation.md) | What clean-context critique means, how to invoke the `critique-critic` subagent from a host session, what its steering-strip behavior actually does (evidenced from recorded bench runs, not just asserted), and the inline fallback a skill runs when no subagent tool is available. |

## See also

- [Gate in CI](../../docs/how-to/gate-in-ci.md), the full how-to this folder's first recipe builds a
  worked example on top of.
- [Dispositions](../../docs/how-to/dispositions.md), the full disposition-log reference the second
  recipe uses.
- [`agents/critique-critic.md`](../../agents/critique-critic.md), the subagent definition the third
  recipe walks through.
- [Methodology](../../docs/explanation/methodology.md), sections 7 and 10, for the clean-context and
  human-in-the-loop design behind all three recipes.
- [Critique contract](../../docs/reference/critique-contract.md), the field and gate reference every
  envelope excerpt in this folder conforms to.
