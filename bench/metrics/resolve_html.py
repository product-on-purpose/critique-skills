"""Location resolution and tolerance for the `html` artifact type
(bench/README.md, "`html`"). Parses with the stdlib `html.parser`, builds
an element tree, and resolves a finding's free text against it with a
bounded selector engine: tag, `#id`, `.class`, descendant, child, and
`:nth-of-type` only, exactly the subset bench/README.md scopes the
resolver to.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

from bench.metrics.ordinals import ordinal_to_int
from bench.metrics.text_util import normalize_loose

_VOID_ELEMENTS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
)

NOUN_TAGS: dict[str, tuple[str, ...]] = {
    "link": ("a",),
    "image": ("img",),
    "button": ("button",),
    "heading": ("h1", "h2", "h3", "h4", "h5", "h6"),
    "field": ("input", "select", "textarea"),
    "table": ("table",),
    "list": ("ul", "ol"),
}

_ORDINAL_NOUN = re.compile(
    r"\bthe\s+([a-zA-Z]+)\s+(" + "|".join(NOUN_TAGS) + r")\b", re.IGNORECASE
)
_ID_HASH = re.compile(r"#([A-Za-z][\w-]*)")
_QUOTED = re.compile(r"[`\"“]([^`\"”]{1,400})[`\"”]")
_SIMPLE_SELECTOR = re.compile(
    r"^(?P<tag>[a-zA-Z][a-zA-Z0-9]*)?(?P<id>#[\w-]+)?(?P<classes>(?:\.[\w-]+)*)"
    r"(?::nth-of-type\((?P<nth>\d+)\))?$"
)


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    parent: int | None
    children: list[int] = field(default_factory=list)
    own_text: list[str] = field(default_factory=list)
    doc_position: int = 0


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list[_Node] = []
        self._stack: list[int] = []
        self._counter = 0

    def _open(self, tag: str, attrs: list[tuple[str, str | None]]) -> int:
        parent = self._stack[-1] if self._stack else None
        node = _Node(
            tag=tag.lower(),
            attrs={k: (v or "") for k, v in attrs},
            parent=parent,
            doc_position=self._counter,
        )
        self._counter += 1
        idx = len(self.nodes)
        self.nodes.append(node)
        if parent is not None:
            self.nodes[parent].children.append(idx)
        self._stack.append(idx)
        return idx

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open(tag, attrs)
        if tag.lower() in _VOID_ELEMENTS:
            self._stack.pop()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open(tag, attrs)
        self._stack.pop()

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self._stack) - 1, -1, -1):
            if self.nodes[self._stack[i]].tag == tag.lower():
                del self._stack[i:]
                return

    def handle_data(self, data: str) -> None:
        if self._stack:
            self.nodes[self._stack[-1]].own_text.append(data)


@dataclass(frozen=True, slots=True)
class HtmlDoc:
    nodes: tuple[_Node, ...]

    def full_text(self, idx: int) -> str:
        parts: list[str] = []

        def walk(i: int) -> None:
            parts.extend(self.nodes[i].own_text)
            for c in self.nodes[i].children:
                walk(c)

        walk(idx)
        return "".join(parts)

    def by_id(self, element_id: str) -> int | None:
        for i, n in enumerate(self.nodes):
            if n.attrs.get("id") == element_id:
                return i
        return None

    def ancestors(self, idx: int) -> list[int]:
        out: list[int] = []
        p = self.nodes[idx].parent
        while p is not None:
            out.append(p)
            p = self.nodes[p].parent
        return out

    def distance(self, from_idx: int, to_idx: int) -> int | None:
        """Steps from `from_idx` up to `to_idx` if `to_idx` is an
        ancestor of `from_idx`, else steps down if `to_idx` is a
        descendant of `from_idx`, else None."""
        anc = self.ancestors(from_idx)
        if to_idx in anc:
            return anc.index(to_idx) + 1
        stack: list[tuple[int, int]] = [(c, 1) for c in self.nodes[from_idx].children]
        while stack:
            cur, d = stack.pop()
            if cur == to_idx:
                return d
            for c in self.nodes[cur].children:
                stack.append((c, d + 1))
        return None

    def css_path(self, idx: int) -> str:
        parts: list[str] = []
        cur: int | None = idx
        while cur is not None:
            n = self.nodes[cur]
            siblings = (
                [c for c in self.nodes[n.parent].children if self.nodes[c].tag == n.tag]
                if n.parent is not None
                else []
            )
            if len(siblings) > 1:
                parts.append(f"{n.tag}:nth-of-type({siblings.index(cur) + 1})")
            else:
                parts.append(n.tag)
            cur = n.parent
        return " > ".join(reversed(parts))


def parse_html(text: str) -> HtmlDoc:
    builder = _TreeBuilder()
    builder.feed(text)
    builder.close()
    return HtmlDoc(tuple(builder.nodes))


def _tokenize_selector(selector: str) -> list[tuple[str, str]] | None:
    """Split a bounded selector into `(combinator, simple)` pairs, the
    first pair's combinator being `""`. Only `>` (child) and whitespace
    (descendant) combinators are recognized, per the bound."""
    raw = selector.strip()
    if not raw:
        return None
    chunks = re.split(r"(>)", raw)
    out: list[tuple[str, str]] = []
    combinator = ""
    for chunk in chunks:
        chunk = chunk.strip()
        if chunk == ">":
            combinator = ">"
            continue
        if not chunk:
            continue
        for i, sp in enumerate(chunk.split()):
            out.append((combinator if i == 0 else " ", sp))
            combinator = ""
    return out or None


def _matches_simple(doc: HtmlDoc, idx: int, simple: str) -> bool:
    m = _SIMPLE_SELECTOR.match(simple)
    if not m:
        return False
    node = doc.nodes[idx]
    if m.group("tag") and node.tag != m.group("tag").lower():
        return False
    if m.group("id") and node.attrs.get("id") != m.group("id")[1:]:
        return False
    classes = m.group("classes") or ""
    if classes:
        wanted = {c[1:] for c in re.findall(r"\.[\w-]+", classes)}
        have = set((node.attrs.get("class") or "").split())
        if not wanted <= have:
            return False
    if m.group("nth"):
        n = int(m.group("nth"))
        if node.parent is None:
            return False
        siblings = [c for c in doc.nodes[node.parent].children if doc.nodes[c].tag == node.tag]
        if siblings.index(idx) + 1 != n:
            return False
    return True


def _satisfies_chain(doc: HtmlDoc, idx: int, steps: list[tuple[str, str]]) -> bool:
    comb, simple = steps[-1]
    if comb == ">":
        parent = doc.nodes[idx].parent
        if parent is None or not _matches_simple(doc, parent, simple):
            return False
        return True if len(steps) == 1 else _satisfies_chain(doc, parent, steps[:-1])
    p = doc.nodes[idx].parent
    while p is not None:
        if _matches_simple(doc, p, simple):
            return True if len(steps) == 1 else _satisfies_chain(doc, p, steps[:-1])
        p = doc.nodes[p].parent
    return False


def resolve_css(doc: HtmlDoc, selector: str) -> set[int]:
    """Resolve a bounded CSS selector to the set of matching element
    indices. Returns an empty set for a selector outside the bound
    (bench/README.md: "A selector outside the bounded engine is
    unresolvable.")."""
    steps = _tokenize_selector(selector)
    if not steps:
        return set()
    last_comb, last_simple = steps[-1]
    candidates = {i for i in range(len(doc.nodes)) if _matches_simple(doc, i, last_simple)}
    if len(steps) == 1:
        return candidates
    return {idx for idx in candidates if _satisfies_chain(doc, idx, steps[:-1])}


@dataclass(frozen=True, slots=True)
class ResolvedHtml:
    resolvable: bool
    candidates: frozenset[int] = frozenset()
    canonical_key: str = "?:"


def _canonical_key(doc: HtmlDoc, candidates: frozenset[int], location_text: str) -> str:
    if not candidates:
        return "?:" + normalize_loose(location_text)
    idx = min(candidates, key=lambda i: doc.nodes[i].doc_position)
    node = doc.nodes[idx]
    if node.attrs.get("id"):
        return f"#{node.attrs['id']}"
    return doc.css_path(idx)


def resolve(doc: HtmlDoc, location_text: str) -> ResolvedHtml:
    candidates: set[int] = set()

    id_match = _ID_HASH.search(location_text)
    if id_match:
        idx = doc.by_id(id_match.group(1))
        if idx is not None:
            candidates.add(idx)
    else:
        for word in re.findall(r"[A-Za-z][\w-]*", location_text):
            idx = doc.by_id(word)
            if idx is not None:
                candidates.add(idx)

    quoted = list(_QUOTED.finditer(location_text))
    for qm in quoted:
        matched = resolve_css(doc, qm.group(1))
        if matched:
            candidates |= matched

    ordinal_match = _ORDINAL_NOUN.search(location_text)
    if ordinal_match:
        word, noun = ordinal_match.group(1).lower(), ordinal_match.group(2).lower()
        tags = NOUN_TAGS[noun]
        elements = sorted(
            (i for i, n in enumerate(doc.nodes) if n.tag in tags), key=lambda i: doc.nodes[i].doc_position
        )
        n = ordinal_to_int(word, total=len(elements))
        if n is not None:
            candidates.add(elements[n - 1])

    for qm in quoted:
        content_norm = normalize_loose(qm.group(1))
        if len(content_norm) >= 8:
            matches = [i for i in range(len(doc.nodes)) if normalize_loose(doc.full_text(i)) == content_norm]
            if len(matches) == 1:
                candidates.add(matches[0])

    frozen = frozenset(candidates)
    return ResolvedHtml(
        resolvable=bool(frozen), candidates=frozen, canonical_key=_canonical_key(doc, frozen, location_text)
    )


def _resolve_truth_node(doc: HtmlDoc, truth: dict) -> int | None:
    kind = truth["kind"]
    if kind == "element-id":
        return doc.by_id(truth["element_id"])
    if kind == "css":
        matches = resolve_css(doc, truth["css"])
        return next(iter(matches)) if len(matches) == 1 else None
    return None


def is_hit(doc: HtmlDoc, resolved: ResolvedHtml, truth: dict) -> bool:
    """HIT if a resolved node is the truth node, an ancestor of it at
    distance 1 or 2, or a descendant of it at distance 1
    (bench/README.md, "`html`", "Tolerance")."""
    truth_idx = _resolve_truth_node(doc, truth)
    if truth_idx is None:
        return False
    truth_ancestors = set(doc.ancestors(truth_idx))
    for c in resolved.candidates:
        if c == truth_idx:
            return True
        if c in truth_ancestors:
            if doc.distance(truth_idx, c) in (1, 2):
                return True
        else:
            if doc.distance(truth_idx, c) == 1:
                return True
    return False


def self_match(doc: HtmlDoc, a: ResolvedHtml, b: ResolvedHtml) -> bool:
    """Whether two findings' resolved locations name the same place,
    used for consistency. Symmetric: the ancestor/descendant windows are
    checked in both directions."""
    for ca in a.candidates:
        ca_ancestors = set(doc.ancestors(ca))
        for cb in b.candidates:
            if ca == cb:
                return True
            if cb in ca_ancestors:
                if doc.distance(ca, cb) in (1, 2):
                    return True
            elif doc.distance(ca, cb) == 1:
                return True
    if not a.resolvable and not b.resolvable:
        return a.canonical_key == b.canonical_key
    return False
