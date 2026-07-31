"""Accessibility domain: critique-accessibility's bench corpus module.

Artifact type: html. Namespace: WCAG. See bench/generator/README.md for the
domain-plugin API this module implements, and skills/critique-accessibility/
SKILL.md and references/WCAG.md for the criterion registry this module
seeds (13 scripted, 4 of the 9 judged criteria, matching the S-05 spec's
'>=3 judged-lane criteria' floor).

No bench/generator/html.py shared composition module exists yet (this is
the first html-artifact domain to land; see bench/generator/leak.py's own
note that html support is established when a first html domain lands). Per
bench/generator/README.md, "What a domain module owes the harness": "A
domain module is one Python file." So the html composition model below
(El, Doc) is domain-local rather than a shared harness module, exactly as
markdown.py is shared only because toy needed it first. A future html
domain (critique-usability) can lift this model into a shared module
without changing this file's public compose/render/address/injectors
contract.

Fictional setting, per bench/README.md, "Content and licensing": a fictional
regional transit agency, Cascadia Regional Transit. No real product, no
reproduced rubric text.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace as _dc_replace
from typing import Mapping, Sequence

from bench.generator.api import Domain, InjectionResult, Location, Plant, Recipe, Target, injector

# ---------------------------------------------------------------------------
# 1. Vocabulary. Frozen tuples. Order is part of the corpus identity:
#    appending is safe, reordering or removing regenerates every artifact.
# ---------------------------------------------------------------------------

PAGE_TITLES = (
    "Cascadia Regional Transit: Route Updates",
    "Cascadia Regional Transit: Rider Services",
    "Cascadia Regional Transit: Fare Information",
    "Cascadia Regional Transit: Service Announcements",
)

H1_TEXTS = (
    "Rider service updates",
    "Current route information",
    "Fare and service announcements",
    "This week at Cascadia Regional Transit",
)

SECTION_TITLES = (
    "Schedule changes",
    "Accessibility improvements",
    "Fare adjustments",
    "Station updates",
    "Weekend service",
)

SUBJECTS = ("Riders", "Commuters", "Passengers", "Local residents")
ACTIONS = (
    "can check real time arrivals",
    "may request a fare adjustment",
    "should review the updated schedule",
    "can report a service issue",
)
CHANNELS = (
    "through the mobile app",
    "at any station kiosk",
    "by calling rider services",
    "through the online portal",
)
TAILS = (
    "Updates post to the schedule page within one business day.",
    "A confirmation message follows once the request is processed.",
    "Station staff can also help with the same request in person.",
    "The change takes effect on the following service day.",
)

IMAGE_ALTS = (
    "A transit operator inspecting the platform screen doors before the morning shift.",
    "A newly installed tactile paving strip along the platform edge.",
    "A station attendant assisting a rider at the fare gate.",
    "Crews repainting the accessible parking spaces near the station entrance.",
)

LINK_PHRASES = (
    "review this month's fare adjustments",
    "view the full route change history",
    "read the accessibility improvements list",
    "check the current station closures",
)

NAV_LABELS = (
    ("Plan a trip", "/plan"),
    ("Fares and passes", "/fares"),
    ("Service alerts", "/alerts"),
    ("Accessibility", "/accessibility"),
)

FOOTER_LINKS = (
    ("Privacy policy", "/privacy"),
    ("Terms of service", "/terms"),
)

STEP_LABELS = ("Choose a plan", "Enter payment details", "Confirm your order")

# ---------------------------------------------------------------------------
# 2. Structure and 3. Composition: a small, domain-local html element tree.
#    Slots are identities; indices (the rendered `id` attribute) are
#    derived from the slot at construction time and never renumbered.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class El:
    """One html element. `children` holds El instances and/or plain str
    text nodes, in document order. `slot` is the element's permanent
    identity; empty for elements (table rows and cells) that are never a
    plant target and never individually addressed."""

    tag: str
    attrs: tuple[tuple[str, str], ...]
    children: tuple[object, ...]
    slot: str


def _el(tag: str, slot: str, attrs: Sequence[tuple[str, str]] = (), children: Sequence[object] = ()) -> El:
    """Build one slotted element. Every slotted element carries a
    content-derived `id` attribute unless one is already supplied (a form
    control needs a specific id for its <label for> pairing), per
    bench/README.md's invariant that every injectable element carries an
    id in clean and seeded artifacts alike, so an id never itself signals
    a plant."""
    attrs = tuple(attrs)
    if slot and not any(k == "id" for k, _v in attrs):
        attrs = attrs + (("id", slot.replace(".", "-")),)
    return El(tag=tag, attrs=attrs, children=tuple(children), slot=slot)


def _static(tag: str, attrs: Sequence[tuple[str, str]] = (), children: Sequence[object] = ()) -> El:
    """An element with no identity of its own: never a plant target,
    never individually addressed. Table rows and cells use this."""
    return El(tag=tag, attrs=tuple(attrs), children=tuple(children), slot="")


def _find(el: El, slot: str) -> El | None:
    if el.slot == slot:
        return el
    for c in el.children:
        if isinstance(c, El):
            found = _find(c, slot)
            if found is not None:
                return found
    return None


def _slot_index_walk(el: El, slot: str, counter: int) -> tuple[int | None, int]:
    if el.slot == slot:
        return counter, counter + 1
    counter += 1
    for c in el.children:
        if isinstance(c, El):
            found, counter = _slot_index_walk(c, slot, counter)
            if found is not None:
                return found, counter
    return None, counter


def _transform(el: El, slot: str, fn) -> El | None:
    if el.slot == slot:
        return fn(el)
    new_children = []
    for c in el.children:
        if isinstance(c, El):
            nc = _transform(c, slot, fn)
            if nc is not None:
                new_children.append(nc)
        else:
            new_children.append(c)
    return _dc_replace(el, children=tuple(new_children))


def _merge_attrs(attrs: tuple[tuple[str, str], ...], updates: Mapping[str, str | None]) -> tuple[tuple[str, str], ...]:
    d = dict(attrs)
    for k, v in updates.items():
        if v is None:
            d.pop(k, None)
        else:
            d[k] = v
    return tuple(d.items())


@dataclass(frozen=True, slots=True)
class Doc:
    """An immutable html document, rooted at the <html> element. Every
    mutation returns a new Doc; nothing here is ever changed in place,
    matching bench/generator/README.md's markdown.Document convention."""

    root: El

    def find(self, slot: str) -> El:
        found = _find(self.root, slot)
        if found is None:
            raise KeyError(f"slot not found: {slot!r}")
        return found

    def slot_index(self, slot: str) -> int:
        """Document order key, read by the harness at manifest-assembly
        time (bench/generator/pipeline.py's _defect_document_position)."""
        found, _ = _slot_index_walk(self.root, slot, 0)
        if found is None:
            raise KeyError(f"slot not found: {slot!r}")
        return found

    def transform(self, slot: str, fn) -> "Doc":
        return Doc(root=_transform(self.root, slot, fn))

    def with_attrs(self, slot: str, updates: Mapping[str, str | None]) -> "Doc":
        return self.transform(slot, lambda el: _dc_replace(el, attrs=_merge_attrs(el.attrs, updates)))

    def with_text(self, slot: str, text: str) -> "Doc":
        return self.transform(slot, lambda el: _dc_replace(el, children=(text,)))

    def with_tag(self, slot: str, tag: str) -> "Doc":
        return self.transform(slot, lambda el: _dc_replace(el, tag=tag))

    def remove(self, slot: str) -> "Doc":
        return self.transform(slot, lambda el: None)

    def reorder(self, parent_slot: str, child_slot_order: Sequence[str]) -> "Doc":
        def fn(el: El) -> El:
            by_slot = {c.slot: c for c in el.children if isinstance(c, El)}
            return _dc_replace(el, children=tuple(by_slot[s] for s in child_slot_order))

        return self.transform(parent_slot, fn)


