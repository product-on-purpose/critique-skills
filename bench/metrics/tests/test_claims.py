"""Tests for claim extraction from a run envelope
(bench/metrics/claims.py)."""

from __future__ import annotations

from bench.metrics.claims import claims_from_envelope
from bench.metrics.tests.fixtures import envelope, finding


def test_finding_with_no_instances_is_one_claim() -> None:
    env = envelope(findings=[finding(finding_id="F-001", location="paragraph 1")])
    claims = claims_from_envelope(env)
    assert len(claims) == 1
    assert claims[0].location == "paragraph 1"
    assert claims[0].finding_id == "F-001"


def test_finding_with_n_instances_is_n_plus_one_claims() -> None:
    f = finding(
        finding_id="F-002",
        location="paragraph 1",
        instances=[
            {"location": "paragraph 4"},
            {"location": "paragraph 7"},
        ],
    )
    env = envelope(findings=[f])
    claims = claims_from_envelope(env)
    assert len(claims) == 3
    locations = {c.location for c in claims}
    assert locations == {"paragraph 1", "paragraph 4", "paragraph 7"}
    assert all(c.finding_id == "F-002" for c in claims)
    assert all(c.criterion == f["criterion"] for c in claims)


def test_empty_findings_yields_no_claims() -> None:
    env = envelope(findings=[])
    assert claims_from_envelope(env) == []
