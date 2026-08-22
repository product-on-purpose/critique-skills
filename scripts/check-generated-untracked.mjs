#!/usr/bin/env node
// what-it-is:   the guard that keeps the generated site tree out of git
// what-it-does: regenerates the site content tree, then asserts two things about every file the
//               generator emitted: git ignores it, and git does not track it
// why:          the site uses clause 14.4's preferred model, gitignored-and-rebuilt (site plan
//               3.3), and that model fails silently in two directions. A tracked generated page
//               goes stale against its source and nothing notices, because the build overwrites
//               it locally and CI commits the difference back as noise. A generated directory
//               missing from .gitignore is worse: the list in .gitignore is static, so the first
//               person to add a quadrant or a wing gets a tree of generated files staged into
//               their next commit. Comparing against the generator's own emitted list, rather
//               than against a second copy of the .gitignore list, is what makes the check
//               survive a new emit directory
// used-by:      contributors before a commit, and the build-site job in .github/workflows/ci.yml
//               (wired in W7)
//
// Usage:  node scripts/check-generated-untracked.mjs
// Exit 0 when the generated tree is fully ignored and fully untracked, 1 otherwise.
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { generate } from "./gen-site.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");

/** Run a git command in the repo root and return { status, stdout }. */
function git(args, input) {
  const result = spawnSync("git", args, {
    cwd: ROOT,
    encoding: "utf8",
    input,
  });
  return { status: result.status, stdout: result.stdout ?? "", stderr: result.stderr ?? "" };
}

/**
 * The subset of `paths` that git does not ignore.
 * `git check-ignore --stdin` prints the paths that ARE ignored, and exits 1 when none of them
 * are, which is a legitimate outcome here rather than a failure to run.
 * @param {string[]} paths - repo-relative, POSIX separators
 * @returns {string[]}
 */
function notIgnored(paths) {
  const { status, stdout, stderr } = git(["check-ignore", "--stdin"], paths.join("\n") + "\n");
  if (status !== 0 && status !== 1) {
    throw new Error(`git check-ignore failed (exit ${status}): ${stderr.trim()}`);
  }
  const ignored = new Set(
    stdout
      .split(/\r?\n/)
      .map((line) => line.trim().split("\\").join("/"))
      .filter(Boolean),
  );
  return paths.filter((p) => !ignored.has(p));
}

/**
 * The subset of `paths` that git tracks.
 * @param {string[]} paths - repo-relative, POSIX separators
 * @returns {string[]}
 */
function tracked(paths) {
  const { status, stdout, stderr } = git(["ls-files", "--", ...paths]);
  if (status !== 0) {
    throw new Error(`git ls-files failed (exit ${status}): ${stderr.trim()}`);
  }
  const listed = new Set(
    stdout
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean),
  );
  return paths.filter((p) => listed.has(p));
}

export function check() {
  const { files } = generate({ quiet: true });
  if (files.length === 0) {
    console.error("check-generated-untracked: the generator emitted no files, which is never correct.");
    return 1;
  }

  const problems = [];

  const unignored = notIgnored(files);
  if (unignored.length > 0) {
    problems.push(
      `${unignored.length} generated file(s) are NOT gitignored. Add the emitting directory to ` +
        ".gitignore (see the Astro block there and site plan 3.3):\n  " +
        unignored.join("\n  "),
    );
  }

  const inIndex = tracked(files);
  if (inIndex.length > 0) {
    problems.push(
      `${inIndex.length} generated file(s) are TRACKED by git. Remove them from the index with ` +
        "`git rm --cached <path>`; they are rebuilt on every build:\n  " +
        inIndex.join("\n  "),
    );
  }

  if (problems.length > 0) {
    console.error("check-generated-untracked: FAIL\n\n" + problems.join("\n\n"));
    return 1;
  }

  console.log(
    `check-generated-untracked: OK - ${files.length} generated files, all gitignored, none tracked.`,
  );
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(check());
}
