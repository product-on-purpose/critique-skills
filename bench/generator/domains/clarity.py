"""Clarity domain: bench corpus for critique-clarity.

Artifact type: markdown-prose. Namespaces: PLAIN, WILLIAMS. Scored corpus
(S-05, critique-clarity, core). Subject matter is an invented internal
benefits memo for a fictional employer ("Home-Office Equipment Stipend
Policy"), the same bureaucratic-memo register the PLAIN rubric itself
targets.

Every one of critique-clarity's 15 scripted criteria has its own injector
here, per bench/generator/README.md's checklist ("Write one injector per
criterion. Cover every scripted-lane criterion and at least three
judged-lane criteria"):

    PLAIN-ACTIVE, PLAIN-CONCISE, PLAIN-DOUBLE-NEGATIVE, PLAIN-HEADINGS,
    PLAIN-JARGON, PLAIN-LISTS, PLAIN-MUST, PLAIN-NOMINALIZATION,
    PLAIN-PARAGRAPH, PLAIN-PRONOUNS, PLAIN-SENTENCE-LENGTH,
    PLAIN-SUBJECT-VERB-OBJECT, PLAIN-TRANSITIONS, WILLIAMS-PARALLELISM,
    WILLIAMS-SHAPE.

Five judged-lane criteria (exceeding the three-criterion floor) also carry
injectors, illustrating a defect no fixed pattern can detect:

    PLAIN-AUDIENCE, PLAIN-CONSISTENT-TERMS, PLAIN-MAIN-IDEA-FIRST,
    WILLIAMS-CHARACTER-ACTION, WILLIAMS-COHESION.

Document shape (thirteen sections, one role each; shared by every recipe):

    1.  Program Overview             filler, no criterion targets it
    2.  Eligibility                  PLAIN-MAIN-IDEA-FIRST, PLAIN-DOUBLE-NEGATIVE, PLAIN-PARAGRAPH
    3.  How to Apply                 PLAIN-LISTS, PLAIN-SUBJECT-VERB-OBJECT, PLAIN-SENTENCE-LENGTH
    4.  Approval Timeline            PLAIN-ACTIVE, PLAIN-TRANSITIONS
    5.  Required Documentation       PLAIN-JARGON, PLAIN-MUST
    6.  Reimbursement Amounts        PLAIN-NOMINALIZATION, PLAIN-CONCISE
    7.  Restrictions and Exceptions  PLAIN-PRONOUNS, WILLIAMS-SHAPE
    8.  Terminology Notes            PLAIN-CONSISTENT-TERMS, PLAIN-AUDIENCE
    9.  Request Steps                WILLIAMS-PARALLELISM
    10. Special Cases                PLAIN-HEADINGS (the section's own heading)
    11. Program Coordination         WILLIAMS-COHESION
    12. Review Responsibility        WILLIAMS-CHARACTER-ACTION
    13. Questions and Updates        filler, no criterion targets it

Every injector below does a wholesale replacement of its own target
paragraph's (or, for PLAIN-HEADINGS, heading's) text, the same technique
critique-argument's own domain module uses and for the same reason: text
this module's own `compose` generated from a template it owns can be
inverted with no parser, per bench/generator/README.md, "Transforms
operate on a grammar you own." Injector order therefore never matters for
correctness, since no injector reads another injector's output.

Two pairs of criteria in this rubric test closely related phenomena at
different thresholds, and a sentence built to genuinely trigger one member
of a pair will, by construction of the real check functions, always also
satisfy the other:

  - PLAIN-SENTENCE-LENGTH fires whenever a sentence exceeds 30 words with
    any subordinate-clause markers, or 50 words outright.
    WILLIAMS-SHAPE requires at least 40 words, which is always already
    past PLAIN-SENTENCE-LENGTH's 30-word floor, so the WILLIAMS-SHAPE
    plant at section 7 is also a genuine (unplanted) PLAIN-SENTENCE-LENGTH
    finding a correct scripted lane will report. Both land at severity 3,
    since the planted sentence runs past both criteria's own hard
    thresholds.
  - PLAIN-PARAGRAPH's topic-mismatch branch and WILLIAMS-COHESION both
    test whether a passage's sentences hang together; a paragraph built to
    demonstrate WILLIAMS-COHESION's severity-3 anchor (a subject that
    changes in every sentence) will also read, by PLAIN-PARAGRAPH's own
    word-overlap heuristic, as an opening sentence that fails to preview
    the paragraph's topic.

Both overlaps are a property of the rubric's own design, not an artifact of
this module's prose; they are called out here rather than engineered away,
because engineering them away would mean the corpus no longer demonstrates
the very sentence and paragraph shapes the severity-3 anchors describe.

A third overlap used to be listed here and is now gone rather than
documented. PLAIN-PARAGRAPH's length branch and PLAIN-HEADINGS'
section-length branch once shared the identical 150-word constant, and
since a section is never shorter than its longest paragraph, every planted
over-long paragraph also produced a PLAIN-HEADINGS finding about the same
words. That was a constant collision in checks.py, not a property of the
rubric; the section threshold now sits at 400 words, well above the
paragraph threshold, and one over-long paragraph produces one finding.

Output bound budget
-------------------

A skill reports every severity 3 and 4 finding but at most five below that
(methodology section 7; `skills/_shared/envelope.py`'s
OUTPUT_BOUND_BELOW_SEVERITY_3). A recipe that plants more than five
below-severity-3 defects in one artifact therefore guarantees that some of
them cannot appear in any contract-valid envelope, and recall for those
criteria is unmeasurable on that artifact no matter how well the skill
detects them. An earlier arrangement of these recipes planted seven and
nine, and four planted defects across the corpus were unreportable for that
reason alone.

The rule this module now keeps: **the number of below-severity-3 findings a
correct run produces on one artifact, counting unplanted-but-genuine ones
and counting a plant that fires more than once as more than one, must not
exceed five.** Current counts are 5, 5, and 4 (see the per-recipe comments
in section 6). Anyone adding a plant here has to recount, not just check
that the injector exists; the harness cannot check this, because it does
not know what a correct run reports.
"""

