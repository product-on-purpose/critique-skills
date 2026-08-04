---
title: critique-usability
---

# critique-usability

Reviews HTML or markdown UI specs, wireframe write-ups, and page mockups against Nielsen's 10
usability heuristics: system status, user control and exits, consistency, error prevention and
recovery, recognition over recall, and minimalist design. Version 0.1.0. The claim is narrower
than it may look: static specs and mockups, not live running applications.

## Inventory

- `SKILL.md` - the skill's frontmatter, trigger description, and four-pass protocol instructions.
- `references/` - `NNG-HEURISTICS.md` (the operationalized criteria, cited by ID) and
  `severity-anchors.md` (the domain's anchors on the shared 0-4 severity scale).
- `scripts/` - `checks.py` (the scripted lane) and its `tests/` suite.
- `evals/` - `triggers.eval.json`, the trigger-description eval cases.
- `examples/` - golden and anti-pattern fixtures (`golden-*.json`, `anti-*.json`) plus supporting
  `artifacts/`, used by the scripted-lane tests and the benchmark corpus.
