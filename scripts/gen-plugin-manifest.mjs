#!/usr/bin/env node
// what-it-is:   the native-manifest generator (repo-local wrapper), plus the repo's drift gate
// what-it-does: regenerates .claude-plugin/plugin.json from library.json via the toolkit's
//               gen-manifest.mjs, so the native manifest is never hand-authored (Standard sec 5, G4).
//               Under --check, instead of writing, it diffs the native manifest against what
//               library.json would generate, notes any generated docs this repo does not have yet
//               (INDEX.md, README result tables), and checks that AGENTS.md documents every command
//               .github/workflows/ci.yml runs, marked "# doc-check" (S-07 CI-pipeline spec, AC-5).
// why:          library.json is the single source of truth; regenerating deterministically from it
//               keeps the two manifests diff-free instead of hand-edited in parallel and drifting.
//               --check is the "drift" job's one command (S-07): CI must never hand-compute a
//               verdict, so this file is where that verdict lives instead.
// used-by:      contributors ("npm run gen"), the manifest-drift check (U8) that this keeps green,
//               and .github/workflows/ci.yml's "drift" job ("npm run gen -- --check")
//
// Usage:  node scripts/gen-plugin-manifest.mjs [--target=claude|codex|resolved|all]
//         node scripts/gen-plugin-manifest.mjs --check
// Defaults to --target=claude (the only native manifest this plugin ships at Universal tier; Codex
// targeting is a Convergent+ concern, Standard sec 5.1 S1/S6). Without --check, always writes.
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
    "gen-plugin-manifest: agent-skills-toolkit (the generator) not found.\n" +
      "Clone it next to this repo, or set AGENT_SKILLS_TOOLKIT:\n" +
      `  git clone ${TOOLKIT_REPO_URL}.git ../agent-skills-toolkit\n` +
      "Looked in:\n  " +
      toolkitCandidates(ROOT).join("\n  "),
  );
  process.exit(2);
}

// Normalize line endings so the diff is not flaky on a checkout that rewrote CRLF/LF (mirrors the
// toolkit's own index-drift.mjs norm()).
const norm = (s) => s.replace(/\r\n/g, "\n").replace(/\s+$/, "");

/** Diff the committed .claude-plugin/plugin.json against what library.json would generate. */
function checkManifestDrift() {
  const file = resolve(ROOT, ".claude-plugin", "plugin.json");
  const rendered = spawnSync(
    "node",
    [resolve(toolkit, "scripts", "generators", "gen-manifest.mjs"), ROOT, "--target=claude"],
    { encoding: "utf8" },
  );
  if (rendered.status !== 0) {
    return {
      ok: false,
      messages: [`gen --check: rendering .claude-plugin/plugin.json failed:\n${rendered.stderr}`],
    };
  }
  if (!existsSync(file)) {
    return {
      ok: false,
      messages: [`gen --check: ${file} does not exist; generate it with: npm run gen`],
    };
  }
  const onDisk = readFileSync(file, "utf8");
  if (norm(onDisk) !== norm(rendered.stdout)) {
    return {
      ok: false,
      messages: [
        "gen --check: .claude-plugin/plugin.json is out of date with library.json; regenerate with: npm run gen",
      ],
    };
  }
  return { ok: true, messages: ["gen --check: .claude-plugin/plugin.json matches library.json."] };
}

/**
 * Generated docs this repo does not have yet (INDEX.md is a Gold-tier concern, and the bench
 * results tables need bench/results/ to exist first). Vacuously OK: there is nothing to diff
 * against a file that legitimately does not exist yet (S-07 CI-pipeline spec: "the script must
 * succeed vacuously with a clear message, not fail"). Kept here, rather than silently omitted, so a
 * future reader sees this drift job already knows about both and will start checking them the day
 * they show up.
 */
function checkGeneratedDocsPlaceholder() {
  const messages = [];
  if (!existsSync(resolve(ROOT, "INDEX.md"))) {
    messages.push("gen --check: INDEX.md does not exist yet (Gold-tier concern); nothing to check.");
  }
  if (!existsSync(resolve(ROOT, "bench", "results"))) {
    messages.push("gen --check: bench/results/ does not exist yet; no README result tables to check.");
  }
  return { ok: true, messages };
}

/**
 * AC-5: AGENTS.md must document every command .github/workflows/ci.yml runs. Commands opt in by
 * ending their `run:` line with the literal comment "# doc-check"; every such command must appear
 * verbatim as a substring somewhere in AGENTS.md. This is the deliberate, narrow scope: the seven
 * ci.yml job commands (S-07 AC-1, AC-5), not every install/checkout step in every workflow.
 */
function checkAgentsDocCoverage() {
  const ciPath = resolve(ROOT, ".github", "workflows", "ci.yml");
  if (!existsSync(ciPath)) {
    return {
      ok: true,
      messages: ["gen --check: .github/workflows/ci.yml not found yet; skipping command-coverage check."],
    };
  }
  const ciText = readFileSync(ciPath, "utf8");
  const agentsPath = resolve(ROOT, "AGENTS.md");
  const agentsText = existsSync(agentsPath) ? readFileSync(agentsPath, "utf8") : "";

  const commandRe = /^\s*run:\s*(.+?)\s*#\s*doc-check\s*$/gm;
  const commands = [...ciText.matchAll(commandRe)].map((m) => m[1].trim());

  if (commands.length === 0) {
    return {
      ok: false,
      messages: [
        "gen --check: no '# doc-check'-marked commands found in .github/workflows/ci.yml; " +
          "the coverage check has nothing to verify, which is itself drift.",
      ],
    };
  }
  const missing = commands.filter((cmd) => !agentsText.includes(cmd));
  if (missing.length > 0) {
    return {
      ok: false,
      messages: [
        "gen --check: AGENTS.md is missing these ci.yml commands (S-07 CI-pipeline spec, AC-5):",
        ...missing.map((c) => `  - ${c}`),
      ],
    };
  }
  return {
    ok: true,
    messages: [`gen --check: AGENTS.md documents all ${commands.length} ci.yml command(s).`],
  };
}

const args = process.argv.slice(2);

if (args.includes("--check")) {
  const results = [checkManifestDrift(), checkGeneratedDocsPlaceholder(), checkAgentsDocCoverage()];
  let ok = true;
  for (const r of results) {
    for (const m of r.messages) console.log(m);
    if (!r.ok) ok = false;
  }
  process.exit(ok ? 0 : 1);
}

const targetArg = args.find((a) => a.startsWith("--target=")) ?? "--target=claude";

const result = spawnSync(
  "node",
  [resolve(toolkit, "scripts", "generators", "gen-manifest.mjs"), ROOT, targetArg, "--write"],
  { stdio: "inherit" },
);
process.exit(result.status ?? 1);
