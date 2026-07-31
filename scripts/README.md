---
title: scripts
---

# scripts

Repo tooling: the conformance gate wrapper, the manifest generator and drift check, the release
version guard, and their shared library.

## Inventory

- `check.mjs` - the conformance gate entry point; wraps the toolkit's checks.
- `gen-plugin-manifest.mjs` - regenerates `.claude-plugin/plugin.json` from `library.json`; under
  `--check`, the CI "drift" job's entry point instead.
- `check-release-versions.mjs` - the release tag-vs-manifest version guard; the CI "release" job's
  entry point.
- `lib/` - shared helpers used by the scripts above.
