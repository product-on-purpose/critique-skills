# The bench generator: domain-plugin API

This is the interface a skill pipeline builds against to contribute its bench domain module. It is
the design, frozen at phase A4 step 1. The modules it describes do not exist yet; the harness
implementation stage (A4 step 2) creates them exactly as specified here, and any deviation is a
change to this document first.

Read [`bench/README.md`](../README.md) for corpus design, the location-tolerance rules, and the
metric definitions. Read [`manifest.schema.json`](manifest.schema.json) for the ground-truth record
this pipeline emits. Read
[ADR 0015 (location tolerance: per artifact type)](../../docs/internal/decisions/0015-location-tolerance-per-artifact-type.md)
for why the tolerance rules are shaped the way they are.

## What a domain module owes the harness

A domain module is one Python file. It declares five things and nothing else:

1. **Vocabulary.** Frozen word banks the generated prose is assembled from.
2. **Structure.** Per recipe, the exact shape of the artifact, declared as data.
3. **Composition.** A pure function from a seeded stream plus a declared shape to a composed
   artifact, with no defects in it.
4. **Injectors.** One callable per criterion ID, each of which takes a clean composition and
   returns a composition with that criterion breached at one named slot.
5. **Recipes.** The artifacts this domain contributes to the corpus, each naming its shape and its
   planted defects with declared targets.

Everything else, seeding, addressing, hashing, manifest writing, leak checking, and determinism
verification, belongs to the harness. A domain module never opens a file, never touches the clock,
never imports `random`, and never writes a manifest.

## The two rules that shape everything else

**Structure is declared; prose is generated.** The seeded stream chooses words. It never chooses how
many sections exist, how many paragraphs each holds, or where a defect goes. Those are recipe data.
Consequences: every plant target is statically checkable before a byte is generated, a human can
review the ground truth without running anything, and rotating the corpus seed changes the prose
without moving a single defect.

**Slots are identities; indices are derived.** Every composed unit carries a slot id assigned at
creation (`s2.p1`), and that id never changes. Paragraph numbers, element positions, and item
indices are computed from the final composition after every injection has run. An injector that
inserts a block therefore cannot corrupt the recorded location of a defect planted earlier, because
no location has been recorded yet.

## The pipeline

Six stages, in this order, per artifact.

| Stage | Input | Output | Who |
|---|---|---|---|
| 1. Resolve | recipe id | recipe, artifact seed | harness |
| 2. Compose | seed, declared shape | clean composition | domain `compose` |
| 3. Inject (structure phase) | composition, structural plants | composition | domain injectors |
| 4. Inject (text phase) | composition, text plants | composition | domain injectors |
| 5. Address | final composition, slots | one `Location` per defect | domain `address` |
| 6. Emit | composition, defects | artifact bytes, manifest | harness |

Stage 5 running after stage 4 is the whole point of slots. Within a phase, injections apply in a
canonical order: sorted by `(target.section, target.block, criterion)`. Across phases, structural
injectors always run first, because a text injector's slot must still exist when it runs.

The harness verifies before it writes:

- The rendered artifact re-parses to the same addresses the domain reported (round-trip check).
- Every `Location` validates against the `location` subschema of `manifest.schema.json`.
- The leak check passes (see below).
- The corpus invariants hold (see `bench/README.md`).

## Determinism

Byte-identical output for identical `(seed, domain, recipe)`, on any machine, any OS, any run. The
generator is the evidence base for every published number, so this is not a quality goal, it is a
correctness property with a CI job attached.

### Seeding

One string constant is the root of the whole corpus:

```python
CORPUS_SEED = "critique-skills/bench/corpus/v1"
PERSON = b"critique-bench"
```

All key material derives from it by blake2b, which is stdlib, byte-exact by specification, and
identical on every platform and every Python version:

