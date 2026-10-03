"""Forms domain: critique-forms's bench corpus module.

Artifact type: html. Namespace: FORMS. See bench/generator/README.md for the
domain-plugin API this module implements, and skills/critique-forms/
references/FORMS.md and skills/critique-forms/scripts/checks.py for the
criterion registry this module seeds (all 18 scripted criteria, plus 3 of
the 6 judged criteria, matching the README checklist's ">=3 judged-lane
criteria" floor).

Uses the shared html composition model (bench/generator/html.py:
HtmlDocument, el, render), the same one bench/generator/domains/usability.py
uses, rather than a domain-local element tree: this module is not the first
html domain to land, so the shared module already exists.

Fictional setting, per bench/README.md, "Content and licensing": a fictional
outdoor-gear retailer, Meridian Outfitters. No real product, no reproduced
rubric text.

One shared page skeleton, identical across all four recipes (the one thing
`shape` varies is a little cosmetic vocabulary, never structure): a single
<form> wide enough to host all 21 planted criteria at a distinct, named
slot, every field clean by default against every one of the 18 scripted
checks. Each injector changes exactly the one thing its own criterion
tests, which is what lets the clean recipe (forms-004) be a genuine
zero-finding artifact and each seeded recipe plant only what it declares.

Six fields are inserted only when their own criterion plants them
(structure-phase): the house-number field (FORMS-ADDRESS-FORMAT), the
second password field (FORMS-CONFIRM-PASSWORD), the three birth-date
selects (FORMS-DATE-SELECTS), the "how did you hear about us" select
(FORMS-FIELD-NECESSITY), the reset button (FORMS-RESET-BUTTON), and the
given/family name pair that replaces the single "Your name" field
(FORMS-SPLIT-ENTITY). Everywhere else, a criterion's injector mutates one
attribute or one text node of an element the skeleton already composes.

Three criteria plant at a different element than the one they mutate, each
following accessibility.py's WCAG-3.3.2 precedent ("the plant targets the
control... the mutation lands on the paired label, one slot over"):
FORMS-PHONE-REASON mutates the phone field's own explanatory paragraph but
addresses the phone field itself (which is where checks.py's own finding
points); FORMS-PLACEHOLDER-INSTRUCTION and FORMS-REQUIRED-OPTIONAL mutate a
label's text but address the field that label belongs to, for the same
reason.
"""

from __future__ import annotations

from bench.generator.api import Domain, InjectionResult, Location, Plant, Recipe, Target, injector
from bench.generator.html import Element, HtmlDocument, el as _raw_el, render

# ---------------------------------------------------------------------------
# 1. Vocabulary. Frozen tuples. Order is part of the corpus identity:
#    appending is safe, reordering or removing regenerates every artifact.
# ---------------------------------------------------------------------------

PAGE_TITLES = (
    "Create your Meridian Outfitters account",
    "Join Meridian Outfitters",
)
H1_TEXTS = (
    "Create your account",
    "Set up your account",
)

SHIPPING_SPEED_OPTIONS = ("Standard", "Express", "Overnight", "Next-day", "International")
HEAR_ABOUT_OPTIONS = ("Search engine", "Social media", "Friend or colleague", "Advertisement", "Other")

DAY_OPTIONS = tuple(str(d) for d in range(1, 32))
MONTH_OPTIONS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
# 60 real options: well past the ">30" threshold FORMS-DATE-SELECTS' severity
# 3 anchor names ("a year list running back a hundred years").
YEAR_OPTIONS = tuple(str(y) for y in range(1950, 2010))

PHONE_REASON_CLEAN = "We will text you about delivery updates."
PHONE_REASON_DIRTY = "Thanks for signing up."

INJECTORS: dict = {}

# ---------------------------------------------------------------------------
# 2 and 3. Structure and composition. A tiny local wrapper over the shared
#    html.el(): every slotted element's own `id` equals its slot, assigned
#    unconditionally, in the clean composition and every seeded one alike
#    (bench/README.md's html invariant). `_static` is for elements with no
#    identity of their own (never a plant target, never addressed): <option>
#    and <legend>, matching accessibility.py's own convention.
# ---------------------------------------------------------------------------


def _el(tag: str, slot: str, *, attrs: tuple = (), children: tuple = ()) -> Element:
    if not any(k == "id" for k, _v in attrs):
        attrs = (("id", slot), *attrs)
    return _raw_el(tag, slot, attrs=attrs, children=children)


