"""The shared composition model for `html` domains. A domain module
supplies vocabulary, shape, and injectors on top of `Element` and
`HtmlDocument`; it never reinvents an element tree of its own. See
`bench/generator/README.md`, "Shared composition models".

Slots are identities; indices are derived. Every `Element` carries a slot
id assigned at creation, and that id never changes. `slot_index` is
computed from the final composition, after every injection has run,
exactly as the README's "two rules that shape everything else" require.

A domain assigns `id` attributes to its own controls and sections as
ordinary composed content, unconditionally, whether or not any injector
ever targets a given element: this is what lets `bench/README.md`'s HTML
invariant hold by construction ("Every element of an injectable class
carries a content-derived id, in clean and seeded artifacts alike, ...
so the presence of an id never signals a plant"). This module does not
invent ids on a domain's behalf, matching the way `markdown.py` does not
invent heading text; it only carries whatever `attrs` the domain wrote.

The generator's own round-trip check (`bench/generator/pipeline.py`)
re-parses this module's rendered output with `bench/metrics/resolve_html.py`,
the metrics module's normative HTML parser, rather than with a second
copy of the tree logic here: the same relationship `markdown.py`'s own
docstring describes between itself and the metrics module's block parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace as _dc_replace
from typing import Union

Node = Union["Element", str]

# Elements with no closing tag, matching skills/critique-usability/
# scripts/checks.py's own `_VOID_ELEMENTS` and bench/metrics/resolve_html.py's
# `_VOID_ELEMENTS`, so a domain module's HTML round-trips through the same
# grammar the scored resolver and the skill's own scripted lane both use.
VOID_TAGS: frozenset[str] = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
})

# html, head, and body are page scaffolding: their own children render at
# the same indent depth as themselves, not one level deeper, so a
# generated page reads the way every hand-authored fixture in this
# repository already does (content flush under <body>, not indented
# under it).
_TRANSPARENT_INDENT_TAGS: frozenset[str] = frozenset({"html", "head", "body"})


@dataclass(frozen=True, slots=True)
class Element:
    """One HTML element. `attrs` is an ordered sequence of `(name, value)`
    pairs, never a dict or a set: attribute order in the rendered bytes
    must be a property of the code that built it, matching the forbidden-
    constructs rule against iterating a set or a dict comprehension over
    one. `children` is a document-order mix of `Element` and raw text
    `str`. `slot` is the element's permanent identity, assigned once at
    composition time and never renumbered."""

    tag: str
    attrs: tuple[tuple[str, str], ...]
    children: tuple[Node, ...]
    slot: str

    def attr(self, name: str) -> str | None:
        for k, v in self.attrs:
            if k == name:
                return v
        return None

    def text(self) -> str:
        """Flattened text content of this element and its descendants, in
        document order, matching the DOM notion of `.textContent`."""
        parts: list[str] = []

        def walk(node: Element) -> None:
            for child in node.children:
                if isinstance(child, str):
                    parts.append(child)
                else:
                    walk(child)

        walk(self)
        return "".join(parts)


def el(
    tag: str,
    slot: str,
    *,
    attrs: tuple[tuple[str, str], ...] = (),
    children: tuple[Node, ...] = (),
) -> Element:
    """Convenience constructor a domain's `compose` calls instead of
    spelling out the dataclass: `el("button", "s2.save-btn",
    attrs=(("type", "submit"),), children=("Save",))`."""
    return Element(tag=tag, attrs=attrs, children=children, slot=slot)


def _iter_elements(node: Element, *, skip_self: bool):
    """Every element under `node`, pre-order, document order. `skip_self`
    excludes `node` itself, used to walk a document's body without
    yielding the synthetic root."""
    if not skip_self:
        yield node
    for child in node.children:
        if isinstance(child, Element):
            yield from _iter_elements(child, skip_self=False)


@dataclass(frozen=True, slots=True)
class HtmlDocument:
    """An ordered, immutable tree of elements, wrapping the page `title`
    and a `root` element (conventionally `tag="body"`, `slot="#root"`).
    Every mutation returns a new HtmlDocument; nothing here is ever
    changed in place."""

    title: str
    root: Element

    # -- lookup ---------------------------------------------------------

    def element(self, slot: str) -> Element:
        if self.root.slot == slot:
            return self.root
        for e in _iter_elements(self.root, skip_self=True):
            if e.slot == slot:
                return e
        raise KeyError(f"slot not found: {slot!r}")

    def slot_index(self, slot: str) -> int:
        """The element's 0-based position in document order (pre-order,
        under the root, root itself excluded). Used by the harness to
        sort a manifest's defects in document order."""
        for i, e in enumerate(_iter_elements(self.root, skip_self=True)):
            if e.slot == slot:
                return i
        raise KeyError(f"slot not found: {slot!r}")

    # -- mutation ---------------------------------------------------------

    def replace_children(self, slot: str, children: tuple[Node, ...]) -> "HtmlDocument":
        """Return a new HtmlDocument with the element at `slot` carrying
        `children` in place of its own. Tag, attrs, and slot are
        unchanged: a text injector rewrites an element's contents, never
        its identity."""
        return _dc_replace(self, root=_replace_at(self.root, slot, lambda e: _dc_replace(e, children=children)))

    def replace_text(self, slot: str, text: str) -> "HtmlDocument":
        return self.replace_children(slot, (text,))

    def set_attr(self, slot: str, name: str, value: str) -> "HtmlDocument":
        """Set (overwrite in place, or append if absent) one attribute."""

        def transform(e: Element) -> Element:
            kept = [(k, v) for k, v in e.attrs if k != name]
            kept.append((name, value))
            return _dc_replace(e, attrs=tuple(kept))

        return _dc_replace(self, root=_replace_at(self.root, slot, transform))

    def remove_attr(self, slot: str, name: str) -> "HtmlDocument":
        def transform(e: Element) -> Element:
            return _dc_replace(e, attrs=tuple((k, v) for k, v in e.attrs if k != name))

        return _dc_replace(self, root=_replace_at(self.root, slot, transform))

    def remove_element(self, slot: str) -> "HtmlDocument":
        """Remove the element at `slot`, and everything under it, from
        its parent's children. Nothing else in the document is
        renumbered, per the README's "slots are identities" rule."""
        new_root = _remove_at(self.root, slot)
        if new_root is None:
            raise KeyError(f"slot not found, or is the document root: {slot!r}")
        return _dc_replace(self, root=new_root)

    def insert_after(self, anchor_slot: str, new_element: Element) -> "HtmlDocument":
        """Insert `new_element` as the next sibling of `anchor_slot`.
        `new_element` carries its own new slot; nothing already in the
        document is renumbered."""
        new_root = _insert_sibling(self.root, anchor_slot, new_element, after=True)
        if new_root is None:
            raise KeyError(f"slot not found: {anchor_slot!r}")
        return _dc_replace(self, root=new_root)

    def insert_before(self, anchor_slot: str, new_element: Element) -> "HtmlDocument":
        new_root = _insert_sibling(self.root, anchor_slot, new_element, after=False)
        if new_root is None:
            raise KeyError(f"slot not found: {anchor_slot!r}")
        return _dc_replace(self, root=new_root)

    def append_child(self, parent_slot: str, new_element: Element) -> "HtmlDocument":
        """Append `new_element` as the last child of `parent_slot`,
        which may be the document root itself."""
        if self.root.slot == parent_slot:
            return _dc_replace(self, root=_dc_replace(self.root, children=(*self.root.children, new_element)))

        def transform(e: Element) -> Element:
            return _dc_replace(e, children=(*e.children, new_element))

        return _dc_replace(self, root=_replace_at(self.root, parent_slot, transform))


