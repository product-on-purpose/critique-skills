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
import { writeFileSync, mkdirSync, readFileSync } from "node:fs";
import { resolve, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { runNode } from "./helpers/proc.mjs";
import { tempDir, copyInto } from "./helpers/tmp.mjs";
import {
  QUADRANTS,
  SLUG_OVERRIDES,
  CRITERIA_ROUTE,
  EXTRA_ROUTES,
  criterionPattern,
  parseSkill,
  extractIntro,
  loadSkills,
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
    // The load-bearing half, and the one that must never relax: governance docs are not routed.
    assert.ok(!source.startsWith("docs/internal/"), `${source} must never be routed (standard 14.1)`);
    if (!source.startsWith("docs/")) continue; // W3 widened the map beyond docs/: skills, agents
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
const GITIGNORE_FIXTURE = [
  "site/src/content/docs/how-to/",
  "site/src/content/docs/reference/",
  "site/src/content/docs/skills/critique-*.md",
].join("\n") + "\n";

function buildGuardFixture(t) {
  const root = tempDir(t, "gen-site-guard-");
  for (const name of ["gen-site.mjs", "site-base.mjs", "check-generated-untracked.mjs"]) {
    copyInto(resolve(root, "scripts", name), resolve(REPO_ROOT, "scripts", name));
  }
  // The real contract schema, because the generator reads the criterion-ID grammar out of it
  // rather than carrying a copy. Copied whole so the fixture cannot drift from the frozen file.
  copyInto(
    resolve(root, "contract", "critique-contract.schema.json"),
    resolve(REPO_ROOT, "contract", "critique-contract.schema.json"),
  );
  writeFileSync(
    resolve(root, "library.json"),
    JSON.stringify({
      components: {
        skills: [
          { name: "critique-fixture", path: "skills/critique-fixture", version: "0.1.0", status: "active" },
          { name: "critique-gated", path: "skills/critique-gated", version: "0.1.0", status: "gated" },
        ],
      },
    }),
    "utf8",
  );
  mkdirSync(resolve(root, "skills", "critique-fixture"), { recursive: true });
  writeFileSync(
    resolve(root, "skills", "critique-fixture", "SKILL.md"),
    [
      "---",
      "name: critique-fixture",
      'description: "Reviews fixtures. Use when testing."',
      "version: 0.1.0",
      "license: Apache-2.0",
      "rubric_sources:",
      "  - id: OPENSTD",
      '    citation: "An Open Standard (2020)"',
      "    url: https://example.invalid/std",
      "    accessed: 2026-07-31",
      "    operationalization: open-standard",
      "checks:",
      "  scripted:",
      "    - OPENSTD-ALPHA",
      "  judged:",
      "    - OPENSTD-BETA",
      "---",
      "",
      "# critique-fixture",
      "",
      "Intro.",
      "",
    ].join("\n"),
    "utf8",
  );
  mkdirSync(resolve(root, "agents"), { recursive: true });
  writeFileSync(
    resolve(root, "agents", "critique-critic.md"),
    ["---", "name: critique-critic", 'description: "The critic."', "---", "", "# critique-critic", "", "Body."].join("\n"),
    "utf8",
  );
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
  writeFileSync(resolve(root, ".gitignore"), GITIGNORE_FIXTURE, "utf8");
  const { status, stdout, stderr } = runNode(resolve(root, "scripts", "check-generated-untracked.mjs"), [], { cwd: root });
  assert.equal(status, 0, stderr);
  assert.match(stdout, /all gitignored, none tracked/);
});

test("check-generated-untracked fails when a generated file is tracked", (t) => {
  const root = buildGuardFixture(t);
  writeFileSync(resolve(root, ".gitignore"), GITIGNORE_FIXTURE, "utf8");
  // Generate first, then force the emitted page into the index past its own ignore rule, which
  // is exactly the state this guard exists to catch.
  runNode(resolve(root, "scripts", "gen-site.mjs"), [], { cwd: root });
  const add = spawnSync("git", ["add", "--force", "site/src/content/docs/how-to/index.md"], { cwd: root, encoding: "utf8" });
  assert.equal(add.status, 0, `git add failed: ${add.stderr}`);

  const { status, stderr } = runNode(resolve(root, "scripts", "check-generated-untracked.mjs"), [], { cwd: root });
  assert.equal(status, 1);
  assert.match(stderr, /TRACKED by git/);
});

// --- SKILL.md parsing (W3) --------------------------------------------------

/** A SKILL.md frontmatter exercising every shape the real six use, including `url: null`. */
const FIXTURE_SKILL = [
  "---",
  "name: critique-fixture",
  'description: "Reviews fixtures. Use when testing. See critique-sibling for the other half."',
  "version: 0.2.0",
  "license: Apache-2.0",
  "rubric_sources:",
  "  - id: OPENSTD",
  '    citation: "An Open Standard (2020)"',
  "    url: https://example.invalid/std",
  "    accessed: 2026-07-31",
  "    operationalization: open-standard",
  "  - id: BOOK",
  '    citation: "Someone, A. (2003). A Printed Book. ISBN 1-2-3."',
  "    url: null",
  "    accessed: 2026-07-31",
  "    operationalization: paraphrased",
  "checks:",
  "  scripted:",
  "    - OPENSTD-1.4.11",
  "    - OPENSTD-ALPHA",
  "  judged:",
  "    - BOOK-BETA",
  "---",
  "",
  "# critique-fixture",
  "",
  "Intro prose stating the artifact claim.",
  "",
  "## Contract",
  "",
  "Agent-facing protocol that must not reach the page.",
  "",
].join("\n");

test("parseSkill reads both rubric sources, including one with url: null", () => {
  const skill = parseSkill(FIXTURE_SKILL, "skills/critique-fixture/SKILL.md");
  assert.equal(skill.name, "critique-fixture");
  assert.equal(skill.version, "0.2.0");
  assert.equal(skill.license, "Apache-2.0");
  assert.equal(skill.rubricSources.length, 2);
  assert.deepEqual(skill.rubricSources[0], {
    id: "OPENSTD",
    citation: "An Open Standard (2020)",
    url: "https://example.invalid/std",
    accessed: "2026-07-31",
    operationalization: "open-standard",
  });
  // `url: null` is the convention for a printed source and must normalize to empty, never to
  // the literal string "null", which would render as a link to a four-character path.
  assert.equal(skill.rubricSources[1].id, "BOOK");
  assert.equal(skill.rubricSources[1].url, "");
  assert.equal(skill.rubricSources[1].citation, "Someone, A. (2003). A Printed Book. ISBN 1-2-3.");
});

test("parseSkill reads both criterion lanes, dotted IDs included", () => {
  const skill = parseSkill(FIXTURE_SKILL, "skills/critique-fixture/SKILL.md");
  // A lane that comes back empty is the failure this asserts against: two different stop-regex
  // bugs in development each returned [] for every lane, and the generator happily emitted six
  // skill pages carrying no criteria at all.
  assert.deepEqual(skill.scripted, ["OPENSTD-1.4.11", "OPENSTD-ALPHA"]);
  assert.deepEqual(skill.judged, ["BOOK-BETA"]);
});

test("parseSkill throws on a missing frontmatter block and on a missing scalar", () => {
  assert.throws(() => parseSkill("# no frontmatter\n", "x/SKILL.md"), /no frontmatter/);
  assert.throws(
    () => parseSkill(["---", "name: x", "---", "", "body"].join("\n"), "x/SKILL.md"),
    /no description/,
  );
});

test("extractIntro keeps the prose above the first H2 and drops the protocol below it", () => {
  const { body } = parseSkill(FIXTURE_SKILL, "skills/critique-fixture/SKILL.md");
  const intro = extractIntro(body);
  assert.equal(intro, "Intro prose stating the artifact claim.");
  assert.doesNotMatch(intro, /Contract/);
  assert.doesNotMatch(intro, /must not reach the page/);
});

test("criterionPattern comes from the frozen contract schema, not a copy of it", () => {
  const pattern = criterionPattern();
  // The exact bug this guards: a hand-typed [A-Z][A-Z0-9-]* silently drops every dotted WCAG ID.
  assert.ok(pattern.test("WCAG-1.4.11"), "dotted IDs must match");
  assert.ok(pattern.test("DIATAXIS-HEADING-DEPTH"));
  assert.ok(pattern.test("NNG-EM-CONSTRUCTIVE"));
  assert.ok(!pattern.test("lowercase-id"));
  assert.ok(!pattern.test("NOHYPHEN"));

  const schema = JSON.parse(
    readFileSync(resolve(REPO_ROOT, "contract", "critique-contract.schema.json"), "utf8"),
  );
  assert.equal(pattern.source, schema.$defs.criterionId.pattern);
});

// --- the real skills --------------------------------------------------------

test("the shipped skills carry exactly 42 scripted and 54 judged criteria", () => {
  // Hard-coded on purpose. In this repository a criterion is added, removed, or moved between
  // lanes only by a deliberate, versioned change to a skill, so this test breaking is the
  // correct alarm and not friction: it means the site's headline figure moved and the README's
  // hand-typed sentence ("42 run as deterministic scripts and 54 require judgment") is stale.
  const skills = loadSkills();
  assert.equal(skills.length, 6);
  const scripted = skills.reduce((n, s) => n + s.scripted.length, 0);
  const judged = skills.reduce((n, s) => n + s.judged.length, 0);
  assert.equal(scripted, 42, "scripted lane");
  assert.equal(judged, 54, "judged lane");
  assert.equal(scripted + judged, 96, "total criteria");
});

test("every shipped criterion ID is unique and matches the contract grammar", () => {
  const pattern = criterionPattern();
  const seen = new Set();
  for (const skill of loadSkills()) {
    for (const id of [...skill.scripted, ...skill.judged]) {
      assert.ok(pattern.test(id), `${id} (${skill.name}) does not match the contract grammar`);
      assert.ok(!seen.has(id), `${id} is declared twice`);
      seen.add(id);
    }
  }
  assert.equal(seen.size, 96);
});

test("every skill version agrees with library.json", () => {
  const library = JSON.parse(readFileSync(resolve(REPO_ROOT, "library.json"), "utf8"));
  const active = new Map(
    library.components.skills.filter((s) => s.status === "active").map((s) => [s.name, s.version]),
  );
  const skills = loadSkills();
  assert.equal(skills.length, active.size);
  for (const skill of skills) {
    assert.equal(skill.version, active.get(skill.name), `${skill.name} version`);
  }
});

test("every shipped rubric source has a citation, and a url only when one exists", () => {
  for (const skill of loadSkills()) {
    assert.ok(skill.rubricSources.length > 0, `${skill.name} declares no rubric source`);
    for (const src of skill.rubricSources) {
      assert.ok(src.citation, `${skill.name}/${src.id} has no citation`);
      assert.ok(src.accessed, `${skill.name}/${src.id} has no accessed date`);
      assert.notEqual(src.url, "null", `${skill.name}/${src.id} kept the literal string null`);
      if (src.url) assert.match(src.url, /^https:\/\//, `${skill.name}/${src.id} url`);
    }
  }
});

test("the route map routes every shipped skill and the critic subagent", () => {
  const skills = loadSkills();
  const routes = buildRouteMap(skills);
  for (const skill of skills) {
    assert.equal(routes.get(skill.path), `/skills/${skill.name}/`);
  }
  for (const [source, route] of Object.entries(EXTRA_ROUTES)) {
    assert.equal(routes.get(source), route);
  }
  // The criteria explorer is an aggregate with no source file, so it is deliberately absent.
  assert.ok(![...routes.values()].includes(CRITERIA_ROUTE));
  assert.equal(outputPathFor(CRITERIA_ROUTE), "/reference/criteria.md");
});

test("a skill page resolves to the file the gitignore claims the generator owns", () => {
  for (const skill of loadSkills()) {
    const out = outputPathFor(skill.route);
    assert.match(out, /^\/skills\/critique-[\w-]+\.md$/, `${skill.name} -> ${out}`);
  }
});