def _static(tag: str, *, attrs: tuple = (), children: tuple = ()) -> Element:
    return _raw_el(tag, slot="", attrs=attrs, children=children)


def _label(slot: str, for_slot: str, text: str) -> Element:
    return _el("label", slot, attrs=(("for", for_slot),), children=(text,))


def _row(slot: str, children: tuple) -> Element:
    return _el("div", slot, children=children)


def _options(labels: tuple) -> tuple:
    return tuple(_static("option", children=(t,)) for t in labels)


def compose(rng, shape) -> HtmlDocument:
    page_title = rng.choice(PAGE_TITLES)
    h1_text = rng.choice(H1_TEXTS)

    row_name = _row("row-name", (
        _label("name-label", "name-input", "Full name"),
        _el("input", "name-input", attrs=(
            ("name", "full_name"), ("type", "text"), ("autocomplete", "name"),
            ("autocorrect", "off"), ("spellcheck", "false"), ("required", ""),
        )),
    ))
    row_email = _row("row-email", (
        _label("email-label", "email-input", "Email address"),
        _el("input", "email-input", attrs=(
            ("name", "email"), ("type", "email"), ("autocomplete", "email"), ("required", ""),
        )),
    ))
    row_password = _row("row-password", (
        _label("password-label", "password-input", "Create a password"),
        _el("input", "password-input", attrs=(
            ("name", "password"), ("type", "password"), ("autocomplete", "new-password"),
            ("minlength", "8"), ("required", ""),
        )),
    ))
    row_street = _row("row-street", (
        _label("street-label", "street-input", "Street address"),
        _el("input", "street-input", attrs=(
            ("name", "street_address"), ("type", "text"), ("autocomplete", "address-line1"),
            ("autocorrect", "off"), ("spellcheck", "false"), ("required", ""),
        )),
    ))
    row_phone = _row("row-phone", (
        _label("phone-label", "phone-input", "Phone number"),
        _el("input", "phone-input", attrs=(
            ("name", "phone"), ("type", "tel"), ("autocomplete", "tel"), ("required", ""),
        )),
        _raw_el("p", "phone-reason-text", children=(PHONE_REASON_CLEAN,)),
    ))
    row_phone2 = _row("row-phone2", (
        _label("phone2-label", "phone2-input", "Secondary phone (optional)"),
        _el("input", "phone2-input", attrs=(
            ("name", "phone_secondary"), ("type", "tel"), ("autocomplete", "tel"),
        )),
    ))
    row_website = _row("row-website", (
        _label("website-label", "website-input", "Company website"),
        _el("input", "website-input", attrs=(("name", "website"), ("type", "url"), ("required", ""))),
    ))
    row_member = _row("row-member", (
        _label("member-label", "member-input", "Membership number (8 digits)"),
        _el("input", "member-input", attrs=(
            ("name", "membership_number"), ("type", "text"), ("inputmode", "numeric"),
            ("placeholder", "Must be 8 digits"), ("required", ""),
        )),
    ))
    row_acctnum = _row("row-acctnum", (
        _label("acctnum-label", "acctnum-input", "Account number"),
        _el("input", "acctnum-input", attrs=(
            ("name", "account_number"), ("type", "text"), ("inputmode", "numeric"), ("required", ""),
        )),
    ))
    row_postal = _row("row-postal", (
        _label("postal-label", "postal-input", "Postal code"),
        _el("input", "postal-input", attrs=(
            ("name", "postal_code"), ("type", "text"), ("autocomplete", "postal-code"), ("required", ""),
        )),
    ))
    row_shipspeed = _row("row-shipspeed", (
        _label("shipspeed-label", "shipspeed-select", "Preferred shipping speed"),
        _el("select", "shipspeed-select", attrs=(("required", ""),), children=_options(SHIPPING_SPEED_OPTIONS)),
    ))
    row_legalname = _row("row-legalname", (
        _label("legalname-label", "legalname-input", "Your name"),
        _el("input", "legalname-input", attrs=(
            ("name", "legal_name"), ("type", "text"), ("autocomplete", "name"),
            ("autocorrect", "off"), ("spellcheck", "false"), ("required", ""),
        )),
    ))
    row_org = _row("row-org", (
        _label("org-label", "org-input", "Organization name"),
        _el("input", "org-input", attrs=(
            ("name", "organization"), ("type", "text"), ("style", "font-size:16px"), ("required", ""),
        )),
    ))
    row_contacttime = _row("row-contacttime", (
        _el("label", "contacttime-label", attrs=(("for", "contacttime-input"), ("style", "display:block")),
            children=("Preferred contact time",)),
        _el("input", "contacttime-input", attrs=(
            ("name", "contact_time"), ("type", "text"), ("required", ""),
        )),
    ))
    viewdetails_btn = _el("button", "viewdetails-btn", attrs=(
        ("type", "button"), ("style", "padding:12px 20px;font-size:16px"),
    ), children=("View details",))
    submit_btn = _el("button", "submit-btn", attrs=(("type", "submit"),), children=("Create account",))

    form = _el("form", "form", children=(
        row_name, row_email, row_password, row_street, row_phone, row_phone2,
        row_website, row_member, row_acctnum, row_postal, row_shipspeed,
        row_legalname, row_org, row_contacttime, viewdetails_btn, submit_btn,
    ))
    body = _raw_el("body", "#root", children=(
        _raw_el("h1", "h0", children=(h1_text,)),
        form,
    ))
    return HtmlDocument(title=page_title, root=body)


