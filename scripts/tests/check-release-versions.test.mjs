// what-it-is:   unit tests for the release tag-vs-manifest version guard
// what-it-does: copies scripts/check-release-versions.mjs and scripts/lib/version-manifest.mjs
//               into an isolated temp fixture tree (mirroring the real repo's relative layout, since
//               the script resolves its root from its own file location), writes crafted
//               package.json / library.json / .claude-plugin/plugin.json fixtures, and runs the
//               copied script as a child process against them
// why:          this is the tag guard the family release pattern depends on to stop a mismatched
//               tag from ever reaching a published GitHub Release (S-07 CI-pipeline spec, AC-4);
//               before this file, "npm test" collected zero tests and reported green regardless of
//               whether this guard actually guards anything
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { runNode } from "./helpers/proc.mjs";
import { tempDir, copyInto } from "./helpers/tmp.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..", "..");
const SRC_SCRIPT = resolve(REPO_ROOT, "scripts", "check-release-versions.mjs");
const SRC_MANIFEST = resolve(REPO_ROOT, "scripts", "lib", "version-manifest.mjs");

/** Build an isolated copy of the script + its manifest module under a fresh temp root. */
function buildFixture(t) {
  const root = tempDir(t, "check-release-versions-");
  const scriptPath = resolve(root, "scripts", "check-release-versions.mjs");
  copyInto(scriptPath, SRC_SCRIPT);
  copyInto(resolve(root, "scripts", "lib", "version-manifest.mjs"), SRC_MANIFEST);
  return { root, scriptPath };
}

/** Write package.json, library.json, and .claude-plugin/plugin.json with the given versions. */
function writeManifests(root, { pkg, lib, plugin }) {
  writeFileSync(resolve(root, "package.json"), JSON.stringify({ name: "fixture", version: pkg }));
  writeFileSync(resolve(root, "library.json"), JSON.stringify({ name: "fixture", version: lib }));
  mkdirSync(resolve(root, ".claude-plugin"), { recursive: true });
  writeFileSync(resolve(root, ".claude-plugin", "plugin.json"), JSON.stringify({ name: "fixture", version: plugin }));
}

test("version guard passes when every manifest agrees with the tag", (t) => {
  const { root, scriptPath } = buildFixture(t);
  writeManifests(root, { pkg: "1.2.3", lib: "1.2.3", plugin: "1.2.3" });

  const { status, stdout } = runNode(scriptPath, ["1.2.3"], { cwd: root });

  assert.equal(status, 0);
  assert.match(stdout, /ok: package\.json = 1\.2\.3/);
  assert.match(stdout, /ok: library\.json = 1\.2\.3/);
  assert.match(stdout, /ok: \.claude-plugin[\\/]plugin\.json = 1\.2\.3/);
  assert.match(stdout, /version guard passed: every version-bearing manifest agrees with tag v1\.2\.3/);
});

test("version guard strips a leading 'v' from the tag before comparing", (t) => {
  const { root, scriptPath } = buildFixture(t);
  writeManifests(root, { pkg: "1.2.3", lib: "1.2.3", plugin: "1.2.3" });

  const { status, stdout } = runNode(scriptPath, ["v1.2.3"], { cwd: root });

  assert.equal(status, 0);
  assert.match(stdout, /version guard passed: every version-bearing manifest agrees with tag v1\.2\.3/);
});

test("version guard fails when one manifest disagrees with the tag, and still reports every file", (t) => {
  const { root, scriptPath } = buildFixture(t);
  writeManifests(root, { pkg: "1.2.3", lib: "1.2.3", plugin: "1.2.4" });

  const { status, stdout, stderr } = runNode(scriptPath, ["1.2.3"], { cwd: root });

  assert.equal(status, 1);
  // the two agreeing files are still checked and reported, not short-circuited on first failure
  assert.match(stdout, /ok: package\.json = 1\.2\.3/);
  assert.match(stdout, /ok: library\.json = 1\.2\.3/);
  assert.match(stderr, /\.claude-plugin[\\/]plugin\.json version "1\.2\.4" does not match tag "1\.2\.3"/);
  assert.match(stderr, /version guard failed: tag\/version mismatch; aborting before publishing a release/);
});

test("version guard fails clearly when a listed manifest file is missing", (t) => {
  const { root, scriptPath } = buildFixture(t);
  // write only two of the three; library.json is never created
  writeFileSync(resolve(root, "package.json"), JSON.stringify({ version: "1.2.3" }));
  mkdirSync(resolve(root, ".claude-plugin"), { recursive: true });
  writeFileSync(resolve(root, ".claude-plugin", "plugin.json"), JSON.stringify({ version: "1.2.3" }));

  const { status, stderr } = runNode(scriptPath, ["1.2.3"], { cwd: root });

  assert.equal(status, 1);
  assert.match(stderr, /error: library\.json:/);
});

test("version guard exits 2 with a usage message when no tag is given and GITHUB_REF_NAME is unset", (t) => {
  const { root, scriptPath } = buildFixture(t);
  writeManifests(root, { pkg: "1.2.3", lib: "1.2.3", plugin: "1.2.3" });

  const { status, stderr } = runNode(scriptPath, [], {
    cwd: root,
    env: { ...process.env, GITHUB_REF_NAME: "" },
  });

  assert.equal(status, 2);
  assert.match(stderr, /usage: node scripts\/check-release-versions\.mjs <tag-or-version>/);
});

test("version guard falls back to GITHUB_REF_NAME when no tag argument is given", (t) => {
  const { root, scriptPath } = buildFixture(t);
  writeManifests(root, { pkg: "1.2.3", lib: "1.2.3", plugin: "1.2.3" });

  const { status, stdout } = runNode(scriptPath, [], {
    cwd: root,
    env: { ...process.env, GITHUB_REF_NAME: "v1.2.3" },
  });

  assert.equal(status, 0);
  assert.match(stdout, /version guard passed: every version-bearing manifest agrees with tag v1\.2\.3/);
});
