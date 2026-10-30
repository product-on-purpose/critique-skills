---
title: critique-argument
---

# critique-argument

Reviews argumentative prose - essays, proposals, position papers, recommendation memos, strategy
docs, and op-eds - against the Toulmin model of argument: whether the claim, grounds, warrant,
backing, qualifier, and rebuttal are present, explicit, and actually hold together. Version 0.1.1.

## Inventory

- `SKILL.md` - the skill's frontmatter, trigger description, and four-pass protocol instructions.
- `references/` - `TOULMIN.md` (the operationalized criteria, cited by ID) and
  `severity-anchors.md` (the domain's anchors on the shared 0-4 severity scale).
- `scripts/` - `checks.py` (the scripted lane), `merge.py` (the pass 4 envelope assembler), and the `tests/` suite.
- `evals/` - `triggers.eval.json`, the trigger-description eval cases.
- `examples/` - golden and anti-pattern fixtures (`golden-*.json`, `anti-*.json`, and the
  `argument-golden-*.md` source artifacts they score), used by the scripted-lane tests and the
  benchmark corpus.

## Known limitations

- **`TOULMIN-HEDGE-DENSITY` fires on arguments that are right to hedge.** The criterion counts
  hedged sentences and fires when they reach 0.35 of the artifact, so it cannot tell appropriate
  caution from evasion. Two arguments written to hedge only their genuinely uncertain claims both
  fire: one hedges 3 of 8 sentences (0.38) and reads severity 2, and the other hedges 5 of 6 (0.83)
  and reads severity 3. Both are held as tests in `scripts/tests/test_checks_argument.py`. Read the
  finding as a surface trace of how much the text hedges, not as a verdict that it hedges too
  much. `TOULMIN-QUALIFIER`, which is judged against the grounds, is the criterion that answers
  whether a claim is qualified correctly. The maintainer kept the 0.35 threshold on 2026-10-29
  ([E75 (hedge-density recalibration)](../../docs/internal/backlog/enhancements.md)), because
  [ADR 0017](../../docs/internal/decisions/0017-argument-lane-split-scripted-assists-as-criteria.md)
  defines the criterion as a measurement, and any threshold can be crossed by a document that is
  uncertain about most of what it says. How often the criterion fires on real documents is not
  measured.
