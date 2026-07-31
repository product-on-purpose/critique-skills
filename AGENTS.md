# AGENTS.md

Agent navigation entrypoint for this plugin.

## What this is

`critique-skills` is an Advanced Skill Library Standard plugin (`tier: convergent` at v0.1.0) of
rubric-cited, machine-parseable critique skills: structured review of interfaces, documents, and
writing that reports measured, evidence-graded findings against a defect rubric instead of
freeform opinion. See `library.json` for the authoritative name, version, and tier.

## Canonical facts

- **Plugin identity and component index:** `library.json` (root). The single source of truth for
  name, version, tier, prefix, and the components inventory. `.claude-plugin/plugin.json` is
  generated from it; never hand-edit the generated file.
- **Decisions log (locked scope, naming, architecture choices):** `docs/internal/decisions/`
  (MADR-format ADRs) and, for the originating planning session, `_local/initial-plan/00-README.md`
  (gitignored, not part of the shipped repo).
- **Release plans:** `docs/internal/release-plans/`.
- **Change history:** `CHANGELOG.md` (full technical history) and `RELEASE-NOTES.md` (curated,
  user-facing summary); the two are kept distinct.
- **Human-facing overview:** `README.md`.

## Components

- **Skills:** `critique-accessibility`, `critique-argument`, `critique-clarity`, `critique-docs`,
  `critique-microcopy`, `critique-usability` (all `skills/critique-*`, v0.1.0, `active`). The toy
  fixture at `skills/_template-fixture` is a scaffolding sample, not a shipped skill, and is
  deliberately not registered in `library.json`.
- **Subagents:** `critique-critic` (`agents/critique-critic.md`, v0.1.0, `active`, Claude-only) - the
  clean-context critic every `critique-<domain>` skill delegates to.
- **Commands:** none yet.

## Checks

The gate is the single command a contributor or CI runs to validate this plugin against the
`agent-skills-toolkit` Standard. It wraps the toolkit rather than vendoring its checks (Pattern A);
see `docs/internal/decisions/` for the gate-wiring ADR.

```
node scripts/check.mjs [<plugin-path>] [--strict] [--mode local|published-verdict] [--profile <name>]
```

- `<plugin-path>` - defaults to this repo's root.
- `--strict` - grade against the full live Standard instead of the pinned `standard` version.
- `--mode local|published-verdict` - `published-verdict` clamps overridable findings to at least
  `warn`, for a verdict meant to be published as-is.
- `--profile <name>` - select a named severity profile from `askit.config.json`, if present.

Equivalent: `npm run check`.

Requires a local checkout of `agent-skills-toolkit` next to this repo, or `AGENT_SKILLS_TOOLKIT`
set to one:

```
git clone https://github.com/product-on-purpose/agent-skills-toolkit.git ../agent-skills-toolkit
```

Regenerate the native manifest from `library.json` after any manifest change:

```
node scripts/gen-plugin-manifest.mjs
```

Equivalent: `npm run gen`.

### CI (`.github/workflows/ci.yml`)

Every push and pull request against `main` runs seven jobs, each a single command with zero
validation logic in the workflow itself (Standard sec 4.1/4.4); every command below is exactly what
the workflow runs and reproduces the same result locally. Node matrix: `22.12.0` and `24`. Python:
`3.12`. See `docs/internal/release-plans/plan_v0.1.0/S-07_ci-pipeline/spec.md` for the acceptance
criteria and `docs/internal/decisions/0011-gate-wiring-toolkit-wrapper.md` for the toolkit-checkout
prerequisite `npm run check` and `npm run gen -- --check` share.

| Job | Command |
|---|---|
| conformance | `npm run check` |
| unit-python | `python -m pytest` |
| unit-node | `npm test` |
| schema | `npm run validate:envelopes` |
| corpus | `python -m bench.generator verify --corpus bench/corpus` |
| drift | `npm run gen -- --check` |
| audit | `npm audit --audit-level=high` |

A command whose target does not exist yet (no bench results, no bench corpus, no Node test files)
succeeds vacuously with a message saying so, rather than failing on an artifact nobody has built
yet; each script's own docstring says which future effort replaces the vacuous path.

`npm run gen -- --check` also enforces that every command in the table above appears in this file:
edit both together, or the `drift` job fails (S-07 CI-pipeline spec, AC-5).

### Bench (`.github/workflows/bench.yml`)

`workflow_dispatch` only; never runs on push or PR (judged-lane runs cost money and are
non-deterministic). Reproduce a dispatch locally:

```
python bench/run_bench.py --skills all --k 5 --tiers "" --dry-run
```

Drop `--dry-run` for a live run; that requires `ANTHROPIC_API_KEY` in the environment. See
`bench/README.md` for the corpus, metrics, and results design this command will drive once the
judged-lane harness (S-03, S-06) ships.

### Release (`.github/workflows/release.yml`)

Triggered by pushing a tag matching `v*`. Re-runs every command in the CI table above, then guards
that the tag equals every version-bearing manifest, listed once in
`scripts/lib/version-manifest.mjs` so the guard and any future version-bump tool cannot drift apart.
Reproduce the guard locally against the tag you are about to push:

```
node scripts/check-release-versions.mjs v0.1.0
```

It then extracts that version's `RELEASE-NOTES.md` section into the release body, failing clearly if
the section is missing or empty rather than publishing the whole changelog. Reproduce locally:

```
node scripts/extract-release-notes.mjs v0.1.0
```

<!-- More checks land here as later phases add them (skills, evals, docs generation). Append new
     commands below this line; do not reorder the gate command above. -->
