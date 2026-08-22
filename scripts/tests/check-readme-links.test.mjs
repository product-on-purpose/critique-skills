// what-it-is:   unit tests for the README front-door guard
// what-it-does: exercises both halves against fixtures (a site link naming a route the manifest
//               does not carry, and doors that disagree with the landing cards), plus a live check
//               that the real README and the real landing page currently agree
// why:          under decision D1 the README is the front door to a primary artifact that lives
//               elsewhere, so a renamed route turns the project's most-read document into 404s and
//               nothing else notices: the site's own guards only check the site's internal links.
//               This guard found a real dead link (/conformance/) the first time it ran
// used-by:      "npm test" (node --test), .github/workflows/ci.yml's unit-node job
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { tempDir } from "./helpers/tmp.mjs";
import { checkReadmeLinks, readmeDoors, landingCardTitles } from "../check-readme-links.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, "..", "..");
const SITE = "https://product-on-purpose.github.io/critique-skills";

const DOORS = ["Use it on something", "Decide whether to believe it", "Build on it or contribute"];

function fixture(t, { links = [], doors = DOORS, cards = DOORS, routes = [] } = {}) {
  const root = tempDir(t, "readme-links-");
  const readme = resolve(root, "README.md");
  const manifest = resolve(root, "manifest.txt");
  const landing = resolve(root, "index.mdx");

  writeFileSync(
    readme,
    [
      "# Title",
      "",
      "### Start here",
      "",
      "| You want to | Start at | Then |",
      "|---|---|---|",
      ...doors.map((door) => `| **${door}** | a | b |`),
      "",
      "## Elsewhere",
      "",
      ...links.map((link) => `See [it](${SITE}${link}).`),
      "",
    ].join("\n"),
    "utf8",
  );
  writeFileSync(manifest, routes.join("\n") + "\n", "utf8");
  writeFileSync(landing, cards.map((card) => `<Card title="${card}" icon="x">body</Card>`).join("\n"), "utf8");
  return { readme, manifest, landing };
}

test("passes when every site link names a route the manifest carries", (t) => {
  const paths = fixture(t, {
    links: ["/", "/skills/", "/receipts/"],
    routes: ["/index.html", "/skills/index.html", "/receipts/index.html"],
  });
  assert.equal(checkReadmeLinks(paths), 0);
});

test("fails a README link to a route the site does not build", (t) => {
  // The exact failure this guard caught on its first run: the applied README linked twice to
  // /conformance/, a page W5 deliberately did not build.
  const paths = fixture(t, {
    links: ["/skills/", "/conformance/"],
    routes: ["/skills/index.html"],
  });
  assert.equal(checkReadmeLinks(paths), 1);
});

test("fails when the README's doors and the landing cards disagree", (t) => {
  const paths = fixture(t, {
    links: [],
    routes: ["/index.html"],
    doors: DOORS,
    cards: ["The skills", "The receipts", "How it works"],
  });
  // These were the real W5 card titles before W8 aligned them; the README and the site offered a
  // reader two different sets of three doors.
  assert.equal(checkReadmeLinks(paths), 1);
});

test("fails when a door is added on one side only", (t) => {
  const paths = fixture(t, {
    links: [],
    routes: ["/index.html"],
    doors: [...DOORS, "A fourth door"],
    cards: DOORS,
  });
  assert.equal(checkReadmeLinks(paths), 1);
});

test("fails when the README loses its door table entirely", (t) => {
  const root = tempDir(t, "readme-links-");
  const readme = resolve(root, "README.md");
  const manifest = resolve(root, "manifest.txt");
  const landing = resolve(root, "index.mdx");
  writeFileSync(readme, "# Title\n\nNo door table here.\n", "utf8");
  writeFileSync(manifest, "/index.html\n", "utf8");
  writeFileSync(landing, '<Card title="Use it on something" icon="x">b</Card>', "utf8");
  assert.equal(checkReadmeLinks({ readme, manifest, landing }), 1);
});

test("readmeDoors reads the leading bold cell of each row, at any heading level", () => {
  const text = ["## Start here", "", "| a | b |", "|---|---|", "| **One** | x |", "| **Two** | y |", "", "## Next", "", "| **Not a door** | z |"].join("\n");
  assert.deepEqual(readmeDoors(text), ["One", "Two"]);
});

test("landingCardTitles reads every Card title", () => {
  assert.deepEqual(
    landingCardTitles('<Card title="A" icon="x">b</Card>\n<Card title="B">c</Card>'),
    ["A", "B"],
  );
});

test("the real README and the real landing page currently agree", () => {
  // The live assertion: this is what fails in CI if someone renames a route, moves a door, or
  // edits one of the two documents without the other.
  assert.equal(checkReadmeLinks({}), 0);
  const landing = readFileSync(resolve(REPO_ROOT, "site", "src", "content", "docs", "index.mdx"), "utf8");
  assert.deepEqual(landingCardTitles(landing), DOORS);
});
