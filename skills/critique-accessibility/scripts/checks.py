"""critique-accessibility scripted lane: the 13 WCAG 2.2 AA criteria in
SKILL.md's checks.scripted, against `references/WCAG.md`'s own
Operational test column for each. See docs/internal/skill-template.md,
"Wiring scripts/checks.py", for the pattern this file follows.

Scope of the CSS this file resolves (the artifact claim is "markup and
declared CSS as text", never a rendered page, per SKILL.md and
references/WCAG.md, "Scope"):

  - Inline `style="..."` attributes, and `<style>` blocks whose selectors
    are simple compound selectors with no combinator: a type selector
    (`div`), a class selector (`.card`), an id selector (`#hero`), the
    universal selector (`*`), or any concatenation of those
    (`div.card#hero`). A selector using a descendant combinator, a
    pseudo-class, an attribute selector, or anything else outside that
    set is not matched against any element; the declaration it carries
    is simply never applied. External stylesheets (`<link rel="stylesheet">`)
    are not fetched; nothing in them is read.
  - `@media` (and every other `@`-rule) is stripped out of the general
    cascade entirely, so the styles this file resolves are the page's
    unconditional declared styles, never a simulated viewport. Two
    checks (WCAG-1.4.10, WCAG-1.4.12) that specifically need to know
    whether a responsive override exists look at `@media` block text
    directly, as a coarse presence signal, not as a second cascade.
  - The cascade applied is: inline style, then matched `<style>`-block
    rules ordered by CSS specificity (id count, class count, type
    count), ties broken by source order, exactly as a browser's cascade
    resolves ties. `color` is treated as inherited (the walk continues
    to the parent when unset); `background-color` is resolved by
    walking up to the nearest ancestor with a non-transparent declared
    background, which is how backgrounds actually show through in the
    absence of CSS inheritance, not a browser rendering claim.
  - Colors: hex (#rgb, #rrggbb), rgb()/rgba(), and a few dozen common
    CSS named colors (_NAMED_COLORS, below). A color this file cannot
    parse (a gradient, a CSS variable, an unrecognized name) is treated
    as "cannot determine", and the check that needed it is skipped for
    that element rather than guessed at.
  - Font size and weight are resolved the same way, with px, pt, em,
    and rem units understood (em/rem relative to the parent's own
    resolved font-size, not compounded through the whole ancestor
    chain, since that already IS the ancestor chain).

This file assumes well-formed HTML input: it does not implement HTML5's
tag-soup auto-closing and error-recovery rules (an unclosed <p> is not
auto-closed the way a browser would close it). Every check below also
skips hidden content (a `hidden` attribute, `aria-hidden="true"`, or an
inline `display: none` / `visibility: hidden`, on the element or an
ancestor): a screen-reader user does not encounter it either, so it is
not a finding location a reader can navigate to.

Severity policy (methodology section 6, and this skill's own
`references/severity-anchors.md`, "Frequency and persistence pull
within the range impact set"): a criterion whose two anchor rows in
`references/WCAG.md` differ mainly in how many places the defect recurs
uses `_severity_for_count`: one instance is severity 2, two or more is
severity 3. A criterion whose anchor rows differ instead in how far a
measurement falls short (contrast ratio) scales severity off that
measurement directly. A criterion whose Operational test fires at most once per page (a
missing <html> lang attribute, a page with neither a main landmark nor
a skip link, an unusable <title>) cannot be graded by count at all, so
it is graded by impact directly, which is what the weighing order puts
first anyway: which branch of the condition fired, or how much of the
page the failure actually reaches. Both branches of every such check
correspond to that criterion's own two anchor rows in
references/WCAG.md; see each check function's own comment.

Every threshold this file applies is restated, with its reasoning, in
references/severity-anchors.md, "Thresholds the scripted lane applies",
so a judged-lane reviewer grades the same defect the same way rather
than having to read this module to find out where a boundary sits.

Location emission (`_loc`, `_element_anchor`): every finding names the
element it is about by that element's own id, written as a `#id` token,
and falls back to a bounded CSS path in double quotes for an element
that carries no id. A line number is kept at the end of the string as a
human convenience, never as the anchor: an html location resolves
through an element id, a quoted bounded selector, an ordinal over a noun
table, or a quoted span of element text, and a line number is none of
those, so a location built only from one names no element at all. See
SKILL.md, "Naming a location", which states the same rule for the judged
lane, and ADR 0027 (accessibility location-emission calibration), in
docs/internal/decisions/, for why this was worth a version.
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
    "WCAG-1.1.1",
    "WCAG-1.3.1",
    "WCAG-1.4.3",
    "WCAG-1.4.4",
    "WCAG-1.4.10",
    "WCAG-1.4.11",
    "WCAG-1.4.12",
    "WCAG-2.4.1",
    "WCAG-2.4.2",
    "WCAG-2.4.4",
    "WCAG-2.5.3",
    "WCAG-3.1.1",
    "WCAG-3.3.2",
})

# ---------------------------------------------------------------------------
# A minimal HTML tree: enough structure (parent, children, attrs, the
# exact source text of the opening tag, and a source line number) for
# every check below, with no dependency beyond html.parser.
# ---------------------------------------------------------------------------

VOID_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})

SKIP_TEXT_TAGS = frozenset({
    "script", "style", "head", "title", "meta", "link", "noscript", "template",
})

INTERACTIVE_TAGS = frozenset({"button", "a", "input", "select", "textarea"})
INTERACTIVE_ROLES = frozenset({"button", "link", "checkbox", "radio", "switch", "tab", "menuitem"})

GENERIC_LINK_PHRASES = frozenset({
    "click here", "here", "read more", "more", "link", "this page", "learn more",
})

PLACEHOLDER_ALT_WORDS = frozenset({"image", "photo", "icon", "graphic"})
IMAGE_EXT_RE = re.compile(r"\.(jpe?g|png|gif|svg|webp|bmp|tiff?)$", re.I)

PLACEHOLDER_TITLES = frozenset({"untitled", "untitled document", "document", "new page", "page title"})


class Node:
    """One element (or the synthetic '#root' wrapper) in the parsed
    tree. `raw` is the exact source text of the opening tag, captured
    via HTMLParser.get_starttag_text(), so evidence fields quote the
    artifact rather than reconstructing it."""

    def __init__(self, tag, attrs, line, parent=None, raw=""):
        self.tag = tag
        self.attrs = attrs
        self.line = line
        self.parent = parent
        self.raw = raw
        self.children = []  # list of Node or str

    def text_content(self):
        parts = []

        def walk(n):
            for c in n.children:
                if isinstance(c, str):
                    parts.append(c)
                else:
                    walk(c)

        walk(self)
        return "".join(parts)

    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.iter()


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, 1)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        self._open(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def _open(self, tag, attrs):
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


def _parse_html(text):
    builder = _TreeBuilder()
    builder.feed(text)
    builder.close()
    return builder.root


# ---------------------------------------------------------------------------
# Declared CSS: parsing, cascade, and resolution. See the module
# docstring for exactly what is and is not supported.
# ---------------------------------------------------------------------------

_CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)


def _strip_css_comments(text):
    return _CSS_COMMENT_RE.sub("", text or "")


def _strip_at_rules(text):
    """Removes every `@rule { ... }` or `@rule ...;` block, with
    correct brace nesting, so the remainder is safe to split on '}' as
    flat, unconditional rule blocks."""
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
            depth = 1
            j = brace_pos + 1
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


def _extract_media_block_texts(css_text):
    """Every `@media { ... }` block's inner text, kept (not stripped),
    for the two checks that use media-query presence as a coarse
    mitigating signal rather than folding it into the general cascade."""
    blocks = []
    lowered = css_text.lower()
    i, n = 0, len(css_text)
    while i < n:
        if lowered.startswith("@media", i):
            brace_pos = css_text.find("{", i)
            if brace_pos == -1:
                break
            depth = 1
            j = brace_pos + 1
            while j < n and depth > 0:
                if css_text[j] == "{":
                    depth += 1
                elif css_text[j] == "}":
                    depth -= 1
                j += 1
            blocks.append(css_text[brace_pos + 1: j - 1])
            i = j
            continue
        i += 1
    return blocks


def _parse_declarations(text):
    decls = {}
    for item in (text or "").split(";"):
        if ":" not in item:
            continue
        prop, _, value = item.partition(":")
        prop = prop.strip().lower()
        value = value.strip()
        if prop and value:
            decls[prop] = value
    return decls


def _parse_style_block(text):
    """`text` has already had comments and @rules removed, so every
    remaining '}'-delimited chunk is one flat, unconditional rule."""
    rules = []
    for chunk in text.split("}"):
        if "{" not in chunk:
            continue
        sel_part, decl_part = chunk.split("{", 1)
        selectors = [s.strip() for s in sel_part.split(",") if s.strip()]
        decls = _parse_declarations(decl_part)
        if selectors and decls:
            rules.append((selectors, decls))
    return rules


_SIMPLE_SELECTOR_TOKEN_RE = re.compile(r"\*|[A-Za-z][A-Za-z0-9]*|\.[A-Za-z_-][\w-]*|#[A-Za-z_-][\w-]*")


def _parse_compound_selector(sel):
    """Returns a list of simple-selector tokens for a combinator-free
    compound selector (`div.card#hero`), or None when the selector uses
    a combinator, an attribute selector, or a pseudo-class/element,
    none of which this file matches against anything."""
    sel = sel.strip()
    if not sel or any(ch in sel for ch in " \t\n>+~[:"):
        return None
    tokens = _SIMPLE_SELECTOR_TOKEN_RE.findall(sel)
    if "".join(tokens) != sel:
        return None
    return tokens


def _selector_matches(tokens, node):
    for tok in tokens:
        if tok == "*":
            continue
        if tok.startswith("#"):
            if node.attrs.get("id") != tok[1:]:
                return False
        elif tok.startswith("."):
            classes = (node.attrs.get("class") or "").split()
            if tok[1:] not in classes:
                return False
        else:
            if node.tag != tok.lower():
                return False
    return True


def _specificity(tokens):
    ids = sum(1 for t in tokens if t.startswith("#"))
    classes = sum(1 for t in tokens if t.startswith("."))
    types = sum(1 for t in tokens if t != "*" and not t.startswith(("#", ".")))
    return ids, classes, types


def _build_stylesheet(tree):
    """Every declared_check-eligible rule across every <style> block in
    the document, as (specificity, source_order, tokens, declarations)
    tuples, ready for _matched_decls to apply per element."""
    rules = []
    order = 0
    for node in tree.iter():
        if node.tag != "style":
            continue
        css_text = _strip_at_rules(_strip_css_comments(node.text_content()))
        for selectors, decls in _parse_style_block(css_text):
            for sel in selectors:
                tokens = _parse_compound_selector(sel)
                if tokens is None:
                    continue
                rules.append((_specificity(tokens), order, tokens, decls))
                order += 1
    return rules


def _style_text(tree):
    """The comment-stripped, but @rule-intact, text of every <style>
    block, for the media-query presence signal only."""
    return "\n".join(_strip_css_comments(n.text_content()) for n in tree.iter() if n.tag == "style")


def _matched_decls(node, rules):
    matches = [(spec, order, decls) for spec, order, tokens, decls in rules if _selector_matches(tokens, node)]
    matches.sort(key=lambda m: (m[0], m[1]))
    result = {}
    for _spec, _order, decls in matches:
        result.update(decls)
    return result


def _find_declared(node, prop, rules):
    """The cascade-resolved value `node` itself declares for `prop`
    (inline style wins over a matched <style>-block rule), or None when
    nothing at this element declares it."""
    inline = _parse_declarations(node.attrs.get("style") or "")
    if prop in inline:
        return inline[prop]
    return _matched_decls(node, rules).get(prop)


_TRANSPARENT_KEYWORDS = frozenset({"transparent", "inherit", "initial", "unset", ""})
_INHERIT_KEYWORDS = frozenset({"inherit", "initial", "unset", "currentcolor", ""})


def _extract_color_token(value):
    """The first color-shaped token inside a shorthand value (`border`,
    `background`), skipping widths and style keywords."""
    if not value:
        return None
    m = re.search(r"rgba?\([^)]*\)", value, re.I)
    if m:
        return m.group(0)
    for token in value.split():
        t = token.strip().rstrip(";")
        low = t.lower()
        if t.startswith("#") or low in _NAMED_COLORS or low in ("transparent", "currentcolor"):
            return t
    return None


_BORDER_STYLE_KEYWORDS = frozenset({
    "none", "hidden", "solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset",
})


def _extract_style_token(value):
    for token in value.split():
        if token.strip().lower() in _BORDER_STYLE_KEYWORDS:
            return token.strip()
    return None


def _extract_width_token(value):
    for token in value.split():
        t = token.strip()
        if _LENGTH_RE.match(t.lower()):
            return t
    return None


def _resolve_color(node, prop, rules, default):
    """Walk-up resolution for an inherited color property (`color`):
    the nearest ancestor (including `node` itself) that declares a
    usable value wins; a declared-but-unparseable value (currentColor,
    a variable) stops the search and returns None rather than guessing.
    """
    n = node
    while n is not None:
        raw = _find_declared(n, prop, rules)
        if raw is not None:
            lowered = raw.strip().lower()
            if lowered in _INHERIT_KEYWORDS:
                n = n.parent
                continue
            return _parse_color(raw)
        n = n.parent
    return default


def _resolve_background(node, rules, default):
    """Walk-up resolution for `background-color` (not CSS-inherited,
    but painted backgrounds show through a transparent element to
    whatever is behind it, which this models by continuing the walk on
    `transparent`/absent and stopping on any other declared value)."""
    n = node
    while n is not None:
        raw = _find_declared(n, "background-color", rules)
        source = raw
        if source is None:
            shorthand = _find_declared(n, "background", rules)
            source = _extract_color_token(shorthand) if shorthand else None
        if source is not None:
            lowered = source.strip().lower()
            if lowered in _TRANSPARENT_KEYWORDS:
                n = n.parent
                continue
            return _parse_color(source)
        n = n.parent
    return default


def _resolve_border_or_outline(node, rules):
    """(color_token, width_token, style_token) for whichever of border
    or outline `node` declares a color for, border taking precedence.
    All three come from either the longhand property or a parsed
    shorthand; any that cannot be found stays None."""
    for prefix in ("border", "outline"):
        color = _find_declared(node, f"{prefix}-color", rules)
        width = _find_declared(node, f"{prefix}-width", rules)
        style = _find_declared(node, f"{prefix}-style", rules)
        shorthand = _find_declared(node, prefix, rules)
        if shorthand:
            if color is None:
                color = _extract_color_token(shorthand)
            if style is None:
                style = _extract_style_token(shorthand)
            if width is None:
                width = _extract_width_token(shorthand)
        if color:
            return color, width, (style.strip().lower() if style else None)
    return None, None, None


def _computed_font_size_px(node, rules):
    base = 16.0 if node.parent is None else _computed_font_size_px(node.parent, rules)
    raw = _find_declared(node, "font-size", rules)
    length = _parse_length(raw) if raw else None
    if length is None:
        return base
    px = _length_to_px(length, base_px=base)
    return px if px is not None else base


def _computed_font_weight(node, rules):
    raw = _find_declared(node, "font-weight", rules)
    if raw is not None:
        lowered = raw.strip().lower()
        if lowered == "bold":
            return 700
        if lowered == "normal":
            return 400
        try:
            return int(float(lowered))
        except ValueError:
            pass
    if node.tag in ("b", "strong"):
        return 700
    if node.parent is None:
        return 400
    return _computed_font_weight(node.parent, rules)


def _has_media_width_override(node, media_blocks):
    """A coarse presence signal, not a second cascade: true when some
    @media block's raw text both mentions `width` and mentions this
    element by tag, class, or id."""
    tokens = [node.tag]
    if node.attrs.get("id"):
        tokens.append("#" + node.attrs["id"])
    for cls in (node.attrs.get("class") or "").split():
        tokens.append("." + cls)
    for block in media_blocks:
        if "width" not in block:
            continue
        for token in tokens:
            if token and re.search(re.escape(token) + r"(?![\w-])", block):
                return True
    return False


# ---------------------------------------------------------------------------
# Length, color, and contrast arithmetic
# ---------------------------------------------------------------------------

_LENGTH_RE = re.compile(r"^(-?[\d.]+)(px|pt|em|rem|%|vw|vh)?$")


def _parse_length(value):
    if value is None:
        return None
    v = value.strip().lower()
    m = _LENGTH_RE.match(v)
    if not m:
        return None
    try:
        num = float(m.group(1))
    except ValueError:
        return None
    return num, (m.group(2) or "px")


def _length_to_px(length, base_px=16.0):
    num, unit = length
    if unit == "px":
        return num
    if unit == "pt":
        return num * 4.0 / 3.0
    if unit in ("em", "rem"):
        return num * base_px
    return None  # %, vw, vh: a relative unit, not a fixed px measure


def _is_zero_length(token):
    length = _parse_length(token)
    return length is not None and length[0] == 0


# A working subset of the CSS named-color table, not all 147: common
# names a hand-written test page or fixture is likely to use. A name
# outside this set is treated as "cannot determine" (see the module
# docstring), never guessed at.
_NAMED_COLORS = {
    "black": (0, 0, 0), "white": (255, 255, 255), "red": (255, 0, 0), "green": (0, 128, 0),
    "blue": (0, 0, 255), "yellow": (255, 255, 0), "cyan": (0, 255, 255), "magenta": (255, 0, 255),
    "gray": (128, 128, 128), "grey": (128, 128, 128), "silver": (192, 192, 192),
    "maroon": (128, 0, 0), "olive": (128, 128, 0), "lime": (0, 255, 0), "aqua": (0, 255, 255),
    "teal": (0, 128, 128), "navy": (0, 0, 128), "fuchsia": (255, 0, 255), "purple": (128, 0, 128),
    "orange": (255, 165, 0), "pink": (255, 192, 203), "brown": (165, 42, 42), "gold": (255, 215, 0),
    "indigo": (75, 0, 130), "violet": (238, 130, 238), "coral": (255, 127, 80), "salmon": (250, 128, 114),
    "khaki": (240, 230, 140), "plum": (221, 160, 221), "orchid": (218, 112, 214), "tan": (210, 180, 140),
    "beige": (245, 245, 220), "ivory": (255, 255, 240), "lavender": (230, 230, 250), "crimson": (220, 20, 60),
    "chocolate": (210, 105, 30), "darkgray": (169, 169, 169), "darkgrey": (169, 169, 169),
    "lightgray": (211, 211, 211), "lightgrey": (211, 211, 211), "dimgray": (105, 105, 105),
    "dimgrey": (105, 105, 105), "slategray": (112, 128, 144), "slategrey": (112, 128, 144),
    "steelblue": (70, 130, 180), "skyblue": (135, 206, 235), "royalblue": (65, 105, 225),
    "dodgerblue": (30, 144, 255), "forestgreen": (34, 139, 34), "seagreen": (46, 139, 87),
    "darkgreen": (0, 100, 0), "lightgreen": (144, 238, 144), "firebrick": (178, 34, 34),
    "indianred": (205, 92, 92), "hotpink": (255, 105, 180), "deeppink": (255, 20, 147),
    "darkorange": (255, 140, 0), "tomato": (255, 99, 71), "darkred": (139, 0, 0),
    "darkblue": (0, 0, 139), "midnightblue": (25, 25, 112), "whitesmoke": (245, 245, 245),
    "gainsboro": (220, 220, 220), "darkgoldenrod": (184, 134, 11),
}


def _parse_color(value):
    if value is None:
        return None
    v = value.strip().lower()
    if not v or v in ("transparent", "inherit", "initial", "unset", "currentcolor"):
        return None
    m = re.fullmatch(r"#([0-9a-f]{3})", v)
    if m:
        r, g, b = m.group(1)
        return int(r * 2, 16), int(g * 2, 16), int(b * 2, 16)
    m = re.fullmatch(r"#([0-9a-f]{6})", v)
    if m:
        h = m.group(1)
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    m = re.fullmatch(r"rgba?\(\s*([\d.]+%?)\s*,\s*([\d.]+%?)\s*,\s*([\d.]+%?)\s*(?:,\s*[\d.]+\s*)?\)", v)
    if m:
        def chan(tok):
            if tok.endswith("%"):
                return round(float(tok[:-1]) / 100 * 255)
            return round(float(tok))

        return tuple(max(0, min(255, chan(t))) for t in m.groups())
    if v in _NAMED_COLORS:
        return _NAMED_COLORS[v]
    return None


def _relative_luminance(rgb):
    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(rgb1, rgb2):
    l1 = _relative_luminance(rgb1)
    l2 = _relative_luminance(rgb2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _to_hex(rgb):
    return "#%02x%02x%02x" % rgb


# ---------------------------------------------------------------------------
# Small shared helpers
# ---------------------------------------------------------------------------


def _normalize_ws(s):
    return " ".join((s or "").split())


def _truncate(s, n=300):
    s = s or ""
    return s if len(s) <= n else s[: n - 3] + "..."


_MAX_LOCATION_CHARS = 400  # contract/critique-contract.schema.json, $defs/locationText

# An element id the html location grammar recognizes as a bare `#id`
# token: it starts with a letter, then word characters and hyphens
# (bench/README.md, "Location tolerance", the `html` row).
_BARE_ID_RE = re.compile(r"[A-Za-z][\w-]*")


def _css_path_parts(node):
    """The document-root-to-`node` path as a list of simple selectors,
    using tag names and `:nth-of-type` only. That subset, joined by the
    child combinator, is inside the bounded selector engine the location
    grammar defines (tag, `#id`, `.class`, descendant, child, and
    `:nth-of-type`), so a reader and a resolver read the same path."""
    parts = []
    cur = node
    while cur is not None and cur.tag != "#root":
        parent = cur.parent
        siblings = (
            [c for c in parent.children if isinstance(c, Node) and c.tag == cur.tag]
            if parent is not None
            else []
        )
        if len(siblings) > 1:
            parts.append(f"{cur.tag}:nth-of-type({siblings.index(cur) + 1})")
        else:
            parts.append(cur.tag)
        cur = parent
    parts.reverse()
    return parts


def _element_anchor(node):
    """The part of a location string that names *which element* the
    finding is about, in the artifact type's own location grammar: the
    element's id as a `#id` token when it has one, and otherwise a
    bounded CSS path in double quotes.

    This exists because a line number is not an anchor. `line 21, <img>
    element` tells a reader roughly where to look and tells a resolver
    nothing at all: the html grammar recognizes an element id, a quoted
    bounded selector, an ordinal over a noun table, or a quoted string of
    element text, and a bare line number is none of the four. Every check
    below already holds the node, so the id is free; discarding it was
    the defect ADR 0027 fixes."""
    element_id = (node.attrs.get("id") or "").strip()
    if element_id and _BARE_ID_RE.fullmatch(element_id):
        return f"#{element_id}"

    parts = _css_path_parts(node)
    if element_id:
        # An id outside the bare-token grammar (one not starting with a
        # letter) still resolves inside a bounded selector, so carry it
        # there rather than dropping it. It replaces the last step's
        # `:nth-of-type`, which it makes redundant anyway.
        last = f"{node.tag}#{element_id}"
        parts = parts[:-1] + [last] if parts else [last]
    if not parts:
        parts = [node.tag]
    return '"' + " > ".join(parts) + '"'


def _loc(node, descriptor):
    """`<anchor>, <descriptor>, line <n>`.

    The anchor comes first because it is the part that has to resolve;
    the descriptor says what kind of thing it is, and the line number is
    a human convenience at the end, never the anchor itself. A location
    long enough to reach the contract's 400-character bound loses the
    tail rather than the anchor, for the same reason: a truncated
    descriptor still resolves, and a truncated anchor does not."""
    anchor = _element_anchor(node)
    tail = f", {descriptor}, line {node.line}"
    budget = _MAX_LOCATION_CHARS - len(anchor)
    if len(tail) > budget:
        tail = tail[: max(0, budget - 3)].rstrip() + "..."
    return (anchor + tail)[:_MAX_LOCATION_CHARS]


def _has_direct_text(node):
    return any(isinstance(c, str) and c.strip() for c in node.children)


def _is_hidden(node):
    """Hidden by a `hidden` attribute, `aria-hidden="true"`, or an
    inline `display: none` / `visibility: hidden`, on this element or
    any ancestor. Only inline styles are consulted here (not the
    <style>-block cascade), a deliberate scope narrowing that keeps
    this helper usable from every check without threading the
    stylesheet through all of them; see the module docstring."""
    n = node
    while n is not None:
        if "hidden" in n.attrs:
            return True
        if (n.attrs.get("aria-hidden") or "").strip().lower() == "true":
            return True
        inline = _parse_declarations(n.attrs.get("style") or "")
        if (inline.get("display") or "").strip().lower() == "none":
            return True
        if (inline.get("visibility") or "").strip().lower() == "hidden":
            return True
        n = n.parent
    return False


def _is_full_page(tree):
    return any(n.tag in ("html", "body") for n in tree.iter())


def _severity_for_count(count):
    """Escalation shared by every criterion whose severity 2 and 3
    anchors differ mainly in how many places the defect recurs (see
    the module docstring, "Severity policy"): one instance stays at the
    criterion's base severity of 2; two or more escalates to 3."""
    return 3 if count >= 2 else 2


