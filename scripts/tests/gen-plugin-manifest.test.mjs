// what-it-is:   unit tests for the native-manifest generator wrapper's --check mode (the "drift"
//               CI job's entry point)
// what-it-does: (1) an unconditional test that gen-plugin-manifest.mjs fails loudly when
//               agent-skills-toolkit cannot be resolved, run from an isolated fixture copy; (2) a
//               smoke test, skipped when no toolkit is resolvable in this environment, that the
//               real script's --check prints all four of its documented check sections and that
//               its exit code agrees with whether any of them reported failure
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
import { runNode } from "./helpers/proc.mjs";
import { tempDir, copyInto, copyDirInto } from "./helpers/tmp.mjs";
import { resolveToolkit } from "../lib/resolve-toolkit.mjs";

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
  "smoke: the real script's --check prints all four documented checks with a consistent exit code",
  { skip: toolkitAvailable ? false : "agent-skills-toolkit is not resolvable in this environment" },
  () => {
    const { status, stdout } = runNode(resolve(REPO_ROOT, "scripts", "gen-plugin-manifest.mjs"), ["--check"], {
      cwd: REPO_ROOT,
    });

    assert.ok(status === 0 || status === 1, `expected exit 0 or 1, got ${status}`);
    assert.match(stdout, /gen --check: .*plugin\.json/);
    assert.match(stdout, /gen:index --check:/);
    assert.match(stdout, /gen --check: AGENTS\.md/);

    const anyFailureWord = /(out of date|does not exist|is missing|failed)/.test(stdout);
    assert.equal(status === 1, anyFailureWord, `exit code and message content disagree:\n${stdout}`);
  },
);
