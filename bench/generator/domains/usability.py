"""Usability domain: bench corpus for critique-usability.

Artifact type: html. Namespace: NNG. Scored corpus (S-05, critique-usability,
core; bench/README.md's corpus design table: usability, 4 artifacts, 1
clean). Subject matter is an invented project-workspace console: a
fictional SaaS product-management tool, matching bench/README.md's own
"a fictional SaaS console" example of invented content with no reproduced
rubric text and no real product names.

Every one of the three scripted-lane criteria has its own injector here,
per bench/generator/README.md's checklist ("Cover every scripted-lane
criterion and at least three judged-lane criteria"), plus four judged
criteria: NNG-H3-DEADEND, NNG-H4-CONTROL-NAMING, and NNG-H6-LABELED
(scripted, ADR 0021) alongside NNG-H5-CONFIRM, NNG-H9-IDENTIFY,
NNG-H3-UNDO, and NNG-H8 (judged). The corpus plants all seven across three
seeded recipes, plus one clean recipe.

Page shape (eight states, one `<section id=...>` each, matching the HTML
conventions skills/critique-usability/scripts/checks.py itself reads:
a state is a named `<section>`, an edge is an `<a href="#target-id">`
inside it whose target names another defined state):

    1. workspace-overview    NNG-H8
    2. project-settings      NNG-H6-LABELED, NNG-H5-CONFIRM
    3. invite-member         filler flow step, no criterion targets it
    4. invite-sent           NNG-H3-DEADEND
    5. archive-confirm       NNG-H3-UNDO
    6. project-archived      filler result state, no criterion targets it
    7. import-status         NNG-H9-IDENTIFY
    8. notification-settings NNG-H4-CONTROL-NAMING

One statement of reversibility, and only one, appears in the clean
composition: the closing sentence of `archive-confirm`'s copy, which says
the project can be restored from the archived projects list. The
`project-archived` result state deliberately does not repeat it. That is
what makes NNG-H3-UNDO's injector produce a real defect rather than a
cosmetic edit: removing that one sentence leaves the artifact with no
reversal path named anywhere, which is exactly what the criterion's
operational test asks about. A second copy of the same statement in the
result state would have made the planted defect unfindable by a critic
reading the whole artifact, and the manifest's own description of it
false.

Every commit control (the `<button type="submit">` in each of the three
forms) reads "Save" in the clean composition, exactly like every other
control label in the artifact: NNG-H4-CONTROL-NAMING's injector is what
introduces the second distinct commit synonym, matching the toy and
argument domains' own pattern of composing clean-by-default and letting
the injector introduce the breach. Every state the clean composition
defines carries at least one outgoing `<a href="#...">` to another
defined state, so a clean recipe (`usability-004`) is a genuine zero-
finding artifact for the scripted lane, not merely one nothing was
checked against.

Every control and section this module composes carries a content-derived
`id` attribute unconditionally, in the clean recipe and every seeded one
alike, per bench/README.md's HTML invariant ("Every element of an
injectable class carries a content-derived id ... so the presence of an
id never signals a plant"): ids are written as ordinary composed content
in `compose`, before any injector runs. No injector here adds an id to,
or removes one from, an element the composition already produced. The one
element that does not exist before injection is NNG-H8's promotional
banner, which the injector inserts; it is given a content-derived id in
the same `<section-id>-<suffix>` form every composed element uses, so it
is indistinguishable by id shape from ordinary content and the invariant
still holds.
"""

from __future__ import annotations

from bench.generator.api import Domain, InjectionResult, Location, Plant, Recipe, Target, injector
from bench.generator.html import HtmlDocument, el, render
from bench.generator.text import split_sentences

# --- 1. Vocabulary. Frozen tuples. Order is part of the corpus identity: appending is safe,
#        reordering or removing regenerates every usability artifact. -----------------------------

PAGE_TITLE = "Project workspace mockup"
PAGE_HEADING = "Project workspace"

# Section 2, 5, 6's shared subject: the one project every settings and
# archive control in the artifact acts on.
PROJECT_NAMES = ("Q3 Roadmap", "Customer Migration", "Design System Refresh", "Vendor Onboarding")

# Section 1: filler background list, no criterion targets it. Combinatorial
# in the same shape as the toy and argument domains' own filler content, so
# a false positive has somewhere neutral to land.
RECENT_PROJECT_POOL = (
    "Beta Launch Plan",
    "Holiday Campaign Assets",
    "Support Backlog Triage",
    "Mobile App Revamp",
    "Data Warehouse Cutover",
    "Partner Integration Pilot",
)
LAST_SYNCED_PHRASES = ("synced 2 days ago", "synced this morning", "synced last week", "synced 5 hours ago")

