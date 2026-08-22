#!/usr/bin/env node
// what-it-is:   the guard that every "Edit page" link points at a file that exists
// what-it-does: extracts every edit-link href from the built dist, normalizes it to a
//               repo-relative path, and asserts the target file is really there; also fails when
//               the total count collapses, which is what a silently broken emission looks like
// why:          this site is generator-heavy, and Starlight's editUrl auto-derivation resolves to
//               the GITIGNORED generated path, which 404s on GitHub the moment a reader clicks it.
//               Every generated page therefore sets editUrl explicitly, and this is the guard that
//               keeps that true. Family Astro site standard 14.11 names it for exactly this case
// used-by:      scripts/check-site.mjs (and therefore scripts/check.mjs), and both CI jobs
//
// Usage:  node scripts/verify-edit-links.mjs [distDir] [repoRoot]
//
// Ported from pm-skills/scripts/verify-edit-links.mjs, parameterized, with the 14.11 robustness
// rules the donor does not apply here: both attribute quote styles (the donor's regex already
// accepts either, and that is kept), a CLI guard so importing cannot exit the importing process,
// and an explicit empty-dist hard-fail rather than leaning on the count threshold alone.
//
// Two shapes of edit link exist in this site and both are checked by the same rule:
//   - generated pages set editUrl explicitly to their real source, e.g. .../edit/main/skills/
//     critique-docs/SKILL.md
//   - hand-authored pages let Starlight derive it from editLink.baseUrl, which carries the /site/
//     segment, e.g. .../edit/main/site/src/content/docs/index.mdx
// Aggregate pages set editUrl:false and emit no link at all, which is why the threshold below is
// not simply "one per page".
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { join, relative, resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const EDIT_BASE_URL = "https://github.com/product-on-purpose/critique-skills/edit/main/";

/** Default floor for the occurrence count. Well under the real number, above zero. */
export const DEFAULT_MIN_EDIT_LINKS = 30;

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    const stat = statSync(full);
    if (stat.isDirectory()) yield* walk(full);
    else if (stat.isFile()) yield full;
  }
}

function escapeForRegex(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * @param {{dist?: string, repoRoot?: string, minLinks?: number, editBaseUrl?: string}} options
 * @returns {number} 0 pass, 1 fail, 2 dist missing
 */
export function verifyEditLinks({ dist, repoRoot, minLinks, editBaseUrl } = {}) {
  const DIST = resolve(dist || join(ROOT, "site", "dist"));
  const REPO = resolve(repoRoot || ROOT);
  const BASE_URL = editBaseUrl || EDIT_BASE_URL;
  const MIN = minLinks ?? Number.parseInt(process.env.MIN_EDIT_LINKS ?? String(DEFAULT_MIN_EDIT_LINKS), 10);

  if (!existsSync(DIST)) {
    console.error(`verify-edit-links: dist not found at ${DIST}; build the site first.`);
    return 2;
  }

  const hrefPattern = new RegExp(`href=["']${escapeForRegex(BASE_URL)}([^"'#?]+)`, "g");
  let total = 0;
  const checked = new Set();
  const failures = [];
  const onDisk = [];
  let pages = 0;

  for (const file of walk(DIST)) {
    if (!file.endsWith(".html")) continue;
    pages++;
    const html = readFileSync(file, "utf8");
    for (const match of html.matchAll(hrefPattern)) {
      total++;
      let target;
      try {
        target = decodeURIComponent(match[1]);
      } catch {
        // Fail on this guard's own assertion, never on a parse error of malformed input.
        target = match[1];
      }
      if (checked.has(target)) continue;
      checked.add(target);
      if (!existsSync(join(REPO, target))) {
        failures.push({ firstSeenIn: relative(REPO, file), target, why: "not on disk" });
      } else {
        onDisk.push({ firstSeenIn: relative(REPO, file), target });
      }
    }
  }

  // Same empty-dist reasoning as the sibling guards: zero pages would otherwise sail past every
  // assertion below and print a green next to a red build.
  if (pages === 0) {
    console.error(
      `verify-edit-links: ${DIST} exists but holds no .html page. The build likely failed after ` +
        "emptying outDir. Failing, because a built site is never empty.",
    );
    return 1;
  }

  // EXISTING ON DISK IS NOT ENOUGH, and this is the whole point of the guard.
  //
  // An edit link points at GitHub, where only TRACKED files exist. The generated content tree is
  // gitignored-and-rebuilt, so every one of its files is present locally and in CI right after a
  // build, and an editUrl that auto-derived into it passes an existence check while 404ing for
  // every reader who clicks "Edit page". The donor implementation checks existence only and would
  // report green on exactly the failure it was written to catch.
  if (onDisk.length > 0) {
    const listed = spawnSync("git", ["ls-files", "--", ...onDisk.map((f) => f.target)], {
      cwd: REPO,
      encoding: "utf8",
    });
    if (listed.status === 0) {
      const tracked = new Set(
        listed.stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean),
      );
      for (const candidate of onDisk) {
        if (!tracked.has(candidate.target)) {
          failures.push({ ...candidate, why: "on disk but NOT tracked by git" });
        }
      }
    } else {
      console.warn(
        "verify-edit-links: git ls-files failed, so targets were checked for existence only. " +
          "A generated, gitignored target would not be caught in this run.",
      );
    }
  }

  if (failures.length > 0) {
    console.error(
      `FAIL: ${failures.length} edit-link target(s) do not exist in the repo ` +
        `(${total} occurrences across ${checked.size} unique targets).`,
    );
    for (const failure of failures.slice(0, 20)) {
      console.error(`  first seen in: ${failure.firstSeenIn}`);
      console.error(`  target:        ${failure.target}  (${failure.why})`);
    }
    if (failures.length > 20) console.error(`  ... and ${failures.length - 20} more`);
    console.error(
      "\nA generated page whose editUrl auto-derived to the gitignored content tree is the usual " +
        "cause. Generated pages must set editUrl explicitly, or editUrl:false when they aggregate.",
    );
    return 1;
  }

  if (total < MIN) {
    console.error(
      `FAIL: ${total} edit-link occurrence(s), below the floor of ${MIN}. This is what a silently ` +
        "broken emission looks like: config drift, a baseUrl typo, or a loader change. Without a " +
        "floor the guard would pass on zero and hide it.",
    );
    return 1;
  }

  console.log(
    `PASS: ${total} edit-link occurrences across ${checked.size} unique targets, all resolving ` +
      `to real repo files (floor ${MIN}).`,
  );
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(verifyEditLinks({ dist: process.argv[2], repoRoot: process.argv[3] }));
}