# ---------------------------------------------------------------------------
# 4. Injectors, keyed by criterion ID. Each reads its target location from
#    `target.element`, the slot the plant is about; every injector returns
#    a new HtmlDocument, never mutating the one it is given.
# ---------------------------------------------------------------------------


@injector("FORMS-ACTION-LABEL")
def inject_action_label(rng, doc, target):
    slot = target.element
    return InjectionResult(
        composed=doc.replace_text(slot, "Submit"),
        slot=slot,
        severity_expected=2,
        description="The form's primary button is relabelled with a bare generic word that says nothing about what pressing it does.",
    )


@injector("FORMS-ADDRESS-FORMAT", phase="structure")
def inject_address_format(rng, doc, target):
    """Insert a required house-number field ahead of the street-address
    field the clean composition already carries, so an address with no
    number cannot be entered."""
    slot = target.element
    row = _row("row-housenumber", (
        _label("housenumber-label", slot, "House number"),
        _el("input", slot, attrs=(("name", "house_number"), ("type", "text"), ("required", ""))),
    ))
    return InjectionResult(
        composed=doc.insert_before("row-street", row),
        slot=slot,
        severity_expected=3,
        description="A required house-number field is inserted ahead of the street-address field, splitting one address line into two and leaving an address with no number impossible to enter.",
    )


@injector("FORMS-AUTOCOMPLETE")
def inject_autocomplete(rng, doc, target):
    slot = target.element
    return InjectionResult(
        composed=doc.set_attr(slot, "autocomplete", "e-mail"),
        slot=slot,
        severity_expected=3,
        description="This field's autocomplete value is replaced with a token the HTML standard does not define, so autofill is certainly broken for it.",
    )


@injector("FORMS-AUTOCORRECT")
def inject_autocorrect(rng, doc, target):
    slot = target.element
    doc2 = doc.remove_attr(slot, "autocorrect")
    doc2 = doc2.remove_attr(slot, "spellcheck")
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=2,
        description="A name field's autocorrect and spellcheck switches are removed, leaving autocorrection and spellchecking on for a value a phone keyboard's dictionary does not know.",
    )


@injector("FORMS-CONFIRM-PASSWORD", phase="structure")
def inject_confirm_password(rng, doc, target):
    slot = target.element
    row = _row("row-confirm-password", (
        _label("confirm-password-label", slot, "Confirm password"),
        _el("input", slot, attrs=(
            ("name", "password_again"), ("type", "password"), ("autocomplete", "new-password"), ("required", ""),
        )),
    ))
    return InjectionResult(
        composed=doc.insert_after("row-password", row),
        slot=slot,
        severity_expected=2,
        description="The new password is asked for a second time to confirm it, doubling the typing the new-password field already collects once.",
    )


