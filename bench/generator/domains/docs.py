"""Docs domain: bench corpus for critique-docs.

Artifact type: markdown-tree. Namespace: DIATAXIS. Scored corpus (S-05,
critique-docs, stretch). Subject matter is an invented documentation set
for a fictional alerting console, one page per recipe, each page written
in the minimal frontmatter-declared-mode convention
skills/critique-docs/scripts/checks.py reads and
skills/critique-docs/references/DIATAXIS.md, "Marker registry and
thresholds", defines normatively.

Six of the nine DIATAXIS-* criteria have an injector here: all three
scripted (DIATAXIS-HEADING-DEPTH, DIATAXIS-MODE, DIATAXIS-NAV-LENGTH) plus
three judged (DIATAXIS-HOWTO-GOAL, DIATAXIS-REFERENCE-NEUTRAL,
DIATAXIS-TUTORIAL-ACTION), satisfying bench/generator/README.md's
checklist ("Cover every scripted-lane criterion and at least three
judged-lane criteria"). DIATAXIS-CROSSLINK, DIATAXIS-EXPLANATION-CONTEXT,
and DIATAXIS-ORPHAN are deliberately not injected here:

- DIATAXIS-CROSSLINK and DIATAXIS-ORPHAN are tree-dependent. Both need
  every *other* page's outbound links to decide whether a given page's
  own condition holds; bench/README.md's own location-tolerance rule
  fixes "one artifact is one page" for the markdown-tree type, so a
  single-page corpus artifact never carries the sibling-page data either
  criterion's operational test needs. See
  skills/critique-docs/references/DIATAXIS.md, "Why DIATAXIS-ORPHAN moved
  to the judged lane", and skills/critique-docs/examples/golden-03.json's
  note, which states the identical reasoning for the skill's own
  hand-authored single-page example.
- DIATAXIS-EXPLANATION-CONTEXT is single-page decidable and is left out
  only to keep this module's recipe count close to bench/README.md's
  corpus-design table (docs: 3 artifacts, 1 clean); three judged criteria
  already satisfies the floor this module's checklist item sets, and
  every one of the four mode-fit criteria (DIATAXIS-HOWTO-GOAL,
  DIATAXIS-REFERENCE-NEUTRAL, DIATAXIS-TUTORIAL-ACTION,
  DIATAXIS-EXPLANATION-CONTEXT) needs its own page mode, so covering a
  fourth would need a fourth seeded page. Nothing about
  DIATAXIS-EXPLANATION-CONTEXT stops a later stage from adding it.

Recipe overview (four artifacts, one clean, matching the table's
per-skill floor of at least three including at least one clean):

    docs-001   how-to page      DIATAXIS-MODE (scripted), DIATAXIS-HOWTO-GOAL (judged)
    docs-002   tutorial page    DIATAXIS-HEADING-DEPTH (scripted), DIATAXIS-TUTORIAL-ACTION (judged)
    docs-003   reference page   DIATAXIS-NAV-LENGTH (scripted), DIATAXIS-REFERENCE-NEUTRAL (judged)
    docs-004   reference page   clean, no plants

Why frontmatter is a block, not a render-time prefix
------------------------------------------------------
Every page declares its mode in a "---"-delimited frontmatter block at
the very top of the file, exactly the convention
skills/critique-docs/scripts/checks.py's `_split_frontmatter` reads. That
block is composed as this document's own first `Block` (slot "fm", kind
"paragraph"), never prepended to the rendered text outside the block
list. The reason is the round-trip check
(bench/generator/pipeline.py, `_round_trip_check_markdown`): it reparses
the rendered bytes with `bench/generator/blockparse.py`'s independent
copy of the normative block parser and requires the block *count* to
match this module's own `Document.blocks`, one for one. A bare "---"
line matches none of that parser's heading, list, blockquote, fence,
table, or HTML markers, and the frontmatter's three lines are not a
two-line block, so the whole run falls through to that parser's default
classification, "paragraph", exactly the kind this module already gives
it. Composing it as a real block (with the blank line `render_blocks`
already inserts between every pair of blocks) keeps both parsers' block
counts, and both parsers' paragraph counts, in permanent agreement: the
frontmatter block counts as paragraph 1 in both, so every real content
paragraph's `location.paragraph` is one higher than a reader unfamiliar
with this trick might expect, consistently on both sides of the
round-trip check.

Why every plural-item list sits at the very end of its document
-------------------------------------------------------------------
`bench/generator/markdown.py`'s shared `Block` model has exactly two
kinds, "heading" and "paragraph"; it has no "list" kind. The normative
block parser (bench/README.md, "The block parser (normative)") does
have one: a block opening with `-`, `*`, `+`, or a digit-marker followed
by a space classifies as a list, not a paragraph, and is excluded from
that parser's own paragraph count. `DIATAXIS-NAV-LENGTH` cannot be
planted without real list markdown syntax; scripts/checks.py's own
`_check_nav_length` requires it. Composing that syntax into a block this
module still calls "paragraph" internally is therefore a controlled and
deliberate mismatch with the round-trip parser's classification of that
one block, safe only because nothing downstream ever depends on the
mismatch: the injector below reports the defect's location at the
*heading* immediately before the list, never at the list block's own
slot, and the list is always the trailing content of its page, so no
later `location.kind == "paragraph"` record's index is ever computed
across it. See `inject_nav_length`.

Why an injector reads its own mode back out of the composition
--------------------------------------------------------------
`Injector`'s signature is `(SeededRng, composition, Target)`; it never
receives the recipe's own `shape` dict. `inject_mode` needs to know
which marker group is foreign to the page's own declared mode
(skills/critique-docs/references/DIATAXIS.md, "Marker registry and
thresholds"), so it reads the frontmatter block composed above back out
of the `Document` it was handed, via `_page_mode`, rather than being
told directly.
"""

