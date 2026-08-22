#!/usr/bin/env node
// what-it-is:   the one command that runs every docs-site guard
// what-it-does: runs the three 14.11 validators plus the generated-tree guard against a built
//               dist, reports each, and exits non-zero when any of them fails
// why:          family Astro site standard 14.11 requires the guards to run in BOTH the PR build
//               and the deploy build, not the PR build only, and a contributor should not have to
//               remember four commands. This is the single entry point both use
// used-by:      scripts/check.mjs (which runs it when a built dist exists), and the build-site and
//               deploy jobs in .github/workflows/
//
// Usage:  node scripts/check-site.mjs [distDir]
// Exit:   0 = every guard passed; 1 = at least one failed.
//
// The fourth 14.11 validator, remark-resolve-links.mjs, is deliberately NOT ported: it exists to
// repair relative .md links emitted by a generator, and this repo's generator never emits one
// (site plan decision 2.3). Porting three of four and documenting why the fourth is inapplicable
// is the conformance position ADR 0032 records.
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { checkRenderedLinks } from "./check-rendered-links.mjs";
import { checkRouteParity } from "./check-route-parity.mjs";
import { verifyEditLinks } from "./verify-edit-links.mjs";
import { check as checkGeneratedUntracked } from "./check-generated-untracked.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

/**
 * @param {string} [distArg]
 * @returns {number} 0 pass, 1 fail
 */
export function checkSite(distArg) {
  const dist = resolve(distArg || join(ROOT, "site", "dist"));
  if (!existsSync(dist)) {
    console.error(
      `check-site: no built site at ${dist}.\n` +
        "Build it first:  cd site && npm ci && npm run build",
    );
    return 1;
  }

  const results = [];
  const run = (name, fn) => {
    console.log(`\n--- ${name} ---`);
    // A guard that throws is a guard that did not run, which must not read as a pass.
    let code;
    try {
      code = fn();
    } catch (error) {
      console.error(`${name}: threw rather than returning a verdict: ${error.message}`);
      code = 1;
    }
    results.push({ name, code });
    return code;
  };

  run("rendered links", () => checkRenderedLinks(dist));
  run("route parity", () => checkRouteParity({ dist }));
  run("edit links", () => verifyEditLinks({ dist }));
  run("generated tree untracked", () => checkGeneratedUntracked());

  const failed = results.filter((r) => r.code !== 0);
  console.log("\n=== Site guards ===");
  for (const result of results) {
    console.log(`  ${result.code === 0 ? "pass" : "FAIL"}  ${result.name}`);
  }
  if (failed.length === 0) {
    console.log(`\nPASS: ${results.length} site guard(s).`);
    return 0;
  }
  console.log(`\nFAIL: ${failed.length} of ${results.length} site guard(s).`);
  return 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(checkSite(process.argv[2]));
}
