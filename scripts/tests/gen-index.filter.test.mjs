// what-it-is:   unit tests for the INDEX.md phantom-row filter
// what-it-does: exercises dropPhantomRows() against a scratch directory of real files/dirs, so
//               existsSync() resolution is tested for real rather than mocked
// why:          this repo's central claim is that nothing is asserted without evidence, and
//               dropPhantomRows() is the enforcement point for that claim in INDEX.md; it needs
//               its own coverage independent of regenerating the whole file
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
//
// Deliberately imports only from lib/gen-index-filter.mjs, not scripts/gen-index.mjs: that wrapper
// resolves a local agent-skills-toolkit checkout as a module-load side effect and exits if one is
// not found, but the unit-node CI job does not check the toolkit out. dropPhantomRows() itself has
// no toolkit dependency, so importing it directly keeps this test runnable there.
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { dropPhantomRows } from "../lib/gen-index-filter.mjs";

let root;

before(() => {
  root = mkdtempSync(join(tmpdir(), "gen-index-filter-"));
  writeFileSync(join(root, "README.md"), "# fixture\n");
  mkdirSync(join(root, "docs"));
  writeFileSync(join(root, "docs", "real.md"), "# real\n");
});

after(() => {
  rmSync(root, { recursive: true, force: true });
});

test("keeps a single-link row whose target exists", () => {
  const input = "- [`README.md`](README.md) - overview.";
  assert.equal(dropPhantomRows(input, root), input);
});

test("drops a single-link row whose target is missing", () => {
  const input = "- [`STANDARD.md`](STANDARD.md) - the standard.";
  assert.equal(dropPhantomRows(input, root), "");
});

test("does not split a single-link row on a semicolon inside trailing prose", () => {
  const input = "- [`README.md`](README.md) - overview (generated; do not hand-edit).";
  assert.equal(dropPhantomRows(input, root), input);
});

test("drops a single-link row whole even when its own trailing prose has a semicolon", () => {
  const input = "- [`STANDARD.md`](STANDARD.md) - the standard (generated; do not hand-edit).";
  assert.equal(dropPhantomRows(input, root), "");
});

test("keeps a multi-link row unchanged when every link exists", () => {
  const input = "- [`README.md`](README.md) - overview; [`docs/real.md`](docs/real.md) - real doc.";
  assert.equal(dropPhantomRows(input, root), input);
});

test("keeps only the surviving segments of a partially-phantom multi-link row, restoring the trailing period", () => {
  const input =
    "- [`docs/real.md`](docs/real.md) - real doc; [`docs/ghost.md`](docs/ghost.md) - missing; " +
    "[`docs/also-ghost.md`](docs/also-ghost.md) - also missing.";
  assert.equal(dropPhantomRows(input, root), "- [`docs/real.md`](docs/real.md) - real doc.");
});

test("drops a multi-link row entirely when every segment is phantom", () => {
  const input =
    "- [`docs/ghost.md`](docs/ghost.md) - missing; [`docs/also-ghost.md`](docs/also-ghost.md) - also missing.";
  assert.equal(dropPhantomRows(input, root), "");
});

test("resolves an existing directory target with a trailing slash", () => {
  const input = "- [`docs/`](docs/) - Diataxis docs.";
  assert.equal(dropPhantomRows(input, root), input);
});

test("drops a missing directory target with a trailing slash", () => {
  const input = "- [`templates/`](templates/) - scaffolder templates.";
  assert.equal(dropPhantomRows(input, root), "");
});

test("passes through lines with no markdown link unchanged, including bullet prose like '- none'", () => {
  const input = ["# INDEX - fixture", "", "### Commands (0)", "", "- none", ""].join("\n");
  assert.equal(dropPhantomRows(input, root), input);
});

test("preserves surrounding lines, dropping only the phantom row among them", () => {
  const input = [
    "## Manifests",
    "",
    "- [`README.md`](README.md) - overview.",
    "- [`STANDARD.md`](STANDARD.md) - the standard.",
    "",
  ].join("\n");
  const expected = ["## Manifests", "", "- [`README.md`](README.md) - overview.", ""].join("\n");
  assert.equal(dropPhantomRows(input, root), expected);
});

test("is idempotent: filtering already-filtered text is a no-op", () => {
  const input = [
    "- [`README.md`](README.md) - overview.",
    "- [`STANDARD.md`](STANDARD.md) - the standard.",
    "- [`docs/real.md`](docs/real.md) - real; [`docs/ghost.md`](docs/ghost.md) - missing.",
  ].join("\n");
  const once = dropPhantomRows(input, root);
  const twice = dropPhantomRows(once, root);
  assert.equal(twice, once);
});
