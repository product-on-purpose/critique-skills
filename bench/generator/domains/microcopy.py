"""Microcopy domain: bench corpus for critique-microcopy.

Artifact type: markdown-prose. Namespace: NNG. Scored corpus (S-05,
critique-microcopy, stretch). Per ADR 0018 (microcopy artifact format),
the artifact grammar is annotated context encoded as markdown-prose, not a
bare string list: one or more screens, each a level-2 heading naming the
screen or state, and under each heading one message block per user-facing
string. A message block is a single markdown paragraph (no blank line
inside it) carrying eight fixed-label lines, one field per physical line,
in this exact order:

    Message: <the exact user-facing string>
    Placement: <free text>
    Container: inline | toast | modal
    Signal: <visual-weight description>, <non-color cue token>
    Fires: <timing token>
    Predictable mistake: yes | no
    Input on resubmission: preserved | cleared | not-applicable
    Suggested fix: none | described, <note> | selectable, <note>

This is the exact grammar skills/critique-microcopy/scripts/checks.py
parses (see its module docstring and _FIELD_LABELS); the two were built to
match, per ADR 0018's implementation-sites note.

Every one of the fourteen criteria in skills/critique-microcopy/references/
NNG-EM.md has its own injector here, per bench/generator/README.md's
checklist ("Write one injector per criterion. Cover every scripted-lane
criterion and at least three judged-lane criteria"): all six scripted
criteria plus all eight judged criteria. Message-text criteria
(CONSTRUCTIVE, NEUTRAL-TONE, PLAIN-LANGUAGE, SPECIFIC, EXPLAIN, GRACE)
replace the Message field wholesale with one of a small set of pre-authored
variants, the same "matched pair, swapped by the injector" pattern
bench/generator/README.md's worked example describes, rather than parsing
prose the injector does not own. Field-only criteria (NOT-COLOR-ONLY,
PRESERVE-INPUT, TIMING, PREVENT, PROXIMITY, SALIENT, SELECTABLE-FIX,
SEVERITY-CONTAINER) mutate exactly one field in place. Where the real
scripted lane's own severity rule is simple and reads another field already
on the block (CONSTRUCTIVE reads Suggested fix, NOT-COLOR-ONLY and
PREVENT read Container, PRESERVE-INPUT reads the section's message count),
each injector below recomputes that same rule from the block's current
field state, so the manifest's severity_expected agrees with what
scripts/checks.py would actually report, even though bench/README.md
records this field as unscored in v0.1.

Every injector works the same way regardless of which topic (see TOPICS
below) occupies its target slot: wholesale replacement injectors do not
read the prior Message text at all, and field-only injectors read only the
one field they need.

Topics are bound to screens, not drawn from one pool. Each Topic declares
the SCREEN_TITLES entry it belongs on, and compose() draws a section's
messages only from that section's own screen pool. Headings stay a
structural, per-recipe declaration in each Recipe's shape["screens"]; what
the binding removes is the possibility of a message about converting a file
appearing under a two-factor-setup heading with a Placement naming an
upload control that screen does not have. Eight of this skill's fourteen
criteria (NNG-EM-PROXIMITY, NNG-EM-SPECIFIC, NNG-EM-SEVERITY-CONTAINER and
the rest of the judged lane) are judgments about a message against its
screen context, so an incoherent pairing does not read as neutral filler to
a reviewer: it reads as a defect, and every one of those reads lands on the
corpus as an unplanted finding counted against precision
(bench/README.md, "A finding that is genuinely correct but was not
planted counts against precision").

The same reasoning constrains every clean Topic below, not just its topic
binding. A Topic is unplanted-defect-free against the judged lane as well
as the scripted one: it names its own cause and its next step, it states
the reason behind any restriction whose reason is not self-evident, it sits
beside the control it concerns, its Container matches how much the problem
blocks, its Signal describes a treatment that stands out, its Suggested fix
is none or selectable but never a described single unambiguous option
(which is NNG-EM-SELECTABLE-FIX's own severity-3 anchor), and a Predictable
mistake of yes never pairs with Fires of on-submit (which is exactly what
NNG-EM-PREVENT flags). The injectors below are what introduce defects; the
vocabulary must not.
"""

from __future__ import annotations

import re

from bench.generator.api import Domain, InjectionResult, Location, Plant, Recipe, Target, injector
from bench.generator.markdown import Block, Document, heading_path, paragraph_index, render_blocks

# --- 1. Vocabulary. Frozen tuples. Order is part of the corpus identity: appending is safe,
#        reordering or removing regenerates every microcopy artifact. -----------------------------

# Field grammar, matching skills/critique-microcopy/scripts/checks.py's
# _FIELD_LABELS exactly, order included.
DOC_TITLE = "Screens Under Review"

