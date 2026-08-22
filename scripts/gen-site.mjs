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
// Scope: W2 and W3 of the site plan. This emits the four Diataxis quadrants, one page per
// shipped skill, the criteria explorer, and the critic subagent page. The receipts explorer (W4)
// and the narrative wings (W5) add sources to the route map and their own emit functions;
// nothing else about this file needs to change for them.
//
// The skill list comes from library.json's active components, never from what happens to be on
// disk under skills/. A skill held out of a release is absent from the active set, and the site
// must reflect that honestly rather than publish a page for it. This matches
// gen-readme-catalog.mjs, deliberately: two generators disagreeing about which skills ship is a
// worse failure than either one being wrong alone.
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

/**
 * Publishable sources that do not live under docs/, as repo-relative path to site route.
 * The six skill pages are not listed here: they are discovered from library.json so the site
 * cannot publish a page for a skill the plugin does not ship.
 */
export const EXTRA_ROUTES = {
  "agents/critique-critic.md": "/reference/critic-subagent/",
};

/**
 * The criteria explorer's route. It has no single source file: it is an aggregate of all six
 * SKILL.md frontmatters, which is also why its page sets `editUrl: false`. Nothing resolves a
 * link *to* a source path for it, so it is deliberately absent from the route map and the
 * generator writes links to it from this constant.
 */
export const CRITERIA_ROUTE = "/reference/criteria/";

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

/** Parse a JSON file as UTF-8. Throws with the path named if it is missing or malformed. */
function readJson(path) {
  if (!existsSync(path)) throw new Error(`gen-site: required file not found: ${path}`);
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (cause) {
    throw new Error(`gen-site: ${path} is not valid JSON: ${cause.message}`);
  }
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

/**
 * Remove the generated skill pages, and only those.
 *
 * The skills output directory is NOT freshDir'd, because it holds the hand-authored, tracked
 * `index.md` that sits beside the generated pages, and freshDir would delete it on every astro
 * invocation. The `critique-*.md` shape is the same one `.gitignore` uses to decide what this
 * generator owns in that directory, which keeps one definition of ownership rather than two.
 */
function removeGeneratedSkillPages() {
  const dir = join(DOCS_OUT, "skills");
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
    return;
  }
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isFile() && /^critique-.*\.md$/.test(entry.name)) {
      rmSync(join(dir, entry.name), { force: true });
    }
  }
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

// --- SKILL.md ---------------------------------------------------------------

/**
 * The criterion-ID grammar, read from the frozen contract schema at generation time.
 *
 * Not re-typed here on purpose. A hand-copied pattern is how a generator silently drops criteria:
 * an earlier draft of this work used `[A-Z][A-Z0-9-]*` and lost all 22 dotted WCAG IDs
 * (`WCAG-1.4.11`) without a word of complaint, turning 96 criteria into 74. Reading the schema
 * means the generator cannot disagree with the contract about what a criterion ID is.
 * `contract/critique-contract.schema.json` is frozen, so this coupling is stable.
 * @returns {RegExp}
 */
export function criterionPattern() {
  const schema = readJson(join(ROOT, "contract", "critique-contract.schema.json"));
  const pattern = schema?.$defs?.criterionId?.pattern;
  if (typeof pattern !== "string") {
    throw new Error(
      "gen-site: contract/critique-contract.schema.json has no $defs/criterionId/pattern. " +
        "The criterion-ID grammar moved; find it and update criterionPattern(), do not re-type it here.",
    );
  }
  return new RegExp(pattern);
}

/**
 * Parse the parts of a SKILL.md frontmatter this generator publishes.
 *
 * Deliberately shape-specific rather than a YAML parser. SKILL.md frontmatter nests two levels
 * deep in two different ways (`rubric_sources` is a list of objects, `checks.scripted` and
 * `checks.judged` are block lists under a mapping), which the docs-side parseFrontmatter() states
 * in its own comment that it does not handle. A parser that understands exactly this shape and
 * throws on anything else is the house pattern, and it fails loudly where a general parser would
 * quietly return a partial object.
 *
 * @param {string} content - the full SKILL.md text
 * @param {string} sourcePath - repo-relative path, used only in error messages
 * @returns {{name: string, description: string, version: string, license: string,
 *            rubricSources: Array<{id: string, citation: string, url: string, accessed: string,
 *            operationalization: string}>, scripted: string[], judged: string[], body: string}}
 */
