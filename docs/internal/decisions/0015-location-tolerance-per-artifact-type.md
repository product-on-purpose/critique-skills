# 0015 - Location tolerance: keyed on artifact type, resolver plus bounded proximity

## TL;DR
- **Decision:** location-match tolerance is defined per **artifact type**, not per skill, in four rules: `markdown-prose` and `markdown-tree` match on paragraph index within plus or minus 1 or on heading path, `html` matches on element id or CSS path with an ancestor window of 2 and a descendant window of 1, and `string-list` matches on exact item index or key with **zero** tolerance. Scoring works in two steps: resolve a finding's free-text location into anchors using the artifact itself as the vocabulary, then compare within the rule. A location that resolves to no anchor is a miss and a false positive.
- **Why:** tolerance is not a constant, it is a function of whether adjacency carries meaning in the artifact type. Paragraphs are adjacent in meaning; list items are not. Keying on artifact type rather than skill means two skills critiquing the same artifact type are scored identically, which is the only way a cross-domain comparison means anything. The generous half of the rule, crediting heading-only locations, is bounded by a **generator constraint** (at most 6 paragraphs per section) rather than by a special case in the matcher.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, build-run P1 bench-architect pass (Claude)

## Context and problem statement

[S-03 (bench-harness spec)](../release-plans/plan_v0.1.0/S-03_bench-harness/spec.md) OQ-1 asks for
"location-tolerance definitions per domain (exact heading path? paragraph index plus or minus 1?)",
to be set during P1 harness design, documented in `bench/README.md`, and reviewed at RC. The
question is a direct consequence of
[ADR 0012 (location grammar)](0012-location-grammar-freetext-plus-reserved-selector.md), which made
`finding.location` free text and named this cost explicitly: "recall and consistency depend on
string matching with a per-domain tolerance, which is a documented approximation and a known source
of measurement noise; S-03 OQ-1 carries that cost."

The stakes are the whole benchmark. S-03 defines recall as the fraction of planted defects found by
"criterion match plus location match within tolerance", and consistency as mean pairwise Jaccard
over `(criterion, location)` sets. Both metrics are functions of this rule. A tolerance set too
tight scores correct findings as misses and publishes numbers that understate every skill uniformly.
A tolerance set too loose credits a skill for gesturing at the right region, and the published
recall stops meaning "found the defect".

Two facts constrain any answer. First, findings arrive as prose, so there is a parsing problem
before there is a comparison problem. Second, the methodology's own gate test is prose based and its
worked example location is "Section 2, hero banner", a section-level location with no paragraph
index in it. A rule that scores that example as a miss would put the metric in disagreement with the
constitution it implements.

## Decision drivers

- The metric must be computable from committed artifacts alone, so a sceptical external reader can
  recompute every published number. That rules out anything requiring a model call or a human in the
  scoring path.
- Every rule has to be paired with something that bounds its generosity, or the number it produces
  is not defensible in public.
- Six launch domains produce four artifact shapes, and two pairs of domains share a shape
  (clarity with argument, accessibility with usability). Per-skill tolerances would let two skills be
  scored by different rules on identical artifacts.
- S-05 OQ-2 leaves `critique-microcopy`'s artifact format undecided between a bare string list and
  annotated context. Whatever is chosen must not reopen this decision.
- The corpus is generated, so a constraint on the corpus is enforceable at build time and verifiable
  in CI, whereas a special case in the matcher is only as good as its tests.
- Python 3.12 stdlib only, per
  [ADR 0009 (Python and Node toolchain split)](0009-python-node-toolchain-split.md). No CSS engine,
  no markdown library, no NLP.

## Considered options

1. **One tolerance for everything, for example "same paragraph or one either side".** Rejected: the
   rule is meaningless for HTML, where there is no paragraph, and actively wrong for string lists,
   where crediting item 5 for a defect planted in item 4 credits a wrong answer. Adjacency is a
   property of the artifact type, not of documents in general.
2. **Per-skill tolerance, each skill pipeline setting its own.** Rejected: it lets a skill tune its
   own scoring, which is the one thing a benchmark must not permit, and it makes clarity and
   argument incomparable despite critiquing identical artifact types.
3. **Exact match only, no tolerance.** Rejected: it contradicts the methodology's own example
   location, penalizes correct section-level findings, and, because `location` is free text, mostly
   measures phrasing agreement rather than defect detection. It would understate every skill and
   flatter none, which sounds conservative but is really just noisy.
4. **Semantic matching by a model judging whether two locations refer to the same place.** Rejected:
   it makes the benchmark unreproducible, puts a model inside the scoring path for a metric whose
   purpose is to measure models, and cannot be recomputed by a reader from committed files.
5. **Per artifact type, resolver plus bounded proximity, with the generosity bounded by a corpus
   invariant (chosen).**

## Decision outcome

Option 5. The rules are normative in
[`bench/README.md`](../../../bench/README.md), under "Location tolerance"; what follows is the
reasoning, not a second copy of the rules.

