---
title: critique-microcopy
---

# critique-microcopy

Reviews error messages, empty states, and other short microcopy strings, including screens
annotated with placement, container, timing, and behavior context, against NN/g's error-message
guidelines: plain language, specificity, constructive next steps, neutral tone, and recovery
grace. Version 0.1.0.

## Inventory

- `SKILL.md` - the skill's frontmatter, trigger description, and four-pass protocol instructions.
- `references/` - `NNG-EM.md` (the operationalized criteria, cited by ID) and
  `severity-anchors.md` (the domain's anchors on the shared 0-4 severity scale).
- `scripts/` - `checks.py` (the scripted lane) and its `tests/` suite.
- `evals/` - `triggers.eval.json`, the trigger-description eval cases.
- `examples/` - golden and anti-pattern fixtures (`golden-*.json`, `anti-*.json`, and the
  `microcopy-golden-*.md` source artifacts they score), used by the scripted-lane tests and the
  benchmark corpus.