# ---------------------------------------------------------------------------
# Structural rebuild helpers. Each walks the tree once and rebuilds only
# the ancestors of the found slot; a subtree with no match anywhere in it
# is returned unchanged (not merely equal, the same object), so a mutation
# touches only the bytes it means to.
# ---------------------------------------------------------------------------


def _replace_at(node: Element, slot: str, fn) -> Element:
    new_root, found = _transform(node, slot, fn)
    if not found:
        raise KeyError(f"slot not found: {slot!r}")
    return new_root


def _transform(node: Element, slot: str, fn) -> tuple[Element, bool]:
    new_children: list[Node] = []
    found_here = False
    for child in node.children:
        if isinstance(child, Element):
            if child.slot == slot:
                found_here = True
                new_children.append(fn(child))
                continue
            new_child, found_below = _transform(child, slot, fn)
            found_here = found_here or found_below
            new_children.append(new_child)
        else:
            new_children.append(child)
    if found_here:
        return _dc_replace(node, children=tuple(new_children)), True
    return node, False


def _remove_at(node: Element, slot: str) -> Element | None:
    new_root, found = _transform_optional(node, slot, lambda e: None)
    return new_root if found else None


def _transform_optional(node: Element, slot: str, fn) -> tuple[Element, bool]:
    """Like `_transform`, but `fn` may return `None` to delete the
    matched element outright instead of replacing it."""
    new_children: list[Node] = []
    found_here = False
    for child in node.children:
        if isinstance(child, Element):
            if child.slot == slot:
                found_here = True
                replacement = fn(child)
                if replacement is not None:
                    new_children.append(replacement)
                continue
            new_child, found_below = _transform_optional(child, slot, fn)
            found_here = found_here or found_below
            new_children.append(new_child)
        else:
            new_children.append(child)
    if found_here:
        return _dc_replace(node, children=tuple(new_children)), True
    return node, False


