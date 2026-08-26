# 0033 - One required check, and a guard that keeps it honest

## TL;DR
- **Decision:** `main` is protected by a repository ruleset, and the one status check it requires is
  a new aggregate job, `ci-ok`, which runs no command and reports whether the other nine jobs in
  [`ci.yml`](../../../.github/workflows/ci.yml) passed. `scripts/lib/ci-gate.mjs`, run by the
  existing `drift` job, fails when `ci-ok` does not depend on every job in the file, or has lost its
  `if: always()`.
- **Why:** Every other job in `ci.yml` reports a matrix-expanded name (`conformance (Node 24)`), so
  requiring the jobs directly means naming all fourteen in a setting that lives outside this
  repository. Bumping the Node matrix then strands the old names silently: branch protection goes on
  waiting for a context that nothing will ever emit again, and **every pull request blocks on a
  check that cannot report**, with no failure to read anywhere. One stable name lets the matrix
  change without anyone remembering a setting they cannot see from the code.
- **What the guard is for:** An aggregate job is only a gate while it depends on everything. A job
  added to `ci.yml` without a `needs:` entry is gated by nothing, and the pipeline still goes green.
  That is a worse failure than the one this ADR fixes, because it is invisible rather than blocking,
  so it is checked rather than remembered.
- **Status:** Accepted
- **Date:** 2026-08-25
- **Deciders:** Jonathan Prisant

## Builds on

- [0011 - Gate wiring: wrap the toolkit rather than vendor its checks](0011-gate-wiring-toolkit-wrapper.md),
  whose rule this ADR keeps: CI schedules, it does not judge. `ci-ok` is the one job that breaks the
  companion rule (every job is exactly one documented command), and the exception is the point of
  it, so it is stated in `ci.yml`'s header, in [`AGENTS.md`](../../../AGENTS.md), and here.
- S-07 (CI pipeline), `docs/internal/release-plans/plan_v0.1.0/S-07_ci-pipeline/spec.md`, AC-1 and
  AC-5. That spec is frozen at seven jobs and is not amended by this ADR; `smoke`, `build-site` and
  now `ci-ok` were all added after it.

## Context and problem statement

Until 2026-08-25 the default branch of this public repository had **no branch protection at all**:
no ruleset, no classic protection, force-push and deletion both open. Every one of the last twenty
commits arrived through a pull request with all checks green, so the practice was already there;
nothing enforced it.

Protection was added the same day as a repository ruleset, initially requiring the fourteen
status-check contexts `ci.yml` actually emits. That list is correct, and it is brittle in a specific
way. The contexts are job **names**, and seven of the nine jobs run under a matrix, so their names
carry the matrix value: `conformance (Node 22.12.0)`, `conformance (Node 24)`, and so on. The Node
matrix is deliberately a floor and a ceiling, so the ceiling is expected to move. The day it moves
from `24` to `26`, `ci.yml` is correct, CI is green, and the ruleset is still waiting for
`conformance (Node 24)`. A required check that never reports does not fail; it stays pending, and
the pull request cannot be merged by anyone who is not an admin, with nothing anywhere saying why.

This repository has been bitten by the neighbouring class of drift already: `ci.yml`'s own header
comment said "Seven jobs" while the file had eight, and [`AGENTS.md`](../../../AGENTS.md) said seven
while the table beneath it listed nine. Configuration that describes other configuration goes stale
unless something compares the two.

## Decision drivers

- **A required check must be able to fail.** Pending forever is the worst of the outcomes available,
  because it looks like waiting rather than like breakage.
- **The Node matrix must stay free to move.** It exists to test a floor and a ceiling; a ceiling that
  cannot be bumped without editing GitHub settings is a ceiling that will not be bumped.
- **The protection surface must be visible from the repository.** Before this ADR nothing in the
  tree recorded that `main` was protected, or how. A setting nobody can read is a setting nobody
  maintains.
- **Zero dependencies.** `package.json` declares none, and the repository SHA-pins every action.

## Considered options

1. **Require the fourteen contexts directly.** Shipped first, replaced the same day. Correct today,
   silently wrong the day the matrix moves, and its failure mode is a blocked repository rather than
   a red check.
2. **Require no checks, keep only the pull-request rule.** Cheapest, and it gives up the property
   worth having: it makes review mandatory but lets a red pipeline merge.
3. **An aggregate gate job, requiring only its name. Chosen.** One context, stable across matrix
   changes, and its correctness is a property of a file in this repository rather than of a setting
   outside it, which means it can be tested.
4. **A third-party alls-green action.** Does the same job, and adds a dependency plus a pinned SHA to
   a repository that has neither, in order to run four lines of shell.

## Decision outcome

`ci.yml` gains `ci-ok`: `needs` all nine jobs, `if: always()` at job level, and one step that exits
1 when any needed result is `failure`, `cancelled` or `skipped`.

`if: always()` is the part that is easy to get wrong and impossible to notice. Without it, GitHub
skips a job whose dependency failed; a skipped check counts as a **passing** one for branch
protection; and the gate would report success in exactly the case it exists to catch. `skipped` and
`cancelled` are failures here for the same reason: a job that did not run has not passed.

The ruleset on `main` therefore requires exactly one context, `ci-ok`, with "require branches to be
up to date" left on. The rest of the ruleset is unchanged from the day it was created: pull request
required with **0 approvals** (there is one collaborator, so requiring an approval would make every
pull request unmergeable except by bypass), review-thread resolution required, squash and rebase
merges only, linear history, no force-push, no deletion, and admin bypass set to "always".

Admin bypass means the maintainer's direct pushes to `main` still succeed. That is the family
convention, and it is recorded here rather than discovered later: this guards against accident and
against outside contributors, not against the maintainer.

## Consequences

- The Node matrix can move without touching branch protection, which was the point.
- Adding a job to `ci.yml` now carries one extra obligation, and it is enforced rather than
  documented: list it in `ci-ok`'s `needs`, or `npm run gen -- --check` fails naming the job.
- A pull request that edits `ci.yml` runs the edited `ci.yml`, so branch protection cannot defend
  against a change that weakens CI. That is inherent to GitHub Actions and is not new here; the
  defence is that the change is visible in a reviewed diff, which is what the pull-request rule is
  for.
- The strict setting means a branch behind `main` must be updated before it merges, which re-runs
  CI. With one maintainer merging serially this is rare, and it is what makes "a green pull request
  predicts a green deploy" true rather than approximately true.

## Implementation sites

- [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) - the `ci-ok` job, and the header
  comment that carves it out of the one-documented-command rule.
- `scripts/lib/ci-gate.mjs` - the parser and the assertion, pure over `ci.yml`'s text and free of the
  toolkit dependency, so it is unit-testable on its own.
- `scripts/gen-plugin-manifest.mjs` - `checkCiGateCoverage()`, the fifth check in `--check`.
- `scripts/tests/gen-plugin-manifest.test.mjs` - seven tests, including the one asserting the shipped
  `ci.yml` passes, and the one asserting that a gate without `if: always()` fails.
- [`AGENTS.md`](../../../AGENTS.md) - the contributor-facing statement of what `ci-ok` is.
- The ruleset itself, `main Protection`, on the repository's Rules settings page. Not in the tree,
  which is why this ADR restates its shape.