# ---------------------------------------------------------------------------
# WCAG-1.1.1: text alternatives for non-text content
# ---------------------------------------------------------------------------


def _check_alt_text(tree):
    candidates = []
    for node in tree.iter():
        if _is_hidden(node):
            continue
        tag = node.tag
        is_img_like = tag in ("img", "area") or (tag == "input" and (node.attrs.get("type") or "").strip().lower() == "image")
        is_role_img = (node.attrs.get("role") or "").strip().lower() == "img"
        if is_img_like or is_role_img:
            candidates.append((node, is_img_like))

    violations = []
    for node, is_img_like in candidates:
        role = (node.attrs.get("role") or "").strip().lower()
        aria_hidden = (node.attrs.get("aria-hidden") or "").strip().lower()
        is_decorative = role in ("presentation", "none") or aria_hidden == "true"
        if is_img_like and node.attrs.get("alt") == "":
            is_decorative = True
        if is_decorative:
            continue

        if is_img_like:
            alt = node.attrs.get("alt")
            if alt is None:
                violations.append((node, "missing", None))
                continue
            text = alt
        else:
            if node.attrs.get("aria-labelledby"):
                continue
            text = node.attrs.get("aria-label")
            if text is None:
                violations.append((node, "missing", None))
                continue

        normalized = _normalize_ws(text).lower()
        if normalized in PLACEHOLDER_ALT_WORDS or IMAGE_EXT_RE.search(normalized):
            violations.append((node, "placeholder", text))

    severity = _severity_for_count(len(violations))
    findings = []
    for node, kind, text in violations:
        if kind == "missing":
            violation = "No text alternative is present and the element is not marked decorative."
            fix = 'Add an alt attribute (or aria-label) describing the image, or mark it decorative with alt="".'
        else:
            violation = f"The text alternative '{text}' is a generic placeholder rather than a description."
            fix = "Replace the text alternative with a description of what the image conveys."
        findings.append(RawFinding(
            criterion="WCAG-1.1.1",
            severity=severity,
            location=_loc(node, f"<{node.tag}> element"),
            evidence=_truncate(node.raw),
            violation=violation,
            fix=fix,
        ))
    return findings


