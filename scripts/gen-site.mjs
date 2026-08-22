#!/usr/bin/env node
// what-it-is:   the Astro Starlight site content generator
// what-it-does: reads the publishable half of the repo-root docs/ tree (the four Diataxis
//               quadrants) and writes a Starlight-shaped copy into site/src/content/docs/,
//               emitting explicit frontmatter and rewriting every markdown link at generation
//               time so no relative .md link ever reaches the build
// why:          Pattern S (family Astro site standard 14.1) mounts site/src/content/docs/ with
//               the stock docsLoader(); a custom loader over docs/ is prohibited, so the docs
//               have to be transformed into that tree. Rewriting links here rather than in a
//               remark plugin is site plan decision 2.3: pm-skills needs a 178-line
//               remark-resolve-links plugin only because its generators emit relative .md links
//               in the first place, and that plugin sits on a deprecated config key whose
//               migration risks silently dropping every mermaid diagram. A generator that never
//               emits a relative link needs none of it
// used-by:      site/astro.config.mjs (calls generate() at config load, so every entrypoint -
//               astro build, dev, sync, check - regenerates), `npm run gen` inside site/, and
//               scripts/check-generated-untracked.mjs
//
// Scope: W2 of the site plan. This emits the four Diataxis quadrants only. Skill pages (W3),
// the receipts explorer (W4), and the narrative wings (W5) extend SOURCE_ROUTES and add their
// own emit functions; nothing else about this file needs to change for them.
//
// The site landing page is deliberately NOT generated from README.md (route map 5.1): a repo
// README answers "what is this repo" and a docs landing page answers "what can I do here", and
// generating one from the other guarantees whichever is secondary reads badly. index.mdx is
// hand-authored and tracked. Do not "fix" that duplication by generating it.
//
// Zero dependency, Node ESM. UTF-8 in and out, explicitly: this repo is developed on Windows
// and cp1252 would corrupt the emitted tree.
import {
  readFileSync,
  writeFileSync,
  mkdirSync,
  rmSync,
  existsSync,
  readdirSync,
} from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, resolve, join } from "node:path";
import { BASE } from "./site-base.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, ".."); // this repo's root, cwd-independent
const DOCS_SRC = join(ROOT, "docs");
const DOCS_OUT = join(ROOT, "site", "src", "content", "docs");

const GH = "https://github.com/product-on-purpose/critique-skills";
const GH_BLOB = `${GH}/blob/main`;
const GH_TREE = `${GH}/tree/main`;
// Generated pages set editUrl explicitly to their real editable source. Starlight's
// auto-derivation would resolve to the gitignored generated path and 404; verify-edit-links.mjs
// (W6) is what enforces this. Aggregate pages with no single source (the criteria explorer, the
// receipts explorer) will set `editUrl: false` when W3 and W4 add them.
const GH_EDIT = `${GH}/edit/main`;

/**
 * The four Diataxis quadrants under docs/ that publish, in reader order.
 * docs/internal/ is absent by design and is never routed (standard 14.1): the 31 ADRs, the
 * execution reports, and the release-plan tree stay on GitHub and are linked as blob URLs.
 */
export const QUADRANTS = ["tutorials", "how-to", "reference", "explanation"];

/**
 * Route slugs that deliberately differ from the source filename. Keyed by repo-relative path.
 * Route map 2.6 drops the leading article so the URL reads as a noun.
 */
export const SLUG_OVERRIDES = {
  "docs/explanation/the-benchmark-harness.md": "benchmark-harness",
};

// --- path helpers -----------------------------------------------------------

/** Read a file as UTF-8, or "" if it does not exist. */
function readUtf8(path) {
  return existsSync(path) ? readFileSync(path, "utf8") : "";
}

/** Write a file as UTF-8, creating parent directories first. */
function writeUtf8(path, content) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, content, "utf8");
}

/**
 * Remove and recreate a directory this generator owns.
 * Only ever called on the quadrant directories listed in QUADRANTS. The hand-authored,
 * tracked pages beside them (index.mdx, skills/index.md) are never touched.
 */
