---
title: workflows
---

# workflows

CI as a scheduler, not a judge: every job here runs exactly one documented command that is also
reproducible locally (see `AGENTS.md`, "Checks"). No workflow contains validation logic of its own.

## Inventory

- `ci.yml` - the pull-request and push gate. Seven jobs (conformance, unit-python, unit-node,
  schema, corpus, drift, audit), each one command, each reproducible locally.
- `bench.yml` - `workflow_dispatch` only, by design: the benchmark's judged lane costs money and is
  non-deterministic, so it never runs on push or PR. `--dry-run` validates wiring without calling a
  model; a live run commits new envelopes to a fresh branch rather than pushing to `main` directly.
- `release.yml` - triggers on a pushed `v*` tag. Re-runs the full deterministic suite, enforces the
  tag-equals-manifest version guard, extracts the tagged version's `RELEASE-NOTES.md` section, and
  publishes a GitHub Release.