FIELD_ORDER = (
    "Message",
    "Placement",
    "Container",
    "Signal",
    "Fires",
    "Predictable mistake",
    "Input on resubmission",
    "Suggested fix",
)

# Screen headings. Twelve entries; each recipe below declares which slice it
# uses via shape["screens"], a domain-defined shape key alongside the
# generic "paragraphs" key every markdown-prose domain declares. Kept as an
# explicit per-recipe structural choice (like toy's and argument's own
# SECTION_TITLES indexing) rather than a random draw, because which screens
# an artifact covers is document structure, not word choice. Every entry
# here carries at least two Topics below, which is the largest per-section
# message count any recipe asks for.
SCREEN_TITLES = (
    "Signup form, email field",
    "Checkout form, payment method",
    "Profile settings, phone number",
    "Checkout form, shipping address",
    "File upload, receipts",
    "Password reset, new password",
    "Account settings, username",
    "Search results, no matches",
    "Notification center, sync status",
    "Two-factor setup, verification code",
    "Billing, promo code",
    "Signup form, confirm password",
)


class Topic:
    """One clean message, bound to the screen it belongs on. Frozen by
    construction: never mutated after the module loads.

    Every field is written so that, unmodified, the block passes all six
    scripted checks in skills/critique-microcopy/scripts/checks.py (an
    instruction marker somewhere in Message, no blame phrase, no jargon or
    code token, a non-none Signal cue, Input on resubmission never cleared,
    Fires never mid-keystroke or on-load-before-input) and gives the judged
    lane nothing to report either, per the module docstring's list. Two
    invariants there are easy to break and worth restating: Suggested fix is
    never described, and predictable_mistake of yes never pairs with fires
    of on-submit.

    Injectors never read a Topic directly; they read the rendered field text
    off the composition, so a Topic's only job is to seed that text cleanly.
    """

    __slots__ = (
        "screen", "message", "placement", "container", "signal", "fires",
        "predictable_mistake", "input_resub", "suggested_fix",
    )

    def __init__(self, screen, message, placement, container, signal, fires,
                 predictable_mistake, input_resub, suggested_fix):
        self.screen = screen
        self.message = message
        self.placement = placement
        self.container = container
        self.signal = signal
        self.fires = fires
        self.predictable_mistake = predictable_mistake
        self.input_resub = input_resub
        self.suggested_fix = suggested_fix


