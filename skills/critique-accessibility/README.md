---
title: critique-accessibility
---

# critique-accessibility

Reviews HTML pages and fragments (markdown where mappable) against WCAG 2.2 AA: contrast, alt
text, heading structure, link text, and keyboard and screen-reader access. Version 0.1.1; see the
root README's "most instructive number is a failure" section for why this skill shipped, lost to
the unrubricked baseline, and was recalibrated in place rather than silently replaced.

## Inventory

- `SKILL.md` - the skill's frontmatter, trigger description, and four-pass protocol instructions.
- `references/` - `WCAG.md` (the operationalized criteria, cited by ID) and
  `severity-anchors.md` (the domain's anchors on the shared 0-4 severity scale).
- `scripts/` - `checks.py` (the scripted lane) and its `tests/` suite.
- `evals/` - `triggers.eval.json`, the trigger-description eval cases.
- `examples/` - golden and anti-pattern fixtures (`golden-*.json`, `anti-*.json`) plus supporting
  `artifacts/`, used by the scripted-lane tests and the benchmark corpus.
