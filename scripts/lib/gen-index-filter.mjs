// what-it-is:   the INDEX.md phantom-row filter
// what-it-does: post-processes rendered INDEX.md text, dropping any bullet-list row (or, within a
//               multi-link row, any individual "; "-joined segment) whose linked path does not
//               exist on disk
// why:          the toolkit's gen-index generator renders its "## Manifests" and "##
//               Documentation and governance" sections as fixed boilerplate written for the
//               toolkit's own repo layout (STANDARD.md, .codex-plugin/, manifest.generated.json,
//               docs/internal/backlog/, docs/internal/STATUS.md, agents/_chain-permitted.yaml,
//               templates/) rather than deriving them from ctx, so those sections can list paths
//               that do not exist in a consuming repo. This repo's central claim is that nothing
//               is asserted without evidence; INDEX.md must not be the exception. Kept in its own
//               module, separate from scripts/gen-index.mjs's toolkit-spawning wrapper, so it has
//               no dependency on a local agent-skills-toolkit checkout and can be unit-tested
//               (and imported) without one.
// used-by:      scripts/gen-index.mjs (both --check and the writer path);
//               scripts/tests/gen-index.filter.test.mjs
import { existsSync } from "node:fs";
import { resolve } from "node:path";

// A markdown link of the generator's own shape: [`label`](target). Reused to both detect a link
// inside a bullet and to pull its target back out.
const LINK_RE = /\[`[^`]+`\]\(([^)]+)\)/;
// Splits a bullet's body into one segment per link, only at a "; " that is immediately followed
// by the start of the next link. This is deliberately narrower than splitting on every "; ": some
// single-link rows carry a "; " inside trailing prose (e.g. "(generated; do not hand-edit)"), and
// that "; " is never followed by "[`", so it is left alone and the row is treated as one segment.
const SEGMENT_SPLIT_RE = /;\s+(?=\[`)/;

/**
 * Drop any bullet-list row (or, within a multi-link row, any individual "; "-joined segment)
 * whose linked path does not exist on disk, resolved relative to `root`. Handles both file and
 * directory targets (existsSync works on either; a trailing "/" on a directory link is fine) and
 * rows that carry more than one link-plus-prose clause, so a partially-valid row keeps its valid
 * clauses instead of being dropped wholesale. Pure function of (text, root): same inputs always
 * produce the same output, so running the generator twice is idempotent and --check stays
 * meaningful. Lines with no link (headings, prose, "- none yet") pass through untouched.
 */
export function dropPhantomRows(text, root) {
  const lines = text.split("\n");
  const kept = [];
  for (const line of lines) {
    if (!line.startsWith("- ") || !LINK_RE.test(line)) {
      kept.push(line);
      continue;
    }
    const body = line.slice(2);
    const segments = body.split(SEGMENT_SPLIT_RE);
    const survivors = segments.filter((seg) => {
      const m = seg.match(LINK_RE);
      if (!m) return true; // no link in this segment: nothing to verify, keep it
      return existsSync(resolve(root, m[1]));
    });
    if (survivors.length === 0) continue; // every link in the row was phantom: drop the row
    let rebuilt = "- " + survivors.join("; ");
    if (survivors.length < segments.length && !/[.!?]$/.test(rebuilt)) rebuilt += ".";
    kept.push(rebuilt);
  }
  return kept.join("\n");
}
