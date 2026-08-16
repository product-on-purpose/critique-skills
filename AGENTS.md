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

- **Skills:** `critique-accessibility` (v0.1.1, calibrated after P3 measurement; see ADR 0027 and
  ADR 0028), `critique-argument`, `critique-clarity`, `critique-docs`, `critique-microcopy`,
  `critique-usability` (v0.1.0 each) (all `skills/critique-*`, `active`). The toy fixture at
  `skills/_template-fixture` is a scaffolding sample, not a shipped skill, and is deliberately not
  registered in `library.json`.
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
| smoke | `python scripts/smoke.py --expect no-deps`, then `python scripts/smoke.py --expect ready` |

**`smoke` answers a question no other job asks: does this plugin run for someone who just installed
it?** Every other job installs dependencies before it runs anything, so none of them sees what
`/plugin install` delivers, which is a git clone and nothing else. That gap shipped a real defect:
`contract/validate.py` imported `jsonschema` at module load, `/plugin install` does not run `pip`,
and a fresh install answered step 2 of every skill's protocol with a raw traceback while 784 tests
passed and the gate was clean. The job asserts both user states in order on one runner, first with
no dependencies (every skill must fail naming the exact install command, with no traceback), then
with them (every skill must emit a usable envelope). Asserting only the second would have missed the
defect the job exists because of.

A command whose target does not exist yet (no bench results, no bench corpus) succeeds vacuously
with a message saying so, rather than failing on an artifact nobody has built yet; each script's
own docstring says which future effort replaces the vacuous path. `unit-node` (`npm test` ->
`node --test`) is not on that vacuous list: `scripts/tests/*.test.mjs` covers the release tag
guard, the version manifest, release-notes extraction, and a smoke test per generator `--check`
mode (`scripts/tests/README.md` has the current inventory).

`npm run gen -- --check` also enforces that every command in the table above appears in this file:
edit both together, or the `drift` job fails (S-07 CI-pipeline spec, AC-5).

### Bench (`.github/workflows/bench.yml`)

`workflow_dispatch` only; never runs on push or PR (judged-lane runs cost money and are
non-deterministic). Reproduce a dispatch locally:

```
python bench/run_bench.py --skills all --k 5 --tiers "" --dry-run
```

Drop `--dry-run` for a live run. **That needs no API key**, and you must not add one: the harness
reaches the model through the Claude Code CLI, which authenticates from a Claude subscription
([ADR 0030](docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md)). A live run
does need the `claude` CLI on `PATH`, and it always passes `--model` explicitly, because a benchmark
that inherits the caller's model measures nothing reproducible.

Point every live run at a fresh `--out-dir`. `bench/results/runs*/` is immutable measurement
evidence; the harness refuses an `--out-dir` that already holds envelopes for exactly that reason.
`--out-dir` defaults to `bench/results/runs`, so a live run that omits it is refused:

```
python bench/run_bench.py --skills critique-clarity --k 5 --tiers "" --out-dir bench/results/runs-local
```

A dispatch names its own directory. `bench.yml` writes to `bench/results/runs-dispatch-<run id>`
unless its `out_dir` input says otherwise, which is what makes a live dispatch possible at all: it
passed no `--out-dir` until v0.1.6 and so exited at the immutability guard before its first model
call. `bench/tests/test_bench_workflow.py` holds that contract.

See `bench/README.md` for the corpus, metrics, and results design, and
`docs/explanation/the-benchmark-harness.md` for what the harness does step by step and which of its
steps touch a model at all.

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
