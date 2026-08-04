---
title: critique-docs
---

# critique-docs

Reviews technical documentation pages and page trees written in markdown against the Diataxis
framework: tutorial, how-to, reference, and explanation mode fit, plus heading structure, orphaned
pages, cross-mode linking, and navigation-list length. Version 0.1.0.

## Inventory

- `SKILL.md` - the skill's frontmatter, trigger description, and four-pass protocol instructions.
- `references/` - `DIATAXIS.md` (the operationalized criteria, cited by ID) and
  `severity-anchors.md` (the domain's anchors on the shared 0-4 severity scale).
- `scripts/` - `checks.py` (the scripted lane) and its `tests/` suite.
- `evals/` - `triggers.eval.json`, the trigger-description eval cases.
- `examples/` - golden and anti-pattern fixtures (`golden-*.json`, `anti-*.json`, and the
  `docs-golden-*.md` source artifacts they score), used by the scripted-lane tests and the
  benchmark corpus.