@injector("FORMS-DATE-SELECTS", phase="structure")
def inject_date_selects(rng, doc, target):
    """Insert a birth-date fieldset of three drop-downs, with a year list
    long enough (60 real options) to trigger the severity-3 anchor."""
    slot = target.element
    fieldset = _el("fieldset", "row-dob", children=(
        _static("legend", children=("Date of birth",)),
        _label("dob-day-label", "dob-day-select", "Day"),
        _el("select", "dob-day-select", attrs=(("autocomplete", "bday-day"), ("required", "")),
            children=_options(DAY_OPTIONS)),
        _label("dob-month-label", "dob-month-select", "Month"),
        _el("select", "dob-month-select", attrs=(("autocomplete", "bday-month"), ("required", "")),
            children=_options(MONTH_OPTIONS)),
        _label("dob-year-label", "dob-year-select", "Year"),
        _el("select", "dob-year-select", attrs=(("autocomplete", "bday-year"), ("required", "")),
            children=_options(YEAR_OPTIONS)),
    ))
    return InjectionResult(
        composed=doc.insert_before("submit-btn", fieldset),
        slot=slot,
        severity_expected=3,
        description="A birth date is collected through three drop-downs instead of three short text fields, with a year list long enough that reaching the right year costs a long scroll.",
    )


@injector("FORMS-FIELD-WIDTH")
def inject_field_width(rng, doc, target):
    slot = target.element
    return InjectionResult(
        composed=doc.set_attr(slot, "size", "3"),
        slot=slot,
        severity_expected=3,
        description="A postal-code field is sized to far fewer characters than a typical postal code needs, so the value cannot stay visible while it is typed and checked.",
    )


@injector("FORMS-FORMAT-TOLERANCE")
def inject_format_tolerance(rng, doc, target):
    slot = target.element
    return InjectionResult(
        composed=doc.set_attr(slot, "pattern", "[0-9]+"),
        slot=slot,
        severity_expected=3,
        description="A phone field gains a pattern accepting digits only, rejecting the same number written with the spaces, dashes or brackets people commonly use.",
    )


@injector("FORMS-INPUT-FONT-SIZE")
def inject_input_font_size(rng, doc, target):
    slot = target.element
    return InjectionResult(
        composed=doc.set_attr(slot, "style", "font-size:13px"),
        slot=slot,
        severity_expected=2,
        description="A field's declared text size is lowered below the 16-pixel threshold at which a phone stops zooming the page on focus.",
    )


@injector("FORMS-INPUT-TYPE")
def inject_input_type(rng, doc, target):
    slot = target.element
    return InjectionResult(
        composed=doc.set_attr(slot, "type", "text"),
        slot=slot,
        severity_expected=2,
        description="A field collecting a web address declares the plain text type instead of the type built for that value, so a phone shows the wrong keyboard.",
    )


@injector("FORMS-NUMERIC-INPUTMODE")
def inject_numeric_inputmode(rng, doc, target):
    slot = target.element
    return InjectionResult(
        composed=doc.remove_attr(slot, "inputmode"),
        slot=slot,
        severity_expected=2,
        description="A digit-string field that is not a quantity loses its numeric input mode, so a phone shows the full keyboard for typing digits.",
    )


@injector("FORMS-OPTION-CONTROL", phase="structure")
def inject_option_control(rng, doc, target):
    """Drop two of the five clean options, leaving three: a single choice
    among fewer than five options, which belongs on visible radio buttons."""
    slot = target.element
    kept = _options(SHIPPING_SPEED_OPTIONS[:3])
    return InjectionResult(
        composed=doc.replace_children(slot, kept),
        slot=slot,
        severity_expected=2,
        description="A single choice among fewer than five options is left in a drop-down instead of visible radio buttons, so the person must open it to see every option.",
    )


@injector("FORMS-PASSWORD-RULES")
def inject_password_rules(rng, doc, target):
    slot = target.element
    return InjectionResult(
        composed=doc.set_attr(slot, "minlength", "6"),
        slot=slot,
        severity_expected=2,
        description="The new-password field's minimum length is lowered below eight characters, letting a person choose a password too short to be safe.",
    )


@injector("FORMS-PHONE-REASON")
def inject_phone_reason(rng, doc, target):
    """The plant targets the phone field itself (where checks.py's own
    finding points, per references/FORMS.md's phone-reason operational
    test); the mutation lands on the field's own explanatory paragraph,
    one slot over, matching accessibility.py's WCAG-3.3.2 precedent."""
    slot = target.element
    return InjectionResult(
        composed=doc.replace_text("phone-reason-text", PHONE_REASON_DIRTY),
        slot=slot,
        severity_expected=3,
        description="A required phone field's explanatory text is replaced with neutral wording that says nothing about why the number is needed, though the form also asks for an email address.",
    )