from __future__ import annotations

import re

from bench.generator.api import Domain, InjectionResult, Location, Plant, Recipe, Target, injector
from bench.generator.markdown import Block, Document, heading_path, paragraph_index, render_blocks
from bench.generator.text import ORDINALS, split_sentences

# --- 1. Vocabulary. Frozen tuples. Order is part of the corpus identity: appending is safe,
#        reordering or removing regenerates every docs artifact. --------------------------------

# The closed marker lexicons DIATAXIS-MODE checks, copied here from
# skills/critique-docs/references/DIATAXIS.md, "Marker registry and
# thresholds" (the same source skills/critique-docs/scripts/checks.py's
# own ACTION_MARKERS, EXPLANATION_MARKERS, and FOREIGN_MARKERS_BY_MODE
# copy from), so a change to the registry belongs there first and is
# picked up here by hand, matching that file's own drift-prevention note.
ACTION_MARKERS = ("first,", "next,", "then,", "finally,", "after that,", "once you have", "now,")
EXPLANATION_MARKERS = (
    "because",
    "since",
    "this is because",
    "the reason is",
    "as a result,",
    "in other words,",
    "consequently,",
)
FOREIGN_MARKERS_BY_MODE = {
    "tutorial": (EXPLANATION_MARKERS,),
    "how-to": (EXPLANATION_MARKERS,),
    "reference": (ACTION_MARKERS, EXPLANATION_MARKERS),
    "explanation": (ACTION_MARKERS,),
}

# Markers `inject_mode` must not use, even though scripts/checks.py flags
# every one of them. Each is a subordinating conjunction: prefixing it to
# a complete declarative sentence yields a subordinate clause with no main
# clause, so the seeded page reads "Since the console applies the new
# threshold to every future evaluation of this rule." That is a sentence
# fragment, and a fragment is a louder, cheaper tell than the register
# slip actually being planted. A critic finds it by noticing broken
# grammar rather than by applying DIATAXIS-MODE's own test, which inflates
# recall for this criterion against a defect nobody had to reason about.
# The remaining markers are adverbial or copular and read as grammatical
# openers, so the only thing wrong with a seeded sentence is the register
# the criterion is about.
NON_PREFIXABLE_MARKERS = ("because", "since", "once you have", "the reason is")
PREFIXABLE_ACTION_MARKERS = tuple(m for m in ACTION_MARKERS if m not in NON_PREFIXABLE_MARKERS)
PREFIXABLE_EXPLANATION_MARKERS = tuple(
    m for m in EXPLANATION_MARKERS if m not in NON_PREFIXABLE_MARKERS
)
PREFIXABLE_MARKERS_BY_MODE = {
    "tutorial": (PREFIXABLE_EXPLANATION_MARKERS,),
    "how-to": (PREFIXABLE_EXPLANATION_MARKERS,),
    "reference": (PREFIXABLE_ACTION_MARKERS, PREFIXABLE_EXPLANATION_MARKERS),
    "explanation": (PREFIXABLE_ACTION_MARKERS,),
}

