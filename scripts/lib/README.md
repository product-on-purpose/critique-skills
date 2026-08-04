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
- `gen-index-filter.mjs` - drops any INDEX.md bullet-list row (or link-plus-prose segment) whose
  linked path does not exist on disk; post-processes the toolkit gen-index generator's boilerplate
  sections in `gen-index.mjs`. Has no toolkit dependency, unlike `resolve-toolkit.mjs`'s consumers,
  so it is unit-testable without a local `agent-skills-toolkit` checkout.
