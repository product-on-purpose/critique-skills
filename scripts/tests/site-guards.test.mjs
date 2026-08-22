// what-it-is:   unit tests for the three ported 14.11 docs-site guards and their aggregate
// what-it-does: builds tiny dist fixtures in a temp directory and asserts each guard's PASS and
//               FAIL paths, including the four robustness rules that are easy to regress into a
//               guard that always passes: an existing-but-empty dist, a wrong base path, a
//               single-quoted href, and importing a guard without it exiting the process
// why:          a guard that cannot fail is worse than no guard, because it reports green. Family
//               Astro site standard 14.11 requires these to fail on their own assertions rather
//               than on a parse error, and the donor implementations apply several of those rules
//               to only one of the three files
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, mkdirSync, rmSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { tempDir } from "./helpers/tmp.mjs";
import { runNode } from "./helpers/proc.mjs";
import { checkRenderedLinks } from "../check-rendered-links.mjs";
import { checkRouteParity, routesIn } from "../check-route-parity.mjs";
import { verifyEditLinks } from "../verify-edit-links.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..", "..");
const BASE = "/critique-skills";
const EDIT = "https://github.com/product-on-purpose/critique-skills/edit/main/";

/** Write one built page into a fixture dist. */
function page(root, route, body) {
  const dir = route === "/" ? root : resolve(root, route.replace(/^\/|\/$/g, ""));
  mkdirSync(dir, { recursive: true });
  writeFileSync(resolve(dir, "index.html"), `<html><body>${body}</body></html>`, "utf8");
}

/** A minimal two-page dist whose links all resolve. */
function buildDist(t) {
  const root = tempDir(t, "site-guards-");
  page(root, "/", `<a href="${BASE}/how-to/">how-to</a>`);
  page(root, "/how-to/", `<h2 id="a-heading">H</h2><a href="${BASE}/">home</a>`);
  return root;
}

// --- check-rendered-links ---------------------------------------------------

test("rendered links passes a dist whose links all resolve", (t) => {
  assert.equal(checkRenderedLinks(buildDist(t), BASE), 0);
});

test("rendered links fails a link to a route that does not exist", (t) => {
  const root = buildDist(t);
  page(root, "/how-to/", `<a href="${BASE}/nope/">broken</a>`);
  assert.equal(checkRenderedLinks(root, BASE), 1);
});

test("rendered links fails a WRONG base, which proves the guard consumes it", (t) => {
  // The highest-cost misconfiguration in the site plan is a base that disagrees between the build
  // and the checks: it serves "Site not found" while every validator reports green. A guard that
  // passed here would be worthless.
  assert.equal(checkRenderedLinks(buildDist(t), "/wrong-base"), 1);
});

test("rendered links matches BOTH attribute quote styles", (t) => {
  const root = buildDist(t);
  // The donor matches id=(?:"..."|'...') but href="..." alone, so a single-quoted broken href
  // sails past it. On a link guard, a skipped link is a passed link.
  page(root, "/how-to/", `<a href='${BASE}/nope/'>single quoted</a>`);
  assert.equal(checkRenderedLinks(root, BASE), 1);
});

test("rendered links resolves a bare-relative href against the page URL", (t) => {
  const root = buildDist(t);
  // The splash landing page writes its links this way on purpose (site decision D3).
  page(root, "/", `<a href="how-to/">relative</a>`);
  assert.equal(checkRenderedLinks(root, BASE), 0);
  page(root, "/", `<a href="nope/">relative and broken</a>`);
  assert.equal(checkRenderedLinks(root, BASE), 1);
});

test("rendered links fails a fragment that no element on the target page carries", (t) => {
  const root = buildDist(t);
  page(root, "/", `<a href="${BASE}/how-to/#a-heading">good</a>`);
  assert.equal(checkRenderedLinks(root, BASE), 0);
  page(root, "/", `<a href="${BASE}/how-to/#not-there">stale</a>`);
  assert.equal(checkRenderedLinks(root, BASE), 1);
});

test("rendered links survives a fragment that is not a valid percent-escape", (t) => {
  const root = buildDist(t);
  // decodeURIComponent throws URIError on "#50%-off"; a guard must fail on its own assertions,
  // never on a parse error of malformed input, or one hand-typed anchor kills the whole pass.
  page(root, "/", `<a href="${BASE}/how-to/#50%-off">odd</a>`);
  assert.doesNotThrow(() => checkRenderedLinks(root, BASE));
});

test("rendered links hard-fails an existing but EMPTY dist", (t) => {
  const root = tempDir(t, "site-guards-empty-");
  // What Astro leaves when a build crashes after emptying outDir. Scanning zero pages would
  // otherwise pass and print a green next to a red build.
  assert.equal(checkRenderedLinks(root, BASE), 1);
});

// --- check-route-parity -----------------------------------------------------

test("route parity passes when every baseline route is still built", (t) => {
  const root = buildDist(t);
  const baseline = resolve(root, "manifest.txt");
  assert.equal(checkRouteParity({ dist: root, baseline, update: true }), 0);
  assert.equal(checkRouteParity({ dist: root, baseline }), 0);
});