# The subsection `inject_heading_depth` adds, as (title, body) pairs
# drawn together so the body always answers its own heading. A heading
# with nothing under it is its own recognizable artifact, and the family
# already treats that exact shape as a defect in its own right (the
# template fixture's TOY-ORPHAN criterion), so leaving the injected
# heading bare would seed two defects and declare one. Each body is a
# plain imperative confirmation step, native to the tutorial register the
# only recipe planting this criterion declares, and opens with no marker
# in either lexicon above.
HEADING_JUMP_SUBSECTIONS = (
    (
        "Confirm the console loaded",
        "Look at the console header and confirm the workspace name matches the account you "
        "signed in with.",
    ),
    (
        "Check the sidebar updated",
        "Look at the sidebar and confirm the rule count now includes the sample rule.",
    ),
)

NAV_ITEMS = (
    "Webhook delivery reference",
    "Rate limit reference",
    "Alert rule schema",
    "Escalation policy reference",
    "Notification channel reference",
    "Metric catalog reference",
    "Time window reference",
    "Severity mapping reference",
    "Suppression rule reference",
    "Delivery status codes",
    "Retry backoff reference",
)
NAV_ITEM_COUNT = 9  # two past DIATAXIS-NAV-LENGTH's seven-item threshold, the severity 2 anchor

HOWTO_GOAL_DEFINITIONS = (
    "A threshold is the numeric boundary that triggers an alert once a metric crosses it.",
    "A rule is the stored combination of a metric, a comparison, and a threshold that the "
    "console evaluates on a schedule.",
)

TUTORIAL_ACTION_ASIDES = (
    "The status indicator takes a few seconds to update while the delivery pipeline processes "
    "the event in the background.",
    "The sample rule exists only on new accounts and is safe to trigger as many times as "
    "needed during setup.",
)

# Both of these have to actually recommend something, because the
# injector's own ground-truth `description` says the planted aside
# recommends a particular way to use the field. An aside that merely
# reports what most teams happen to do is a different defect shape, and a
# manifest whose description does not describe the artifact is ground
# truth a scorer cannot match a critic's finding against.
REFERENCE_NEUTRAL_ASIDES = (
    "We recommend setting this field well above its minimum for rules that depend on slower "
    "upstream services.",
    "Leaving this field at its default is the right choice for most teams, and raising it is "
    "worth doing only when a specific integration needs the extra room.",
)

INJECTORS = {}

# --- 2 and 3. Composition. Structure comes from the recipe shape; the stream picks words only. --
#
# shape keys: "mode" (the frontmatter value), "title" (the page's own
# h1), "section_titles" (one per declared section), "paragraphs" (the
# frozen per-section paragraph-count tuple bench/generator/api.py's own
# shape check reads), and "paragraph_variants", a same-shaped nested
# tuple of per-paragraph phrasing choices the seeded stream picks among.


def compose(rng, shape):
    mode = shape["mode"]
    title = shape["title"]
    section_titles = shape["section_titles"]
    counts = shape["paragraphs"]
    variants = shape["paragraph_variants"]
    blocks = [
        Block(kind="paragraph", level=0, text=f"---\nmode: {mode}\n---", slot="fm"),
        Block(kind="heading", level=1, text=f"# {title}", slot="h0"),
    ]
    for section, count in enumerate(counts, start=1):
        s_title = section_titles[section - 1]
        blocks.append(Block(kind="heading", level=2, text=f"## {s_title}", slot=f"s{section}.h"))
        for p in range(1, count + 1):
            prng = rng.child("para", section, p)
            text = prng.choice(variants[section - 1][p - 1])
            blocks.append(Block(kind="paragraph", level=0, text=text, slot=f"s{section}.p{p}"))
    return Document(tuple(blocks))


def render(doc):
    return render_blocks(doc.blocks)  # blocks joined by one blank line


_FRONTMATTER_MODE_LINE_RE = re.compile(r"^mode:\s*([a-z-]+)$")


def _page_mode(doc: Document) -> str:
    """Read the declared mode back out of the page's own frontmatter
    block (slot "fm"). See the module docstring, "Why an injector reads
    its own mode back out of the composition"."""
    for line in doc.block("fm").text.splitlines():
        match = _FRONTMATTER_MODE_LINE_RE.match(line.strip())
        if match:
            return match.group(1)
    raise ValueError("page has no frontmatter mode declared")


