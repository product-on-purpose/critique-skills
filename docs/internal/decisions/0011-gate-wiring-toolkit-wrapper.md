# 0011 - Gate wiring: thin wrapper over a local agent-skills-toolkit checkout

## TL;DR
- **Decision:** `scripts/check.mjs` and `scripts/gen-plugin-manifest.mjs` are thin Node wrappers that resolve a local `agent-skills-toolkit` checkout (by `AGENT_SKILLS_TOOLKIT` env var, a sibling checkout, or an `.agent-skills-toolkit` clone) and `spawnSync` its own `scripts/check.mjs` and `scripts/generators/gen-manifest.mjs`, forwarding CLI args unchanged. No toolkit checks are vendored or reimplemented.
- **Why:** `thinking-framework-skills`, the settled sibling precedent, wires the gate exactly this way (Pattern A). Copying it verbatim means the validators can never drift from the family's shared Standard implementation, and satisfies S-01 (repo-scaffold spec) AC-7's instruction to inspect and copy the family's current answer rather than invent a new mechanism.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, planning session with Claude (build-run gate-fixer pass)

## Builds on

- [0009 - Python and Node toolchain split](0009-python-node-toolchain-split.md), which places repository tooling and "the family conformance-gate wiring (mechanism, vendored, dependency, or wrapper, chosen and recorded as its own ADR during phase P0, per S-07's own open question)" in Node, explicitly deferring the wiring mechanism itself to this ADR.

## Context and problem statement

S-01 (repo-scaffold spec) AC-7 requires that "the gate-wiring choice (vendored, dependency, or wrapper) is recorded as an ADR citing the sibling repo inspected," and its own Requirements section states the mechanism "follows whatever `pm-skills` or `thinking-framework-skills` currently uses (inspect first, copy the family answer, ADR the choice)." S-07 (CI-pipeline spec) restates the same open question, resolved here per its own note: "N/A - the gate-wiring question lives in S-01 OQ-1." A plugin that must validate against the `agent-skills-toolkit` Standard can get the validators into its own gate command three ways: vendor (copy the check scripts into this repo, and maintain them in parallel), depend (an npm package dependency on the toolkit), or wrap (a thin script that locates and invokes a toolkit checkout the repo does not own). The decision was which of the three, following whichever sibling has already answered it.

## Decision drivers

- S-01 AC-7 requires citing the sibling repo actually inspected, not inventing a new mechanism.
- `pm-skills` is not part of the `agent-skills-toolkit` family Standard at all (own `skill-manifest.json`, no `library.json`, no `check.mjs` wrapper, no toolkit dependency), so it is not a candidate precedent for this question.
- `thinking-framework-skills` is a settled precedent: its `scripts/check.mjs` resolves a toolkit checkout (`AGENT_SKILLS_TOOLKIT` env var, `.agent-skills-toolkit`, or a sibling `../agent-skills-toolkit` checkout, worktree-portable via `git rev-parse --git-common-dir`) and `spawnSync`s the toolkit's own validators, never vendoring them (`E:/Projects/product-on-purpose/thinking-framework-skills/scripts/check.mjs`, lines 58-98). Its CI (`.github/workflows/ci.yml`, lines 27-46) checks the toolkit out at a pinned ref into `.agent-skills-toolkit` and sets `AGENT_SKILLS_TOOLKIT` to that path before running `node scripts/check.mjs`, so the identical local command runs unchanged in CI.
- `agent-skills-toolkit`'s own `scripts/check.mjs` (lines 1-5) is documented as "the aggregate conformance gate entry point... used by contributors and `.github/workflows/ci.yml`", i.e. the toolkit already expects to be invoked this way by consumers, not copied.
- Vendoring the checks would let this repo's copy of the Standard's validators silently drift from the toolkit's, defeating the entire point of a shared family conformance gate (the exact failure mode S-01's "follows whatever the sibling uses" instruction is designed to prevent).
- An npm package dependency on `agent-skills-toolkit` was not the sibling's chosen mechanism and would add a publish-and-version-pin step the toolkit does not currently offer; not pursued, since S-01 AC-7 directs copying the family's actual current answer, not the theoretically cleanest one.

## Considered options

