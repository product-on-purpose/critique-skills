#!/usr/bin/env node
// what-it-is:   the CI dependency audit: `npm audit` at high severity, plus a dated exception list
// what-it-does: runs `npm audit --json` for the root tree or, with --prefix, another tree; fails on
//               any high or critical advisory that scripts/audit-exceptions.json does not excuse,
//               and on any exception that is malformed or past its expiry date while its advisory
//               is still reported
// why:          npm audit cannot excuse one advisory, so an advisory with no fixed version anywhere
//               (GHSA-ch52-4w7c-c8xp, 2026-10-02) failed every branch and blocked every merge; a
//               written exception that expires keeps every other advisory gating while that one
//               waits for its upstream fix
// used-by:      .github/workflows/ci.yml (both steps of the audit job) and release.yml
//
// Usage:  node scripts/audit.mjs [--prefix <dir>]
//
// An exception names one advisory by its GHSA id, the reason it does not apply here, and an expiry
// date. On the expiry date the advisory gates again, so an exception cannot outlive the judgment
// behind it without someone renewing it on purpose. An exception whose advisory is no longer
// reported is printed as stale, so it can be removed.
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const EXCEPTIONS_PATH = resolve(HERE, "audit-exceptions.json");
const GATING = new Set(["high", "critical"]);
const REQUIRED_FIELDS = ["id", "package", "reason", "expires"];

/** The GHSA id at the end of an advisory URL, or the URL itself when it has none. */
function advisoryId(url) {
  const match = /GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}/i.exec(url ?? "");
  return match ? match[0] : String(url);
}

/**
 * Every advisory in an `npm audit --json` report, one entry per advisory and package. A package
 * that is vulnerable only because it depends on another lists that package's name as a string in
 * `via`; only the object entries are advisories, so excusing the root advisory excuses its
 * dependents too.
 */
export function listAdvisories(report) {
  const seen = new Map();
  for (const [name, vuln] of Object.entries(report?.vulnerabilities ?? {})) {
    for (const via of vuln.via ?? []) {
      if (typeof via !== "object" || via === null) continue;
      const id = advisoryId(via.url);
      const key = `${id} ${name}`;
      if (!seen.has(key)) {
        seen.set(key, { id, package: name, severity: via.severity, title: via.title ?? "", url: via.url ?? "" });
      }
    }
  }
  return [...seen.values()];
}

/** The exceptions that apply to one tree: "root", or the --prefix directory. No `tree` means root. */
export function exceptionsFor(exceptions, tree) {
  return exceptions.filter((exception) => (exception?.tree ?? "root") === tree);
}

/**
 * Decide the audit. `today` is an ISO date (YYYY-MM-DD). Returns failures (each a sentence),
 * the advisories excused, and warnings about exceptions that excuse nothing.
 */
export function evaluateAudit(report, exceptions, today) {
  const failures = [];
  const excused = [];
  const warnings = [];
  const byId = new Map();

  for (const exception of exceptions) {
    const missing = REQUIRED_FIELDS.filter((field) => !exception?.[field]);
    if (missing.length > 0) {
      failures.push(`exception ${exception?.id ?? "(no id)"} is missing ${missing.join(", ")}`);
      continue;
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(exception.expires)) {
      failures.push(`exception ${exception.id} has an expiry that is not YYYY-MM-DD: ${exception.expires}`);
      continue;
    }
    byId.set(exception.id.toUpperCase(), exception);
  }

  const reported = new Set();
  for (const advisory of listAdvisories(report)) {
    if (!GATING.has(advisory.severity)) continue;
    reported.add(advisory.id.toUpperCase());
    const exception = byId.get(advisory.id.toUpperCase());
    if (!exception) {
      failures.push(`${advisory.severity}: ${advisory.package} ${advisory.id} ${advisory.title} ${advisory.url}`.trim());
    } else if (today >= exception.expires) {
      failures.push(
        `${advisory.severity}: ${advisory.package} ${advisory.id} is still reported, and its exception expired on ${exception.expires}; renew it on purpose or fix the dependency`,
      );
    } else {
      excused.push(`${advisory.package} ${advisory.id}, excused until ${exception.expires}: ${exception.reason}`);
    }
  }

  for (const [id, exception] of byId) {
    if (!reported.has(id)) {
      warnings.push(`exception ${exception.id} (${exception.package}) excuses nothing in this tree; remove it once no tree reports it`);
    }
  }
  return { failures, excused, warnings };
}

function runNpmAudit(prefix) {
  const args = ["audit", "--json", ...(prefix ? ["--prefix", prefix] : [])];
  // npm exits non-zero whenever it finds anything, so the exit code is not the verdict; the JSON is.
  const result = spawnSync("npm", args, { cwd: ROOT, encoding: "utf-8", shell: process.platform === "win32" });
  try {
    return JSON.parse(result.stdout);
  } catch {
    throw new Error(`npm audit did not return JSON (exit ${result.status}): ${(result.stderr || result.stdout || "").trim().slice(0, 500)}`);
  }
}

function main(argv) {
  const prefixIndex = argv.indexOf("--prefix");
  const prefix = prefixIndex >= 0 ? argv[prefixIndex + 1] : undefined;
  const tree = prefix ?? "root";
  const exceptions = exceptionsFor(JSON.parse(readFileSync(EXCEPTIONS_PATH, "utf-8")).exceptions ?? [], tree);
  const today = new Date().toISOString().slice(0, 10);

  let report;
  try {
    report = runNpmAudit(prefix);
  } catch (error) {
    console.error(`audit: ${error.message}`);
    return 1;
  }
  const { failures, excused, warnings } = evaluateAudit(report, exceptions, today);

  for (const line of excused) console.log(`audit (${tree}): excused: ${line}`);
  for (const line of warnings) console.log(`audit (${tree}): note: ${line}`);
  if (failures.length > 0) {
    for (const line of failures) console.error(`audit (${tree}): ${line}`);
    console.error(`audit (${tree}): FAIL, ${failures.length} unexcused high or critical finding(s).`);
    return 1;
  }
  console.log(`audit (${tree}): PASS, no unexcused high or critical advisory.`);
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv.slice(2)));
}