export function parseSkill(content, sourcePath) {
  const m = content.replace(/^﻿/, "").match(/^---\s*\r?\n([\s\S]*?)\r?\n---\s*\r?\n([\s\S]*)$/);
  if (!m) throw new Error(`gen-site: ${sourcePath} has no frontmatter block.`);
  const [, fm, body] = m;

  const scalar = (key) => {
    const hit = fm.match(new RegExp(`^${key}:\\s*(.+)$`, "m"));
    if (!hit) throw new Error(`gen-site: ${sourcePath} frontmatter has no ${key}.`);
    return hit[1].trim().replace(/^"/, "").replace(/"$/, "").trim();
  };

  // Read the required scalars before anything nested, so a SKILL.md missing its description
  // reports that rather than reporting whichever deeper structure happened to be checked first.
  const name = scalar("name");
  const description = scalar("description");
  const version = scalar("version");
  const license = scalar("license");

  // rubric_sources: a list of objects, walked line by line for the same reason the lanes are.
  // The slice-on-a-stop-regex version of this read `chunk.search(/^\S/m)` to find where a source
  // block ended, which returns 0 every time: in multiline mode position 0 IS a line start, so
  // every block was sliced to the empty string and every rubric row rendered blank. Both bugs in
  // this parser were a stop condition matching immediately. Walking lines has no stop condition.
  const unquote = (value) => value.trim().replace(/^"/, "").replace(/"$/, "").trim();
  const rubricSources = [];
  const fmLines = fm.split(/\r?\n/);
  const sourcesStart = fmLines.findIndex((line) => /^rubric_sources:\s*$/.test(line));
  if (sourcesStart !== -1) {
    let current = null;
    for (const line of fmLines.slice(sourcesStart + 1)) {
      const opener = line.match(/^\s+-\s*id:\s*(\S+)\s*$/);
      if (opener) {
        current = { id: opener[1], citation: "", url: "", accessed: "", operationalization: "" };
        rubricSources.push(current);
        continue;
      }
      const field = line.match(/^\s+([\w-]+):\s*(.+)$/);
      if (field && current && field[1] in current) {
        current[field[1]] = unquote(field[2]);
        continue;
      }
      if (line.trim() === "") continue;
      break; // an unindented line is the next top-level key, which ends the block
    }
  }
  for (const src of rubricSources) {
    // `url: null` is the deliberate convention for a source with no web address: TOULMIN and
    // WILLIAMS are printed books, and they are precisely the `paraphrased` sources whose text this
    // library never reproduces. Normalized to "" here so the emitters render a plain citation
    // rather than a link to the four-character string "null", which is what a truthiness check
    // alone produced.
    if (src.url === "null" || src.url === "~") src.url = "";
    for (const key of ["citation", "accessed", "operationalization"]) {
      if (!src[key]) throw new Error(`gen-site: ${sourcePath} rubric source ${src.id} has no ${key}.`);
    }
  }
  if (rubricSources.length === 0) {
    throw new Error(`gen-site: ${sourcePath} declares no rubric_sources.`);
  }

  // checks.scripted and checks.judged: block lists of criterion IDs.
  const checksBlock = fm.split(/^checks:\s*$/m)[1];
  if (checksBlock === undefined) throw new Error(`gen-site: ${sourcePath} has no checks block.`);
  // Walked line by line rather than sliced by a stop-regex. The obvious stop pattern for "the
  // next key at a shallower indent" also matches a list item at this indent, which silently
  // returned an empty lane for all six skills: the generator reported 0 criteria and emitted six
  // skill pages with no criterion on them, cheerfully. A list item is a line starting with "-";
  // anything else that is not blank ends the lane. No indent arithmetic, nothing to get wrong.
  const lane = (key) => {
    const lines = checksBlock.split(/\r?\n/);
    const start = lines.findIndex((line) => new RegExp(`^\\s+${key}:\\s*$`).test(line));
    if (start === -1) return [];
    const ids = [];
    for (const line of lines.slice(start + 1)) {
      const item = line.match(/^\s+-\s*(\S+)\s*$/);
      if (item) {
        ids.push(item[1]);
        continue;
      }
      if (line.trim() === "") continue;
      break;
    }
    return ids;
  };

  return {
    name,
    description,
    version,
    license,
    rubricSources,
    scripted: lane("scripted"),
    judged: lane("judged"),
    body,
  };
}

