# 0032 - Build to the proposed Section 14, claim conformance to it nowhere

## TL;DR
- **Decision:** The `site/` documentation site is built to clauses 14.1 through 14.11 of the family's
  Astro site standard, and **no conformance to Section 14 is claimed anywhere in this repository**
  until Section 14 lands in the one normative `STANDARD.md`. [`library.json`](../../../library.json)
  keeps `"standard": "0.12"`, and neither it nor `README.md` gains a Section 14 assertion. This ADR
  is where the conformance position lives instead.
- **Why:** `SITE-STANDARD.md` is marked "promoted, tracked, **PROPOSED** for `STANDARD.md`
  Section 14". A plugin's conformance is pinned to the `STANDARD.md` version its `library.json`
  declares, and 0.12 does not contain Section 14. Building to a proposed standard is convergence
  work; claiming conformance to a version that does not carry the clauses would be a false statement
  in the one field the marketplace reads as a promise.
- **The guard position, stated once so it is not relitigated:** three of the four reference 14.11
  validators are ported. `remark-resolve-links.mjs` is not, because this site's generator emits
  Starlight-correct links directly and never emits a relative `.md` link for it to repair.
- **Status:** Proposed (lands with the site scaffold).

- **Status:** Proposed
- **Date:** 2026-08-20
- **Deciders:** Jonathan Prisant

## Builds on

- [0011 - Gate wiring: wrap the toolkit rather than vendor its checks](0011-gate-wiring-toolkit-wrapper.md),
  which set the rule this ADR keeps intact: the conformance gate is the family's shared
  implementation run against this plugin, never a local reimplementation of it. The site's guards are
  the exception that proves it, and the reason they stay out of `scripts/check.mjs` is spelled out
  under Consequences.
- The proposed family Astro site standard, Section 14 (clauses 14.1 to 14.11), owned in
  `agent-plugins/standards/domains/astro-sites/SITE-STANDARD.md`. Not landed in `STANDARD.md`; this
  ADR records this repository's position toward it.
- `agent-skills-toolkit` ADR 0026 (Astro site 14.11 conformance), the family precedent for recording
  a conformance position in an ADR when the shared infrastructure a clause prefers does not exist
  yet. This ADR follows its shape and reaches a different guard count, with cause.

## Context and problem statement

`critique-skills` is getting a documentation site: an Astro + Starlight app in `site/`, published to
GitHub Pages at `/critique-skills`, with its content generated at build time from the repository's
own sources of truth. The plan for it is `_local/astro/00-astro-starlight-site-plan.md`.

The standard that governs such a site has a status problem that has to be settled before the first
file lands rather than after.

`SITE-STANDARD.md` carries this header: **"Status: promoted, tracked, PROPOSED for `STANDARD.md`
Section 14."** Its own text is explicit that promotion is not landing, and that "until that LAND,
this document is authoritative as the family's proposed site standard and the reference for in-flight
convergence work, but a plugin's conformance is pinned to the `STANDARD.md` version in its
`library.json`, which does not yet contain Section 14."

This repository declares `"standard": "0.12"`. That field is a pin, not an aspiration: it names the
version of the Standard the conformance gate holds this plugin to, and 0.12 has no Section 14 in it.
So there is a gap between what the site is being built to satisfy and what this repository can
truthfully say it conforms to, and the gap is not closable from this side. It closes when Section 14
lands upstream.

A second question rides along with the first. Clause 14.11 names a reference set of four build-aware
validators and permits "a small hand-authored site" to port only the two load-bearing ones. This site
is neither small nor hand-authored: the generator will emit roughly forty pages. The exemption does
not apply, and the fourth validator is inapplicable for an unrelated reason. Both need saying in one
place, because "we ported three of four" reads as a shortfall unless the cause is recorded.

## Decision drivers

- **The `standard` field is read as a promise.** It is the field the gate and the marketplace consume
  to decide what this plugin is held to. Widening it to claim clauses the pinned version does not
  contain would make the field mean something different here than everywhere else in the family.
- **Not building the site until Section 14 lands is an unbounded wait.** Landing is a governance
  action in another repository, sequenced behind earlier roadmap phases. The toolkit faced exactly
  this and resolved it the same way: build now, record the position, do not claim.
- **Convergence is measured by behaviour, not by assertion.** Every clause that costs something
  (Pattern S, the base single-source, gitignored-and-rebuilt generated content, the favicon, the
  guards, the Node pin read through `node-version-file`) is implemented. What is withheld is only the
  claim.
- **A guard count without a cause is indistinguishable from a shortcut.** Clause 14.11's exemption is
  written for small hand-authored sites; invoking it here would be wrong, and skipping a validator
  for a real reason is not the same act. The distinction only survives if it is written down.
- **This repository's ADRs are its conformance record already.** The standard's own revision note 10
  warns against asserting a value is stale without reading the repository's decision record. Putting
  the position in an ADR is what makes that possible for the next auditor.

## Considered options

1. **Build to 14.1 through 14.11, claim nothing, record the position in this ADR (chosen).** The site
   satisfies every clause; `library.json` and `README.md` stay silent about Section 14; this document
   is the answer to "why does a site built to Section 14 not say so anywhere."
2. **Bump `library.json` `"standard"` to claim Section 14 now.** Rejected. There is no version to
   bump to that carries Section 14; the clauses live in a domain document that is explicitly
   pre-land. This would put a claim in the field that the gate cannot check and that the standard's
   own text contradicts.
3. **Wait for Section 14 to land, then build the site.** Rejected. The site is on this repository's
   critical path (the README becomes the front door to it), and the landing is gated on a governance
   sequence in another repository with no date. The standard itself rejects this reasoning for 14.11
   in its revision note 6: implementing locally now is the sanctioned bridge, deferring is not.