1. **Vendor the toolkit's check scripts into this repo.** Rejected: creates a second copy of the Standard's validators that must be manually kept in sync with the toolkit, the opposite of what a shared family gate is for, and matches neither sibling's actual practice.
2. **Depend on `agent-skills-toolkit` as an npm package.** Not pursued: the toolkit does not currently ship as a versioned npm package for this purpose, and neither `pm-skills` (not a Standard-family member) nor `thinking-framework-skills` (wrapper, not a package dependency) uses this mechanism; choosing it would mean inventing a new mechanism, which AC-7 explicitly rules out.
3. **Thin wrapper resolving a local toolkit checkout (chosen).** Copies `thinking-framework-skills`'s `scripts/check.mjs` pattern: locate a toolkit checkout by env var or sibling path, `spawnSync` its `scripts/check.mjs`, forward args, exit with its status code. Applied the same way to `scripts/gen-plugin-manifest.mjs` against the toolkit's `scripts/generators/gen-manifest.mjs`, since both repo-tooling entry points need the identical toolkit-resolution logic (factored into the shared `scripts/lib/resolve-toolkit.mjs`, since this repo has exactly two toolkit-invoking scripts rather than `thinking-framework-skills`'s fourteen-layer aggregate, an inline resolver was not worth re-duplicating twice).

## Decision outcome

Option 3. `scripts/lib/resolve-toolkit.mjs` is the single shared resolver both `scripts/check.mjs` and `scripts/gen-plugin-manifest.mjs` call, checked in resolution order: `AGENT_SKILLS_TOOLKIT` env var, `.agent-skills-toolkit` next to this repo's root, `../agent-skills-toolkit` sibling checkout, and the same two paths again relative to the main repo root (worktree-portable, mirroring the sibling's `git rev-parse --git-common-dir` probe). Locally, this repo resolves the toolkit at `E:/Projects/product-on-purpose/agent-skills-toolkit` via the sibling-checkout candidate, with no env var needed. A future `.github/workflows/ci.yml` (S-07 scope, not yet created as of this ADR) would check the toolkit out to `.agent-skills-toolkit` at a pinned ref and set `AGENT_SKILLS_TOOLKIT`, exactly mirroring the sibling's CI job, so the local and CI commands stay identical.

## Consequences

**Positive:** the validators can never drift from the family's shared Standard implementation, matching the sibling's actual practice rather than a theoretically cleaner mechanism S-01 AC-7 would have rejected anyway. Contributors run the same command AGENTS.md documents and CI will eventually run, with zero CI-only logic (S-07 requirement). The two-script split (`check.mjs`, `gen-plugin-manifest.mjs`) sharing one resolver keeps toolkit-location logic in exactly one place instead of two copies drifting apart.

**Negative:** running the gate locally requires a toolkit checkout to already exist next to this repo (or `AGENT_SKILLS_TOOLKIT` set); there is no fallback that works with zero setup. This is the same cost the sibling accepts, not a new one.

**Neutral:** CI pinning the toolkit to a specific ref (as `thinking-framework-skills`'s workflow does at `2f480d159fc0b36734538fda2215bfeac1d553a0`) is S-07 (CI-pipeline spec) scope; this ADR covers the local wrapper mechanism, which is the part S-01 AC-7 requires and the part CI will invoke unchanged once it exists.

## Implementation sites

- `scripts/check.mjs` - the gate entry point; wraps the toolkit's `scripts/check.mjs`.
- `scripts/gen-plugin-manifest.mjs` - the manifest generator; wraps the toolkit's `scripts/generators/gen-manifest.mjs`.
- `scripts/lib/resolve-toolkit.mjs` - the shared toolkit-checkout resolver both scripts call.
- `AGENTS.md` "Checks" section - documents the exact command (`node scripts/check.mjs [<plugin-path>] [--strict] [--mode local|published-verdict] [--profile <name>]`, equivalently `npm run check`) and the local toolkit-checkout prerequisite.
- `package.json` - `npm run check` and `npm run gen` scripts calling the two wrappers above.

Not yet created: `.github/workflows/ci.yml`, which would pin the toolkit ref and set `AGENT_SKILLS_TOOLKIT` for CI (S-07, CI-pipeline spec scope).