from __future__ import annotations

from bench.generator.api import Domain, InjectionResult, Location, Plant, Recipe, Target, injector
from bench.generator.markdown import Block, Document, heading_path, paragraph_index, render_blocks
from bench.generator.text import ORDINALS

# --- 1. Vocabulary. Frozen tuples. Order is part of the corpus identity: appending is safe,
#        reordering or removing regenerates every clarity artifact. ------------------------------

DOC_TITLE = "Home-Office Equipment Stipend Policy"
SECTION_TITLES = (
    "Program Overview",
    "Eligibility",
    "How to Apply",
    "Approval Timeline",
    "Required Documentation",
    "Reimbursement Amounts",
    "Restrictions and Exceptions",
    "Terminology Notes",
    "Request Steps",
    "Special Cases",
    "Program Coordination",
    "Review Responsibility",
    "Questions and Updates",
)

# Filler paragraphs (sections 1, 10, 13): plain active-voice status
# sentences with no comma-joined series, no negation marker, no jargon, no
# institutional pronoun substitute, and no subordinate-clause pileup, so
# they never trip a scripted criterion by accident. A non-first paragraph
# opens with a transition word for the same reason every other non-first,
# non-PLAIN-TRANSITIONS-target paragraph in this module does: PLAIN-
# TRANSITIONS is a whole-document check, and any paragraph that is not the
# first in its section and does not open with a transition word is a real
# (if unplanted) finding.
FILLER_SUBJECTS = (
    "The benefits team",
    "The IT asset group",
    "The people operations office",
    "The finance liaison",
)
FILLER_VERBS = ("tracks", "reviews", "publishes", "updates")
FILLER_OBJECTS = (
    "the stipend budget",
    "the equipment catalog",
    "the reimbursement log",
    "the vendor list",
)
FILLER_WHENS = (
    "each quarter",
    "at the start of the fiscal year",
    "after every open enrollment period",
    "on the first business day of the month",
)
FILLER_TAILS = (
    "Every entry carries a date stamp so the record stays easy to audit.",
    "A copy of each update goes to the shared benefits folder the same day.",
    "The most recent version supersedes the one that came before it.",
    "Staff can request a printed copy from the benefits team at any time.",
)
FILLER_CONT_OPENERS = ("In addition,", "Also,", "Similarly,", "Likewise,")

