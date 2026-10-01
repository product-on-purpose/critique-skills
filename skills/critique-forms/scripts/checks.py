"""critique-forms scripted lane: the 18 FORMS criteria in SKILL.md's
checks.scripted, against `references/FORMS.md`'s own Operational test
column for each. See docs/internal/skill-template.md, "Wiring
scripts/checks.py", for the pattern this file follows.

What this file reads (the artifact claim is "markup and declared CSS as
text", never a rendered page, per SKILL.md and references/FORMS.md,
"Artifact and reach"):

  - The HTML tree, through html.parser, assuming well-formed markup. It
    does not implement HTML5's tag-soup recovery rules.
  - Declared CSS for two criteria only. FORMS-INPUT-FONT-SIZE reads a
    control's own `font-size`, and FORMS-FIELD-WIDTH reads a control's own
    `width` in `ch` units. Both come from the control's inline `style`
    attribute, or from a `<style>` block rule whose selector is a
    combinator-free compound of tag, class and id (`input`, `.field`,
    `#email`, `input.field`), resolved by specificity then source order.
    `@media` and every other at-rule are ignored, so the size read is the
    unconditional declared size, and an external stylesheet is never
    fetched. A control the artifact declares nothing for reports nothing.

How a field's purpose is read is stated once, in references/FORMS.md,
"How a field's purpose is read", and implemented once here, in
`_purpose` and `_has_cue`. Twelve checks depend on it.

Severity policy: each check's split is the one its operational test
states, and references/severity-anchors.md, "Thresholds the scripted
lane applies", restates every one of them. Recurrence uses
`_severity_for_count`, the same rule critique-accessibility applies.

Location emission follows critique-accessibility's (ADR 0027): an
element's `#id` first, a bounded CSS path in double quotes otherwise, a
descriptor, and a line number last as a human convenience.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills._shared.runner import run_scripted_lane
from skills._shared.findings import RawFinding

# Every criterion this scripted lane checks. Cross-checked against
# SKILL.md's checks.scripted by scripts/skill-selftest.py; the two must
# name exactly the same set.
IMPLEMENTED_CRITERIA = frozenset({
    "FORMS-ACTION-LABEL",
    "FORMS-ADDRESS-FORMAT",
    "FORMS-AUTOCOMPLETE",
    "FORMS-AUTOCORRECT",
    "FORMS-CONFIRM-PASSWORD",
    "FORMS-DATE-SELECTS",
    "FORMS-FIELD-WIDTH",
    "FORMS-FORMAT-TOLERANCE",
    "FORMS-INPUT-FONT-SIZE",
    "FORMS-INPUT-TYPE",
    "FORMS-NUMERIC-INPUTMODE",
    "FORMS-OPTION-CONTROL",
    "FORMS-PASSWORD-RULES",
    "FORMS-PHONE-REASON",
    "FORMS-PLACEHOLDER-INSTRUCTION",
    "FORMS-REQUIRED-OPTIONAL",
    "FORMS-RESET-BUTTON",
    "FORMS-SPLIT-ENTITY",
})

# ---------------------------------------------------------------------------
# The HTML tree
# ---------------------------------------------------------------------------

VOID_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})

# Descendants whose text is not part of an element's own label text.
_NON_LABEL_TEXT_TAGS = frozenset({"select", "option", "textarea", "script", "style", "template"})


class Node:
    """One element, or the synthetic '#root' wrapper. `raw` is the exact
    source text of the opening tag, so evidence quotes the artifact."""

    def __init__(self, tag, attrs, line, parent=None, raw=""):
        self.tag = tag
        self.attrs = attrs
        self.line = line
        self.parent = parent
        self.raw = raw
        self.children = []

    def text_content(self, skip=frozenset()):
        parts = []

        def walk(n):
            for c in n.children:
                if isinstance(c, str):
                    parts.append(c)
                elif c.tag not in skip:
                    walk(c)

        walk(self)
        return "".join(parts)

    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.iter()

    def element_children(self):
        return [c for c in self.children if isinstance(c, Node)]


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, 1)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attr_dict = {}
        for key, value in attrs:
            attr_dict[key.lower()] = value if value is not None else ""
        line, _col = self.getpos()
        raw = self.get_starttag_text() or f"<{tag}>"
        node = Node(tag, attr_dict, line, parent=self.stack[-1], raw=raw)
        self.stack[-1].children.append(node)
        if tag not in VOID_ELEMENTS:
            self.stack.append(node)

    def handle_endtag(self, tag):
        tag = tag.lower()
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def _parse_html(text):
    builder = _TreeBuilder()
    builder.feed(text)
    builder.close()
    return builder.root


# ---------------------------------------------------------------------------
# Declared CSS, for FORMS-INPUT-FONT-SIZE and FORMS-FIELD-WIDTH only
# ---------------------------------------------------------------------------

_CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
_SIMPLE_SELECTOR_TOKEN_RE = re.compile(r"\*|[A-Za-z][A-Za-z0-9]*|\.[A-Za-z_-][\w-]*|#[A-Za-z_-][\w-]*")


def _strip_at_rules(text):
    """Removes every `@rule { ... }` or `@rule ...;`, with brace nesting,
    so the remainder splits on '}' into flat, unconditional rules."""
    out = []
    i, n = 0, len(text)
    while i < n:
        if text[i] == "@":
            brace_pos = text.find("{", i)
            semi_pos = text.find(";", i)
            if brace_pos == -1 and semi_pos == -1:
                break
            if semi_pos != -1 and (brace_pos == -1 or semi_pos < brace_pos):
                i = semi_pos + 1
                continue
            depth, j = 1, brace_pos + 1
            while j < n and depth > 0:
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                j += 1
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _parse_declarations(text):
    decls = {}
    for item in (text or "").split(";"):
        if ":" not in item:
            continue
        prop, _, value = item.partition(":")
        prop, value = prop.strip().lower(), value.strip()
        if prop and value:
            decls[prop] = value
    return decls


def _compound_tokens(selector):
    selector = selector.strip()
    if not selector or any(ch in selector for ch in " \t\n>+~[:"):
        return None
    tokens = _SIMPLE_SELECTOR_TOKEN_RE.findall(selector)
    return tokens if "".join(tokens) == selector else None


def _selector_matches(tokens, node):
    for tok in tokens:
        if tok == "*":
            continue
        if tok.startswith("#"):
            if node.attrs.get("id") != tok[1:]:
                return False
        elif tok.startswith("."):
            if tok[1:] not in (node.attrs.get("class") or "").split():
                return False
        elif node.tag != tok.lower():
            return False
    return True


def _build_stylesheet(tree):
    """(specificity, source order, tokens, declarations, selector text) for
    every compound-selector rule in every <style> block."""
    rules, order = [], 0
    for node in tree.iter():
        if node.tag != "style":
            continue
        css = _strip_at_rules(_CSS_COMMENT_RE.sub("", node.text_content()))
        for chunk in css.split("}"):
            if "{" not in chunk:
                continue
            sel_part, decl_part = chunk.split("{", 1)
            decls = _parse_declarations(decl_part)
            for sel in (s.strip() for s in sel_part.split(",")):
                tokens = _compound_tokens(sel)
                if tokens is None or not decls:
                    continue
                spec = (
                    sum(1 for t in tokens if t.startswith("#")),
                    sum(1 for t in tokens if t.startswith(".")),
                    sum(1 for t in tokens if t != "*" and not t.startswith(("#", "."))),
                )
                rules.append((spec, order, tokens, decls, sel))
                order += 1
    return rules


def _declared(node, prop, rules):
    """(value, source) for `prop` as this element itself declares it: the
    inline style wins, then the most specific matching rule, later rules
    winning ties. (None, None) when nothing declares it."""
    inline = _parse_declarations(node.attrs.get("style") or "")
    if prop in inline:
        return inline[prop], "its inline style"
    best = None
    for spec, order, tokens, decls, sel in rules:
        if prop in decls and _selector_matches(tokens, node):
            if best is None or (spec, order) >= (best[0], best[1]):
                best = (spec, order, decls[prop], sel)
    if best is None:
        return None, None
    return best[2], f"the rule {best[3]}"


_LENGTH_RE = re.compile(r"^(-?\d+(?:\.\d+)?|-?\.\d+)\s*(px|pt|em|rem|ch)?$")


def _parse_length(value):
    if value is None:
        return None
    v = re.sub(r"\s*!important\s*$", "", value.strip().lower())
    m = _LENGTH_RE.match(v)
    if not m:
        return None
    return float(m.group(1)), (m.group(2) or "px")


def _font_size_px(value):
    """A declared font size in pixels, counting em and rem at 16 pixels
    each, as references/FORMS.md states; None for any other unit or form."""
    length = _parse_length(value)
    if length is None:
        return None
    num, unit = length
    if unit == "px":
        return num
    if unit == "pt":
        return num * 4.0 / 3.0
    if unit in ("em", "rem"):
        return num * 16.0
    return None


# ---------------------------------------------------------------------------
# Text, locations and small helpers
# ---------------------------------------------------------------------------

_DASHES = str.maketrans({"\u2013": "-", "\u2014": "-"})
_MAX_LOCATION_CHARS = 400
_BARE_ID_RE = re.compile(r"[A-Za-z][\w-]*")


def _clean(s):
    """Whitespace collapsed, en and em dashes made plain hyphens: the
    contract's prose fields allow neither dash, and evidence quotes the
    artifact, which might contain one."""
    return " ".join((s or "").translate(_DASHES).split())


def _truncate(s, n=300):
    s = _clean(s)
    return s if len(s) <= n else s[: n - 3] + "..."


def _quoteless(s, n=60):
    """Label text made safe to embed in a location descriptor: double
    quotes would read as a selector in the html location grammar."""
    return _truncate(s, n).replace('"', "'")


def _css_path_parts(node):
    parts, cur = [], node
    while cur is not None and cur.tag != "#root":
        parent = cur.parent
        siblings = [c for c in parent.children if isinstance(c, Node) and c.tag == cur.tag] if parent else []
        parts.append(f"{cur.tag}:nth-of-type({siblings.index(cur) + 1})" if len(siblings) > 1 else cur.tag)
        cur = parent
    parts.reverse()
    return parts


def _element_anchor(node):
    element_id = (node.attrs.get("id") or "").strip()
    if element_id and _BARE_ID_RE.fullmatch(element_id):
        return f"#{element_id}"
    parts = _css_path_parts(node)
    if element_id:
        last = f"{node.tag}#{element_id}"
        parts = parts[:-1] + [last] if parts else [last]
    return '"' + " > ".join(parts or [node.tag]) + '"'


def _loc(node, descriptor):
    anchor = _element_anchor(node)
    tail = f", {descriptor}, line {node.line}"
    budget = _MAX_LOCATION_CHARS - len(anchor)
    if len(tail) > budget:
        tail = tail[: max(0, budget - 3)].rstrip() + "..."
    return (anchor + tail).translate(_DASHES)[:_MAX_LOCATION_CHARS]


def _attr(node, name):
    return (node.attrs.get(name) or "").strip()


def _attr_lower(node, name):
    return _attr(node, name).lower()


def _is_hidden(node):
    n = node
    while n is not None:
        if "hidden" in n.attrs or _attr_lower(n, "aria-hidden") == "true":
            return True
        inline = _parse_declarations(n.attrs.get("style") or "")
        if (inline.get("display") or "").strip().lower() == "none":
            return True
        if (inline.get("visibility") or "").strip().lower() == "hidden":
            return True
        n = n.parent
    return False


def _severity_for_count(count):
    """One instance in the form is severity 2; two or more make every
    instance severity 3 (references/severity-anchors.md, recurrence)."""
    return 3 if count >= 2 else 2


def _int_attr(node, name):
    value = _attr(node, name)
    return int(value) if re.fullmatch(r"\d+", value) else None


# ---------------------------------------------------------------------------
# Forms, controls and labels
# ---------------------------------------------------------------------------

# Input types a person types into, for the checks that concern typing.
TEXT_LIKE_TYPES = frozenset({"text", "email", "tel", "url", "search", "number", "password"})
NON_FIELD_INPUT_TYPES = frozenset({"hidden", "submit", "reset", "button", "image"})


def _input_type(node):
    return _attr_lower(node, "type") or "text"


def _is_text_like(node):
    if node.tag == "textarea":
        return True
    return node.tag == "input" and _input_type(node) in TEXT_LIKE_TYPES


class Form:
    """One <form>, or the artifact itself when its controls sit in no
    form, with its visible controls in document order."""

    def __init__(self, node):
        self.node = node
        self.controls = []

    def fields(self):
        """Controls a person fills in: text-like inputs, selects and
        textareas. Checkboxes, radios and buttons are not fields here."""
        return [c for c in self.controls if c.tag in ("select", "textarea") or (c.tag == "input" and _is_text_like(c))]

    def buttons(self):
        return [
            c for c in self.controls
            if c.tag == "button" or (c.tag == "input" and _input_type(c) in ("submit", "reset", "button", "image"))
        ]

    def primary_submit(self):
        for c in self.buttons():
            kind = _attr_lower(c, "type")
            if (c.tag == "button" and kind in ("", "submit")) or (c.tag == "input" and kind == "submit"):
                return c
        return None


def _nearest(node, tag):
    n = node.parent
    while n is not None:
        if n.tag == tag:
            return n
        n = n.parent
    return None


def _collect_forms(tree):
    forms, loose = {}, Form(tree)
    order = []
    for node in tree.iter():
        if node.tag not in ("input", "select", "textarea", "button"):
            continue
        if node.tag == "input" and _input_type(node) == "hidden":
            continue
        if "disabled" in node.attrs or _is_hidden(node):
            continue
        form_node = _nearest(node, "form")
        if form_node is None:
            if loose not in order:
                order.append(loose)
            loose.controls.append(node)
            continue
        if id(form_node) not in forms:
            forms[id(form_node)] = Form(form_node)
            order.append(forms[id(form_node)])
        forms[id(form_node)].controls.append(node)
    return order


class Labels:
    """Label text per control: the <label for> matching its id, or the
    <label> that wraps it, without the text of any nested control."""

    def __init__(self, tree):
        self.by_for = {}
        self.by_id = {}
        for node in tree.iter():
            node_id = node.attrs.get("id")
            if node_id and node_id not in self.by_id:
                self.by_id[node_id] = node
            if node.tag == "label" and node.attrs.get("for"):
                self.by_for.setdefault(node.attrs["for"], node)

    def label_node(self, control):
        control_id = control.attrs.get("id")
        if control_id and control_id in self.by_for:
            return self.by_for[control_id]
        return _nearest(control, "label")

    def text(self, control):
        label = self.label_node(control)
        return _clean(label.text_content(_NON_LABEL_TEXT_TAGS)) if label is not None else ""

    def has_label(self, control):
        """A label of any kind WCAG-3.3.2 accepts. A field with none is
        that criterion's ground, never this skill's."""
        if self.label_node(control) is not None:
            return True
        if _attr(control, "aria-label") or _attr(control, "title"):
            return True
        return any(ref in self.by_id for ref in _attr(control, "aria-labelledby").split())

    def described_text(self, control):
        refs = _attr(control, "aria-describedby").split() + _attr(control, "aria-labelledby").split()
        return _clean(" ".join(self.by_id[r].text_content() for r in refs if r in self.by_id))


# ---------------------------------------------------------------------------
# Purpose inference: references/FORMS.md, "How a field's purpose is read"
# ---------------------------------------------------------------------------


def _words(text):
    """Lower-case words, split at case changes, digits and anything that
    is not a letter or digit (hyphens, underscores, punctuation, spaces)."""
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text or "")
    text = re.sub(r"([A-Za-z])(\d)|(\d)([A-Za-z])", lambda m: " ".join(g for g in m.groups() if g), text)
    return re.sub(r"[^A-Za-z0-9]+", " ", text).lower().split()


def _matches(cue, words):
    """A cue matches as a whole-word run, or with its spaces removed as one
    word, so firstname reads as first name and zipcode as zip code."""
    cue_words = _words(cue)
    n = len(cue_words)
    if any(words[i:i + n] == cue_words for i in range(len(words) - n + 1)):
        return True
    return n > 1 and "".join(cue_words) in words


# references/FORMS.md's cue table, in its precedence order: where two
# purposes match one signal, the earlier wins.
BIRTH_CUES = ("birth", "date of birth", "dob", "born", "birthday")
PURPOSE_CUES = (
    ("house number", ("house number", "street number", "building number", "house no")),
    ("postal code", ("postcode", "post code", "postal code", "zip", "zip code")),
    ("one-time code", ("one-time code", "verification code", "security code", "otp", "passcode")),
    ("account number", ("account number", "reference number", "membership number", "customer number", "policy number")),
    ("birth date", BIRTH_CUES),
    ("email", ("email", "e-mail", "email address")),
    ("phone", ("phone", "telephone", "tel", "mobile", "cell", "phone number", "mobile number", "telephone number")),
    ("web address", ("website", "url", "homepage", "web address")),
    ("search", ("search", "query", "q")),
    ("username", ("username", "user name", "login", "user id")),
    ("street address", ("address", "street", "address line")),
    ("city", ("city", "town")),
    ("county", ("county",)),
    ("region", ("state", "province", "region")),
    ("country", ("country",)),
    ("date part", ("day", "month", "year")),
    ("quantity", ("quantity", "qty", "amount", "number of", "count", "age")),
    ("name", ("first name", "last name", "surname", "given name", "family name", "full name", "forename", "middle name", "your name")),
)

# Words a label carries to mark its field, not to name its purpose.
MARKER_WORDS = frozenset({"required", "optional", "mandatory"})

TOKEN_PURPOSE = {
    "name": "name", "honorific-prefix": "name", "given-name": "name", "additional-name": "name",
    "family-name": "name", "honorific-suffix": "name", "nickname": "name",
    "email": "email", "url": "web address", "username": "username",
    "new-password": "new password", "current-password": "current password",
    "one-time-code": "one-time code",
    "street-address": "street address", "address-line1": "street address",
    "address-line2": "street address", "address-line3": "street address",
    "address-level2": "city", "address-level1": "region",
    "country": "country", "country-name": "country", "postal-code": "postal code",
    "bday": "birth date", "bday-day": "birth date", "bday-month": "birth date", "bday-year": "birth date",
}
for _tel in ("tel", "tel-country-code", "tel-national", "tel-area-code", "tel-local",
             "tel-local-prefix", "tel-local-suffix", "tel-extension"):
    TOKEN_PURPOSE[_tel] = "phone"

TYPE_PURPOSE = {"email": "email", "tel": "phone", "url": "web address", "search": "search"}

NEW_PASSWORD_CUES = ("new", "create", "choose", "set", "register")
CONFIRM_CUES = ("confirm", "repeat", "re-enter", "retype", "again", "verify")


def _purpose_of_words(words):
    for purpose, cues in PURPOSE_CUES:
        if any(_matches(cue, words) for cue in cues):
            return purpose
    if words == ["name"]:
        # The bare word names a person only when it is the whole signal,
        # so Company name or Event name never reads as a person's name.
        return "name"
    return None


def _signal_words(control, labels):
    """Signals 3 and 4: the name and id words, then the label words without
    the words that only mark a field required or optional."""
    return (
        _words(_attr(control, "name")) + _words(_attr(control, "id")),
        [w for w in _words(labels.text(control)) if w not in MARKER_WORDS],
    )


def _has_cue(control, labels, cues):
    """Whether any of `cues` appears in the control's name, id or label."""
    name_id_words, label_words = _signal_words(control, labels)
    return any(_matches(cue, words) for cue in cues for words in (name_id_words, label_words))