# --- 4. Injectors, keyed by criterion ID. Each returns a new composition, never mutates. --------


@injector("DIATAXIS-MODE")
def inject_mode(rng, doc, target):
    """Prefix the target paragraph's first sentence with a marker foreign
    to the page's own declared mode: the exact closed-lexicon pattern
    scripts/checks.py's DIATAXIS-MODE check flags."""
    slot = f"s{target.section}.p{target.block}"
    block = doc.block(slot)
    mode = _page_mode(doc)
    foreign_markers = tuple(m for group in PREFIXABLE_MARKERS_BY_MODE[mode] for m in group)
    sentences = split_sentences(block.text)
    head = sentences[0]
    marker = rng.choice(foreign_markers)
    prefixed = f"{marker[0].upper()}{marker[1:]} {head[0].lower()}{head[1:]}"
    text = " ".join([prefixed, *sentences[1:]])
    return InjectionResult(
        composed=doc.replace(slot, text),
        slot=slot,
        severity_expected=2,
        description=(
            "One sentence prefixed with a lexical marker belonging to a different mode's "
            "register than the page's own declared mode."
        ),
        sentence=1,
    )


@injector("DIATAXIS-HEADING-DEPTH", phase="structure")
def inject_heading_depth(rng, doc, target):
    """Add a heading two levels below the target section's own heading,
    with no intermediate level between them: the single-jump shape
    references/DIATAXIS.md's severity 2 anchor names.

    The heading gets a body paragraph of its own. The defect is the
    level jump alone, and a heading standing over nothing would plant a
    second, louder anomaly the manifest never declares (see
    HEADING_JUMP_BODIES). Both blocks anchor on the same section
    heading, so the body lands immediately after the new heading and
    before the next level-2 section."""
    anchor = f"s{target.section}.h"
    slot = f"s{target.section}.x1"
    body_slot = f"s{target.section}.x2"
    title, body_text = rng.choice(HEADING_JUMP_SUBSECTIONS)
    heading = Block(kind="heading", level=4, text=f"#### {title}", slot=slot)
    body = Block(kind="paragraph", level=0, text=body_text, slot=body_slot)
    return InjectionResult(
        composed=doc.insert_after_section(anchor, heading).insert_after_section(anchor, body),
        slot=slot,
        severity_expected=2,
        description=(
            "A heading inserted two levels below the heading immediately before it in "
            "document order, with no intermediate level between them."
        ),
    )


@injector("DIATAXIS-NAV-LENGTH", phase="structure")
def inject_nav_length(rng, doc, target):
    """Add a flat list of nine items under the target section's own
    (otherwise empty) heading: two past DIATAXIS-NAV-LENGTH's seven-item
    threshold, no subgrouping, the severity 2 anchor's own shape.

    The recorded slot is the section's own heading, not the list block:
    see the module docstring, "Why every plural-item list sits at the
    very end of its document". Every recipe that plants this criterion
    targets its document's last declared section, which is why nothing
    downstream of the list ever needs a paragraph-kind location across
    it."""
    anchor = f"s{target.section}.h"
    slot = f"s{target.section}.x1"
    items = rng.sample(NAV_ITEMS, NAV_ITEM_COUNT)
    list_text = "\n".join(f"- {item}" for item in items)
    list_block = Block(kind="paragraph", level=0, text=list_text, slot=slot)
    return InjectionResult(
        composed=doc.insert_after_section(anchor, list_block),
        slot=anchor,
        severity_expected=2,
        description=(
            f"A flat list of {NAV_ITEM_COUNT} items added under a heading with no other "
            "content, past the flat-listing threshold, with no subgrouping."
        ),
    )


@injector("DIATAXIS-HOWTO-GOAL", phase="structure")
def inject_howto_goal(rng, doc, target):
    """Add one paragraph defining a basic term a reader capable of
    reaching this step would already know: DIATAXIS-HOWTO-GOAL's severity
    2 anchor's own shape."""
    anchor = f"s{target.section}.h"
    slot = f"s{target.section}.x1"
    text = rng.choice(HOWTO_GOAL_DEFINITIONS)
    para = Block(kind="paragraph", level=0, text=text, slot=slot)
    return InjectionResult(
        composed=doc.insert_after_section(anchor, para),
        slot=slot,
        severity_expected=2,
        description=(
            "One paragraph added defining a basic term a reader capable of reaching this "
            "step would already know."
        ),
    )