# Section 2, paragraph 1: PLAIN-MAIN-IDEA-FIRST (judged).
MAIN_IDEA_FIRST_CLEAN = (
    "Full-time employees who have completed 90 days of continuous service are "
    "eligible for the home-office equipment stipend. The stipend covers one "
    "claim per employee per benefit year."
)
MAIN_IDEA_FIRST_DEFECT = (
    "If the position counts as full-time, the stipend can apply. If the "
    "employee has completed 90 days of continuous service, the stipend can "
    "apply. If the request arrives before the benefit year ends, the stipend "
    "can apply. Only once every condition above is met does the home-office "
    "equipment stipend become available to the employee."
)

# Section 2, paragraph 2: PLAIN-DOUBLE-NEGATIVE.
DOUBLE_NEGATIVE_CLEAN = (
    "However, employees on an approved leave of absence remain eligible once "
    "they return to active status. The stipend clock resumes on their first "
    "day back."
)
DOUBLE_NEGATIVE_DEFECT = (
    "However, reimbursement is not available without a completed receipt. A "
    "scanned copy sent by email satisfies the requirement."
)

# Section 2, paragraph 3: PLAIN-PARAGRAPH (length branch: the defect text
# alone runs past the 150-word threshold; the clean text stays short).
PARAGRAPH_CLEAN = (
    "In addition, eligibility applies only to a dedicated home workspace the "
    "employee personally uses. Shared or communal spaces do not qualify "
    "under this policy."
)
PARAGRAPH_DEFECT = (
    "In addition, eligibility for the workspace stipend depends on several "
    "details the reviewer checks one at a time. The workspace must sit "
    "inside the employee's primary residence for the stipend to apply. A "
    "workspace located in a shared coworking space does not qualify for the "
    "stipend under this section. A workspace used only occasionally for "
    "calls does not meet the bar the stipend policy sets. The reviewer "
    "confirms the workspace address matches the address already on file "
    "with payroll. A workspace shared with a roommate can still qualify if "
    "the desk area belongs to the employee alone. The stipend covers only "
    "the equipment placed inside that confirmed workspace, nothing located "
    "elsewhere in the home. A workspace that changes address during the "
    "benefit year needs a fresh confirmation before the stipend continues. "
    "The reviewer logs every workspace confirmation in the same shared "
    "tracking sheet the benefits team maintains. A workspace confirmation "
    "from more than one year ago no longer satisfies the stipend "
    "requirement on its own."
)

# Section 3, paragraph 1: PLAIN-LISTS.
LISTS_CLEAN = (
    "Employees start a stipend request in the benefits portal. The portal "
    "walks through each step in order."
)
LISTS_DEFECT = (
    "Employees must submit the receipt, the manager's approval form, and "
    "the original purchase order before the review begins."
)

# Section 3, paragraph 2: PLAIN-SUBJECT-VERB-OBJECT.
SVO_CLEAN = (
    "Also, the portal saves a draft automatically every few minutes. "
    "Employees can return to finish later without losing progress."
)
SVO_DEFECT = (
    "Also, the stipend request, once the manager signs it, after finance "
    "confirms the budget line, moves to final processing. The employee "
    "receives a confirmation email once processing finishes."
)

# Section 3, paragraph 3: PLAIN-SENTENCE-LENGTH.
SENTENCE_LENGTH_CLEAN = (
    "Then, the employee reviews the confirmation summary before submitting "
    "the final request. The summary shows the equipment cost and the "
    "requested delivery date."
)
SENTENCE_LENGTH_DEFECT = (
    "Then, the review takes longer because the manager who normally handles "
    "it is traveling; the backup reviewer who covers for absences was not "
    "told that the request needs sign-off before the portal releases the "
    "confirmation email."
)

# Section 4, paragraph 1: PLAIN-ACTIVE.
ACTIVE_CLEAN = (
    "The manager reviews the request within two business days. The manager "
    "confirms the equipment category matches the approved list."
)
ACTIVE_DEFECT = (
    "The request is reviewed within two business days. The manager confirms "
    "the equipment category matches the approved list."
)

# Section 4, paragraph 2: PLAIN-TRANSITIONS. The clean form opens with a
# transition word like every other non-first paragraph in this module; the
# defect removes exactly that opener, which is the entire violation.
TRANSITIONS_CLEAN = (
    "However, an incomplete request pauses the timeline until the missing "
    "item arrives. The requester gets an automatic reminder after three "
    "days."
)
TRANSITIONS_DEFECT = (
    "An incomplete request pauses the timeline until the missing item "
    "arrives. The requester gets an automatic reminder after three days."
)