function freshDir(dir) {
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
}

/** Sorted list of *.md filenames directly inside dir. */
function listMarkdown(dir) {
  if (!existsSync(dir)) return [];
  return readdirSync(dir, { withFileTypes: true })
    .filter((e) => e.isFile() && e.name.endsWith(".md"))
    .map((e) => e.name)
    .sort();
}

/**
 * Normalize a POSIX-style relative path, resolving "." and "..".
 * Returns null when the path escapes above its starting point, which for a repo-relative path
 * means it escapes the repo and cannot be resolved to either a route or a GitHub URL.
 * @param {string} p
 * @returns {string|null}
 */
export function normalizePosix(p) {
  const out = [];
  for (const part of p.split("/")) {
    if (part === "" || part === ".") continue;
    if (part === "..") {
      if (out.length === 0) return null;
      out.pop();
      continue;
    }
    out.push(part);
  }
  return out.join("/");
}

// --- frontmatter ------------------------------------------------------------

/**
 * Split YAML frontmatter from a markdown body.
 * Deliberately not a general YAML parser: every source under docs/ uses flat "key: value"
 * scalars, and the generator reads exactly two of them (title, description). Block scalars,
 * nested keys, and multi-line folded values are not supported and are not used.
 * @param {string} content
 * @returns {{meta: Record<string,string>, body: string}}
 */
