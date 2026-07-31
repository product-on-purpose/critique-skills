# The bench

Every quality claim this library makes is a computed number or it is not made. The bench is what
computes it: a deterministic seeded-defect corpus, a scoring module that reads only manifests and
run envelopes, and a frozen baseline to compare against.

This document is the design, frozen at phase A4 step 1. The corpus and the modules do not exist
yet; the harness implementation stage builds them exactly as specified here. Sections marked
**(next stage)** describe an interface that is frozen but unbuilt.

- Domain-plugin API and the worked toy example: [`generator/README.md`](generator/README.md)
- Ground-truth record per artifact: [`generator/manifest.schema.json`](generator/manifest.schema.json)
- Output format every run produces: [`../contract/README.md`](../contract/README.md)
- Why the tolerance rules are shaped this way:
  [ADR 0015 (location tolerance: per artifact type)](../docs/internal/decisions/0015-location-tolerance-per-artifact-type.md)

## Layout

```
bench/
  README.md                     this file
  generator/                    the deterministic corpus generator and its domain plugins
  metrics/                      recall, precision, consistency, and the location resolvers
  baseline/                     frozen generic prompt and its runner
  corpus/                       generated artifacts and their manifests
    <domain>/<recipe>.<ext>
    <domain>/<recipe>.manifest.json
    corpus.lock.json            root seed, generator version, sha256 of every manifest
  results/
    <run-set>/*.json            contract-valid run envelopes, one per skill per artifact per run
    <run-set>/results.json      the computed numbers, machine-readable
```

Nothing in `corpus/` is hand-edited, ever. It is generator output, and a hand edit breaks the
determinism check on the next CI run, which is the intended behaviour.

## Corpus design

21 scored artifacts across the six launch domains, plus 3 unscored `toy` fixtures.

| Domain | Skill | Status | Artifacts | Clean | Artifact type | Namespaces |
|---|---|---|---|---|---|---|
| clarity | critique-clarity | core | 4 | 1 | `markdown-prose` | `PLAIN`, `WILLIAMS` |
| accessibility | critique-accessibility | core | 4 | 1 | `html` | `WCAG` |
| usability | critique-usability | core | 4 | 1 | `html` | `NNG` |
| docs | critique-docs | stretch | 3 | 1 | `markdown-tree` | `DIATAXIS` |
| microcopy | critique-microcopy | stretch | 3 | 1 | `string-list` | `NNG` |
| argument | critique-argument | stretch | 3 | 1 | `markdown-prose` | `TOULMIN` |
| toy | none | fixture | 3 | 1 | `markdown-prose` | `TOY` |

This satisfies S-03 AC-3 (at least 20 artifacts, at least 3 per core domain, at least 1 clean per
core domain) with margin, and S-05's per-skill floor of at least 3 artifacts including at least 1
clean. Clean artifacts are not padding: they are the only place a false positive can be observed
without a human adjudicating whether an unplanted finding is genuine.

`critique-microcopy`'s artifact type depends on S-05 OQ-2, which the microcopy pipeline decides. If
it chooses bare string lists, the type is `string-list` and the item-index rule applies. If it
chooses annotated context, the type becomes `markdown-prose` with one string per paragraph and the
paragraph rule applies unchanged. Both rules are specified below, so the pipeline's decision does
not reopen this design.

### Invariants

The generator enforces these at build time and CI re-checks them. Several are load-bearing for the
tolerance rules, which is the point: a tolerance that depends on the corpus staying a certain shape
must be paired with a constraint that keeps it that shape.

| Invariant | Why |
|---|---|
| At most 6 paragraphs per section in `markdown-prose` and `markdown-tree` | Caps what a heading-only location can be credited for, see the tolerance rules |
| At most one planted defect per criterion per section, or per top-level `<section>` in HTML | Makes the greedy match assignment unambiguous in practice |
| Every element of an injectable class carries a content-derived `id`, in clean and seeded artifacts alike | An exact location is always available, and an `id` never signals a plant |
| Recipe ids and paths reveal nothing: no criterion, no count, no `clean` or `defect` token | The artifact path reaches the skill under test |
| No defect `description` shares a 6-token shingle with its artifact | S-03 AC-8: the defect must not be findable by string search |
| Every artifact has a schema-valid manifest, and `defects` is present even when empty | An empty array asserts "clean"; a missing key asserts only "not recorded" |
| Artifact bytes are UTF-8, no BOM, LF, one trailing newline, NFC | Byte-identity across platforms |