def _sentence(rng) -> str:
    return f"{rng.choice(SUBJECTS)} {rng.choice(ACTIONS)} {rng.choice(CHANNELS)}."


def _paragraph(rng) -> str:
    return f"{_sentence(rng)} {rng.choice(TAILS)}"


def compose(rng, shape: Mapping[str, object]) -> Doc:
    """Structure below is fixed (declared by this function itself, not by
    `shape`): every recipe composes the same rich page skeleton, wide
    enough to host all 17 planted criteria at a distinct, named slot. The
    one thing `shape` varies is filler paragraph counts per section, kept
    here rather than hardcoded so the convention 'structure from shape,
    words from rng' still holds for the one axis that legitimately
    varies."""
    p1, p2, p3 = shape["paragraphs"]

    title_text = rng.choice(PAGE_TITLES)
    h1_text = rng.choice(H1_TEXTS)
    sec1_title, sec2_title, sec3_title = rng.sample(SECTION_TITLES, 3)
    nav_picks = rng.sample(NAV_LABELS, 2)
    image_alt = rng.choice(IMAGE_ALTS)
    link_phrase = rng.choice(LINK_PHRASES)

    para_rng = rng.child("para")
    s1_paragraphs = [
        _el("p", slot=f"s1.p{i}", children=(_paragraph(para_rng.child(1, i)),)) for i in range(1, p1 + 1)
    ]
    s2_paragraphs = [
        _el("p", slot=f"s2.p{i}", children=(_paragraph(para_rng.child(2, i)),)) for i in range(1, p2 + 1)
    ]
    s3_paragraphs = [
        _el("p", slot=f"s3.p{i}", children=(_paragraph(para_rng.child(3, i)),)) for i in range(1, p3 + 1)
    ]

    head = _el(
        "head",
        slot="head",
        children=(
            _el("meta", slot="head.charset", attrs=(("charset", "utf-8"),)),
            _el(
                "meta",
                slot="head.viewport",
                attrs=(("name", "viewport"), ("content", "width=device-width, initial-scale=1")),
            ),
            _el("title", slot="head.title", children=(title_text,)),
        ),
    )

    nav_links = tuple(
        _el("a", slot=f"nav.link{i + 1}", attrs=(("href", href),), children=(label,))
        for i, (label, href) in enumerate(nav_picks)
    )
    header = _el("header", slot="header", children=(_el("nav", slot="nav", children=nav_links),))
    skiplink = _el(
        "a", slot="body.skiplink", attrs=(("href", "#main-content"),), children=("Skip to main content",)
    )

    section1 = _el(
        "section",
        slot="s1",
        children=(
            _el("h2", slot="s1.h", children=(sec1_title,)),
            *s1_paragraphs,
            _el("img", slot="s1.img1", attrs=(("src", "/img/platform-update.jpg"), ("alt", image_alt))),
        ),
    )

    table_rows = (
        _static(
            "tr",
            children=(
                _static("th", attrs=(("scope", "col"),), children=("Zone",)),
                _static("th", attrs=(("scope", "col"),), children=("Status",)),
            ),
        ),
        _static("tr", children=(_static("td", children=("North",)), _static("td", children=("On time",)))),
        _static("tr", children=(_static("td", children=("South",)), _static("td", children=("On time",)))),
    )
    section2 = _el(
        "section",
        slot="s2",
        children=(
            _el("h2", slot="s2.h", children=(sec2_title,)),
            *s2_paragraphs,
            _el("table", slot="s2.table1", children=table_rows),
        ),
    )

    banner = _el(
        "div",
        slot="s3.banner",
        attrs=(("class", "promo-banner"),),
        children=(_static("p", children=("Route adjustments take effect on the posted effective date.",)),),
    )
    statuscard = _el(
        "div",
        slot="s3.statuscard",
        attrs=(("class", "status-card"),),
        children=(_static("p", children=(_paragraph(para_rng.child("statuscard")),)),),
    )
    button1 = _el(
        "button",
        slot="s3.button1",
        attrs=(("type", "button"), ("class", "btn-secondary")),
        children=("Refresh status",),
    )
    # Genuinely icon-only: the visible content is a decorative image, not a
    # text glyph. A text glyph here would carry a visible label that is not
    # a substring of the accessible name, which is a real WCAG-2.5.3
    # violation the scripted lane reports on every artifact built from this
    # skeleton, clean control included. A clean artifact has to be clean
    # against every scripted check, not only the ones a recipe plants.
    customcontrol = _el(
        "div",
        slot="s3.customcontrol",
        attrs=(
            ("class", "icon-delete"),
            ("role", "button"),
            ("tabindex", "0"),
            ("aria-label", "Delete item"),
        ),
        children=(_static("img", attrs=(("src", "/img/trash-icon.svg"), ("alt", ""))),),
    )
    steps = tuple(
        _el("div", slot=f"s3.step{i + 1}", attrs=(("class", "step"),), children=(label,))
        for i, label in enumerate(STEP_LABELS)
    )
    wizard = _el("div", slot="s3.wizard", attrs=(("class", "wizard-steps"),), children=steps)
    link_para = _el(
        "p",
        slot="s3.linkpara",
        children=(
            "For the full list of upcoming adjustments, ",
            _el("a", slot="s3.link1", attrs=(("href", "/fares/history"),), children=(link_phrase,)),
            ".",
        ),
    )

    topic_select = _el(
        "select",
        slot="s3.form.topic",
        attrs=(("id", "topic"),),
        children=(_static("option", children=("Northbound",)), _static("option", children=("Southbound",))),
    )
    topic_label = _el("label", slot="s3.form.topic.label", attrs=(("for", "topic"),), children=("Route",))
    email_label = _el(
        "label", slot="s3.form.email.label", attrs=(("for", "email"),), children=("Email address",)
    )
    email_input = _el("input", slot="s3.form.email", attrs=(("id", "email"), ("type", "email")))
    phone_label = _el(
        "label",
        slot="s3.form.phone.label",
        attrs=(("for", "phone"),),
        children=("Phone number (required)",),
    )
    phone_input = _el("input", slot="s3.form.phone", attrs=(("id", "phone"), ("type", "tel")))
    promo_label = _el(
        "label", slot="s3.form.promo.label", attrs=(("for", "promo"),), children=("Promo code",)
    )
    promo_input = _el(
        "input", slot="s3.form.promo", attrs=(("id", "promo"), ("type", "text"), ("aria-invalid", "true"))
    )
    promo_error = _el(
        "span",
        slot="s3.form.promo.error",
        attrs=(("class", "error-text"),),
        children=("Enter a 6 character code using letters and numbers only.",),
    )
    submit_button = _el(
        "button",
        slot="s3.form.submit",
        attrs=(("type", "submit"), ("class", "btn-primary")),
        children=("Submit",),
    )
    form = _el(
        "form",
        slot="s3.form",
        children=(
            topic_label,
            topic_select,
            email_label,
            email_input,
            phone_label,
            phone_input,
            promo_label,
            promo_input,
            promo_error,
            submit_button,
        ),
    )

    section3 = _el(
        "section",
        slot="s3",
        children=(
            _el("h2", slot="s3.h", children=(sec3_title,)),
            *s3_paragraphs,
            banner,
            statuscard,
            button1,
            customcontrol,
            wizard,
            link_para,
            form,
        ),
    )

    main = _el(
        "main",
        slot="main",
        attrs=(("id", "main-content"),),
        children=(_el("h1", slot="main.h1", children=(h1_text,)), section1, section2, section3),
    )

    footer_links = tuple(
        _el("a", slot=f"footer.link{i + 1}", attrs=(("href", href),), children=(label,))
        for i, (label, href) in enumerate(FOOTER_LINKS)
    )
    footer = _el("footer", slot="footer", children=footer_links)

    body = _el("body", slot="body", children=(skiplink, header, main, footer))
    html_el = _el("html", slot="html", attrs=(("lang", "en"),), children=(head, body))
    return Doc(root=html_el)


