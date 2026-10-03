// what-it-is:   unit tests for the CI dependency audit and its dated exception list
// what-it-does: feeds evaluateAudit() npm-audit-shaped reports and exception lists, and checks the
//               committed scripts/audit-exceptions.json is well formed
// why:          an exception list is a hole in a security gate by construction; these tests hold
//               the hole to its edges: one advisory, a reason, an expiry that re-closes it, and no
//               excuse for anything not named
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { evaluateAudit, exceptionsFor, listAdvisories } from "../audit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));

// The shape `npm audit --json` (npm 10) produced for site/ on 2026-10-02: one advisory, five
// packages flagged only through their dependency on it.
const REPORT = {
  auditReportVersion: 2,
  vulnerabilities: {
    "http-cache-semantics": {
      name: "http-cache-semantics",
      severity: "high",
      via: [
        {
          source: 1240991,
          title: "http-cache-semantics max-stale handling can disclose cross-user cached responses",
          url: "https://github.com/advisories/GHSA-ch52-4w7c-c8xp",
          severity: "high",
          range: "<=4.2.0",
        },
      ],
    },
    astro: { name: "astro", severity: "high", via: ["http-cache-semantics"] },
    "@astrojs/mdx": { name: "@astrojs/mdx", severity: "high", via: ["astro"] },
  },
};

const EXCEPTION = {
  id: "GHSA-ch52-4w7c-c8xp",
  package: "http-cache-semantics",
  reason: "build-time only",
  expires: "2026-11-02",
};

test("only object via entries are advisories, so dependents are not counted twice", () => {
  const advisories = listAdvisories(REPORT);
  assert.equal(advisories.length, 1);
  assert.equal(advisories[0].id, "GHSA-ch52-4w7c-c8xp");
  assert.equal(advisories[0].package, "http-cache-semantics");
});

test("an unexcused high advisory fails", () => {
  const { failures } = evaluateAudit(REPORT, [], "2026-10-02");
  assert.equal(failures.length, 1);
  assert.match(failures[0], /GHSA-ch52-4w7c-c8xp/);
});

test("an excused advisory passes before its expiry", () => {
  const { failures, excused } = evaluateAudit(REPORT, [EXCEPTION], "2026-10-02");
  assert.deepEqual(failures, []);
  assert.equal(excused.length, 1);
});

test("an exception gates again on its expiry date", () => {
  const { failures } = evaluateAudit(REPORT, [EXCEPTION], "2026-11-02");
  assert.equal(failures.length, 1);
  assert.match(failures[0], /expired on 2026-11-02/);
});

test("an exception excuses only the advisory it names", () => {
  const other = structuredClone(REPORT);
  other.vulnerabilities.undici = {
    name: "undici",
    severity: "critical",
    via: [{ title: "x", url: "https://github.com/advisories/GHSA-aaaa-bbbb-cccc", severity: "critical" }],
  };
  const { failures, excused } = evaluateAudit(other, [EXCEPTION], "2026-10-02");
  assert.equal(excused.length, 1);
  assert.equal(failures.length, 1);
  assert.match(failures[0], /GHSA-aaaa-bbbb-cccc/);
});

test("moderate and low advisories do not gate, matching --audit-level=high", () => {
  const mild = structuredClone(REPORT);
  mild.vulnerabilities["http-cache-semantics"].via[0].severity = "moderate";
  assert.deepEqual(evaluateAudit(mild, [], "2026-10-02").failures, []);
});

test("an exception missing its reason or expiry is itself a failure", () => {
  const { failures } = evaluateAudit(REPORT, [{ id: EXCEPTION.id, package: EXCEPTION.package }], "2026-10-02");
  assert.ok(failures.some((f) => /missing reason, expires/.test(f)));
});

test("an exception for an advisory no longer reported is a warning, not a failure", () => {
  const { failures, warnings } = evaluateAudit({ vulnerabilities: {} }, [EXCEPTION], "2026-10-02");
  assert.deepEqual(failures, []);
  assert.equal(warnings.length, 1);
});

test("an exception applies only to the tree it names, and no tree means the root tree", () => {
  const site = { ...EXCEPTION, tree: "site" };
  const root = { ...EXCEPTION, id: "GHSA-aaaa-bbbb-cccc" };
  assert.deepEqual(exceptionsFor([site, root], "site"), [site]);
  assert.deepEqual(exceptionsFor([site, root], "root"), [root]);
});

test("the committed exception list is well formed and every entry expires", () => {
  const data = JSON.parse(readFileSync(resolve(HERE, "..", "audit-exceptions.json"), "utf-8"));
  for (const exception of data.exceptions) {
    for (const field of ["id", "package", "reason", "expires", "added"]) {
      assert.ok(exception[field], `${exception.id} lacks ${field}`);
    }
    assert.match(exception.expires, /^\d{4}-\d{2}-\d{2}$/);
    const days = (Date.parse(exception.expires) - Date.parse(exception.added)) / 86_400_000;
    assert.ok(days > 0 && days <= 31, `${exception.id} lasts ${days} days; an exception lasts at most 31`);
  }
});
