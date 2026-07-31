"""Tests for greedy claim-to-defect assignment and the symmetric
assignment consistency uses (bench/metrics/match.py)."""

from __future__ import annotations

from bench.metrics import locate, match
from bench.metrics.claims import Claim
from bench.metrics.tests.fixtures import TOY_MD


def _parsed():
    return locate.parse_artifact("markdown-prose", TOY_MD)


def test_two_defects_same_criterion_different_sections_both_matched() -> None:
    parsed = _parsed()
    claims = [
        Claim(criterion="TOY-ACTIVE", location="paragraph 1", finding_id="F-001", severity=2),
        Claim(criterion="TOY-ACTIVE", location="paragraph 3", finding_id="F-002", severity=2),
    ]
    resolved = [locate.resolve_location(parsed, "markdown-prose", c.location) for c in claims]
    defects = [
        {"criterion": "TOY-ACTIVE", "location": {"kind": "paragraph", "paragraph": 1, "text": ""}},
        {"criterion": "TOY-ACTIVE", "location": {"kind": "paragraph", "paragraph": 3, "text": ""}},
    ]
    matched_defects, matched_claims = match.match_claims_to_defects(
        parsed, "markdown-prose", claims, resolved, defects
    )
    assert matched_defects == {0, 1}
    assert matched_claims == {0, 1}


def test_wrong_criterion_never_matches_even_at_same_location() -> None:
    parsed = _parsed()
    claims = [Claim(criterion="TOY-HEDGE", location="paragraph 2", finding_id="F-001", severity=2)]
    resolved = [locate.resolve_location(parsed, "markdown-prose", c.location) for c in claims]
    defects = [{"criterion": "TOY-ACTIVE", "location": {"kind": "paragraph", "paragraph": 2, "text": ""}}]
    matched_defects, matched_claims = match.match_claims_to_defects(
        parsed, "markdown-prose", claims, resolved, defects
    )
    assert matched_defects == set()
    assert matched_claims == set()


def test_jaccard_tolerant_is_symmetric() -> None:
    parsed = _parsed()
    claims_a = [
        Claim(criterion="TOY-ACTIVE", location="paragraph 2", finding_id="F-001", severity=2),
        Claim(criterion="TOY-HEDGE", location="paragraph 4", finding_id="F-002", severity=2),
    ]
    claims_b = [
        Claim(criterion="TOY-ACTIVE", location="paragraph 3", finding_id="G-001", severity=2),
    ]
    j_ab = match.jaccard_tolerant(parsed, "markdown-prose", claims_a, claims_b)
    j_ba = match.jaccard_tolerant(parsed, "markdown-prose", claims_b, claims_a)
    assert j_ab == j_ba


def test_jaccard_tolerant_both_empty_is_perfect_agreement() -> None:
    parsed = _parsed()
    assert match.jaccard_tolerant(parsed, "markdown-prose", [], []) == 1.0


def test_jaccard_exact_disagrees_on_phrasing_that_resolves_the_same() -> None:
    """Two claims naming the same paragraph by different phrasing agree
    under the tolerant metric; the exact metric only requires the same
    canonical key, which paragraph resolution also produces here, so both
    should agree. This test pins that canonicalization, not literal
    string equality, is what consistency_exact keys on."""
    parsed = _parsed()
    claims_a = [Claim(criterion="TOY-ACTIVE", location="paragraph 2", finding_id="F-001", severity=2)]
    claims_b = [Claim(criterion="TOY-ACTIVE", location="the second paragraph", finding_id="G-001", severity=2)]
    assert match.jaccard_exact(parsed, "markdown-prose", claims_a, claims_b) == 1.0
