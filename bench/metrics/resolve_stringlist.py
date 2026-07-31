"""Location resolution and tolerance for the `string-list` artifact type
(bench/README.md, "`string-list`"): zero tolerance, because adjacency in a
list of otherwise-unrelated strings carries no meaning.

Artifact format. bench/README.md describes the artifact type as "an
ordered or keyed list of user-facing strings" without pinning a byte
format (S-05 OQ-2 leaves `critique-microcopy`'s choice of bare list versus
annotated context open, and an annotated-context choice would use
`markdown-prose` instead, not this module at all). This module accepts a
JSON document in any of three shapes, in order of preference: a top-level
array of `{"key": ..., "value": ...}` objects (explicit order and keys), a
top-level array of bare strings (explicit order, no keys), or a top-level
JSON object mapping key to value (order is Python's `json` module's
insertion-preserving dict, which reflects source order for a
well-formed object). Whichever shape a domain settles on, `parse_string_list`
normalizes it to the same `StringItem` sequence before resolution runs.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from bench.metrics.ordinals import ordinal_to_int
from bench.metrics.text_util import normalize_loose

_ITEM_NUM = re.compile(r"\b(?:item|string|message)\s+(\d+)\b", re.IGNORECASE)
_ORD_ITEM = re.compile(r"\b([A-Za-z]+)\s+item\b", re.IGNORECASE)
_QUOTED = re.compile(r"[`\"“]([^`\"”]{1,400})[`\"”]")
_KEY_TOKEN = re.compile(r"[\w][\w.:-]*")


@dataclass(frozen=True, slots=True)
class StringItem:
    index: int  # 1-based, document order
    key: str | None
    value: str


@dataclass(frozen=True, slots=True)
class StringListDoc:
    items: tuple[StringItem, ...]

    def by_index(self, n: int) -> StringItem | None:
        return self.items[n - 1] if 1 <= n <= len(self.items) else None

    def by_key(self, key: str) -> StringItem | None:
        for item in self.items:
            if item.key == key:
                return item
        return None


def parse_string_list(text: str) -> StringListDoc:
    data = json.loads(text)
    items: list[StringItem] = []
    if isinstance(data, list):
        for i, entry in enumerate(data, start=1):
            if isinstance(entry, str):
                items.append(StringItem(index=i, key=None, value=entry))
            elif isinstance(entry, dict):
                key = entry.get("key")
                items.append(StringItem(index=i, key=key, value=str(entry.get("value", ""))))
            elif isinstance(entry, list) and len(entry) == 2:
                items.append(StringItem(index=i, key=str(entry[0]), value=str(entry[1])))
            else:
                raise ValueError(f"unsupported string-list entry at index {i}: {entry!r}")
    elif isinstance(data, dict):
        for i, (key, value) in enumerate(data.items(), start=1):
            items.append(StringItem(index=i, key=key, value=str(value)))
    else:
        raise ValueError("string-list artifact must be a JSON array or a JSON object")
    return StringListDoc(tuple(items))


@dataclass(frozen=True, slots=True)
class ResolvedStringList:
    resolvable: bool
    indices: frozenset[int] = frozenset()
    keys: frozenset[str] = frozenset()
    canonical_key: str = "?:"


def resolve(doc: StringListDoc, location_text: str) -> ResolvedStringList:
    indices: set[int] = set()
    keys: set[str] = set()

    m = _ITEM_NUM.search(location_text)
    if m:
        n = int(m.group(1))
        if doc.by_index(n) is not None:
            indices.add(n)
    else:
        m = _ORD_ITEM.search(location_text)
        if m:
            n = ordinal_to_int(m.group(1), total=len(doc.items))
            if n is not None:
                indices.add(n)

    known_keys = {item.key for item in doc.items if item.key is not None}
    for token in _KEY_TOKEN.findall(location_text):
        if token in known_keys:
            keys.add(token)

    for qm in _QUOTED.finditer(location_text):
        content_norm = normalize_loose(qm.group(1))
        if len(content_norm) >= 8:
            matches = [item for item in doc.items if normalize_loose(item.value) == content_norm]
            if len(matches) == 1:
                indices.add(matches[0].index)
                if matches[0].key is not None:
                    keys.add(matches[0].key)

    if indices:
        canonical_key = str(min(indices))
    elif keys:
        canonical_key = "key:" + min(keys)
    else:
        canonical_key = "?:" + normalize_loose(location_text)

    return ResolvedStringList(
        resolvable=bool(indices) or bool(keys), indices=frozenset(indices), keys=frozenset(keys),
        canonical_key=canonical_key,
    )


def is_hit(resolved: ResolvedStringList, truth: dict) -> bool:
    """Zero tolerance: HIT only on an exact index or exact key match."""
    item_index = truth.get("item_index")
    if item_index is not None and item_index in resolved.indices:
        return True
    item_key = truth.get("item_key")
    if item_key is not None and item_key in resolved.keys:
        return True
    return False


def self_match(a: ResolvedStringList, b: ResolvedStringList) -> bool:
    if a.indices & b.indices:
        return True
    if a.keys & b.keys:
        return True
    if not a.resolvable and not b.resolvable:
        return a.canonical_key == b.canonical_key
    return False
