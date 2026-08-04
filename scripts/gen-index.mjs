#!/usr/bin/env node
// what-it-is:   the INDEX.md generator (repo-local wrapper)
// what-it-does: regenerates the navigational INDEX.md from library.json plus component frontmatter
//               by spawning the toolkit's own scripts/generators/gen-index.mjs, then post-filters
//               the rendered text through lib/gen-index-filter.mjs's dropPhantomRows() before
//               writing or diffing (Standard sec 2.6, G4)
// why:          this plugin wraps the toolkit rather than vendoring its generators, so INDEX.md can
//               never silently disagree with what the family's shared implementation produces
//               (Pattern A; see docs/internal/decisions/0011-gate-wiring-toolkit-wrapper.md, which
//               settles the same question for scripts/check.mjs and scripts/gen-plugin-manifest.mjs)
// used-by:      contributors ("npm run gen:index"), scripts/gen-plugin-manifest.mjs (folds this
//               into "npm run gen" and its "npm run gen -- --check" drift check), and, once wired,
//               the "drift" CI job
//
// Usage:  node scripts/gen-index.mjs           (writes INDEX.md)
//         node scripts/gen-index.mjs --check   (diffs; exits 1 on drift, 0 if current)
//
// Upstream limitation, worked around here rather than patched in the toolkit (wrap-don't-vendor):
// the toolkit's generator renders its "## Manifests" and "## Documentation and governance"
// sections as fixed boilerplate written for the toolkit's own repo layout (STANDARD.md,
// .codex-plugin/, manifest.generated.json, docs/internal/backlog/, docs/internal/STATUS.md,
// agents/_chain-permitted.yaml, templates/) rather than deriving them from ctx, so those two
// sections can list paths that do not exist in a consuming repo like this one.
// lib/gen-index-filter.mjs's dropPhantomRows() strips any bullet-list link whose target does not
// exist on disk, so INDEX.md never asserts a path this repo does not have. Everything above those
// two sections (title, tier line, Skills/Subagents/Commands) is already correctly data-driven
// from library.json and component frontmatter and passes through unchanged. See
// docs/internal/upstream-gen-index-boilerplate.md for the upstream finding writeup.
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveToolkit, toolkitCandidates, TOOLKIT_REPO_URL } from "./lib/resolve-toolkit.mjs";
import { dropPhantomRows } from "./lib/gen-index-filter.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");

const toolkit = resolveToolkit(ROOT);
if (!toolkit) {
  console.error(
    "gen-index: agent-skills-toolkit (the generator) not found.\n" +
      "Clone it next to this repo, or set AGENT_SKILLS_TOOLKIT:\n" +
      `  git clone ${TOOLKIT_REPO_URL}.git ../agent-skills-toolkit\n` +
      "Looked in:\n  " +
      toolkitCandidates(ROOT).join("\n  "),
  );
  process.exit(2);
}

const GENERATOR = resolve(toolkit, "scripts", "generators", "gen-index.mjs");

// Normalize line endings so the diff is not flaky on a checkout that rewrote CRLF/LF (mirrors
// gen-plugin-manifest.mjs's checkManifestDrift and the toolkit's own index-drift.mjs norm()).
const norm = (s) => s.replace(/\r\n/g, "\n").replace(/\s+$/, "");

/** Render INDEX.md via the toolkit generator, then filter it through dropPhantomRows(). */
function renderFiltered() {
  const rendered = spawnSync("node", [GENERATOR, ROOT], { encoding: "utf8" });
  if (rendered.status !== 0) return { ok: false, stderr: rendered.stderr };
  return { ok: true, text: dropPhantomRows(rendered.stdout, ROOT) };
}

/** Diff the committed INDEX.md against what the toolkit generator (filtered) would produce now. */
export function checkIndexDrift() {
  const file = resolve(ROOT, "INDEX.md");
  const rendered = renderFiltered();
  if (!rendered.ok) {
    return { ok: false, messages: [`gen:index --check: rendering INDEX.md failed:\n${rendered.stderr}`] };
  }
  if (!existsSync(file)) {
    return { ok: false, messages: ["gen:index --check: INDEX.md does not exist; generate it with: npm run gen"] };
  }
  const onDisk = readFileSync(file, "utf8");
  if (norm(onDisk) !== norm(rendered.text)) {
    return {
      ok: false,
      messages: [
        "gen:index --check: INDEX.md is out of date with library.json + component frontmatter; regenerate with: npm run gen",
      ],
    };
  }
  return { ok: true, messages: ["gen:index --check: INDEX.md matches library.json + component frontmatter."] };
}

/** Regenerate INDEX.md: render via the toolkit generator, filter, then write it ourselves (the
 * toolkit generator's own --write is not used, since it would write the unfiltered text). */
export function writeIndex() {
  const rendered = renderFiltered();
  if (!rendered.ok) {
    process.stderr.write(rendered.stderr ?? "gen:index: rendering INDEX.md failed\n");
    return { status: 1 };
  }
  writeFileSync(resolve(ROOT, "INDEX.md"), rendered.text);
  return { status: 0 };
}

const invokedDirectly = process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url));
if (invokedDirectly) {
  if (process.argv.includes("--check")) {
    const { ok, messages } = checkIndexDrift();
    for (const m of messages) console.log(m);
    process.exit(ok ? 0 : 1);
  } else {
    const result = writeIndex();
    process.exit(result.status ?? 1);
  }
}
