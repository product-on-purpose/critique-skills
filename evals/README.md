---
title: evals
---

# evals

Evaluation fixtures that span more than one skill. A fixture scoped to a single skill lives with
that skill, in `skills/<skill>/evals/`; this folder is for the ones that are only meaningful when
several skills are considered together.

There is exactly one such fixture today, and it exists because of a gap an external review found:
every skill's own `evals/triggers.eval.json` is validated in isolation, so nothing in the pipeline
ever compares one skill's description against another's. Six sibling skills in one namespace, all
of them about critique, is precisely where that matters.

**These fixtures are not scored in CI, and the distinction is deliberate.** Which skill fires is a
model decision over descriptions in context. A lexical proxy scored in CI would measure string
overlap rather than routing, and this library does not publish a number produced by a mechanism
other than the one being described (`docs/explanation/methodology.md`). What CI does enforce is
structural: that the fixture is well formed, that every skill it names exists, and that each
contested pair of skills carries a boundary clause in both descriptions naming the other. See
`scripts/tests/test_joint_routing_eval.py`, whose module docstring states that scope explicitly.

Each fixture's own `scoring` block records its mechanism and whether it has been run. A fixture
whose `status` is `not-yet-run` publishes no results, and a test enforces that.

## Inventory

- `joint-routing.eval.json` - ambiguous and control queries with an expected winner among the six
  skills, for scoring with all six descriptions in view at once. Distinguishes three case kinds:
  `contested` (a defensible single winner, plus the sibling it is contested with), `ambiguous` (no
  correct single winner, where asking for clarification is the right behavior), and `control`
  (unambiguous, present so a scoring run that fails these has a wiring problem rather than a
  discrimination problem).