@injector("DIATAXIS-TUTORIAL-ACTION", phase="structure")
def inject_tutorial_action(rng, doc, target):
    """Add one paragraph pausing the step sequence for a short aside on
    why the tool behaves this way, after which the sequence resumes at
    the next step: DIATAXIS-TUTORIAL-ACTION's severity 2 anchor's own
    shape."""
    anchor = f"s{target.section}.h"
    slot = f"s{target.section}.x1"
    text = rng.choice(TUTORIAL_ACTION_ASIDES)
    para = Block(kind="paragraph", level=0, text=text, slot=slot)
    return InjectionResult(
        composed=doc.insert_after_section(anchor, para),
        slot=slot,
        severity_expected=2,
        description=(
            "One paragraph added pausing the step sequence for a short aside on why the "
            "tool behaves this way, before the sequence resumes."
        ),
    )


@injector("DIATAXIS-REFERENCE-NEUTRAL", phase="structure")
def inject_reference_neutral(rng, doc, target):
    """Add one short aside recommending a particular way to use the
    target field, breaking the page's otherwise neutral, field-by-field
    description: DIATAXIS-REFERENCE-NEUTRAL's severity 2 anchor's own
    shape."""
    anchor = f"s{target.section}.h"
    slot = f"s{target.section}.x1"
    text = rng.choice(REFERENCE_NEUTRAL_ASIDES)
    para = Block(kind="paragraph", level=0, text=text, slot=slot)
    return InjectionResult(
        composed=doc.insert_after_section(anchor, para),
        slot=slot,
        severity_expected=2,
        description=(
            "One aside added recommending a particular way to use this field, breaking the "
            "page's otherwise neutral, field-by-field description."
        ),
    )


# --- 5. Addressing. Called by the harness after every injection, on the final composition. ------


def _ordinal_within_section(doc, slot):
    """1-based ordinal of the paragraph at `slot` among paragraph blocks
    in its own immediate (level-2) section, counted in document order
    from the final composition. Never read off the slot's own `.p{n}`
    suffix, per bench/generator/README.md's "slots are identities"
    rule. The frontmatter block precedes every section heading, so it
    is always reset away by the first section's own heading and never
    contributes to any section's ordinal."""
    count = 0
    for block in doc.blocks:
        if block.kind == "heading" and block.level == 2:
            count = 0
            continue
        if block.slot == slot:
            return count + 1
        if block.kind == "paragraph":
            count += 1
    raise KeyError(f"slot not found: {slot!r}")


def address(doc, slot, sentence=None):
    block = doc.block(slot)
    if block.kind == "heading":
        path = heading_path(doc, slot)
        return Location(kind="heading-path", heading_path=path, text=f"the {path[-1]} heading")
    index = paragraph_index(doc, slot)
    path = heading_path(doc, slot)
    within = _ordinal_within_section(doc, slot)
    text = f"{path[-1]}, {ORDINALS[within]} paragraph"
    if sentence is not None:
        text = f"{text}, {ORDINALS[sentence]} sentence"
    return Location(kind="paragraph", paragraph=index, sentence=sentence, heading_path=path, text=text)


# --- 6. Recipes. Four artifacts, one of them clean. ---------------------------------------------

_HOWTO_STEP1 = (
    "Open the alerts panel from the console sidebar and select the rule you want to adjust.",
    "Open the alerts panel from the settings menu and select the rule you want to change.",
)
_HOWTO_STEP2A = (
    "Enter the new threshold value in the field provided and confirm the unit matches the "
    "metric you selected.",
    "Enter the updated threshold value in the field provided and confirm the unit matches the "
    "metric in use.",
)
_HOWTO_STEP2B = (
    "The console applies the new threshold to every future evaluation of this rule.",
    "The new threshold takes effect the next time the console evaluates this rule.",
)
_HOWTO_STEP3 = (
    "Save the rule and check the rule list to confirm the updated threshold appears.",
    "Save the rule and open the rule list to confirm the new threshold appears there.",
)

_TUTORIAL_STEP1 = (
    "Open the test console from the developer menu and select the sample alert rule provided "
    "for new accounts.",
    "Open the test console from the developer menu and pick the sample alert rule that comes "
    "with new accounts.",
)
_TUTORIAL_STEP2 = (
    "Click Trigger sample alert and wait for the status indicator to change to Sent.",
    "Click Trigger sample alert and watch the status indicator switch to Sent.",
)
_TUTORIAL_STEP3 = (
    "Open the delivery log and confirm the test alert appears with a Sent status and a "
    "timestamp.",
    "Open the delivery log and check that the test alert shows a Sent status with a "
    "timestamp.",
)

