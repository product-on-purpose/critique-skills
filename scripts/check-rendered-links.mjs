#!/usr/bin/env node
// what-it-is:   the browser-broken-link guard for the built docs site
// what-it-does: walks every .html page in the built dist, resolves every intra-site href against
//               the page's REAL served URL, and asserts the target exists in dist; fragments are
//               checked against the target page's element ids
// why:          a filesystem-correct link can still 404 in a browser, because pages build to
//               slug/index.html and are served one URL level deeper than their source. This is
//               the load-bearing MUST of family Astro site standard 14.11, and it is the standing
//               replacement for the throwaway crawler used through W2 to W5
// used-by:      scripts/check-site.mjs (and therefore scripts/check.mjs), and both CI jobs
//
// Ported from pm-skills/scripts/check-rendered-links.mjs, parameterized. Two robustness rules from
// 14.11 that the donor applies to only part of its own input are applied throughout here:
//   - BOTH attribute quote styles are matched for href, not only for id. The donor matches
//     id=(?:"..."|'...') but href="..." alone, so a single-quoted href would be skipped silently,
//     which on a link guard means a broken link passes.
//   - Path segments are percent-decoded before the filesystem lookup, not only fragments. A route
//     containing an escaped character would otherwise be reported broken when it is fine.
//
// The base path is NOT redeclared here (14.7): it is a parameter defaulting to the single source
// in site-base.mjs, so the build and this guard cannot disagree, and a test can prove a wrong base
// FAILS rather than passing silently.
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { BASE as DEFAULT_BASE } from "./site-base.mjs";

// Schemes that are out of scope. A bare "#frag" is NOT skipped: it is a same-page anchor.
const SKIP = /^(https?:|mailto:|tel:|ftp:|ws:|wss:|data:|javascript:|\/\/)/i;

/** Every .html file under dir. */
function walk(dir, acc = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, acc);
    else if (entry.name.endsWith(".html")) acc.push(full);
  }
  return acc;
}

/** Percent-decode a path, falling back to the raw value rather than throwing on bad input. */
function decodePath(value) {
  try {
    return decodeURIComponent(value);
  } catch {
    // A literal % that is not a valid escape must not crash a guard: 14.11 requires failing on
    // the guard's own assertions, never on a parse error of malformed input.
    return value;
  }
}

/**
 * Check every internal link in a built site.
 * Never calls process.exit, so it is importable and testable.
 * @param {string} distArg - path to the built dist
 * @param {string} base - the site's base path; a parameter so a test can prove a wrong one fails
 * @param {{strictAnchors?: boolean}} opts
 * @returns {number} 0 pass, 1 fail
 */