```python
def root_seed() -> bytes:
    return hashlib.blake2b(CORPUS_SEED.encode("utf-8"), digest_size=16, person=PERSON).digest()

def derive(parent: bytes, *parts: object) -> bytes:
    h = hashlib.blake2b(digest_size=16, person=PERSON)
    h.update(parent)
    for part in parts:
        h.update(b"\x1f")                          # unit separator, so ("ab","c") != ("a","bc")
        h.update(str(part).encode("utf-8"))
    return h.digest()
```

An artifact's seed is `derive(root_seed(), domain, recipe_id)`, recorded in its manifest as 32
lowercase hex characters. That seed alone regenerates the artifact: nothing in the pipeline reaches
back to the root. Within an artifact, every subtree draws from its own derived child stream
(`rng.child("para", section, index)`), so editing one recipe changes only its own bytes and adding a
section does not shift the prose of the sections beside it. Review diffs stay small on purpose.

Rotating `CORPUS_SEED` regenerates every artifact and invalidates every published number. It
requires its own ADR.

### The PRNG

`bench/generator/rng.py` defines `SeededRng`, a counter-based deterministic byte stream over
blake2b. The `random` module is forbidden in the entire `bench/` tree. Mersenne Twister seeding and
the internals of `random.choice` and `random.shuffle` are CPython implementation details that have
changed between versions; a hash-defined stream cannot change, because the hash is a specification.

```python
class SeededRng:
    """Counter-mode blake2b. Fully specified by the hash, so stable across versions forever."""

    def __init__(self, seed: bytes) -> None:
        self._seed, self._counter, self._buf = seed, 0, b""

    def _refill(self) -> None:
        h = hashlib.blake2b(digest_size=32, person=PERSON)
        h.update(self._seed)
        h.update(self._counter.to_bytes(8, "big"))
        self._counter += 1
        self._buf += h.digest()

    def bits(self, k: int) -> int:
        """k uniform bits, big-endian, taken from whole bytes and right-shifted."""
        nbytes = (k + 7) // 8
        while len(self._buf) < nbytes:
            self._refill()
        chunk, self._buf = self._buf[:nbytes], self._buf[nbytes:]
        return int.from_bytes(chunk, "big") >> (8 * nbytes - k)

    def below(self, n: int) -> int:
        """Uniform integer in [0, n) by rejection sampling. No modulo bias, no floats."""
        if n < 1:
            raise ValueError("below(n) requires n >= 1")
        if n == 1:
            return 0
        k = (n - 1).bit_length()
        while True:
            v = self.bits(k)
            if v < n:
                return v

    def choice(self, seq):          return seq[self.below(len(seq))]
    def shuffle(self, items):       # Fisher-Yates, descending, in place
        for i in range(len(items) - 1, 0, -1):
            j = self.below(i + 1)
            items[i], items[j] = items[j], items[i]
    def sample(self, seq, k):       # shuffle a copy, take a prefix
        pool = list(seq); self.shuffle(pool); return pool[:k]
    def child(self, *parts) -> "SeededRng":
        return SeededRng(derive(self._seed, *parts))
```

Domain modules use `below`, `choice`, `shuffle`, `sample`, and `child`. Nothing else. There is no
float API on purpose.

### Forbidden constructs

A lint job greps the `bench/` tree for these and fails the build. The right-hand column is the only
accepted alternative.

| Forbidden | Why it breaks byte-identity | Use instead |
|---|---|---|
| `import random`, `secrets`, `os.urandom` | unseeded or version-dependent | `SeededRng` |
| `hash()`, iterating a `set` or `frozenset` | `PYTHONHASHSEED` reorders string sets | iterate `sorted(...)`, or use a tuple |
| `time`, `datetime.now`, `date.today` | wall clock | `CORPUS_EPOCH = "2026-01-01"`, a frozen constant |
| `locale.*`, `str.format` with locale, `strxfrm` | environment dependent | explicit format strings, codepoint `sorted` |
| `os.listdir`, `glob`, `Path.iterdir`, `Path.rglob` | filesystem order is not defined | the explicit `registry.DOMAIN_MODULES` tuple |
| float arithmetic in generated content | platform rounding | integer arithmetic only |
| `uuid4`, `id()`, default `repr` of an object | address or entropy dependent | slot ids from the composition path |
| `os.path.join` for a recorded path | backslashes on Windows | `PurePosixPath`, forward slashes always |
| `open(p, "w")` without `newline=` | Python rewrites LF to CRLF on Windows | `open(p, "w", encoding="utf-8", newline="\n")` |