4. **Port all four 14.11 validators.** Rejected with cause, and the cause is specific rather than
   economic. `remark-resolve-links.mjs` repairs relative `.md` links inside content. This site's
   generator emits base-absolute site routes for anything published and absolute
   `https://github.com/...` URLs for anything outside the published tree, so there is no relative
   `.md` link for the plugin to act on. Porting it would add an mdast transform, plus the
   `@astrojs/markdown-remark` direct dependency its deprecated `markdown.remarkPlugins` key requires
   under Astro 7, to run over zero inputs. The donor's own config records that this dependency path
   silently broke an Astro upgrade once already.
5. **Port only the two load-bearing guards, under 14.11's small-site exemption.** Rejected. The
   exemption is written for "a small hand-authored site"; this one is generator-driven and will emit
   roughly forty pages. `verify-edit-links.mjs` exists precisely for that condition: it fails a
   generated page whose `editUrl` auto-derives to a gitignored path, which is the exact failure mode
   a gitignored-and-rebuilt content tree creates. Taking the exemption here would skip the guard this
   site needs most.

## Decision outcome

Chosen: **option 1.** Concretely, and this is the checklist a later audit should hold the site to:

**Built to, without claiming:** 14.1 (Pattern S, the Astro app in `site/`, stock `docsLoader()`,
repo-root `docs/` never built by Astro), 14.2 (Astro plus Starlight, `site` set so the sitemap
auto-registers, `astro-mermaid` before `starlight`), 14.3 and 14.4 (reference pages generated from
`skills/` and `library.json`; the generated tree gitignored and rebuilt, the preferred model, with
`check-generated-untracked.mjs` enforcing it), 14.5 (no committed build output), 14.6 (a PR-triggered
non-deploying `build-site` job running the same recipe as the deploy build), 14.7 (the base declared
once in [`scripts/site-base.mjs`](../../../scripts/site-base.mjs) and consumed, with the two
sanctioned duplications commented as such), 14.8 (`engines.node >=22.12.0`, a committed `.nvmrc`
pinning `24`, CI reading it through `node-version-file`, versions pinned by the committed lockfile
and `npm ci`), 14.9 (Pagefind, sitemap, `robots.txt`, and a favicon, which is a MUST because
Starlight emits a `<link rel="icon">` on every page whether or not the file exists), 14.10 (no config
sidecars), and 14.11 as described below.

**14.11, three of four.** `check-rendered-links.mjs` and `check-route-parity.mjs` are the two
load-bearing MUSTs. `verify-edit-links.mjs` is ported because this site is generator-heavy and that
is the condition it exists for. `remark-resolve-links.mjs` is not ported, per option 4 above. All
three run in both the PR build and the deploy build, not the PR build only, and each preserves the
standard's normative robustness contract: hard-fail an empty-but-existing `dist`, resolve
bare-relative hrefs, decode percent-escaped path segments, match both attribute quote styles, and
fail on their own assertions rather than on a parse error of malformed input.

**Claimed nowhere.** `library.json` keeps `"standard": "0.12"`. `README.md` gains no Section 14
assertion. No skill frontmatter changes. The conformance gate
([`scripts/check.mjs`](../../../scripts/check.mjs)) is untouched by the site and continues to run the
pinned toolkit's validators against the plugin.

**What changes when Section 14 lands.** Three things, in this order: bump `"standard"` in
`library.json` to the version that carries Section 14 and re-run the gate; add `critique-skills` to
the per-repo convergence table in the standard's section 5, where it does not yet appear because it
had no site when that table was written; and append a landed note to this ADR rather than superseding
it, since the position it records will have been discharged rather than reversed.

## Consequences

**Positive.** The site can be built now, on the critical path it actually sits on, without either
waiting on another repository's governance queue or writing a claim this repository cannot support.
The guard position is recorded with its cause, so "three of four" is auditable as a decision instead
of readable as a gap. The `standard` field keeps meaning exactly one thing family-wide.

**Negative.** For as long as Section 14 is unlanded, this repository ships a site built to a standard
that nothing in its own CI checks: the conformance gate validates the plugin, not the site, and the
site's own guards enforce link and route integrity rather than clause conformance. The only record
that the clauses were followed is this ADR and the comments in the site's configuration. That is a
real weakness and it is accepted knowingly; the alternative was a claim in `library.json` that would
have been worse.

**Neutral.** This is a site-only decision. It changes no skill, no criterion, no contract, and no
benchmark figure, and a consumer who installs the plugin and never opens the site is unaffected by
every word of it.

## Implementation sites

- [`.nvmrc`](../../../.nvmrc): `24`, the committed Node pin clause 14.8 requires. The plugin core's
  own CI matrix (`22.12.0` and `24`) is deliberately left alone: it tests a floor and a pin, which is
  a different purpose from the site's single build environment.
- [`scripts/site-base.mjs`](../../../scripts/site-base.mjs): the single source of the base path
  (14.7), consumed by `site/astro.config.mjs` and, when they land, by the generator and the
  rendered-link guard.
- `site/astro.config.mjs`: integration order, the branded mermaid theme, the explicit `editLink`
  base, and the comments recording why `markdown.remarkPlugins` is absent.
- `site/public/favicon.svg`: the family `#5C7CFA` three-diamond mark, reused verbatim from
  `pm-skills` (14.9 MUST).
- [`.gitignore`](../../../.gitignore): the gitignored-and-rebuilt generated tree (14.4).
- `scripts/check-rendered-links.mjs`, `scripts/check-route-parity.mjs`,
  `scripts/verify-edit-links.mjs`, `scripts/check-generated-untracked.mjs`: the guards, arriving in a
  later phase of the site work, each of which this ADR commits to.