# Section 5, paragraph 1: PLAIN-JARGON.
JARGON_CLEAN = (
    "Employees keep proof of purchase for every stipend item. A photo of "
    "the receipt is enough for most requests."
)
JARGON_DEFECT = (
    "The manager approves items pursuant to internal discretion, "
    "notwithstanding the standard review checklist."
)

# Section 5, paragraph 2: PLAIN-MUST. The defect plants exactly one
# non-must requirement statement in a document that states every other
# requirement with must, which is the criterion's own severity 2 anchor, so
# severity_expected is 2 in every recipe that plants it. checks.py escalates
# to 3 only when a document carries two or more such statements alongside
# must or should; a corpus artifact demonstrating that would need a second
# planted PLAIN-MUST instance in another section, which the at-most-one-
# plant-per-criterion-per-artifact rule this module keeps does not allow.
MUST_CLEAN = "Additionally, employees must retain receipts for one year after the purchase date."
MUST_DEFECT = "Additionally, employees shall retain receipts for one year after the purchase date."

# Section 6, paragraph 1: PLAIN-NOMINALIZATION.
NOMINALIZATION_CLEAN = (
    "The stipend pays up to 500 dollars per benefit year. The finance "
    "office deposits the amount within one pay cycle."
)
NOMINALIZATION_DEFECT = (
    "The finance office conducts an evaluation of every submitted receipt "
    "before it approves the amount."
)

# Section 6, paragraph 2: PLAIN-CONCISE.
CONCISE_CLEAN = "Also, unused stipend amounts do not roll over to the next benefit year."
CONCISE_DEFECT = (
    "Also, the deposit happens in order to offset costs the employee "
    "already paid at this point in time."
)

# Section 7, paragraph 1: PLAIN-PRONOUNS.
# Both institutional substitutes sit in one sentence rather than one each in
# two sentences. One planted defect should produce one finding: the earlier
# two-sentence form tripped the check twice and spent two of the artifact's
# five below-severity-3 output-bound slots on a single plant (see "Output
# bound budget" in the module docstring).
PRONOUNS_CLEAN = (
    "You must keep your equipment in good working condition and we may ask "
    "for a brief photo check once a year."
)
PRONOUNS_DEFECT = (
    "The applicant must keep the equipment in good working condition and "
    "this office may ask for a brief photo check once a year."
)

# Section 7, paragraph 2: WILLIAMS-SHAPE, at its own severity 3 anchor (well
# past 60 words, with subordinate-clause markers stacked ahead of the main
# verb). See the module docstring for why this defect is also a genuine,
# unplanted PLAIN-SENTENCE-LENGTH finding, and why both land at severity 3.
# The defect carries exactly one comma, the one after its opening transition
# word: a second comma would read as an interrupting aside and add an
# unplanted PLAIN-SUBJECT-VERB-OBJECT finding, and an and or or joining two
# comma-separated segments would read as a series and add an unplanted
# PLAIN-LISTS one.
SHAPE_CLEAN = "Similarly, the policy applies to one device per category per employee."
SHAPE_DEFECT = (
    "Similarly, the policy applies to one device per category per employee "
    "whenever the benefits team confirms that the role genuinely requires a "
    "second device because fieldwork regularly takes the employee away from "
    "the single fixed desk that the standard equipment list assumes every "
    "applicant has for the whole benefit year while the finance office "
    "tracks the second device against the same annual amount that the "
    "equipment catalog publishes for each category."
)

# Section 8, paragraph 1: PLAIN-CONSISTENT-TERMS (judged). The defect
# *enacts* the drift, naming the one thing three ways in three sentences,
# rather than narrating that a document elsewhere drifts. An earlier form
# did the latter, which failed the criterion's own operational test twice
# over: it stated the equivalence out loud (a stated equivalence is exactly
# the signal the test exempts), and it made the plant findable by reading
# the paragraph's self-description instead of by noticing the drift
# (bench/generator/README.md, checklist step 10).
CONSISTENT_TERMS_CLEAN = (
    "You record the stipend item on the request form. Finance reconciles the "
    "stipend item against the request log each month. Payroll releases the "
    "stipend item amount after that monthly review."
)
CONSISTENT_TERMS_DEFECT = (
    "You record the stipend item on the request form. Finance reconciles the "
    "reimbursable item against the request log each month. Payroll releases "
    "the covered purchase amount after that monthly review."
)

