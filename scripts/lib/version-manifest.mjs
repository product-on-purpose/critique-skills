// what-it-is:   the single enumeration of every version-bearing file in this repo
// what-it-does: lists each file that carries this plugin's semantic version, and the dotted JSON
//               path to read it from
// why:          the release tag guard and any future version-bump tool must read from exactly one
//               list, or the two drift apart (S-07 CI-pipeline spec, deliverable 4: "a single
//               enumeration consumed by both the release guard and future bump tooling")
// used-by:      scripts/check-release-versions.mjs (the release guard); future version-bump tooling
//
// contract/critique-contract.schema.json's contract_version is deliberately NOT listed here: it is
// versioned independently of the plugin (contract/README.md "Versioning and extension", ADR 0013),
// and release version-bump tooling must never touch it. .codex-plugin/plugin.json is not listed
// either, because this plugin does not ship a Codex native manifest at Universal tier (see
// scripts/gen-plugin-manifest.mjs); add it here the day that manifest is generated.
export const VERSION_MANIFESTS = [
  { file: "package.json", pointer: "version" },
  { file: "library.json", pointer: "version" },
  { file: ".claude-plugin/plugin.json", pointer: "version" },
];
