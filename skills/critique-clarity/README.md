---
title: critique-clarity
---

# critique-clarity

Reviews markdown or plain-text prose for clarity against the Federal Plain Language Guidelines and
Williams' *Style*: readability, passive voice, sentence length, and nominalization density.
Version 0.1.0.

## Inventory

- `SKILL.md` - the skill's frontmatter, trigger description, and four-pass protocol instructions.
- `references/` - `PLAIN.md`, `WILLIAMS.md` (the operationalized criteria, cited by ID) and
  `severity-anchors.md` (the domain's anchors on the shared 0-4 severity scale).
- `scripts/` - `checks.py` (the scripted lane) and its `tests/` suite.
- `evals/` - `triggers.eval.json`, the trigger-description eval cases.
- `examples/` - golden and anti-pattern fixtures (`golden-*.json`, `anti-*.json`, and the
  `clarity-golden-*.md` source artifacts they score), used by the scripted-lane tests and the
  benchmark corpus.