# Section 4: filler expiry wording for the invite-sent result state.
INVITE_EXPIRY_DAYS = (5, 7, 10)

# Section 8: filler digest-frequency options for the notifications form.
DIGEST_OPTION_SETS = (("Daily", "Weekly"), ("Daily", "Weekly", "Monthly"))

# Section 7: the clean, specific import-status message names which rows
# were skipped and why. IMPORT_ROW_NUMBER_POOL is sampled from, not
# iterated as a whole, so the row numbers named differ artifact to
# artifact without the surrounding sentence changing shape.
IMPORT_SKIPPED_ROW_COUNTS = (2, 3, 4)
IMPORT_ROW_NUMBER_POOL = tuple(range(2, 100))

# NNG-H9-IDENTIFY's injected replacement: a generic notice with a raw code,
# naming neither which rows failed nor why, matching the severity-3 anchor
# in references/NNG-HEURISTICS.md ("a generic message and a numeric code").
GENERIC_IMPORT_ERROR_VARIANTS = (
    "Import failed. Error code IMP-500. Contact support if this continues.",
    "Something went wrong during the import. Error code IMP-7712. Try again later.",
)

# NNG-H4-CONTROL-NAMING's injected replacement: any commit synonym other
# than "Save", the label every commit control carries by default. Members
# of scripts/checks.py's own COMMIT_SYNONYMS tuple.
CONTROL_NAMING_ALT_LABELS = ("Apply changes", "Submit", "Confirm")

# NNG-H8's injected insertion: a promotional element competing with the
# screen's primary control, matching the severity-2 anchor in
# references/NNG-HEURISTICS.md ("a promotional banner above the fold that
# pushes the first setting below it").
PROMO_BANNER_VARIANTS = (
    ("promo-upgrade", "Upgrade to Team Pro for unlimited projects and priority support."),
    ("promo-referral", "Invite 3 teammates this month to unlock the advanced reporting add-on."),
)

SECTION_IDS = (
    "workspace-overview",
    "project-settings",
    "invite-member",
    "invite-sent",
    "archive-confirm",
    "project-archived",
    "import-status",
    "notification-settings",
)
SECTION_TITLES = (
    "Your projects",
    "Project settings",
    "Invite a team member",
    "Invite sent",
    "Archive this project?",
    "Project archived",
    "Import status",
    "Notifications",
)

INJECTORS = {}

# --- 2 and 3. Composition. Structure comes from the recipe shape; the stream picks words only. --


def compose(rng, shape):
    project_name = rng.choice(PROJECT_NAMES)
    recent = rng.sample(RECENT_PROJECT_POOL, shape["recent_projects"])
    last_synced = rng.choice(LAST_SYNCED_PHRASES)
    invite_days = rng.choice(INVITE_EXPIRY_DAYS)
    digest_options = rng.choice(DIGEST_OPTION_SETS)
    skipped_count = rng.choice(IMPORT_SKIPPED_ROW_COUNTS)
    skipped_rows = sorted(rng.sample(IMPORT_ROW_NUMBER_POOL, skipped_count))

    sections = (
        _workspace_overview(recent, last_synced),
        _project_settings(project_name),
        _invite_member(),
        _invite_sent(invite_days),
        _archive_confirm(project_name),
        _project_archived(project_name),
        _import_status(skipped_rows),
        _notification_settings(digest_options),
    )
    body = el("body", "#root", children=(el("h1", "h0", children=(PAGE_HEADING,)), *sections))
    return HtmlDocument(title=PAGE_TITLE, root=body)


def _section(index, children):
    sid = SECTION_IDS[index]
    n = index + 1
    return el(
        "section",
        f"s{n}",
        attrs=(("id", sid),),
        children=(el("h2", f"s{n}.h", children=(SECTION_TITLES[index],)), *children),
    )


def _list_with_and(items):
    """'a', 'a and b', or 'a, b, and c': a plain-English list join. Used
    only for filler prose (the skipped-row count in the import-status
    message), never for anything an injector or a location depends on."""
    items = list(items)
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _link(slot, section_id, key, target_id, label):
    return el(
        "a",
        slot,
        attrs=(("id", f"{section_id}-{key}"), ("href", f"#{target_id}")),
        children=(label,),
    )