export function parseFrontmatter(content) {
  const text = content.replace(/^﻿/, "");
  const m = text.match(/^---\s*\r?\n([\s\S]*?)\r?\n---\s*\r?\n?([\s\S]*)$/);
  if (!m) return { meta: {}, body: text };
  const meta = {};
  for (const line of m[1].split(/\r?\n/)) {
    const kv = line.match(/^([\w-]+):\s*(.*)$/);
    if (!kv) continue;
    meta[kv[1]] = kv[2].trim().replace(/^["']/, "").replace(/["']$/, "").trim();
  }
  return { meta, body: m[2] };
}

/**
 * Drop a leading H1 from a body.
 * Starlight renders the frontmatter `title` as the page H1, and every source doc opens with an
 * H1 that repeats its own title. Without this every generated page shows the heading twice.
 * @param {string} body
 * @returns {string}
 */
export function stripLeadingH1(body) {
  return body.replace(/^\s*#\s+[^\n]*\r?\n+/, "");
}

/** Quote a string as a YAML double-quoted scalar. Safe for any title or description here. */
export function yamlString(value) {
  return `"${String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

/**
 * Emit the frontmatter block for a generated page.
 * `editUrl` is always explicit, never auto-derived: pass a URL, or `false` for an aggregate page
 * that has no single editable source.
 * @param {{title: string, description?: string, editUrl: string|false, extra?: string[]}} fields
 */
export function emitFrontmatter({ title, description, editUrl, extra = [] }) {
  const lines = ["---", `title: ${yamlString(title)}`];
  if (description) lines.push(`description: ${yamlString(description)}`);
  lines.push(`editUrl: ${editUrl === false ? "false" : yamlString(editUrl)}`);
  lines.push(...extra, "---");
  return lines.join("\n");
}

// --- routes -----------------------------------------------------------------

/**
 * The site route for a publishable repo-relative source path.
 * A quadrant's README.md is that quadrant's index (docs/how-to/README.md -> /how-to/), which is
 * why the route map lists /how-to/ and /explanation/ as generated rather than hand-authored.
 * @param {string} repoPath - e.g. "docs/how-to/gate-in-ci.md"
 * @returns {string} e.g. "/how-to/gate-in-ci/"
 */
export function routeFor(repoPath) {
  const parts = repoPath.split("/");
  const quadrant = parts[1];
  const file = parts[parts.length - 1];
  if (file === "README.md") return `/${quadrant}/`;
  const slug = SLUG_OVERRIDES[repoPath] ?? file.replace(/\.md$/, "");
  return `/${quadrant}/${slug}/`;
}

/**
 * The content-tree path a route is served from, relative to site/src/content/docs.
 * The inverse of routeFor(): "/how-to/" -> "/how-to/index.md", "/how-to/gate-in-ci/" ->
 * "/how-to/gate-in-ci.md". Keeping this a function of the route rather than of the source
 * filename is what makes a slug override safe.
 * @param {string} route
 * @returns {string}
 */
export function outputPathFor(route) {
  const segments = route.split("/").filter(Boolean);
  // A single-segment route is a section index, and it must be <section>/index.md rather than
  // <section>.md: `autogenerate: { directory }` in the sidebar reads the directory, and a
  // sibling file would leave the section without its own overview page.
  if (segments.length === 1) return `/${segments[0]}/index.md`;
  const file = `${segments[segments.length - 1]}.md`;
  return `/${segments.slice(0, -1).join("/")}/${file}`;
}

/**
 * Discover every page this generator emits, as repo-relative source path -> site route.
 *
 * This is the generator's whole model of "what exists as a page". The link resolver consults it
 * and nothing else: a target in the map becomes a site route, a target anywhere else in the repo
 * becomes a GitHub URL. That is what keeps the emitted tree free of links to routes that do not
 * exist yet. W3, W4, and W5 add their sources here and the prose links to them flip on the next
 * regeneration with no edit to any document.
 * @returns {Map<string,string>}
 */
export function buildRouteMap() {
  const routes = new Map();
  for (const quadrant of QUADRANTS) {
    for (const file of listMarkdown(join(DOCS_SRC, quadrant))) {
      const repoPath = `docs/${quadrant}/${file}`;
      routes.set(repoPath, routeFor(repoPath));
    }
  }
  return routes;
}

// --- link rewriting ---------------------------------------------------------

/**
 * Resolve one markdown link target as seen from a source file's directory.
 *
 * Four outcomes, in order:
 *   1. external, mailto, protocol-relative, or a bare fragment -> returned unchanged
 *   2. a repo file this generator publishes -> base-absolute site route, fragment preserved
 *   3. any other path inside the repo -> absolute GitHub blob (or tree, for a directory) URL,
 *      which the rendered-link guard skips by design
 *   4. a path that escapes the repo root -> returned unchanged, and reported by the caller
 *
 * @param {string} href - the raw link target
 * @param {string} fromDir - repo-relative directory of the file containing the link
 * @param {Map<string,string>} routes - from buildRouteMap()
 * @returns {{href: string, kind: "external"|"route"|"github"|"unresolved"}}
 */
export function resolveLink(href, fromDir, routes) {
  const raw = href.trim();
  if (raw === "" || /^[a-z][a-z0-9+.-]*:/i.test(raw) || raw.startsWith("//") || raw.startsWith("#")) {
    return { href, kind: "external" };
  }

  const hashAt = raw.indexOf("#");
  const fragment = hashAt === -1 ? "" : raw.slice(hashAt);
  const pathPart = hashAt === -1 ? raw : raw.slice(0, hashAt);
  if (pathPart === "") return { href, kind: "external" };

  const isDir = pathPart.endsWith("/");
  const repoPath = normalizePosix(`${fromDir}/${pathPart}`);
  if (repoPath === null) return { href, kind: "unresolved" };

  const route = routes.get(repoPath);
  if (route) return { href: `${BASE}${route}${fragment}`, kind: "route" };

  const prefix = isDir ? GH_TREE : GH_BLOB;
  return { href: `${prefix}/${repoPath}${isDir ? "/" : ""}${fragment}`, kind: "github" };
}

/**
 * Rewrite every markdown link in a body, leaving fenced code blocks alone.
 *
 * Fence awareness matters because a doc that demonstrates a link in a code sample must keep the
 * literal text it is demonstrating. No publishable doc does that today; docs/internal/ does, and
 * a future doc easily could.
 *
 * @param {string} body
 * @param {string} fromDir - repo-relative directory of the source file
 * @param {Map<string,string>} routes
 * @returns {{body: string, unresolved: string[]}}
 */
export function rewriteLinks(body, fromDir, routes) {
  const unresolved = [];
  const rewrite = (href) => {
    const result = resolveLink(href, fromDir, routes);
    if (result.kind === "unresolved") unresolved.push(href);
    return result.href;
  };

  let inFence = false;
  let fenceMarker = "";
  const out = body.split("\n").map((line) => {
    const fence = line.match(/^\s*(`{3,}|~{3,})/);
    if (fence) {
      if (!inFence) {
        inFence = true;
        fenceMarker = fence[1][0];
      } else if (fence[1][0] === fenceMarker) {
        inFence = false;
      }
      return line;
    }
    if (inFence) return line;

    // Inline and image links: [text](target) and [text](target "title").
    let rewritten = line.replace(/\]\(([^)\s]+)((?:\s+"[^"]*")?)\)/g, (_m, target, title) => {
      return `](${rewrite(target)}${title})`;
    });
    // Reference-style definitions: [id]: target
    rewritten = rewritten.replace(/^(\s*\[[^\]]+\]:\s*)(\S+)/, (_m, head, target) => {
      return `${head}${rewrite(target)}`;
    });
    return rewritten;
  });

  return { body: out.join("\n"), unresolved };
}

