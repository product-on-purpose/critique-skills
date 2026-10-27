#!/usr/bin/env node
// what-it-is:   the release tag-vs-manifest version guard
// what-it-does: reads scripts/lib/version-manifest.mjs's single enumeration of every version-bearing
//               file, reads each file's declared version, and fails if any of them disagrees with
//               the given tag
// why:          the family release pattern requires the pushed tag to equal every version-bearing
//               manifest before a GitHub Release is published (S-07 CI-pipeline spec, AC-4); reading
//               the enumeration from one shared module keeps this guard and any future version-bump
//               tool from drifting apart
// used-by:      .github/workflows/release.yml ("Guard - tag must equal every version-bearing
//               manifest" step)
//
// Usage:  node scripts/check-release-versions.mjs <tag-or-version>
// With no argument, falls back to the GITHUB_REF_NAME environment variable (what release.yml sets
// from the pushed tag). A leading "v" is stripped either way, so "v0.1.0" and "0.1.0" are equivalent.
//
// To run locally against the tag you are about to push:
//   node scripts/check-release-versions.mjs v0.1.0
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { VERSION_MANIFESTS, readEntryVersions } from "./lib/version-manifest.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");

const rawTag = process.argv[2] ?? process.env.GITHUB_REF_NAME;
if (!rawTag) {
  console.error(
    "usage: node scripts/check-release-versions.mjs <tag-or-version>\n" +
      "  (or set GITHUB_REF_NAME, which release.yml does from the pushed tag)",
  );
  process.exit(2);
}
const expected = rawTag.startsWith("v") ? rawTag.slice(1) : rawTag;

let fail = false;
for (const entry of VERSION_MANIFESTS) {
  let versions;
  try {
    versions = readEntryVersions(entry, ROOT);
  } catch (e) {
    console.error(`error: ${entry.file}: ${e.message}`);
    fail = true;
    continue;
  }
  if (versions.length > 1) {
    console.error(`error: ${entry.file} pins disagree with each other: ${versions.join(", ")}`);
    fail = true;
    continue;
  }
  const actual = versions[0];
  if (actual !== expected) {
    console.error(`error: ${entry.file} version "${actual}" does not match tag "${expected}"`);
    fail = true;
  } else {
    console.log(`ok: ${entry.file} = ${actual}`);
  }
}

if (fail) {
  console.error("version guard failed: tag/version mismatch; aborting before publishing a release");
  process.exit(1);
}
console.log(`version guard passed: every version-bearing manifest agrees with tag v${expected}`);