def _workspace_overview(recent, last_synced):
    items = tuple(el("li", f"s1.recent{i}", children=(name,)) for i, name in enumerate(recent, start=1))
    return _section(
        0,
        (
            el(
                "p",
                "s1.p1",
                children=(f"This workspace holds {len(recent) + 1} projects, {last_synced}.",),
            ),
            # A composed <div>, present in the clean recipe and every seeded
            # one. NNG-H8's injector inserts a <div> too; without an
            # ordinary one here, "the artifact's only <div>" would be a
            # mechanical signature for that plant, findable by tag name
            # without reading a word of content. Same reasoning as the id
            # invariant in the module docstring, applied to tag choice.
            el(
                "div",
                "s1.recent-wrap",
                attrs=(("id", "workspace-overview-recent"),),
                children=(el("ul", "s1.recent-list", children=items),),
            ),
            _link("s1.projects-link", "workspace-overview", "projects-link", "project-settings", "Open project settings"),
            _link("s1.import-link", "workspace-overview", "import-link", "import-status", "View last import result"),
        ),
    )


def _project_settings(project_name):
    form = el(
        "form",
        "s2.form",
        children=(
            el("label", "s2.name-label", attrs=(("for", "project-settings-name-input"),), children=("Project name",)),
            el(
                "input",
                "s2.name-input",
                attrs=(("id", "project-settings-name-input"), ("type", "text"), ("value", project_name)),
            ),
            el(
                "button",
                "s2.save-btn",
                attrs=(("id", "project-settings-save-btn"), ("type", "submit")),
                children=("Save",),
            ),
        ),
    )
    duplicate_btn = el(
        "button",
        "s2.duplicate-btn",
        attrs=(
            ("id", "project-settings-duplicate-btn"),
            ("type", "button"),
            ("aria-label", "Duplicate project"),
        ),
    )
    return _section(
        1,
        (
            form,
            duplicate_btn,
            _link("s2.notif-link", "project-settings", "notif-link", "notification-settings", "Go to notification settings"),
            _link("s2.invite-link", "project-settings", "invite-link", "invite-member", "Invite a team member"),
            _link("s2.archive-link", "project-settings", "archive-link", "archive-confirm", "Archive project"),
            _link("s2.back-link", "project-settings", "back-link", "workspace-overview", "Back to your projects"),
        ),
    )


def _invite_member():
    form = el(
        "form",
        "s3.form",
        children=(
            el("label", "s3.email-label", attrs=(("for", "invite-member-email-input"),), children=("Email address",)),
            el("input", "s3.email-input", attrs=(("id", "invite-member-email-input"), ("type", "email"))),
            el(
                "button",
                "s3.save-btn",
                attrs=(("id", "invite-member-save-btn"), ("type", "submit")),
                children=("Save",),
            ),
        ),
    )
    return _section(
        2,
        (
            form,
            _link("s3.continue-link", "invite-member", "continue-link", "invite-sent", "Continue"),
            _link("s3.cancel-link", "invite-member", "cancel-link", "project-settings", "Cancel"),
        ),
    )


def _invite_sent(invite_days):
    return _section(
        3,
        (
            el(
                "p",
                "s4.p1",
                children=(
                    f"An invite was sent to the address entered above. It expires in "
                    f"{invite_days} days if not accepted.",
                ),
            ),
            _link("s4.exit-link", "invite-sent", "exit-link", "project-settings", "Back to project settings"),
        ),
    )


def _archive_confirm(project_name):
    copy_text = (
        f'Archiving "{project_name}" will remove it from the active projects list for everyone on '
        f"the team. You can restore it at any time from the archived projects list."
    )
    return _section(
        4,
        (
            el("p", "s5.copy", attrs=(("id", "archive-confirm-copy"),), children=(copy_text,)),
            _link("s5.cancel-link", "archive-confirm", "cancel-link", "project-settings", "Cancel"),
            _link("s5.archive-link", "archive-confirm", "archive-link", "project-archived", "Archive"),
        ),
    )


def _project_archived(project_name):
    return _section(
        5,
        (
            el(
                "p",
                "s6.p1",
                children=(
                    # Deliberately states no reversal path: archive-confirm's
                    # closing sentence is the artifact's single statement of
                    # reversibility, so NNG-H3-UNDO's injector has exactly one
                    # sentence to remove. See the module docstring.
                    f'"{project_name}" has been moved to archived projects. It no longer appears '
                    f"in the active projects list for anyone on the team.",
                ),
            ),
            _link("s6.exit-link", "project-archived", "exit-link", "workspace-overview", "Back to your projects"),
        ),
    )


def _import_status(skipped_rows):
    row_list = _list_with_and(str(n) for n in skipped_rows)
    message = (
        f"The last import finished with {len(skipped_rows)} rows skipped: each referenced a project "
        f"that does not exist in this workspace. Rows {row_list} were skipped; every other row was "
        f"imported."
    )
    return _section(
        6,
        (
            el("p", "s7.message", attrs=(("id", "import-status-message"),), children=(message,)),
            _link("s7.exit-link", "import-status", "exit-link", "workspace-overview", "Back to your projects"),
        ),
    )


