// what-it-is:   unit tests for the single enumeration of every version-bearing file
// what-it-does: imports the real scripts/lib/version-manifest.mjs directly (it is pure data, no
//               filesystem or process side effects, so importing it is safe) and checks that its
//               enumeration is complete, that every listed file exists on disk, and that the real
//               repo's version-bearing files currently agree with each other (a live consistency
//               check: disagreement here is exactly what the tag guard exists to catch)
// why:          the release tag guard and any future version-bump tool must read from exactly one
//               list, or the two drift apart (S-07 CI-pipeline spec, deliverable 4); this file
//               proves the enumeration itself is correct, independent of the guard that consumes it
//               (that guard's own pass/fail behavior is covered in check-release-versions.test.mjs)
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { VERSION_MANIFESTS } from "../lib/version-manifest.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..", "..");

/** Minimal dot-path getter, mirroring check-release-versions.mjs's readPointer(). Duplicated
 * deliberately (it is three lines) rather than imported, so this file exercises the manifest's
 * data shape independently of the guard script's own implementation. */
function readPointer(data, pointer) {
  return pointer.split(".").reduce((node, key) => (node == null ? node : node[key]), data);
}

test("enumerates exactly the three version-bearing files this repo's release pattern expects", () => {
  assert.equal(VERSION_MANIFESTS.length, 3);
  const files = VERSION_MANIFESTS.map((m) => m.file).sort();
  assert.deepEqual(files, [".claude-plugin/plugin.json", "library.json", "package.json"].sort());
  for (const entry of VERSION_MANIFESTS) {
    assert.equal(typeof entry.file, "string");
    assert.equal(typeof entry.pointer, "string");
    assert.ok(entry.pointer.length > 0, `${entry.file}: pointer must not be empty`);
  }
});

test("every enumerated file exists on disk at the repo root", () => {
  for (const { file } of VERSION_MANIFESTS) {
    assert.ok(existsSync(resolve(REPO_ROOT, file)), `${file} does not exist at repo root`);
  }
});

test("every enumerated pointer resolves to a non-empty string in its real file", () => {
  for (const { file, pointer } of VERSION_MANIFESTS) {
    const data = JSON.parse(readFileSync(resolve(REPO_ROOT, file), "utf8"));
    const value = readPointer(data, pointer);
    assert.equal(typeof value, "string", `${file}: ${pointer} did not resolve to a string`);
    assert.ok(value.length > 0, `${file}: ${pointer} resolved to an empty string`);
  }
});

test("detects disagreement: every enumerated file's real version currently agrees with the others", () => {
  const versions = VERSION_MANIFESTS.map(({ file, pointer }) => {
    const data = JSON.parse(readFileSync(resolve(REPO_ROOT, file), "utf8"));
    return { file, version: readPointer(data, pointer) };
  });
  const distinct = new Set(versions.map((v) => v.version));
  assert.equal(
    distinct.size,
    1,
    `version-bearing files disagree: ${versions.map((v) => `${v.file}=${v.version}`).join(", ")}`,
  );
});