export function checkRenderedLinks(distArg, base = DEFAULT_BASE, opts = {}) {
  const DIST = path.resolve(distArg || "site/dist");
  const BASE = base;
  // This site's anchors are generator-emitted rather than hand-typed, so a broken one is a real
  // defect rather than a typo, and enforcing by default is the honest setting. The donor defaults
  // these to advisory because its links are hand-authored.
  const STRICT_ANCHORS = opts.strictAnchors ?? process.env.STRICT_ANCHORS !== "0";

  if (!fs.existsSync(DIST)) {
    console.error(`check-rendered-links: dist not found at ${DIST}; build the site first.`);
    return 1;
  }

  const urlOf = (file) => {
    let rel = path.relative(DIST, file).split(path.sep).join("/");
    if (rel.endsWith("/index.html")) rel = rel.slice(0, -"index.html".length);
    else if (rel === "index.html") rel = "";
    else rel = rel.replace(/\.html$/, "/");
    return `${BASE}/${rel}`;
  };

  const distFileFor = (urlPath) => {
    if (!urlPath.startsWith(`${BASE}/`) && urlPath !== BASE) return null;
    const rel = decodePath(urlPath.slice(`${BASE}/`.length)).replace(/\/$/, "");
    const candidates =
      rel === ""
        ? [path.join(DIST, "index.html")]
        : [path.join(DIST, rel, "index.html"), path.join(DIST, rel), path.join(DIST, `${rel}.html`)];
    for (const candidate of candidates) {
      if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) return candidate;
    }
    return null;
  };

  const idCache = new Map();
  const idsOfFile = (file) => {
    if (idCache.has(file)) return idCache.get(file);
    const set = new Set();
    try {
      // Both quote styles. name="..." is deliberately NOT matched: <meta name=...> would flood
      // the id set and mask genuinely broken anchors.
      for (const m of fs.readFileSync(file, "utf8").matchAll(/\sid=(?:"([^"]+)"|'([^']+)')/g)) {
        set.add(m[1] ?? m[2]);
      }
    } catch {
      /* unreadable: leave empty */
    }
    idCache.set(file, set);
    return set;
  };

  const pages = walk(DIST);
  // A built site is never empty. An existing-but-empty dist is what Astro leaves when a build
  // crashes after emptying outDir; scanning zero pages would otherwise PASS and show a misleading
  // green next to a red build.
  if (pages.length === 0) {
    console.error(
      `check-rendered-links: ${DIST} exists but holds no .html page. The build likely failed after ` +
        "emptying outDir. Failing, because a built site is never empty.",
    );
    return 1;
  }

  const broken = [];
  const brokenAnchors = [];

  for (const file of pages) {
    const html = fs.readFileSync(file, "utf8");
    const pageUrl = urlOf(file);
    for (const m of html.matchAll(/\shref=(?:"([^"]*)"|'([^']*)')/g)) {
      const raw = m[1] ?? m[2];
      if (!raw || SKIP.test(raw)) continue;

      const hashIndex = raw.indexOf("#");
      const fragment = hashIndex === -1 ? "" : decodePath(raw.slice(hashIndex + 1).split("?")[0]);

      if (raw.startsWith("#")) {
        if (fragment && !idsOfFile(file).has(fragment)) {
          brokenAnchors.push({ page: pageUrl, href: raw });
        }
        continue;
      }

      const isRelative = !raw.startsWith("/");
      const isBaseAbsolute = raw.startsWith(`${BASE}/`) || raw === BASE;
      // A host-root link that is not under the base is the "Site not found" class: it resolves
      // outside the project subpath. Flag it rather than skipping it.
      const isHostRoot = raw.startsWith("/") && !isBaseAbsolute;
      if (!isRelative && !isBaseAbsolute && !isHostRoot) continue;

      const clean = raw.split("#")[0].split("?")[0];
      if (!clean) continue;

      let resolved;
      try {
        resolved = new URL(clean, `https://x${pageUrl}`).pathname;
      } catch {
        continue;
      }

      const target = distFileFor(resolved);
      if (!target) {
        broken.push({ page: pageUrl, href: raw, resolved });
        continue;
      }
      if (fragment && !idsOfFile(target).has(fragment)) {
        brokenAnchors.push({ page: pageUrl, href: raw });
      }
    }
  }

  console.log("=== Rendered link resolution ===");
  console.log(`Pages scanned: ${pages.length}`);
  console.log(`Browser-broken internal links: ${broken.length}`);
  console.log(`Broken anchors (${STRICT_ANCHORS ? "enforcing" : "advisory"}): ${brokenAnchors.length}`);

  const report = (title, items) => {
    console.log(`\n${title}`);
    const byPage = {};
    for (const item of items) (byPage[item.page] ||= []).push(item);
    for (const page of Object.keys(byPage).sort().slice(0, 40)) {
      console.log(`  ${page}`);
      for (const item of byPage[page]) {
        console.log(`     ${item.href}${item.resolved ? `  ->  ${item.resolved}` : ""}`);
      }
    }
  };

  if (broken.length) report("Broken internal links (resolved against the page URL):", broken);
  if (brokenAnchors.length) report("Broken anchors (page exists, fragment id does not):", brokenAnchors);

  const failed = broken.length > 0 || (STRICT_ANCHORS && brokenAnchors.length > 0);
  if (!failed) {
    console.log("\nPASS: every internal link resolves in the browser.");
    return 0;
  }
  console.log("\nFAIL: fix by routing to a published page or to an absolute GitHub source URL.");
  console.log("The generator resolves links at emit time; a broken one usually means a route moved.");
  return 1;
}

// CLI entry. The process.argv[1] null-guard keeps a bare import (node -e, a REPL, a programmatic
// consumer) from crashing on pathToFileURL(undefined): a guard module must not throw on import
// (14.11, guard robustness). A guard that crashes is worse than no guard.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(checkRenderedLinks(process.argv[2]));
}
