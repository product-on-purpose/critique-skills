---
title: scripts/tests
---

# scripts/tests

Two test suites live here side by side: a pytest suite for the Python tooling in `scripts/`
(`skill-selftest.py`), and a `node --test` suite for the Node spine in `scripts/` (the release tag
guard, the version manifest, release-notes extraction, and the generators). `npm test` ->
`node --test` discovers every `*.test.mjs` file under the repo root by default, so nothing extra is
needed to wire these into `npm test` or the CI `unit-node` job; run `python -m pytest` for the
Python half.

## Inventory (Node, `*.test.mjs`)

- `check-release-versions.test.mjs` - the release tag-vs-manifest version guard: passes when every
  manifest agrees with the tag, fails (and still reports every file) when one disagrees, fails
  clearly when a listed file is missing, and the usage/`GITHUB_REF_NAME`-fallback paths.
- `version-manifest.test.mjs` - the single version-bearing-file enumeration: shape and completeness
  of `lib/version-manifest.mjs`, every listed file resolvable on disk, and a live check that the
  real repo's version-bearing files currently agree with each other.
- `extract-release-notes.test.mjs` - the `RELEASE-NOTES.md` section extractor: returns the right
  section, fails on a missing heading, fails when a heading has no content under it (including
  whitespace-only content), and the output-path/`GITHUB_REF_NAME`-fallback paths.
- `gen-readme-catalog.test.mjs` - the README skill-catalog generator's `checkCatalogDrift()` /
  `writeCatalog()` exports against an isolated fixture (drift detection, regeneration, missing
  markers), plus an unconditional smoke test of the real `--check` against this repo (this
  generator has no toolkit dependency).
- `gen-index.test.mjs` - the INDEX.md generator wrapper's `--check`: fails loudly when
  `agent-skills-toolkit` is not resolvable (isolated fixture, environment-independent), plus a
  smoke test - skipped when no toolkit is resolvable locally - that the real `--check`'s exit code
  agrees with its own `checkIndexDrift()` verdict.
- `gen-plugin-manifest.test.mjs` - the native-manifest generator wrapper's `--check` (the "drift" CI
  job's entry point): the same toolkit-not-found and toolkit-available smoke coverage as
  `gen-index.test.mjs`, checking all four of its documented check sections print and that its exit
  code is consistent with them.
- `gen-index.filter.test.mjs` - unit tests for `lib/gen-index-filter.mjs`'s `dropPhantomRows()`
  (the INDEX.md phantom-link filter); not part of this task's scope, documented here for inventory
  completeness only.
- `gen-site.test.mjs` - the docs-site content generator. Pure helpers (path normalization, the
  route and output-path mapping plus the invariant that the two agree, link resolution across its
  four outcomes, fence-aware link rewriting, frontmatter parsing and emission) and the `SKILL.md`
  parser (both rubric sources including one with `url: null`, both criterion lanes, intro
  extraction, and the loud failures on a missing frontmatter block or scalar). Live checks against
  the real repository: `buildRouteMap()` routes nothing from `docs/internal/`, the shipped skills
  carry exactly **42 scripted and 54 judged criteria**, every criterion ID is unique and matches the
  grammar read from the frozen contract schema, and every skill version agrees with `library.json`.
  The 42/54/96 figures are hard-coded on purpose: a criterion moves only by a deliberate, versioned
  change, so a break there is the correct alarm that the README's hand-typed lane-split sentence has
  gone stale. Plus `check-generated-untracked.mjs` exercised against an isolated temp git
  repository in all three states: not ignored, ignored, and force-tracked.
- `helpers/proc.mjs` - spawns a script under test as a child process (`runNode()`). Several scripts
  above run unconditional top-level code, including `process.exit()`, on module load - see the
  file's own header comment for why importing them directly into the test runner is unsafe.
- `helpers/tmp.mjs` - creates an `mkdtemp` fixture directory registered for cleanup via the test's
  own `TestContext#after` (`tempDir()`), and copies a file or whole directory into it
  (`copyInto()` / `copyDirInto()`) so a script that resolves paths relative to its own file location
  can be exercised against crafted fixtures without ever touching the real repo.

## Inventory (Python)

- `__init__.py` - package marker so `scripts/tests/` resolves against the repository root.
- `test_skill_selftest.py`, `test_skills_conformance.py` - pytest suite for `skill-selftest.py` and
  the plugin's conformance surface.
