---
title: Upstream findings for agent-skills-toolkit
---

# Upstream findings for agent-skills-toolkit

Two findings surfaced while fixing the INDEX.md phantom-path defect in this repo (see this
task's report for the full root-cause writeup and fix). Neither is ours to patch here per the
wrap-don't-vendor rule (docs/internal/decisions/0011-gate-wiring-toolkit-wrapper.md); both should
be raised as issues against `agent-skills-toolkit` directly.

## Finding 1: `gen-index.mjs`'s two boilerplate sections are not derived from `ctx`

**File:** `agent-skills-toolkit/scripts/generators/gen-index.mjs`

**Lines:** 71-87, the `## Manifests` and `## Documentation and governance` sections of
`renderIndex(ctx)`:

```js
lines.push("## Manifests");
lines.push("");
lines.push("- [`library.json`](library.json) - authored canonical cross-agent manifest (the source of truth).");
lines.push("- [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) - Claude Code native manifest (generated; do not hand-edit).");
lines.push("- [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) - Codex native manifest (generated; do not hand-edit).");
lines.push("- [`manifest.generated.json`](manifest.generated.json) - agent index (generated).");
lines.push("");

lines.push("## Documentation and governance");
lines.push("");
lines.push("- [`STANDARD.md`](STANDARD.md) - the Advanced Skill Library Standard (normative).");
lines.push("- [`README.md`](README.md) - overview, positioning, quickstart.");
lines.push("- [`CHANGELOG.md`](CHANGELOG.md) - full technical history; [`RELEASE-NOTES.md`](RELEASE-NOTES.md) - curated, user-facing notes.");
lines.push("- [`docs/`](docs/) - Diataxis docs (reference, how-to, explanation).");
lines.push("- [`docs/internal/decisions/`](docs/internal/decisions/) - ADRs; [`docs/internal/backlog/`](docs/internal/backlog/) - backlog; [`docs/internal/STATUS.md`](docs/internal/STATUS.md) - live tracker.");
lines.push("- [`agents/_chain-permitted.yaml`](agents/_chain-permitted.yaml) - the chain contract; [`templates/`](templates/) - scaffolder templates.");
lines.push("- [`scripts/`](scripts/) - the Node validation spine (conformance checks, generators, gate, evaluate).");
```

Every other section of `renderIndex` (title, tier line, Skills/Subagents/Commands) is correctly
data-driven from `ctx.library` and component frontmatter. These two sections are not: they are
the toolkit's own repo layout, hardcoded, and rendered verbatim for every consuming plugin
regardless of what that plugin's tree actually contains. A plugin that does not ship
`.codex-plugin/`, `manifest.generated.json`, its own copy of `STANDARD.md`,
`docs/internal/backlog/`, `docs/internal/STATUS.md`, `agents/_chain-permitted.yaml`, or
`templates/` (i.e. any plugin below Advanced tier, or any plugin that targets Claude only) gets an
INDEX.md that asserts paths which do not exist in its tree. Because `gen-index --check`
(downstream) and the toolkit's own `index-drift` check (below) both compare against this same
boilerplate, the phantom links pass every drift check forever; nothing catches them.

In `critique-skills`, this produced seven dangling links out of twenty-four before the local fix:
`.codex-plugin/plugin.json`, `manifest.generated.json`, `STANDARD.md`, `docs/internal/backlog/`,
`docs/internal/STATUS.md`, `agents/_chain-permitted.yaml`, `templates/`.

**Suggested fix:** derive both sections from `ctx` instead of a fixed string list. Concretely,
build the manifest/doc row list as data (path, label, prose) and filter each row by
`existsSync(path.join(ctx.root, path))` before rendering it, the same approach this repo's local
workaround (`scripts/lib/gen-index-filter.mjs`'s `dropPhantomRows`) takes as a post-processing
step. Doing it in `renderIndex` itself, rather than after the fact, would also let a partially
present manifest set (e.g. a plugin that ships `.codex-plugin/` but not `manifest.generated.json`)
render correctly without any downstream repo needing its own filter at all.

## Finding 1b (consequence): the toolkit's own `index-drift` (G4) check inherits the same gap

**File:** `agent-skills-toolkit/scripts/checks/index-drift.mjs`

This Advanced/Gold-tier check (`meta.reqId: "G4"`) diffs a plugin's on-disk `INDEX.md` directly
against `renderIndex(ctx)` (line 33: `norm(onDisk) !== norm(renderIndex(ctx))`), with no
existence filtering of its own. Before the local fix, `critique-skills`' `INDEX.md` was exactly
`renderIndex(ctx)`'s raw output, so this check passed. After the local fix intentionally makes
`INDEX.md` diverge from the raw boilerplate (to stop asserting the seven phantom paths above),
this check reports drift:

```
[error] index-drift (G4): INDEX.md is out of date with library.json + component frontmatter
  (a hand-edited generated file is an error at Gold, Standard sec 2.6 G4). Regenerate:
  node scripts/generators/gen-index.mjs . --write  -> INDEX.md
```

This is informational only for `critique-skills` today (Advanced/Gold is above the plugin's
declared Convergent/Silver tier, so it does not affect the grade or exit code: `node
scripts/check.mjs` still reports "0 error(s), 0 warning(s)" and exits 0). But it means this one
finding is currently permanent and unresolvable by any downstream repo working around Finding 1
locally, for as long as it holds: a repo cannot both (a) stop asserting phantom paths in its own
INDEX.md and (b) satisfy G4's literal-boilerplate-reproduction check, without the fix in Finding 1
landing upstream first. Once `renderIndex` is made existence-aware, both the local filter and this
check converge back to agreement, since neither the plugin's INDEX.md nor `index-drift`'s
reference render would contain the phantom rows anymore.

## Finding 2: `SKIP_DIRS` does not exclude Python tool-cache directories

**File:** `agent-skills-toolkit/scripts/lib/fs-utils.mjs`, line 14:

```js
export const SKIP_DIRS = new Set(["node_modules", ".git", ".memsearch", "_local", "_LOCAL", "_agent-context", "dist", ".astro"]);
```

`SKIP_DIRS` is the shared skip-list for repo-wide content scanners (its own docstring: "matched by
basename at any depth... shared by the repo-wide content checks (U12 mermaid-valid, G8
folder-readme)"). It lists JS/Node build-output and dependency directories but no Python
equivalents. A plugin with a Python component (this repo's `scripts/tests/` and
`skills/_shared/` both run `pytest`, which creates `__pycache__/` and, when configured,
`.pytest_cache/`) gets those tool-cache directories treated as meaningful, README-requiring
folders by G8 `folder-readme`, producing findings like:

```
[error] folder-readme (G8): child "__pycache__" exists on disk but is not in the README
  inventory (under-listed); add it or refresh with askit-build-docs folder-readme mode.
  -> scripts/README.md
[error] folder-readme (G8): child "__pycache__" exists on disk but is not in the README
  inventory (under-listed); add it or refresh with askit-build-docs folder-readme mode.
  -> skills/_shared/README.md
[error] folder-readme (G8): meaningful folder has no README.md (ADR 0024 D1.1); scaffold
  one with askit-build-docs folder-readme mode.  -> skills/__pycache__/README.md
```

These three of `critique-skills`' four remaining above-tier gate issues (Advanced/Gold; informal,
non-blocking at this plugin's declared Convergent/Silver tier) trace directly to this gap. The
fourth, unrelated issue (`docs-presence` G10, incomplete architecture-overview/detailed doc pair)
is a real gap in this repo's own docs and is not an upstream finding.

**Suggested fix:** add `"__pycache__"` and `".pytest_cache"` to `SKIP_DIRS` alongside the existing
Node-focused entries, so any plugin in the family that mixes Python tooling with its Node
validation spine (per ADR 0009, docs/internal/decisions/0009-python-node-toolchain-split.md, the
family's own sanctioned toolchain split) does not have to gitignore-and-hope or hand-maintain
README inventory entries for directories Python itself creates as a byproduct of running tests.

## Status

Both are reported here, not patched, per the wrap-don't-vendor rule
(docs/internal/decisions/0011-gate-wiring-toolkit-wrapper.md): this repo's own generators and
checks are thin wrappers over a toolkit checkout it does not own, so the fix belongs in
`agent-skills-toolkit` itself. Raise both as issues against that repo when convenient; until then,
Finding 1 has a local workaround (`scripts/lib/gen-index-filter.mjs`), and Finding 2's three
downstream symptoms are accepted as known above-tier gate noise (Convergent/Silver is this
plugin's declared and graded tier; the four issues are all Advanced/Gold-only).