# ---------------------------------------------------------------------------
# Rendering. Containers put each child on its own line (matching this
# skill's own golden fixtures' zero-indent style); everything else
# concatenates its children inline, so a paragraph's mixed text and <a>
# stay on one line.
# ---------------------------------------------------------------------------

CONTAINER_TAGS = frozenset(
    {"html", "head", "body", "header", "nav", "main", "footer", "section", "form", "table", "div", "ul", "ol"}
)
VOID_TAGS = frozenset({"img", "meta", "input", "br", "hr", "link"})


def _escape_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_attr(v: str) -> str:
    return _escape_text(v).replace('"', "&quot;")


def _render_attrs(attrs: tuple[tuple[str, str], ...]) -> str:
    return "".join(f' {k}="{_escape_attr(v)}"' for k, v in attrs)


def _render_el(el: El) -> str:
    attrs = _render_attrs(el.attrs)
    if el.tag in VOID_TAGS:
        return f"<{el.tag}{attrs}>"
    if el.tag in CONTAINER_TAGS:
        lines = [f"<{el.tag}{attrs}>"]
        for c in el.children:
            if isinstance(c, El):
                lines.append(_render_el(c))
            else:
                text = _escape_text(c).strip()
                if text:
                    lines.append(text)
        lines.append(f"</{el.tag}>")
        return "\n".join(lines)
    inner = "".join(_render_el(c) if isinstance(c, El) else _escape_text(c) for c in el.children)
    return f"<{el.tag}{attrs}>{inner}</{el.tag}>"


