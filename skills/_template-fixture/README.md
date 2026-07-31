---
title: _template-fixture
---

# _template-fixture

The skill template's own committed reference build: one complete, self-test-passing skill, built by
following [`docs/internal/skill-template.md`](../../docs/internal/skill-template.md) end to end
against the `toy` domain that already ships with the bench harness. The
[S-04 skill-template spec](../../docs/internal/release-plans/plan_v0.1.0/S-04_skill-template/spec.md),
Behavior/Examples, is what requires it to exist: "when the template guide is followed end to end, then
the resulting toy skill passes the self-test runner; this worked example is committed as the template's
own golden example."

## Inventory

- `critique-toy/` - the fixture skill itself, in the exact directory shape the template mandates.

## Why the nesting

The fixture is a real skill directory, so it obeys the template's naming rule with no exemption: the
directory is named `critique-toy` and its frontmatter `name` is `critique-toy`. It is *not* a shipped
component, so it must not be discovered as one.

Those two facts are what the `_template-fixture/` wrapper reconciles. The family conformance gate
(`npm run check`) and the plugin manifest treat exactly `skills/<dir>/SKILL.md` as the set of skills a
plugin ships; a `SKILL.md` one level deeper is invisible to that scan. Putting the fixture at
`skills/_template-fixture/critique-toy/SKILL.md` therefore keeps the naming rule absolute while keeping
the fixture out of the shipped inventory - and out of `library.json`, which stays the single source of
truth for what this plugin actually ships.

Naming the fixture directory itself `_template-fixture` (or anything else outside the
`critique-<domain>` pattern) was tried first and does not work: the family gate raises a U4
`name-matches-dir` error against it, which blocks the Universal tier outright.

## Running it

```
python scripts/skill-selftest.py skills/_template-fixture/critique-toy
python skills/_template-fixture/critique-toy/scripts/checks.py bench/corpus/toy/toy-001.md --gate
```

The fixture's own pytest suite runs as part of `python -m pytest` from the repository root; its path is
listed in `pytest.ini`'s `testpaths`.