### Output bytes

Artifacts and manifests are written UTF-8, no BOM, LF line endings, exactly one trailing newline,
NFC-normalized. Manifests serialize as
`json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"`, so key order is a property of
the schema rather than of the code that built the dict.

`bench/corpus/**` requires a `.gitattributes` entry before the first corpus commit, or git will
normalize line endings on checkout and every recorded sha256 will be wrong on Windows:

```
bench/corpus/** -text
```

This is a hard prerequisite for AC-1, not a nicety. It is listed in `bench/README.md` under corpus
prerequisites.

### Discovery

There is no discovery. `bench/generator/registry.py` holds one explicit ordered tuple:

```python
DOMAIN_MODULES = (
    "bench.generator.domains.toy",
    "bench.generator.domains.clarity",
    "bench.generator.domains.accessibility",
    "bench.generator.domains.usability",
    "bench.generator.domains.docs",
    "bench.generator.domains.microcopy",
    "bench.generator.domains.argument",
)
```

A domain that is not listed does not exist. A skill gated out of `library.json` at RC keeps its
corpus and its published numbers, because the corpus does not depend on the plugin manifest.

### Verification in CI

The determinism job generates the corpus twice into two scratch directories and compares hashes,
with two twists that catch the failures determinism jobs usually miss:

- The two runs use different `PYTHONHASHSEED` values (`0` and `12345`). Identical output proves no
  set or dict iteration order leaked into the bytes.
- The job runs on a Linux runner and a Windows runner and compares across them. Identical output
  proves no line-ending or path-separator dependence.

## The API

`bench/generator/api.py`. Types are shown with the fields a domain module touches.

```python
Phase = Literal["structure", "text"]

@dataclass(frozen=True, slots=True)
class Target:
    """Where a plant goes, declared in the recipe. Statically checked against the shape."""
    section: int                     # 1-based section ordinal
    block: int | None = None         # 1-based paragraph ordinal within the section
    item: int | None = None          # 1-based list item, string-list domains
    element: str | None = None       # element slot id, html domains

@dataclass(frozen=True, slots=True)
class Plant:
    criterion: str                   # must match the contract's criterion ID grammar
    target: Target
    severity_expected: int           # 1 to 4

@dataclass(frozen=True, slots=True)
class Recipe:
    id: str                          # opaque slug, unique in the domain, reveals nothing
    shape: Mapping[str, object]      # declared structure, domain-defined keys
    plants: tuple[Plant, ...]        # empty tuple means a clean artifact

@dataclass(frozen=True, slots=True)
class Location:
    """Mirrors the location object in manifest.schema.json, field for field."""
    kind: str
    text: str
    paragraph: int | None = None
    sentence: int | None = None
    heading_path: tuple[str, ...] = ()
    css: str | None = None
    element_id: str | None = None
    item_index: int | None = None
    item_key: str | None = None
    page_path: str | None = None

@dataclass(frozen=True, slots=True)
class InjectionResult:
    composed: object                 # the new composition; never mutate the input in place
    slot: str                        # the slot the defect now lives at
    severity_expected: int
    description: str                 # meta-language only, never a quote of the artifact
    sentence: int | None = None      # optional refinement, markdown domains

Injector = Callable[[SeededRng, object, Target], InjectionResult]

@dataclass(frozen=True, slots=True)
class Domain:
    name: str                        # slug, matches the owning skill's suffix
    artifact_type: str               # markdown-prose | markdown-tree | html | string-list
    extension: str                   # ".md", ".html", ".json"
    namespaces: tuple[str, ...]      # criterion namespaces this domain seeds
    compose: Callable[[SeededRng, Mapping[str, object]], object]
    render: Callable[[object], str]
    address: Callable[..., Location]
    injectors: Mapping[str, Injector]
    recipes: tuple[Recipe, ...]
```