# Section 8, paragraph 2: PLAIN-AUDIENCE (judged). Same rule as the
# paragraph above: the defect drops one manager-facing imperative between
# two employee-facing sentences, with nothing marking the switch, so a
# reader genuinely cannot tell which sentence is theirs to act on. The
# earlier form announced the switch in so many words, which is a defect
# description, not a defect.
AUDIENCE_CLEAN = (
    "Also, you submit the request in the portal. You track its status there "
    "until the payment clears."
)
AUDIENCE_DEFECT = (
    "Also, you submit the request in the portal. Countersign the employee "
    "request within two business days. You track its status there until the "
    "payment clears."
)

# Section 9, paragraph 1: WILLIAMS-PARALLELISM. A two-item, comma-joined
# series (PLAIN-LISTS needs three or more items, so this stays below its
# threshold in both the clean and the defect form).
PARALLELISM_CLEAN = "Completing the request begins with confirming eligibility, and uploading the receipt."
PARALLELISM_DEFECT = "Completing the request begins with confirming eligibility, and the uploaded receipt."

# Section 10: PLAIN-HEADINGS. The defect replaces the section's own
# heading text with an entry from checks.py's fixed non-specific-label
# list; the paragraph beneath it is filler.
HEADING_LABEL_DEFECT = "Overview"

# Section 11, paragraph 1: WILLIAMS-COHESION (judged). See the module
# docstring for why the defect is also a genuine, unplanted PLAIN-
# PARAGRAPH finding.
COHESION_CLEAN = (
    "The benefits team coordinates every stipend request from intake to "
    "payout. The team logs each request the moment it arrives. The team "
    "then routes the request to the correct approver based on department. "
    "Once approved, the team schedules the reimbursement for the next pay "
    "cycle."
)
COHESION_DEFECT = (
    "The benefits team coordinates every stipend request from intake to "
    "payout. A separate audit last spring reviewed unrelated travel "
    "expenses. Federal guidance on remote work continues to evolve each "
    "year. The office coffee budget was reset at the start of the quarter."
)

# Section 12, paragraph 1: WILLIAMS-CHARACTER-ACTION (judged).
CHARACTER_ACTION_CLEAN = (
    "The finance office reviews every stipend request over 200 dollars "
    "before it pays out. The finance office also flags any request that "
    "repeats within the same quarter."
)
CHARACTER_ACTION_DEFECT = (
    "The determination of stipend eligibility happens before any payment "
    "goes out. The escalation of repeat requests happens automatically "
    "within the same quarter."
)

INJECTORS = {}

# --- 2 and 3. Composition. Structure comes from the recipe shape; the stream picks words only. --


def compose(rng, shape):
    counts = shape["paragraphs"]  # (2,3,3,2,2,2,2,2,1,1,1,1,1): thirteen sections, this domain's only shape
    blocks = [Block(kind="heading", level=1, text=f"# {DOC_TITLE}", slot="h0")]
    for section, count in enumerate(counts, start=1):
        title = SECTION_TITLES[section - 1]
        blocks.append(Block(kind="heading", level=2, text=f"## {title}", slot=f"s{section}.h"))
        for p in range(1, count + 1):
            prng = rng.child("para", section, p)
            text = _paragraph_text(prng, section, p)
            blocks.append(Block(kind="paragraph", level=0, text=text, slot=f"s{section}.p{p}"))
    return Document(tuple(blocks))


def _filler_paragraph(rng, *, first):
    subject = rng.choice(FILLER_SUBJECTS)
    verb = rng.choice(FILLER_VERBS)
    obj = rng.choice(FILLER_OBJECTS)
    when = rng.choice(FILLER_WHENS)
    tail = rng.choice(FILLER_TAILS)
    if first:
        lead = f"{subject} {verb} {obj} {when}."
    else:
        opener = rng.choice(FILLER_CONT_OPENERS)
        lowered = f"{subject[0].lower()}{subject[1:]}"
        lead = f"{opener} {lowered} {verb} {obj} {when}."
    return f"{lead} {tail}"