def _insert_sibling(node: Element, anchor_slot: str, new_element: Element, *, after: bool) -> Element | None:
    new_children: list[Node] = []
    found_here = False
    for child in node.children:
        if isinstance(child, Element):
            if child.slot == anchor_slot:
                found_here = True
                if after:
                    new_children.append(child)
                    new_children.append(new_element)
                else:
                    new_children.append(new_element)
                    new_children.append(child)
                continue
            new_child = _insert_sibling(child, anchor_slot, new_element, after=after)
            if new_child is not None:
                found_here = True
                new_children.append(new_child)
            else:
                new_children.append(child)
        else:
            new_children.append(child)
    if found_here:
        return _dc_replace(node, children=tuple(new_children))
    return None


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _escape_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_attr(s: str) -> str:
    return _escape_text(s).replace('"', "&quot;")


def _render_element(e: Element, indent: int) -> str:
    """An element with only text children (or none) renders compact, on
    one line. An element with at least one element child renders as a
    block: open tag, one indented line per child, close tag. This is a
    purely structural decision, not a per-tag lookup table, so it is
    correct for any tag a domain module composes, including ones this
    module has never heard of."""
    pad = "  " * indent
    attr_str = "".join(f' {k}="{_escape_attr(v)}"' for k, v in e.attrs)
    if e.tag in VOID_TAGS:
        return f"{pad}<{e.tag}{attr_str}>"

    has_element_child = any(isinstance(c, Element) for c in e.children)
    if not has_element_child:
        inner = "".join(_escape_text(c) for c in e.children)
        return f"{pad}<{e.tag}{attr_str}>{inner}</{e.tag}>"

    child_indent = indent if e.tag in _TRANSPARENT_INDENT_TAGS else indent + 1
    lines = [f"{pad}<{e.tag}{attr_str}>"]
    for child in e.children:
        if isinstance(child, str):
            stripped = child.strip()
            if stripped:
                lines.append(f"{'  ' * child_indent}{_escape_text(stripped)}")
        else:
            lines.append(_render_element(child, child_indent))
    lines.append(f"{pad}</{e.tag}>")
    return "\n".join(lines)


def render(doc: HtmlDocument) -> str:
    """Serialize a full page: doctype, `<html lang="en">`, a `<head>`
    with a UTF-8 meta tag and `doc.title`, and `doc.root` (conventionally
    `<body>...</body>`). Does not add a trailing newline: the harness's
    emit stage is responsible for the single trailing newline every
    artifact carries, uniformly across artifact types."""
    head = el(
        "head",
        "#head",
        children=(
            el("meta", "#charset", attrs=(("charset", "utf-8"),)),
            el("title", "#title", children=(doc.title,)),
        ),
    )
    page = el("html", "#html", attrs=(("lang", "en"),), children=(head, doc.root))
    return f"<!doctype html>\n{_render_element(page, 0)}"