### Registering an injector

The decorator keys the injector by criterion ID and records its phase. A module-local dict, never a
global, so import order cannot matter.

```python
INJECTORS: dict[str, Injector] = {}

def injector(criterion: str, *, phase: Phase = "text"):
    def wrap(fn):
        fn.criterion, fn.phase = criterion, phase
        INJECTORS[criterion] = fn
        return fn
    return wrap
```

Use `phase="structure"` when the injector adds, removes, or reorders composed units. Use the default
`"text"` when it only rewrites the contents of one unit.

### Shared composition models

Domains do not each reinvent a document model. The harness ships one per artifact type, and a domain
module supplies vocabulary, shape, and injectors on top.

| Module | Artifact types | Provides |
|---|---|---|
| `bench/generator/markdown.py` | `markdown-prose`, `markdown-tree` | `Block`, `Document`, `Document.block(slot)`, `heading_path(slot)` (enclosing headings, plus the block itself when it is a heading), `paragraph_index(slot)`, renderer |
| `bench/generator/html.py` | `html` | `Element` tree, content-derived id assignment, CSS path computation, serializer |
| `bench/generator/strings.py` | `string-list` | `StringList` of `(key, value)` pairs, index and key lookup, serializer |

`markdown.Document.paragraph_index` is the generator's copy of the block-parsing rule; the normative
definition lives in the metrics module and is documented in `bench/README.md`. The round-trip check
at stage 6 is what keeps the two honest: the generator asserts that re-parsing its own rendered
output with the metrics parser reproduces every address it recorded. If the two ever disagree,
generation fails rather than publishing a corpus whose ground truth the scorer cannot resolve.

### The leak rule

Manifest content must not be discoverable inside the artifact. AC-8 tests this; the generator
enforces it at build time so a violation never reaches the corpus.

1. Normalize the artifact text and each defect `description`: NFC, casefold, split on whitespace,
   strip non-alphanumerics from each token.
2. Build the set of contiguous 6-token shingles of each. No description shingle may appear in the
   artifact's shingle set.
3. No criterion ID may appear anywhere in the artifact text.
4. No corpus path may contain a criterion ID, a defect count, or any of `clean`, `defect`, `seed`,
   `plant`, `bug`. Recipe ids are opaque sequential slugs for exactly this reason: the artifact path
   is handed to the skill under test.
5. HTML ids are assigned to every element of an injectable class in clean and seeded artifacts
   alike, from the same content-derived scheme, so the presence of an id never signals a plant.

The practical consequence for an injector author: write descriptions in meta-language. "One sentence
recast into passive voice with the acting party deleted" is a description. Quoting the sentence back
is a leak, and the build will say so.

### Self-validation

`Domain.validate()` runs before any generation and fails loudly:

- every injector key matches the contract's criterion ID grammar, and its namespace is in
  `namespaces`;
- every plant's criterion has a registered injector;
- every plant's target exists in the declared shape;
- no two plants in one recipe share a criterion inside one section (the corpus invariant the
  markdown tolerance rule depends on, see `bench/README.md`);
- `artifact_type` is one of the four in the manifest schema;
- at least one recipe has `plants=()`;
- recipe ids are unique, slug-shaped, and pass the path leak rule.

---

## Worked example: the `toy` domain

Copy this file, rename it, replace the vocabulary and the injectors. It is deliberately small and it
exercises every part of the API: two text injectors, one structural injector, both location kinds
that `markdown-prose` uses, and a clean recipe. `critique-*` skills use it as the pattern; the skill
template (S-04) uses the skill built from it as its own golden example.

`toy` is registered in `DOMAIN_MODULES` and generates into `bench/corpus/toy/`, but it is excluded
from every scored metric. It is a fixture, not evidence.

### `bench/generator/domains/toy.py`

