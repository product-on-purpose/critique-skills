---
title: scripts
---

# scripts

Repo tooling: the conformance gate wrapper, the manifest generator, and their shared library.

## Inventory

- `check.mjs` - the conformance gate entry point; wraps the toolkit's checks.
- `gen-plugin-manifest.mjs` - regenerates `.claude-plugin/plugin.json` from `library.json`.
- `lib/` - shared helpers used by the scripts above.