TOPICS = (
    # --- Signup form, email field ---
    Topic(
        screen="Signup form, email field",
        message="Enter an email address that includes an at sign and a domain, for example "
                "name@example.com, so the confirmation link has somewhere to go.",
        placement="directly below the email input field",
        container="inline",
        signal="one step bolder and larger than the field label, icon",
        fires="on-blur",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="none",
    ),
    Topic(
        screen="Signup form, email field",
        message="This address is already registered. Sign in instead, or enter a different "
                "address.",
        placement="directly below the email input field",
        container="inline",
        signal="one step bolder and larger than the field label, icon",
        fires="on-blur",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="selectable, offers a sign-in link in place of the message",
    ),
    # --- Checkout form, payment method ---
    Topic(
        screen="Checkout form, payment method",
        message="The card issuer declined this charge. Choose a different payment method, or "
                "contact your bank about this card.",
        placement="in a banner directly above the payment method selector, staying on screen "
                  "until another method is chosen",
        container="inline",
        signal="bold text set larger than the surrounding form labels, icon",
        fires="on-submit",
        predictable_mistake="no",
        input_resub="preserved",
        suggested_fix="none",
    ),
    Topic(
        screen="Checkout form, payment method",
        message="The expiry date on this card has passed. Update the expiry date, or choose a "
                "different card.",
        placement="directly below the card expiry date field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="after-field-complete",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="none",
    ),
    # --- Profile settings, phone number ---
    Topic(
        screen="Profile settings, phone number",
        message="Enter this phone number as 10 digits with no dashes or spaces, the only shape "
                "the carrier accepts for verification texts.",
        placement="directly below the phone number field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="on-blur",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="none",
    ),
    Topic(
        screen="Profile settings, phone number",
        message="This phone number is already on another account. Remove it there first, or "
                "contact support to move it across.",
        placement="directly below the phone number field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="on-blur",
        predictable_mistake="no",
        input_resub="preserved",
        suggested_fix="none",
    ),
    # --- Checkout form, shipping address ---
    Topic(
        screen="Checkout form, shipping address",
        message="Complete the city and postal code fields; the carrier needs both before it can "
                "quote a delivery date.",
        placement="directly below the shipping address block",
        container="inline",
        signal="bold text set above the address block at a larger size than its labels, icon",
        fires="on-blur",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="none",
    ),
    Topic(
        screen="Checkout form, shipping address",
        message="This postal code does not belong to the selected country. Correct the postal "
                "code, or select the country it belongs to.",
        placement="directly below the postal code field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="after-field-complete",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="none",
    ),
    # --- File upload, receipts ---
    Topic(
        screen="File upload, receipts",
        message="This receipt is over the 10 MB limit, which keeps uploads quick on slow "
                "connections. Reduce the file size and upload it again.",
        placement="directly below the upload control",
        container="inline",
        signal="bold text below the upload control at a larger size than its caption, icon",
        fires="after-field-complete",
        predictable_mistake="yes",
        input_resub="not-applicable",
        suggested_fix="none",
    ),
    Topic(
        screen="File upload, receipts",
        message="Receipts upload as PDF or PNG only, the two formats the expense system can "
                "read. Change this file to one of those formats and upload it again, or select a "
                "different receipt.",
        placement="directly below the upload control",
        container="inline",
        signal="bold text below the upload control at a larger size than its caption, icon",
        fires="after-field-complete",
        predictable_mistake="yes",
        input_resub="not-applicable",
        suggested_fix="selectable, offers a convert and retry action in place of the message",
    ),
    # --- Password reset, new password ---
    Topic(
        screen="Password reset, new password",
        message="Choose a password of at least 8 characters, long enough that a guessing attack "
                "cannot work through every combination.",
        placement="directly below the new password field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="after-field-complete",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="none",
    ),
    Topic(
        screen="Password reset, new password",
        message="This reset link expired an hour after it was sent, so nobody can reuse it from "
                "an old message. Request a new link and check the inbox again.",
        placement="in a dialog centered on the password reset step, over the new password field "
                  "it blocks",
        container="modal",
        signal="bold heading text at the top of the dialog, icon",
        fires="on-focus",
        predictable_mistake="no",
        input_resub="not-applicable",
        suggested_fix="selectable, offers a send a new link button in place of the message",
    ),
    # --- Account settings, username ---
    Topic(
        screen="Account settings, username",
        message="This username is taken. Choose another one; jordan-riley99 is free right now.",
        placement="directly below the username field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="on-blur",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="selectable, offers the available username as a one-click choice",
    ),
    Topic(
        screen="Account settings, username",
        message="Usernames take letters, numbers, and hyphens only, because the username becomes "
                "part of a profile web address. Remove the other characters and save again.",
        placement="directly below the username field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="on-blur",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="none",
    ),
    # --- Search results, no matches ---
    Topic(
        screen="Search results, no matches",
        message="No orders match the words tripod mount. Check the spelling, or remove one of "
                "the filters to widen the search.",
        placement="in the results panel, in place of the results list",
        container="inline",
        signal="bold heading text where the first result would sit, text-label",
        fires="on-submit",
        predictable_mistake="no",
        input_resub="not-applicable",
        suggested_fix="none",
    ),
    Topic(
        screen="Search results, no matches",
        message="No orders fall inside the selected date range. Change the date range, or clear "
                "the filters to see every order.",
        placement="in the results panel, directly under the filter bar it concerns",
        container="inline",
        signal="bold heading text where the first result would sit, text-label",
        fires="on-submit",
        predictable_mistake="no",
        input_resub="not-applicable",
        suggested_fix="selectable, offers a clear filters button beside the message",
    ),
    # --- Notification center, sync status ---
    Topic(
        screen="Notification center, sync status",
        message="The last three changes are saved on this device but not synced yet. Reconnect "
                "to the network and they will upload on their own.",
        placement="in a status toast at the bottom right, beside the sync indicator it reports on",
        container="toast",
        signal="one step bolder than the surrounding status text, with a status label reading "
               "Not synced, text-label",
        fires="on-focus",
        predictable_mistake="no",
        input_resub="not-applicable",
        suggested_fix="none",
    ),
    Topic(
        screen="Notification center, sync status",
        message="Sync is paused while this device is on a metered connection, so syncing does "
                "not spend a data allowance. Select resume to sync now.",
        placement="in the notification list, directly under the sync status row",
        container="inline",
        signal="bold text at the top of the notification list, icon",
        fires="on-focus",
        predictable_mistake="no",
        input_resub="not-applicable",
        suggested_fix="selectable, offers a resume now action inside the notification",
    ),
    # --- Two-factor setup, verification code ---
    Topic(
        screen="Two-factor setup, verification code",
        message="This verification code expired 10 minutes after it was sent, which stops an "
                "intercepted code from being reused later. Request a new code and enter it here.",
        placement="directly below the verification code field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="on-submit",
        predictable_mistake="no",
        input_resub="preserved",
        suggested_fix="selectable, offers a resend code button in place of the message",
    ),
    Topic(
        screen="Two-factor setup, verification code",
        message="Verification codes are 6 digits long, and this one has 5. Check the message "
                "again and enter all six.",
        placement="directly below the verification code field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="on-blur",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="none",
    ),
    # --- Billing, promo code ---
    Topic(
        screen="Billing, promo code",
        message="This promo code ended on 30 June. Enter a current code, or continue without one.",
        placement="directly below the promo code field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="on-blur",
        predictable_mistake="no",
        input_resub="preserved",
        suggested_fix="none",
    ),
    Topic(
        screen="Billing, promo code",
        message="This promo code applies to annual plans, and the selected plan is monthly. "
                "Change the plan to annual, or remove the code.",
        placement="directly below the promo code field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="on-blur",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="none",
    ),
    # --- Signup form, confirm password ---
    Topic(
        screen="Signup form, confirm password",
        message="The two password fields do not match. Re-enter the password in this field to "
                "confirm it.",
        placement="directly below the confirm password field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="on-blur",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="none",
    ),
    Topic(
        screen="Signup form, confirm password",
        message="Confirm the password here, so a typo in the first field does not leave the "
                "account locked out later.",
        placement="directly below the confirm password field",
        container="inline",
        signal="bold text set larger than the field label, icon",
        fires="on-blur",
        predictable_mistake="yes",
        input_resub="preserved",
        suggested_fix="none",
    ),
)

