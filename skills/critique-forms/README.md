---
title: critique-forms
---

# critique-forms

Reviews HTML forms for how easy they are to complete, especially on a phone: input types and mobile
keyboards, autofill tokens, field widths, required and optional marking, password rules, button
labels, and layout. Its 24 criteria form one synthesized rubric, `FORMS`, drawn from convergent
research by Baymard, GOV.UK, web.dev, NN/g and others, with each criterion citing its own sources
by evidence grade. Version 0.1.0.

## Inventory

- `SKILL.md` - the skill's frontmatter, trigger description, and four-pass protocol instructions.
- `references/` - `FORMS.md` (the operationalized criteria, each row citing its sources, and the
  purpose heuristic twelve scripted criteria share) and `severity-anchors.md` (the domain's anchors
  on the shared 0-4 severity scale, with every threshold the scripted lane applies).
- `scripts/` - `checks.py` (the scripted lane, 18 criteria), `merge.py` (the pass 4 envelope
  assembler), and the `tests/` suite, which includes a check that every criterion row cites what
  the research record cites, at the grade it records.
- `evals/` - `triggers.eval.json`, the trigger-description eval cases.
- `examples/` - golden and anti-pattern fixtures (`golden-*.json`, `anti-*.json`) plus supporting
  `artifacts/`, which between them exercise all 18 scripted criteria.
