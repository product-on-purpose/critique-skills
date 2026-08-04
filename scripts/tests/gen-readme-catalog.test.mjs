// what-it-is:   unit tests for the README skill-catalog table generator's --check mode
// what-it-does: (1) copies scripts/gen-readme-catalog.mjs into an isolated temp fixture tree
//               (mirroring the real repo's relative layout, since it reads library.json from its
//               own file location) with a crafted library.json, skill, and target markdown file,
//               and imports the copy directly to exercise checkCatalogDrift()/writeCatalog(); (2)
//               runs the real script's --check against the real repo as an unconditional smoke
//               test, since this generator has no toolkit dependency
// why:          S-08 (docs-and-packaging spec) requires the README's skill catalog to be generated,
//               never hand-typed (AC-4); before this file, nothing exercised checkCatalogDrift() or
//               writeCatalog() at all
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, readFileSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { runNode } from "./helpers/proc.mjs";
import { tempDir, copyInto } from "./helpers/tmp.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..", "..");
const SRC_SCRIPT = resolve(REPO_ROOT, "scripts", "gen-readme-catalog.mjs");

const MARKERS = ["<!-- skill-catalog:start -->", "<!-- skill-catalog:end -->"];

/** Build an isolated copy of the generator plus a one-skill library.json + SKILL.md fixture. */
function buildFixture(t) {
  const root = tempDir(t, "gen-readme-catalog-");
  const scriptPath = resolve(root, "scripts", "gen-readme-catalog.mjs");
  copyInto(scriptPath, SRC_SCRIPT);

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
  );

  mkdirSync(resolve(root, "skills", "critique-fixture"), { recursive: true });
  writeFileSync(
    resolve(root, "skills", "critique-fixture", "SKILL.md"),
    [
      "---",
      "name: critique-fixture",
      'description: "Reviews fixtures for the test suite. Use when validating this generator."',
      "rubric_sources:",
      "  - id: FIX-01",
      "  - id: FIX-02",
      "---",
      "",
      "# critique-fixture",
    ].join("\n"),
  );

  return { root, scriptPath };
}

/** Import the fixture copy of the generator via a fresh file:// URL (no toolkit dependency). */
async function importFixtureModule(scriptPath) {
  return import(pathToFileURL(scriptPath).href);
}

test("checkCatalogDrift reports drift when the target's table is stale", async (t) => {
  const { root, scriptPath } = buildFixture(t);
  const target = resolve(root, "README.md");
  writeFileSync(target, ["# Fixture", "", MARKERS[0], "stale content", MARKERS[1], ""].join("\n"));

  const { checkCatalogDrift } = await importFixtureModule(scriptPath);
  const result = checkCatalogDrift(target);

  assert.equal(result.ok, false);
  assert.match(result.messages[0], /skill-catalog table is out of date/);
});

test("writeCatalog regenerates the table so checkCatalogDrift then reports clean", async (t) => {
  const { root, scriptPath } = buildFixture(t);
  const target = resolve(root, "README.md");
  writeFileSync(target, ["# Fixture", "", MARKERS[0], "stale content", MARKERS[1], "", "trailing text"].join("\n"));

  const { checkCatalogDrift, writeCatalog } = await importFixtureModule(scriptPath);

  const before = checkCatalogDrift(target);
  assert.equal(before.ok, false);

  const writeStatus = writeCatalog(target);
  assert.equal(writeStatus, 0);

  const after = checkCatalogDrift(target);
  assert.equal(after.ok, true);

  const written = readFileSync(target, "utf8");
  assert.match(written, /critique-fixture/);
  assert.match(written, /FIX-01, FIX-02/);
  // the gated skill is not "active" and must not appear in the rendered table
  assert.doesNotMatch(written, /critique-gated/);
  // content outside the markers must survive untouched
  assert.match(written, /^# Fixture/);
  assert.match(written, /trailing text$/);
});

test("checkCatalogDrift fails clearly when the target has no marker pair", async (t) => {
  const { root, scriptPath } = buildFixture(t);
  const target = resolve(root, "README.md");
  writeFileSync(target, "# Fixture with no markers\n");

  const { checkCatalogDrift } = await importFixtureModule(scriptPath);
  const result = checkCatalogDrift(target);

  assert.equal(result.ok, false);
  assert.match(result.messages[0], /not found in target/);
});

test("smoke: the real generator's --check runs against this repo without crashing", () => {
  const { status, stdout, stderr } = runNode(resolve(REPO_ROOT, "scripts", "gen-readme-catalog.mjs"), ["--check"], {
    cwd: REPO_ROOT,
  });

  assert.ok(status === 0 || status === 1, `expected exit 0 or 1, got ${status}. stderr: ${stderr}`);
  assert.match(stdout, /gen:catalog --check:/);
});
