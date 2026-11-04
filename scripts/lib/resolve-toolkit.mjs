#!/usr/bin/env node
// what-it-is:   the agent-skills-toolkit resolver
// what-it-does: finds agent-skills-toolkit (the validators this plugin does not vendor): the
//               AGENT_SKILLS_TOOLKIT env var if set, otherwise the version package.json pins, in
//               node_modules here or next to a linked worktree's main root
// why:          scripts/check.mjs and scripts/gen-plugin-manifest.mjs both need the toolkit's
//               scripts and must resolve it the same way, so this is the one shared lookup
//               (Pattern A, the thinking-framework-skills wrapper model)
// used-by:      scripts/check.mjs, scripts/gen-plugin-manifest.mjs
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { execSync } from "node:child_process";

/**
 * Candidate toolkit paths, in resolution order: the AGENT_SKILLS_TOOLKIT env var, which lets a
 * contributor test against a toolkit checkout, then the pinned package in this root's node_modules,
 * then in the MAIN repo root's (worktree-portable: when `root` is a linked worktree, e.g. under
 * .claude/worktrees/, the main checkout's install is still found).
 */
function candidates(root) {
  let mainRoot = root;
  try {
    const commonDir = execSync("git rev-parse --git-common-dir", { cwd: root, encoding: "utf8" }).trim();
    if (commonDir) mainRoot = resolve(root, commonDir, ".."); // commonDir is <main>/.git -> parent is <main>
  } catch {
    // not a git checkout, or git unavailable: fall back to root
  }
  return [
    process.env.AGENT_SKILLS_TOOLKIT,
    resolve(root, "node_modules", "agent-skills-toolkit"),
    resolve(mainRoot, "node_modules", "agent-skills-toolkit"),
  ].filter(Boolean);
}

/** Resolve agent-skills-toolkit, or return null if none is found. */
export function resolveToolkit(root) {
  return candidates(root).find((p) => existsSync(resolve(p, "scripts", "check.mjs"))) ?? null;
}

/** The candidate list `resolveToolkit` searched, for a not-found error message. */
export function toolkitCandidates(root) {
  return candidates(root);
}