```python
"""Toy domain: the worked example a skill pipeline copies.

Artifact type: markdown-prose. Namespace: TOY. Not scored.
"""

from bench.generator.api import Domain, InjectionResult, Location, Plant, Recipe, Target, injector
from bench.generator.markdown import Block, Document, heading_path, paragraph_index, render_blocks
from bench.generator.text import ORDINALS, split_sentences

# --- 1. Vocabulary. Frozen tuples. Order is part of the corpus identity: appending is safe,
#        reordering or removing regenerates every toy artifact. --------------------------------

DOC_TITLE = "Field operations notice"
SECTION_TITLES = ("Service window", "Meter replacement", "Billing adjustments", "Outage reporting")
ACTORS = ("The field crew", "The billing team", "The duty engineer", "The records clerk")
VERBS = ("reviews", "files", "closes", "signs off on")
OBJECTS = ("the meter log", "the outage report", "the service ticket", "the rate table")
WHENS = ("before the shift ends", "within one business day", "at the start of each week")
TAILS = (
    "Crews that finish early return the vehicle to the depot and record the mileage.",
    "Any reading outside the expected band goes to the duty engineer on the same day.",
    "A replacement meter carries its own serial number, and that number goes on the ticket.",
    "Adjustments raised after that point land in the following cycle.",
)
HEDGES = ("It may possibly be the case that", "It could perhaps be argued that")
PARTICIPLES = {"reviews": "is reviewed", "files": "is filed", "closes": "is closed",
               "signs off on": "is signed off on"}
ORPHAN_HEADINGS = ("Escalation", "Exceptions")

INJECTORS = {}

# --- 2 and 3. Composition. Structure comes from the recipe shape; the stream picks words only. --

def compose(rng, shape):
    counts = shape["paragraphs"]                      # e.g. (2, 1, 1): three sections
    blocks = [Block(kind="heading", level=1, text=f"# {DOC_TITLE}", slot="h0")]
    for section, count in enumerate(counts, start=1):
        title = SECTION_TITLES[section - 1]
        blocks.append(Block(kind="heading", level=2, text=f"## {title}", slot=f"s{section}.h"))
        for p in range(1, count + 1):
            prng = rng.child("para", section, p)
            blocks.append(Block(kind="paragraph", level=0, text=_paragraph(prng),
                                slot=f"s{section}.p{p}"))
    return Document(tuple(blocks))


def _paragraph(rng):
    lead = f"{rng.choice(ACTORS)} {rng.choice(VERBS)} {rng.choice(OBJECTS)} {rng.choice(WHENS)}."
    return f"{lead} {rng.choice(TAILS)}"


def render(doc):
    return render_blocks(doc.blocks)                  # blocks joined by one blank line

# --- 4. Injectors, keyed by criterion ID. Each returns a new composition, never mutates. --------

@injector("TOY-ACTIVE")
def inject_active(rng, doc, target):
    """Recast the lead sentence into passive voice and delete the acting party."""
    slot = f"s{target.section}.p{target.block}"
    block = doc.block(slot)
    sentences = split_sentences(block.text)
    actor, verb, rest = _parse_lead(sentences[0])     # safe: the grammar is ours
    passive = f"{rest.object_phrase[0].upper()}{rest.object_phrase[1:]} " \
              f"{PARTICIPLES[verb]} {rest.when}."
    text = " ".join([passive, *sentences[1:]])
    return InjectionResult(
        composed=doc.replace(slot, text),
        slot=slot,
        severity_expected=2,
        description="One sentence recast into passive voice with the acting party deleted.",
        sentence=1,
    )


@injector("TOY-HEDGE")
def inject_hedge(rng, doc, target):
    """Stack a hedge in front of an otherwise direct statement."""
    slot = f"s{target.section}.p{target.block}"
    block = doc.block(slot)
    sentences = split_sentences(block.text)
    head = sentences[0]
    hedged = f"{rng.choice(HEDGES)} {head[0].lower()}{head[1:]}"
    text = " ".join([hedged, *sentences[1:]])
    return InjectionResult(
        composed=doc.replace(slot, text),
        slot=slot,
        severity_expected=2,
        description="A stacked hedge placed ahead of an otherwise direct statement.",
        sentence=1,
    )


@injector("TOY-ORPHAN", phase="structure")
def inject_orphan(rng, doc, target):
    """Add a subheading with no body before the next heading of equal or higher level."""
    anchor = f"s{target.section}.h"
    slot = f"s{target.section}.x1"                    # a new identity, not a renumbering
    heading = Block(kind="heading", level=3, text=f"### {rng.choice(ORPHAN_HEADINGS)}", slot=slot)
    return InjectionResult(
        composed=doc.insert_after_section(anchor, heading),
        slot=slot,
        severity_expected=3,
        description="A subheading left with no body before the next heading of equal or higher level.",
    )

# --- 5. Addressing. Called by the harness after every injection, on the final composition. ------

def address(doc, slot, sentence=None):
    block = doc.block(slot)
    path = heading_path(doc, slot)     # enclosing headings, plus this block when it is a heading
    if block.kind == "heading":
        return Location(kind="heading-path", heading_path=path,
                        text=f"the {path[-1]} heading")
    index = paragraph_index(doc, slot)
    within = _ordinal_within_section(doc, slot)
    text = f"{path[-1]}, {ORDINALS[within]} paragraph"
    if sentence is not None:
        text = f"{text}, {ORDINALS[sentence]} sentence"
    return Location(kind="paragraph", paragraph=index, sentence=sentence,
                    heading_path=path, text=text)

# --- 6. Recipes. Three artifacts, one of them clean. -------------------------------------------

RECIPES = (
    Recipe(id="toy-001", shape={"paragraphs": (2, 1, 1)}, plants=(
        Plant("TOY-ACTIVE", Target(section=1, block=2), severity_expected=2),
        Plant("TOY-HEDGE", Target(section=3, block=1), severity_expected=2),
    )),
    Recipe(id="toy-002", shape={"paragraphs": (2, 2, 1, 1)}, plants=(
        Plant("TOY-ORPHAN", Target(section=4), severity_expected=3),
        Plant("TOY-ACTIVE", Target(section=2, block=1), severity_expected=2),
        Plant("TOY-HEDGE", Target(section=1, block=1), severity_expected=2),
    )),
    Recipe(id="toy-003", shape={"paragraphs": (1, 2, 1)}, plants=()),
)

DOMAIN = Domain(
    name="toy",
    artifact_type="markdown-prose",
    extension=".md",
    namespaces=("TOY",),
    compose=compose,
    render=render,
    address=address,
    injectors=INJECTORS,
    recipes=RECIPES,
)
```