**Two-step scoring.** Resolve, then compare. Resolution parses the finding's prose into anchors,
using the artifact itself as the vocabulary: the scorer re-derives the document's block structure,
heading inventory, element tree, or item list from the artifact bytes, after checking them against
the manifest's `artifact_sha256`. That is why the manifest records an anchor and not a line map: the
structure is recoverable from the artifact, so duplicating it in the ground truth would only create
a way for the two to disagree.

**Keyed on `artifact_type`, carried in the manifest.** Not on domain and not on skill. A domain that
later adds a second artifact type gets the right rule with no change to the metrics module.

**The four rules and what bounds each.**

- `markdown-prose` and `markdown-tree`: paragraph index within plus or minus 1, or heading path.
  A section anchor resolves to every paragraph under that heading, which is the generous case;
  it is bounded by the corpus invariant that no section holds more than 6 paragraphs, making a
  heading-only location worth at most a 1-in-6 guess, uniformly, by construction. When a finding
  names both a section and a paragraph ordinal, the plus or minus 1 window is clipped to that
  section: a finding that asserted a section is held to it, which closes the cross-boundary
  over-credit.
- `html`: element id, CSS path, element kind with an ordinal, or unique text content. Ancestors
  count at distance 1 or 2, descendants at distance 1. The asymmetry reflects navigability: the
  containing `<figure>` of an `<img>` with a bad `alt` is a location a reader can use, `<body>` is
  not. It is bounded by the generator assigning a content-derived `id` to every element of an
  injectable class in clean and seeded artifacts alike, so an exact match is always available and
  the tolerance is a fallback rather than the normal path.
- `string-list`: exact item index or exact key, zero tolerance. Nothing to bound, because nothing is
  granted.
- `markdown-tree` additionally requires the page to resolve before the prose rule applies.

**Unresolvable locations are misses and false positives.** "Throughout the document" produces no
anchor and is scored as no location. This is the methodology's Part 1 gate expressed as arithmetic
rather than as an extra penalty invented for the bench.

**Sentence index is recorded and not scored.** Manifests carry it; v0.1 matching ignores it.
Requiring sentence agreement would score a correct paragraph-level finding as a miss, and the field
costs nothing to record now and would cost a corpus regeneration to add later.

**Consistency uses the same predicate.** Mean pairwise Jaccard is computed tolerance-aware,
`|M| / (|A| + |B| - |M|)` over a maximal matching under the same criterion-plus-tolerance predicate,
with candidate pairs sorted symmetrically so `J(A, B)` equals `J(B, A)`. A plain exact-key Jaccard
is reported beside it as `consistency_exact`, and the gap between them is the skill's
location-phrasing instability, published on its own. Using two different match rules for recall and
consistency would have made the two numbers uncomparable.

**RC review question**, per S-03 OQ-1: did any launch skill produce locations the resolver could not
parse at a rate high enough to distort its numbers? The `consistency_exact` gap and the count of
unresolvable locations are both reported per skill precisely so this question has data rather than
opinion behind it at RC.

## Consequences

**Positive:** every published number is recomputable from committed files by anyone, with no model
and no human in the scoring path. Two skills on the same artifact type are scored identically.
Locations that the methodology holds up as good examples score as hits. The generous case is bounded
by a build-time constraint that CI verifies, rather than by a matcher special case that only its
tests defend. S-05 OQ-2 is pre-answered: whichever microcopy format the pipeline picks, a rule
already exists for it.

**Negative:** the tolerance rule and the generator are now one design. The plus or minus 1 window and
the heading-path credit are only defensible while the corpus holds at most 6 paragraphs per section
and at most one defect per criterion per section; changing either constraint silently changes what
every published recall figure means. This coupling is recorded as an invariant in `bench/README.md`
and enforced by `Domain.validate()`, but it is a coupling, and a future contributor who relaxes a
generator constraint to make an artifact read better will move the metric without touching the
metrics module.

The resolver is a parser for prose written by a model, which means it will meet phrasings it does
not recognize and score them as unresolvable. That understates recall by an unknown amount. It is
measured rather than hidden: unresolvable-location counts are reported per skill, so the size of the
approximation is visible next to the numbers it affects.

Greedy assignment rather than maximum-cardinality matching can, in principle, leave a matchable
plant unmatched when two claims contend for overlapping truths. The corpus invariant of at most one
defect per criterion per section makes this rare rather than impossible, and maximum matching is a
v0.2 refinement that can only raise scores.

**Neutral:** the four artifact types are now a closed set that the manifest schema enumerates.
Adding a fifth is a manifest minor version and requires a tolerance rule here first, which is the
intended amount of friction.

## Implementation sites

- `bench/README.md`, "Location tolerance": the normative rules, the block parser definition, and the
  per-type resolver tables. Written.
- `bench/generator/manifest.schema.json`: `$defs/location` and `$defs/artifactType` encode the anchor
  vocabulary and the closed type set. Written.
- `bench/generator/README.md`: the corpus invariants the tolerance depends on, and `Domain.validate()`
  as the place they are enforced. Written.
- Not yet created: `bench/metrics/locate.py` (resolvers), `bench/metrics/match.py` (tolerance
  predicates and symmetric greedy assignment), `bench/metrics/score.py` (recall, precision,
  consistency), and their unit tests covering the five scenarios S-03 AC-4 names, of which
  "location-tolerance edge" is this decision's test.