def _field_name_token(value):
    """The autofill field name of a valid detail value, else None."""
    return _parse_autofill((value or "").lower().split())


def _purpose(control, labels, form=None):
    """The one purpose references/FORMS.md's four signals give this
    control, or None. Password fields resolve to new or current. A
    textarea holds several lines, and a street address is the only
    multi-line purpose, so a textarea has that purpose or none, and a
    question such as State your reason never reads as a region."""
    purpose = _single_line_purpose(control, labels, form)
    if control.tag == "textarea" and purpose != "street address":
        return None
    return purpose


def _single_line_purpose(control, labels, form):
    token = _field_name_token(_attr(control, "autocomplete"))
    if token in TOKEN_PURPOSE:
        return TOKEN_PURPOSE[token]
    if control.tag == "input":
        kind = _input_type(control)
        if kind == "password":
            if _has_cue(control, labels, NEW_PASSWORD_CUES):
                return "new password"
            if form is not None and _followed_by_confirm(control, form, labels):
                return "new password"
            return "current password"
        if kind in TYPE_PURPOSE:
            return TYPE_PURPOSE[kind]
    name_id_words, label_words = _signal_words(control, labels)
    return _purpose_of_words(name_id_words) or _purpose_of_words(label_words)


def _password_fields(form):
    return [c for c in form.controls if c.tag == "input" and _input_type(c) == "password"]


