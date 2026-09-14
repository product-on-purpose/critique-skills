#!/usr/bin/env node
// what-it-is:   the conformance gate entry point
// what-it-does: resolves a local checkout of agent-skills-toolkit and runs its aggregate check
//               (scripts/check.mjs) against this plugin, forwarding CLI args unchanged, then runs
//               the docs-site guards when a built site is present
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
import { existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveToolkit, toolkitCandidates, TOOLKIT_REPO_URL } from "./lib/resolve-toolkit.mjs";
import { checkSite } from "./check-site.mjs";
import { checkReadmeLinks } from "./check-readme-links.mjs";
import { checkReadmeFigures } from "./check-readme-figures.mjs";

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
const toolkitArgs = args.filter((a) => a !== "--skip-site");
const forwarded = hasPathArg ? toolkitArgs : [ROOT, ...toolkitArgs];

const result = spawnSync("node", [resolve(toolkit, "scripts", "check.mjs"), ...forwarded], {
  stdio: "inherit",
});
const toolkitStatus = result.status ?? 1;

// The docs-site guards (family Astro site standard 14.11) run from the same command a contributor
// already knows, so nobody has to remember four more. They need a BUILT site, which most runs of
// this gate do not have and do not need: a missing site/dist is announced and skipped rather than
// failed, because the plugin's conformance does not depend on the site being built locally. CI
// builds the site first and then calls scripts/check-site.mjs directly, so the guards are never
// skipped where they matter. Pass --skip-site to suppress this half entirely.

// The README front-door guard runs UNCONDITIONALLY, unlike the dist-based site guards below: it
// compares tracked files against the tracked route manifest and needs no build. Gating it on a
// built site would leave the README's links unchecked in exactly the situation where nobody has
// built one.
console.log("");
const readmeStatus = checkReadmeLinks();

// Same reasoning as the link guard above: this compares TRACKED prose against the TRACKED
// envelope tree, needs no build, and so runs unconditionally.
console.log("");
const figuresStatus = checkReadmeFigures();

let siteStatus = 0;
if (!args.includes("--skip-site")) {
  if (existsSync(resolve(ROOT, "site", "dist"))) {
    console.log("\n=== Docs site guards ===");
    siteStatus = checkSite();
  } else {
    console.log(
      "\nDocs site guards: skipped, no built site at site/dist." +
        "\n  Build it with `cd site && npm ci && npm run build`, then re-run.",
    );
  }
}

process.exit(toolkitStatus || readmeStatus || figuresStatus || siteStatus);
