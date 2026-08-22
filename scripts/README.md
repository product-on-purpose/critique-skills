---
title: scripts
---

# scripts

Repo tooling: the conformance gate wrapper, the manifest and README generators and their drift
checks, the release version guard and notes extractor, the per-skill template self-test, and their
shared library.

## Inventory

- `check.mjs` - the conformance gate entry point; wraps the toolkit's checks.
- `gen-plugin-manifest.mjs` - regenerates `.claude-plugin/plugin.json` from `library.json`; under
  `--check`, the CI "drift" job's entry point instead.
- `gen-readme-catalog.mjs` - regenerates `README.md`'s skill-catalog table from `library.json` and
  each shipped skill's own `SKILL.md` frontmatter; `--check` compares instead of writing. The
  README's results table has its own generator, `python -m bench.report table` (see
  `bench/README.md`, "Results"); this script does not touch it.
- `gen-index.mjs` - regenerates the navigational `INDEX.md` from `library.json` plus component
  frontmatter; `--check` compares instead of writing. `gen-plugin-manifest.mjs` folds this in under
  `npm run gen` and its `--check` drift mode, so it is rarely invoked standalone.
- `check-release-versions.mjs` - the release tag-vs-manifest version guard; the CI "release" job's
  entry point.
- `extract-release-notes.mjs` - pulls one version's section out of `RELEASE-NOTES.md` for the GitHub
  release body.
- `skill-selftest.py` - validates one `skills/critique-<domain>/` directory against the S-04 skill
  template; see `docs/internal/skill-template.md`, "Self-test".
- `run-joint-routing.py` - the scorer for `evals/joint-routing.eval.json`. Loads this repo as a
  plugin with `claude --plugin-dir`, so all six skill descriptions are in context exactly as they
  are for a user, then puts one query at a time to a pinned model and records which skill comes
  back. Forced choice, `--k` repeats per query with the modal answer scored, because routing is
  stochastic. Run by hand; not in CI, because it calls a live model.
- `smoke.py` - the does-it-actually-run check, and the CI "smoke" job's entry point. Runs every
  skill's scripted lane on a real committed artifact and asserts the outcome for the environment:
  `--expect no-deps` (a fresh install, where each skill must fail naming the exact install command
  and printing no traceback) or `--expect ready` (dependencies installed, where each must emit a
  usable envelope). Stdlib only, because it has to run in the environment where the third-party
  dependency is missing.
- `site-base.mjs` - the one place the docs site's published base path (`/critique-skills`) is
  written down, exported as `BASE`. Not a runnable script: `site/astro.config.mjs` imports it, and
  the site's link and route guards will import the same value, so the build and the checks cannot
  disagree about where the site lives. See
  `docs/internal/decisions/0032-astro-site-conformance-position.md`.
- `gen-site.mjs` - generates the docs site's content tree: reads the four publishable Diataxis
  quadrants under `docs/` and writes a Starlight-shaped copy into `site/src/content/docs/`, with
  explicit frontmatter and every markdown link resolved at generation time (a published page
  becomes a site route, anything else in the repo becomes a GitHub URL). `docs/internal/` is never
  routed. Called by `site/astro.config.mjs` at config load, so every astro entrypoint regenerates.
- `check-generated-untracked.mjs` - asserts that every file `gen-site.mjs` emits is gitignored and
  untracked, which is what keeps the gitignored-and-rebuilt model from failing silently when a new
  emit directory is added.
- `check-site.mjs` - the one command that runs every docs-site guard against a built `site/dist`:
  the three ported 14.11 validators below plus `check-generated-untracked.mjs`. `check.mjs` runs it
  when a built site is present, and both CI jobs call it directly.
- `check-rendered-links.mjs` - the browser-broken-link guard. Resolves every intra-site href against
  the page's real served URL and asserts the target exists in `dist`, with fragments checked against
  the target page's element ids. A filesystem-correct link can still 404 in a browser, because pages
  build to `slug/index.html` and are served one URL level deeper than their source.
- `check-route-parity.mjs` - the guard against silently removing a published route. Diffs the built
  route set against `route-manifest.txt` and fails when a baseline route disappears; added routes are
  allowed. Run with `--update` to rewrite the baseline after an intentional removal.
- `verify-edit-links.mjs` - asserts every "Edit page" link in the built site points at a file that
  really exists, and fails when the total count collapses. This site is generator-heavy and
  Starlight's `editUrl` auto-derivation resolves to the gitignored generated tree, so this is the
  guard that keeps every generated page's explicit `editUrl` honest.
- `route-manifest.txt` - the committed baseline `check-route-parity.mjs` diffs against: one line per
  built route. Regenerate with `node scripts/check-route-parity.mjs --update` and commit it in the
  same change as the route removal that made it necessary, with the reason in the message.
- `lib/` - shared helpers used by the scripts above.
- `tests/` - two suites: `node --test` coverage for the Node spine above, and the pytest suite for
  the Python tooling here (`skill-selftest.py`); see `tests/README.md` for the inventory.
- `__init__.py` - package marker so `scripts/` resolves against the repository root.