def _is_confirm(control, labels):
    return _has_cue(control, labels, CONFIRM_CUES)


def _followed_by_confirm(control, form, labels):
    fields = _password_fields(form)
    if control not in fields:
        return False
    later = fields[fields.index(control) + 1:]
    return bool(later) and _is_confirm(later[0], labels)


# ---------------------------------------------------------------------------
# The HTML standard's autofill grammar (whatwg-html-autofill, 4.10.18.7)
# ---------------------------------------------------------------------------

AUTOFILL_FIELD_NAMES = frozenset({
    "name", "honorific-prefix", "given-name", "additional-name", "family-name",
    "honorific-suffix", "nickname", "organization-title", "username", "new-password",
    "current-password", "one-time-code", "organization", "street-address",
    "address-line1", "address-line2", "address-line3", "address-level4",
    "address-level3", "address-level2", "address-level1", "country", "country-name",
    "postal-code", "cc-name", "cc-given-name", "cc-additional-name", "cc-family-name",
    "cc-number", "cc-exp", "cc-exp-month", "cc-exp-year", "cc-csc", "cc-type",
    "transaction-currency", "transaction-amount", "language", "bday", "bday-day",
    "bday-month", "bday-year", "sex", "url", "photo",
})
AUTOFILL_CONTACT_FIELD_NAMES = frozenset({
    "tel", "tel-country-code", "tel-national", "tel-area-code", "tel-local",
    "tel-local-prefix", "tel-local-suffix", "tel-extension", "email", "impp",
})
AUTOFILL_CONTACT_TYPES = frozenset({"home", "work", "mobile", "fax", "pager"})