# Topics grouped by the screen they belong on, built once at import. compose()
# draws a section's messages from its own screen's pool only, never from
# TOPICS as a whole; see the module docstring for why an incoherent
# message-to-screen pairing is a seeded defect rather than neutral filler.
TOPICS_BY_SCREEN = {
    title: tuple(topic for topic in TOPICS if topic.screen == title)
    for title in SCREEN_TITLES
}

_screens_without_topics = sorted(
    title for title, pool in TOPICS_BY_SCREEN.items() if len(pool) < 2
)
if _screens_without_topics:  # pragma: no cover - a module-authoring error, caught at import
    raise ValueError(
        "every SCREEN_TITLES entry needs at least two Topics (the largest per-section "
        f"message count any recipe asks for); short: {_screens_without_topics}"
    )
_orphan_topics = sorted({topic.screen for topic in TOPICS} - set(SCREEN_TITLES))
if _orphan_topics:  # pragma: no cover - a module-authoring error, caught at import
    raise ValueError(f"Topic.screen values not in SCREEN_TITLES: {_orphan_topics}")

# Message-text injector variants. Each is a wholesale replacement of the
# Message field, independent of whatever topic occupied the slot before,
# the same pattern bench/generator/domains/argument.py uses for its own
# judged injectors (see that module's *_VARIANTS tuples). Every variant
# below carries at least one instruction marker from
# skills/critique-microcopy/scripts/checks.py's own INSTRUCTION_MARKERS
# list (enter, choose, check, contact, correct, re-enter), so planting one
# of these six criteria never also creates an unplanted, genuine
# NNG-EM-CONSTRUCTIVE violation at the same location.

# Each variant names its own cause and offers no next step, so it breaches
# NNG-EM-CONSTRUCTIVE and nothing else. A bare something-went-wrong wording
# would breach NNG-EM-SPECIFIC at the same location, and a stated rule with
# no reason would breach NNG-EM-EXPLAIN; both would be genuine unplanted
# findings counted against precision.
CONSTRUCTIVE_VARIANTS = (
    "The connection dropped before this finished.",
    "This request timed out before it could finish.",
)

# (text, severity_expected). Severity mirrors checks.py's own rule: a
# blame phrase paired with a repetition marker (keep, again, repeatedly,
# every time, once more, still) is severity 3, otherwise severity 2.
NEUTRAL_TONE_VARIANTS = (
    ("You did not enter a valid value here. Re-enter it to continue.", 2),
    ("You keep entering the wrong value. Re-enter it to continue.", 3),
)

# (text, severity_expected). Severity mirrors checks.py's own rule: three
# or fewer words remaining once the jargon or code span is removed is
# severity 3, more than three is severity 2.
PLAIN_LANGUAGE_VARIANTS = (
    ("Contact support: internal server error.", 3),
    ("Please correct the highlighted field. Error code: 502.", 2),
)

SPECIFIC_VARIANTS = (
    ("Something went wrong. Contact support if this continues.", 3),
    (
        "One of the required fields on this form is missing. Check the fields marked with an "
        "asterisk.",
        2,
    ),
)

# Screen-agnostic on purpose, like every other message-text variant here: an
# injector replaces the Message wholesale wherever a recipe points it, so a
# variant naming a control that the target screen does not have would plant
# an incoherence (and with it an unplanted NNG-EM-SPECIFIC or
# NNG-EM-PROXIMITY finding) on top of the criterion actually being seeded.
EXPLAIN_VARIANTS = (
    ("This field takes a maximum of 30 characters. Shorten the entry and save again.", 2),
    ("This account is locked. Contact support to continue.", 3),
)

