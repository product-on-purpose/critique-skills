#!/usr/bin/env node
// what-it-is:   the native-manifest generator (repo-local wrapper)
// what-it-does: regenerates .claude-plugin/plugin.json from library.json via the toolkit's
//               gen-manifest.mjs, so the native manifest is never hand-authored (Standard sec 5, G4)
// why:          library.json is the single source of truth; regenerating deterministically from it
//               keeps the two manifests diff-free instead of hand-edited in parallel and drifting
// used-by:      contributors ("npm run gen"), and the manifest-drift check (U8) that this keeps green
//
// Usage:  node scripts/gen-plugin-manifest.mjs [--target=claude|codex|resolved|all]
// Defaults to --target=claude (the only native manifest this plugin ships at Universal tier; Codex
// targeting is a Convergent+ concern, Standard sec 5.1 S1/S6). Always writes.
import { spawnSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveToolkit, toolkitCandidates, TOOLKIT_REPO_URL } from "./lib/resolve-toolkit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");

const toolkit = resolveToolkit(ROOT);
if (!toolkit) {
  console.error(
    "gen-plugin-manifest: agent-skills-toolkit (the generator) not found.\n" +
      "Clone it next to this repo, or set AGENT_SKILLS_TOOLKIT:\n" +
      `  git clone ${TOOLKIT_REPO_URL}.git ../agent-skills-toolkit\n` +
      "Looked in:\n  " +
      toolkitCandidates(ROOT).join("\n  "),
  );
  process.exit(2);
}

const args = process.argv.slice(2);
const targetArg = args.find((a) => a.startsWith("--target=")) ?? "--target=claude";

const result = spawnSync(
  "node",
  [resolve(toolkit, "scripts", "generators", "gen-manifest.mjs"), ROOT, targetArg, "--write"],
  { stdio: "inherit" },
);
process.exit(result.status ?? 1);
