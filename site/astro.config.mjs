import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import mermaid from 'astro-mermaid';
import { BASE } from '../scripts/site-base.mjs';
import { generate } from '../scripts/gen-site.mjs';

// Generate the content tree before defineConfig runs. Calling the generator here rather than
// from an npm script is the recipe's contract and site plan decision 2.2: every entrypoint
// regenerates, so astro build, astro dev, astro sync and astro check all see a current tree.
// pm-skills wires generation into its build script only, which leaves `astro dev` serving
// whatever the last build emitted. The cost is a slower config load on every astro invocation,
// which for a site this size is well under a second.
generate();

// The critique-skills documentation site (Astro + Starlight), the fifth site in the
// Product on Purpose family. It lives in this isolated site/ subdirectory so the plugin
// root stays legible as a plugin: skills/, library.json, contract/, and bench/ are
// untouched by the frontend toolchain (family Astro site standard 14.1, Pattern S).
//
// W5. The sidebar below is hand-ordered and is the last thing that shapes routes: W6
// freezes the route list into scripts/route-manifest.txt, after which removing a route
// fails the build.
//
// The base path lives in ../scripts/site-base.mjs and is imported, never repeated
// (14.7). A wrong base does not produce a broken link, it produces "Site not found".
export default defineConfig({
  // GitHub Pages project hosting: https://<org>.github.io/<repo>. Setting `site` is
  // also what makes Starlight auto-register the sitemap (14.2, 14.9).
  site: 'https://product-on-purpose.github.io',
  base: BASE,

  // No `markdown.remarkPlugins` key, deliberately. pm-skills resolves relative .md
  // links with a remark plugin and therefore needs @astrojs/markdown-remark as a direct
  // dependency; this site's generator will emit Starlight-correct links at generation
  // time instead (plan decision 2.3), so neither the plugin nor the dependency exists
  // here. Adding a remarkPlugins key later without that dependency hard-fails config
  // validation under Astro 7.
  integrations: [
    // astro-mermaid MUST come before starlight (integration-order rule, 14.2).
    // autoTheme follows Starlight's light and dark modes. The brand line color and
    // system font mirror pm-skills and the toolkit; the shared preset owns this once
    // it lands.
    mermaid({
      theme: 'default',
      autoTheme: true,
      mermaidConfig: {
        themeVariables: {
          lineColor: '#5C7CFA',
          fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
          fontSize: '14px',
        },
      },
    }),
    starlight({
      title: 'critique-skills',
      description:
        'Rubric-cited, machine-parseable critique skills that produce measured, evidence-graded findings instead of freeform opinion.',
      editLink: {
        // Content lives at site/src/content/docs/. Starlight builds the edit URL as
        // baseUrl plus the file path relative to the Astro project root (site/), so the
        // baseUrl carries the /site/ segment to reach the real repo path. Generated
        // pages (gitignored, rebuilt) must set editUrl explicitly to their true source
        // or to false; W2's generator owns that, and verify-edit-links.mjs (W6) is what
        // stops an auto-derived editUrl pointing at a gitignored path.
        baseUrl: 'https://github.com/product-on-purpose/critique-skills/edit/main/site/',
      },
      customCss: ['./src/styles/custom.css'],

      // THE READER'S ORDER, NOT THE REPOSITORY'S. Install, then what the six skills are, then
      // whether to believe the numbers, then worked examples, then task-oriented how-tos, then
      // reference, then the theory. Project furniture sits at the bottom and Releases is
      // collapsed, because the changelog is 354 lines and nobody navigating a docs site wants it
      // expanded.
      //
      // The four Diataxis quadrants are deliberately NOT the top-level organizing principle even
      // though docs/ is structured that way. Diataxis is right for a documentation set's internal
      // discipline and wrong as a first-time visitor's navigation: "explanation" and "reference"
      // do not describe what a reader wants. Skills, receipts and examples do.
      //
      // Every labelled section wraps `autogenerate` in an `items` array, which Starlight 0.39 and
      // later require. Directory paths are plain content slugs with no docs/ prefix, because the
      // stock docsLoader() mounts site/src/content/docs/ directly (Pattern S).
      sidebar: [
        { label: 'Getting started', items: [{ autogenerate: { directory: 'getting-started' } }] },
        // skills/index.md carries sidebar.order 0 and the six generated pages carry 1 through 6,
        // so autogenerate alone orders this correctly and does not double-list the overview.
        { label: 'The skills', items: [{ autogenerate: { directory: 'skills' } }] },
        { label: 'The receipts', items: [{ autogenerate: { directory: 'receipts' } }] },
        { label: 'Worked examples', items: [{ autogenerate: { directory: 'examples' } }] },
        { label: 'How-to', items: [{ autogenerate: { directory: 'how-to' } }] },
        { label: 'Reference', items: [{ autogenerate: { directory: 'reference' } }] },
        { label: 'Explanation', items: [{ autogenerate: { directory: 'explanation' } }] },
        { label: 'Tutorials', collapsed: true, items: [{ autogenerate: { directory: 'tutorials' } }] },
        { label: 'Contributing', items: [{ autogenerate: { directory: 'contributing' } }] },
        { label: 'Releases', collapsed: true, items: [{ autogenerate: { directory: 'releases' } }] },
      ],
    }),
  ],
});