@injector("FORMS-PLACEHOLDER-INSTRUCTION")
def inject_placeholder_instruction(rng, doc, target):
    """The plant targets the field itself; the mutation lands on its own
    label, one slot over, matching the same accessibility.py precedent."""
    slot = target.element
    return InjectionResult(
        composed=doc.replace_text("member-label", "Membership number"),
        slot=slot,
        severity_expected=3,
        description="A field's label is shortened to drop the format rule it used to restate, leaving that rule stated only in the placeholder, which disappears as soon as typing starts.",
    )


@injector("FORMS-REQUIRED-OPTIONAL")
def inject_required_optional(rng, doc, target):
    """The plant targets the one optional field in the form; the mutation
    lands on its own label, one slot over, matching the same precedent."""
    slot = target.element
    return InjectionResult(
        composed=doc.replace_text("phone2-label", "Secondary phone"),
        slot=slot,
        severity_expected=3,
        description="The form's one optional field loses the word marking it optional, leaving a mix of required and optional fields with no field anywhere marked either way.",
    )


@injector("FORMS-RESET-BUTTON", phase="structure")
def inject_reset_button(rng, doc, target):
    slot = target.element
    button = _el("button", slot, attrs=(("type", "reset"),), children=("Clear form",))
    return InjectionResult(
        composed=doc.insert_after("submit-btn", button),
        slot=slot,
        severity_expected=3,
        description="A control that clears every entered value is inserted directly beside the primary submit button, where a press aimed at one can land on the other.",
    )


@injector("FORMS-SPLIT-ENTITY", phase="structure")
def inject_split_entity(rng, doc, target):
    """Replace the single clean name field with a given-name/family-name
    pair. Both new fields carry their own valid autocomplete token and a
    clean autocorrect/spellcheck state, so this plant does not also, and
    silently, breach FORMS-AUTOCORRECT or FORMS-AUTOCOMPLETE."""
    slot = target.element
    given = _el("input", slot, attrs=(
        ("name", "given_name"), ("type", "text"), ("autocomplete", "given-name"),
        ("autocorrect", "off"), ("spellcheck", "false"), ("required", ""),
    ))
    family = _el("input", "family-input", attrs=(
        ("name", "family_name"), ("type", "text"), ("autocomplete", "family-name"),
        ("autocorrect", "off"), ("spellcheck", "false"), ("required", ""),
    ))
    new_children = (
        _label("given-label", slot, "First name"), given,
        _label("family-label", "family-input", "Last name"), family,
    )
    return InjectionResult(
        composed=doc.replace_children("row-legalname", new_children),
        slot=slot,
        severity_expected=2,
        description="A single name field is split into separate given-name and family-name fields, so a name that does not fit that shape must be forced into it.",
    )


# --- Judged-lane injectors (>=3 required; three implemented). -------------


@injector("FORMS-FIELD-NECESSITY", phase="structure")
def inject_field_necessity(rng, doc, target):
    """Insert a required field whose answer the account-creation task does
    not use: a marketing-attribution question, asked before it could wait
    until after the account exists."""
    slot = target.element
    row = _row("row-hear", (
        _label("hear-label", slot, "How did you hear about us?"),
        _el("select", slot, attrs=(("required", ""),), children=_options(HEAR_ABOUT_OPTIONS)),
    ))
    return InjectionResult(
        composed=doc.insert_before("submit-btn", row),
        slot=slot,
        severity_expected=3,
        description="A required marketing-attribution question is inserted into the form, though creating the account uses none of its answers and the question could wait until afterward.",
    )


@injector("FORMS-LABEL-POSITION")
def inject_label_position(rng, doc, target):
    """A single mutation standing in for a layout judgment: the rest of
    the form's labels stay above their fields, so this one field's label
    now disagrees with the form's own prevailing alignment."""
    slot = target.element
    return InjectionResult(
        composed=doc.set_attr(f"{slot[:-len('-input')]}-label", "style", "display:inline-block;float:left;width:140px"),
        slot=slot,
        severity_expected=2,
        description="One field's label is set to render beside its field while every other label in the form renders above its own, so the form no longer keeps one label alignment throughout.",
    )


@injector("FORMS-TOUCH-TARGET")
def inject_touch_target(rng, doc, target):
    slot = target.element
    return InjectionResult(
        composed=doc.set_attr(slot, "style", "padding:1px 2px;font-size:11px"),
        slot=slot,
        severity_expected=3,
        description="A tappable control's declared padding and text size shrink it well under the size a fingertip needs, with nothing else enlarging the target.",
    )