def _parse_autofill(tokens):
    """The field name of a valid autofill detail value, or None when the
    tokens are not one: [section-*] [shipping|billing] [contact type before
    a contact field name] field-name [webauthn], case-insensitively."""
    i, n = 0, len(tokens)
    if i < n and tokens[i].startswith("section-"):
        i += 1
    if i < n and tokens[i] in ("shipping", "billing"):
        i += 1
    if i < n and tokens[i] in AUTOFILL_CONTACT_TYPES:
        i += 1
        if i >= n or tokens[i] not in AUTOFILL_CONTACT_FIELD_NAMES:
            return None
    elif i >= n or tokens[i] not in (AUTOFILL_FIELD_NAMES | AUTOFILL_CONTACT_FIELD_NAMES):
        return None
    field_name = tokens[i]
    i += 1
    if i < n and tokens[i] == "webauthn":
        i += 1
    return field_name if i == n else None


# ---------------------------------------------------------------------------
# Finding construction
# ---------------------------------------------------------------------------


def _is_button(control):
    return control.tag == "button" or (control.tag == "input" and _input_type(control) in ("submit", "reset", "button", "image"))


def _descriptor(control, labels):
    """What kind of control this is, and the words a reader finds it by:
    its label, or its name when it has no label."""
    if _is_button(control):
        text = _button_label(control)
        return f"<{control.tag}> button, text '{_quoteless(text)}'" if text else f"<{control.tag}> button"
    label = labels.text(control) or _clean(_attr(control, "aria-label"))
    if label:
        return f"<{control.tag}> field, label '{_quoteless(label)}'"
    name = _attr(control, "name")
    return f"<{control.tag}> field, name '{_quoteless(name)}'" if name else f"<{control.tag}> field"


def _finding(criterion, severity, control, labels, violation, fix, evidence=None):
    return RawFinding(
        criterion=criterion,
        severity=severity,
        location=_loc(control, _descriptor(control, labels)),
        evidence=_truncate(evidence if evidence is not None else control.raw),
        violation=_clean(violation),
        fix=_clean(fix),
    )


def _occurrence_findings(criterion, severity, controls, labels, violation, fix, evidence=None):
    """One breach that appears at several controls, the first being the
    representative. The contract's instance list needs at least two
    entries, so two occurrences become two findings and three or more
    become one finding listing the rest as instances, the same rule
    critique-usability's _findings_from_occurrences applies."""
    if len(controls) <= 2:
        return [_finding(criterion, severity, c, labels, violation, fix, evidence) for c in controls]
    first, rest = controls[0], controls[1:]
    return [RawFinding(
        criterion=criterion,
        severity=severity,
        location=_loc(first, _descriptor(first, labels)),
        evidence=_truncate(evidence if evidence is not None else first.raw),
        violation=_clean(violation),
        fix=_clean(fix),
        instances=tuple({"location": _loc(c, _descriptor(c, labels)), "evidence": _truncate(c.raw)} for c in rest),
    )]


# ---------------------------------------------------------------------------
# The 18 checks, in ID order
# ---------------------------------------------------------------------------

GENERIC_SUBMIT_WORDS = frozenset({"submit", "send", "ok", "go", "enter"})


def _visible_button_text(button):
    if button.tag == "input":
        return _clean(_attr(button, "value"))
    return _clean(button.text_content())


def _button_label(button):
    return _visible_button_text(button) or _clean(_attr(button, "aria-label"))


def _bare_word(text):
    """The text without surrounding punctuation or inner dots, lower-cased,
    so Submit, SUBMIT! and O.K. compare as submit and ok."""
    core = re.sub(r"^[\W_]+|[\W_]+$", "", text or "")
    return core.lower().replace(".", "")


def _check_action_label(form, labels):
    submit = form.primary_submit()
    if submit is None:
        return []
    label = _button_label(submit)
    if _bare_word(label) not in GENERIC_SUBMIT_WORDS:
        return []
    return [_finding(
        "FORMS-ACTION-LABEL", 2, submit, labels,
        f"The form's primary button is labelled {label}, a generic word that says nothing about what pressing it does.",
        "Label the button with the action it performs, such as Create account or Send message.",
    )]


def _check_address_format(form, labels):
    fields = form.fields()
    purposes = {id(c): _purpose(c, labels, form) for c in fields}
    has_street = any(p == "street address" for p in purposes.values())
    findings = []
    for c in fields:
        purpose = purposes[id(c)]
        required = _is_required(c)
        if purpose == "house number" and has_street:
            findings.append(_finding(
                "FORMS-ADDRESS-FORMAT", 3 if required else 2, c, labels,
                "The house number has its own field separate from the street"
                + (", and it is required, so an address with no number cannot be entered." if required else ", which splits one address line in two."),
                "Collect the house number and street together in one address-line field.",
            ))
        elif purpose == "county" and required:
            findings.append(_finding(
                "FORMS-ADDRESS-FORMAT", 2, c, labels,
                "A county is required, though postal delivery does not need one, so a person without one must invent a value.",
                "Make the county field optional, or remove it.",
            ))
    return findings