# (section, paragraph) -> (clean text, defect text). Filler slots are not
# listed here; _paragraph_text falls back to _filler_paragraph for any
# slot absent from this table.
_TARGET_TEXT = {
    (2, 1): (MAIN_IDEA_FIRST_CLEAN, MAIN_IDEA_FIRST_DEFECT),
    (2, 2): (DOUBLE_NEGATIVE_CLEAN, DOUBLE_NEGATIVE_DEFECT),
    (2, 3): (PARAGRAPH_CLEAN, PARAGRAPH_DEFECT),
    (3, 1): (LISTS_CLEAN, LISTS_DEFECT),
    (3, 2): (SVO_CLEAN, SVO_DEFECT),
    (3, 3): (SENTENCE_LENGTH_CLEAN, SENTENCE_LENGTH_DEFECT),
    (4, 1): (ACTIVE_CLEAN, ACTIVE_DEFECT),
    (4, 2): (TRANSITIONS_CLEAN, TRANSITIONS_DEFECT),
    (5, 1): (JARGON_CLEAN, JARGON_DEFECT),
    (5, 2): (MUST_CLEAN, MUST_DEFECT),
    (6, 1): (NOMINALIZATION_CLEAN, NOMINALIZATION_DEFECT),
    (6, 2): (CONCISE_CLEAN, CONCISE_DEFECT),
    (7, 1): (PRONOUNS_CLEAN, PRONOUNS_DEFECT),
    (7, 2): (SHAPE_CLEAN, SHAPE_DEFECT),
    (8, 1): (CONSISTENT_TERMS_CLEAN, CONSISTENT_TERMS_DEFECT),
    (8, 2): (AUDIENCE_CLEAN, AUDIENCE_DEFECT),
    (9, 1): (PARALLELISM_CLEAN, PARALLELISM_DEFECT),
    (11, 1): (COHESION_CLEAN, COHESION_DEFECT),
    (12, 1): (CHARACTER_ACTION_CLEAN, CHARACTER_ACTION_DEFECT),
}

_FILLER_SECTIONS = frozenset({1, 10, 13})


def _paragraph_text(rng, section, p):
    if section in _FILLER_SECTIONS:
        return _filler_paragraph(rng, first=(p == 1))
    clean, _defect = _TARGET_TEXT[(section, p)]
    return clean


def render(doc):
    return render_blocks(doc.blocks)  # blocks joined by one blank line

# --- 4. Injectors, keyed by criterion ID. Each returns a new composition, never mutates. --------


@injector("PLAIN-MAIN-IDEA-FIRST")
def inject_main_idea_first(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, MAIN_IDEA_FIRST_DEFECT),
        slot=slot,
        severity_expected=3,
        description=(
            "The passage opens with a run of conditions and only states the governing "
            "rule in its final sentence, so the reader has to reach the end before the "
            "opening sentences make sense."
        ),
    )


@injector("PLAIN-DOUBLE-NEGATIVE")
def inject_double_negative(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, DOUBLE_NEGATIVE_DEFECT),
        slot=slot,
        severity_expected=2,
        description=(
            "Two negation markers from the fixed negation list co-occur in one clause, so "
            "the reader has to work out the statement's logical sign before understanding it."
        ),
    )


@injector("PLAIN-PARAGRAPH")
def inject_paragraph(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, PARAGRAPH_DEFECT),
        slot=slot,
        severity_expected=2,
        description="The paragraph runs well past the length threshold with no intervening break.",
    )


@injector("PLAIN-LISTS")
def inject_lists(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, LISTS_DEFECT),
        slot=slot,
        severity_expected=2,
        description=(
            "A sentence embeds three comma-separated parallel items inline rather than "
            "presenting them as a formatted list."
        ),
    )


@injector("PLAIN-SUBJECT-VERB-OBJECT")
def inject_svo(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, SVO_DEFECT),
        slot=slot,
        severity_expected=2,
        description=(
            "Two comma-set-off clauses intervene between a sentence's apparent subject and its verb."
        ),
    )


@injector("PLAIN-SENTENCE-LENGTH")
def inject_sentence_length(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, SENTENCE_LENGTH_DEFECT),
        slot=slot,
        severity_expected=3,
        description=(
            "A single sentence runs long with several subordinate-clause markers, longer "
            "than the reader can hold in mind on one pass."
        ),
    )


@injector("PLAIN-ACTIVE")
def inject_active(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, ACTIVE_DEFECT),
        slot=slot,
        severity_expected=2,
        description="One sentence is recast into passive voice with the acting party deleted.",
        sentence=1,
    )


