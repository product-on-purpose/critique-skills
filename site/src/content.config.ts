import { defineCollection } from 'astro:content';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

// Pattern S (family Astro site standard 14.1): rendered content lives in
// site/src/content/docs/ and is read by the stock Starlight docsLoader() with no
// arguments. A custom glob loader over the repo-root docs/ tree is prohibited; the
// generator (scripts/gen-site.mjs, W2) reads docs/ and writes into this tree instead.
//
// The schema is stock docsSchema() for now. If generated pages later need extra
// frontmatter fields, extend it here, and do NOT re-declare fields docsSchema()
// already defines: pm-skills records that shadowing the built-in `draft` field in
// extend drops every route from the production filter and kills the build.
export const collections = {
  docs: defineCollection({ loader: docsLoader(), schema: docsSchema() }),
};
