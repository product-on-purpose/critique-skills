---
title: workflows
---

# workflows

CI as a scheduler, not a judge: every job here runs exactly one documented command that is also
reproducible locally (see `AGENTS.md`, "Checks"). No workflow contains validation logic of its own.

## Inventory

- `ci.yml` - the pull-request and push gate. Nine jobs (conformance, unit-python, unit-node,
  schema, corpus, drift, audit, smoke, build-site), each reproducible locally. All but one run a
  single command; `audit` runs two, because the root tree and `site/` are separate dependency
  graphs and for a long time only the root was checked.
- `deploy-pages.yml` - publishes the documentation site to GitHub Pages on a push to `main`, and
  on `workflow_dispatch`. It runs the SAME build recipe and the SAME guards as `ci.yml`'s
  non-deploying `build-site` job, because a green pull request has to predict a green deploy
  (family Astro site standard 14.6). One deployment at a time, never cancelling one in flight.
  There is no `gh-pages` branch to fall back to, so the rollback is re-running the previous
  successful deployment from the Actions UI.
- `bench.yml` - `workflow_dispatch` only, by design: the benchmark's judged lane costs money and is
  non-deterministic, so it never runs on push or PR. `--dry-run` validates wiring without calling a
  model; a live run commits new envelopes to a fresh branch rather than pushing to `main` directly.
- `codeql.yml` - static analysis of this repository's own Python and Node code, reporting to the
  Security tab on push, pull request and a weekly schedule. A different question from `ci.yml`'s
  `audit` job, which asks whether other people's packages carry known advisories. Deliberately
  outside the `ci-ok` aggregate gate and never a required status check: a finding here is triage,
  not a broken build.
- `release.yml` - triggers on a pushed `v*` tag. Re-runs the full deterministic suite, enforces the
  tag-equals-manifest version guard, extracts the tagged version's `RELEASE-NOTES.md` section, and
  publishes a GitHub Release.
