"""Argument domain: bench corpus for critique-argument.

Artifact type: markdown-prose. Namespace: TOULMIN. Scored corpus (S-05,
critique-argument, stretch). Subject matter is an invented recommendation
memo for a fictional regional library consortium proposing to end overdue
fines systemwide, structured around the six Toulmin elements plus the two
scripted assists critique-argument's own registry defines
(skills/critique-argument/references/TOULMIN.md, "Registry"):

    TOULMIN-BACKING, TOULMIN-CLAIM, TOULMIN-CLAIM-MARKER, TOULMIN-GROUNDS,
    TOULMIN-HEDGE-DENSITY, TOULMIN-QUALIFIER, TOULMIN-REBUTTAL, TOULMIN-WARRANT.

Every one of the eight criteria has its own injector here, per
bench/generator/README.md's checklist ("Write one injector per criterion.
Cover every scripted-lane criterion and at least three judged-lane
criteria"). The corpus plants all eight across two seeded recipes plus one
clean recipe, matching bench/README.md's corpus design table (argument: 3
artifacts, 1 clean).

Document shape (five sections, one role each):

    1. Circulation Trends                       filler, no criterion targets it
    2. What the Pilot Showed                     TOULMIN-GROUNDS
    3. Recommendation                            TOULMIN-CLAIM-MARKER, TOULMIN-CLAIM, TOULMIN-QUALIFIER
    4. Why the Pilot Result Applies Systemwide   TOULMIN-WARRANT, TOULMIN-BACKING
    5. Addressing the Revenue Concern            TOULMIN-REBUTTAL

Every judged injector below does a wholesale replacement of its own target
paragraph's text rather than a partial edit, so injector order never
matters for correctness: TOULMIN-HEDGE-DENSITY's document-wide rewrite
(section 1, sorted first) touches every paragraph, and any later injector
targeting one of those paragraphs simply overwrites it outright with fresh,
un-hedged text. See bench/generator/README.md, "The pipeline", on why
structural injectors run before text injectors and why canonical order is
(section, block, criterion); nothing here relies on injectors seeing each
other's output.
"""

from __future__ import annotations

from bench.generator.api import Domain, InjectionResult, Location, Plant, Recipe, Target, injector
from bench.generator.markdown import Block, Document, heading_path, paragraph_index, render_blocks
from bench.generator.text import ORDINALS, split_sentences

# --- 1. Vocabulary. Frozen tuples. Order is part of the corpus identity: appending is safe,
#        reordering or removing regenerates every argument artifact. -----------------------------

DOC_TITLE = "Ending Overdue Fines Systemwide: A Recommendation"
SECTION_TITLES = (
    "Circulation Trends",
    "What the Pilot Showed",
    "Recommendation",
    "Why the Pilot Result Applies Systemwide",
    "Addressing the Revenue Concern",
)

# Section 1: filler background, no criterion targets it. Combinatorial in
# the same shape as the toy domain's own filler, so a false positive has
# somewhere neutral to land.
CONTEXT_SUBJECTS = (
    "The consortium's circulation team",
    "The branch managers' working group",
    "The finance office",
    "The systems team",
)
CONTEXT_VERBS = ("tracks", "reviews", "reports", "audits")
CONTEXT_OBJECTS = (
    "monthly checkout volume",
    "overdue notice counts",
    "self-checkout usage",
    "renewal rates",
)
CONTEXT_WHENS = (
    "at the end of each quarter",
    "on the first of every month",
    "after each fiscal period",
)
CONTEXT_TAILS = (
    "Branch-level totals roll up into the consortium's shared reporting dashboard.",
    "Any branch that misses a reporting deadline is flagged for follow-up the next week.",
    "The dashboard has tracked these figures consistently since the current system launched.",
    "Historical figures are archived for five years before being summarized and retired.",
)

# Section 2: grounds. Paragraph 1 is the TOULMIN-GROUNDS target, paragraph 2
# stays untouched evidence so a clean artifact still has real support left
# after the plant.
PILOT_BRANCH_COUNTS = (3, 4, 5)
PILOT_MONTHS = (12, 14, 16, 18)
PILOT_RATE_NEW = (91, 92, 93, 94)
PILOT_RATE_OLD = (86, 87, 88, 89)
SURVEY_BEFORE = (18, 19, 20, 21, 22)
SURVEY_AFTER = (3, 4, 5)

