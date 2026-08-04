// what-it-is:   shared subprocess helper for scripts/tests/*.test.mjs
// what-it-does: spawns `node <scriptPath> [...args]` synchronously in a fresh process and returns
//               its status/stdout/stderr
// why:          several scripts under scripts/ (check-release-versions.mjs,
//               extract-release-notes.mjs, gen-index.mjs, gen-plugin-manifest.mjs) run
//               unconditional top-level code on module load - some with no invokedDirectly guard
//               at all, some (gen-index.mjs) with a guard that still resolves the toolkit and
//               calls process.exit() unconditionally at module scope. Importing any of those
//               directly inside the test runner's own process risks killing the whole test run
//               (or every subsequent test in the file) via a stray process.exit(). Spawning them
//               as a child process is the only safe way to exercise them in isolation.
// used-by:      scripts/tests/*.test.mjs
import { spawnSync } from "node:child_process";

/**
 * Run `node <scriptPath> ...args` as a child process and collect the result.
 * @param {string} scriptPath - absolute path to the .mjs entry point to run
 * @param {string[]} args - CLI arguments
 * @param {object} [options] - forwarded to spawnSync (e.g. cwd, env)
 * @returns {{status: number|null, stdout: string, stderr: string}}
 */
export function runNode(scriptPath, args = [], options = {}) {
  const result = spawnSync(process.execPath, [scriptPath, ...args], {
    encoding: "utf8",
    ...options,
  });
  return { status: result.status, stdout: result.stdout ?? "", stderr: result.stderr ?? "" };
}