_REF_TIMEOUT = (
    "The timeout field accepts a duration in milliseconds, and values below 1000 are rejected "
    "by the validator.",
    "The timeout field takes a duration in milliseconds, and the validator rejects any value "
    "below 1000.",
)
_REF_RETRIES = (
    "The retries field accepts an integer between 0 and 10, and the default value is 3.",
    "The retries field takes an integer from 0 to 10, and it defaults to 3.",
)
_REF_LOGGING = (
    "The logging field accepts one of debug, info, warn, or error, and the default value is "
    "info.",
    "The logging field takes one of debug, info, warn, or error, and it defaults to info.",
)

_CLEAN_ENDPOINT = (
    "The endpoint_url field accepts an HTTPS URL that receives the webhook payload for each "
    "triggered alert.",
    "The endpoint_url field takes an HTTPS URL, and the console sends the webhook payload "
    "there for each triggered alert.",
)
_CLEAN_SECRET = (
    "The signing_secret field accepts a string used to verify the payload signature on "
    "receipt.",
    "The signing_secret field takes a string, and the receiving end uses it to verify the "
    "payload signature.",
)
_CLEAN_RETRY = (
    "The retry_policy field accepts one of none, linear, or exponential, and the default "
    "value is exponential.",
    "The retry_policy field takes one of none, linear, or exponential, and it defaults to "
    "exponential.",
)

RECIPES = (
    Recipe(
        id="docs-001",
        shape={
            "mode": "how-to",
            "title": "Configure alert thresholds",
            "section_titles": ("Open alert settings", "Set the new threshold", "Save and verify"),
            "paragraphs": (1, 2, 1),
            "paragraph_variants": (
                (_HOWTO_STEP1,),
                (_HOWTO_STEP2A, _HOWTO_STEP2B),
                (_HOWTO_STEP3,),
            ),
        },
        plants=(
            Plant("DIATAXIS-HOWTO-GOAL", Target(section=1), severity_expected=2),
            Plant("DIATAXIS-MODE", Target(section=2, block=2), severity_expected=2),
        ),
    ),
    Recipe(
        id="docs-002",
        shape={
            "mode": "tutorial",
            "title": "Send your first test alert",
            "section_titles": ("Open the test console", "Trigger the sample alert", "Check the delivery log"),
            "paragraphs": (1, 1, 1),
            "paragraph_variants": (
                (_TUTORIAL_STEP1,),
                (_TUTORIAL_STEP2,),
                (_TUTORIAL_STEP3,),
            ),
        },
        plants=(
            Plant("DIATAXIS-HEADING-DEPTH", Target(section=1), severity_expected=2),
            Plant("DIATAXIS-TUTORIAL-ACTION", Target(section=2), severity_expected=2),
        ),
    ),
    Recipe(
        id="docs-003",
        shape={
            "mode": "reference",
            "title": "Alert rule fields reference",
            "section_titles": ("timeout", "retries", "logging", "Related pages"),
            "paragraphs": (1, 1, 1, 0),
            "paragraph_variants": (
                (_REF_TIMEOUT,),
                (_REF_RETRIES,),
                (_REF_LOGGING,),
                (),
            ),
        },
        plants=(
            Plant("DIATAXIS-REFERENCE-NEUTRAL", Target(section=1), severity_expected=2),
            Plant("DIATAXIS-NAV-LENGTH", Target(section=4), severity_expected=2),
        ),
    ),
    Recipe(
        id="docs-004",
        shape={
            "mode": "reference",
            "title": "Webhook delivery reference",
            "section_titles": ("endpoint_url", "signing_secret", "retry_policy"),
            "paragraphs": (1, 1, 1),
            "paragraph_variants": (
                (_CLEAN_ENDPOINT,),
                (_CLEAN_SECRET,),
                (_CLEAN_RETRY,),
            ),
        },
        plants=(),
    ),
)

DOMAIN = Domain(
    name="docs",
    artifact_type="markdown-tree",
    extension=".md",
    namespaces=("DIATAXIS",),
    compose=compose,
    render=render,
    address=address,
    injectors=INJECTORS,
    recipes=RECIPES,
)