# Section 3: the recommendation. Paragraph 1 carries the marker clause
# (TOULMIN-CLAIM-MARKER target), paragraph 2 is the crisp claim
# (TOULMIN-CLAIM target), paragraph 3 is the bounded qualifier
# (TOULMIN-QUALIFIER target). references/TOULMIN.md's own closed
# conclusion-marker lexicon, narrowed to the three phrases that read as a
# grammatical sentence-initial clause.
MARKER_LEADS = ("Therefore,", "Thus,", "Hence,")

# references/TOULMIN.md's own closed hedging lexicon
# (skills/critique-argument/scripts/checks.py, HEDGES), paired with a
# sentence-initial template so the phrase reads as a grammatical clause
# rather than a bare prefix. The phrase itself (first tuple element) is
# unused by the injector directly; it documents which lexicon entry each
# template exercises, matched against the same order checks.py declares it.
HEDGE_TEMPLATES = (
    ("may", "It may be that {s}"),
    ("might", "It might be that {s}"),
    ("could", "It could be that {s}"),
    ("possibly", "Possibly, {s}"),
    ("perhaps", "Perhaps, {s}"),
    ("arguably", "Arguably, {s}"),
    ("somewhat", "In a somewhat qualified way, {s}"),
    ("relatively", "Relatively speaking, {s}"),
    ("it seems", "It seems that {s}"),
    ("appears to", "This appears to be true: {s}"),
    ("tends to", "This tends to hold: {s}"),
    ("to a degree", "To a degree, {s}"),
)

# Injected-text variants, two per judged criterion, chosen by the injector's
# own rng so a corpus regeneration is not locked to one fixed sentence.
CLAIM_VAGUE_VARIANTS = (
    "Specifically, the recommended change is about making things better for patrons going "
    "forward, in whatever way the consortium finds workable.",
    "Specifically, the recommended change is meant to improve how the consortium serves its "
    "patrons over time.",
)
QUALIFIER_OVERREACH_VARIANTS = (
    "This recommendation eliminates all overdue-related billing for every item, in every "
    "circumstance, with no exceptions of any kind.",
    "This recommendation removes every overdue-related charge permanently, for every item the "
    "consortium owns, without qualification.",
)
WARRANT_GAP_VARIANTS = (
    "The systems team plans to update the online catalog's fine-display field during the same "
    "rollout window.",
    "The communications office will send a single email announcement to all cardholders once "
    "the change takes effect.",
)
BACKING_UNSUPPORTED_VARIANTS = (
    "This is simply how patron behavior works, and no library that has tried it has ever found "
    "otherwise.",
    "Anyone familiar with how lending libraries operate already knows this to be true.",
)
REBUTTAL_ABANDONED_VARIANTS = (
    "The branch renovation project remains on schedule for completion next spring.",
    "The consortium's annual report is due to the state library agency in early summer.",
)
GROUNDS_RESTATEMENT_VARIANTS = (
    "Ending overdue fines is clearly the right call for the consortium, and every branch stands "
    "to gain from making the change as soon as possible.",
    "Ending overdue fines is plainly the better path for the consortium, and delaying the "
    "change would only cost every branch more.",
)

# The marker-free form of the recommendation sentence _recommendation_paragraph(rng, 1) produces:
# everything after MARKER_LEADS's chosen phrase is fixed text with no further rng draws, so this
# is a constant, not a parse of whatever text currently occupies the slot. Written as a wholesale
# replacement, matching every other judged injector in this module, so TOULMIN-CLAIM-MARKER never
# has to assume it runs before TOULMIN-HEDGE-DENSITY's document-wide rewrite; both are text-phase
# and section-1-sorts-first means the hedge pass runs first in practice, and a partial edit that
# expected the original unhedged prefix would break exactly as a partial edit should be expected
# to when another injector has already touched the same slot.
RECOMMENDATION_MARKER_FREE = (
    "Given the return-rate and avoidance-survey results above, the stronger choice is a "
    "systemwide end to overdue fines across all ten consortium branches, effective at the start "
    "of the next fiscal year."
)

INJECTORS = {}

# --- 2 and 3. Composition. Structure comes from the recipe shape; the stream picks words only. --