### What `toy-001` generates

`bench/corpus/toy/toy-001.md`, 692 bytes, sha256
`61ac98b86964a7fcc355f99370546467e5e45de80847b306d71b570ba053f044`:

```markdown
# Field operations notice

## Service window

The field crew reviews the meter log before the shift ends. Crews that finish early return the vehicle to the depot and record the mileage.

The outage report is filed within one business day. Any reading outside the expected band goes to the duty engineer on the same day.

## Meter replacement

The records clerk signs off on the service ticket before the shift ends. A replacement meter carries its own serial number, and that number goes on the ticket.

## Billing adjustments

It may possibly be the case that the billing team closes the rate table at the start of each week. Adjustments raised after that point land in the following cycle.
```

Document paragraph 1 is clean and shows the active pattern the injector broke in paragraph 2.
Paragraph 4 carries the hedge. Paragraph 3 is untouched filler that exists so a skill has somewhere
to raise a false positive.

### What `toy-001` records

`bench/corpus/toy/toy-001.manifest.json`, validated against `manifest.schema.json`:

```json
{
  "artifact": "bench/corpus/toy/toy-001.md",
  "artifact_sha256": "61ac98b86964a7fcc355f99370546467e5e45de80847b306d71b570ba053f044",
  "artifact_type": "markdown-prose",
  "defects": [
    {
      "criterion": "TOY-ACTIVE",
      "description": "One sentence recast into passive voice with the acting party deleted.",
      "location": {
        "heading_path": [
          "Field operations notice",
          "Service window"
        ],
        "kind": "paragraph",
        "paragraph": 2,
        "sentence": 1,
        "text": "Service window, second paragraph, first sentence"
      },
      "severity_expected": 2
    },
    {
      "criterion": "TOY-HEDGE",
      "description": "A stacked hedge placed ahead of an otherwise direct statement.",
      "location": {
        "heading_path": [
          "Field operations notice",
          "Billing adjustments"
        ],
        "kind": "paragraph",
        "paragraph": 4,
        "sentence": 1,
        "text": "Billing adjustments, first paragraph, first sentence"
      },
      "severity_expected": 2
    }
  ],
  "domain": "toy",
  "manifest_version": "1.0.0",
  "recipe": "toy-001",
  "seed": "95f4393141bd0f4c0611135bcba857f6"
}
```