# ---------------------------------------------------------------------------
# WCAG-1.3.1: info and relationships (heading-level skips, table headers)
# ---------------------------------------------------------------------------


def _check_structure(tree):
    findings = []

    headings = [n for n in tree.iter() if n.tag in ("h1", "h2", "h3", "h4", "h5", "h6") and not _is_hidden(n)]
    skips = []
    for prev, cur in zip(headings, headings[1:]):
        prev_level = int(prev.tag[1])
        cur_level = int(cur.tag[1])
        if cur_level - prev_level > 1:
            skips.append((prev, cur))

    # Count-based: a single skip is severity 2, a document with several
    # is severity 3 (see "Severity policy" in the module docstring).
    heading_severity = _severity_for_count(len(skips))
    for prev, cur in skips:
        # prev_level is recomputed here, from this skip pair's own `prev`,
        # rather than reused from the detection loop above: that loop's
        # `prev_level`/`cur_level` are left holding whichever heading pair
        # it examined last (not necessarily this skip), and reusing them
        # named the wrong target level once a heading followed the skip.
        prev_level = int(prev.tag[1])
        heading_text = _normalize_ws(cur.text_content())[:60]
        findings.append(RawFinding(
            criterion="WCAG-1.3.1",
            severity=heading_severity,
            location=_loc(cur, f"<{cur.tag}> heading, '{heading_text}'"),
            evidence=_truncate(cur.raw),
            violation=f"Heading level skips from <{prev.tag}> to <{cur.tag}> with no intervening level.",
            fix=f"Change this heading to <h{prev_level + 1}>, or add the missing intervening heading level.",
        ))

    for table in [n for n in tree.iter() if n.tag == "table" and not _is_hidden(n)]:
        rows = [n for n in table.iter() if n.tag == "tr"]
        if len(rows) < 2:
            continue
        col_counts = [
            sum(1 for c in row.children if isinstance(c, Node) and c.tag in ("td", "th"))
            for row in rows
        ]
        col_count = max(col_counts) if col_counts else 0
        if col_count < 2:
            continue
        has_headers = any(n.tag == "th" or "scope" in n.attrs or "headers" in n.attrs for n in table.iter())
        if has_headers:
            continue
        # Not count-based: a whole unmarked, multi-row, multi-column
        # table is the structural failure the anchor row describes
        # directly, so this is always severity 3.
        findings.append(RawFinding(
            criterion="WCAG-1.3.1",
            severity=3,
            location=_loc(table, "<table> element"),
            evidence=f"table with {len(rows)} rows and {col_count} columns, no th, scope, or headers attributes present",
            violation="A multi-row, multi-column data table has no th, scope, or headers markup associating cells with their headers.",
            fix="Mark header cells with <th>, and set scope (or headers/id pairs) linking data cells to their header cells.",
        ))

    return findings