def compose(rng, shape):
    counts = shape["paragraphs"]  # (2, 2, 3, 2, 2): five sections, this domain's only shape
    blocks = [Block(kind="heading", level=1, text=f"# {DOC_TITLE}", slot="h0")]
    for section, count in enumerate(counts, start=1):
        title = SECTION_TITLES[section - 1]
        blocks.append(Block(kind="heading", level=2, text=f"## {title}", slot=f"s{section}.h"))
        for p in range(1, count + 1):
            prng = rng.child("para", section, p)
            text = _paragraph_text(prng, section, p)
            blocks.append(Block(kind="paragraph", level=0, text=text, slot=f"s{section}.p{p}"))
    return Document(tuple(blocks))


def _paragraph_text(rng, section, p):
    if section == 1:
        return _context_paragraph(rng)
    if section == 2:
        return _grounds_paragraph(rng, p)
    if section == 3:
        return _recommendation_paragraph(rng, p)
    if section == 4:
        return _warrant_backing_paragraph(p)
    if section == 5:
        return _rebuttal_paragraph(p)
    raise ValueError(f"no paragraph template for section {section}")


def _context_paragraph(rng):
    lead = (
        f"{rng.choice(CONTEXT_SUBJECTS)} {rng.choice(CONTEXT_VERBS)} "
        f"{rng.choice(CONTEXT_OBJECTS)} {rng.choice(CONTEXT_WHENS)}."
    )
    return f"{lead} {rng.choice(CONTEXT_TAILS)}"


def _grounds_paragraph(rng, p):
    if p == 1:
        months = rng.choice(PILOT_MONTHS)
        branches = rng.choice(PILOT_BRANCH_COUNTS)
        rate_new = rng.choice(PILOT_RATE_NEW)
        rate_old = rng.choice(PILOT_RATE_OLD)
        article = "an" if months == 18 else "a"
        return (
            f"During {article} {months}-month pilot at {branches} branches, the on-time-or-eventual "
            f"return rate for borrowed items held at {rate_new} percent, compared with "
            f"{rate_old} percent at the branches that kept fines in place over the same period. "
            f"Materials-recovery staff logged the comparison monthly using the same circulation "
            f"software used consortium-wide."
        )
    before = rng.choice(SURVEY_BEFORE)
    after = rng.choice(SURVEY_AFTER)
    return (
        f"A parallel patron survey found that self-reported avoidance of the library due to "
        f"fear of fines dropped from {before} percent of respondents before the pilot to "
        f"{after} percent after it, using the same survey instrument both times. The survey was "
        f"administered at the same pilot branches immediately before and twelve months into the "
        f"pilot."
    )


def _recommendation_paragraph(rng, p):
    if p == 1:
        marker = rng.choice(MARKER_LEADS)
        return (
            f"{marker} given the return-rate and avoidance-survey results above, the stronger "
            f"choice is a systemwide end to overdue fines across all ten consortium branches, "
            f"effective at the start of the next fiscal year."
        )
    if p == 2:
        return (
            "Specifically, the recommended change eliminates overdue fines for all item types "
            "at all ten branches, replacing the current fine notices with automatic email "
            "reminders sent three, seven, and fourteen days after the due date."
        )
    return (
        "This recommendation applies to items returned within 60 days of their due date; items "
        "still unreturned past that window remain subject to the existing replacement-cost "
        "billing process, matching the return-rate pattern the pilot data actually established."
    )


def _warrant_backing_paragraph(p):
    if p == 1:
        return (
            "Removing the financial penalty for late returns predictably increases both "
            "on-time return rates and overall program participation, which is the reason the "
            "pilot's return-rate and avoidance-survey results, taken together, support ending "
            "fines for the whole consortium rather than only the pilot branches."
        )
    return (
        "This relationship is documented in the Tri-County Library Data Cooperative's 2023 "
        "fines-elimination research brief, which reviewed return-rate data from fourteen "
        "library systems that eliminated fines between 2017 and 2022."
    )


def _rebuttal_paragraph(p):
    if p == 1:
        return (
            "A skeptic on the board points to overdue fines as a source of "
            "materials-replacement funding, and argues that eliminating them systemwide will "
            "leave a shortfall the consortium has not planned for."
        )
    return (
        "Consortium finance records show fine revenue covered under 2 percent of the annual "
        "materials budget over the last three fiscal years, and the four pilot branches "
        "absorbed the loss without a measurable change to their replacement-copy spending, so "
        "the shortfall the objection anticipates has not materialized where the policy has "
        "already been tried."
    )


