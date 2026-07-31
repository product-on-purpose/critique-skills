"""Toy domain: the worked example a skill pipeline copies.

Artifact type: markdown-prose. Namespace: TOY. Not scored. Implemented
exactly as specified in `bench/generator/README.md`, "Worked example: the
toy domain": two text injectors, one structural injector, both location
kinds that markdown-prose uses, and a clean recipe.
"""

from __future__ import annotations

from dataclasses import dataclass

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


# --- Parsing helper the injectors below lean on. Safe because compose() built every lead
#     sentence from exactly this grammar, in exactly this order: there is nothing here an
#     injector could misparse. See the README's "Transforms operate on a grammar you own". ------


@dataclass(frozen=True, slots=True)
class _LeadRest:
    object_phrase: str
    when: str


def _parse_lead(sentence: str) -> tuple[str, str, _LeadRest]:
    for actor in ACTORS:
        actor_prefix = f"{actor} "
        if not sentence.startswith(actor_prefix):
            continue
        after_actor = sentence[len(actor_prefix):]
        for verb in VERBS:
            verb_prefix = f"{verb} "
            if not after_actor.startswith(verb_prefix):
                continue
            after_verb = after_actor[len(verb_prefix):]
            for obj in OBJECTS:
                obj_prefix = f"{obj} "
                if not after_verb.startswith(obj_prefix):
                    continue
                after_obj = after_verb[len(obj_prefix):]
                for when in WHENS:
                    if after_obj == f"{when}.":
                        return actor, verb, _LeadRest(object_phrase=obj, when=when)
    raise ValueError(f"lead sentence does not match the generated grammar: {sentence!r}")


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


def _ordinal_within_section(doc, slot):
    """1-based ordinal of the paragraph at `slot` among paragraph blocks in
    its own immediate (level-2) section, counted in document order from the
    final composition. Never read off the slot's own `.p{n}` suffix: a
    structural injector that ran before this one could in principle have
    changed what counts as "this section", and the README's own rule is
    that every index is derived from the final composition, not from a
    slot id."""
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
