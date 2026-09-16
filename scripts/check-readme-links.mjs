#!/usr/bin/env node
// what-it-is:   the guard on the README's front-door contract with the docs site
// what-it-does: asserts every documentation-site link in README.md names a route the site really
//               builds, per the committed route manifest, and that the README's three door labels
//               match the three card titles on the site's landing page
// why:          under decision D1 the README is the front door to a primary artifact that lives
//               elsewhere, which makes every site link in it load-bearing: a renamed route turns
//               the project's most-read document into a set of 404s, and nothing else notices,
//               because the site's own guards only check the site's internal links. Risk R13
// used-by:      scripts/check.mjs, which runs it UNCONDITIONALLY
//
// Usage:  node scripts/check-readme-links.mjs [readme] [manifest] [landingPage]
// Exit:   0 = every site link resolves and the doors agree; 1 = at least one does not.
//
// This runs unconditionally, unlike the dist-based guards in check-site.mjs, because it compares
// TRACKED FILES against a TRACKED manifest. It needs no build, so making it depend on one would
// mean the README's links go unchecked in exactly the situation where someone is least likely to
// have built the site.
import { readFileSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { BASE } from "./site-base.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const SITE_ORIGIN = "https://product-on-purpose.github.io";

/**
 * Escape a literal string for safe interpolation into a RegExp.
 *
 * Found by CodeQL on its first run against this repository (js/incomplete-hostname-regexp).
 * SITE_ORIGIN was interpolated raw into the pattern below, so every "." in the hostname was a
 * regex wildcard rather than a literal dot, and the pattern matched hostnames it was never meant
 * to match. The practical blast radius is a spurious failure rather than a missed one, because an
 * over-matched link then fails the route check. That still makes it a guard that is wrong about
 * what it is looking at, which is the class of defect this repository keeps finding in its checks.
 */
export function escapeRegExp(literal) {
  return literal.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * The three doors, as the README's routing table lists them.
 * They are the leading bold cell of each row in the table under "Start here".
 */
export function readmeDoors(readmeText) {
  // The table sits under a "Start here" heading at whatever level; take everything from that
  // heading to the next heading of any level, so the extractor does not depend on the level.
  const start = readmeText.search(/^#{1,6}\s+Start here\s*$/im);
  if (start === -1) return [];
  const rest = readmeText.slice(start).replace(/^#{1,6}\s+Start here\s*$/im, "");
  const next = rest.search(/^#{1,6}\s/m);
  const table = next === -1 ? rest : rest.slice(0, next);
  return [...table.matchAll(/^\|\s*\*\*([^*]+)\*\*\s*\|/gm)].map((m) => m[1].trim());
}

/** The three card titles, as the site's landing page declares them. */
export function landingCardTitles(mdxText) {
  return [...mdxText.matchAll(/<Card\s+title="([^"]+)"/g)].map((m) => m[1].trim());
}

/**
 * @param {{readme?: string, manifest?: string, landing?: string}} [options]
 * @returns {number} 0 pass, 1 fail
 */
export function checkReadmeLinks({ readme, manifest, landing } = {}) {
  const readmePath = resolve(readme || join(ROOT, "README.md"));
  const manifestPath = resolve(manifest || join(ROOT, "scripts", "route-manifest.txt"));
  const landingPath = resolve(landing || join(ROOT, "site", "src", "content", "docs", "index.mdx"));

  for (const [label, path] of [
    ["README", readmePath],
    ["route manifest", manifestPath],
    ["landing page", landingPath],
  ]) {
    if (!existsSync(path)) {
      console.error(`check-readme-links: ${label} not found at ${path}`);
      return 1;
    }
  }

  const readmeText = readFileSync(readmePath, "utf8");
  const routes = new Set(
    readFileSync(manifestPath, "utf8")
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean),
  );

  const problems = [];

  // --- every site link names a built route ---------------------------------
  const prefix = `${SITE_ORIGIN}${BASE}`;
  const seen = new Set();
  let checked = 0;
  const prefixPattern = escapeRegExp(prefix);
  for (const match of readmeText.matchAll(new RegExp(`${prefixPattern}([^\\s")\\]]*)`, "g"))) {
    const path = match[1] || "/";
    if (seen.has(path)) continue;
    seen.add(path);
    checked++;
    // The manifest lists built files: "/skills/index.html", "/skills/critique-docs/index.html".
    const clean = path.split("#")[0].split("?")[0];
    const candidates = [
      `${clean.replace(/\/$/, "")}/index.html`,
      `${clean.replace(/\/$/, "")}.html`,
      clean,
    ];
    if (!candidates.some((candidate) => routes.has(candidate))) {
      problems.push(`the README links ${prefix}${path}, which the site does not build`);
    }
  }

  // --- the doors agree with the landing page -------------------------------
  // A reader arriving at the README and a reader arriving at the site have to be offered the same
  // three routes, or the front door and the building disagree about what is inside. Decision D3
  // specifies the landing CardGrid carries "the three doors in full".
  const doors = readmeDoors(readmeText);
  const cards = landingCardTitles(readFileSync(landingPath, "utf8"));
  if (doors.length === 0) {
    problems.push("the README has no 'Start here' door table, or its shape changed");
  } else if (doors.length !== cards.length || doors.some((door, i) => door !== cards[i])) {
    problems.push(
      "the README's doors and the site's landing cards disagree:\n" +
        `    README: ${JSON.stringify(doors)}\n` +
        `    site:   ${JSON.stringify(cards)}`,
    );
  }

  console.log("=== README front-door links ===");
  console.log(`site links checked: ${checked}   doors: ${doors.length}   landing cards: ${cards.length}`);

  if (problems.length > 0) {
    console.error(`\nFAIL: ${problems.length} problem(s) with the README's contract with the site:`);
    for (const problem of problems) console.error(`  - ${problem}`);
    console.error(
      "\nA site link must name a route in scripts/route-manifest.txt. If a route moved on purpose, " +
        "rebuild the site, run check-route-parity.mjs --update, and fix the README in the same change.",
    );
    return 1;
  }

  console.log("\nPASS: every README site link names a built route, and the doors match.");
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(checkReadmeLinks({ readme: process.argv[2], manifest: process.argv[3], landing: process.argv[4] }));
}