GRACE_VARIANTS = (
    ("This service is unavailable right now. Contact support for updates.", 2),
    (
        "The last changes were not saved and cannot be recovered. Contact support for "
        "assistance.",
        3,
    ),
)

# Field-only injector variants.
PROXIMITY_VARIANTS = (
    (
        "at the top of a long form, requiring the reader to scroll up to see it, though the "
        "field itself stays visible on the page",
        2,
    ),
    (
        "on a separate error-summary screen reached only by leaving the form, so the field "
        "itself is no longer visible",
        3,
    ),
)

SALIENT_VARIANTS = (
    (
        "same weight as the surrounding label text, with only a subtle color change setting it "
        "apart",
        2,
    ),
    (
        "styled identically to informational banners elsewhere on the page, with no visual cue "
        "that this one demands action",
        3,
    ),
)

SELECTABLE_FIX_VARIANTS = (
    ("names the one available alternative but requires the reader to enter it by hand", 2),
    (
        "names the one action that would resolve this but requires the reader to carry it out "
        "elsewhere and start the step again",
        3,
    ),
)

TIMING_TOKENS = ("mid-keystroke", "on-load-before-input")

# checks.py's own ERROR_TONE_MARKERS, mirrored here so NNG-EM-TIMING's
# severity matches what the real scripted lane would compute.
ERROR_TONE_MARKERS = (
    "invalid", "incorrect", "not valid", "must be", "is required", "wrong",
    "please enter a valid", "failed", "error",
)

INJECTORS = {}

# --- 2 and 3. Composition. Structure comes from the recipe shape; the stream picks words only. --


def _topic_fields(topic):
    return {
        "Message": topic.message,
        "Placement": topic.placement,
        "Container": topic.container,
        "Signal": topic.signal,
        "Fires": topic.fires,
        "Predictable mistake": topic.predictable_mistake,
        "Input on resubmission": topic.input_resub,
        "Suggested fix": topic.suggested_fix,
    }


def _render_fields(fields):
    return "\n".join(f"{label}: {fields[label]}" for label in FIELD_ORDER)


def _parse_fields(text):
    fields = {}
    for line in text.split("\n"):
        label, _, value = line.partition(": ")
        fields[label] = value
    return fields


def _slot(target):
    return f"s{target.section}.p{target.block}"


def compose(rng, shape):
    counts = shape["paragraphs"]  # per-section message counts, e.g. (2, 2, 2)
    screens = shape["screens"]  # per-section heading titles, same length as counts
    # A level-1 title, never a plant target, wraps the screens so every screen heading nests
    # correctly under it. This is a corpus-module addition beyond the bare "## screen heading"
    # shape ADR 0018's own worked examples render: without a level-1 ancestor,
    # bench/generator/markdown.py's heading_path() (and blockparse.py's independent copy of the
    # same formula) truncates a sibling level-2 heading's path at index 1, which never reaches
    # index 0, so consecutive screens accumulate into one growing path instead of each screen
    # replacing the last. checks.py's own parser is heading-level-agnostic (_HEADING_RE matches
    # any of 1 to 6 hashes and only ever tracks "the most recent heading"), so this title changes
    # nothing about how the artifact parses under SKILL.md's protocol; it exists purely to give
    # the shared harness's path-truncation math a level-1 floor to truncate against.
    blocks = [Block(kind="heading", level=1, text=f"# {DOC_TITLE}", slot="h0")]
    for section, count in enumerate(counts, start=1):
        screen = screens[section - 1]
        blocks.append(
            Block(kind="heading", level=2, text=f"## {screen}", slot=f"s{section}.h")
        )
        # Sampled from this screen's own pool, without replacement, so a section never repeats a
        # message and no message lands under a heading it does not belong to. Keyed on the screen
        # title rather than the section ordinal so the same screen composes the same way wherever a
        # recipe places it, and so adding a recipe never reshuffles an existing one. A recipe
        # asking a screen for more messages than that screen has Topics is an authoring error the
        # module-level check above catches at import for the counts recipes actually use.
        topics = rng.child("topics", screen).sample(TOPICS_BY_SCREEN[screen], count)
        for p, topic in enumerate(topics, start=1):
            text = _render_fields(_topic_fields(topic))
            blocks.append(Block(kind="paragraph", level=0, text=text, slot=f"s{section}.p{p}"))
    return Document(tuple(blocks))


def render(doc):
    return render_blocks(doc.blocks)  # blocks joined by one blank line

# --- 4. Injectors, keyed by criterion ID. Each returns a new composition, never mutates. --------


def _contains_phrase(text, phrase):
    return re.search(rf"\b{re.escape(phrase)}\b", text, re.IGNORECASE) is not None


def _contains_any(text, phrases):
    return any(_contains_phrase(text, phrase) for phrase in phrases)