AUTOCOMPLETE_PURPOSES = frozenset({
    "name", "email", "phone", "username", "new password", "current password",
    "street address", "postal code", "city", "county", "region", "country", "birth date",
})
OFF_IS_SEVERE = frozenset({
    "username", "new password", "current password",
    "street address", "postal code", "city", "county", "region", "country",
})


def _check_autocomplete(form, labels):
    form_off = form.node.tag == "form" and _attr_lower(form.node, "autocomplete") == "off"
    findings = []
    for c in form.fields():
        purpose = _purpose(c, labels, form)
        if purpose not in AUTOCOMPLETE_PURPOSES:
            continue
        value = _attr_lower(c, "autocomplete")
        if not value and form_off:
            value = "off"
        if value in ("", "on"):
            findings.append(_finding(
                "FORMS-AUTOCOMPLETE", 2, c, labels,
                f"This {purpose} field carries no autofill token, so the browser must guess what it holds and may not fill it.",
                "Add the autocomplete token the HTML standard defines for this field, for example "
                + _suggested_token(purpose, c, labels) + ".",
            ))
        elif value == "off":
            severe = purpose in OFF_IS_SEVERE
            findings.append(_finding(
                "FORMS-AUTOCOMPLETE", 3 if severe else 2, c, labels,
                f"Autofill is switched off on this {purpose} field, data a person enters often and a browser could fill.",
                "Remove autocomplete=off and give the field its standard autofill token.",
            ))
        elif _parse_autofill(value.split()) is None:
            findings.append(_finding(
                "FORMS-AUTOCOMPLETE", 3, c, labels,
                f"The autocomplete value {value} is not a valid autofill detail in the HTML standard, so autofill is broken for this field.",
                "Replace it with the standard token for this field, for example " + _suggested_token(purpose, c, labels) + ".",
            ))
    return findings


def _suggested_token(purpose, control=None, labels=None):
    if purpose == "birth date" and control is not None:
        unit = _date_unit(control, labels)
        if unit:
            return f"bday-{unit}"
    return {
        "name": "name, given-name or family-name", "email": "email", "phone": "tel",
        "username": "username", "new password": "new-password", "current password": "current-password",
        "street address": "street-address or address-line1", "postal code": "postal-code",
        "city": "address-level2", "county": "address-level2 or address-level1",
        "region": "address-level1", "country": "country or country-name", "birth date": "bday",
    }.get(purpose, "the matching field name")


AUTOCORRECT_PURPOSES = frozenset({"name", "email", "username", "street address"})


def _check_autocorrect(form, labels):
    flagged = []
    for c in form.fields():
        if c.tag != "input" or _input_type(c) != "text":
            continue
        purpose = _purpose(c, labels, form)
        if purpose not in AUTOCORRECT_PURPOSES:
            continue
        correction_off = _attr_lower(c, "autocorrect") == "off" or _attr_lower(c, "spellcheck") == "false"
        caps_off = _attr_lower(c, "autocapitalize") in ("none", "off")
        problems = []
        if not correction_off:
            problems.append("autocorrection and spellchecking stay on")
        if purpose in ("email", "username") and not caps_off:
            problems.append("auto-capitalization stays on")
        if problems:
            flagged.append((c, purpose, problems))
    severity = _severity_for_count(len(flagged))
    return [
        _finding(
            "FORMS-AUTOCORRECT", severity, c, labels,
            f"On this {purpose} field, " + " and ".join(problems) + ", so a phone keyboard can change a value it does not know.",
            "Add autocorrect=off and spellcheck=false"
            + (", and autocapitalize=none" if purpose in ("email", "username") else "") + ".",
        )
        for c, purpose, problems in flagged
    ]


def _check_confirm_password(form, labels):
    fields = _password_fields(form)
    findings = []
    for earlier, later in zip(fields, fields[1:]):
        both_new = _attr_lower(earlier, "autocomplete") == "new-password" and _attr_lower(later, "autocomplete") == "new-password"
        if _is_confirm(later, labels) or both_new:
            findings.append(_finding(
                "FORMS-CONFIRM-PASSWORD", 2, later, labels,
                "The form asks for the new password a second time to confirm it, doubling the typing for every person.",
                "Remove the confirmation field and offer a control that shows the password as typed.",
            ))
    return findings


def _is_real_option(option):
    """An option a person can choose: not disabled, and not the empty-valued
    prompt such as Please select. An option with no value attribute takes
    its text as its value."""
    if "disabled" in option.attrs:
        return False
    if "value" in option.attrs:
        return _attr(option, "value") != ""
    return bool(_clean(option.text_content()))


def _real_options(select):
    return [o for o in select.iter() if o.tag == "option" and _is_real_option(o)]


DATE_UNIT_TOKENS = {"bday-day": "day", "bday-month": "month", "bday-year": "year"}


def _date_unit(control, labels):
    """day, month or year when the control's token or cues name one."""
    token_unit = DATE_UNIT_TOKENS.get(_field_name_token(_attr(control, "autocomplete")))
    if token_unit:
        return token_unit
    return next((unit for unit in ("day", "month", "year") if _has_cue(control, labels, (unit,))), None)


def _legend_text(control):
    fieldset = _nearest(control, "fieldset")
    if fieldset is None:
        return ""
    legend = next((n for n in fieldset.iter() if n.tag == "legend"), None)
    return _clean(legend.text_content()) if legend is not None else ""


def _check_date_selects(form, labels):
    part = {}
    for s in (c for c in form.controls if c.tag == "select"):
        unit = _date_unit(s, labels)
        if unit and unit not in part:
            part[unit] = s
    if len(part) < 3:
        return []
    trio = sorted(part.values(), key=lambda s: s.line)
    legend_words = _words(_legend_text(trio[0]))
    is_birth = (
        any(_has_cue(s, labels, BIRTH_CUES) or _field_name_token(_attr(s, "autocomplete")) in DATE_UNIT_TOKENS for s in trio)
        or any(_matches(cue, legend_words) for cue in BIRTH_CUES)
    )
    year_options = len(_real_options(part["year"]))
    if not is_birth and year_options <= 30:
        return []
    severity = 3 if year_options > 30 else 2
    return [_finding(
        "FORMS-DATE-SELECTS", severity, trio[0], labels,
        f"A date the person knows by heart is picked from three drop-downs, the year from {year_options} options.",
        "Use three short text fields for day, month and year, with the numeric input mode.",
        evidence=" ".join(s.raw for s in trio),
    )]


FIELD_WIDTH_NARROW = {"email": 20, "phone": 10, "city": 13, "postal code": 5, "one-time code": 4}
FIELD_WIDTH_WIDE = {"postal code": 24, "one-time code": 24, "year": 12, "day": 6, "month": 6}