# ---------------------------------------------------------------------------
# WCAG-1.4.3: contrast, text
# ---------------------------------------------------------------------------


def _check_text_contrast(tree, rules):
    findings = []
    for node in tree.iter():
        if node.tag in SKIP_TEXT_TAGS or _is_hidden(node):
            continue
        if not _has_direct_text(node):
            continue

        fg = _resolve_color(node, "color", rules, default=(0, 0, 0))
        bg = _resolve_background(node, rules, default=(255, 255, 255))
        if fg is None or bg is None:
            continue

        font_px = _computed_font_size_px(node, rules)
        font_weight = _computed_font_weight(node, rules)
        is_large = font_px >= 24 or (font_px >= 18.66 and font_weight >= 700)
        threshold = 3.0 if is_large else 4.5

        ratio = _contrast_ratio(fg, bg)
        if ratio >= threshold - 1e-9:
            continue

        # Ratio-based, not count-based: the anchor rows differ by how
        # far below the minimum the ratio falls, not by how many times
        # it recurs (see "Severity policy" in the module docstring).
        severity = 3 if ratio < threshold - 1.0 else 2

        snippet = _truncate(_normalize_ws("".join(c for c in node.children if isinstance(c, str))), 80)
        findings.append(RawFinding(
            criterion="WCAG-1.4.3",
            severity=severity,
            location=_loc(node, f"<{node.tag}> element, text '{snippet}'"),
            evidence=f"text color {_to_hex(fg)} on background {_to_hex(bg)}, contrast ratio {ratio:.2f}:1",
            violation=f"Contrast ratio {ratio:.2f}:1 is below the {threshold:.1f}:1 AA minimum for {'large' if is_large else 'normal'} text.",
            fix=f"Darken the text or lighten the background until the ratio reaches at least {threshold:.1f}:1.",
        ))
    return findings


