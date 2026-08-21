// what-it-is:   the one place the published base path of the docs site is written down
// what-it-does: exports BASE, the GitHub Pages project subpath the site is served under
// why:          family Astro site standard 14.7 requires the base to be declared once and
//               consumed, never redeclared as a literal. A base that disagrees between the
//               build and a validator passes the check while the live site serves
//               "Site not found", which is the highest-cost misconfiguration in the site plan
// used-by:      site/astro.config.mjs (`base`), and, once they land, the generator's emitted
//               routes (scripts/gen-site.mjs) and the rendered-link guard's default base
//               (scripts/check-rendered-links.mjs)
//
// Two duplications of this value are sanctioned by 14.7 because they are not consumed
// config: a test that value-pins the expected base, and the sitemap URL in
// site/public/robots.txt (Astro copies public/ verbatim, so it cannot be templated).
//
// When the shared @product-on-purpose/astro-docs-preset lands (family decision A-2),
// `base` moves into the preset call and this module is retired.
export const BASE = "/critique-skills";
