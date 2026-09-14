// what-it-is:   unit tests for the front-door envelope-count guard
// what-it-does: exercises every figure shape it claims to cover (prose, the shields.io badge value,
//               the badge alt text), the disagreement path, the refuse-on-zero precondition, and a
//               live check that the real README.md and ROADMAP.md currently agree with the tree
// why:          six hand-typed figures across two documents said 502 while the tree held 541, and
//               nothing noticed for weeks. A guard whose own patterns are untested would have
//               reported PASS over the badge it never matched, which is the failure it exists to
//               prevent
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, mkdirSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { tempDir } from "./helpers/tmp.mjs";
import { checkReadmeFigures, countEnvelopes } from "../check-readme-figures.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..", "..");

/** A results tree holding exactly `n` envelopes, spread across two run roots and nested dirs. */
function resultsTree(t, n) {
  const dir = tempDir(t, "figures-results-");
  const runs = join(dir, "runs", "critique-toy", "toy-001");
  mkdirSync(runs, { recursive: true });
  for (let i = 0; i < n; i += 1) writeFileSync(join(runs, `haiku-r${i}.json`), "{}");
  // A sidecar and a non-run directory, neither of which may be counted.
  writeFileSync(join(runs, "haiku-r0.raw.txt"), "raw");
  mkdirSync(join(dir, "notes"), { recursive: true });
  writeFileSync(join(dir, "notes", "stray.json"), "{}");
  return dir;
}

function doc(t, body) {
  const dir = tempDir(t, "figures-doc-");
  const p = join(dir, "DOC.md");
  writeFileSync(p, body);
  return p;
}

test("counts only *.json under runs* roots, ignoring sidecars and other directories", (t) => {
  assert.equal(countEnvelopes(resultsTree(t, 7)), 7);
});

test("passes when prose, badge value and badge alt text all agree with the tree", (t) => {
  const results = resultsTree(t, 12);
  const file = doc(
    t,
    [
      "![b](https://img.shields.io/badge/run%20envelopes-12-purple) <!-- alt Run envelopes: 12 -->",
      "The benchmark holds 12 run envelopes.",
      "A deterministic benchmark with 12 committed run envelopes across two tiers.",
    ].join("\n"),
  );
  assert.equal(checkReadmeFigures({ files: [file], resultsDir: results }), 0);
});

test("fails on a stale prose figure", (t) => {
  const file = doc(t, "The benchmark holds 502 run envelopes.");
  assert.equal(checkReadmeFigures({ files: [file], resultsDir: resultsTree(t, 541) }), 1);
});

test("fails on a stale badge value, which prose-only matching would miss", (t) => {
  const file = doc(t, "![b](https://img.shields.io/badge/run%20envelopes-502-purple)");
  assert.equal(checkReadmeFigures({ files: [file], resultsDir: resultsTree(t, 541) }), 1);
});

test("fails on stale badge alt text", (t) => {
  const file = doc(t, '<img src="x" alt="Run envelopes: 502">');
  assert.equal(checkReadmeFigures({ files: [file], resultsDir: resultsTree(t, 541) }), 1);
});

test("refuses to validate against an empty tree rather than passing vacuously", (t) => {
  const empty = tempDir(t, "figures-empty-");
  const file = doc(t, "The benchmark holds 541 run envelopes.");
  assert.equal(checkReadmeFigures({ files: [file], resultsDir: empty }), 1);
});

test("fails when a named document does not exist", (t) => {
  const results = resultsTree(t, 3);
  assert.equal(checkReadmeFigures({ files: [join(tempDir(t, "figures-absent-"), "absent.md")], resultsDir: results }), 1);
});

test("the shipped README.md and ROADMAP.md agree with the committed tree", () => {
  assert.equal(
    checkReadmeFigures({
      files: [join(REPO_ROOT, "README.md"), join(REPO_ROOT, "ROADMAP.md")],
      resultsDir: join(REPO_ROOT, "bench", "results"),
    }),
    0,
  );
});
