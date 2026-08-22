---
title: workflows
---

# workflows

CI as a scheduler, not a judge: every job here runs exactly one documented command that is also
reproducible locally (see `AGENTS.md`, "Checks"). No workflow contains validation logic of its own.

## Inventory

- `ci.yml` - the pull-request and push gate. Nine jobs (conformance, unit-python, unit-node,
  schema, corpus, drift, audit, smoke, build-site), each one command, each reproducible locally.
- `deploy-pages.yml` - publishes the documentation site to GitHub Pages on a push to `main`, and
  on `workflow_dispatch`. It runs the SAME build recipe and the SAME guards as `ci.yml`'s
  non-deploying `build-site` job, because a green pull request has to predict a green deploy
  (family Astro site standard 14.6). One deployment at a time, never cancelling one in flight.
  There is no `gh-pages` branch to fall back to, so the rollback is re-running the previous
  successful deployment from the Actions UI.
- `bench.yml` - `workflow_dispatch` only, by design: the benchmark's judged lane costs money and is
  non-deterministic, so it never runs on push or PR. `--dry-run` validates wiring without calling a
  model; a live run commits new envelopes to a fresh branch rather than pushing to `main` directly.
- `release.yml` - triggers on a pushed `v*` tag. Re-runs the full deterministic suite, enforces the
  tag-equals-manifest version guard, extracts the tagged version's `RELEASE-NOTES.md` section, and
  publishes a GitHub Release.