// --- emit -------------------------------------------------------------------

/**
 * Transform one source doc into its generated page.
 * @param {string} repoPath - repo-relative source path
 * @param {Map<string,string>} routes
 * @returns {{outPath: string, repoOut: string, unresolved: string[]}}
 */
function generatePage(repoPath, routes) {
  const { meta, body } = parseFrontmatter(readUtf8(join(ROOT, repoPath)));
  const fromDir = repoPath.split("/").slice(0, -1).join("/");
  const { body: linked, unresolved } = rewriteLinks(stripLeadingH1(body), fromDir, routes);

  // The output filename is derived from the route, never from the source filename, so a slug
  // override cannot move the route while leaving the file where it was: that combination emits
  // links to a page that does not exist and is invisible until something crawls the built dist.
  const file = repoPath.split("/").pop();
  const repoOut = `site/src/content/docs${outputPathFor(routes.get(repoPath))}`;

  const frontmatter = emitFrontmatter({
    title: meta.title || file.replace(/\.md$/, ""),
    description: meta.description,
    editUrl: `${GH_EDIT}/${repoPath}`,
  });
  const banner = `<!-- Generated by scripts/gen-site.mjs from ${repoPath}. Do not edit: this file is gitignored and rewritten on every build. -->`;

  writeUtf8(join(ROOT, repoOut), `${frontmatter}\n\n${banner}\n\n${linked.trim()}\n`);
  return { repoOut, unresolved };
}

/**
 * Generate the site content tree.
 *
 * Idempotent, and quiet enough to run on every astro entrypoint: one summary line. Returns the
 * emitted files so check-generated-untracked.mjs can assert on the real list rather than on a
 * static copy of it that could drift.
 *
 * @param {{quiet?: boolean}} [options]
 * @returns {{files: string[], routes: Map<string,string>}}
 */
export function generate({ quiet = false } = {}) {
  if (!existsSync(DOCS_SRC)) {
    throw new Error(`gen-site: docs directory not found at ${DOCS_SRC}`);
  }

  const routes = buildRouteMap();
  const files = [];
  const unresolved = [];

  for (const quadrant of QUADRANTS) {
    freshDir(join(DOCS_OUT, quadrant));
  }
  for (const repoPath of routes.keys()) {
    const result = generatePage(repoPath, routes);
    files.push(result.repoOut);
    for (const href of result.unresolved) unresolved.push(`${repoPath}: ${href}`);
  }

  if (unresolved.length > 0) {
    // Left unchanged in the output rather than guessed at, so the W6 rendered-link guard fails
    // on it loudly instead of the generator inventing a URL that resolves to nothing.
    console.warn(
      `gen-site: ${unresolved.length} link(s) escape the repo root and were left as-is:\n  ` +
        unresolved.join("\n  "),
    );
  }
  if (!quiet) {
    console.log(`gen-site: ${files.length} pages across ${QUADRANTS.length} quadrants -> ${DOCS_OUT}`);
  }
  return { files, routes };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) generate();
