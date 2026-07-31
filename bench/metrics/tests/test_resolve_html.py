"""Tests for the `html` artifact type's location resolution and tolerance
(bench/metrics/resolve_html.py)."""

from __future__ import annotations

from bench.metrics.resolve_html import is_hit, parse_html, resolve, resolve_css

HTML = """
<html><body>
<main>
<section id="intro">
<h2>Introduction</h2>
<p>Welcome to the service portal for residents.</p>
</section>
<section id="pricing">
<h2>Pricing</h2>
<figure>
<img id="pricing-hero" src="hero.png" alt="">
</figure>
<a id="pricing-cta" class="cta" href="/buy">Buy now</a>
<a href="/learn">Learn more</a>
</section>
</main>
</body></html>
"""


def test_element_id_hash_token_resolves() -> None:
    doc = parse_html(HTML)
    r = resolve(doc, "the #pricing-cta button")
    assert is_hit(doc, r, {"kind": "element-id", "element_id": "pricing-cta"})


def test_bare_id_token_resolves() -> None:
    doc = parse_html(HTML)
    r = resolve(doc, "see pricing-cta for the call to action")
    assert is_hit(doc, r, {"kind": "element-id", "element_id": "pricing-cta"})


def test_exact_node_is_a_hit() -> None:
    doc = parse_html(HTML)
    r = resolve(doc, "pricing-hero")
    assert is_hit(doc, r, {"kind": "element-id", "element_id": "pricing-hero"})


def test_ancestor_within_two_levels_is_a_hit() -> None:
    doc = parse_html(HTML)
    # The figure is the parent of the img (distance 1).
    figure_idx = next(i for i, n in enumerate(doc.nodes) if n.tag == "figure")
    r = resolve(doc, f'`{resolve_selector_for(doc, figure_idx)}`')
    assert is_hit(doc, r, {"kind": "element-id", "element_id": "pricing-hero"})


def resolve_selector_for(doc, idx) -> str:
    return doc.css_path(idx)


def test_body_two_levels_beyond_is_a_miss() -> None:
    doc = parse_html(HTML)
    body_idx = next(i for i, n in enumerate(doc.nodes) if n.tag == "body")
    r = resolve(doc, f"`{doc.css_path(body_idx)}`")
    assert not is_hit(doc, r, {"kind": "element-id", "element_id": "pricing-hero"})


def test_descendant_at_distance_one_is_a_hit() -> None:
    doc = parse_html(HTML)
    # section#pricing is the truth (by css); its child <figure> is a
    # descendant at distance 1 and should be credited.
    figure_idx = next(i for i, n in enumerate(doc.nodes) if n.tag == "figure")
    r = resolve(doc, f"`{doc.css_path(figure_idx)}`")
    assert is_hit(doc, r, {"kind": "css", "css": "main > section:nth-of-type(2)"})


def test_css_selector_bounded_engine_child_and_nth_of_type() -> None:
    doc = parse_html(HTML)
    matches = resolve_css(doc, "main > section:nth-of-type(2) > figure > img")
    assert len(matches) == 1
    idx = next(iter(matches))
    assert doc.nodes[idx].attrs.get("id") == "pricing-hero"


def test_ordinal_and_noun_resolves_second_link() -> None:
    doc = parse_html(HTML)
    r = resolve(doc, "the second link on the page")
    assert is_hit(doc, r, {"kind": "css", "css": "main > section:nth-of-type(2) > a:nth-of-type(2)"})


def test_content_quote_resolves_unique_element() -> None:
    doc = parse_html(HTML)
    r = resolve(doc, 'the text "Welcome to the service portal for residents."')
    assert is_hit(doc, r, {"kind": "css", "css": "main > section:nth-of-type(1) > p"})


def test_unresolvable_location_is_not_a_hit() -> None:
    doc = parse_html(HTML)
    r = resolve(doc, "somewhere on the page")
    assert not r.resolvable
    assert not is_hit(doc, r, {"kind": "element-id", "element_id": "pricing-hero"})
