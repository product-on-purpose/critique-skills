#!/usr/bin/env node
// what-it-is:   the RELEASE-NOTES.md section extractor
// what-it-does: reads RELEASE-NOTES.md, pulls out the "## <version>" section for the given version,
//               and writes it to a release-body file; exits nonzero with a clear message when that
//               section is missing or empty
// why:          CI workflows must contain no logic that computes a verdict (S-07 CI-pipeline spec,
//               AC-2); extraction and the missing/empty guard both belong in a script so the release
//               job is a single command and any failure reproduces locally with that same command
// used-by:      .github/workflows/release.yml ("Extract this version's RELEASE-NOTES section" step)
//
// Usage:  node scripts/extract-release-notes.mjs <tag-or-version> [output-file]
// With no argument, falls back to the GITHUB_REF_NAME environment variable (what release.yml sets
// from the pushed tag). A leading "v" is stripped either way, so "v0.1.0" and "0.1.0" are equivalent.
// output-file defaults to RELEASE_BODY.md at the repo root.
//
// To run locally against the tag you are about to push:
//   node scripts/extract-release-notes.mjs v0.1.0
import { readFileSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");

const rawTag = process.argv[2] ?? process.env.GITHUB_REF_NAME;
if (!rawTag) {
  console.error(
    "usage: node scripts/extract-release-notes.mjs <tag-or-version> [output-file]\n" +
      "  (or set GITHUB_REF_NAME, which release.yml does from the pushed tag)",
  );
  process.exit(2);
}
const version = rawTag.startsWith("v") ? rawTag.slice(1) : rawTag;
const outputPath = resolve(ROOT, process.argv[3] ?? "RELEASE_BODY.md");

const notesPath = resolve(ROOT, "RELEASE-NOTES.md");
const notes = readFileSync(notesPath, "utf8").split("\n");

const heading = `## ${version}`;
const nextHeadingRe = /^## \d+\.\d+\.\d+/;

const extracted = [];
let inSection = false;
for (const line of notes) {
  if (line === heading || line.startsWith(`${heading} `)) {
    inSection = true;
    extracted.push(line);
    continue;
  }
  if (inSection && nextHeadingRe.test(line)) {
    inSection = false;
  }
  if (inSection) {
    extracted.push(line);
  }
}

const body = extracted.join("\n").trim();

if (body === "") {
  console.error(
    `::error::no RELEASE-NOTES.md section for ${version}; add a '## ${version}' heading before ` +
      "tagging (refusing to publish the whole changelog as the release body)",
  );
  process.exit(1);
}

writeFileSync(outputPath, `${body}\n`, "utf8");
console.log(`ok: wrote ${extracted.length} line(s) for ${version} to ${outputPath}`);