# ---------------------------------------------------------------------------
# WCAG-1.4.4: resize text (viewport zoom blocking)
# ---------------------------------------------------------------------------


def _check_viewport_zoom(tree):
    meta = next(
        (n for n in tree.iter() if n.tag == "meta" and (n.attrs.get("name") or "").strip().lower() == "viewport"),
        None,
    )
    if meta is None:
        return []

    content = meta.attrs.get("content") or ""
    settings = {}
    for part in content.split(","):
        if "=" in part:
            key, _, value = part.partition("=")
            settings[key.strip().lower()] = value.strip().lower()

    user_scalable = settings.get("user-scalable")
    max_scale_raw = settings.get("maximum-scale")
    max_scale = None
    if max_scale_raw is not None:
        try:
            max_scale = float(max_scale_raw)
        except ValueError:
            max_scale = None

    blocks_entirely = user_scalable in ("no", "0")
    caps_below_200 = max_scale is not None and max_scale < 2.0

    if not blocks_entirely and not caps_below_200:
        return []

    # Not count-based: full block versus a partial cap are two
    # different conditions the operational test distinguishes by
    # outcome, not by recurrence, so severity comes from which
    # condition fired (see "Severity policy" in the module docstring).
    if blocks_entirely:
        severity = 3
        violation = "The viewport meta tag sets user-scalable=no, disabling browser zoom entirely."
        fix = "Remove user-scalable=no so readers can zoom the page."
    else:
        severity = 2
        violation = f"The viewport meta tag caps maximum-scale at {max_scale_raw}, below the 200 percent a reader needs to enlarge text."
        fix = "Raise maximum-scale to at least 2, or remove it, so readers can zoom to 200 percent."

    return [RawFinding(
        criterion="WCAG-1.4.4",
        severity=severity,
        location=_loc(meta, "<meta> viewport element"),
        evidence=_truncate(meta.raw),
        violation=violation,
        fix=fix,
    )]