/**
 * The prose between a body's H1 and its first H2.
 *
 * This is where every skill states what it reads and what it refuses to claim, and it is the only
 * reader-facing prose in a SKILL.md: everything below the first H2 is agent-facing protocol.
 *
 * Emitted whole rather than mined for an "artifact claim" sentence, because there is no marker to
 * mine. Checked across all six sources: `critique-clarity` writes `**Artifact claim.**`,
 * `critique-docs` writes `**Artifact claim (v0.1, narrow):**`, `critique-microcopy` writes
 * `**Narrow artifact claim.**`, `critique-accessibility` writes it as plain prose, and
 * `critique-argument` and `critique-usability` do not announce one at all. Any extractor over
 * that would silently publish two skill pages with no claim on them. Emitting the paragraph the
 * author wrote cannot be silently incomplete.
 *
 * @param {string} body
 * @returns {string}
 */
export function extractIntro(body) {
  const afterH1 = body.replace(/^\s*#\s+[^\n]*\r?\n/, "");
  const firstH2 = afterH1.search(/^##\s/m);
  return (firstH2 === -1 ? afterH1 : afterH1.slice(0, firstH2)).trim();
}

/**
 * Load every shipped skill, in library.json order, with every criterion ID validated.
 *
 * A criterion that does not match the contract's own grammar is a build failure, not a warning.
 * The alternative is a site that publishes a criteria explorer quietly missing rows.
 *
 * @returns {Array<ReturnType<typeof parseSkill> & {path: string, route: string}>}
 */
export function loadSkills() {
  const library = readJson(join(ROOT, "library.json"));
  const listed = (library.components?.skills ?? []).filter((s) => s.status === "active");
  if (listed.length === 0) throw new Error("gen-site: library.json lists no active skill.");

  const idPattern = criterionPattern();
  const seen = new Map();
  const skills = [];

  for (const entry of listed) {
    const sourcePath = `${entry.path}/SKILL.md`;
    const parsed = parseSkill(readUtf8(join(ROOT, sourcePath)), sourcePath);
    if (parsed.version !== entry.version) {
      throw new Error(
        `gen-site: ${sourcePath} is version ${parsed.version} but library.json says ${entry.version}.`,
      );
    }
    for (const id of [...parsed.scripted, ...parsed.judged]) {
      if (!idPattern.test(id)) {
        throw new Error(
          `gen-site: ${sourcePath} declares criterion "${id}", which does not match the contract's ` +
            `criterionId grammar ${idPattern.source}.`,
        );
      }
      if (seen.has(id)) {
        throw new Error(`gen-site: criterion ${id} is declared by both ${seen.get(id)} and ${parsed.name}.`);
      }
      seen.set(id, parsed.name);
    }
    skills.push({ ...parsed, path: sourcePath, dir: entry.path, route: `/skills/${parsed.name}/` });
  }
  return skills;
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
export function buildRouteMap(skills = loadSkills()) {
  const routes = new Map();
  for (const quadrant of QUADRANTS) {
    for (const file of listMarkdown(join(DOCS_SRC, quadrant))) {
      const repoPath = `docs/${quadrant}/${file}`;
      routes.set(repoPath, routeFor(repoPath));
    }
  }
  for (const skill of skills) routes.set(skill.path, skill.route);
  for (const [source, route] of Object.entries(EXTRA_ROUTES)) routes.set(source, route);
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
 * A rubric citation as a table cell: a link when the source has a URL, plain text when it does
 * not. A `paraphrased` source is often a printed book (TOULMIN, WILLIAMS) whose frontmatter
 * carries `url: null` on purpose, and those are exactly the sources whose text is never
 * reproduced here.
 */
function citationCell(src) {
  return src.url ? `[${src.citation}](${src.url})` : src.citation;
}

/** A markdown inline-code list of criterion IDs, or an explicit note when a lane is empty. */
function criterionList(ids) {
  return ids.length === 0 ? "_None in this lane._" : ids.map((id) => `\`${id}\``).join(" ");
}

/**
 * Emit one skill page from its SKILL.md.
 * Carries the version badge read from library.json, the rubric provenance table with citation
 * URLs, both criterion lanes, and boundary links to the sibling skills its own description names.
 */
function generateSkillPage(skill, index, skills, routes) {
  const siblings = skills
    .filter((other) => other.name !== skill.name && skill.description.includes(other.name))
    .map((other) => `[${other.name}](${BASE}${other.route})`);

  const rubricRows = skill.rubricSources.map(
    (src) => `| \`${src.id}\` | ${citationCell(src)} | ${src.operationalization} | ${src.accessed} |`,
  );

  const total = skill.scripted.length + skill.judged.length;
  const { body: intro } = rewriteLinks(extractIntro(skill.body), skill.dir, routes);

  const sections = [
    intro,
    "",
    "## What it reads against",
    "",
    "| Rubric | Citation | Operationalization | Accessed |",
    "|---|---|---|---|",
    ...rubricRows,
    "",
    `Rubric text is never reproduced. Each source is operationalized into criteria in the skill's own [\`references/\`](${GH_TREE}/${skill.dir}/references/) directory: \`open-standard\` sources are encoded from public specifications, \`paraphrased\` sources are encoded as original-wording operational tests.`,
    "",
    "## Criteria",
    "",
    `${total} criteria: **${skill.scripted.length} scripted**, **${skill.judged.length} judged**. Every one of them, with its rubric and lane, is in the [criteria explorer](${BASE}${CRITERIA_ROUTE}#${skill.name}).`,
    "",
    `### Scripted (${skill.scripted.length})`,
    "",
    "Deterministic. Run by the skill's own `scripts/checks.py`, and the same input gives the same finding every time.",
    "",
    criterionList(skill.scripted),
    "",
    `### Judged (${skill.judged.length})`,
    "",
    "Requires reasoning. This is the lane the benchmark measures, and the lane where two runs can disagree.",
    "",
    criterionList(skill.judged),
    "",
  ];

  if (siblings.length > 0) {
    sections.push(
      "## Boundaries",
      "",
      `This skill's own description marks its edge against ${siblings.join(" and ")}. The boundary is deliberate: overlapping skills that both claim an artifact produce double-counted findings.`,
      "",
    );
  }

  sections.push(
    "## Elsewhere",
    "",
    `- [\`SKILL.md\`](${GH_BLOB}/${skill.path}), the source this page is generated from`,
    `- [Worked example](${GH_BLOB}/examples/${skill.name.replace(/^critique-/, "")}/README.md)`,
    `- License: ${skill.license}`,
    "",
  );

  const frontmatter = emitFrontmatter({
    title: skill.name,
    description: skill.description,
    editUrl: `${GH_EDIT}/${skill.path}`,
    extra: ["sidebar:", `  order: ${index + 1}`, "  badge:", `    text: v${skill.version}`],
  });
  const repoOut = `site/src/content/docs${outputPathFor(skill.route)}`;
  const banner = `<!-- Generated by scripts/gen-site.mjs from ${skill.path}. Do not edit: this file is gitignored and rewritten on every build. -->`;
  writeUtf8(join(ROOT, repoOut), `${frontmatter}\n\n${banner}\n\n${sections.join("\n").trim()}\n`);
  return repoOut;
}

/**
 * Emit the criteria explorer: every criterion the shipped skills score, in one page.
 *
 * `editUrl: false` because it has no single source. One section per skill, which gives each skill
 * page a real anchor to link into, and one summary table whose totals are derived rather than
 * typed. The README states the lane split as a sentence; this page is where that claim becomes
 * auditable, so if a skill adds a criterion the site is right and the README is stale.
 */
function generateCriteriaExplorer(skills) {
  const scripted = skills.reduce((n, s) => n + s.scripted.length, 0);
  const judged = skills.reduce((n, s) => n + s.judged.length, 0);
  const namespaces = new Map();
  for (const skill of skills) {
    for (const src of skill.rubricSources) namespaces.set(src.id, src);
  }

  const lines = [
    `**${scripted + judged} criteria** across ${skills.length} shipped skills: **${scripted} scripted** and **${judged} judged**. Every figure on this page is counted from the six \`SKILL.md\` frontmatters at build time, and every ID is checked against the criterion grammar in the frozen contract schema before it is written here.`,
    "",
    "A criterion ID is permanent. It is never reused for a different test and never renumbered, because a finding recorded against it has to stay meaningful after the rubric behind it is revised. The grammar and the permanence rules are in [criterion IDs](" + BASE + "/reference/criterion-ids/).",
    "",
    "| Skill | Version | Scripted | Judged | Total | Rubrics |",
    "|---|---|---:|---:|---:|---|",
    ...skills.map(
      (s) =>
        `| [${s.name}](${BASE}${s.route}) | ${s.version} | ${s.scripted.length} | ${s.judged.length} | ${s.scripted.length + s.judged.length} | ${s.rubricSources.map((r) => `\`${r.id}\``).join(", ")} |`,
    ),
    `| **Total** | | **${scripted}** | **${judged}** | **${scripted + judged}** | |`,
    "",
    "## Rubric sources",
    "",
    "| Namespace | Citation | Operationalization |",
    "|---|---|---|",
    ...[...namespaces.values()]
      .sort((a, b) => a.id.localeCompare(b.id))
      .map((src) => `| \`${src.id}\` | ${citationCell(src)} | ${src.operationalization} |`),
    "",
  ];

  for (const skill of skills) {
    const rows = [
      ...skill.scripted.map((id) => ({ id, lane: "scripted" })),
      ...skill.judged.map((id) => ({ id, lane: "judged" })),
    ].sort((a, b) => a.id.localeCompare(b.id));
    lines.push(
      `## ${skill.name}`,
      "",
      `${rows.length} criteria, from ${skill.rubricSources.map((r) => `\`${r.id}\``).join(" and ")}. [Skill page](${BASE}${skill.route}).`,
      "",
      "| Criterion | Lane | Rubric |",
      "|---|---|---|",
      ...rows.map((row) => {
        const namespace = row.id.split("-")[0];
        const src = skill.rubricSources.find((r) => r.id === namespace) ?? skill.rubricSources[0];
        return `| \`${row.id}\` | ${row.lane} | \`${src.id}\` |`;
      }),
      "",
    );
  }

  const frontmatter = emitFrontmatter({
    title: "Criteria",
    description: `All ${scripted + judged} criteria the shipped critique skills score, each with its lane, its owning skill, and the rubric it traces to.`,
    editUrl: false,
    extra: ["tableOfContents:", "  maxHeadingLevel: 2"],
  });
  const repoOut = `site/src/content/docs${outputPathFor(CRITERIA_ROUTE)}`;
  const banner =
    "<!-- Generated by scripts/gen-site.mjs from all six SKILL.md frontmatters. Do not edit: this file is gitignored and rewritten on every build. -->";
  writeUtf8(join(ROOT, repoOut), `${frontmatter}\n\n${banner}\n\n${lines.join("\n").trim()}\n`);
  return repoOut;
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

  const skills = loadSkills();
  const routes = buildRouteMap(skills);
  const skillSources = new Set(skills.map((skill) => skill.path));
  const files = [];
  const unresolved = [];

  // ORDER IS LOAD-BEARING. The quadrant pass wipes reference/, and both the criteria explorer
  // (/reference/criteria/) and the critic subagent page (/reference/critic-subagent/) are emitted
  // into it. Moving either emit above this loop deletes it on the next build, and the page simply
  // stops existing rather than failing. Clear first, write second.
  for (const quadrant of QUADRANTS) {
    freshDir(join(DOCS_OUT, quadrant));
  }
  removeGeneratedSkillPages();

  for (const repoPath of routes.keys()) {
    // Skill pages have their own emit: they are assembled from frontmatter rather than copied.
    if (skillSources.has(repoPath)) continue;
    const result = generatePage(repoPath, routes);
    files.push(result.repoOut);
    for (const href of result.unresolved) unresolved.push(`${repoPath}: ${href}`);
  }
  skills.forEach((skill, index) => {
    files.push(generateSkillPage(skill, index, skills, routes));
  });
  files.push(generateCriteriaExplorer(skills));

  if (unresolved.length > 0) {
    // Left unchanged in the output rather than guessed at, so the W6 rendered-link guard fails
    // on it loudly instead of the generator inventing a URL that resolves to nothing.
    console.warn(
      `gen-site: ${unresolved.length} link(s) escape the repo root and were left as-is:\n  ` +
        unresolved.join("\n  "),
    );
  }
  if (!quiet) {
    const criteria = skills.reduce((n, s) => n + s.scripted.length + s.judged.length, 0);
    console.log(
      `gen-site: ${files.length} pages -> ${DOCS_OUT} ` +
        `(${QUADRANTS.length} quadrants, ${skills.length} skills, ${criteria} criteria)`,
    );
  }
  return { files, routes, skills };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) generate();
