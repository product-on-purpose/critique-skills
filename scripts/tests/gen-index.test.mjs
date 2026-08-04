// what-it-is:   unit tests for the INDEX.md generator wrapper's --check mode
// what-it-does: (1) an unconditional test that gen-index.mjs fails loudly (exit 2, clear stderr)
//               when agent-skills-toolkit cannot be resolved, run from an isolated fixture copy so
//               it never depends on this machine's checkout state; (2) a smoke test, skipped when
//               no toolkit is resolvable in this environment, that the real script's --check exit
//               code agrees with what its own exported checkIndexDrift() reports for the real repo
// why:          gen-index.mjs resolves the toolkit and can process.exit() unconditionally at
//               module load, so it must always be exercised as a child process, never imported
//               directly into the test runner (see helpers/proc.mjs); the unit-node CI job does not
//               check out the toolkit, so the toolkit-required path is skipped there rather than
//               asserted, the same vacuous-but-honest-and-visible pattern this repo's own
//               scripts/gen-plugin-manifest.mjs already uses for checks with nothing to verify yet
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
import { test } from "node:test";
import assert from "node:assert/strict";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { runNode } from "./helpers/proc.mjs";
import { tempDir, copyInto, copyDirInto } from "./helpers/tmp.mjs";
import { resolveToolkit } from "../lib/resolve-toolkit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..", "..");
const SRC_GEN_INDEX = resolve(REPO_ROOT, "scripts", "gen-index.mjs");
const SRC_LIB_DIR = resolve(REPO_ROOT, "scripts", "lib");

const toolkitAvailable = Boolean(resolveToolkit(REPO_ROOT));

test("gen-index --check fails with a clear message when the toolkit cannot be resolved", (t) => {
  // An isolated temp dir has no sibling agent-skills-toolkit and is not the real repo, so
  // resolveToolkit() finds nothing regardless of this machine's own checkout state.
  const root = tempDir(t, "gen-index-no-toolkit-");
  const scriptPath = resolve(root, "scripts", "gen-index.mjs");
  copyInto(scriptPath, SRC_GEN_INDEX);
  copyDirInto(resolve(root, "scripts", "lib"), SRC_LIB_DIR);

  const { status, stderr } = runNode(scriptPath, ["--check"], {
    cwd: root,
    env: { ...process.env, AGENT_SKILLS_TOOLKIT: "" },
  });

  assert.equal(status, 2);
  assert.match(stderr, /agent-skills-toolkit \(the generator\) not found/);
});

test(
  "smoke: the real script's --check exit code agrees with checkIndexDrift()'s own verdict",
  { skip: toolkitAvailable ? false : "agent-skills-toolkit is not resolvable in this environment" },
  () => {
    const { status, stdout } = runNode(resolve(REPO_ROOT, "scripts", "gen-index.mjs"), ["--check"], {
      cwd: REPO_ROOT,
    });

    assert.ok(status === 0 || status === 1, `expected exit 0 or 1, got ${status}`);
    const claimsClean = /INDEX\.md matches library\.json/.test(stdout);
    const claimsDrift = /INDEX\.md is out of date/.test(stdout);
    assert.ok(claimsClean || claimsDrift, `--check produced neither a clean nor a drift message:\n${stdout}`);
    // exit code and the message it printed must not contradict each other
    assert.equal(status === 0, claimsClean);
    assert.equal(status === 1, claimsDrift);
  },
);