def render(doc: Doc) -> str:
    return "<!DOCTYPE html>\n" + _render_el(doc.root)


# ---------------------------------------------------------------------------
# 4. Injectors, keyed by criterion ID. Each reads its target location from
#    `target.element` (the slot id), per bench/generator/api.py's Target
#    docstring: "element: str | None  # element slot id, html domains".
#    Every injector returns a new Doc, never mutates the one it is given.
# ---------------------------------------------------------------------------

INJECTORS: dict = {}


@injector("WCAG-1.1.1")
def inject_missing_alt(rng, doc, target):
    """Remove a content image's alt attribute entirely, with no
    decorative marking added in its place."""
    slot = target.element
    doc2 = doc.with_attrs(slot, {"alt": None})
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=2,
        description="A content image's alt attribute is removed entirely, with no decorative marking added in its place.",
    )


@injector("WCAG-1.3.1")
def inject_heading_skip(rng, doc, target):
    slot = target.element
    doc2 = doc.with_tag(slot, "h4")
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=2,
        description="A section heading is dropped two levels below the heading immediately before it in document order.",
    )


@injector("WCAG-1.4.3")
def inject_low_text_contrast(rng, doc, target):
    slot = target.element
    doc2 = doc.with_attrs(slot, {"style": "color:#999999"})
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=3,
        description="A paragraph's text color is set to a shade that falls well under the contrast minimum against its background.",
    )