test("route parity fails when a baseline route disappears, and allows new ones", (t) => {
  const root = buildDist(t);
  const baseline = resolve(root, "manifest.txt");
  checkRouteParity({ dist: root, baseline, update: true });

  page(root, "/brand-new/", "added");
  assert.equal(checkRouteParity({ dist: root, baseline }), 0, "an added route is allowed");

  rmSync(resolve(root, "how-to"), { recursive: true, force: true });
  assert.equal(checkRouteParity({ dist: root, baseline }), 1, "a removed route fails");
});

test("route parity refuses to write a baseline from an empty dist", (t) => {
  const root = tempDir(t, "site-guards-empty-");
  const baseline = resolve(root, "manifest.txt");
  // Without this, one crashed build silently overwrites a good baseline with nothing, which
  // disarms the guard permanently and quietly.
  assert.equal(checkRouteParity({ dist: root, baseline, update: true }), 1);
});

test("routesIn lists built routes deterministically", (t) => {
  const routes = routesIn(buildDist(t));
  assert.deepEqual(routes, ["/how-to/index.html", "/index.html"]);
});

// --- verify-edit-links ------------------------------------------------------

test("edit links passes when every target exists in the repo", (t) => {
  const root = tempDir(t, "site-guards-edit-");
  page(root, "/", `<a href="${EDIT}README.md">Edit</a>`);
  page(root, "/how-to/", `<a href="${EDIT}library.json">Edit</a>`);
  assert.equal(verifyEditLinks({ dist: root, repoRoot: REPO_ROOT, minLinks: 2 }), 0);
});

test("edit links fails a target that is not in the repo at all", (t) => {
  const root = tempDir(t, "site-guards-edit-");
  page(root, "/", `<a href="${EDIT}no/such/file.md">Edit</a>`);
  assert.equal(verifyEditLinks({ dist: root, repoRoot: REPO_ROOT, minLinks: 1 }), 1);
});

test("edit links fails a target that EXISTS on disk but is not tracked by git", (t) => {
  const root = tempDir(t, "site-guards-edit-");
  // The failure this guard is actually for: a generated page whose editUrl auto-derived into the
  // gitignored content tree. That file is present locally and in CI right after a build, so an
  // existence check passes it, and it 404s for every reader who clicks "Edit page". Skipped when
  // the generated tree has not been built, since there is then nothing untracked to point at.
  const untracked = "site/src/content/docs/receipts/index.md";
  if (!existsSync(resolve(REPO_ROOT, untracked))) return;
  page(root, "/", `<a href="${EDIT}${untracked}">Edit</a>`);
  assert.equal(verifyEditLinks({ dist: root, repoRoot: REPO_ROOT, minLinks: 1 }), 1);
});

test("edit links fails when the count collapses, which is what broken emission looks like", (t) => {
  const root = tempDir(t, "site-guards-edit-");
  page(root, "/", "no edit link at all");
  // Without a floor the guard passes on zero and hides an all-or-nothing regression.
  assert.equal(verifyEditLinks({ dist: root, repoRoot: REPO_ROOT, minLinks: 5 }), 1);
});

test("edit links reports a missing dist distinctly from a failure", (t) => {
  const root = tempDir(t, "site-guards-edit-");
  assert.equal(verifyEditLinks({ dist: resolve(root, "absent"), repoRoot: REPO_ROOT }), 2);
});

// --- guard robustness -------------------------------------------------------

test("no guard exits the process when it is merely imported", () => {
  // A guard module that runs process.exit at module scope takes the whole test runner with it.
  // The donor's route-parity and edit-link scripts both do exactly that.
  // Paths are relative to the probe file, which is written beside the guards' own directory.
  const script = [
    "await import('../check-rendered-links.mjs');",
    "await import('../check-route-parity.mjs');",
    "await import('../verify-edit-links.mjs');",
    "await import('../check-site.mjs');",
    "console.log('imported-all');",
  ].join("\n");
  const probe = resolve(REPO_ROOT, "scripts", "tests", ".import-probe.mjs");
  writeFileSync(probe, script, "utf8");
  try {
    const { status, stdout } = runNode(probe, [], { cwd: REPO_ROOT });
    assert.equal(status, 0, "importing a guard must not exit");
    assert.match(stdout, /imported-all/);
  } finally {
    rmSync(probe, { force: true });
  }
});

test("the committed route manifest matches what the repo currently builds", () => {
  // Skipped rather than failed when the site has not been built locally: this asserts the
  // committed baseline is CURRENT, which only means something against a real build. CI always
  // builds before running the guards, so there it never skips.
  const dist = resolve(REPO_ROOT, "site", "dist");
  const baseline = resolve(REPO_ROOT, "scripts", "route-manifest.txt");
  if (!existsSync(dist) || !existsSync(baseline)) return;
  assert.equal(checkRouteParity({ dist, baseline }), 0);
});