def _declared_width_chars(control, rules):
    size = _int_attr(control, "size")
    if size is not None:
        return size, f"size={size}"
    value, source = _declared(control, "width", rules)
    length = _parse_length(value)
    if length is not None and length[1] == "ch":
        return length[0], f"width: {value} declared by {source}"
    return None, None


def _check_field_width(form, labels, rules):
    findings = []
    for c in form.fields():
        if c.tag != "input":
            continue
        width, evidence = _declared_width_chars(c, rules)
        if width is None:
            continue
        purpose = _purpose(c, labels, form)
        maxlength = _int_attr(c, "maxlength")
        narrow = FIELD_WIDTH_NARROW.get(purpose)
        if narrow is not None and width < narrow and not (maxlength is not None and maxlength <= width):
            findings.append(_finding(
                "FORMS-FIELD-WIDTH", 3, c, labels,
                f"This {purpose} field shows {width:g} characters, too few to show a typical value whole while it is typed and checked.",
                f"Size the field to show at least {narrow} characters.",
                evidence=f"{c.raw} ({evidence})",
            ))
            continue
        wide_key = purpose if purpose in FIELD_WIDTH_WIDE else _date_unit(c, labels)
        wide = FIELD_WIDTH_WIDE.get(wide_key)
        if wide is not None and width > wide:
            findings.append(_finding(
                "FORMS-FIELD-WIDTH", 2, c, labels,
                f"This {wide_key} field is {width:g} characters wide, far wider than its value, so its width suggests a longer answer.",
                "Size the field to the length of the value it holds.",
                evidence=f"{c.raw} ({evidence})",
            ))
    return findings


PHONE_SAMPLES = ("+44 20 7946 0958", "020 7946 0958", "020-7946-0958", "(020) 7946 0958")
NAME_SAMPLES = ("Zo\u00eb Lee", "Jos\u00e9 Garc\u00eda", "Nguy\u1ec5n V\u0103n An", "\u738b\u5c0f\u660e", "Anne-Marie O'Brien")
POSTCODE_SAMPLES = ("SW1A 1AA", "K1A 0B1", "1012 AB")


# Characters the browser's v-flag syntax, which the HTML standard compiles
# every pattern attribute with, forbids unescaped inside a character class,
# and the punctuators it forbids doubled there.
_V_CLASS_SYNTAX = frozenset("(){}/|")
_V_CLASS_DOUBLED = frozenset("&!#$%*+,.:;<=>?@^`~")


def _v_mode_rejects(pattern):
    """Whether a character class in the pattern uses syntax the v flag
    rejects, such as an unescaped hyphen at a class edge ([A-Za-z-]). A
    browser ignores a pattern it cannot compile, so such a pattern rejects
    nothing and is not judged. Conservative: a construct this scan cannot
    place counts as rejected, which costs a miss, never a false alarm."""
    i, n, in_class, prev = 0, len(pattern), 0, None
    while i < n:
        ch = pattern[i]
        if ch == "\\":
            i += 2
            prev = "char"
            continue
        if not in_class:
            if ch == "[":
                in_class, prev = 1, "open"
                if i + 1 < n and pattern[i + 1] == "^":
                    i += 1
            i += 1
            continue
        if ch == "[":
            in_class += 1
            prev = "open"
        elif ch == "]":
            in_class -= 1
            prev = "char"
        elif ch in _V_CLASS_SYNTAX:
            return True
        elif ch == "-":
            nxt = pattern[i + 1] if i + 1 < n else ""
            if prev != "char" or nxt in ("]", "-", ""):
                return True
            prev = "range"
        elif ch in _V_CLASS_DOUBLED and i + 1 < n and pattern[i + 1] == ch:
            return True
        else:
            prev = "char" if prev != "range" else "range-end"
        i += 1
    return in_class != 0


def _pattern_rejects(pattern, samples):
    """The samples the pattern rejects, matched against the whole value as a
    browser applies it; None when the pattern is not judged. ASCII mode
    gives \\w, \\d and \\b the meaning they have in the browser, where \\w
    matches no accented letter."""
    if _v_mode_rejects(pattern):
        return None
    try:
        compiled = re.compile(f"(?:{pattern})", re.ASCII)
    except re.error:
        return None
    return [s for s in samples if compiled.fullmatch(s) is None]


def _check_format_tolerance(form, labels):
    has_country = any(_purpose(c, labels, form) == "country" for c in form.fields())
    findings = []
    for c in form.fields():
        purpose = _purpose(c, labels, form)
        pattern = c.attrs.get("pattern")
        samples = {"phone": PHONE_SAMPLES, "name": NAME_SAMPLES}.get(purpose)
        if purpose == "postal code" and has_country:
            samples = POSTCODE_SAMPLES
        if pattern and samples:
            rejected = _pattern_rejects(pattern, samples)
            if rejected:
                findings.append(_finding(
                    "FORMS-FORMAT-TOLERANCE", 3, c, labels,
                    f"The pattern on this {purpose} field rejects valid values such as " + "; ".join(rejected[:2]) + ".",
                    "Loosen the pattern to accept every valid way of writing the value, and normalise it after submission.",
                    evidence=f"pattern={pattern}",
                ))
                continue
        maxlength = _int_attr(c, "maxlength")
        if purpose == "email" and maxlength is not None and maxlength < 254:
            findings.append(_finding(
                "FORMS-FORMAT-TOLERANCE", 2, c, labels,
                f"The email field accepts at most {maxlength} characters, though an email address may be up to 254.",
                "Remove the maximum length, or raise it to 254.",
                evidence=f"maxlength={maxlength}",
            ))
    return findings


def _check_input_font_size(form, labels, rules):
    """One finding per declaration, not per field: a single stylesheet rule
    that sizes every input at 14 pixels is one defect with one fix, and the
    fields it reaches are its instances."""
    groups = {}
    for c in form.fields():
        value, source = _declared(c, "font-size", rules)
        px = _font_size_px(value)
        if px is None or px >= 16:
            continue
        key = id(c) if source == "its inline style" else source
        groups.setdefault(key, (px, value, source, []))[3].append(c)
    findings = []
    for px, value, source, controls in groups.values():
        findings.extend(_occurrence_findings(
            "FORMS-INPUT-FONT-SIZE", 3 if px < 12 else 2, controls, labels,
            f"The text in this field is {px:g} pixels, below the 16 pixels at which a phone stops zooming the page on focus.",
            "Set the field's font size to at least 16 pixels.",
            evidence=f"font-size: {value} declared by {source}",
        ))
    return findings


INPUT_TYPE_EXPECTED = {"email": "email", "phone": "tel", "web address": "url", "search": "search"}
INPUT_TYPE_CANDIDATES = frozenset({"text", "number", "tel", "email", "url", "search"})


