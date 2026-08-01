#!/usr/bin/env node
// what-it-is:   the INDEX.md generator (repo-local wrapper)
// what-it-does: regenerates the navigational INDEX.md from library.json plus component frontmatter
//               by spawning the toolkit's own scripts/generators/gen-index.mjs; under --check,
//               diffs the committed INDEX.md against what that generator would produce instead of
//               writing (Standard sec 2.6, G4)
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
// Known limitation (reported, not patched here, per the wrap-don't-vendor rule above): the
// toolkit's generator renders its "## Manifests" and "## Documentation and governance" sections as
// fixed boilerplate written for the toolkit's own repo layout (STANDARD.md, .codex-plugin/,
// manifest.generated.json, docs/internal/backlog/, docs/internal/STATUS.md,
// agents/_chain-permitted.yaml, templates/) rather than deriving them from ctx, so those two
// sections list several paths that do not exist in this repo. Everything above them (title, tier
// line, Skills/Subagents/Commands) is correctly data-driven from library.json and component
// frontmatter. See this task's final report for the conflict writeup.
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveToolkit, toolkitCandidates, TOOLKIT_REPO_URL } from "./lib/resolve-toolkit.mjs";

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

/** Diff the committed INDEX.md against what the toolkit generator would produce right now. */
export function checkIndexDrift() {
  const file = resolve(ROOT, "INDEX.md");
  const rendered = spawnSync("node", [GENERATOR, ROOT], { encoding: "utf8" });
  if (rendered.status !== 0) {
    return { ok: false, messages: [`gen:index --check: rendering INDEX.md failed:\n${rendered.stderr}`] };
  }
  if (!existsSync(file)) {
    return { ok: false, messages: ["gen:index --check: INDEX.md does not exist; generate it with: npm run gen"] };
  }
  const onDisk = readFileSync(file, "utf8");
  if (norm(onDisk) !== norm(rendered.stdout)) {
    return {
      ok: false,
      messages: [
        "gen:index --check: INDEX.md is out of date with library.json + component frontmatter; regenerate with: npm run gen",
      ],
    };
  }
  return { ok: true, messages: ["gen:index --check: INDEX.md matches library.json + component frontmatter."] };
}

/** Regenerate INDEX.md by invoking the toolkit generator with --write. */
export function writeIndex() {
  return spawnSync("node", [GENERATOR, ROOT, "--write"], { stdio: "inherit" });
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