### Prerequisites

Two repository-level changes the harness stage must make before the first corpus commit.

**1. `.gitattributes`, which does not exist yet:**

```
bench/corpus/** -text
```

Without it, git normalizes line endings on checkout and every recorded `artifact_sha256` is wrong on
Windows. AC-1 cannot pass without this line.

**2. `pytest.ini`, whose `testpaths` currently names only `contract/tests`:**

```
testpaths = contract/tests bench/metrics/tests
```

The five unit-test scenarios S-03 AC-4 requires (perfect run, empty run, duplicate findings,
location-tolerance edge, clean-artifact false positive) live in `bench/metrics/tests` and are
invisible to `pytest` until that line changes.

The `bench` tree is a package rooted at the repository root, matching `contract/`: every module has
an `__init__.py` and every entry point is `python -m bench.<module>`. `jsonschema` is already the
single permitted runtime dependency in `requirements.txt`, and the bench adds none.

### Content and licensing

Corpus text is original generated content about invented subject matter: a fictional municipal
utility, a fictional SaaS console, a fictional documentation set. It contains no reproduced rubric
text, no real product names, and no third-party prose, honouring the paraphrase policy in
[ADR 0006 (copyright paraphrase policy)](../docs/internal/decisions/0006-copyright-paraphrase-policy.md).
Criterion identifiers appear in manifests, never in artifacts.

