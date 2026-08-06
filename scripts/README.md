---
title: scripts
---

# scripts

Repo tooling: the conformance gate wrapper, the manifest and README generators and their drift
checks, the release version guard and notes extractor, the per-skill template self-test, and their
shared library.

## Inventory

- `check.mjs` - the conformance gate entry point; wraps the toolkit's checks.
- `gen-plugin-manifest.mjs` - regenerates `.claude-plugin/plugin.json` from `library.json`; under
  `--check`, the CI "drift" job's entry point instead.
- `gen-readme-catalog.mjs` - regenerates `README.md`'s skill-catalog table from `library.json` and
  each shipped skill's own `SKILL.md` frontmatter; `--check` compares instead of writing. The
  README's results table has its own generator, `python -m bench.report table` (see
  `bench/README.md`, "Results"); this script does not touch it.
- `gen-index.mjs` - regenerates the navigational `INDEX.md` from `library.json` plus component
  frontmatter; `--check` compares instead of writing. `gen-plugin-manifest.mjs` folds this in under
  `npm run gen` and its `--check` drift mode, so it is rarely invoked standalone.
- `check-release-versions.mjs` - the release tag-vs-manifest version guard; the CI "release" job's
  entry point.
- `extract-release-notes.mjs` - pulls one version's section out of `RELEASE-NOTES.md` for the GitHub
  release body.
- `skill-selftest.py` - validates one `skills/critique-<domain>/` directory against the S-04 skill
  template; see `docs/internal/skill-template.md`, "Self-test".
- `smoke.py` - the does-it-actually-run check, and the CI "smoke" job's entry point. Runs every
  skill's scripted lane on a real committed artifact and asserts the outcome for the environment:
  `--expect no-deps` (a fresh install, where each skill must fail naming the exact install command
  and printing no traceback) or `--expect ready` (dependencies installed, where each must emit a
  usable envelope). Stdlib only, because it has to run in the environment where the third-party
  dependency is missing.
- `lib/` - shared helpers used by the scripts above.
- `tests/` - two suites: `node --test` coverage for the Node spine above, and the pytest suite for
  the Python tooling here (`skill-selftest.py`); see `tests/README.md` for the inventory.
- `__init__.py` - package marker so `scripts/` resolves against the repository root.
