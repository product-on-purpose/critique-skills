// what-it-is:   unit tests for scripts/lib/release-parity.mjs
// what-it-does: holds the committed ci.yml and release.yml in parity, and proves the check fails
//               when release.yml drops a ci.yml command and passes when only an excluded job's is
//               missing
// why:          release.yml once claimed full parity while skipping smoke and build-site (E29,
//               release.yml's re-run parity); a guard that never fails is decoration
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import {
  checkReleaseParity,
  ciDocCheckCommands,
  workflowRunCommands,
  RELEASE_EXCLUDED_JOBS,
} from "../lib/release-parity.mjs";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const read = (name) => readFileSync(resolve(REPO_ROOT, ".github", "workflows", name), "utf8");

const CI = `on:
  push:
jobs:
  smoke:
    steps:
      - run: python scripts/smoke.py --expect no-deps # doc-check
  build-site:
    steps:
      - run: node scripts/check-site.mjs # doc-check
`;

test("the committed release.yml re-runs every ci.yml command outside the excluded jobs", () => {
  const result = checkReleaseParity(read("ci.yml"), read("release.yml"));
  assert.ok(result.ok, result.messages.join("\n"));
});

test("commands are attributed to their job, and on: keys are not read as jobs", () => {
  assert.deepEqual(ciDocCheckCommands(CI), [
    { job: "smoke", command: "python scripts/smoke.py --expect no-deps" },
    { job: "build-site", command: "node scripts/check-site.mjs" },
  ]);
});

test("a release that drops a ci.yml command fails, naming the command and its job", () => {
  const result = checkReleaseParity(CI, "jobs:\n  release:\n    steps:\n      - run: echo nothing\n");
  assert.equal(result.ok, false);
  assert.match(result.messages.join("\n"), /smoke\.py --expect no-deps {2}\(ci\.yml job "smoke"\)/);
});

test("only an excluded job's command missing is a pass", () => {
  assert.ok("build-site" in RELEASE_EXCLUDED_JOBS);
  const release = "      - run: python scripts/smoke.py --expect no-deps\n";
  assert.ok(checkReleaseParity(CI, release).ok);
});

test("a trailing comment on a release run line does not hide the command", () => {
  assert.deepEqual(workflowRunCommands("      run: npm test # doc-check\n      run: |\n"), ["npm test"]);
});
