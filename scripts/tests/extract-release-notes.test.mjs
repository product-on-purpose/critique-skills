// what-it-is:   unit tests for the RELEASE-NOTES.md section extractor
// what-it-does: copies scripts/extract-release-notes.mjs into an isolated temp fixture tree
//               (mirroring the real repo's relative layout, since the script resolves
//               RELEASE-NOTES.md from its own file location), writes a crafted RELEASE-NOTES.md,
//               and runs the copied script as a child process against it
// why:          CI workflows must contain no logic that computes a verdict (S-07 CI-pipeline spec,
//               AC-2), so this script is the only thing standing between a missing or empty
//               release-notes section and publishing the whole changelog as a release body; before
//               this file, "npm test" collected zero tests and never exercised any of that
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { runNode } from "./helpers/proc.mjs";
import { tempDir, copyInto } from "./helpers/tmp.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..", "..");
const SRC_SCRIPT = resolve(REPO_ROOT, "scripts", "extract-release-notes.mjs");

/** Build an isolated copy of the script under a fresh temp root, with the given RELEASE-NOTES.md. */
function buildFixture(t, releaseNotes) {
  const root = tempDir(t, "extract-release-notes-");
  const scriptPath = resolve(root, "scripts", "extract-release-notes.mjs");
  copyInto(scriptPath, SRC_SCRIPT);
  writeFileSync(resolve(root, "RELEASE-NOTES.md"), releaseNotes);
  return { root, scriptPath };
}

const FIXTURE_NOTES = [
  "# Release notes",
  "",
  "## 1.2.3",
  "",
  "- Added the thing.",
  "- Fixed the other thing.",
  "",
  "## 1.2.2",
  "",
  "- Older notes that must not leak into the 1.2.3 extract.",
  "",
].join("\n");

test("extracts exactly the requested version's section", (t) => {
  const { root, scriptPath } = buildFixture(t, FIXTURE_NOTES);
  const outPath = resolve(root, "OUT.md");

  const { status, stdout } = runNode(scriptPath, ["1.2.3", outPath], { cwd: root });

  assert.equal(status, 0);
  assert.match(stdout, /ok: wrote \d+ line\(s\) for 1\.2\.3 to/);
  const body = readFileSync(outPath, "utf8");
  assert.match(body, /^## 1\.2\.3/);
  assert.match(body, /Added the thing\./);
  assert.doesNotMatch(body, /Older notes that must not leak/);
  assert.doesNotMatch(body, /## 1\.2\.2/);
});

test("strips a leading 'v' from the tag before looking up the heading", (t) => {
  const { root, scriptPath } = buildFixture(t, FIXTURE_NOTES);
  const outPath = resolve(root, "OUT.md");

  const { status } = runNode(scriptPath, ["v1.2.3", outPath], { cwd: root });

  assert.equal(status, 0);
  assert.match(readFileSync(outPath, "utf8"), /Added the thing\./);
});

test("defaults the output file to RELEASE_BODY.md at the root when none is given", (t) => {
  const { root, scriptPath } = buildFixture(t, FIXTURE_NOTES);

  const { status } = runNode(scriptPath, ["1.2.3"], { cwd: root });

  assert.equal(status, 0);
  const defaultPath = resolve(root, "RELEASE_BODY.md");
  assert.ok(existsSync(defaultPath));
  assert.match(readFileSync(defaultPath, "utf8"), /Added the thing\./);
});

test("fails clearly when the requested version has no heading at all", (t) => {
  const { root, scriptPath } = buildFixture(t, FIXTURE_NOTES);
  const outPath = resolve(root, "OUT.md");

  const { status, stderr } = runNode(scriptPath, ["9.9.9", outPath], { cwd: root });

  assert.equal(status, 1);
  assert.match(stderr, /no RELEASE-NOTES\.md section for 9\.9\.9/);
  assert.equal(existsSync(outPath), false);
});

test("fails clearly when the requested version's heading exists but has no content under it", (t) => {
  const emptyNotes = ["# Release notes", "", "## 1.2.3", "", "## 1.2.2", "", "- Older notes.", ""].join("\n");
  const { root, scriptPath } = buildFixture(t, emptyNotes);
  const outPath = resolve(root, "OUT.md");

  const { status, stderr } = runNode(scriptPath, ["1.2.3", outPath], { cwd: root });

  assert.equal(status, 1);
  assert.match(stderr, /'## 1\.2\.3' section has no content under the heading/);
  assert.equal(existsSync(outPath), false);
});

test("fails clearly when the requested version's heading exists with only blank lines under it", (t) => {
  const blankNotes = ["## 1.2.3", "", "   ", "", "## 1.2.2", "", "- Older notes.", ""].join("\n");
  const { root, scriptPath } = buildFixture(t, blankNotes);
  const outPath = resolve(root, "OUT.md");

  const { status, stderr } = runNode(scriptPath, ["1.2.3", outPath], { cwd: root });

  assert.equal(status, 1);
  assert.match(stderr, /'## 1\.2\.3' section has no content under the heading/);
  assert.equal(existsSync(outPath), false);
});

test("falls back to GITHUB_REF_NAME when no tag argument is given", (t) => {
  const { root, scriptPath } = buildFixture(t, FIXTURE_NOTES);

  // no argv[2] tag, so the script falls back to GITHUB_REF_NAME; with no argv[3] either, the
  // output file defaults to RELEASE_BODY.md at the fixture root.
  const { status } = runNode(scriptPath, [], {
    cwd: root,
    env: { ...process.env, GITHUB_REF_NAME: "v1.2.3" },
  });

  assert.equal(status, 0);
  assert.match(readFileSync(resolve(root, "RELEASE_BODY.md"), "utf8"), /Added the thing\./);
});