@injector("PLAIN-TRANSITIONS")
def inject_transitions(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, TRANSITIONS_DEFECT),
        slot=slot,
        severity_expected=2,
        description=(
            "The paragraph opens with none of the fixed transition words, so the reader "
            "is not told how it relates to the paragraph before it."
        ),
    )


@injector("PLAIN-JARGON")
def inject_jargon(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, JARGON_DEFECT),
        slot=slot,
        severity_expected=2,
        description="A legal-jargon term from the fixed list appears with no plain-language definition nearby.",
    )


@injector("PLAIN-MUST")
def inject_must(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, MUST_DEFECT),
        slot=slot,
        severity_expected=2,
        description="One binding requirement is stated in a non-mandatory register in a document that otherwise states requirements plainly.",
    )


@injector("PLAIN-NOMINALIZATION")
def inject_nominalization(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, NOMINALIZATION_DEFECT),
        slot=slot,
        severity_expected=2,
        description=(
            "The action is buried inside a nominalized noun carried by a generic support "
            "verb, instead of stated as the sentence's own main verb."
        ),
    )


@injector("PLAIN-CONCISE")
def inject_concise(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, CONCISE_DEFECT),
        slot=slot,
        severity_expected=2,
        description="Two wordy constructions from the fixed list appear where a shorter equivalent exists.",
    )


@injector("PLAIN-PRONOUNS")
def inject_pronouns(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, PRONOUNS_DEFECT),
        slot=slot,
        severity_expected=2,
        description=(
            "The reader and the writer's organization are routed through third-person "
            "institutional substitutes instead of direct address."
        ),
    )


@injector("WILLIAMS-SHAPE")
def inject_shape(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, SHAPE_DEFECT),
        slot=slot,
        severity_expected=3,
        description=(
            "A long sentence stacks subordinate-clause markers between its subject and its "
            "main verb instead of holding the main clause together."
        ),
    )


@injector("PLAIN-CONSISTENT-TERMS")
def inject_consistent_terms(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, CONSISTENT_TERMS_DEFECT),
        slot=slot,
        severity_expected=3,
        description=(
            "Three different terms are used interchangeably for the same single concept "
            "across the passage, with no signal they are meant to mean the same thing."
        ),
    )


@injector("PLAIN-AUDIENCE")
def inject_audience(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, AUDIENCE_DEFECT),
        slot=slot,
        severity_expected=2,
        description=(
            "The passage addresses one reader directly, then switches mid-passage to "
            "instructing a second, different reader with no signal the audience changed."
        ),
    )


@injector("WILLIAMS-PARALLELISM")
def inject_parallelism(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, PARALLELISM_DEFECT),
        slot=slot,
        severity_expected=2,
        description="The series' two items mix grammatical forms at their head words instead of sharing one form.",
    )


@injector("PLAIN-HEADINGS", phase="text")
def inject_headings(rng, doc, target):
    """Replace the section's own heading text with an entry from the fixed
    non-specific-label list. A text-phase rewrite of one block's own
    content, not a structural change, so the default phase applies."""
    slot = f"s{target.section}.h"
    return InjectionResult(
        composed=doc.replace(slot, f"## {HEADING_LABEL_DEFECT}"),
        slot=slot,
        severity_expected=2,
        description=(
            "The heading text matches the fixed list of non-specific heading labels, so a "
            "reader scanning headings cannot tell whether the section beneath applies to them."
        ),
    )


@injector("WILLIAMS-COHESION")
def inject_cohesion(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, COHESION_DEFECT),
        slot=slot,
        severity_expected=3,
        description=(
            "The passage changes its subject in every sentence, with no sentence picking "
            "up the topic the one before it just established."
        ),
    )


@injector("WILLIAMS-CHARACTER-ACTION")
def inject_character_action(rng, doc, target):
    slot = f"s{target.section}.p{target.block}"
    return InjectionResult(
        composed=doc.replace(slot, CHARACTER_ACTION_DEFECT),
        slot=slot,
        severity_expected=3,
        description=(
            "Every sentence in the passage runs its action through an abstract noun as "
            "subject instead of naming the real-world actor responsible for it."
        ),
    )

# --- 5. Addressing. Called by the harness after every injection, on the final composition. ------


