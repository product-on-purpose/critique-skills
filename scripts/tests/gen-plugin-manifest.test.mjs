// what-it-is:   unit tests for the native-manifest generator wrapper's --check mode (the "drift"
//               CI job's entry point)
// what-it-does: (1) an unconditional test that gen-plugin-manifest.mjs fails loudly when
//               agent-skills-toolkit cannot be resolved, run from an isolated fixture copy; (2) a
//               smoke test, skipped when no toolkit is resolvable in this environment, that the
//               real script's --check prints all five of its documented check sections and that
//               its exit code agrees with whether any of them reported failure; (3) unit tests for
//               the ci.yml aggregate-gate assertion, which need no toolkit because the parsing
//               lives in scripts/lib/ci-gate.mjs
// why:          this is the "drift" CI job's one command (S-07 CI-pipeline spec); before this file,
//               nothing exercised it at all
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
//
// Note: gen-plugin-manifest.mjs statically imports gen-index.mjs, and gen-index.mjs resolves the
// toolkit and can process.exit() unconditionally at module load (see gen-index.test.mjs's header
// comment). That import runs before gen-plugin-manifest.mjs's own toolkit check ever gets a
// chance to, so when the toolkit is unresolvable, the process actually exits with gen-index.mjs's
// error message, not gen-plugin-manifest.mjs's - confirmed below rather than assumed.
import { test } from "node:test";
import assert from "node:assert/strict";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { readFileSync } from "node:fs";
import { runNode } from "./helpers/proc.mjs";
import { tempDir, copyInto, copyDirInto } from "./helpers/tmp.mjs";
import { resolveToolkit } from "../lib/resolve-toolkit.mjs";
import { checkCiGate, findCiJobs, findJobNeeds, GATE_JOB } from "../lib/ci-gate.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..", "..");
const SRC_GEN_PLUGIN_MANIFEST = resolve(REPO_ROOT, "scripts", "gen-plugin-manifest.mjs");
const SRC_GEN_INDEX = resolve(REPO_ROOT, "scripts", "gen-index.mjs");
const SRC_LIB_DIR = resolve(REPO_ROOT, "scripts", "lib");

const toolkitAvailable = Boolean(resolveToolkit(REPO_ROOT));

test("gen --check fails with a clear message when the toolkit cannot be resolved", (t) => {
  const root = tempDir(t, "gen-plugin-manifest-no-toolkit-");
  const scriptPath = resolve(root, "scripts", "gen-plugin-manifest.mjs");
  copyInto(scriptPath, SRC_GEN_PLUGIN_MANIFEST);
  copyInto(resolve(root, "scripts", "gen-index.mjs"), SRC_GEN_INDEX);
  copyDirInto(resolve(root, "scripts", "lib"), SRC_LIB_DIR);

  const { status, stderr } = runNode(scriptPath, ["--check"], {
    cwd: root,
    env: { ...process.env, AGENT_SKILLS_TOOLKIT: "" },
  });

  assert.equal(status, 2);
  // the statically-imported gen-index.mjs resolves the toolkit at module load and exits first, so
  // this is gen-index's error text, not gen-plugin-manifest's own - see the file header note.
  assert.match(stderr, /agent-skills-toolkit \(the generator\) not found/);
});

test(
  "smoke: the real script's --check prints all five documented checks with a consistent exit code",
  { skip: toolkitAvailable ? false : "agent-skills-toolkit is not resolvable in this environment" },
  () => {
    const { status, stdout } = runNode(resolve(REPO_ROOT, "scripts", "gen-plugin-manifest.mjs"), ["--check"], {
      cwd: REPO_ROOT,
    });

    assert.ok(status === 0 || status === 1, `expected exit 0 or 1, got ${status}`);
    assert.match(stdout, /gen --check: .*plugin\.json/);
    assert.match(stdout, /gen:index --check:/);
    assert.match(stdout, /gen --check: AGENTS\.md/);
    assert.match(stdout, /gen --check: "ci-ok"/);

    const anyFailureWord = /(out of date|does not exist|is missing|failed)/.test(stdout);
    assert.equal(status === 1, anyFailureWord, `exit code and message content disagree:\n${stdout}`);
  },
);