# ---------------------------------------------------------------------------
# 5. Addressing. Called by the harness after every injection, on the final
#    composition. Every slotted element already carries a content-derived
#    id (assigned at compose time, never renumbered), so every location
#    here is kind "element-id".
# ---------------------------------------------------------------------------

_NOUN_BY_TAG = {
    "input": "field",
    "select": "field",
    "textarea": "field",
    "button": "button",
    "label": "label",
}


def address(doc: HtmlDocument, slot: str, sentence=None) -> Location:
    element = doc.element(slot)
    element_id = element.attr("id")
    if not element_id:
        raise ValueError(f"slot {slot!r} resolved to an element with no id attribute")
    noun = _NOUN_BY_TAG.get(element.tag, element.tag)
    return Location(kind="element-id", element_id=element_id, text=f'the {noun}, id `{element_id}`')


# ---------------------------------------------------------------------------
# 6. Recipes. Four artifacts, one of them clean. All 18 scripted criteria
#    and three judged criteria are planted exactly once each, spread across
#    the three seeded recipes so that every recipe's below-severity-3
#    finding count stays well under the five-finding output bound
#    (skills/_shared/envelope.py's OUTPUT_BOUND_BELOW_SEVERITY_3).
# ---------------------------------------------------------------------------

_SHAPE: dict = {}

RECIPES = (
    Recipe(
        id="forms-001",
        shape=_SHAPE,
        plants=(
            Plant("FORMS-ACTION-LABEL", Target(section=1, element="submit-btn"), severity_expected=2),
            Plant("FORMS-ADDRESS-FORMAT", Target(section=2, element="housenumber-input"), severity_expected=3),
            Plant("FORMS-AUTOCOMPLETE", Target(section=3, element="email-input"), severity_expected=3),
            Plant("FORMS-AUTOCORRECT", Target(section=4, element="name-input"), severity_expected=2),
            Plant("FORMS-CONFIRM-PASSWORD", Target(section=5, element="confirm-password-input"), severity_expected=2),
            Plant("FORMS-FIELD-NECESSITY", Target(section=6, element="hear-select"), severity_expected=3),
        ),
    ),
    Recipe(
        id="forms-002",
        shape=_SHAPE,
        plants=(
            Plant("FORMS-DATE-SELECTS", Target(section=1, element="dob-day-select"), severity_expected=3),
            Plant("FORMS-FIELD-WIDTH", Target(section=2, element="postal-input"), severity_expected=3),
            Plant("FORMS-FORMAT-TOLERANCE", Target(section=3, element="phone2-input"), severity_expected=3),
            Plant("FORMS-INPUT-FONT-SIZE", Target(section=4, element="org-input"), severity_expected=2),
            Plant("FORMS-INPUT-TYPE", Target(section=5, element="website-input"), severity_expected=2),
            Plant("FORMS-LABEL-POSITION", Target(section=6, element="contacttime-input"), severity_expected=2),
        ),
    ),
    Recipe(
        id="forms-003",
        shape=_SHAPE,
        plants=(
            Plant("FORMS-NUMERIC-INPUTMODE", Target(section=1, element="acctnum-input"), severity_expected=2),
            Plant("FORMS-OPTION-CONTROL", Target(section=2, element="shipspeed-select"), severity_expected=2),
            Plant("FORMS-PASSWORD-RULES", Target(section=3, element="password-input"), severity_expected=2),
            Plant("FORMS-PHONE-REASON", Target(section=4, element="phone-input"), severity_expected=3),
            Plant("FORMS-PLACEHOLDER-INSTRUCTION", Target(section=5, element="member-input"), severity_expected=3),
            Plant("FORMS-REQUIRED-OPTIONAL", Target(section=6, element="phone2-input"), severity_expected=3),
            Plant("FORMS-RESET-BUTTON", Target(section=7, element="reset-btn"), severity_expected=3),
            Plant("FORMS-SPLIT-ENTITY", Target(section=8, element="given-input"), severity_expected=2),
            Plant("FORMS-TOUCH-TARGET", Target(section=9, element="viewdetails-btn"), severity_expected=3),
        ),
    ),
    Recipe(id="forms-004", shape=_SHAPE, plants=()),
)

DOMAIN = Domain(
    name="forms",
    artifact_type="html",
    extension=".html",
    namespaces=("FORMS",),
    compose=compose,
    render=render,
    address=address,
    injectors=INJECTORS,
    recipes=RECIPES,
)