@injector("WCAG-1.4.4")
def inject_viewport_zoom_block(rng, doc, target):
    slot = target.element
    doc2 = doc.with_attrs(slot, {"content": "width=device-width, initial-scale=1, user-scalable=no"})
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=3,
        description="The viewport meta tag gains a directive that disables browser zoom entirely.",
    )


@injector("WCAG-1.4.10")
def inject_fixed_width_reflow(rng, doc, target):
    slot = target.element
    doc2 = doc.with_attrs(slot, {"style": "width:960px"})
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=3,
        description="A page-width element gains a fixed pixel width above the reflow threshold, with no responsive override.",
    )


@injector("WCAG-1.4.11")
def inject_low_component_contrast(rng, doc, target):
    # The border color is chosen to land just under the 3:1 component
    # minimum (roughly 2.7:1 against white), which is the single-control
    # severity-2 anchor in references/WCAG.md. A much darker shortfall
    # would be a correct plant at severity 3, not 2, and would disagree
    # with severity_expected below.
    slot = target.element
    doc2 = doc.with_attrs(slot, {"style": "border:1px solid #9d9d9d"})
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=2,
        description="A secondary button gains a border color with too little contrast against its background.",
    )


@injector("WCAG-1.4.12")
def inject_text_spacing_clip(rng, doc, target):
    slot = target.element
    doc2 = doc.with_attrs(slot, {"style": "height:60px;overflow:hidden"})
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=2,
        description="A status card gains a fixed height paired with clipped overflow around its own text.",
    )


@injector("WCAG-2.4.1", phase="structure")
def inject_missing_bypass_block(rng, doc, target):
    """Downgrade the main landmark to a generic element and remove the
    leading skip link, so neither bypass mechanism survives. Removing the
    skip link element is what makes this a structure-phase injector: it
    deletes a composed unit rather than only rewriting one."""
    body_slot = target.element
    doc2 = doc.with_tag("main", "div")
    doc2 = doc2.remove("body.skiplink")
    return InjectionResult(
        composed=doc2,
        slot=body_slot,
        severity_expected=3,
        description="The page's main landmark is downgraded to a generic element and its leading skip link is removed.",
    )


