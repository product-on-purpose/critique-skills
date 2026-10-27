// what-it-is:   the single enumeration of every version-bearing file in this repo
// what-it-does: lists each file that carries this plugin's semantic version, and how to read that
//               version back out of it: a dotted JSON path (`pointer`, for a JSON file) or a
//               regular expression with one capturing group (`pattern`, for a prose file that pins
//               the version inline instead of storing it as a field). `readEntryVersions()` is the
//               one place that interprets either shape, so the release guard and this file's own
//               tests read a `pattern` entry exactly the same way.
// why:          the release tag guard and any future version-bump tool must read from exactly one
//               list, or the two drift apart (S-07 CI-pipeline spec, deliverable 4: "a single
//               enumeration consumed by both the release guard and future bump tooling"). PR 102
//               (the E53 gate recipe) shipped two prose pins of the plugin version
//               (docs/how-to/gate-in-ci.md, examples/recipes/gate-in-ci.md) that this enumeration
//               did not cover, so a release could leave them stale with the guard reporting green.
// used-by:      scripts/check-release-versions.mjs (the release guard); future version-bump tooling
//
// contract/critique-contract.schema.json's contract_version is deliberately NOT listed here: it is
// versioned independently of the plugin (contract/README.md "Versioning and extension", ADR 0013),
// and release version-bump tooling must never touch it. .codex-plugin/plugin.json is not listed
// either, because this plugin does not ship a Codex native manifest at Universal tier (see
// scripts/gen-plugin-manifest.mjs); add it here the day that manifest is generated.
//
// examples/recipes/gate-in-ci.md's "skill_version": "0.1.1" and "contract_version": "1.0.0" lines
// are also deliberately NOT guarded: the first is a critique-accessibility skill version, not the
// plugin version, and the second is the same independently-versioned contract excluded above.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export const VERSION_MANIFESTS = [
  { file: "package.json", pointer: "version" },
  { file: "library.json", pointer: "version" },
  { file: ".claude-plugin/plugin.json", pointer: "version" },
  // Each file pins this plugin's version two ways: the "pins `v0.2.0`" sentence (prose only, in
  // docs/how-to/gate-in-ci.md) and the `ref: v0.2.0` critique-skills checkout step (both files).
  // The pattern is deliberately narrow to "ref: v" or "pins `v" so it never matches the pinned
  // actions/checkout SHAs' own "# v7.0.1"-style version comments a few lines away.
  { file: "docs/how-to/gate-in-ci.md", pattern: "(?:ref: v|pins `v)(\\d+\\.\\d+\\.\\d+)" },
  { file: "examples/recipes/gate-in-ci.md", pattern: "(?:ref: v|pins `v)(\\d+\\.\\d+\\.\\d+)" },
];

/**
 * Reads the version(s) one manifest entry's real file declares.
 *
 * A `pointer` entry reads one JSON file and returns the single string at that dotted path, as an
 * array of one, so callers have one return shape regardless of entry kind.
 *
 * A `pattern` entry reads one prose file as text and returns every distinct version matched by
 * the pattern (a one-capturing-group RegExp applied globally). A file that pins the same version
 * twice reads back as one version; a file whose two pins disagree reads back as more than one, so
 * the caller can report that disagreement instead of silently picking one of them.
 *
 * Throws if the file cannot be read, a JSON pointer does not resolve to a string, or a pattern
 * matches nothing.
 *
 * @param {{file: string, pointer?: string, pattern?: string}} entry
 * @param {string} repoRoot
 * @returns {string[]}
 */
export function readEntryVersions(entry, repoRoot) {
  const abs = resolve(repoRoot, entry.file);
  if (entry.pointer) {
    const data = JSON.parse(readFileSync(abs, "utf8"));
    const value = entry.pointer
      .split(".")
      .reduce((node, key) => (node == null ? node : node[key]), data);
    if (typeof value !== "string") {
      throw new Error(`${entry.pointer} did not resolve to a string`);
    }
    return [value];
  }
  const text = readFileSync(abs, "utf8");
  const re = new RegExp(entry.pattern, "g");
  const found = [...text.matchAll(re)].map((m) => m[1]);
  if (found.length === 0) {
    throw new Error(`pattern ${entry.pattern} matched nothing`);
  }
  return [...new Set(found)];
}