def render(doc):
    return render_blocks(doc.blocks)  # blocks joined by one blank line

# --- 4. Injectors, keyed by criterion ID. Each returns a new composition, never mutates. --------


@injector("TOULMIN-CLAIM-MARKER")
def inject_claim_marker(rng, doc, target):
    """Replace the recommendation sentence with its marker-free form (RECOMMENDATION_MARKER_FREE
    is the fixed text that follows the marker clause in every possible composition), leaving no
    phrase from the marker lexicon anywhere in the document. A wholesale replacement rather than a
    parse of the slot's current text, so it does not matter whether TOULMIN-HEDGE-DENSITY's
    document-wide rewrite already touched this slot before this injector runs."""
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, RECOMMENDATION_MARKER_FREE),
        slot="h0",
        severity_expected=3,
        description=(
            "The leading conclusion-signalling clause was removed from the sentence stating "
            "the recommendation, and no phrase from the marker lexicon appears anywhere else in "
            "the document."
        ),
    )


@injector("TOULMIN-HEDGE-DENSITY")
def inject_hedge_density(rng, doc, target):
    """Prepend a hedging clause to every sentence of every paragraph in the document, document-
    wide, pushing the hedged-sentence ratio well past the fire threshold. Any later injector that
    fully overwrites one of these paragraphs simply replaces the hedged text outright, so running
    this first (it always sorts first, being the lowest section number) never conflicts with a
    judged injector's own rewrite of its own slot."""
    composed = doc
    for block in doc.blocks:
        if block.kind != "paragraph":
            continue
        sentences = split_sentences(block.text)
        hedged_sentences = []
        for sentence in sentences:
            _, template = rng.choice(HEDGE_TEMPLATES)
            lowered = f"{sentence[0].lower()}{sentence[1:]}" if sentence else sentence
            hedged_sentences.append(template.format(s=lowered))
        composed = composed.replace(block.slot, " ".join(hedged_sentences))
    return InjectionResult(
        composed=composed,
        slot="h0",
        severity_expected=3,
        description=(
            "A hedging clause was inserted at the start of every sentence in every paragraph of "
            "the document, raising the hedged-sentence ratio well past the threshold."
        ),
    )


@injector("TOULMIN-CLAIM")
def inject_claim(rng, doc, target):
    """Replace the specific, checkable recommendation sentence with a generic statement broad
    enough that no reader could disagree with it."""
    slot = f"s{target.section}.p{target.block}"
    new_text = rng.choice(CLAIM_VAGUE_VARIANTS)
    return InjectionResult(
        composed=doc.replace(slot, new_text),
        slot=slot,
        severity_expected=3,
        description=(
            "The specific, checkable recommendation sentence was replaced with a generic "
            "statement broad enough that no reader could disagree with it."
        ),
    )


@injector("TOULMIN-QUALIFIER")
def inject_qualifier(rng, doc, target):
    """Replace the sentence bounding the recommendation to the evidence's actual scope with an
    unqualified absolute claim the evidence does not support."""
    slot = f"s{target.section}.p{target.block}"
    new_text = rng.choice(QUALIFIER_OVERREACH_VARIANTS)
    return InjectionResult(
        composed=doc.replace(slot, new_text),
        slot=slot,
        severity_expected=3,
        description=(
            "The sentence bounding the recommendation to the evidence's actual scope was "
            "replaced with an unqualified absolute claim the evidence does not support."
        ),
    )


@injector("TOULMIN-WARRANT")
def inject_warrant(rng, doc, target):
    """Replace the sentence stating the general principle that connects the evidence to the
    conclusion with an unrelated operational detail, leaving the connection unstated."""
    slot = f"s{target.section}.p{target.block}"
    new_text = rng.choice(WARRANT_GAP_VARIANTS)
    return InjectionResult(
        composed=doc.replace(slot, new_text),
        slot=slot,
        severity_expected=3,
        description=(
            "The sentence stating the general principle that connects the evidence to the "
            "conclusion was replaced with an unrelated operational detail, leaving the "
            "connection unstated."
        ),
    )