def _suggested_fix_token(fields):
    return fields.get("Suggested fix", "").split(",")[0].strip().lower()


def _section_message_count(doc, section):
    prefix = f"s{section}.p"
    return sum(1 for b in doc.blocks if b.kind == "paragraph" and b.slot.startswith(prefix))


@injector("NNG-EM-CONSTRUCTIVE")
def inject_constructive(rng, doc, target):
    """Replace the Message field with a statement that names the problem and offers no next step.
    Severity mirrors checks.py's own rule: severity 2 when the Suggested fix field already offers a
    described or selectable fix, severity 3 otherwise, read off the block's current Suggested fix
    token rather than assumed. Where that token is not none, the field's note is rewritten to a
    neutral wording as well: the note the Topic supplied describes a fix for the message this
    injector just replaced, and leaving it would leave the block describing a next step that has
    nothing to do with what the message now says."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    fields["Message"] = rng.choice(CONSTRUCTIVE_VARIANTS)
    token = _suggested_fix_token(fields)
    if token == "selectable":
        fields["Suggested fix"] = "selectable, offers the one available next step as a direct action"
    elif token == "described":
        fields["Suggested fix"] = "described, states the next step in prose beside the message"
    severity = 2 if token in ("described", "selectable") else 3
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Message text was replaced with a statement that names the problem and offers no "
            "imperative instruction or named next step anywhere in it."
        ),
    )


@injector("NNG-EM-NEUTRAL-TONE")
def inject_neutral_tone(rng, doc, target):
    """Replace the Message field with a variant carrying a second-person accusatory
    construction. Severity is 3 for the variant that also pairs the accusation with a repetition
    marker, matching checks.py's own weighing of a routine mistake framed as a recurring
    personal failing; otherwise 2."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    text, severity = rng.choice(NEUTRAL_TONE_VARIANTS)
    fields["Message"] = text
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Message text was replaced with a variant carrying a second-person accusatory "
            "construction that frames the problem as something the reader personally did wrong."
        ),
    )


@injector("NNG-EM-PLAIN-LANGUAGE")
def inject_plain_language(rng, doc, target):
    """Replace the Message field with a variant carrying an internal error code or an
    engineering-jargon term standing in for a plain-language explanation. Severity mirrors
    checks.py's own word-count rule for what remains once the jargon span is removed."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    text, severity = rng.choice(PLAIN_LANGUAGE_VARIANTS)
    fields["Message"] = text
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Message text was replaced with a variant carrying an internal error code or an "
            "engineering-jargon term standing in for a plain-language explanation."
        ),
    )


@injector("NNG-EM-NOT-COLOR-ONLY")
def inject_not_color_only(rng, doc, target):
    """Replace the Signal field's non-color cue token with none, leaving the visual-weight
    description untouched. Severity is 3 when the message's own Container is a self-clearing
    toast, matching checks.py's own rule that a colorblind reader has the least chance of
    noticing a toast that already clears itself, 2 otherwise."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    desc, _sep, _token = fields["Signal"].rpartition(", ")
    fields["Signal"] = f"{desc}, none" if desc else "none"
    severity = 3 if fields.get("Container", "").strip().lower() == "toast" else 2
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Signal field's non-color cue token was replaced with none, so color or "
            "highlight is the only stated cue for this message."
        ),
    )


@injector("NNG-EM-PRESERVE-INPUT")
def inject_preserve_input(rng, doc, target):
    """Replace the Input on resubmission field's token with cleared. Severity is 3 when three or
    more messages share the same screen, matching checks.py's own rule that clearing a longer
    form costs the reader more to redo."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    fields["Input on resubmission"] = "cleared"
    severity = 3 if _section_message_count(doc, target.section) >= 3 else 2
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Input on resubmission field's token was replaced with cleared, so a failed "
            "submission drops what the reader already entered instead of keeping it in place."
        ),
    )


@injector("NNG-EM-TIMING")
def inject_timing(rng, doc, target):
    """Replace the Fires field's token with one of the two disallowed timing tokens. Severity is
    3 when the Message text already carries an error-toned marker, matching checks.py's own rule
    that an alarming message arriving too early costs the reader more than an informational one."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    fields["Fires"] = rng.choice(TIMING_TOKENS)
    severity = 3 if _contains_any(fields.get("Message", ""), ERROR_TONE_MARKERS) else 2
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Fires field's token was replaced with one from the disallowed timing set, so "
            "the message can appear before the reader has had a fair chance to finish the "
            "relevant input."
        ),
    )


