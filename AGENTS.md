# AGENTS.md

Agent navigation entrypoint for this plugin.

## What this is

`critique-skills` is an Advanced Skill Library Standard plugin (`tier: universal` at v0.1.0) of
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

- **Skills:** none yet. Add the first with `askit-build-skill` (create mode).
- **Subagents:** none yet.
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

<!-- More checks land here as later phases add them (skills, evals, docs generation). Append new
     commands below this line; do not reorder the gate command above. -->
