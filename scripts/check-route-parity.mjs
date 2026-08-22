#!/usr/bin/env node
// what-it-is:   the guard against silently removing a published route
// what-it-does: compares the built route set against a committed baseline
//               (scripts/route-manifest.txt) and fails when a baseline route has disappeared;
//               added routes are allowed, because new pages are expected
// why:          a removed or renamed URL is a "Site not found" for every existing external link
//               and bookmark, and nothing else in the build notices. Load-bearing MUST of family
//               Astro site standard 14.11
// used-by:      scripts/check-site.mjs (and therefore scripts/check.mjs), and both CI jobs
//
// Usage:  node scripts/check-route-parity.mjs [distDir] [baselineFile]
//         node scripts/check-route-parity.mjs --update    (rewrite the baseline)
//
// When a route is removed on purpose: add a redirect for it, which keeps the route present as a
// redirect page and keeps this guard passing, OR run --update and commit the new baseline in the
// same change with the reason in the message.
//
// SCOPE, deliberately: this checks route PRESENCE, not page CONTENT. A route that keeps its path
// while its content regresses still passes. That is the same mechanism that lets an intentional
// redirect pass, and the failure this guard exists to prevent is the removed URL.
//
// Ported from pm-skills/scripts/check-route-parity.mjs with two robustness rules from 14.11 that
// the donor does not apply to this file: a CLI guard so importing it cannot kill the importing
// process at module scope, and an explicit hard-fail on an existing-but-empty dist rather than
// relying on the removed-route check to catch it (which it does not when the baseline is empty,
// and which in --update mode would happily write an empty baseline over a good one).
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const DEFAULT_BASELINE = path.join(ROOT, "scripts", "route-manifest.txt");

/** Every built route, as a dist-relative .html path, sorted. */
export function routesIn(dir) {
  const out = [];
  const walk = (d) => {
    for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name.endsWith(".html")) {
        out.push("/" + path.relative(dir, full).split(path.sep).join("/"));
      }
    }
  };
  walk(dir);
  return out.sort();
}

/**
 * @param {{dist?: string, baseline?: string, update?: boolean}} options
 * @returns {number} 0 pass, 1 fail
 */
export function checkRouteParity({ dist, baseline, update = false } = {}) {
  const DIST = path.resolve(dist || path.join(ROOT, "site", "dist"));
  const BASELINE = path.resolve(baseline || DEFAULT_BASELINE);

  if (!fs.existsSync(DIST)) {
    console.error(`route-parity: dist not found at ${DIST}; build the site first.`);
    return 1;
  }

  const current = routesIn(DIST);
  // An existing-but-empty dist is what Astro leaves when a build crashes after emptying outDir.
  // Without this, --update would overwrite a good baseline with nothing, which is the one failure
  // mode that disarms this guard permanently and silently.
  if (current.length === 0) {
    console.error(
      `route-parity: ${DIST} exists but holds no .html page. The build likely failed after emptying ` +
        "outDir. Failing, because a built site is never empty.",
    );
    return 1;
  }

  if (update) {
    fs.writeFileSync(BASELINE, current.join("\n") + "\n", "utf8");
    console.log(`route-parity: wrote ${current.length} routes to ${path.relative(ROOT, BASELINE)}`);
    return 0;
  }

  if (!fs.existsSync(BASELINE)) {
    console.error(
      `route-parity: baseline not found at ${BASELINE}. Generate it with --update and commit it.`,
    );
    return 1;
  }

  const expected = fs
    .readFileSync(BASELINE, "utf8")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  const currentSet = new Set(current);
  const expectedSet = new Set(expected);
  const removed = expected.filter((route) => !currentSet.has(route));
  const added = current.filter((route) => !expectedSet.has(route));

  console.log("=== Route parity ===");
  console.log(`baseline routes: ${expected.length}   current routes: ${current.length}`);
  if (added.length) {
    console.log(`\n${added.length} new route(s), allowed; update the baseline when convenient:`);
    for (const route of added.slice(0, 20)) console.log(`  + ${route}`);
    if (added.length > 20) console.log(`  ... and ${added.length - 20} more`);
  }

  if (removed.length === 0) {
    console.log("\nPASS: every baseline route is still present.");
    return 0;
  }

  console.log(`\nFAIL: ${removed.length} baseline route(s) removed. These would 404 for existing links:`);
  for (const route of removed) console.log(`  - ${route}`);
  console.log("\nIf intentional: add a redirect, which keeps the route present as a redirect page,");
  console.log("or run --update and commit the new baseline with the reason.");
  return 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2).filter((a) => a !== "--update");
  process.exit(
    checkRouteParity({
      dist: args[0],
      baseline: args[1],
      update: process.argv.includes("--update"),
    }),
  );
}