@injector("WCAG-2.4.2")
def inject_empty_title(rng, doc, target):
    slot = target.element
    doc2 = doc.with_text(slot, "")
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=3,
        description="The page title element is emptied out, leaving the page with no usable title text.",
    )


@injector("WCAG-2.4.4")
def inject_generic_link_text(rng, doc, target):
    slot = target.element
    doc2 = doc.with_text(slot, "click here")
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=2,
        description="A contextual link's text is replaced with a generic phrase that carries no destination information on its own.",
    )


@injector("WCAG-2.5.3")
def inject_label_name_mismatch(rng, doc, target):
    slot = target.element
    doc2 = doc.with_attrs(slot, {"aria-label": "Send form now"})
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=2,
        description="A submit button's accessible name is set to wording that omits its own visible label text.",
    )


@injector("WCAG-3.1.1")
def inject_invalid_lang(rng, doc, target):
    slot = target.element
    doc2 = doc.with_attrs(slot, {"lang": "translanguage"})
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=3,
        description="The page's lang attribute is replaced with a value that is not a well formed language subtag.",
    )


@injector("WCAG-3.3.2")
def inject_broken_label_association(rng, doc, target):
    """The plant targets the control (matching where a correct finding
    would point); the mutation lands on the paired label, one slot over
    by this module's own `<slot>.label` naming convention."""
    control_slot = target.element
    label_slot = f"{control_slot}.label"
    doc2 = doc.with_attrs(label_slot, {"for": "topic-alt"})
    return InjectionResult(
        composed=doc2,
        slot=control_slot,
        severity_expected=2,
        description="A form control's associated label has its for attribute repointed at a different id, breaking the programmatic association.",
    )


# --- Judged-lane injectors (>=3 required; four implemented). -------------


@injector("WCAG-1.3.2", phase="structure")
def inject_meaningless_sequence(rng, doc, target):
    """Scramble the wizard's document order while a CSS order override
    restores the original visual appearance, so a sighted reviewer sees
    nothing wrong while a linearized reading loses the task order. The
    document-order scramble is a genuine reorder of composed units, hence
    structure phase; the CSS values that mask it are a same-call
    attribute rewrite on those same units."""
    wizard_slot = target.element
    doc2 = doc.reorder(wizard_slot, ("s3.step3", "s3.step2", "s3.step1"))
    doc2 = doc2.with_attrs("s3.step1", {"style": "order:1"})
    doc2 = doc2.with_attrs("s3.step2", {"style": "order:2"})
    doc2 = doc2.with_attrs("s3.step3", {"style": "order:3"})
    return InjectionResult(
        composed=doc2,
        slot=wizard_slot,
        severity_expected=3,
        description="A multi-step sequence's document order is scrambled while a CSS order override restores the original visual appearance, so a linearized reading no longer follows the task order a sighted layout still shows.",
    )


@injector("WCAG-1.4.1")
def inject_color_only_required(rng, doc, target):
    slot = target.element
    doc2 = doc.with_text(slot, "Phone number")
    doc2 = doc2.with_attrs(slot, {"style": "color:#cc0000"})
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=2,
        description="A required field's label loses its text indicator and is recolored, leaving color as the only signal that the field is required.",
    )


@injector("WCAG-3.3.1")
def inject_generic_error_text(rng, doc, target):
    slot = target.element
    doc2 = doc.with_text(slot, "Error.")
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=2,
        description="An invalid field's error text is replaced with a generic word that names neither the field nor the specific problem.",
    )


@injector("WCAG-4.1.2")
def inject_unnamed_custom_control(rng, doc, target):
    slot = target.element
    doc2 = doc.with_attrs(slot, {"role": None, "tabindex": None, "aria-label": None})
    return InjectionResult(
        composed=doc2,
        slot=slot,
        severity_expected=3,
        description="A custom interactive control loses its role, its accessible name, and its keyboard handling, leaving only a bare, unlabeled element.",
    )


