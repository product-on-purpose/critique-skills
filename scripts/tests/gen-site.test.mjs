// what-it-is:   unit tests for the Astro Starlight site content generator and its untracked guard
// what-it-does: (1) exercises the pure helpers of scripts/gen-site.mjs by importing them directly
//               (path normalization, the route and output-path mapping and the invariant between
//               them, link resolution across all four outcomes, fence-aware link rewriting,
//               frontmatter parsing and emission); (2) smoke-tests buildRouteMap() against the
//               real repo, which is what would catch docs/internal/ becoming routable; (3) runs
//               scripts/check-generated-untracked.mjs against an isolated temp git repository in
//               both its failing and passing states
// why:          the link resolver is the load-bearing piece of site plan decision 2.3 (rewrite at
//               generation time, no remark plugin) and it is a pure function, so it is both the
//               likeliest place for a bug and the cheapest place to test one. The route/output
//               invariant has already failed once in development: a slug override moved the route
//               while leaving the file where it was, which emits links to a page that does not
//               exist and is invisible until something crawls the built dist
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, mkdirSync } from "node:fs";
import { resolve, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { runNode } from "./helpers/proc.mjs";
import { tempDir, copyInto } from "./helpers/tmp.mjs";
import {
  QUADRANTS,
  SLUG_OVERRIDES,
  normalizePosix,
  parseFrontmatter,
  stripLeadingH1,
  yamlString,
  emitFrontmatter,
  routeFor,
  outputPathFor,
  buildRouteMap,
  resolveLink,
  rewriteLinks,
} from "../gen-site.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..", "..");
const BASE = "/critique-skills";
const BLOB = "https://github.com/product-on-purpose/critique-skills/blob/main";
const TREE = "https://github.com/product-on-purpose/critique-skills/tree/main";

/** A route map standing in for the real one, so resolver tests do not depend on docs/ contents. */
const ROUTES = new Map([
  ["docs/reference/README.md", "/reference/"],
  ["docs/reference/critique-contract.md", "/reference/critique-contract/"],
  ["docs/how-to/gate-in-ci.md", "/how-to/gate-in-ci/"],
  ["docs/explanation/the-benchmark-harness.md", "/explanation/benchmark-harness/"],
]);

// --- path normalization -----------------------------------------------------

test("normalizePosix resolves . and .. and drops empty segments", () => {
  assert.equal(normalizePosix("docs/reference/./critique-contract.md"), "docs/reference/critique-contract.md");
  assert.equal(normalizePosix("docs/how-to/../reference/severity-scale.md"), "docs/reference/severity-scale.md");
  assert.equal(normalizePosix("docs/reference//../../contract/README.md"), "contract/README.md");
});

test("normalizePosix returns null when a path escapes its root", () => {
  assert.equal(normalizePosix("docs/../../elsewhere.md"), null);
  assert.equal(normalizePosix("../outside.md"), null);
});

// --- routes and output paths ------------------------------------------------

test("routeFor maps a quadrant README to the section index and a page to its slug", () => {
  assert.equal(routeFor("docs/how-to/README.md"), "/how-to/");
  assert.equal(routeFor("docs/how-to/gate-in-ci.md"), "/how-to/gate-in-ci/");
});

test("routeFor applies a slug override", () => {
  assert.equal(routeFor("docs/explanation/the-benchmark-harness.md"), "/explanation/benchmark-harness/");
});

test("outputPathFor puts a section index inside its directory, not beside it", () => {
  // <section>.md would also serve /<section>/, but `autogenerate: { directory }` reads the
  // directory, so the overview page has to live inside it.
  assert.equal(outputPathFor("/how-to/"), "/how-to/index.md");
  assert.equal(outputPathFor("/how-to/gate-in-ci/"), "/how-to/gate-in-ci.md");
});

test("every emitted file name agrees with the route it is served at", () => {
  // The invariant a slug override can silently break: if the route says
  // /explanation/benchmark-harness/ while the file is still the-benchmark-harness.md, every
  // link the generator emits to that page 404s.
  for (const [source, route] of buildRouteMap()) {
    const out = outputPathFor(route);
    const segments = route.split("/").filter(Boolean);
    const expected = segments.length === 1 ? "index.md" : `${segments[segments.length - 1]}.md`;
    assert.equal(basename(out), expected, `${source} -> ${route} emitted at ${out}`);
  }
});

// --- link resolution --------------------------------------------------------

test("resolveLink leaves external, mailto, protocol-relative and bare-fragment targets alone", () => {
  for (const href of ["https://diataxis.fr/", "http://example.com", "mailto:a@b.c", "//cdn.example/x.js", "#a-heading"]) {
    const result = resolveLink(href, "docs/reference", ROUTES);
    assert.equal(result.href, href);
    assert.equal(result.kind, "external");
  }
});

test("resolveLink turns a published sibling into a base-absolute site route", () => {
  const result = resolveLink("critique-contract.md", "docs/reference", ROUTES);
  assert.deepEqual(result, { href: `${BASE}/reference/critique-contract/`, kind: "route" });
});

