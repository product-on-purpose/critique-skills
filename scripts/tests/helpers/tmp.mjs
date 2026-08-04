// what-it-is:   shared temp-fixture helpers for scripts/tests/*.test.mjs
// what-it-does: creates an isolated mkdtemp directory per test, registers its cleanup with the
//               test's own TestContext#after (so it is removed even when the test fails), and
//               copies a file into a fixture tree while creating parent directories as needed
// why:          check-release-versions.mjs and extract-release-notes.mjs resolve their working
//               root relative to their own file location (ROOT = resolve(HERE, "..")) rather than
//               accepting a root argument, so testing them in isolation means copying the script
//               (and whatever it statically imports) into a temp directory laid out the same way,
//               never mutating the real repo, and never leaving artifacts behind
// used-by:      scripts/tests/*.test.mjs
import { mkdtempSync, mkdirSync, copyFileSync, cpSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";

/**
 * Create an mkdtemp directory under the OS temp root and register its removal with `t`.
 * @param {import('node:test').TestContext} t
 * @param {string} prefix
 * @returns {string} absolute path to the new directory
 */
export function tempDir(t, prefix) {
  const dir = mkdtempSync(join(tmpdir(), prefix));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  return dir;
}

/** Copy srcPath to destPath, creating destPath's parent directories first. */
export function copyInto(destPath, srcPath) {
  mkdirSync(dirname(destPath), { recursive: true });
  copyFileSync(srcPath, destPath);
}

/**
 * Copy an entire directory (e.g. scripts/lib/) into destDir, recursively. Used instead of
 * copyInto() with a hardcoded file list so a fixture stays correct if the source script's own
 * lib/ imports change (add or drop a sibling module) without this helper needing to know which.
 */
export function copyDirInto(destDir, srcDir) {
  mkdirSync(destDir, { recursive: true });
  cpSync(srcDir, destDir, { recursive: true });
}