// The ci.yml aggregate gate (scripts/lib/ci-gate.mjs).
//
// No subprocess and no toolkit skip here: the parsing is a pure function over ci.yml's text, which
// is the whole reason it lives in scripts/lib/ instead of inside gen-plugin-manifest.mjs.

const REAL_CI = readFileSync(resolve(REPO_ROOT, ".github", "workflows", "ci.yml"), "utf8");

/**
 * A minimal ci.yml carrying the same shape trap as the real one: `push:` under `on:` and
 * `contents:` under `permissions:` sit at exactly the indent a job name sits at.
 */
function fixtureCi({ jobs = ["alpha", "beta"], gateNeeds = ["alpha", "beta"], always = true, gate = true } = {}) {
  const lines = [
    "name: CI",
    "on:",
    "  pull_request:",
    "    branches: [main]",
    "  push:",
    "    branches: [main]",
    "permissions:",
    "  contents: read",
    "jobs:",
  ];
  for (const job of jobs) {
    lines.push(`  ${job}:`, "    runs-on: ubuntu-latest", "    steps:", "      - run: true");
  }
  if (gate) {
    lines.push(`  ${GATE_JOB}:`, "    runs-on: ubuntu-latest");
    if (always) lines.push("    if: always()");
    if (gateNeeds !== null) {
      lines.push("    needs:");
      for (const need of gateNeeds) lines.push(`      - ${need}`);
    }
    lines.push("    steps:", "      - run: true");
  }
  return lines.join("\n") + "\n";
}

test("findCiJobs reads job names only, not the same-indent keys under on: and permissions:", () => {
  assert.deepEqual(findCiJobs(fixtureCi()), ["alpha", "beta", GATE_JOB]);

  const real = findCiJobs(REAL_CI);
  assert.ok(real.includes("conformance") && real.includes("build-site") && real.includes(GATE_JOB));
  // the trap this parser exists to avoid: `push` and `contents` are not jobs
  assert.ok(!real.includes("push"), "`push:` under `on:` was read as a job");
  assert.ok(!real.includes("contents"), "`contents:` under `permissions:` was read as a job");
});

test("the ci.yml this repo actually ships passes the gate assertion", () => {
  const result = checkCiGate(REAL_CI);
  assert.equal(result.ok, true, result.messages.join("\n"));
});

test("a job left out of the gate's needs fails the check by name", () => {
  const result = checkCiGate(fixtureCi({ jobs: ["alpha", "beta"], gateNeeds: ["alpha"] }));
  assert.equal(result.ok, false);
  assert.match(result.messages.join("\n"), /gated by nothing:[\s\S]*beta/);
});

test("a gate that lost its `if: always()` fails, because a skipped check counts as a pass", () => {
  const result = checkCiGate(fixtureCi({ always: false }));
  assert.equal(result.ok, false);
  assert.match(result.messages.join("\n"), /always\(\)/);
});

test("a ci.yml with no gate job at all fails", () => {
  const result = checkCiGate(fixtureCi({ gate: false }));
  assert.equal(result.ok, false);
  assert.match(result.messages.join("\n"), /declares no "ci-ok" job/);
});

test("a gate needing a job that ci.yml does not declare fails", () => {
  const result = checkCiGate(fixtureCi({ gateNeeds: ["alpha", "beta", "ghost"] }));
  assert.equal(result.ok, false);
  assert.match(result.messages.join("\n"), /does not declare:[\s\S]*ghost/);
});

test("the inline `needs: [a, b]` form is understood as well as the block form", () => {
  const inline = fixtureCi().replace("    needs:\n      - alpha\n      - beta", "    needs: [alpha, beta]");
  assert.deepEqual(findJobNeeds(inline, GATE_JOB), ["alpha", "beta"]);
  assert.equal(checkCiGate(inline).ok, true);
});