# ---------------------------------------------------------------------------
# 5. Addressing. Called by the harness after every injection, on the
#    final composition. Every slotted element already carries a
#    content-derived id (assigned at compose time, never renumbered), so
#    every location here is kind "element-id": the exact-match path
#    bench/README.md's html tolerance rule describes as "always available".
# ---------------------------------------------------------------------------

_NOUN_BY_TAG = {
    "img": "image",
    "a": "link",
    "button": "button",
    "input": "field",
    "select": "field",
    "textarea": "field",
    "label": "label",
    "h1": "heading",
    "h2": "heading",
    "h3": "heading",
    "h4": "heading",
    "h5": "heading",
    "h6": "heading",
    "table": "table",
    "title": "page title",
    "meta": "meta tag",
    "html": "page",
    "body": "page body",
    "main": "main region",
    "div": "element",
    "span": "element",
    "p": "paragraph",
    "form": "form",
}


def address(doc: Doc, slot: str, sentence=None) -> Location:
    el = doc.find(slot)
    element_id = dict(el.attrs).get("id", slot.replace(".", "-"))
    noun = _NOUN_BY_TAG.get(el.tag, el.tag)
    return Location(kind="element-id", element_id=element_id, text=f"the {noun}, id `{element_id}`")


# ---------------------------------------------------------------------------
# 6. Recipes. Four artifacts, one of them clean, matching bench/README.md's
#    corpus design table (accessibility: 4 artifacts, 1 clean). Every
#    scripted-lane criterion in checks.py's IMPLEMENTED_CRITERIA (13) plus
#    four judged-lane criteria (>=3 required by S-05) get exactly one
#    planted instance each, spread across the three seeded recipes so
#    every recipe stays readable.
# ---------------------------------------------------------------------------

_SHAPE = {"paragraphs": (2, 1, 2)}

RECIPES = (
    Recipe(
        id="accessibility-001",
        shape=_SHAPE,
        plants=(
            Plant("WCAG-1.1.1", Target(section=1, element="s1.img1"), severity_expected=2),
            Plant("WCAG-1.3.1", Target(section=2, element="s2.h"), severity_expected=2),
            Plant("WCAG-2.4.1", Target(section=0, element="body"), severity_expected=3),
            Plant("WCAG-2.4.2", Target(section=0, element="head.title"), severity_expected=3),
            Plant("WCAG-2.4.4", Target(section=3, element="s3.link1"), severity_expected=2),
            Plant("WCAG-2.5.3", Target(section=3, element="s3.form.submit"), severity_expected=2),
            Plant("WCAG-3.1.1", Target(section=0, element="html"), severity_expected=3),
        ),
    ),
    Recipe(
        id="accessibility-002",
        shape=_SHAPE,
        plants=(
            Plant("WCAG-1.4.3", Target(section=1, element="s1.p1"), severity_expected=3),
            Plant("WCAG-1.4.4", Target(section=0, element="head.viewport"), severity_expected=3),
            Plant("WCAG-1.4.10", Target(section=3, element="s3.banner"), severity_expected=3),
            Plant("WCAG-1.4.11", Target(section=3, element="s3.button1"), severity_expected=2),
            Plant("WCAG-1.4.12", Target(section=3, element="s3.statuscard"), severity_expected=2),
            Plant("WCAG-3.3.2", Target(section=3, element="s3.form.topic"), severity_expected=2),
        ),
    ),
    Recipe(
        id="accessibility-003",
        shape=_SHAPE,
        plants=(
            Plant("WCAG-1.3.2", Target(section=3, element="s3.wizard"), severity_expected=3),
            Plant("WCAG-1.4.1", Target(section=3, element="s3.form.phone.label"), severity_expected=2),
            Plant("WCAG-3.3.1", Target(section=3, element="s3.form.promo.error"), severity_expected=2),
            Plant("WCAG-4.1.2", Target(section=3, element="s3.customcontrol"), severity_expected=3),
        ),
    ),
    Recipe(id="accessibility-004", shape=_SHAPE, plants=()),
)

DOMAIN = Domain(
    name="accessibility",
    artifact_type="html",
    extension=".html",
    namespaces=("WCAG",),
    compose=compose,
    render=render,
    address=address,
    injectors=INJECTORS,
    recipes=RECIPES,
)