test("resolveLink resolves across quadrants and preserves the fragment verbatim", () => {
  const result = resolveLink("../reference/critique-contract.md#envelope-walkthrough", "docs/how-to", ROUTES);
  assert.equal(result.href, `${BASE}/reference/critique-contract/#envelope-walkthrough`);
  assert.equal(result.kind, "route");
});

test("resolveLink honours a slug override, so the link matches the emitted file", () => {
  const result = resolveLink("the-benchmark-harness.md", "docs/explanation", ROUTES);
  assert.equal(result.href, `${BASE}/explanation/benchmark-harness/`);
});

test("resolveLink sends a repo file outside the published tree to a GitHub blob URL", () => {
  assert.equal(
    resolveLink("../../contract/critique-contract.schema.json", "docs/reference", ROUTES).href,
    `${BLOB}/contract/critique-contract.schema.json`,
  );
  assert.equal(
    resolveLink("../../bench/results/README.md", "docs/explanation", ROUTES).href,
    `${BLOB}/bench/results/README.md`,
  );
});

test("resolveLink sends docs/internal/ to GitHub rather than routing an ADR", () => {
  const result = resolveLink("../internal/decisions/0016-contract-enforcement-boundary.md", "docs/reference", ROUTES);
  assert.equal(result.href, `${BLOB}/docs/internal/decisions/0016-contract-enforcement-boundary.md`);
  assert.equal(result.kind, "github");
});

test("resolveLink uses a tree URL for a directory target", () => {
  const result = resolveLink("../../bench/corpus/", "docs/explanation", ROUTES);
  assert.equal(result.href, `${TREE}/bench/corpus/`);
});

test("resolveLink reports a target that escapes the repo root and changes nothing", () => {
  const result = resolveLink("../../../elsewhere.md", "docs/reference", ROUTES);
  assert.equal(result.kind, "unresolved");
  assert.equal(result.href, "../../../elsewhere.md");
});

// --- link rewriting ---------------------------------------------------------

test("rewriteLinks rewrites inline links, image links and link titles", () => {
  const { body } = rewriteLinks(
    [
      "See [the contract](critique-contract.md).",
      "![diagram](../../docs/assets/x.png)",
      'A [titled link](critique-contract.md "The contract").',
    ].join("\n"),
    "docs/reference",
    ROUTES,
  );
  assert.match(body, /\[the contract\]\(\/critique-skills\/reference\/critique-contract\/\)/);
  assert.match(body, /!\[diagram\]\(https:\/\/github\.com\/[^)]*\/blob\/main\/docs\/assets\/x\.png\)/);
  assert.match(body, /\[titled link\]\(\/critique-skills\/reference\/critique-contract\/ "The contract"\)/);
});

test("rewriteLinks rewrites reference-style link definitions", () => {
  const { body } = rewriteLinks("[contract]: critique-contract.md", "docs/reference", ROUTES);
  assert.equal(body, `[contract]: ${BASE}/reference/critique-contract/`);
});