# ---------------------------------------------------------------------------
# WCAG-1.4.10: reflow (fixed pixel width with no responsive override)
# ---------------------------------------------------------------------------


def _check_fixed_width_reflow(tree, rules):
    findings = []
    media_blocks = _extract_media_block_texts(_style_text(tree))

    for node in tree.iter():
        if node.tag in ("html", "head", "meta", "title", "style", "script"):
            continue
        if _is_hidden(node):
            continue

        width_raw = _find_declared(node, "width", rules)
        length = _parse_length(width_raw) if width_raw else None
        if length is None or length[1] not in ("px", "pt"):
            continue
        width_px = _length_to_px(length)
        if width_px is None or width_px <= 320:
            continue

        max_width_raw = _find_declared(node, "max-width", rules)
        if max_width_raw:
            mw = _parse_length(max_width_raw)
            if mw is not None and mw[1] in ("%", "vw", "vh"):
                continue  # a relative cap is a responsive override

        if _has_media_width_override(node, media_blocks):
            continue

        # Count-independent: severity scales with how much of the page
        # the fixed width covers, using pixel width itself as the
        # proxy (see "Severity policy" in the module docstring and the
        # 400px-banner-versus-960px-body-wrapper anchor pair in
        # references/WCAG.md).
        severity = 3 if width_px >= 600 else 2
        findings.append(RawFinding(
            criterion="WCAG-1.4.10",
            severity=severity,
            location=_loc(node, f"<{node.tag}> element"),
            evidence=f"declared width: {width_raw}",
            violation=f"A fixed width of {width_raw} forces horizontal scrolling once the viewport narrows to 320px, with no responsive override.",
            fix="Cap the element's width with a relative max-width (a percentage or viewport unit), or add a media query that shrinks it below 320px.",
        ))
    return findings


# ---------------------------------------------------------------------------
# WCAG-1.4.11: contrast, non-text (interactive component boundaries)
# ---------------------------------------------------------------------------


def _check_component_contrast(tree, rules):
    findings = []
    for node in tree.iter():
        if _is_hidden(node):
            continue
        role = (node.attrs.get("role") or "").strip().lower()
        if node.tag not in INTERACTIVE_TAGS and role not in INTERACTIVE_ROLES:
            continue
        if node.tag == "a" and not node.attrs.get("href"):
            continue

        color_token, width_token, style_token = _resolve_border_or_outline(node, rules)
        if color_token is None:
            continue
        if style_token in ("none", "hidden"):
            continue
        if width_token is not None and _is_zero_length(width_token):
            continue

        fg = _parse_color(color_token)
        if fg is None:
            continue
        bg = _resolve_background(node.parent, rules, default=(255, 255, 255)) if node.parent else (255, 255, 255)
        if bg is None:
            continue

        ratio = _contrast_ratio(fg, bg)
        if ratio >= 3.0 - 1e-9:
            continue

        # Ratio-based, matching the same reasoning as WCAG-1.4.3.
        severity = 3 if ratio < 2.0 else 2
        findings.append(RawFinding(
            criterion="WCAG-1.4.11",
            severity=severity,
            location=_loc(node, f"<{node.tag}> element boundary"),
            evidence=f"boundary color {_to_hex(fg)} against adjacent background {_to_hex(bg)}, contrast ratio {ratio:.2f}:1",
            violation=f"Component boundary contrast ratio {ratio:.2f}:1 is below the 3:1 AA minimum.",
            fix="Darken the border or outline color, or change the adjacent background, until the ratio reaches at least 3:1.",
        ))
    return findings


# ---------------------------------------------------------------------------
# WCAG-1.4.12: text spacing (fixed height plus clipped overflow)
# ---------------------------------------------------------------------------