The seed is `derive(root_seed(), "toy", "toy-001")` with `CORPUS_SEED` as published above; the root
seed is `b7470f08a0096e0192161ee2b062cb16`. Both values are reproducible from the derivation shown
earlier and are the first determinism check the harness implementation should target.

Note what the manifest does not say. It does not quote the passive sentence, name the hedge phrase,
or record which words changed. A reader of the manifest knows where to look and what kind of breach
to expect; a string search of the artifact for manifest content returns nothing.

### Transforms operate on a grammar you own

`inject_active` can safely take a sentence apart because `compose` built it from a known template.
An injector that tried to passivize arbitrary English would be a small NLP project with a
nondeterministic failure mode. This is the single most transferable rule in the file: **generate
prose whose structure you can invert, then invert it.** Where a domain genuinely needs a defect in
text it cannot parse, the clean and defective variants are both written into the vocabulary bank as
a matched pair, and the injector swaps one for the other.

---

## Checklist for a new domain module

1. Pick the artifact type. If it is not one of the four in `manifest.schema.json`, stop: a new type
   needs a tolerance rule in `bench/README.md` and an ADR first.
2. Declare the criterion namespaces, matching the skill's registry (S-05).
3. Write the vocabulary banks as frozen tuples. Never a set, never a dict comprehension over one.
4. Write `compose` taking `(rng, shape)`. Structure from `shape`, words from `rng`. Assign a slot to
   every unit.
5. Write one injector per criterion. Cover every scripted-lane criterion and at least three
   judged-lane criteria (S-04 requirement). Return a new composition, a slot, a severity, and a
   meta-language description.
6. Write `address` for the artifact type's anchor kinds.
7. Write at least three recipes, at least one with `plants=()`. Keep at most one plant per criterion
   per section.
8. Add the module to `registry.DOMAIN_MODULES`.
9. Run `python -m bench.generator validate --domain <name>`, then `build`, then `verify`.
10. Read the generated artifacts. If you can find the defects by looking for something odd about the
    prose rather than something wrong with it, the injector is leaking style, and recall will be
    inflated.

## Commands

Frozen here as the interface; implemented in the harness stage. Every path is repository-relative
and every command is run from the repository root.

| Command | Does |
|---|---|
| `python -m bench.generator validate` | `Domain.validate()` for every registered domain, no output written |
| `python -m bench.generator build --out bench/corpus` | generate the full corpus and its manifests |
| `python -m bench.generator build --domain toy` | regenerate one domain |
| `python -m bench.generator verify --corpus bench/corpus` | regenerate to a temporary tree and compare every sha256 |
| `python -m bench.generator diff toy-001` | show the clean composition against the seeded one, for review |
| `python -m bench.generator leak-check --corpus bench/corpus` | run the leak rules over an existing corpus |

One check works today against the real file. Run under Git Bash on Windows from the repository root:

```
python -c "import json,jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('bench/generator/manifest.schema.json'))); print('manifest schema OK')"
```

The identity check the whole corpus rests on is one line, exercised here against this schema file
and pointed at a corpus artifact once one exists:

```
python -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <path>
```

If it does not print the `artifact_sha256` recorded in the manifest beside the artifact, the
artifact and its ground truth have parted company.