@injector("NNG-EM-SPECIFIC")
def inject_specific(rng, doc, target):
    """Replace the Message field with a generic statement naming no field, value, or rule, even
    where the screen context shows a specific, nameable cause was available."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    text, severity = rng.choice(SPECIFIC_VARIANTS)
    fields["Message"] = text
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Message text was replaced with a generic statement naming no field, value, or "
            "rule, even though the screen context shows a specific, nameable cause was available."
        ),
    )


@injector("NNG-EM-EXPLAIN")
def inject_explain(rng, doc, target):
    """Replace the Message field with a bare statement of the restriction, with no reason
    attached for why it applies."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    text, severity = rng.choice(EXPLAIN_VARIANTS)
    fields["Message"] = text
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Message text was replaced with a bare statement of the restriction, with no "
            "reason attached for why it applies."
        ),
    )


@injector("NNG-EM-GRACE")
def inject_grace(rng, doc, target):
    """Replace the Message field with a bare technical notice carrying no acknowledgment of the
    reader's situation, and set Suggested fix to none. NNG-EM-GRACE only applies where the failure
    is total and unrecoverable in the moment, which NNG-EM.md's operational test reads off three
    signals together: Suggested fix is none, no sibling block under the same heading offers a way
    forward, and the message reports a completed loss or an outage. The recipes place this plant on
    a single-block section, and this injector supplies the first signal rather than depending on
    whichever Topic occupied the slot."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    text, severity = rng.choice(GRACE_VARIANTS)
    fields["Message"] = text
    fields["Suggested fix"] = "none"
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Message text was replaced with a bare technical notice carrying no "
            "acknowledgment of the reader's situation, and the Suggested fix field was set to "
            "none, for a scenario where the failure is total and unrecoverable in the moment."
        ),
    )


@injector("NNG-EM-PREVENT")
def inject_prevent(rng, doc, target):
    """Set the Predictable mistake field to yes and move the Fires field to on-submit, removing
    any warning offered before the point of commitment. Severity is 3 when the message's own
    Container is a modal, standing in for a longer, multi-step flow where the missed warning
    costs the reader more."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    fields["Predictable mistake"] = "yes"
    fields["Fires"] = "on-submit"
    severity = 3 if fields.get("Container", "").strip().lower() == "modal" else 2
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Predictable mistake field was set to yes and the Fires field was moved to "
            "on-submit, removing any warning offered before the point of commitment."
        ),
    )


@injector("NNG-EM-PROXIMITY")
def inject_proximity(rng, doc, target):
    """Replace the Placement field with a variant describing a location away from the control
    the message concerns, requiring the reader to search or navigate to find it."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    text, severity = rng.choice(PROXIMITY_VARIANTS)
    fields["Placement"] = text
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Placement field's text was replaced with a variant describing a location away "
            "from the control the message concerns, requiring the reader to search or navigate "
            "to find it."
        ),
    )


@injector("NNG-EM-SALIENT")
def inject_salient(rng, doc, target):
    """Replace the Signal field's visual-weight description with a variant describing the
    message as indistinguishable from surrounding page content, leaving the non-color cue token
    itself untouched so this plant never also breaches NNG-EM-NOT-COLOR-ONLY."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    _old_desc, _sep, token = fields["Signal"].rpartition(", ")
    new_desc, severity = rng.choice(SALIENT_VARIANTS)
    fields["Signal"] = f"{new_desc}, {token}" if token else new_desc
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Signal field's visual-weight description was replaced with a variant "
            "describing the message as indistinguishable from surrounding page content."
        ),
    )


