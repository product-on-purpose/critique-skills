#!/usr/bin/env node
// what-it-is:   the conformance gate entry point
// what-it-does: resolves a local checkout of agent-skills-toolkit and runs its aggregate check
//               (scripts/check.mjs) against this plugin, forwarding CLI args unchanged
// why:          this plugin wraps the toolkit rather than vendoring its checks, so the validators
//               are never allowed to drift from the family's shared Standard implementation
//               (Pattern A / thinking-framework-skills model; see docs/internal/decisions/)
// used-by:      contributors, build-run subagents (AGENTS.md "Checks"), and .github/workflows/ci.yml
//
// Usage:  node scripts/check.mjs [<plugin-path>] [--strict] [--mode local|published-verdict] [--profile <name>]
// With no <plugin-path>, defaults to this repo's root.
//
// To run locally, clone the toolkit next to this repo (or set AGENT_SKILLS_TOOLKIT):
//   git clone https://github.com/product-on-purpose/agent-skills-toolkit.git ../agent-skills-toolkit
//   node scripts/check.mjs
//
// CI clones it to ./.agent-skills-toolkit and sets AGENT_SKILLS_TOOLKIT (see
// .github/workflows/ci.yml), so the same command runs unchanged.
import { spawnSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveToolkit, toolkitCandidates, TOOLKIT_REPO_URL } from "./lib/resolve-toolkit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, ".."); // this repo's root, cwd-independent

const toolkit = resolveToolkit(ROOT);
if (!toolkit) {
  console.error(
    "Conformance gate: agent-skills-toolkit (the validators) not found.\n" +
      "Clone it next to this repo, or set AGENT_SKILLS_TOOLKIT:\n" +
      `  git clone ${TOOLKIT_REPO_URL}.git ../agent-skills-toolkit\n` +
      "Looked in:\n  " +
      toolkitCandidates(ROOT).join("\n  "),
  );
  process.exit(2);
}

const args = process.argv.slice(2);
// The first non-flag token is the plugin path; forward it if given, else default to this repo's root.
const hasPathArg = args.length > 0 && !args[0].startsWith("--");
const forwarded = hasPathArg ? args : [ROOT, ...args];

const result = spawnSync("node", [resolve(toolkit, "scripts", "check.mjs"), ...forwarded], {
  stdio: "inherit",
});
process.exit(result.status ?? 1);
