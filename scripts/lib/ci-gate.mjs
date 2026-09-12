// what-it-is:   pure parser and assertion for the aggregate gate job in .github/workflows/ci.yml
// what-it-does: lists the jobs ci.yml declares, reads the gate job's `needs:`, and reports whether
//               the gate depends on every other job and still carries the `if: always()` that makes
//               it able to fail
// why:          branch protection on main requires the single "ci-ok" context instead of the
//               fourteen matrix-expanded ones (docs/internal/decisions/0033-aggregate-ci-gate.md).
//               That only gates the pipeline if ci-ok actually depends on all of it, so a job added
//               without a `needs:` entry would be a job nothing gates, and nothing would say so.
// used-by:      scripts/gen-plugin-manifest.mjs --check (ci.yml's "drift" job),
//               scripts/tests/gen-plugin-manifest.test.mjs
//
// Text, not YAML: package.json declares no dependencies, and adding a YAML parser to assert two
// fields is a worse trade than a regex scoped to a file this repo controls the shape of. The scan
// starts after the top-level `jobs:` key on purpose. `push:` under `on:` and `contents:` under
// `permissions:` sit at the same two-space indent as a job name, so a scan that just matched the
// indent would decide "push" is a job and demand the gate depend on it.
//
// Has no toolkit dependency, so it is unit-testable without a local agent-skills-toolkit checkout,
// which is why it lives here rather than inside gen-plugin-manifest.mjs.

/** The job whose name is the one required status check on main. */
export const GATE_JOB = "ci-ok";

/**
 * Every job key ci.yml declares, in file order, or null when there is no top-level `jobs:` key.
 */
export function findCiJobs(ciText) {
  const lines = ciText.split(/\r?\n/);
  const start = lines.findIndex((line) => /^jobs:\s*$/.test(line));
  if (start === -1) return null;

  const jobs = [];
  for (let i = start + 1; i < lines.length; i++) {
    const line = lines[i];
    if (/^\S/.test(line)) break; // a new top-level key ends the jobs block
    const match = /^ {2}([A-Za-z0-9_-]+):\s*$/.exec(line);
    if (match) jobs.push(match[1]);
  }
  return jobs;
}

/**
 * The lines of one job's block: everything under `  <name>:` up to the next job or top-level key.
 */
function jobBlock(ciText, jobName) {
  const lines = ciText.split(/\r?\n/);
  // Plain string compare rather than a built regex: job keys are [A-Za-z0-9_-] only, so there is
  // nothing to escape, and so nothing to get wrong escaping it.
  const header = `  ${jobName}:`;
  const start = lines.findIndex((line) => line.trimEnd() === header);
  if (start === -1) return null;

  const block = [];
  for (let i = start + 1; i < lines.length; i++) {
    const line = lines[i];
    if (/^\S/.test(line) || /^ {2}\S/.test(line)) break;
    block.push(line);
  }
  return block;
}

/**
 * The job names in a job's `needs:`, handling both the inline (`needs: [a, b]`) and the block
 * (`needs:` then `  - a`) forms, or null when the job has no `needs:` at all.
 */
export function findJobNeeds(ciText, jobName) {
  const block = jobBlock(ciText, jobName);
  if (block === null) return null;

  for (let i = 0; i < block.length; i++) {
    const inline = /^ {4}needs:\s*\[(.*)\]\s*$/.exec(block[i]);
    if (inline) {
      return inline[1]
        .split(",")
        .map((name) => name.trim().replace(/^['"]|['"]$/g, ""))
        .filter(Boolean);
    }
    const single = /^ {4}needs:\s*([A-Za-z0-9_-]+)\s*$/.exec(block[i]);
    if (single) return [single[1]];

    if (/^ {4}needs:\s*$/.test(block[i])) {
      const needs = [];
      for (let j = i + 1; j < block.length; j++) {
        const item = /^ {6}-\s*['"]?([A-Za-z0-9_-]+)['"]?\s*$/.exec(block[j]);
        if (!item) break;
        needs.push(item[1]);
      }
      return needs;
    }
  }
  return null;
}

/** True when the job carries a job-level `if: always()`. */
export function gateAlwaysRuns(ciText, jobName = GATE_JOB) {
  const block = jobBlock(ciText, jobName);
  if (block === null) return false;
  return block.some((line) => /^ {4}if:\s*always\(\)\s*$/.test(line));
}

/**
 * The assertion the drift job runs: ci-ok exists, always runs, and depends on every other job.
 * Returns { ok, messages } in the shape gen-plugin-manifest.mjs's other checks use.
 */
export function checkCiGate(ciText) {
  const jobs = findCiJobs(ciText);
  if (jobs === null) {
    return { ok: false, messages: ["ci.yml has no top-level `jobs:` key; the CI gate check cannot run."] };
  }
  if (!jobs.includes(GATE_JOB)) {
    return {
      ok: false,
      messages: [
        `ci.yml declares no "${GATE_JOB}" job, and branch protection on main requires that ` +
          "context. Every pull request would block on a check nothing emits.",
      ],
    };
  }

  const messages = [];
  let ok = true;

  const expected = jobs.filter((job) => job !== GATE_JOB);
  const needs = findJobNeeds(ciText, GATE_JOB) ?? [];
  const missing = expected.filter((job) => !needs.includes(job));
  const unknown = needs.filter((job) => !jobs.includes(job));

  if (missing.length > 0) {
    ok = false;
    messages.push(
      `"${GATE_JOB}" does not depend on every job in ci.yml, so these are gated by nothing:`,
      ...missing.map((job) => `  - ${job}`),
      `Add them to the "${GATE_JOB}" job's \`needs:\`.`,
    );
  }
  if (unknown.length > 0) {
    ok = false;
    messages.push(
      `"${GATE_JOB}" lists jobs in \`needs:\` that ci.yml does not declare:`,
      ...unknown.map((job) => `  - ${job}`),
    );
  }
  if (!gateAlwaysRuns(ciText)) {
    ok = false;
    messages.push(
      `"${GATE_JOB}" is missing its job-level \`if: always()\`. Without it the job is skipped ` +
        "whenever a job it needs fails, and branch protection counts a skipped check as a passing " +
        "one: the gate would go green exactly when it should fail.",
    );
  }
  if (ok) {
    messages.push(`"${GATE_JOB}" always runs and gates all ${expected.length} of ci.yml's other jobs.`);
  }
  return { ok, messages };
}