def _ordinal_within_section(doc, slot):
    """1-based ordinal of the paragraph at `slot` among paragraph blocks in
    its own immediate (level-2) section, counted in document order from
    the final composition. Never read off the slot's own `.p{n}` suffix,
    per bench/generator/README.md's "slots are identities" rule."""
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

# --- 6. Recipes. Four artifacts, one of them clean, matching bench/README.md's corpus design ---
#        table for the clarity domain (4 artifacts, 1 clean). All twenty registered criteria are
#        planted exactly once, spread across the three seeded recipes; no recipe repeats a
#        criterion within one section. Plants are grouped by the severity a correct run assigns
#        them, not by rubric or by section, because the output bound is what decides whether a
#        planted defect can appear in an envelope at all; see "Output bound budget" in the module
#        docstring for the arithmetic each grouping has to satisfy. ------------------------------

SHAPE = {"paragraphs": (2, 3, 3, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1)}

RECIPES = (
    # Below-severity-3 findings: 5 (ACTIVE, CONCISE, DOUBLE-NEGATIVE, HEADINGS, JARGON).
    Recipe(id="clarity-001", shape=SHAPE, plants=(
        Plant("PLAIN-ACTIVE", Target(section=4, block=1), severity_expected=2),
        Plant("PLAIN-CONCISE", Target(section=6, block=2), severity_expected=2),
        Plant("PLAIN-DOUBLE-NEGATIVE", Target(section=2, block=2), severity_expected=2),
        Plant("PLAIN-HEADINGS", Target(section=10), severity_expected=2),
        Plant("PLAIN-JARGON", Target(section=5, block=1), severity_expected=2),
        Plant("PLAIN-SENTENCE-LENGTH", Target(section=3, block=3), severity_expected=3),
        Plant("PLAIN-MAIN-IDEA-FIRST", Target(section=2, block=1), severity_expected=3),
    )),
    # Below-severity-3 findings: 5 (LISTS, MUST, NOMINALIZATION, PARAGRAPH, PRONOUNS). The
    # WILLIAMS-SHAPE plant contributes two severity 3 findings, its own and the PLAIN-SENTENCE-
    # LENGTH one the same sentence genuinely earns; neither is bound-limited.
    Recipe(id="clarity-002", shape=SHAPE, plants=(
        Plant("PLAIN-LISTS", Target(section=3, block=1), severity_expected=2),
        Plant("PLAIN-MUST", Target(section=5, block=2), severity_expected=2),
        Plant("PLAIN-NOMINALIZATION", Target(section=6, block=1), severity_expected=2),
        Plant("PLAIN-PARAGRAPH", Target(section=2, block=3), severity_expected=2),
        Plant("PLAIN-PRONOUNS", Target(section=7, block=1), severity_expected=2),
        Plant("WILLIAMS-SHAPE", Target(section=7, block=2), severity_expected=3),
        Plant("WILLIAMS-CHARACTER-ACTION", Target(section=12, block=1), severity_expected=3),
    )),
    # Below-severity-3 findings: 4 (SUBJECT-VERB-OBJECT, TRANSITIONS, PARALLELISM, AUDIENCE). One
    # slot of headroom is deliberate: this is the artifact carrying most of the judged lane, and
    # the judged lane is the one that can legitimately produce a finding no recipe predicted.
    Recipe(id="clarity-003", shape=SHAPE, plants=(
        Plant("PLAIN-SUBJECT-VERB-OBJECT", Target(section=3, block=2), severity_expected=2),
        Plant("PLAIN-TRANSITIONS", Target(section=4, block=2), severity_expected=2),
        Plant("WILLIAMS-PARALLELISM", Target(section=9, block=1), severity_expected=2),
        Plant("PLAIN-AUDIENCE", Target(section=8, block=2), severity_expected=2),
        Plant("PLAIN-CONSISTENT-TERMS", Target(section=8, block=1), severity_expected=3),
        Plant("WILLIAMS-COHESION", Target(section=11, block=1), severity_expected=3),
    )),
    Recipe(id="clarity-004", shape=SHAPE, plants=()),
)

DOMAIN = Domain(
    name="clarity",
    artifact_type="markdown-prose",
    extension=".md",
    namespaces=("PLAIN", "WILLIAMS"),
    compose=compose,
    render=render,
    address=address,
    injectors=INJECTORS,
    recipes=RECIPES,
)