def _notification_settings(digest_options):
    options = tuple(el("option", f"s8.opt{i}", children=(label,)) for i, label in enumerate(digest_options, start=1))
    form = el(
        "form",
        "s8.form",
        children=(
            el(
                "label",
                "s8.digest-label",
                attrs=(("for", "notification-settings-digest-input"),),
                children=("Digest frequency",),
            ),
            el("select", "s8.digest-input", attrs=(("id", "notification-settings-digest-input"),), children=options),
            el(
                "button",
                "s8.save-btn",
                attrs=(("id", "notification-settings-save-btn"), ("type", "submit")),
                children=("Save",),
            ),
        ),
    )
    return _section(
        7,
        (form, _link("s8.back-link", "notification-settings", "back-link", "project-settings", "Back to project settings")),
    )


# --- 4. Injectors, keyed by criterion ID. Each returns a new composition, never mutates. --------


@injector("NNG-H3-DEADEND", phase="structure")
def inject_deadend(rng, doc, target):
    """Remove the one control inside the target state whose target names
    another defined state, leaving the state with zero outgoing edges."""
    section_slot = f"s{target.section}"
    link_slot = f"s{target.section}.{target.element}"
    return InjectionResult(
        composed=doc.remove_element(link_slot),
        slot=section_slot,
        severity_expected=3,
        description=(
            "The one control inside this state whose target names another defined state was "
            "removed, leaving the state with zero outgoing edges."
        ),
    )


@injector("NNG-H4-CONTROL-NAMING")
def inject_control_naming(rng, doc, target):
    """Change one commit control's label to a different member of the
    same fixed synonym set every other commit control in the artifact
    uses, introducing a second distinct label for what reads as one
    action.

    Scoring note for P3: this defect is planted at one element, but the
    breach it creates is a property of the whole set of commit labels, and
    the criterion's operational test says to list every occurrence. A
    correct run therefore emits one claim per commit control (three here),
    of which one matches the planted location and the rest count against
    precision. That is bench/README.md's stated v0.1 conservatism ("a
    finding that is genuinely correct but was not planted counts against
    precision", S-03 OQ-2), not a defect in either side, and it is
    recorded here so the number is not read as a false-positive rate.
    """
    slot = f"s{target.section}.{target.element}"
    new_label = rng.choice(CONTROL_NAMING_ALT_LABELS)
    return InjectionResult(
        composed=doc.replace_text(slot, new_label),
        slot=slot,
        severity_expected=2,
        description=(
            "This commit control's label was changed to a different member of the fixed commit "
            "synonym set than the label every other commit control in the artifact carries, so two "
            "distinct labels now name what reads as the same action."
        ),
    )


@injector("NNG-H6-LABELED")
def inject_labeled(rng, doc, target):
    """Remove this control's accessible-name attribute, leaving a control
    with no text content and no name a user or a script can read."""
    slot = f"s{target.section}.{target.element}"
    return InjectionResult(
        composed=doc.remove_attr(slot, "aria-label"),
        slot=slot,
        severity_expected=2,
        description=(
            "This control's accessible-name attribute was removed, and it carries no text content, "
            "so nothing on screen names what the control does."
        ),
    )


@injector("NNG-H5-CONFIRM")
def inject_confirm(rng, doc, target):
    """Rewrite this costly control's target so it reaches the committed
    result state directly, bypassing the confirmation state.

    The confirmation state itself is left in the artifact, unreachable
    from this control. That is deliberate: the defect this plants is that
    the gate sits off the path the control actually takes, which is the
    case NNG-H5-CONFIRM's operational test names explicitly. It also keeps
    the artifact's single statement of reversibility (archive-confirm's
    closing sentence) present, so this recipe plants exactly one defect
    rather than silently also breaching NNG-H3-UNDO, which it does not
    declare.
    """
    slot = f"s{target.section}.{target.element}"
    return InjectionResult(
        composed=doc.set_attr(slot, "href", "#project-archived"),
        slot=slot,
        severity_expected=3,
        description=(
            "This control's target was rewritten to reach the committed result state directly, so "
            "the action now commits on a single interaction and the gating step that named its "
            "consequence beforehand is never reached from it."
        ),
    )


