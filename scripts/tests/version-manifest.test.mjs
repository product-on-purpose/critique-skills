// what-it-is:   unit tests for the single enumeration of every version-bearing file
// what-it-does: imports the real scripts/lib/version-manifest.mjs directly (importing it has no
//               side effects; its readEntryVersions() helper reads files only when called) and
//               checks that its enumeration is complete, that every listed file exists on disk,
//               and that the real repo's version-bearing files currently agree with each other (a
//               live consistency check: disagreement here is exactly what the tag guard exists to
//               catch)
// why:          the release tag guard and any future version-bump tool must read from exactly one
//               list, or the two drift apart (S-07 CI-pipeline spec, deliverable 4); this file
//               proves the enumeration itself is correct, independent of the guard that consumes it
//               (that guard's own pass/fail behavior is covered in check-release-versions.test.mjs)
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { VERSION_MANIFESTS, readEntryVersions } from "../lib/version-manifest.mjs";
import { tempDir } from "./helpers/tmp.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..", "..");

test("enumerates exactly the five version-bearing files this repo's release pattern expects", () => {
  assert.equal(VERSION_MANIFESTS.length, 5);
  const files = VERSION_MANIFESTS.map((m) => m.file).sort();
  assert.deepEqual(
    files,
    [
      ".claude-plugin/plugin.json",
      "library.json",
      "package.json",
      "docs/how-to/gate-in-ci.md",
      "examples/recipes/gate-in-ci.md",
    ].sort(),
  );
  for (const entry of VERSION_MANIFESTS) {
    assert.equal(typeof entry.file, "string");
    // every entry is exactly one of the two shapes: a JSON pointer, or a prose regex pattern
    assert.notEqual(Boolean(entry.pointer), Boolean(entry.pattern), `${entry.file}: must have exactly one of pointer/pattern`);
    if (entry.pointer) {
      assert.equal(typeof entry.pointer, "string");
      assert.ok(entry.pointer.length > 0, `${entry.file}: pointer must not be empty`);
    } else {
      assert.equal(typeof entry.pattern, "string");
      assert.ok(entry.pattern.length > 0, `${entry.file}: pattern must not be empty`);
    }
  }
});

test("every enumerated file exists on disk at the repo root", () => {
  for (const { file } of VERSION_MANIFESTS) {
    assert.ok(existsSync(resolve(REPO_ROOT, file)), `${file} does not exist at repo root`);
  }
});

test("every enumerated entry resolves to exactly one non-empty version in its real file", () => {
  for (const entry of VERSION_MANIFESTS) {
    const versions = readEntryVersions(entry, REPO_ROOT);
    assert.equal(versions.length, 1, `${entry.file}: expected one version, got ${versions.join(", ")}`);
    assert.equal(typeof versions[0], "string", `${entry.file} did not resolve to a string`);
    assert.ok(versions[0].length > 0, `${entry.file} resolved to an empty string`);
  }
});

test("detects disagreement: every enumerated file's real version currently agrees with the others", () => {
  const versions = VERSION_MANIFESTS.map((entry) => ({
    file: entry.file,
    version: readEntryVersions(entry, REPO_ROOT)[0],
  }));
  const distinct = new Set(versions.map((v) => v.version));
  assert.equal(
    distinct.size,
    1,
    `version-bearing files disagree: ${versions.map((v) => `${v.file}=${v.version}`).join(", ")}`,
  );
});

test("a pattern entry matching nothing throws, naming the pattern", () => {
  assert.throws(
    () => readEntryVersions({ file: "package.json", pattern: "NOPE-(\\d+)" }, REPO_ROOT),
    /pattern NOPE-\(\\d\+\) matched nothing/,
  );
});

test("a pattern entry with two matching pins of the same version dedupes to one", (t) => {
  const root = tempDir(t, "version-manifest-pattern-");
  writeFileSync(resolve(root, "prose.md"), "pins `v1.2.3` here, and again: ref: v1.2.3\n");
  const versions = readEntryVersions(
    { file: "prose.md", pattern: "(?:ref: v|pins `v)(\\d+\\.\\d+\\.\\d+)" },
    root,
  );
  assert.deepEqual(versions, ["1.2.3"]);
});

test("a pattern entry whose two pins disagree returns both distinct versions", (t) => {
  const root = tempDir(t, "version-manifest-pattern-");
  writeFileSync(resolve(root, "prose.md"), "pins `v1.2.3` here, and again: ref: v1.2.4\n");
  const versions = readEntryVersions(
    { file: "prose.md", pattern: "(?:ref: v|pins `v)(\\d+\\.\\d+\\.\\d+)" },
    root,
  );
  assert.deepEqual(versions.sort(), ["1.2.3", "1.2.4"]);
});
