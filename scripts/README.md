---
title: scripts
---

# scripts

Repo tooling: the conformance gate wrapper, the manifest generator and drift check, the release
version guard and notes extractor, the per-skill template self-test, and their shared library.

## Inventory

- `check.mjs` - the conformance gate entry point; wraps the toolkit's checks.
- `gen-plugin-manifest.mjs` - regenerates `.claude-plugin/plugin.json` from `library.json`; under
  `--check`, the CI "drift" job's entry point instead.
- `check-release-versions.mjs` - the release tag-vs-manifest version guard; the CI "release" job's
  entry point.
- `extract-release-notes.mjs` - pulls one version's section out of `RELEASE-NOTES.md` for the GitHub
  release body.
- `skill-selftest.py` - validates one `skills/critique-<domain>/` directory against the S-04 skill
  template; see `docs/internal/skill-template.md`, "Self-test".
- `lib/` - shared helpers used by the scripts above.
- `tests/` - pytest suite for the Python tooling here (`skill-selftest.py`).
- `__init__.py` - package marker so `scripts/tests/` resolves against the repository root.
