---
title: scripts/lib
---

# scripts/lib

Shared helpers for the repo tooling in `scripts/`.

## Inventory

- `resolve-toolkit.mjs` - finds a local `agent-skills-toolkit` checkout for `check.mjs` and
  `gen-plugin-manifest.mjs` to invoke.
- `version-manifest.mjs` - the single enumeration of every version-bearing file in this repo,
  consumed by `check-release-versions.mjs` and any future version-bump tooling.