def _check_text_spacing_clip(tree, rules):
    candidates = []
    for node in tree.iter():
        if node.tag in ("html", "head", "meta", "title", "style", "script"):
            continue
        if _is_hidden(node):
            continue
        if not node.text_content().strip():
            continue

        height_raw = _find_declared(node, "height", rules) or _find_declared(node, "max-height", rules)
        length = _parse_length(height_raw) if height_raw else None
        if length is None or length[1] not in ("px", "pt"):
            continue

        overflow_raw = _find_declared(node, "overflow", rules) or _find_declared(node, "overflow-y", rules)
        if overflow_raw is None or overflow_raw.strip().lower() not in ("hidden", "clip"):
            continue

        candidates.append((node, height_raw, overflow_raw))

    severity = _severity_for_count(len(candidates))
    findings = []
    for node, height_raw, overflow_raw in candidates:
        findings.append(RawFinding(
            criterion="WCAG-1.4.12",
            severity=severity,
            location=_loc(node, f"<{node.tag}> element"),
            evidence=f"height: {height_raw}; overflow: {overflow_raw}",
            violation="A fixed height combined with clipped overflow truncates this element's text once a reader applies wider line, paragraph, letter, or word spacing.",
            fix="Remove the fixed height so the element grows with its content, or replace the clipped overflow with visible or auto.",
        ))
    return findings


# ---------------------------------------------------------------------------
# WCAG-2.4.1: bypass blocks (main landmark or skip link)
# ---------------------------------------------------------------------------


FOCUSABLE_TAGS = frozenset({"a", "button", "input", "select", "textarea"})


def _focusables_before_first_heading(tree):
    """Every focusable element appearing earlier in document order than
    the page's first heading: the markup's own measure of how much a
    reader has to traverse before reaching content. Used only to grade
    WCAG-2.4.1's severity, never to decide whether it fires."""
    count = 0
    for node in tree.iter():
        if node.tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            break
        if _is_hidden(node):
            continue
        if node.tag == "a" and not node.attrs.get("href"):
            continue
        if node.tag in FOCUSABLE_TAGS:
            count += 1
    return count


def _check_bypass_block(tree):
    if not _is_full_page(tree):
        return []

    has_main = any(
        n.tag == "main" or (n.attrs.get("role") or "").strip().lower() == "main"
        for n in tree.iter()
    )
    if has_main:
        return []

    links_in_order = [n for n in tree.iter() if n.tag == "a" and n.attrs.get("href")]
    ids_in_doc = {n.attrs.get("id") for n in tree.iter() if n.attrs.get("id")}
    has_skip_link = False
    if links_in_order:
        href = links_in_order[0].attrs.get("href", "")
        if href.startswith("#") and len(href) > 1 and href[1:] in ids_in_doc:
            has_skip_link = True
    if has_skip_link:
        return []

    scope = next((n for n in tree.iter() if n.tag == "body"), None) or next((n for n in tree.iter() if n.tag == "html"), None)
    if scope is None:
        return []

    # Not count-based (the condition fires at most once per page) and not
    # measurement-based. Impact is what the weighing order puts first, and
    # here impact is how much a reader has to traverse before reaching
    # content: a page whose markup exposes at most one focusable element
    # ahead of its first heading costs a keyboard reader one extra
    # keystroke, which is the severity-2 anchor row; a page fronted by a
    # full navigation block costs them the whole block on every load,
    # which is the severity-3 anchor row.
    preceding = _focusables_before_first_heading(tree)
    severity = 3 if preceding >= 2 else 2
    return [RawFinding(
        criterion="WCAG-2.4.1",
        severity=severity,
        location=_loc(scope, f"<{scope.tag}> opening tag"),
        evidence=f"{_truncate(scope.raw)}; {preceding} focusable element(s) precede the first heading",
        violation='The page provides neither a main landmark (a <main> element or role="main") nor a leading same-page skip link.',
        fix="Add a <main> element wrapping the primary content, or a skip link as the first focusable element linking to it.",
    )]


# ---------------------------------------------------------------------------
# WCAG-2.4.2: page titled
# ---------------------------------------------------------------------------


def _check_page_title(tree):
    html_node = next((n for n in tree.iter() if n.tag == "html"), None)
    if html_node is None:
        return []

    title_node = next((n for n in tree.iter() if n.tag == "title"), None)
    text = _normalize_ws(title_node.text_content()) if title_node is not None else ""

    if title_node is not None and text and text.lower() not in PLACEHOLDER_TITLES:
        return []

    scope = title_node or next((n for n in tree.iter() if n.tag == "head"), None) or html_node
    evidence = f"<title>{text}</title>" if title_node is not None else _truncate(scope.raw)

    # Not count-based: the condition fires at most once per page. The two
    # branches are the two anchor rows in references/WCAG.md. A recognized
    # placeholder default still announces something on load and still gives
    # a tab, bookmark, and history entry a stable string, so a reader who
    # lands on the page is oriented even though pages of the same site
    # cannot be told apart: severity 2. A missing or empty title leaves
    # nothing to announce and falls back to the raw URL: severity 3.
    is_placeholder = bool(text) and text.lower() in PLACEHOLDER_TITLES
    if is_placeholder:
        severity = 2
        violation = f"The page's title is the placeholder default '{text}' rather than a description of this page."
    else:
        severity = 3
        violation = "The page has no usable title: the title element is missing or empty."

    return [RawFinding(
        criterion="WCAG-2.4.2",
        severity=severity,
        location=_loc(scope, f"<{scope.tag}> element"),
        evidence=evidence,
        violation=violation,
        fix="Give the page a specific <title> describing its topic or purpose.",
    )]


# ---------------------------------------------------------------------------
# WCAG-2.4.4: link purpose (link text)
# ---------------------------------------------------------------------------


def _check_link_purpose(tree):
    candidates = []
    for node in tree.iter():
        if node.tag != "a" or not node.attrs.get("href"):
            continue
        if _is_hidden(node):
            continue
        if node.attrs.get("aria-label") or node.attrs.get("aria-labelledby") or node.attrs.get("title"):
            continue
        text = _normalize_ws(node.text_content()).lower()
        if text in GENERIC_LINK_PHRASES:
            candidates.append(node)

    severity = _severity_for_count(len(candidates))
    findings = []
    for node in candidates:
        visible = _normalize_ws(node.text_content())
        findings.append(RawFinding(
            criterion="WCAG-2.4.4",
            severity=severity,
            location=_loc(node, f"<a> link, text '{visible}'"),
            evidence=_truncate(f"{node.raw}{visible}</a>"),
            violation="The link's accessible name is a generic phrase that gives no clue to its destination out of context.",
            fix="Rewrite the link text to describe its destination or purpose, or add an aria-label.",
        ))
    return findings


# ---------------------------------------------------------------------------
# WCAG-2.5.3: label in name
# ---------------------------------------------------------------------------