def _check_input_type(form, labels):
    flagged = []
    for c in form.fields():
        if c.tag != "input" or _input_type(c) not in INPUT_TYPE_CANDIDATES:
            continue
        purpose = _purpose(c, labels, form)
        expected = INPUT_TYPE_EXPECTED.get(purpose)
        if expected and _input_type(c) != expected:
            flagged.append((c, purpose, expected))
    severity = _severity_for_count(len(flagged))
    return [
        _finding(
            "FORMS-INPUT-TYPE", severity, c, labels,
            f"This {purpose} field is type {_input_type(c)}, so a phone does not show the keyboard built for it.",
            f"Set type={expected} on the field.",
        )
        for c, purpose, expected in flagged
    ]


def _check_numeric_inputmode(form, labels):
    findings = []
    for c in form.fields():
        if c.tag != "input":
            continue
        purpose = _purpose(c, labels, form)
        if purpose not in ("one-time code", "account number"):
            continue
        kind = _input_type(c)
        if kind == "number":
            findings.append(_finding(
                "FORMS-NUMERIC-INPUTMODE", 3, c, labels,
                f"This {purpose} uses the number type, built for quantities, so the browser may alter or refuse what is typed.",
                "Use type=text with inputmode=numeric.",
            ))
        elif kind == "text" and _attr_lower(c, "inputmode") != "numeric":
            findings.append(_finding(
                "FORMS-NUMERIC-INPUTMODE", 2, c, labels,
                f"This {purpose} is a text field without the numeric input mode, so a phone shows the full keyboard for digits.",
                "Add inputmode=numeric.",
            ))
    return findings


def _check_option_control(form, labels):
    flagged = []
    for c in form.controls:
        if c.tag != "select" or "multiple" in c.attrs:
            continue
        count = len(_real_options(c))
        if 2 <= count < 5:
            flagged.append((c, count))
    severity = _severity_for_count(len(flagged))
    return [
        _finding(
            "FORMS-OPTION-CONTROL", severity, c, labels,
            f"A single choice among {count} options sits in a drop-down, so the person must open it to see them.",
            "Offer the options as visible radio buttons.",
        )
        for c, count in flagged
    ]


def _check_password_rules(form, labels):
    findings = []
    for c in _password_fields(form):
        if _purpose(c, labels, form) != "new password" or _is_confirm(c, labels):
            continue
        problems, severity = [], 2
        if c.attrs.get("pattern"):
            problems.append("a pattern forces a composition rule")
            severity = 3
        if _int_attr(c, "maxlength") is not None:
            problems.append(f"a maximum length of {_int_attr(c, 'maxlength')} cuts long passwords short")
            severity = 3
        minlength = _int_attr(c, "minlength")
        if minlength is not None and minlength < 8:
            problems.append(f"the minimum length is only {minlength}")
        if problems:
            findings.append(_finding(
                "FORMS-PASSWORD-RULES", severity, c, labels,
                "On this new-password field, " + "; ".join(problems) + ".",
                "Require at least eight characters and remove the pattern and any maximum length.",
            ))
    return findings


REASON_MARKERS = ("so", "in case", "to contact", "to call", "to text", "about your", "for delivery",
                  "we will", "we'll", "only use", "used to", "why")


def _drop_apostrophes(text):
    return (text or "").replace("\u2019", "").replace("'", "")


def _own_group_text(control, form):
    """The text inside the control's parent element, when that parent groups
    this control alone. A parent holding other controls is a container for
    the whole form, and its text says nothing about this field."""
    parent = control.parent
    if parent is None or parent is form.node:
        return ""
    if any(n is not control and n in form.controls for n in parent.iter()):
        return ""
    return _clean(parent.text_content(_NON_LABEL_TEXT_TAGS))


def _check_phone_reason(form, labels):
    fields = form.fields()
    has_email = any(_purpose(c, labels, form) == "email" for c in fields)
    findings = []
    for c in fields:
        if _purpose(c, labels, form) != "phone" or not _is_required(c):
            continue
        nearby = " ".join((labels.text(c), labels.described_text(c), _own_group_text(c, form)))
        words = _words(_drop_apostrophes(nearby))
        if any(_matches(_drop_apostrophes(marker), words) for marker in REASON_MARKERS):
            continue
        findings.append(_finding(
            "FORMS-PHONE-REASON", 3 if has_email else 2, c, labels,
            "A phone number is required with no word beside the field on why it is needed"
            + (", though the form already asks for an email address." if has_email else "."),
            "Say beside the field what the number is used for, or make it optional.",
        ))
    return findings


RULE_MARKERS_RE = re.compile(r"\bmust\b|\bat least\b|\bcharacters?\b|\bdigits?\b|\bformat\b|\b(?:dd|mm|yy|yyyy)\s*[/.-]\s*(?:dd|mm|yy|yyyy)\b", re.I)
EXAMPLE_MARKERS_RE = re.compile(r"\be\.?g\.?(?=\s|,|:|$)|\bfor example\b|\bexample\b|@|\d{3,}", re.I)


def _check_placeholder_instruction(form, labels):
    findings = []
    for c in form.fields():
        placeholder = _clean(c.attrs.get("placeholder"))
        if not placeholder or not labels.has_label(c):
            continue
        is_rule = bool(RULE_MARKERS_RE.search(placeholder))
        is_example = bool(EXAMPLE_MARKERS_RE.search(placeholder))
        if not (is_rule or is_example):
            continue
        guidance = " ".join((labels.text(c), _clean(_attr(c, "aria-label")), labels.described_text(c)))
        if RULE_MARKERS_RE.search(guidance) or EXAMPLE_MARKERS_RE.search(guidance):
            continue
        findings.append(_finding(
            "FORMS-PLACEHOLDER-INSTRUCTION", 3 if is_rule else 2, c, labels,
            ("A format rule" if is_rule else "An example") + " appears only in the placeholder, which disappears as soon as typing starts.",
            "Move the " + ("rule" if is_rule else "example") + " into hint text beside the field, linked with aria-describedby.",
            evidence=f"placeholder={placeholder}",
        ))
    return findings


def _is_required(control):
    return "required" in control.attrs or _attr_lower(control, "aria-required") == "true"


_MARK_RE = re.compile(r"\*|\brequired\b|\boptional\b", re.I)


def _label_marked(control, labels):
    label = labels.label_node(control)
    if label is None:
        return False
    if _MARK_RE.search(label.text_content(_NON_LABEL_TEXT_TAGS)):
        return True
    return any(re.search(r"\brequired\b", _attr(n, "title"), re.I) for n in label.iter())


def _asterisk_explained(form):
    for node in form.node.iter():
        if node.tag == "label" or _nearest(node, "label") is not None:
            continue
        own = " ".join(c for c in node.children if isinstance(c, str))
        own += " " + " ".join(n.text_content() for n in node.element_children() if n.tag in ("span", "abbr", "strong", "b", "em"))
        if "*" in own and re.search(r"\b(required|mandatory)\b", own, re.I):
            return True
    return False