> **Corpus license.** The contents of `bench/corpus/`, both the generated artifacts and their
> manifests, are licensed under the
> [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
> You may copy, redistribute, adapt, and build on them for any purpose, including commercially,
> provided you give appropriate credit to the critique-skills project and indicate whether changes
> were made. This differs from the rest of the repository, which is Apache-2.0. See
> [ADR 0005 (licensing: Apache-2.0 repo, CC-BY-4.0 corpus)](../docs/internal/decisions/0005-licensing-apache-and-cc-by.md).

---

## Location tolerance

This is the S-03 OQ-1 answer. Reasoning is in
[ADR 0015 (location tolerance: per artifact type)](../docs/internal/decisions/0015-location-tolerance-per-artifact-type.md);
the rules themselves are normative here.

A finding's `location` is free text, by
[ADR 0012 (location grammar)](../docs/internal/decisions/0012-location-grammar-freetext-plus-reserved-selector.md).
A manifest's location is structured. Scoring bridges them in two steps:

1. **Resolve.** Parse the finding's free text into a set of anchors, using the artifact itself as
   the vocabulary. The scorer re-derives the artifact's structure from its bytes, after checking
   them against `artifact_sha256`, so the manifest carries an anchor and not a line map.
2. **Compare.** Apply the artifact type's tolerance to decide whether a resolved anchor names the
   same place as the planted one.

Tolerance is keyed on `artifact_type`, not on the skill. Two skills critiquing the same artifact
type are scored by the same rule, which is what makes a cross-domain comparison mean anything.

### What a hit needs, and where each part comes from

Scoring one defect as hit or miss reads exactly these inputs, and the manifest is required to carry
every one of them that the artifact bytes cannot supply. Checked field by field against
`manifest.schema.json` at the contract freeze.

| Input | Source | Notes |
|---|---|---|
| Criterion to match | `defects[].criterion` | Exact string equality against `finding.criterion` |
| Which tolerance rule applies | `artifact_type` | Per artifact, not per domain or skill |
| The planted anchor | `defects[].location`, per `kind` | `paragraph`, `heading_path`, `css`, `element_id`, `item_index` and `item_key`, or `page_path` |
| The page, for `markdown-tree` | `artifact` | One artifact is one page |
| The vocabulary to resolve a finding into | The artifact bytes | Re-derived by the scorer after checking `artifact_sha256` |
| Which envelopes belong to this artifact | `artifact_sha256` against `run.artifact_sha256` | The join; the path is a convenience |
| The claims to score | `findings[].location` plus `instances[].location` | A finding with `n` instances is `n+1` claims |

Two fields are deliberately not inputs. `defects[].severity_expected` is recorded and unscored in
v0.1, and `defects[].description` is meta-language for a human reader, never matched against
anything, because matching on it would reward a skill for guessing the generator's wording.

`sentence` is recorded and unscored, so a truth of kind `paragraph` needs only `paragraph`; the
enclosing section is re-derived from the artifact rather than read from the manifest, which is why
`heading_path` is optional on that kind rather than required.

**Tolerance is not a constant. It is a function of whether adjacency carries meaning.** Prose
paragraphs are adjacent in meaning, so a defect can honestly be described as sitting a paragraph
either side of where it was planted. Items in a string list are not adjacent in meaning: item 4 and
item 5 are unrelated strings, and crediting one for the other would be crediting a wrong answer.
That principle, not a taste for round numbers, sets every window below.

### The block parser (normative)

Used by `markdown-prose` and `markdown-tree`. The metrics module owns this definition; the
generator asserts its own addresses against it at build time.

A blank line contains only whitespace. Blocks are maximal runs of non-blank lines separated by blank
lines, except that a fenced code block (opened by ``` or `~~~`) runs to its closing fence regardless
of blank lines inside it. A block is a **paragraph** unless, after up to 3 leading spaces, its first
line begins with any of:

`#` plus a space (ATX heading), `-` `*` `+` plus a space or a digit run plus `.` or `)` plus a space
(list), `>` (blockquote), ``` or `~~~` (fenced code), `|` (table row), `<` plus a letter, `/`, or `!`
(HTML block), or four spaces or a tab (indented code). A two-line block whose second line is all `=`
or all `-` is a setext heading, not a paragraph.

- **Paragraph index** is the 1-based position among paragraph blocks in document order.
- **Heading path** for a block is the titles of its enclosing ATX headings, outermost first, with
  the leading `#` markers, one following space, and any trailing `#` markers removed, then trimmed.
- **Heading comparison** normalizes: NFC, casefold, collapse internal whitespace to single spaces,
  trim, then strip trailing characters in `.,:;!?`.

### `markdown-prose` and `markdown-tree`

**Resolution.** From the normalized location text, extract:

| Anchor | Recognized as |
|---|---|
| Paragraph number | `paragraph <n>`, `para <n>`, `paragraph <ordinal>`, `<ordinal> paragraph` |
| Line number | `line <n>`, `lines <n>-<m>`, mapped to the paragraph blocks those lines fall in |
| Section by number | `section <n>`, meaning the nth level-2 heading in document order |
| Section by title | a heading title in backticks or quotes, or the longest heading title of at least 4 characters appearing as a substring of the location text and matching exactly one heading |

`<ordinal>` is a frozen table: `first` through `twentieth`, plus `last`. No locale, no inflection
library. When a section anchor is present, a paragraph ordinal is read as an ordinal **within that
section**; otherwise it is read document-wide. This is why the manifest records both the
document-wide `paragraph` and the `heading_path`.

**Tolerance, for a truth of kind `paragraph`.** Resolve the finding to a set of paragraph indices:

- a paragraph anchor at index `p` contributes `{p-1, p, p+1}`;
- a section anchor contributes every paragraph index under that heading, including nested
  subsections;
- when both are present, the window is **clipped to the named section**, because a finding that
  asserted a section should be held to it;
- when neither is present, the location is **unresolvable**.

HIT if `truth.paragraph` is in the resolved set.

**Tolerance, for a truth of kind `heading-path`.** HIT if the finding resolves a section anchor
whose normalized title equals the last element of `truth.heading_path` (and, when the finding gives
a fuller path, that path matches as a suffix), or if the finding resolves a paragraph index whose
block is immediately before or immediately after the heading in block order.

**Sentence index is recorded and not scored.** The manifest carries it for human review and for a
finer v0.2 tolerance. Requiring it in v0.1 would score a correct paragraph-level finding as a miss.

**Why heading-only locations are credited.** "Section 2, hero banner" is the methodology's own
example of a good location, so rejecting it would make the metric disagree with the constitution.
The over-credit it buys is bounded by the corpus invariant of at most 6 paragraphs per section: a
heading-only location can be worth at most a 1-in-6 guess, uniformly, by construction. **The
tolerance rule and the generator constraint are one design.** Changing either without the other
silently changes what every published number means.

`markdown-tree` adds one step in front: the finding must not name the wrong page. One artifact is
one page, so the page a truth sits on is the manifest's own `artifact`, and the manifest records a
`page_path` only for a truth of kind `page-path`, where the page is the whole of what the defect is
about. A page anchor in a finding is a path appearing in the location text, compared after
normalizing separators to `/` and with a trailing `.md` optional.

- For a truth of kind `page-path`, resolving the page **is** the match.
- For any other truth kind, a finding that resolves a page anchor must resolve it to this artifact,
  and is a MISS otherwise; a finding that names no page is not penalized for it, because it was
  handed one page and had no reason to name it. Then apply the `markdown-prose` rule.

The asymmetry matters: requiring every `markdown-tree` finding to name its page would score almost
every correct finding as a miss, and ignoring a page anchor entirely would credit a finding that
pointed at a different page.

### `html`

**Resolution.** Parse the artifact with `html.parser` into an element tree, recording for each
element its tag, `id`, classes, structural CSS path, and document position. Then extract:

| Anchor | Recognized as |
|---|---|
| Element id | a `#id` token, or a bare token equal to a known `id` |
| CSS selector | a quoted or backticked selector, resolved by a bounded engine: tag, `#id`, `.class`, descendant, child, and `:nth-of-type` only |
| Element by kind and ordinal | `the <ordinal> <noun>`, over a frozen noun table: link to `a`, image to `img`, button to `button`, heading to `h1` through `h6`, field to `input`, `select`, `textarea`, table to `table`, list to `ul`, `ol` |
| Element by content | a quoted string of at least 8 characters that is the text content of exactly one element |

A selector outside the bounded engine is unresolvable. The corpus never records one outside it, so
the bound costs no ground truth.

**Tolerance.** HIT if a resolved node is the truth node, an ancestor of it at element distance 1 or
2, or a descendant of it at distance 1.

The asymmetry is deliberate. Naming the containing `<figure>` for an `<img>` with a bad `alt` is a
navigable location; naming `<body>` is not, and two levels is where that line falls in the corpus's
own markup. Naming a child, the `<span>` inside the offending `<button>`, is still the same control.

Because the generator gives every injectable element a content-derived `id`, the exact-match path is
always available to a skill that wants it, and the tolerance is a fallback rather than the norm.

### `string-list`

**Resolution.** Parse the artifact into an ordered list of `(key, value)` pairs. Extract:

| Anchor | Recognized as |
|---|---|
| Item number | `item <n>`, `string <n>`, `message <n>`, `<ordinal> item` |
| Item key | a token equal to a known key, compared case-sensitively |
| Item content | a quoted substring of at least 8 characters matching exactly one value |

**Tolerance: zero.** HIT only if a resolved index equals `truth.item_index` exactly, or a resolved
key equals `truth.item_key` exactly. Adjacency in a string list carries no meaning, so there is no
neighbourhood to be generous about.

Every item has a position, so a truth is always kind `item-index` and carries `item_index`; a keyed
list records `item_key` beside it rather than instead of it. There is no `item-key` anchor kind, and
the two fields are two ways to name one item, not two kinds of item.

### Unresolvable locations

A location that yields no anchor, "throughout the document", "the copy generally", is a MISS for
recall and counts against precision. This is not a penalty bolted on: it is the methodology's own
Part 1 gate ("if a finding cannot name a location, the framework fails") expressed as arithmetic. A
skill that cannot say where has not made a falsifiable claim.

---

## Metrics

Computed by `bench/metrics/` from manifests plus contract-valid run envelopes, and from nothing
else. All arithmetic accumulates in integers; a ratio is formed once, at the end, and reported to
three decimal places.

### Claims and assignment

A **claim** is one `(criterion, location)` pair asserted by a run. A finding with no `instances`
contributes one claim. A finding with `n` instances contributes `n+1` claims, one per location.
This makes the contract's two expressions of a recurring breach, `n` separate findings or one
finding with an instance list, score identically, which the contract requires them to be
interchangeable for.

A planted defect is claimed by **at most one** claim. Assignment is greedy over a deterministic
order: candidate pairs are sorted by `(criterion, truth anchor key, claim anchor key, finding id)`,
and each candidate is taken when both sides are still unclaimed. Duplicate findings therefore earn
recall once and cost precision every time, which is the intended incentive. Greedy rather than
maximum-cardinality matching is a documented simplification, safe here because the corpus plants at
most one defect per criterion per section; if collisions are ever observed, maximum matching is a
v0.2 refinement that can only raise scores.

**Criterion match is exact string equality.** A finding that correctly identifies a defect under the
wrong criterion ID is a miss and a false positive. This is conservative on purpose: a criterion ID
is the library's unit of accountability, and crediting near-misses would make the ID meaningless.

### Recall

```
recall = matched planted defects / total planted defects
```

Over seeded artifacts only. A clean artifact contributes zero to both sides, so it is excluded from
the denominator rather than scored as a perfect or a failed run.

A planted defect is matched when some claim has the same criterion ID and a location that resolves
within that artifact type's tolerance to the planted location.

### Precision (conservative)

```
precision = claims matched to a planted defect / all claims emitted
```

Over every artifact, clean ones included. The denominator is claims derived from `findings[]` in the
envelope; suppressed findings are excluded, because a suppressed finding is never shown to a user
and cannot mislead one.

**A finding that is genuinely correct but was not planted counts against precision.** v0.1 has no
adjudication step, so there is no honest way to tell a real unplanted defect from a hallucinated
one. This understates skill quality by an unknown amount and is recorded as S-03 OQ-2, accepted for
v0.1 with human adjudication tooling on the v0.2 roadmap. It is stated in every results table rather
than in a footnote, because a number this conservative is only defensible if it is labelled.

### False positives on clean artifacts

```
clean_fp_rate = claims on clean artifacts / number of clean artifacts
```

Reported separately, as a mean claims-per-clean-artifact, because precision aggregated over the
whole corpus hides the behaviour that matters most to a user: what the skill says about a document
with nothing wrong with it. A skill with strong recall and a clean-artifact rate above 1 is a skill
that invents work.

### Consistency

k=5 runs of the same skill against the same artifact on the same pinned model.

```
consistency = mean over the 10 unordered pairs of J(A, B)
J(A, B)     = |M| / (|A| + |B| - |M|)
```

where `A` and `B` are the two runs' claim sets and `M` is a maximal matching between them under the
same predicate recall uses: same criterion ID, locations within tolerance. When both sets are empty,
`J = 1.0`: two runs that both correctly found nothing agree perfectly.

The matching must be **symmetric**, or the result is not a similarity measure. Candidate pairs are
sorted by `(criterion, min(key_a, key_b), max(key_a, key_b))` before the greedy pass, so
`J(A, B) = J(B, A)` by construction. This is the easiest thing in the module to get wrong and the
hardest to notice.

Two runs that name the same paragraph differently, "Section 2, second paragraph" and "line 84",
score as agreeing, because both resolve to the same anchor. This is the cost ADR 0012 anticipated
when it left `location` as free text, paid down by the resolver rather than left in the numbers.

A second figure is reported beside it:

```
consistency_exact = mean pairwise |A ∩ B| / |A ∪ B| on (criterion, canonical key) sets, zero tolerance
```

The canonical key is the paragraph index when one resolves, else `H:` plus the normalized heading
path, else `?:` plus the normalized location text; for HTML the element id, else the structural CSS
path; for string lists the item index, else the key. Unresolvable locations canonicalize to their
normalized text, so two runs that are both vague agree with each other: consistency measures
repeatability, not quality.

The gap between the two figures is the location-phrasing instability of the skill, and it is worth
publishing on its own.

### Baseline comparison (next stage)

`bench/baseline/prompt.txt` holds the frozen generic prompt text, unchanged for the life of v0.1.0.
`bench/baseline/` runs it against the same artifacts on the same pinned models and maps its free
output to the contract by a documented, fixed post-processing rule. Baseline envelopes carry
`skill: "baseline-generic"` and are scored by exactly the same code path as skill envelopes: same
resolver, same tolerance, same assignment. Any change to the prompt text or the mapping rule after
the first published run invalidates the comparison and requires a new run set.

### Results

`bench/results/<run-set>/results.json` carries every computed number for a run set, and the README
results table is generated from it by script with a drift check (S-03 AC-6). No number appears in
any document in this repository that is not present in a committed `results.json`, and no table is
hand-edited. The schema for that file and the table generator are built in the harness stage.

---

## Reproduction

The whole point of the corpus being generated rather than collected is that a sceptical reader can
rebuild it and check the numbers. The full sequence, from a clean checkout **(next stage: these
commands are frozen here and implemented in the harness stage)**:

```
git clone https://github.com/product-on-purpose/critique-skills.git
cd critique-skills

# 1. Rebuild the corpus from seed and confirm it matches what is committed.
python -m bench.generator build --out /tmp/corpus-check
python -m bench.generator verify --corpus bench/corpus

# 2. Confirm no manifest content leaked into any artifact.
python -m bench.generator leak-check --corpus bench/corpus

# 3. Score the committed envelopes against the corpus.
python -m bench.metrics score --corpus bench/corpus --runs bench/results/<run-set> \
    --out bench/results/<run-set>/results.json

# 4. Recompute the published table and confirm it matches the committed one.
python -m bench.report table --results bench/results/<run-set>/results.json --check
```

Step 3 is the one that matters: it takes the committed envelopes, which are the raw output of the
runs, and recomputes every published figure from them. If the recomputed `results.json` differs from
the committed one, the published numbers are wrong.

Requires Python 3.12 and `jsonschema`. No other third-party dependency is permitted without its own
ADR, per
[ADR 0009 (Python and Node toolchain split)](../docs/internal/decisions/0009-python-node-toolchain-split.md).

### What works today

Two checks run against this design rather than against the unbuilt harness. Both were run under Git
Bash on Windows from the repository root:

```
python -c "import json,jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('bench/generator/manifest.schema.json'))); print('manifest schema OK')"

python -c "import json;a=json.load(open('contract/critique-contract.schema.json'));b=json.load(open('bench/generator/manifest.schema.json'));print('noEmDash pattern identical:', a['\$defs']['noEmDash']['pattern']==b['\$defs']['noEmDash']['pattern'])"
```

The second is the manual form of the drift check CI will run. `manifest.schema.json` copies six
definitions from the critique contract (`criterionId`, `sha256`, `artifactPath`, `prose`,
`noEmDash`, `trimmed`) so it validates standalone with no remote reference resolution. The contract
is authoritative; CI compares each copied pattern byte for byte and fails on divergence.

## What the bench does not measure

Stated here so that no reader has to infer it from an absence.

- **Severity agreement.** `severity_expected` is recorded in every manifest and scored by nothing in
  v0.1. Calibration becomes measurable in v0.2 without regenerating the corpus.
- **Unplanted genuine findings.** Counted against precision, not adjudicated. S-03 OQ-2.
- **Evidence quality.** Whether `evidence` is a quotation rather than a characterization is a
  methodology field contract that no schema and no metric can check. It is review-lane, and
  `contract/README.md` says so.
- **Real-world artifacts.** The corpus is generated. It measures whether a skill finds defects of a
  known kind in prose of a known shape. It does not measure whether the rubric is the right rubric,
  and no benchmark can.