def _check_label_in_name(tree):
    candidates = []
    for node in tree.iter():
        if _is_hidden(node):
            continue
        role = (node.attrs.get("role") or "").strip().lower()
        is_control = (
            node.tag in ("button", "a")
            or role in INTERACTIVE_ROLES
            or (node.tag == "input" and (node.attrs.get("type") or "text").strip().lower() in ("submit", "button", "reset"))
        )
        if not is_control:
            continue

        aria_label = node.attrs.get("aria-label")
        if not aria_label:
            continue

        visible_text = node.attrs.get("value") if node.tag == "input" else node.text_content()
        visible_norm = _normalize_ws(visible_text).lower()
        if not visible_norm:
            continue
        aria_norm = _normalize_ws(aria_label).lower()
        if visible_norm in aria_norm:
            continue

        candidates.append((node, visible_text, aria_label))

    severity = _severity_for_count(len(candidates))
    findings = []
    for node, visible_text, aria_label in candidates:
        findings.append(RawFinding(
            criterion="WCAG-2.5.3",
            severity=severity,
            location=_loc(node, f"<{node.tag}> control, visible label '{_normalize_ws(visible_text)}'"),
            evidence=f"visible text '{_normalize_ws(visible_text)}', accessible name '{_normalize_ws(aria_label)}'",
            violation="The control's visible text does not appear within its accessible name, so a voice-control user naming the visible label cannot activate it.",
            fix="Include the visible label text at the start of the aria-label value, or remove the aria-label and rely on the visible text.",
        ))
    return findings


# ---------------------------------------------------------------------------
# WCAG-3.1.1: language of page
# ---------------------------------------------------------------------------

_BCP47_RE = re.compile(r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*$")


def _check_page_language(tree):
    html_node = next((n for n in tree.iter() if n.tag == "html"), None)
    if html_node is None:
        return []

    lang = html_node.attrs.get("lang")
    if lang is not None and lang.strip() and _BCP47_RE.match(lang.strip()):
        return []

    if lang is None:
        violation = "The <html> element has no lang attribute."
    elif not lang.strip():
        violation = "The <html> element's lang attribute is empty."
    else:
        violation = f"The <html> element's lang attribute '{lang}' is not a well-formed BCP 47 language tag."

    # Not count-based: the condition fires at most once per page. Impact
    # is graded by how much of the page actually loses its language
    # declaration, which is the difference between the two anchor rows.
    # A descendant element carrying a well-formed lang still covers its
    # own subtree, so only the content outside that subtree falls back to
    # the reader's default: severity 2. With no well-formed lang anywhere,
    # the whole page falls back at once: severity 3.
    covered_subtree = next(
        (
            n
            for n in tree.iter()
            if n is not html_node
            and (n.attrs.get("lang") or "").strip()
            and _BCP47_RE.match(n.attrs["lang"].strip())
        ),
        None,
    )
    if covered_subtree is not None:
        severity = 2
        violation += (
            f" A <{covered_subtree.tag}> inside it declares lang=\"{covered_subtree.attrs['lang'].strip()}\", "
            "so only content outside that element falls back to the reader's default language."
        )
    else:
        severity = 3

    return [RawFinding(
        criterion="WCAG-3.1.1",
        severity=severity,
        location=_loc(html_node, "<html> element"),
        evidence=_truncate(html_node.raw),
        violation=violation,
        fix='Set lang to a well-formed BCP 47 tag identifying the page\'s default language, for example lang="en".',
    )]


# ---------------------------------------------------------------------------
# WCAG-3.3.2: labels or instructions
# ---------------------------------------------------------------------------


def _has_label_ancestor(node):
    n = node.parent
    while n is not None:
        if n.tag == "label":
            return True
        n = n.parent
    return False


def _check_form_labels(tree):
    labels_by_for = {}
    for node in tree.iter():
        if node.tag == "label":
            for_attr = node.attrs.get("for")
            if for_attr:
                labels_by_for.setdefault(for_attr, node)

    ids_in_doc = {n.attrs.get("id") for n in tree.iter() if n.attrs.get("id")}

    candidates = []
    for node in tree.iter():
        if node.tag not in ("input", "select", "textarea"):
            continue
        if node.tag == "input" and (node.attrs.get("type") or "text").strip().lower() == "hidden":
            continue
        if "disabled" in node.attrs:
            continue
        if _is_hidden(node):
            continue

        control_id = node.attrs.get("id")
        if control_id and control_id in labels_by_for:
            continue
        if _has_label_ancestor(node):
            continue
        if node.attrs.get("aria-label"):
            continue
        labelledby = node.attrs.get("aria-labelledby")
        if labelledby and any(ref in ids_in_doc for ref in labelledby.split()):
            continue
        if node.attrs.get("title"):
            continue

        candidates.append(node)

    severity = _severity_for_count(len(candidates))
    findings = []
    for node in candidates:
        findings.append(RawFinding(
            criterion="WCAG-3.3.2",
            severity=severity,
            location=_loc(node, f"<{node.tag}> control"),
            evidence=_truncate(node.raw),
            violation="No label, aria-label, aria-labelledby, or title identifies what this control expects.",
            fix="Add a <label for> pointing at this control's id, wrap the control in a <label>, or set aria-label.",
        ))
    return findings


# ---------------------------------------------------------------------------
# Aggregation and CLI
# ---------------------------------------------------------------------------


def check(artifact):
    """artifact: skills._shared.artifact.Artifact (artifact.path,
    artifact.text, artifact.sha256). Returns RawFindings, unranked and
    unbounded; run_scripted_lane does the rest."""
    tree = _parse_html(artifact.text)
    rules = _build_stylesheet(tree)

    findings = []
    findings.extend(_check_alt_text(tree))
    findings.extend(_check_structure(tree))
    findings.extend(_check_text_contrast(tree, rules))
    findings.extend(_check_viewport_zoom(tree))
    findings.extend(_check_fixed_width_reflow(tree, rules))
    findings.extend(_check_component_contrast(tree, rules))
    findings.extend(_check_text_spacing_clip(tree, rules))
    findings.extend(_check_bypass_block(tree))
    findings.extend(_check_page_title(tree))
    findings.extend(_check_link_purpose(tree))
    findings.extend(_check_label_in_name(tree))
    findings.extend(_check_page_language(tree))
    findings.extend(_check_form_labels(tree))
    return findings


def main(argv=None):
    return run_scripted_lane(
        skill_name="critique-accessibility",
        skill_version="0.1.1",
        rubrics=["WCAG"],
        check_fn=check,
        argv=argv,
    )


if __name__ == "__main__":
    sys.exit(main())