test("rewriteLinks leaves fenced code blocks untouched", () => {
  const source = [
    "Before [a link](critique-contract.md).",
    "```markdown",
    "[a link](critique-contract.md)",
    "```",
    "~~~md",
    "[another](critique-contract.md)",
    "~~~",
    "After [a link](critique-contract.md).",
  ].join("\n");
  const { body } = rewriteLinks(source, "docs/reference", ROUTES);
  const lines = body.split("\n");
  assert.equal(lines[2], "[a link](critique-contract.md)", "inside a backtick fence");
  assert.equal(lines[5], "[another](critique-contract.md)", "inside a tilde fence");
  assert.match(lines[0], /\/critique-skills\/reference\/critique-contract\//);
  assert.match(lines[7], /\/critique-skills\/reference\/critique-contract\//);
});

test("rewriteLinks collects targets that escape the repo root", () => {
  const { unresolved } = rewriteLinks("[x](../../../y.md)", "docs/reference", ROUTES);
  assert.deepEqual(unresolved, ["../../../y.md"]);
});

// --- frontmatter ------------------------------------------------------------

test("parseFrontmatter splits the block from the body and unquotes scalars", () => {
  const { meta, body } = parseFrontmatter(
    ['---', 'title: "Severity scale"', "description: The shared 0-4 scale", "audience: both", "---", "", "# Severity scale", "", "Body."].join("\n"),
  );
  assert.equal(meta.title, "Severity scale");
  assert.equal(meta.description, "The shared 0-4 scale");
  assert.equal(meta.audience, "both");
  assert.match(body, /^\s*# Severity scale/);
});

test("parseFrontmatter returns the whole text as the body when there is no frontmatter", () => {
  const { meta, body } = parseFrontmatter("# Just a heading\n\nText.");
  assert.deepEqual(meta, {});
  assert.equal(body, "# Just a heading\n\nText.");
});

test("stripLeadingH1 drops only the leading H1", () => {
  assert.equal(stripLeadingH1("# Title\n\nBody.\n\n# Later\n"), "Body.\n\n# Later\n");
  assert.equal(stripLeadingH1("Body first.\n\n# Not leading\n"), "Body first.\n\n# Not leading\n");
});

test("yamlString escapes quotes and backslashes", () => {
  assert.equal(yamlString('a "quoted" value'), '"a \\"quoted\\" value"');
  assert.equal(yamlString("a\\path"), '"a\\\\path"');
});

test("emitFrontmatter always writes an explicit editUrl and omits an absent description", () => {
  const withUrl = emitFrontmatter({ title: "T", description: "D", editUrl: "https://x/y" });
  assert.equal(withUrl, ['---', 'title: "T"', 'description: "D"', 'editUrl: "https://x/y"', '---'].join("\n"));

  const aggregate = emitFrontmatter({ title: "T", editUrl: false });
  assert.equal(aggregate, ["---", 'title: "T"', "editUrl: false", "---"].join("\n"));
  assert.doesNotMatch(aggregate, /description:/);
});

// --- the real repo ----------------------------------------------------------

test("buildRouteMap covers every publishable doc and routes no internal one", () => {
  const routes = buildRouteMap();
  assert.ok(routes.size >= 13, `expected at least 13 routed docs, got ${routes.size}`);
  for (const source of routes.keys()) {
    assert.ok(source.startsWith("docs/"), `${source} is outside docs/`);
    assert.ok(!source.startsWith("docs/internal/"), `${source} must never be routed (standard 14.1)`);
    const quadrant = source.split("/")[1];
    assert.ok(QUADRANTS.includes(quadrant), `${source} is in an unpublished quadrant`);
  }
  for (const [source, slug] of Object.entries(SLUG_OVERRIDES)) {
    assert.ok(routes.has(source), `slug override for ${source} names a file that is not routed`);
    assert.ok(routes.get(source).endsWith(`/${slug}/`), `override ${slug} not applied to ${source}`);
  }
});

// --- check-generated-untracked.mjs ------------------------------------------

/**
 * Build an isolated git repository holding the generator, its base module, the guard, and one
 * source doc. The scripts resolve their root as resolve(HERE, ".."), so the fixture mirrors the
 * real layout: <root>/scripts/*.mjs and <root>/docs/<quadrant>/README.md.
 */
function buildGuardFixture(t) {
  const root = tempDir(t, "gen-site-guard-");
  for (const name of ["gen-site.mjs", "site-base.mjs", "check-generated-untracked.mjs"]) {
    copyInto(resolve(root, "scripts", name), resolve(REPO_ROOT, "scripts", name));
  }
  mkdirSync(resolve(root, "docs", "how-to"), { recursive: true });
  writeFileSync(
    resolve(root, "docs", "how-to", "README.md"),
    ["---", "title: How-to guides", "description: Recipes", "---", "", "# How-to guides", "", "Body."].join("\n"),
    "utf8",
  );
  const init = spawnSync("git", ["init", "--quiet"], { cwd: root, encoding: "utf8" });
  assert.equal(init.status, 0, `git init failed: ${init.stderr}`);
  return root;
}

test("check-generated-untracked fails when a generated file is not gitignored", (t) => {
  const root = buildGuardFixture(t);
  const { status, stderr } = runNode(resolve(root, "scripts", "check-generated-untracked.mjs"), [], { cwd: root });
  assert.equal(status, 1);
  assert.match(stderr, /NOT gitignored/);
  assert.match(stderr, /site\/src\/content\/docs\/how-to\/index\.md/);
});

test("check-generated-untracked passes once the emitting directory is ignored", (t) => {
  const root = buildGuardFixture(t);
  writeFileSync(resolve(root, ".gitignore"), "site/src/content/docs/how-to/\n", "utf8");
  const { status, stdout, stderr } = runNode(resolve(root, "scripts", "check-generated-untracked.mjs"), [], { cwd: root });
  assert.equal(status, 0, stderr);
  assert.match(stdout, /all gitignored, none tracked/);
});

test("check-generated-untracked fails when a generated file is tracked", (t) => {
  const root = buildGuardFixture(t);
  writeFileSync(resolve(root, ".gitignore"), "site/src/content/docs/how-to/\n", "utf8");
  // Generate first, then force the emitted page into the index past its own ignore rule, which
  // is exactly the state this guard exists to catch.
  runNode(resolve(root, "scripts", "gen-site.mjs"), [], { cwd: root });
  const add = spawnSync("git", ["add", "--force", "site/src/content/docs/how-to/index.md"], { cwd: root, encoding: "utf8" });
  assert.equal(add.status, 0, `git add failed: ${add.stderr}`);

  const { status, stderr } = runNode(resolve(root, "scripts", "check-generated-untracked.mjs"), [], { cwd: root });
  assert.equal(status, 1);
  assert.match(stderr, /TRACKED by git/);
});
