// what-it-is:   pure assertion that .github/workflows/release.yml re-runs ci.yml's commands
// what-it-does: collects every "# doc-check" command ci.yml runs, attributed to its job, and reports
//               any that release.yml does not run, skipping the jobs a release deliberately omits
// why:          release.yml re-ran 7 of ci.yml's 9 jobs while its header claimed full parity, and
//               the two it skipped included smoke, the only job that sees a fresh install (E29,
//               release.yml's re-run parity). Nothing would have alarmed if the gap widened again.
// used-by:      scripts/gen-plugin-manifest.mjs --check (ci.yml's "drift" job),
//               scripts/tests/release-parity.test.mjs
//
// Text, not YAML, for the same reason as scripts/lib/ci-gate.mjs: package.json declares no
// dependencies, and both files are shaped by this repository.

/**
 * ci.yml jobs whose commands release.yml deliberately does not run, each with the reason. A job
 * belongs here only with a reason a reader can check; anything else missing from release.yml fails.
 */
export const RELEASE_EXCLUDED_JOBS = {
  "build-site":
    "a release publishes no site; deploy-pages.yml builds and guards the site from main with this job's recipe",
};

// A step may open with its `run:` key (`- run: ...`) or carry it on a later line (`run: ...`).
const DOC_CHECK_RE = /^\s*(?:-\s+)?run:\s*(.+?)\s*#\s*doc-check\s*$/;
const RUN_RE = /^\s*(?:-\s+)?run:\s*(.+?)\s*(?:#.*)?$/;

/** `[{ job, command }]` for every "# doc-check" command under ci.yml's top-level `jobs:` key. */
export function ciDocCheckCommands(ciText) {
  const lines = ciText.split(/\r?\n/);
  const start = lines.findIndex((line) => /^jobs:\s*$/.test(line));
  if (start === -1) return [];
  const found = [];
  let job = null;
  for (let i = start + 1; i < lines.length; i++) {
    const line = lines[i];
    if (/^\S/.test(line)) break;
    const jobMatch = /^ {2}([A-Za-z0-9_-]+):\s*$/.exec(line);
    if (jobMatch) {
      job = jobMatch[1];
      continue;
    }
    const cmd = DOC_CHECK_RE.exec(line);
    if (cmd && job) found.push({ job, command: cmd[1].trim() });
  }
  return found;
}

/** Every single-line `run:` command in a workflow, trailing comment removed. */
export function workflowRunCommands(text) {
  return text
    .split(/\r?\n/)
    .map((line) => RUN_RE.exec(line))
    .filter((m) => m && m[1].trim() !== "|" && m[1].trim() !== ">")
    .map((m) => m[1].trim());
}

/** `{ ok, messages }`: whether release.yml runs every ci.yml command outside the excluded jobs. */
export function checkReleaseParity(ciText, releaseText) {
  const ci = ciDocCheckCommands(ciText);
  if (ci.length === 0) {
    return { ok: false, messages: ["no '# doc-check' commands found in ci.yml; release parity has nothing to compare."] };
  }
  const released = new Set(workflowRunCommands(releaseText));
  const required = ci.filter((c) => !(c.job in RELEASE_EXCLUDED_JOBS));
  const missing = required.filter((c) => !released.has(c.command));
  if (missing.length > 0) {
    return {
      ok: false,
      messages: [
        "release.yml does not re-run these ci.yml commands (E29, release.yml's re-run parity):",
        ...missing.map((c) => `  - ${c.command}  (ci.yml job "${c.job}")`),
        `Run them in release.yml, or add the job to RELEASE_EXCLUDED_JOBS in scripts/lib/release-parity.mjs with a reason.`,
      ],
    };
  }
  const skipped = Object.keys(RELEASE_EXCLUDED_JOBS).join(", ");
  return {
    ok: true,
    messages: [`release.yml re-runs all ${required.length} ci.yml command(s) outside the excluded job(s): ${skipped}.`],
  };
}
