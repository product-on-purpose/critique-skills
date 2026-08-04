---
title: critique-argument
---

# critique-argument

Reviews argumentative prose - essays, proposals, position papers, recommendation memos, strategy
docs, and op-eds - against the Toulmin model of argument: whether the claim, grounds, warrant,
backing, qualifier, and rebuttal are present, explicit, and actually hold together. Version 0.1.0.

## Inventory

- `SKILL.md` - the skill's frontmatter, trigger description, and four-pass protocol instructions.
- `references/` - `TOULMIN.md` (the operationalized criteria, cited by ID) and
  `severity-anchors.md` (the domain's anchors on the shared 0-4 severity scale).
- `scripts/` - `checks.py` (the scripted lane) and its `tests/` suite.
- `evals/` - `triggers.eval.json`, the trigger-description eval cases.
- `examples/` - golden and anti-pattern fixtures (`golden-*.json`, `anti-*.json`, and the
  `argument-golden-*.md` source artifacts they score), used by the scripted-lane tests and the
  benchmark corpus.