@injector("TOULMIN-BACKING")
def inject_backing(rng, doc, target):
    """Replace the sentence naming the source that supports the general principle with an
    assertion that treats the principle as self-evident."""
    slot = f"s{target.section}.p{target.block}"
    new_text = rng.choice(BACKING_UNSUPPORTED_VARIANTS)
    return InjectionResult(
        composed=doc.replace(slot, new_text),
        slot=slot,
        severity_expected=3,
        description=(
            "The sentence naming the study or standard that supports the general principle was "
            "replaced with an assertion that treats the principle as self-evident."
        ),
    )


@injector("TOULMIN-REBUTTAL")
def inject_rebuttal(rng, doc, target):
    """Replace the paragraph answering the objection raised in the preceding paragraph with an
    unrelated status update, leaving the objection stated and then abandoned."""
    slot = f"s{target.section}.p{target.block}"
    new_text = rng.choice(REBUTTAL_ABANDONED_VARIANTS)
    return InjectionResult(
        composed=doc.replace(slot, new_text),
        slot=slot,
        severity_expected=3,
        description=(
            "The paragraph answering the objection raised in the preceding paragraph was "
            "replaced with an unrelated status update, leaving the objection stated and then "
            "abandoned."
        ),
    )


@injector("TOULMIN-GROUNDS")
def inject_grounds(rng, doc, target):
    """Replace the paragraph offering checkable pilot evidence with a restatement of the
    recommendation in different words."""
    slot = f"s{target.section}.p{target.block}"
    new_text = rng.choice(GROUNDS_RESTATEMENT_VARIANTS)
    return InjectionResult(
        composed=doc.replace(slot, new_text),
        slot=slot,
        severity_expected=2,
        description=(
            "The paragraph offering checkable pilot evidence was replaced with a restatement of "
            "the recommendation in different words."
        ),
    )

# --- 5. Addressing. Called by the harness after every injection, on the final composition. ------


def _ordinal_within_section(doc, slot):
    """1-based ordinal of the paragraph at `slot` among paragraph blocks in its own immediate
    (level-2) section, counted in document order from the final composition. Never read off the
    slot's own `.p{n}` suffix, per bench/generator/README.md's "slots are identities" rule."""
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
    if block.kind == "heading" and block.level == 1:
        # TOULMIN-CLAIM-MARKER and TOULMIN-HEDGE-DENSITY are document-level
        # measurements (skills/critique-argument/scripts/checks.py,
        # _document_location): the manifest location for both is the title
        # heading, phrased the same way the real skill's scripted lane
        # phrases it (see skills/critique-argument/examples/golden-02.json).
        path = heading_path(doc, slot)
        return Location(
            kind="heading-path",
            heading_path=path,
            text=f'the whole document, under its "{path[-1]}" heading',
        )
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

# --- 6. Recipes. Three artifacts, one of them clean, matching bench/README.md's corpus design ---
#        table for the argument domain (3 artifacts, 1 clean). All eight criteria are planted
#        across the two seeded recipes; no recipe repeats a criterion within one section. --------

SHAPE = {"paragraphs": (2, 2, 3, 2, 2)}

RECIPES = (
    Recipe(id="argument-001", shape=SHAPE, plants=(
        Plant("TOULMIN-WARRANT", Target(section=4, block=1), severity_expected=3),
        Plant("TOULMIN-BACKING", Target(section=4, block=2), severity_expected=3),
        Plant("TOULMIN-REBUTTAL", Target(section=5, block=2), severity_expected=3),
    )),
    Recipe(id="argument-002", shape=SHAPE, plants=(
        Plant("TOULMIN-CLAIM-MARKER", Target(section=3, block=1), severity_expected=3),
        Plant("TOULMIN-HEDGE-DENSITY", Target(section=1), severity_expected=3),
        Plant("TOULMIN-CLAIM", Target(section=3, block=2), severity_expected=3),
        Plant("TOULMIN-QUALIFIER", Target(section=3, block=3), severity_expected=3),
        Plant("TOULMIN-GROUNDS", Target(section=2, block=1), severity_expected=2),
    )),
    Recipe(id="argument-003", shape=SHAPE, plants=()),
)

DOMAIN = Domain(
    name="argument",
    artifact_type="markdown-prose",
    extension=".md",
    namespaces=("TOULMIN",),
    compose=compose,
    render=render,
    address=address,
    injectors=INJECTORS,
    recipes=RECIPES,
)
