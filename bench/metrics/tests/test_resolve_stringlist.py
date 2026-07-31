"""Tests for the `string-list` artifact type's location resolution and
zero-tolerance matching (bench/metrics/resolve_stringlist.py)."""

from __future__ import annotations

import json

from bench.metrics.resolve_stringlist import is_hit, parse_string_list, resolve

KEYED_JSON = json.dumps(
    [
        {"key": "billing.card-declined", "value": "Your card was declined. Try another one."},
        {"key": "billing.card-expired", "value": "Your card has expired."},
        {"key": "billing.retry", "value": "We could not process your payment right now."},
    ]
)

BARE_JSON = json.dumps(
    [
        "Your card was declined. Try another one.",
        "Your card has expired.",
        "We could not process your payment right now.",
    ]
)


def test_item_number_resolves_exact_index() -> None:
    doc = parse_string_list(KEYED_JSON)
    r = resolve(doc, "item 2")
    assert is_hit(r, {"item_index": 2})


def test_adjacent_index_is_not_credited_zero_tolerance() -> None:
    doc = parse_string_list(KEYED_JSON)
    r = resolve(doc, "item 2")
    assert not is_hit(r, {"item_index": 3})
    assert not is_hit(r, {"item_index": 1})


def test_ordinal_item_resolves() -> None:
    doc = parse_string_list(KEYED_JSON)
    r = resolve(doc, "the third item")
    assert is_hit(r, {"item_index": 3})


def test_item_key_resolves_exact_key() -> None:
    doc = parse_string_list(KEYED_JSON)
    r = resolve(doc, "billing.card-expired needs a friendlier tone")
    assert is_hit(r, {"item_key": "billing.card-expired"})
    assert not is_hit(r, {"item_key": "billing.retry"})


def test_content_quote_resolves_unique_item() -> None:
    doc = parse_string_list(KEYED_JSON)
    r = resolve(doc, 'the string "Your card has expired."')
    assert is_hit(r, {"item_index": 2})
    assert is_hit(r, {"item_key": "billing.card-expired"})


def test_bare_string_list_has_no_keys_only_indices() -> None:
    doc = parse_string_list(BARE_JSON)
    r = resolve(doc, "message 1")
    assert is_hit(r, {"item_index": 1})
    assert doc.items[0].key is None


def test_unresolvable_location_is_not_a_hit() -> None:
    doc = parse_string_list(KEYED_JSON)
    r = resolve(doc, "somewhere in the copy")
    assert not r.resolvable
    assert not is_hit(r, {"item_index": 1})


def test_plain_object_shape_preserves_order() -> None:
    doc = parse_string_list(json.dumps({"a": "First.", "b": "Second.", "c": "Third."}))
    assert [item.key for item in doc.items] == ["a", "b", "c"]
    assert [item.index for item in doc.items] == [1, 2, 3]