@injector("NNG-EM-SELECTABLE-FIX")
def inject_selectable_fix(rng, doc, target):
    """Replace the Suggested fix field's token with described, naming a single unambiguous
    option in prose rather than offering it as something the reader can select directly."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    note, severity = rng.choice(SELECTABLE_FIX_VARIANTS)
    fields["Suggested fix"] = f"described, {note}"
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Suggested fix field's token was replaced with described, naming a single "
            "unambiguous option in prose rather than offering it as something the reader can "
            "select directly."
        ),
    )


@injector("NNG-EM-SEVERITY-CONTAINER")
def inject_severity_container(rng, doc, target):
    """Swap the Container field between a self-clearing and a flow-halting presentation: a modal
    becomes a toast (severity 3, a fully blocking failure now clears itself), anything else
    becomes a modal (severity 2, a minor issue now halts the flow)."""
    slot = _slot(target)
    fields = _parse_fields(doc.block(slot).text)
    current = fields.get("Container", "").strip().lower()
    if current == "modal":
        fields["Container"] = "toast"
        severity = 3
    else:
        fields["Container"] = "modal"
        severity = 2
    return InjectionResult(
        composed=doc.replace(slot, _render_fields(fields)),
        slot=slot,
        severity_expected=severity,
        description=(
            "The Container field's token was swapped between a self-clearing and a "
            "flow-halting presentation, so it no longer matches how much the underlying problem "
            "actually blocks the reader from continuing."
        ),
    )

# --- 5. Addressing. Called by the harness after every injection, on the final composition. ------


def _within_section_index(doc, slot):
    """1-based ordinal of the message at `slot` among message blocks in its own immediate
    (level-2) section, counted in document order from the final composition. Never read off the
    slot's own `.p{n}` suffix, per bench/generator/README.md's "slots are identities" rule.
    Matches skills/critique-microcopy/scripts/checks.py's own per-section message numbering
    (_parse_messages's section_counter), so the manifest's location text and a real finding's
    location text use the same words for the same message."""
    count = 0
    for block in doc.blocks:
        if block.kind == "heading":
            count = 0
            continue
        if block.slot == slot:
            return count + 1
        if block.kind == "paragraph":
            count += 1
    raise KeyError(f"slot not found: {slot!r}")


def address(doc, slot, sentence=None):
    path = heading_path(doc, slot)
    index = paragraph_index(doc, slot)
    within = _within_section_index(doc, slot)
    heading_title = path[-1] if path else None
    text = f"{heading_title}, message {within}" if heading_title else f"message {within}"
    return Location(kind="paragraph", paragraph=index, heading_path=path, text=text)

# --- 6. Recipes. Four artifacts, one of them clean. All fourteen criteria are planted across ----
#        the three seeded recipes; no recipe repeats a criterion within one section. -------------
#
# A Plant's own severity_expected is the recipe's declaration of what it believes it is planting.
# The value that actually reaches the manifest is the one the injector returns on the composition
# it sees, which is the honest number and the one bench/README.md records as unscored in v0.1. The
# two are kept equal here by hand: nothing in the harness reconciles them, so a declaration that
# drifts from what its injector computes is a silent lie to the next reader of this file, not a
# build failure. Re-check them after any change to a variant tuple, a Topic, or a target.

RECIPES = (
    Recipe(
        id="microcopy-001",
        shape={"paragraphs": (2, 2, 2), "screens": SCREEN_TITLES[0:3]},
        plants=(
            Plant("NNG-EM-CONSTRUCTIVE", Target(section=1, block=1), severity_expected=2),
            Plant("NNG-EM-NOT-COLOR-ONLY", Target(section=1, block=2), severity_expected=2),
            Plant("NNG-EM-SPECIFIC", Target(section=2, block=1), severity_expected=3),
            Plant("NNG-EM-TIMING", Target(section=2, block=2), severity_expected=2),
            Plant("NNG-EM-NEUTRAL-TONE", Target(section=3, block=1), severity_expected=3),
            Plant("NNG-EM-PRESERVE-INPUT", Target(section=3, block=2), severity_expected=2),
        ),
    ),
    Recipe(
        id="microcopy-002",
        shape={"paragraphs": (2, 2, 2, 1), "screens": SCREEN_TITLES[3:7]},
        plants=(
            Plant("NNG-EM-EXPLAIN", Target(section=1, block=1), severity_expected=2),
            Plant("NNG-EM-PLAIN-LANGUAGE", Target(section=1, block=2), severity_expected=2),
            Plant("NNG-EM-SELECTABLE-FIX", Target(section=2, block=1), severity_expected=2),
            Plant("NNG-EM-PREVENT", Target(section=2, block=2), severity_expected=2),
            Plant("NNG-EM-PROXIMITY", Target(section=3, block=1), severity_expected=2),
            # Section 3's second block is the one modal in the composed vocabulary, so this is
            # where NNG-EM-SEVERITY-CONTAINER's severity-3 direction (a blocking failure demoted
            # to a self-clearing toast) is reachable at all.
            Plant("NNG-EM-SEVERITY-CONTAINER", Target(section=3, block=2), severity_expected=3),
            Plant("NNG-EM-GRACE", Target(section=4, block=1), severity_expected=3),
        ),
    ),
    Recipe(
        id="microcopy-003",
        shape={"paragraphs": (2, 1), "screens": SCREEN_TITLES[7:9]},
        plants=(
            # Block 1 is the block whose Suggested fix is none, which is what makes
            # NNG-EM-CONSTRUCTIVE's severity-3 direction (nothing on the screen offers a next
            # step) reachable here.
            Plant("NNG-EM-CONSTRUCTIVE", Target(section=1, block=1), severity_expected=3),
            Plant("NNG-EM-SALIENT", Target(section=1, block=2), severity_expected=3),
        ),
    ),
    Recipe(
        id="microcopy-004",
        shape={"paragraphs": (2, 2), "screens": SCREEN_TITLES[9:11]},
        plants=(),
    ),
)

DOMAIN = Domain(
    name="microcopy",
    artifact_type="markdown-prose",
    extension=".md",
    namespaces=("NNG",),
    compose=compose,
    render=render,
    address=address,
    injectors=INJECTORS,
    recipes=RECIPES,
)