@injector("NNG-H9-IDENTIFY")
def inject_identify(rng, doc, target):
    """Replace a specific failure message with a generic notice carrying
    a raw error code, naming neither which entries failed nor why."""
    slot = f"s{target.section}.{target.element}"
    new_text = rng.choice(GENERIC_IMPORT_ERROR_VARIANTS)
    return InjectionResult(
        composed=doc.replace_text(slot, new_text),
        slot=slot,
        severity_expected=3,
        description=(
            "This failure message was replaced with a generic notice carrying a raw error code, "
            "naming neither which entries failed nor why."
        ),
    )


@injector("NNG-H3-UNDO")
def inject_undo(rng, doc, target):
    """Remove the sentence naming how this action can be reversed.

    The clean composition states reversibility exactly once, as this
    element's closing sentence (see the module docstring), so removing it
    leaves no reversal path named anywhere in the artifact and the
    manifest's description of the defect is true of the artifact a critic
    actually reads.
    """
    slot = f"s{target.section}.{target.element}"
    sentences = split_sentences(doc.element(slot).text())
    kept = " ".join(sentences[:-1]) if len(sentences) > 1 else sentences[0]
    return InjectionResult(
        composed=doc.replace_text(slot, kept),
        slot=slot,
        severity_expected=3,
        description=(
            "The sentence naming how this action can be reversed was removed, and no reversal for "
            "it appears anywhere else in the artifact."
        ),
    )


@injector("NNG-H8", phase="structure")
def inject_minimalist(rng, doc, target):
    """Insert a promotional element unrelated to this screen's task ahead
    of its primary control, pushing that control further down the
    screen."""
    anchor = f"s{target.section}.{target.element}"
    suffix, text = rng.choice(PROMO_BANNER_VARIANTS)
    section_id = SECTION_IDS[target.section - 1]
    banner_slot = f"s{target.section}.promo"
    # No class attribute: nothing the composition produces carries one, so a
    # class here would let `class=` locate this plant by grep, with no
    # reading of the artifact at all. The content-derived id is the only
    # attribute it needs, and it is the shape every composed element uses.
    banner = el(
        "div",
        banner_slot,
        attrs=(("id", f"{section_id}-{suffix}"),),
        children=(text,),
    )
    return InjectionResult(
        composed=doc.insert_before(anchor, banner),
        slot=banner_slot,
        severity_expected=2,
        description=(
            "A promotional element unrelated to this screen's task was inserted ahead of its "
            "primary control, pushing that control further down the screen."
        ),
    )


# --- 5. Addressing. Called by the harness after every injection, on the final composition. ------

_NOUN_BY_TAG = {
    "a": "link",
    "button": "control",
    "input": "field",
    "select": "field",
    "textarea": "field",
    "section": "section",
    "p": "message",
    "div": "element",
}


def address(doc, slot, sentence=None):
    element = doc.element(slot)
    element_id = element.attr("id")
    if not element_id:
        raise ValueError(f"slot {slot!r} resolved to an element with no id attribute")
    noun = _NOUN_BY_TAG.get(element.tag, element.tag)
    return Location(kind="element-id", element_id=element_id, text=f'the "{element_id}" {noun}')


# --- 6. Recipes. Four artifacts, one of them clean, matching bench/README.md's corpus design ----
#        table for the usability domain (4 artifacts, 1 clean). All seven criteria are planted
#        across the three seeded recipes; no recipe repeats a criterion within one section. -------


def _shape(recent_projects):
    return {"recent_projects": recent_projects}


RECIPES = (
    Recipe(
        id="usability-001",
        shape=_shape(2),
        plants=(
            Plant("NNG-H3-DEADEND", Target(section=4, element="exit-link"), severity_expected=3),
            Plant("NNG-H6-LABELED", Target(section=2, element="duplicate-btn"), severity_expected=2),
            Plant("NNG-H8", Target(section=1, element="projects-link"), severity_expected=2),
        ),
    ),
    Recipe(
        id="usability-002",
        shape=_shape(4),
        plants=(
            Plant("NNG-H4-CONTROL-NAMING", Target(section=8, element="save-btn"), severity_expected=2),
            Plant("NNG-H5-CONFIRM", Target(section=2, element="archive-link"), severity_expected=3),
        ),
    ),
    Recipe(
        id="usability-003",
        shape=_shape(3),
        plants=(
            Plant("NNG-H9-IDENTIFY", Target(section=7, element="message"), severity_expected=3),
            Plant("NNG-H3-UNDO", Target(section=5, element="copy"), severity_expected=3),
        ),
    ),
    Recipe(id="usability-004", shape=_shape(3), plants=()),
)

DOMAIN = Domain(
    name="usability",
    artifact_type="html",
    extension=".html",
    namespaces=("NNG",),
    compose=compose,
    render=render,
    address=address,
    injectors=INJECTORS,
    recipes=RECIPES,
)
