---
title: evals
---

# evals

Evaluation fixtures that span more than one skill. A fixture scoped to a single skill lives with
that skill, in `skills/<skill>/evals/`; this folder is for the ones that are only meaningful when
several skills are considered together.

The joint-routing fixture exists because of a gap an external review found:
every skill's own `evals/triggers.eval.json` is validated in isolation, so nothing in the pipeline
ever compares one skill's description against another's. Seven sibling skills in one namespace, all
of them about critique, is precisely where that matters.

**These fixtures are not scored in CI, and the distinction is deliberate.** Which skill fires is a
model decision over descriptions in context. A lexical proxy scored in CI would measure string
overlap rather than routing, and this library does not publish a number produced by a mechanism
other than the one being described (`docs/explanation/methodology.md`). What CI does enforce is
structural: that the fixture is well formed, that every skill it names exists, and that each
contested pair of skills carries a boundary clause in both descriptions naming the other. See
`scripts/tests/test_joint_routing_eval.py`, whose module docstring states that scope explicitly.

**The chain eval sets are the exception, and they do run in CI.** Each
`critique-<domain>.revision-loop.eval.json` covers one edge of `agents/_chain-permitted.yaml`, a
skill delegating its critique to `critique-critic`, and its cases test the revision loop's own
deterministic steps: the stop-check, and the revision brief it writes when the loop continues. No
case calls a model, so `skills/_shared/tests/test_revision_loop_evals.py` executes every case in the
`unit-python` job and compares each brief byte for byte with the file under `expected/`.

The joint-routing fixture's own `scoring` block records its mechanism and whether it has been run. A fixture
whose `status` is `not-yet-run` publishes no results, and a test enforces that.

## Inventory

- `joint-routing.eval.json` - ambiguous and control queries with an expected winner among the seven
  skills, for scoring with all seven descriptions in view at once. Distinguishes three case kinds:
  `contested` (a defensible single winner, plus the sibling it is contested with), `ambiguous` (no
  correct single winner, where asking for clarification is the right behavior), and `control`
  (unambiguous, present so a scoring run that fails these has a wiring problem rather than a
  discrimination problem).
- `joint-routing.results-haiku.json` - the same fixture scored on the other pinned tier.
  Both tiers are recorded, because a routing result from one model is not a claim about the other.
- `joint-routing.results-sonnet.json` - the scored output of that fixture, written by
  `scripts/run-joint-routing.py`. Records the model, `k`, every trial per case, and whether the
  answers were unanimous, so a shaky win is distinguishable from a solid one. Committed because
  this repository's rule is that no number appears anywhere that is not in a committed result file.
- `critique-accessibility.revision-loop.eval.json` - the eval set for the `critique-accessibility` to `critique-critic`
  edge of [the revision-loop workflow](../_workflows/critique-revision-loop.md), over
  `examples/accessibility/`: the loop continues at iteration 1 and writes a brief, and it stops without one at
  the three-iteration bound.
- `critique-argument.revision-loop.eval.json` - the eval set for the `critique-argument` to `critique-critic`
  edge of [the revision-loop workflow](../_workflows/critique-revision-loop.md), over
  `examples/argument/`: the loop continues at iteration 1 and writes a brief, and it stops without one at
  the three-iteration bound.
- `critique-clarity.revision-loop.eval.json` - the eval set for the `critique-clarity` to `critique-critic`
  edge of [the revision-loop workflow](../_workflows/critique-revision-loop.md), over
  `examples/clarity/`: the loop continues at iteration 1 and writes a brief, and it stops without one at
  the three-iteration bound.
- `critique-docs.revision-loop.eval.json` - the eval set for the `critique-docs` to `critique-critic`
  edge of [the revision-loop workflow](../_workflows/critique-revision-loop.md), over
  `examples/docs/`: the loop continues at iteration 1 and writes a brief, and it stops without one at
  the three-iteration bound.
- `critique-forms.revision-loop.eval.json` - the eval set for the `critique-forms` to `critique-critic`
  edge of [the revision-loop workflow](../_workflows/critique-revision-loop.md), over
  `examples/forms/`: the loop continues at iteration 1 and writes a brief, and it stops without one at
  the three-iteration bound.
- `critique-microcopy.revision-loop.eval.json` - the eval set for the `critique-microcopy` to `critique-critic`
  edge of [the revision-loop workflow](../_workflows/critique-revision-loop.md), over
  `examples/microcopy/`: the loop continues at iteration 1 and writes a brief, and it stops without one at
  the three-iteration bound.
- `critique-usability.revision-loop.eval.json` - the eval set for the `critique-usability` to `critique-critic`
  edge of [the revision-loop workflow](../_workflows/critique-revision-loop.md), over
  `examples/usability/`: the loop continues at iteration 1 and writes a brief, and it stops without one at
  the three-iteration bound.
- `expected/` - the revision brief each eval set's first case must produce, byte for byte, one
  `<domain>.revision-brief.json` per skill.