def _check_required_optional(form, labels):
    fields = form.fields()
    required = [c for c in fields if _is_required(c)]
    optional = [c for c in fields if not _is_required(c)]
    if not required or not optional:
        return []
    marked = [c for c in fields if _label_marked(c, labels)]
    in_placeholder = [c for c in fields if not _label_marked(c, labels) and _MARK_RE.search(c.attrs.get("placeholder") or "")]
    if not marked and not in_placeholder:
        return _occurrence_findings(
            "FORMS-REQUIRED-OPTIONAL", 3, [optional[0]] + [c for c in fields if c is not optional[0]], labels,
            f"The form mixes {len(required)} required and {len(optional)} optional fields and marks none of them, so the person cannot tell which may be left empty.",
            "Mark the optional fields with the word optional in their labels, or mark the required ones and explain the mark.",
        )
    findings = []
    starred = [c for c in marked if "*" in labels.text(c)]
    if starred and not _asterisk_explained(form):
        findings.append(_finding(
            "FORMS-REQUIRED-OPTIONAL", 2, starred[0], labels,
            "Labels carry an asterisk, but nothing in the form says what the asterisk means.",
            "Explain the asterisk in text before the first field, or mark optional fields in words instead.",
        ))
    findings.extend(_occurrence_findings(
        "FORMS-REQUIRED-OPTIONAL", 2, in_placeholder, labels,
        "Whether this field is required is stated only in its placeholder, which disappears as soon as typing starts.",
        "Move the required or optional marker into the label text.",
    ))
    return findings


RESET_LABELS = frozenset({"reset", "clear", "clear all", "clear form"})


def _adjacent(a, b):
    """Whether two controls share a parent and sit side by side in it, as
    neighbouring elements or as consecutive buttons."""
    if a.parent is None or a.parent is not b.parent:
        return False
    siblings = a.parent.element_children()
    if abs(siblings.index(a) - siblings.index(b)) == 1:
        return True
    buttons = [s for s in siblings if _is_button(s)]
    return abs(buttons.index(a) - buttons.index(b)) == 1


def _check_reset_button(form, labels):
    submit = form.primary_submit()
    findings = []
    for b in form.buttons():
        # Visible text only: an icon button whose accessible name is Clear
        # clears one field, as in a search box, not the whole form.
        is_reset = _attr_lower(b, "type") == "reset" or _bare_word(_visible_button_text(b)) in RESET_LABELS
        if not is_reset or b is submit:
            continue
        adjacent = submit is not None and _adjacent(b, submit)
        findings.append(_finding(
            "FORMS-RESET-BUTTON", 3 if adjacent else 2, b, labels,
            "A control that clears everything entered sits " + ("directly beside the submit button." if adjacent else "in the form."),
            "Remove the reset control.",
        ))
    return findings


def _given_family(control, labels):
    token = _field_name_token(_attr(control, "autocomplete"))
    if token in ("given-name", "additional-name", "family-name"):
        return token
    if _has_cue(control, labels, ("first name", "given name", "forename", "middle name")):
        return "given-name"
    if _has_cue(control, labels, ("last name", "family name", "surname")):
        return "family-name"
    return None


PHONE_PART_TOKENS = frozenset({"tel-area-code", "tel-local-prefix", "tel-local-suffix"})
# The longest part of a split phone number: an area code or a local group.
# A phone field longer than this is a whole number, so two such fields side
# by side are two numbers, such as home and mobile, not one number split.
PHONE_PART_MAX_LENGTH = 5


def _split_kind(control, labels, form):
    """Which split value this input can be a part of, or None."""
    if _int_attr(control, "maxlength") == 1:
        return "one-time code"
    if _field_name_token(_attr(control, "autocomplete")) in PHONE_PART_TOKENS:
        return "phone number"
    maxlength = _int_attr(control, "maxlength")
    if _purpose(control, labels, form) == "phone" and maxlength is not None and maxlength <= PHONE_PART_MAX_LENGTH:
        return "phone number"
    if _given_family(control, labels):
        return "name"
    return None


# The fewest consecutive parts that make each kind a split value. Three for
# a code, because a single one-character field, such as a middle initial,
# is common and two are rare.
SPLIT_MIN_PARTS = {"one-time code": 3, "phone number": 2, "name": 2}


def _check_split_entity(form, labels):
    inputs = [c for c in form.controls if c.tag == "input" and _is_text_like(c)]
    kinds = [_split_kind(c, labels, form) for c in inputs]
    runs, i = [], 0
    while i < len(inputs):
        kind = kinds[i]
        j = i + 1
        while kind and j < len(inputs) and kinds[j] == kind:
            j += 1
        run = inputs[i:j]
        if kind and len(run) >= SPLIT_MIN_PARTS[kind]:
            if kind != "name" or len({_given_family(r, labels) for r in run}) >= 2:
                runs.append((kind, run))
        i = j if kind else i + 1
    severity = _severity_for_count(len(runs))
    return [
        _finding(
            "FORMS-SPLIT-ENTITY", severity, run[0], labels,
            f"One {kind} is split across {len(run)} fields, so the person moves between boxes for a single value.",
            f"Collect the {kind} in one field.",
            evidence=" ".join(r.raw for r in run),
        )
        for kind, run in runs
    ]


# ---------------------------------------------------------------------------
# Aggregation and CLI
# ---------------------------------------------------------------------------


def check(artifact):
    """artifact: skills._shared.artifact.Artifact. Returns RawFindings,
    unranked and unbounded; run_scripted_lane does the rest. Checks run
    form by form in document order, criteria in ID order within each."""
    tree = _parse_html(artifact.text)
    rules = _build_stylesheet(tree)
    labels = Labels(tree)
    findings = []
    for form in _collect_forms(tree):
        findings.extend(_check_action_label(form, labels))
        findings.extend(_check_address_format(form, labels))
        findings.extend(_check_autocomplete(form, labels))
        findings.extend(_check_autocorrect(form, labels))
        findings.extend(_check_confirm_password(form, labels))
        findings.extend(_check_date_selects(form, labels))
        findings.extend(_check_field_width(form, labels, rules))
        findings.extend(_check_format_tolerance(form, labels))
        findings.extend(_check_input_font_size(form, labels, rules))
        findings.extend(_check_input_type(form, labels))
        findings.extend(_check_numeric_inputmode(form, labels))
        findings.extend(_check_option_control(form, labels))
        findings.extend(_check_password_rules(form, labels))
        findings.extend(_check_phone_reason(form, labels))
        findings.extend(_check_placeholder_instruction(form, labels))
        findings.extend(_check_required_optional(form, labels))
        findings.extend(_check_reset_button(form, labels))
        findings.extend(_check_split_entity(form, labels))
    return findings


def main(argv=None):
    return run_scripted_lane(
        skill_name="critique-forms",
        skill_version="0.1.0",
        rubrics=["FORMS"],
        check_fn=check,
        argv=argv,
    )


if __name__ == "__main__":
    sys.exit(main())
